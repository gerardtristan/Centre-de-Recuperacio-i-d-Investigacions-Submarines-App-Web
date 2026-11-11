"""Pantalla de la prova de Cluber (T-M01-24): recorregut web.

Precisions: files de la T-M01-24 a docs/planning.md#ajustos-060-lectura (pantalla, numeració,
recepció, CSRF i registre de la prova). Només dades inventades.
"""

import time

import pytest
from django.contrib.messages import get_messages
from django.core.cache.backends.locmem import LocMemCache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.html import escape

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core.models import AuditEntry, ImportBatch, ImportLine, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.imports import cluber
from apps.members.models import Member, MembershipType
from apps.members.tests.test_cluber_preview import SENTINELS, build, dni, record

URL = "administration:cluber_preview"
ACTION = "members.cluber_import.preview"
MULTIPART_MARGIN = 64 * 1024
SUCCESS = (
    "Prova feta: no s'han modificat dades de socis ni s'ha importat cap soci. "
    "El fitxer no s'ha desat."
)
# Valors de columnes utilitzades, de catàleg i d'una columna desconeguda: mai a la pantalla.
USED = {
    "Nom": "SENTINELLA-NOM-WEB",
    "Cognoms": "SENTINELLA-COGNOMS-WEB",
    "Email": "sentinella-web@example.org",
    "Telèfon": "34611199988",
    "Document d'Identitat": "SENTINELLADOCWEB",
    "Quota": "SENTINELLA-QUOTA-WEB",
    "Estat": "SENTINELLA-ESTAT-WEB",
}
UNKNOWN_HEADER = "SENTINELLA-CAPCALERA-WEB"
HIDDEN = (*SENTINELS.values(), *USED.values(), UNKNOWN_HEADER, "00067")


def csv_file(data, name="socis.csv"):
    return SimpleUploadedFile(name, data, content_type="text/csv")


def admin_client(account, *, csrf=False):
    client = Client(enforce_csrf_checks=csrf)
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_ADMIN
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def post(client, data, *, token=None, **extra):
    fields = {"csrfmiddlewaretoken": token} if token else {}
    fields["fitxer"] = csv_file(data)
    return client.post(reverse(URL), fields, **extra)


def token_of(client):
    client.get(reverse(URL))
    return client.cookies["csrftoken"].value


def audits():
    return list(AuditEntry.objects.filter(action=ACTION))


def no_cache(response):
    cache_control = response.headers.get("Cache-Control", "")
    return "no-store" in cache_control and "no-cache" in cache_control


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin("administrator")


@pytest.fixture
def web(admin):
    return admin_client(admin)


@pytest.fixture
def preview_calls(monkeypatch):
    calls = []
    real = cluber.preview

    def spy(data):
        calls.append(len(data))
        return real(data)

    monkeypatch.setattr(cluber, "preview", spy)
    return calls


class TestAccess:
    def test_anonymous_goes_to_the_admin_login(self, db, preview_calls):
        response = Client().post(reverse(URL), {"fitxer": csv_file(build([record(1)]))})
        assert response.status_code == 302
        assert reverse("administration:login") in response["Location"]
        assert preview_calls == [] and audits() == []

    def test_personal_session_does_not_enter(self, db, personal_account, preview_calls):
        client = Client()
        client.force_login(personal_account)
        session = client.session
        session[AREA_SESSION_KEY] = AREA_PERSONAL
        session.save()
        response = post(client, build([record(1)]))
        assert response.status_code == 302
        assert preview_calls == [] and audits() == []

    def test_admin_without_p18_gets_not_found(self, db, make_admin, preview_calls):  # noqa: F811
        client = admin_client(make_admin("treasurer"))
        assert client.get(reverse(URL)).status_code == 404
        assert post(client, build([record(1)])).status_code == 404
        assert preview_calls == [] and audits() == []

    def test_admin_with_p18_sees_the_form(self, web):
        response = web.get(reverse(URL))
        assert response.status_code == 200
        assert no_cache(response)
        html = response.content.decode()
        assert 'name="fitxer"' in html and 'type="file"' in html and 'accept=".csv' in html
        assert audits() == []

    def test_link_only_with_p18(self, web, make_admin):  # noqa: F811
        link = reverse(URL)
        assert link in web.get(reverse("administration:home")).content.decode()
        other = admin_client(make_admin("treasurer"))
        assert link not in other.get(reverse("administration:home")).content.decode()


class TestCsrf:
    def test_without_token(self, admin, preview_calls):
        client = admin_client(admin, csrf=True)
        response = post(client, build([record(1)]))
        assert response.status_code == 403
        assert no_cache(response)
        assert preview_calls == [] and audits() == []

    def test_wrong_token(self, admin, preview_calls):
        client = admin_client(admin, csrf=True)
        token_of(client)
        response = post(client, build([record(1)]), token="x" * 64)
        assert response.status_code == 403
        assert preview_calls == [] and audits() == []

    def test_right_token(self, admin, preview_calls):
        client = admin_client(admin, csrf=True)
        response = post(client, build([record(1)]), token=token_of(client))
        assert response.status_code == 200
        assert len(preview_calls) == 1 and len(audits()) == 1


class TestReception:
    def _exact(self, size):
        data = build([record(1)])
        remaining = size - len(data)
        return data + b"\r\n" * (remaining // 2) + b"\n" * (remaining % 2)

    def test_file_at_the_limit(self, web):
        data = self._exact(cluber.MAX_BYTES)
        response = post(web, data)
        assert response.status_code == 200
        [entry] = audits()
        assert entry.details["rejected"] is None
        # 079 (A-26, P-65 punt 1): l'empremta canònica de les columnes llegides.
        assert entry.details["file_sha256"] == cluber.preview(data).fingerprint

    def test_file_over_the_limit_is_cut_while_receiving(self, web, preview_calls):
        data = self._exact(cluber.MAX_BYTES) + b"\n"
        response = post(web, data)
        assert response.status_code == 413
        assert no_cache(response)
        assert preview_calls == []  # no s'arriba a validar un fitxer parcial
        [entry] = audits()
        assert entry.details == {"rejected": "too_large", "counts": {}}  # sense empremta

    def test_declared_body_over_the_ceiling_is_rejected_before_reading(self, web, preview_calls):
        limit = cluber.MAX_BYTES + MULTIPART_MARGIN
        response = post(web, build([record(1)]), CONTENT_LENGTH=str(limit + 1))
        assert response.status_code == 413
        assert no_cache(response)
        # Abans del CSRF: no se sap si és un intent vàlid, i no es registra.
        assert preview_calls == [] and audits() == []

    def test_absent_content_length_arrives_empty(self, web, preview_calls):
        # Amb WSGI, Django llegeix zero bytes si no hi ha Content-Length: no arriba cap fitxer.
        response = post(web, build([record(1)]), CONTENT_LENGTH="")
        assert response.status_code == 400
        assert no_cache(response)
        assert preview_calls == []
        [entry] = audits()
        assert entry.details == {"rejected": "no_file", "counts": {}}

    @pytest.mark.parametrize("length", ["200", "1000"])
    def test_shorter_content_length_never_validates_a_partial_file(
        self, web, preview_calls, length
    ):
        # Django descarta la part del fitxer que queda tallada: no arriba cap fitxer a la vista.
        # (Un Content-Length més llarg que el cos no es pot provar amb el client de proves: un
        # servidor real esperaria els bytes que falten fins al temps d'espera.)
        response = post(web, build([record(1)]), CONTENT_LENGTH=length)
        assert response.status_code == 400
        assert no_cache(response)
        assert preview_calls == []
        assert audits()[0].details == {"rejected": "no_file", "counts": {}}

    def test_second_file_is_rejected(self, web, preview_calls):
        files = [csv_file(build([record(1)])), csv_file(build([record(2)]), "altre.csv")]
        response = web.post(reverse(URL), {"fitxer": files})
        assert response.status_code == 400
        assert preview_calls == []
        [entry] = audits()
        assert entry.details == {"rejected": "too_many_files", "counts": {}}

    def test_file_in_another_field_is_rejected(self, web, preview_calls):
        response = web.post(reverse(URL), {"altre": csv_file(build([record(1)]))})
        assert response.status_code == 400
        assert preview_calls == []
        assert audits()[0].details["rejected"] == "too_many_files"

    def test_no_file(self, web, preview_calls):
        response = web.post(reverse(URL), {})
        assert response.status_code == 400
        assert preview_calls == []
        assert audits()[0].details == {"rejected": "no_file", "counts": {}}

    @override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=10)
    def test_only_in_memory_never_a_temporary_file(self, web, monkeypatch):
        # Amb els gestors per defecte, més de 10 bytes aniria a un fitxer temporal.
        def forbidden(*args, **kwargs):
            raise AssertionError("cap fitxer temporal")

        monkeypatch.setattr(TemporaryFileUploadHandler, "new_file", forbidden)
        monkeypatch.setattr("tempfile.NamedTemporaryFile", forbidden)
        monkeypatch.setattr("tempfile.mkstemp", forbidden)
        assert post(web, build([record(1)])).status_code == 200


class TestResult:
    def test_successful_preview(self, web):
        response = post(web, build([record(1), record(2)]))
        assert response.status_code == 200
        assert no_cache(response)
        html = response.content.decode()
        assert SUCCESS in html
        assert "registre d'activitat" in html
        assert "La capçalera és el registre 1." in html
        assert "La importació final encara no està disponible." in html
        assert f'href="{reverse(URL)}"' in html  # provar un altre fitxer

    def test_no_confirmation_or_exclusion_controls(self, web):
        # El resultat no té cap formulari: per provar un altre fitxer hi ha un enllaç (GET).
        html = post(web, build([record(1)])).content.decode()
        assert "<form" not in html and "<button" not in html and 'type="submit"' not in html
        assert "confirm" not in html.lower() and "exclo" not in html.lower()

    def test_rejected_file_shows_the_safe_message(self, web):
        headers = [*cluber.KNOWN_HEADERS[:3]]  # sense el document, que és obligatori
        response = post(web, build([record(1)], headers=headers))
        assert response.status_code == 200
        html = response.content.decode()
        assert escape(str(cluber.MESSAGES["missing_header"])) in html
        assert 'role="alert"' in html and SUCCESS not in html
        [entry] = audits()
        assert entry.details["rejected"] == "missing_header"

    def test_iban_column_is_discarded_and_never_shown(self, web):
        # 071: el fitxer no es rebutja i el valor no surt a la pantalla ni al registre. 079 (A-26):
        # el registre porta l'empremta canònica, calculada sense l'IBAN.
        headers = [*cluber.KNOWN_HEADERS, "IBAN"]
        response = post(web, build([record(1, {"IBAN": "VALOR-INVENTAT"})], headers=headers))
        assert response.status_code == 200
        html = response.content.decode()
        assert SUCCESS in html
        assert escape(str(cluber.MESSAGES["iban_discarded"])) in html
        assert "VALOR-INVENTAT" not in html
        [entry] = audits()
        assert entry.details["rejected"] is None
        without_iban = build([record(1, {"IBAN": "UN-ALTRE-VALOR"})], headers=headers)
        assert entry.details["file_sha256"] == cluber.preview(without_iban).fingerprint
        assert "VALOR-INVENTAT" not in str(entry.details)

    def test_errors_by_record_and_conflict_without_column(self, web, make_person):
        member_person = make_person(id_document_type="dni", id_document_number=dni(9))
        Member.objects.create(
            person=member_person,
            type=MembershipType.objects.get(code="supporter"),
            joined_on="2026-01-01",
            member_number=67,
        )
        records = [record(1, {"Email": "-"}), record(2, {"Nº Soci": "67"})]
        html = post(web, build(records)).content.decode()
        assert "Registre" in html
        assert escape(str(cluber.MESSAGES["email_invalid"])) in html
        assert escape(str(cluber.MESSAGES["identity_conflict"])) in html
        assert "Relació entre el document i el número" in html

    def test_pending_grouped_by_code(self, web):
        html = post(web, build([record(1), record(2), record(3)])).content.decode()
        text = escape(str(cluber.MESSAGES["member_type"]))
        assert html.count(text) == 1  # una sola fila agrupada, no una per registre

    def test_nothing_from_the_file_or_internal_ids(self, web, make_person):
        person = make_person(id_document_type="dni", id_document_number="SENTINELLADOCWEB")
        headers = [*cluber.KNOWN_HEADERS, UNKNOWN_HEADER]
        records = [record(1, {**USED, "Nº Soci": "00067"}), record(2, {UNKNOWN_HEADER: "x"})]
        response = post(web, build(records, headers=headers))
        html = response.content.decode()
        for value in HIDDEN:
            assert value not in html
        assert f"person_id={person.pk}" not in html and "person_id" not in html
        assert set(response.context["summary"]) <= {
            "fingerprint",  # 079: empremta canònica, sense cap valor del fitxer
            "rejected",
            "rejected_column",
            "rejected_row",
            "encoding",
            "counts",
            "warnings",
            "unknown_columns",
            "catalogue",
            "catalogue_omitted",
            "type_names",
            "rows",
        }
        [entry] = audits()
        assert not any(value in str(entry.details) for value in HIDDEN)
        assert set(entry.details) == {"rejected", "counts", "file_sha256"}

    def test_accessible_markup(self, web):
        html = web.get(reverse(URL)).content.decode()
        assert '<label for="id_fitxer"' in html and 'id="id_fitxer"' in html
        assert 'aria-describedby="ajuda-fitxer"' in html and 'id="ajuda-fitxer"' in html
        assert "<h1>" in html
        result = post(web, build([record(1, {"Email": "-"})])).content.decode()
        assert result.count("<caption>") >= 2 and 'scope="col"' in result
        assert 'role="status"' in result


class TestOnlyTheAuthorisedAuditWrite:
    """`preview()` no escriu; el recorregut web només hi afegeix l'entrada del registre."""

    def _writes(self, queries):
        writes = []
        for query in queries:
            sql = query["sql"].lstrip().upper()
            if sql.startswith(("SAVEPOINT", "RELEASE SAVEPOINT", "ROLLBACK TO SAVEPOINT")):
                continue
            if not sql.startswith("SELECT"):
                writes.append(sql.split('"')[1].lower() if '"' in sql else sql[:30])
        return writes

    def test_preexisting_session_refresh_is_the_same_on_any_admin_page(self, web):
        with CaptureQueriesContext(connection) as queries:
            web.get(reverse("administration:home"))
        assert set(self._writes(queries)) <= {"django_session"}

    def test_post_writes_only_the_audit_entry_and_the_session(self, web, make_person):
        make_person(id_document_type="dni", id_document_number=dni(1))
        before = (
            list(Person.objects.order_by("pk").values()),
            list(Member.objects.order_by("pk").values()),
        )
        with CaptureQueriesContext(connection) as queries:
            response = post(web, build([record(1), record(2)]))
        assert response.status_code == 200
        writes = self._writes(queries)
        assert writes.count("core_auditentry") == 1
        assert set(writes) <= {"core_auditentry", "django_session"}
        after = (
            list(Person.objects.order_by("pk").values()),
            list(Member.objects.order_by("pk").values()),
        )
        assert after == before
        assert ImportBatch.objects.count() == 0 and ImportLine.objects.count() == 0

    def test_no_session_messages_or_cache(self, web, monkeypatch):
        def forbidden(*args, **kwargs):
            raise AssertionError("res a la memòria cau")

        for name in ("set", "add", "set_many", "get_or_set"):
            monkeypatch.setattr(LocMemCache, name, forbidden)
        # El middleware de sessió (preexistent) hi afegeix la caducitat a qualsevol pàgina
        # d'administració: es fa primer un GET perquè la comparació només vegi el POST.
        web.get(reverse("administration:home"))
        keys_before = set(web.session.keys())
        response = post(web, build([record(1, USED)]))
        assert response.status_code == 200
        assert set(web.session.keys()) == keys_before
        assert not any(v in str(dict(web.session)) for v in HIDDEN)
        assert list(get_messages(response.wsgi_request)) == []
