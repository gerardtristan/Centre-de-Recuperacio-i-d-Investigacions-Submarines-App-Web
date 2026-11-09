"""Importació de Cluber adaptada al format real (T-M01-24b; decisió 071).

Codificació amb alternativa, columna d'IBAN descartada, taula d'equivalències, normalització, tipus
de soci per nom, preu o pendent, i la mostra inventada de 40 socis en Windows-1252 amb la
capçalera real. Només dades inventades: els IBAN són clarament falsos i no tenen cap format vàlid.
"""

import csv
import datetime
import io
import logging

import pytest

from apps.core.models import AuditEntry, Charge, Consent, ImportBatch, ImportLine, LegalText
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.imports import cluber
from apps.members.models import Member, MembershipType
from apps.members.tests.test_cluber_preview import build, dni, only_row, record
from apps.members.tests.test_cluber_views import admin_client, post

FALSE_IBAN = "ES00IBANFALS"  # prefix de tots els IBAN inventats de la mostra


def fake_iban(n):
    return f"{FALSE_IBAN}{n:012d}"


def real_headers():
    """Capçalera de l'exportació real: la de la mostra parcial amb «IBAN» després de «Soci
    titular» (071, punt 19)."""
    headers = list(cluber.KNOWN_HEADERS)
    headers.insert(headers.index("Soci titular") + 1, "IBAN")
    return headers


SAMPLE_QUOTAS = (
    ("Quota de soci col·laborador 35€.", "35"),  # pel preu (o pendent si dos tipus el comparteixen)
    ("Quota de soci Ple Dret 90 €.", "90,00"),  # pel nom
    ("QUOTA SIMPATITZANT 35€", "35"),  # pel nom, amb majúscules
    ("Quota familiar 50€.", "50"),  # cap tipus amb aquest preu: pendent
    ("Quota juvenil 35€", "35"),  # pel nom si hi ha el tipus «Juvenil»
)
NAMES = ("Àngels", "Jordi", "Núria", "Pere", "Mònica", "Ferran", "Laia", "Iñaki")


def sample_records(count=40):
    rows = []
    for n in range(1, count + 1):
        quota, total = SAMPLE_QUOTAS[n % len(SAMPLE_QUOTAS)]
        rows.append(
            {
                "Nº Soci": str(n),
                "Nom": NAMES[n % len(NAMES)],
                "Cognoms": f"Garcia Inventat{n}",
                "Telèfon": f"346000000{n:02d}",
                "Document d'Identitat": dni(5000 + n),
                "Quota": quota,
                "Preu total": total,
                "Estat": "Activo" if n % 2 else "Pendiente",
                "Soci titular": "",
                "IBAN": fake_iban(n),
                "Email": f"soci{n}@example.org",
                "Data alta/renovació": "" if n % 7 == 0 else f"{n % 28 + 1:02d}/10/2026",
                "Mètode de pagament": "Domiciliación",
                "Adreça": f"Carrer de l'Àncora, {n}",
                "Codi Postal": "08001",
                "Ciutat": "-" if n % 3 == 0 else "Barcelona",
                "Província": "Barcelona",
                "Renovació": "Automática",
                "Polítiques de privadesa": "Sí" if n % 5 else "No",
                "Data d'inscripció": "" if n % 6 == 0 else f"{n % 28 + 1}/{n % 12 + 1}/2010",
                "Data de Naixament": "" if n % 4 == 0 else f"{n % 28 + 1:02d}/05/1980",
                "Edat": "46",
                "idInterno": f"cl-{n:05d}",
                cluber.IMAGE_CONSENT: "Sí" if n % 2 else "No",
            }
        )
    return rows


def sample_file(count=40):
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator="\r\n")
    headers = real_headers()
    writer.writerow(headers)
    for row in sample_records(count):
        writer.writerow([row.get(h, "") for h in headers])
    return out.getvalue().encode("cp1252")


@pytest.fixture
def juvenile(db):
    # Un tercer tipus amb el mateix preu que «Simpatitzant»: el preu ja no decideix.
    return MembershipType.objects.create(code="juvenile", name="Juvenil", annual_fee_cents=3500)


class TestEncoding:
    def test_utf8_is_detected(self, db):
        assert cluber.preview(build([record(1)])).encoding == "utf-8"
        assert cluber.preview(build([record(1)], bom=True)).encoding == "utf-8"

    def test_windows_1252_is_the_fallback(self, db):
        data = build([record(1, {"Nom": "Àngels"})]).decode("utf-8").encode("cp1252")
        with pytest.raises(UnicodeDecodeError):
            data.decode("utf-8")
        result = cluber.preview(data)
        assert result.rejected is None
        assert result.encoding == "windows-1252"
        assert result.unknown_columns == []  # «Nº Soci» i «IMÁGENES» llegits bé
        assert result.summary()["encoding"] == "windows-1252"

    def test_neither_encoding_is_rejected(self, db):
        result = cluber.preview(b"N\x81 Soci;Nom\r\n")
        assert result.rejected == "encoding"
        assert result.encoding is None


class TestEquivalences:
    def test_every_read_column_is_a_known_header_with_a_purpose(self):
        for equivalence in cluber.EQUIVALENCES:
            assert equivalence.column in cluber.KNOWN_HEADERS
            assert equivalence.target and equivalence.purpose

    def test_only_the_nine_fields_and_the_resolution_columns(self):
        # 071, punt 10: nou camps i les columnes per resoldre o informar; res més.
        assert {e.column for e in cluber.EQUIVALENCES} == {
            "Nº Soci",
            "Nom",
            "Cognoms",
            "Document d'Identitat",
            "Email",
            "Telèfon",
            "Data de Naixament",
            "Adreça",
            "Codi Postal",
            "Ciutat",
            "Data d'inscripció",
            "Data alta/renovació",
            "Quota",
            "Preu total",
            "idInterno",
            cluber.IMAGE_CONSENT,
        }

    def test_every_filled_field_has_a_label(self, db):
        row = only_row(cluber.preview(build([record(1, {cluber.IMAGE_CONSENT: "Sí"})])))
        assert set(row.fields) <= set(cluber.FIELD_LABELS)
        assert {"Person.birth_date", "Member.cluber_id", "image_consent"} <= set(row.fields)

    @pytest.mark.parametrize(
        "column",
        ["Estat", "Renovació", "Soci titular", "Mètode de pagament", "Polítiques de privadesa"],
    )
    def test_ignored_columns_do_not_change_the_result(self, db, column):
        plain = only_row(cluber.preview(build([record(1)])))
        changed = only_row(cluber.preview(build([record(1, {column: "x" * 300})])))
        assert changed.summary() == plain.summary()


def values(**cells):
    return lambda column: cells.get(column, "")


class TestNormalize:
    def test_dates_in_dd_mm_yyyy(self, db):
        fields, errors = cluber.normalize(
            values(
                **{
                    "Data de Naixament": "02/05/1980",
                    "Data d'inscripció": "1/3/2010",
                    "Data alta/renovació": "31/10/2026",
                }
            )
        )
        assert errors == []
        assert fields["Person.birth_date"] == datetime.date(1980, 5, 2)
        assert fields["Member.joined_on"] == datetime.date(2010, 3, 1)
        assert fields["last_renewal"] == datetime.date(2026, 10, 31)

    @pytest.mark.parametrize("text", ["1980-05-02", "31/02/2020", "02/05/80", "02.05.1980", "ahir"])
    @pytest.mark.parametrize("column", ["Data de Naixament", "Data d'inscripció"])
    def test_invalid_dates_are_row_errors_without_values(self, db, text, column):
        fields, errors = cluber.normalize(values(**{column: text}))
        assert errors == [("date_invalid", column)]
        assert not {"Person.birth_date", "Member.joined_on"} & set(fields)

    def test_future_birth_date_is_an_error(self, db):
        _, errors = cluber.normalize(values(**{"Data de Naixament": "01/01/2999"}))
        assert errors == [("date_invalid", "Data de Naixament")]

    def test_empty_dates_fill_nothing(self, db):
        fields, errors = cluber.normalize(values())
        assert (fields, errors) == ({}, [])

    def test_address_with_postal_code_and_city_but_no_province(self, db):
        cells = {"Adreça": "Carrer Inventat, 1", "Codi Postal": "08001", "Ciutat": "Barcelona"}
        fields, _ = cluber.normalize(values(**cells, **{"Província": "Barcelona"}))
        assert fields["Person.address"] == "Carrer Inventat, 1, 08001 Barcelona"

    def test_city_dash_is_empty(self, db):
        cells = {"Adreça": "Carrer Inventat, 1", "Codi Postal": "08001", "Ciutat": "-"}
        fields, _ = cluber.normalize(values(**cells))
        assert fields["Person.address"] == "Carrer Inventat, 1, 08001"
        fields, _ = cluber.normalize(values(**{"Ciutat": "-"}))
        assert "Person.address" not in fields

    def test_phone_as_it_comes(self, db):
        fields, _ = cluber.normalize(values(**{"Telèfon": "34600000000"}))
        assert fields["Person.phone"] == "34600000000"

    @pytest.mark.parametrize(
        ("column", "target"),
        [
            ("Nom", "Person.first_name"),
            ("Cognoms", "Person.last_name"),
            ("Telèfon", "Person.phone"),
            ("idInterno", "Member.cluber_id"),
            ("Adreça", "Person.address"),
        ],
    )
    def test_destination_length_without_truncating(self, db, column, target):
        limit = cluber.MAX_LENGTH[target]
        fields, errors = cluber.normalize(values(**{column: "a" * limit}))
        assert fields[target] == "a" * limit and errors == []
        fields, errors = cluber.normalize(values(**{column: "a" * (limit + 1)}))
        assert target not in fields and errors == [("field_too_long", column)]

    @pytest.mark.parametrize("text", ["Sí", "si", "SI", "x", "1", "Acepto"])
    def test_image_consent_granted(self, db, text):
        fields, _ = cluber.normalize(values(**{cluber.IMAGE_CONSENT: text}))
        assert fields["image_consent"] is True

    @pytest.mark.parametrize("text", ["", "No", "0", "potser", "-"])
    def test_image_consent_not_granted_by_default(self, db, text):
        fields, _ = cluber.normalize(values(**{cluber.IMAGE_CONSENT: text}))
        assert "image_consent" not in fields


class TestRowOutcome:
    def test_missing_joined_date_is_imported_with_a_warning(self, db):
        row = only_row(cluber.preview(build([record(1, {"Data d'inscripció": ""})])))
        assert "joined_on" in row.warnings
        assert "joined_on" not in row.pending and not row.errors
        assert "Member.joined_on" not in row.fields

    def test_invalid_joined_date_is_an_error_not_a_warning(self, db):
        row = only_row(cluber.preview(build([record(1, {"Data d'inscripció": "2010-03-15"})])))
        assert row.errors == ["date_invalid"] and row.error_columns == ["Data d'inscripció"]
        assert "joined_on" not in row.warnings

    def test_empty_birth_date_is_allowed(self, db):
        row = only_row(cluber.preview(build([record(1, {"Data de Naixament": ""})])))
        assert not row.errors
        assert "Person.birth_date" not in row.fields

    def test_cluber_status_is_not_used(self, db):
        # 071, punt 7: tots entrarien actius; l'«Estat» de Cluber no decideix res.
        rows = [record(1, {"Estat": "Baja"}), record(2, {"Estat": "Activo"})]
        first, second = cluber.preview(build(rows)).rows
        assert first.summary() | {"row": 0} == second.summary() | {"row": 0}

    def test_no_value_is_kept_in_the_row(self, db):
        row = only_row(cluber.preview(build([record(1, {"idInterno": "SENTINELLA-ID-7Q"})])))
        assert "Member.cluber_id" in row.fields
        assert set(row.data) == {"member_number_text", "member_number", "id_document"}
        assert "SENTINELLA" not in repr(row) + str(row.summary())


class TestMemberType:
    @pytest.mark.parametrize(
        ("quota", "code", "by"),
        [
            ("Quota de soci Ple Dret 90€.", "full", "name"),
            ("QUOTA SIMPATITZANT", "supporter", "name"),
            ("Quota de soci col·laborador 35€.", "supporter", "price"),
            ("Quota de soci col·laborador 35,00 €", "supporter", "price"),
            ("Quota inventada 90€", "full", "price"),
        ],
    )
    def test_resolved_by_name_then_by_price(self, db, quota, code, by):
        row = only_row(cluber.preview(build([record(1, {"Quota": quota, "Preu total": ""})])))
        assert (row.member_type, row.member_type_by) == (code, by)
        assert "member_type" not in row.pending

    @pytest.mark.parametrize(
        "quota",
        [
            "",
            "Quota inventada",  # cap nom ni preu
            "Quota familiar 50€.",  # cap tipus amb aquest preu
            "Quota 35€ o 90€",  # més d'un preu
            "Simpatitzantíssim 12€",  # el nom ha de ser una paraula sencera
        ],
    )
    def test_pending_when_it_cannot_be_resolved(self, db, quota):
        row = only_row(cluber.preview(build([record(1, {"Quota": quota})])))
        assert row.member_type is None and "member_type" in row.pending

    def test_two_types_with_the_same_price_stay_pending(self, db, juvenile):
        quota = "Quota de soci col·laborador 35€."
        row = only_row(cluber.preview(build([record(1, {"Quota": quota})])))
        assert row.member_type is None and "member_type" in row.pending
        # El nom encara decideix.
        row = only_row(cluber.preview(build([record(1, {"Quota": "Quota juvenil 35€"})])))
        assert (row.member_type, row.member_type_by) == ("juvenile", "name")

    def test_two_names_fall_back_to_the_price(self, db):
        quota = "Quota simpatitzant o ple dret 90€"
        row = only_row(cluber.preview(build([record(1, {"Quota": quota})])))
        assert (row.member_type, row.member_type_by) == ("full", "price")

    def test_inactive_types_are_ignored(self, db):
        MembershipType.objects.filter(code="full").update(active=False)
        row = only_row(cluber.preview(build([record(1, {"Quota": "Quota ple dret 90€"})])))
        assert row.member_type is None and "member_type" in row.pending

    @pytest.mark.parametrize(("total", "warned"), [("35", False), ("35,00 €", False), ("40", True)])
    def test_total_price_is_only_informative(self, db, total, warned):
        quota = "Quota simpatitzant"
        row = only_row(cluber.preview(build([record(1, {"Quota": quota, "Preu total": total})])))
        assert ("total_price_differs" in row.warnings) is warned
        assert not row.errors and "member_type" not in row.pending
        assert Charge.objects.count() == 0

    def test_unreadable_total_price_is_ignored(self, db):
        quota = "Quota simpatitzant"
        row = only_row(cluber.preview(build([record(1, {"Quota": quota, "Preu total": "n/d"})])))
        assert "total_price_differs" not in row.warnings and not row.errors


class TestInventedSample:
    """La mostra inventada de 40 socis amb el format de l'exportació real (071, punt 19)."""

    def test_sample_is_windows_1252_with_the_real_header(self):
        data = sample_file()
        with pytest.raises(UnicodeDecodeError):
            data.decode("utf-8")
        header = next(csv.reader(io.StringIO(data.decode("cp1252")), delimiter=";"))
        assert header.index("IBAN") == header.index("Soci titular") + 1
        assert len(header) == len(cluber.KNOWN_HEADERS) + 1

    def test_sample_preview(self, db, juvenile, caplog):
        caplog.set_level(logging.DEBUG)
        result = cluber.preview(sample_file())
        assert result.rejected is None
        assert result.encoding == "windows-1252"
        assert result.warnings == ["no_document_type", "iban_discarded"]
        assert result.unknown_columns == []
        assert result.counts["rows"] == 40 and result.counts["new"] == 40
        assert result.counts["with_errors"] == 0
        assert result.counts["ready"] == 0  # el tipus de document continua pendent (P-62)

        types = {(r.member_type, r.member_type_by) for r in result.rows}
        assert types == {
            ("full", "name"),
            ("supporter", "name"),
            ("juvenile", "name"),
            (None, None),  # col·laborador (dos tipus de 35 €) i familiar (50 €)
        }
        pending_type = [r for r in result.rows if "member_type" in r.pending]
        assert len(pending_type) == 16
        joined_missing = [r for r in result.rows if "joined_on" in r.warnings]
        assert len(joined_missing) == 6  # 6, 12, …, 36
        assert sum("Person.birth_date" in r.fields for r in result.rows) == 30
        assert sum("last_renewal" in r.fields for r in result.rows) == 35
        assert sum("image_consent" in r.fields for r in result.rows) == 20
        assert all("Member.cluber_id" in r.fields for r in result.rows)

        text = repr(result) + repr(result.rows) + str(result.summary()) + caplog.text
        assert FALSE_IBAN not in text

    def test_sample_without_the_extra_type(self, db):
        result = cluber.preview(sample_file())
        by_price = [r for r in result.rows if r.member_type_by == "price"]
        # Sense el tipus «Juvenil», «col·laborador» i «juvenil» (35 €) van a «Simpatitzant».
        assert len(by_price) == 16 and {r.member_type for r in by_price} == {"supporter"}


class TestIbanNeverStored:
    """071, punt 2: el valor de l'IBAN no va enlloc."""

    def test_not_in_the_result_or_the_logs(self, db, caplog):
        caplog.set_level(logging.DEBUG)
        result = cluber.preview(sample_file())
        text = repr(result) + repr(result.rows) + str(result.summary()) + caplog.text
        text += str([vars(r) for r in result.rows]) + str(result.catalogue)
        assert FALSE_IBAN not in text

    def test_iban_value_too_long_is_not_an_error(self, db):
        # El valor s'esborra abans de cap comprovació: no hi ha cap error a la seva columna.
        headers = real_headers()
        long_value = "SENTINELLA-IBAN-7Q" * 600
        result = cluber.preview(build([record(1, {"IBAN": long_value})], headers=headers))
        row = only_row(result)
        assert not row.errors
        assert "SENTINELLA-IBAN" not in repr(result) + str(result.summary())

    def test_errors_never_carry_the_iban(self, db):
        rows = [
            record(1, {"IBAN": fake_iban(1), "Email": "-", "Data de Naixament": "x"}),
            record(1, {"IBAN": fake_iban(2)}),
        ]
        result = cluber.preview(build(rows, headers=real_headers()))
        messages = [str(cluber.MESSAGES[c]) for r in result.rows for c in r.errors + r.warnings]
        assert result.counts["with_errors"] == 2
        assert FALSE_IBAN not in str(messages) + str(result.summary())

    def test_nothing_is_written(self, db):
        cluber.preview(sample_file())
        assert ImportBatch.objects.count() == 0 and ImportLine.objects.count() == 0
        assert Member.objects.count() == 0 and AuditEntry.objects.count() == 0
        assert Consent.objects.count() == 0 and LegalText.objects.filter(kind="cluber").count() == 0

    def test_not_on_the_screen_or_in_the_audit_entry(self, db, make_admin, caplog):  # noqa: F811
        caplog.set_level(logging.DEBUG)
        client = admin_client(make_admin("administrator"))
        response = post(client, sample_file())
        assert response.status_code == 200
        html = response.content.decode()
        assert FALSE_IBAN not in html + caplog.text
        assert "Windows-1252" in html
        assert "Què s&#x27;importaria" in html or "Què s'importaria" in html
        [entry] = AuditEntry.objects.filter(action="members.cluber_import.preview")
        assert FALSE_IBAN not in str(entry.details)
        assert "file_sha256" not in entry.details


class TestScreen:
    def test_what_would_be_imported(self, db, make_admin):  # noqa: F811
        client = admin_client(make_admin("administrator"))
        records = [
            record(1, {"Quota": "Quota de soci ple dret 90€.", "Preu total": "90"}),
            record(2, {"Quota": "Quota de soci col·laborador 35€.", "Preu total": "35"}),
            record(3, {"Quota": "Quota familiar 50€."}),
        ]
        response = post(client, build(records))
        html = response.content.decode()
        assert "Codificació detectada: UTF-8" in html
        assert "Tots els socis importats entrarien actius." in html
        assert "Ple dret" in html and "pel nom" in html and "pel preu" in html
        rows = dict(response.context["would_import"])
        assert rows[cluber.FIELD_LABELS["Person.birth_date"]] == 3
        assert rows[cluber.FIELD_LABELS["image_consent"]] == 0
        assert sorted(response.context["types"]) == [
            ("Ple dret", "pel nom", 1),
            ("Simpatitzant", "pel preu", 1),
        ]
        for value in ("Quota de soci", "Quota familiar", "Prova1 Exemple", "15/03/2010"):
            assert value not in html
