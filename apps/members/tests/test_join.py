"""Formulari «Fer-se soci» i alta presencial (T-M01-13): CA-M01-01, CA-M01-02, cel·les P1 i
P2, límit de peticions, document repetit sense revelar-ho i no fusió de persones. Només dades
inventades (DNI i NIE de prova amb la lletra correcta, correus a example.org)."""

import itertools
import re
import time
from datetime import date

import pytest
from django.db import transaction
from django.test import Client, override_settings
from django.urls import reverse

from apps.accounts import limits
from apps.accounts.models import Account, EmailLinkRequest
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import consents
from apps.core.models import AccountRole, AuditEntry, Consent, OutgoingEmail, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import join
from apps.members.forms import parse_document
from apps.members.models import (
    JoinAcceptance,
    Member,
    MemberRequest,
    MembershipNumberCounter,
    MembershipType,
)
from apps.members.views import admin as admin_views
from conftest import PASSWORD, CommittedDataTestCase, run_together

PUBLIC = "members:join"
IN_PERSON = "administration:join_in_person"
CREATED = "members.join_request.created"
LIMITED = "members.join_request.limited"
TEXT_KINDS = ("privacy", "membership_terms", "guardian_authorization")


def join_versions():
    return ";".join(f"{k}:{consents.current_text(k).version}" for k in TEXT_KINDS)


def form_data(**overrides):
    data = {
        "first_name": "Laia",
        "last_name": "Dorada Rap",
        "id_document": "12345678Z",
        "contact_email": "laia.dorada@example.org",
        "phone": "600 000 001",
        "address": "",
        "membership_type": MembershipType.objects.get(code="supporter").pk,
        "accept_privacy": "on",
        "accept_membership_terms": "on",
        "birth_date": "1990-05-20",
        "text_versions": join_versions(),
        "for_whom": "other",  # T-M01-53: amb sessió; «per a mi» té proves pròpies
    }
    data.update(overrides)
    return {k: v for k, v in data.items() if v is not None}


def _client(account, area):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = area
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


_VISITORS = itertools.count(1)


def visitor():
    """T-M01-53 (108, C.1): «Fer-se soci» només amb la sessió d'un compte personal."""
    n = next(_VISITORS)
    person = Person.objects.create(first_name="Visitant", origin=Person.Origin.WEB)
    account = Account.objects.create_personal(person, f"visitant{n}@example.org", PASSWORD)
    Account.objects.filter(pk=account.pk).update(status=Account.Status.ACTIVE)
    account.refresh_from_db()
    return personal_client(account)


def admin_client(account):
    return _client(account, AREA_ADMIN)


def personal_client(account):
    return _client(account, AREA_PERSONAL)


def strip_tokens(html: str) -> str:
    return re.sub(r'(csrfmiddlewaretoken" value="|X-CSRFToken": ")[^"]+', r"\1", html)


def counts():
    return {
        "person": Person.objects.exclude(first_name="Visitant").count(),  # sense el compte
        "request": MemberRequest.objects.count(),
        "member": Member.objects.count(),
        "consent": Consent.objects.count(),
        "email": OutgoingEmail.objects.count(),
        "counter": MembershipNumberCounter.objects.get().last_number,
    }


def publish_texts(publisher):
    for kind in TEXT_KINDS:
        consents.publish_text(kind, f"Text de prova: {kind}.", by=publisher)


@pytest.fixture
def texts(make_admin):  # noqa: F811
    publisher = make_admin("administrator")
    publish_texts(publisher)
    return publisher


@pytest.fixture
def secretary(make_admin, texts):  # noqa: F811
    return make_admin("secretary", username="secretaria.prova")


def submit(client=None, **overrides):
    return (client or visitor()).post(reverse(PUBLIC), form_data(**overrides))


# --- CA-M01-01 ---------------------------------------------------------------------------------
class TestWebForm:
    def test_get_asks_for_the_birth_date_and_no_adult_declaration(self, texts):
        response = visitor().get(reverse(PUBLIC))
        assert response.status_code == 200
        html = response.content.decode()
        assert 'name="id_document"' in html and 'name="birth_date"' in html
        assert 'name="adult"' not in html and "Confirmo que soc major" not in html
        assert "iban" not in html.lower()
        assert "Text de prova: privacy." in html
        assert "no-store" in response.headers["Cache-Control"]

    def test_valid_submission_creates_a_pending_request_and_no_member(self, texts):
        before = counts()
        response = submit()
        assert response.status_code == 303
        assert response["Location"] == reverse(PUBLIC)

        request = MemberRequest.objects.get()
        assert (request.kind, request.status, request.channel) == ("join", "pending", "web")
        assert request.requested_type.code == "supporter"
        assert request.member is None and request.duplicate_warning == []
        person = request.person
        assert (person.first_name, person.id_document_type, person.id_document_number) == (
            "Laia",
            "dni",
            "12345678Z",
        )
        assert person.origin == Person.Origin.WEB
        after = counts()
        assert after["member"] == before["member"] == 0
        assert after["counter"] == before["counter"]  # cap número consumit

        # Regla uniforme (CA-M01-01): cap consentiment a la persona; les acceptacions queden a
        # la sol·licitud, amb la versió vigent, el canal i qui accepta (l'adult mateix).
        assert not Consent.objects.filter(person=person).exists()
        rows = JoinAcceptance.objects.filter(request=request).select_related("legal_text")
        assert sorted(a.legal_text.kind for a in rows) == ["membership_terms", "privacy"]
        assert all(a.accepted_by == "applicant" for a in rows)
        assert all(a.channel == "web" and a.recorded_by_id is None for a in rows)
        assert all(a.legal_text == consents.current_text(a.legal_text.kind) for a in rows)
        assert request.birth_date == date(1990, 5, 20)
        assert request.guardian_id_document_number == ""

        entry = AuditEntry.objects.get(action=CREATED)
        assert entry.actor_kind == "anonymous" and entry.target_id == str(request.pk)
        assert entry.details == {
            "channel": "web",
            "person_created": True,
            "duplicate_warning": False,
        }

    def test_receipt_email_has_no_personal_data(self, texts):
        submit()
        email = OutgoingEmail.objects.get()
        assert email.template == "rebut-sollicitud-alta"
        assert email.to_address == "laia.dorada@example.org"
        assert email.person_id is None
        assert "Laia" not in email.body_text and "12345678Z" not in email.body_text

    def test_confirmation_after_redirect_and_not_again_on_reload(self, texts):
        client = visitor()
        submit(client)
        page = client.get(reverse(PUBLIC)).content.decode()
        assert "Sol·licitud enviada" in page and "laia.dorada@example.org" in page
        assert 'name="id_document"' not in page
        again = client.get(reverse(PUBLIC)).content.decode()
        assert 'name="id_document"' in again
        assert MemberRequest.objects.count() == 1

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("birth_date", None),
            ("birth_date", ""),
            ("birth_date", "31/02/2000"),  # no existeix
            ("birth_date", "no-es-una-data"),
            ("accept_privacy", None),
            ("accept_membership_terms", None),
            ("id_document", "12345678A"),  # lletra incorrecta
            ("id_document", "PROVA0001"),  # passaport: no s'admet [A validar]
            ("phone", "1234"),
            ("contact_email", "no-es-un-correu"),
            ("first_name", ""),
            ("membership_type", "999999"),
        ],
    )
    def test_invalid_submission_creates_nothing(self, texts, field, value):
        before = counts()
        response = submit(**{field: value})
        assert response.status_code == 200
        assert counts() == before
        assert not AuditEntry.objects.filter(action=CREATED).exists()
        assert not EmailLinkRequest.objects.exists()  # no compta per al límit

    def test_nie_is_accepted_with_its_type(self, texts):
        submit(id_document="x-1234567-l")
        person = MemberRequest.objects.get().person
        assert (person.id_document_type, person.id_document_number) == ("nie", "X1234567L")

    def test_new_text_version_between_get_and_post_is_rejected(self, texts):
        old_versions = join_versions()
        consents.publish_text("privacy", "Text de prova: privacy v2.", by=texts)
        before = counts()
        response = submit(text_versions=old_versions)
        assert response.status_code == 200
        assert "Els textos legals han canviat" in response.content.decode()
        assert counts() == before

    def test_without_published_texts_the_form_is_unavailable(self, db):
        assert visitor().get(reverse(PUBLIC)).status_code == 503
        assert visitor().post(reverse(PUBLIC), {}).status_code == 503
        assert MemberRequest.objects.count() == 0

    def test_csrf_is_required(self, texts):
        client = Client(enforce_csrf_checks=True)
        assert client.post(reverse(PUBLIC), form_data()).status_code == 403
        assert MemberRequest.objects.count() == 0

    def test_public_form_shows_no_internal_marks_or_document_help(self, texts):
        html = visitor().get(reverse(PUBLIC)).content.decode()
        assert "A validar" not in html and "a-validar" not in html
        assert "Només el veu la secretaria" not in html

    def test_legal_texts_open_in_a_window_and_stay_readable_without_javascript(self, texts):
        html = visitor().get(reverse(PUBLIC)).content.decode()
        assert "<details" not in html
        assert "js/textos-legals.js" in html
        for kind in TEXT_KINDS:
            # Text sencer a la secció de la mateixa pàgina (mai una pàgina nova).
            assert f'<article id="text-{kind}"' in html
            assert f"Text de prova: {kind}." in html
        # Cada text que accepta tothom té la seva casella obligatòria, amb l'enllaç a la finestra;
        # l'autorització del representant només surt per a un menor.
        for kind, field in (
            ("privacy", "accept_privacy"),
            ("membership_terms", "accept_membership_terms"),
        ):
            assert f'name="{field}"' in html and f'href="#text-{kind}" data-obre-text' in html
        assert html.count('class="etiqueta-obligatori"') == 2
        assert 'href="#text-guardian_authorization" data-obre-text' not in html
        assert 'target="_blank"' not in html

    def test_next_steps_follow_the_approved_order(self, texts):
        html = visitor().get(reverse(PUBLIC)).content.decode()
        steps = [
            "L'administració del C.R.I.S. revisa la sol·licitud.",
            "t'assigna el número de soci i crea la quota pendent.",
            "Pagues la quota des del teu compte.",
            "Amb l'alta aprovada i el pagament confirmat, passes a ser soci actiu i tens el carnet",
        ]
        html = html.replace("&#x27;", "'")
        positions = [html.index(step) for step in steps]
        assert positions == sorted(positions)
        assert html.index('class="despres"') > html.index("</form>")
        assert "La secretaria revisa" not in html
        # Ni el número ni el compte fan soci (069); per als exempts no es promet cap flux (P-57).
        assert "Ni el número de soci ni el compte activat no et fan soci per si sols." in html
        assert "t'explicarà per correu com continua l'alta" in html

    def test_receipt_names_the_administration_and_asks_nobody_to_pay(self, texts):
        submit()
        body = OutgoingEmail.objects.get().body_text
        assert "L'administració del C.R.I.S." in body
        assert "encara no és una alta aprovada" in body
        assert "secretaria" not in body and "quota" not in body


# --- CA-M01-02: document repetit, sense revelar-ho i sense fusionar ------------------------------
class TestDuplicates:
    @pytest.fixture
    def existing(self, texts):
        return Person.objects.create(
            first_name="Pau",
            last_name="Mero",
            contact_email="pau.mero@example.org",
            phone="600000099",
            id_document_type="dni",
            id_document_number="12345678Z",
            origin=Person.Origin.IN_PERSON,
        )

    def test_same_document_links_to_the_existing_person_without_changing_it(self, existing):
        before = counts()
        submit(id_document="1234 5678-z")  # el mateix document, escrit d'una altra manera
        assert Person.objects.exclude(first_name="Visitant").count() == before["person"]
        request = MemberRequest.objects.get()
        assert request.person == existing
        assert request.duplicate_warning == [{"match": "document", "person_id": existing.pk}]
        existing.refresh_from_db()
        # Cap dada nova s'escriu a la persona existent: no es fusiona res.
        assert (existing.first_name, existing.contact_email, existing.phone) == (
            "Pau",
            "pau.mero@example.org",
            "600000099",
        )
        entry = AuditEntry.objects.get(action=CREATED)
        assert entry.details["person_created"] is False and entry.details["duplicate_warning"]

    def test_visitor_sees_the_same_response_with_or_without_the_document(self, existing):
        new_client, dup_client = visitor(), visitor()
        new = submit(new_client, id_document="00000001R", contact_email="a@example.org")
        dup = submit(dup_client, id_document="12345678Z", contact_email="a@example.org")
        assert (new.status_code, new["Location"]) == (dup.status_code, dup["Location"])
        new_page = strip_tokens(new_client.get(reverse(PUBLIC)).content.decode())
        dup_page = strip_tokens(dup_client.get(reverse(PUBLIC)).content.decode())
        assert new_page == dup_page
        assert "Pau" not in dup_page and "pau.mero" not in dup_page
        first, second = OutgoingEmail.objects.order_by("pk")
        assert (first.subject, first.body_text) == (second.subject, second.body_text)

    def test_a_second_pending_request_is_not_created_and_the_answer_is_the_same(self, existing):
        submit(id_document="12345678Z")
        consents_before = Consent.objects.count()
        response = submit(id_document="12345678Z", contact_email="altra@example.org")
        assert response.status_code == 303
        assert MemberRequest.objects.count() == 1
        assert Consent.objects.count() == consents_before
        assert OutgoingEmail.objects.count() == 2  # el rebut surt igualment

    @pytest.mark.parametrize(
        ("overrides", "match"),
        [
            ({"contact_email": "pau.mero@example.org"}, "email"),
            ({"first_name": "pau", "last_name": "mero", "phone": "600 000 099"}, "name_phone"),
        ],
    )
    def test_possible_duplicate_creates_a_new_person_and_never_merges(
        self, existing, overrides, match
    ):
        submit(id_document="00000002W", **overrides)
        request = MemberRequest.objects.get()
        assert request.person != existing
        assert Person.objects.filter(origin__in=["web", "in_person"]).count() == 3
        assert request.duplicate_warning == [{"match": match, "person_id": existing.pk}]
        existing.refresh_from_db()
        assert (existing.first_name, existing.contact_email) == ("Pau", "pau.mero@example.org")


# --- P1: visitant i participant no soci; la resta, «no trobat» -----------------------------------
class TestP1:
    @pytest.fixture
    def personal(self, texts):
        person = Person.objects.create(first_name="Clara", origin=Person.Origin.WEB)
        account = Account.objects.create_personal(person, "clara.sard@example.org", PASSWORD)
        account.status = Account.Status.ACTIVE
        account.save()
        return account

    def _member(self, person, status):
        Member.objects.create(
            person=person,
            type=MembershipType.objects.get(code="supporter"),
            status=status,
            joined_on="2020-01-01",
            left_on="2024-01-01" if status == "left" else None,
        )

    def test_visitor(self, texts):
        assert visitor().get(reverse(PUBLIC)).status_code == 200

    def test_participant_without_membership(self, personal):
        assert personal_client(personal).get(reverse(PUBLIC)).status_code == 200

    @pytest.mark.parametrize("status", ["pending", "active", "unpaid"])
    def test_member_gets_not_found(self, personal, status):
        self._member(personal.person, status)
        client = personal_client(personal)
        assert client.get(reverse(PUBLIC)).status_code == 404
        assert client.post(reverse(PUBLIC), form_data()).status_code == 404
        assert MemberRequest.objects.count() == 0

    def test_former_member_can_ask_again(self, personal):
        self._member(personal.person, "left")
        assert personal_client(personal).get(reverse(PUBLIC)).status_code == 200

    @pytest.mark.parametrize("roles", [(), ("secretary",), ("administrator",)])
    def test_admin_session_gets_not_found(self, make_admin, texts, roles):  # noqa: F811
        client = admin_client(make_admin(*roles))
        assert client.get(reverse(PUBLIC)).status_code == 404
        assert client.post(reverse(PUBLIC), form_data()).status_code == 404
        assert MemberRequest.objects.count() == 0


# --- P2: alta presencial ------------------------------------------------------------------------
class TestP2:
    @pytest.mark.parametrize("role", ["secretary", "administrator"])
    def test_with_p2_creates_an_in_person_request(self, make_admin, texts, role):  # noqa: F811
        account = make_admin(role)
        client = admin_client(account)
        assert client.get(reverse(IN_PERSON)).status_code == 200
        response = client.post(reverse(IN_PERSON), form_data())
        assert response.status_code == 303
        request = MemberRequest.objects.get()
        assert request.channel == "in_person" and request.person.origin == "in_person"
        assert not Consent.objects.filter(person=request.person).exists()
        rows = JoinAcceptance.objects.filter(request=request)
        assert rows.count() == 2
        assert all(a.channel == "in_person" and a.recorded_by == account for a in rows)
        assert AuditEntry.objects.get(action=CREATED).actor_account == account
        assert Member.objects.count() == 0
        assert "Sol·licitud desada" in client.get(reverse(IN_PERSON)).content.decode()

    @pytest.mark.parametrize(
        "roles", [(), ("treasurer",), ("instructor",), ("history_department",), ("president",)]
    )
    def test_without_p2_gets_not_found(self, make_admin, texts, roles):  # noqa: F811
        client = admin_client(make_admin(*roles))
        before = counts()
        assert client.get(reverse(IN_PERSON)).status_code == 404
        assert client.post(reverse(IN_PERSON), form_data()).status_code == 404
        assert counts() == before

    def test_anonymous_and_personal_session_go_to_the_admin_login(self, texts, personal_account):
        for client in (Client(), personal_client(personal_account)):
            response = client.post(reverse(IN_PERSON), form_data())
            assert response.status_code == 302
            assert reverse("administration:login") in response["Location"]
        assert MemberRequest.objects.count() == 0

    def test_link_on_the_admin_home_only_with_p2(self, secretary, make_admin):  # noqa: F811
        link = reverse(IN_PERSON)
        assert link in admin_client(secretary).get(reverse("administration:home")).content.decode()
        other = admin_client(make_admin("treasurer"))
        assert link not in other.get(reverse("administration:home")).content.decode()

    def _existing(self):
        Person.objects.create(
            first_name="Pau",
            id_document_type="dni",
            id_document_number="12345678Z",
            origin=Person.Origin.WEB,
        )

    def test_secretary_is_told_about_the_duplicate(self, secretary):
        self._existing()
        client = admin_client(secretary)
        client.post(reverse(IN_PERSON), form_data())
        assert "Possible duplicat" in client.get(reverse(IN_PERSON)).content.decode()

    def test_without_p3a_the_answer_is_neutral(self, secretary, monkeypatch):
        self._existing()
        monkeypatch.setattr(admin_views, "has_perm", lambda account, code: False)
        client = admin_client(secretary)
        client.post(reverse(IN_PERSON), form_data())
        page = client.get(reverse(IN_PERSON)).content.decode()
        assert "Possible duplicat" not in page and "Sol·licitud desada" in page


# --- Límit de peticions (llindars provisionals [A validar]) --------------------------------------
class TestRateLimit:
    @override_settings(JOIN_FORM_ORIGIN_MAX=2, JOIN_FORM_ORIGIN_MINUTES=60)
    def test_origin_limit_blocks_without_creating_anything(self, texts):
        assert submit(id_document="00000001R", contact_email="a@example.org").status_code == 303
        assert submit(id_document="00000002W", contact_email="b@example.org").status_code == 303
        before = counts()
        response = submit(id_document="00000003A", contact_email="c@example.org")
        assert response.status_code == 429
        assert "massa sol·licituds" in response.content.decode()
        assert counts() == before
        assert AuditEntry.objects.filter(action=LIMITED).count() == 1
        # Un altre origen no en queda afectat.
        other = Client(REMOTE_ADDR="192.0.2.10")
        assert submit(other, id_document="00000003A").status_code == 303

    def test_join_and_email_link_counters_are_separate(self, db):
        for _ in range(limits.ORIGIN_WINDOW.max_count):
            EmailLinkRequest.objects.create(ip_address="192.0.2.1", purpose="join")
            EmailLinkRequest.objects.create(ip_address="192.0.2.2", purpose="reset")
        assert not limits.origin_limited("192.0.2.1")  # RN-M01-58 no compta les altes
        assert limits.origin_limited("192.0.2.2")
        with override_settings(JOIN_FORM_ORIGIN_MAX=2), transaction.atomic():
            assert limits.start_join("192.0.2.2") is not None  # ni a l'inrevés
            assert limits.start_join("192.0.2.1") is None

    @override_settings(JOIN_FORM_ORIGIN_MAX=1)
    def test_p450_join_and_guest_licence_counters_are_separate(self, db):
        with transaction.atomic():
            assert limits.start_join("192.0.2.3") is not None
            assert limits.start_join("192.0.2.3", limits.GUEST_LICENCE) is not None
            assert limits.start_join("192.0.2.3") is None
            assert limits.start_join("192.0.2.3", limits.GUEST_LICENCE) is None
        assert EmailLinkRequest.objects.filter(purpose="licguest").count() == 1

    @override_settings(JOIN_FORM_RECIPIENT_MAX_PER_DAY=1)
    def test_recipient_limit_stops_the_receipt_but_not_the_request(self, texts):
        submit(id_document="00000001R")
        submit(id_document="00000002W")
        assert MemberRequest.objects.count() == 2
        assert OutgoingEmail.objects.count() == 1

    @override_settings(JOIN_FORM_ORIGIN_MAX=1)
    def test_in_person_has_no_origin_limit(self, secretary):
        client = admin_client(secretary)
        for doc in ("00000001R", "00000002W"):
            assert client.post(reverse(IN_PERSON), form_data(id_document=doc)).status_code == 303
        assert MemberRequest.objects.count() == 2


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("12345678Z", ("dni", "12345678Z")),
        ("12.345.678-z", ("dni", "12345678Z")),
        ("Y1234567X", ("nie", "Y1234567X")),
        ("12345678A", None),
        ("X1234567A", None),
        ("1234567Z", None),
        ("", None),
    ],
)
def test_parse_document(value, expected):
    assert parse_document(value) == expected


# --- Concurrència: dues altes alhora amb el mateix document nou --------------------------------
class TestConcurrency(CommittedDataTestCase):
    def test_same_new_document_twice_creates_one_person_and_one_request(self):
        person = Person.objects.create(first_name="Admin", origin="in_person")
        publisher = Account.objects.create_admin(person, "publicador.prova")
        AccountRole.objects.create(
            admin_account=publisher, role=Role.objects.get(code="administrator")
        )
        publish_texts(publisher)
        data = {
            "first_name": "Laia",
            "last_name": "Dorada",
            "id_document_type": "dni",
            "id_document_number": "00000003A",
            "contact_email": "laia@example.org",
            "phone": "600000001",
            "membership_type": MembershipType.objects.get(code="supporter"),
            "birth_date": date(1990, 5, 20),
        }

        def run():
            join.submit(data, channel="web", send_receipt=False)
            return "fet"

        assert run_together([run, run]) == ["fet", "fet"]
        assert Person.objects.filter(id_document_number="00000003A").count() == 1
        assert MemberRequest.objects.filter(person__id_document_number="00000003A").count() == 1


# --- Punt volat de la ela geminada («l·l») ------------------------------------------------------
# L'únic correcte és U+00B7 (MIDDLE DOT). Aquests altres s'hi assemblen però no ho són.
WRONG_DOTS = {
    chr(0x0307): "U+0307 COMBINING DOT ABOVE",
    chr(0x0140): "U+0140 LATIN SMALL LETTER L WITH MIDDLE DOT",
    chr(0x013F): "U+013F LATIN CAPITAL LETTER L WITH MIDDLE DOT",
    chr(0x2219): "U+2219 BULLET OPERATOR",
    chr(0x22C5): "U+22C5 DOT OPERATOR",
    chr(0x2027): "U+2027 HYPHENATION POINT",
    chr(0x0387): "U+0387 GREEK ANO TELEIA",
    chr(0x02D9): "U+02D9 DOT ABOVE",
    chr(0x2022): "U+2022 BULLET",
}
_ROOT = __import__("pathlib").Path(__file__).resolve().parents[3]


def test_no_wrong_middle_dot_in_templates_emails_or_code():
    found = []
    for folder, patterns in (("templates", ("*.html", "*.txt")), ("apps", ("*.py",))):
        for pattern in patterns:
            for path in (_ROOT / folder).rglob(pattern):
                text = path.read_text(encoding="utf-8")
                found += [
                    (str(path.relative_to(_ROOT)), name)
                    for ch, name in WRONG_DOTS.items()
                    if ch in text
                ]
    assert found == []


def test_public_page_uses_the_right_middle_dot(texts):
    html = visitor().get(reverse(PUBLIC)).content.decode()
    visible = re.sub(r"<[^>]+>", " ", html)
    assert "Sol·licitud" in visible
    assert not [name for ch, name in WRONG_DOTS.items() if ch in html]
    # Tampoc un punt normal en lloc del volat («sol.licitud», «col.laboració»).
    assert not re.search(r"[a-zà-ú]l\.l[a-zà-ú]", visible, re.IGNORECASE)
