"""Importació de Cluber, fase de prova (T-M01-24): lector CSV i previsualització.

Precisions aplicades: les files de la T-M01-24 a la lectura de les tasques substituïdes
(docs/planning.md#ajustos-060-lectura). Criteris: CA-M01-20, CA-M01-21; CA-20.1 a CA-20.4 i
CA-20.9 de la spec 00; L-M01-06.

Només dades inventades. Cap valor de cap exportació real: els fitxers es generen aquí, amb les
capçaleres de la mostra parcial (que no són dades personals) i valors inventats.
"""

import builtins
import csv
import datetime
import io
import logging

import pytest
from django.core import mail
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.models import Account
from apps.core.models import IMPORT_LINE_CODES, ImportBatch, ImportLine, Person
from apps.members.imports import cluber
from apps.members.imports.cluber_sample import dni
from apps.members.models import Member, MembershipType

DOCUMENT = "Document d'Identitat"

# Valors dels camps exclosos: no han d'aparèixer mai al resultat ni als registres.
SENTINELS = {
    "Soci titular": "SENTINELLA-TITULAR-7Q",
    "Informació addicional": "SENTINELLA-INFO-ADDICIONAL-7Q",
    "Professió;": "SENTINELLA-PROFESSIO-7Q",
    "Polítiques de privadesa": "SENTINELLA-POLITIQUES-7Q",
    "Mètode de pagament": "SENTINELLA-METODE-7Q",
    "Identificador": "SENTINELLA-IDENTIFICADOR-7Q",
    "idInterno": "SENTINELLA-IDINTERNO-7Q",
}

# La línia de capçalera de la mostra parcial, sense la columna IBAN (que es descarta, 071):
# tres noms porten un «;» entre cometes.
SAMPLE_HEADER_LINE = (
    "Nº Soci;Nom;Cognoms;Telèfon;Document d'Identitat;Quota;Preu total;Estat;Soci titular;"
    "Email;Data alta/renovació;Mètode de pagament;Adreça;Codi Postal;Ciutat;Província;"
    "Renovació;Polítiques de privadesa;Informació addicional;Identificador;Sector seient;"
    "Fila seient;Seient nº;Data d'inscripció;Data de Naixament;Edat;Telèfon fix;"
    '"Professió;";"Titulacio;";"Especialitats;";idInterno;CONSENTIMIENTO PARA USO DE IMÁGENES: '
    "Autorizo a la publicación de imágenes en redes sociales y página web del club/entidad. "
    "El club/entidad usará las imágenes solo para los fines autorizados y no las compartirá "
    "con terceros."
)


def record(n=1, values=None):
    row = {
        "Nº Soci": str(900 + n),
        "Nom": "Anna",
        "Cognoms": f"Prova{n} Exemple",
        "Telèfon": f"346000000{n:02d}",
        "Document d'Identitat": dni(n),
        "Quota": "Quota inventada A",
        "Preu total": "35",
        "Estat": "Estat inventat A",
        "Email": f"anna{n}@example.org",
        "Adreça": "Carrer Inventat, 1",
        "Codi Postal": "08001",
        "Ciutat": "-",
        "Renovació": "Renovació inventada A",
        "Data d'inscripció": "15/03/2010",
        "Data alta/renovació": "01/10/2026",
        "Data de Naixament": "02/05/1980",
        **SENTINELS,
    }
    row.update(values or {})
    return row


def build(records, headers=None, *, bom=False, newline="\r\n"):
    headers = list(cluber.KNOWN_HEADERS) if headers is None else headers
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";", lineterminator=newline)
    writer.writerow(headers)
    for row in records:
        writer.writerow([row.get(h, "") for h in headers])
    data = out.getvalue().encode("utf-8")
    return b"\xef\xbb\xbf" + data if bom else data


def only_row(result):
    assert result.rejected is None
    assert len(result.rows) == 1
    return result.rows[0]


@pytest.fixture
def supporter(db):
    return MembershipType.objects.get(code="supporter")


@pytest.fixture
def make_member(make_person, supporter):
    def make(person=None, **fields):
        fields.setdefault("type", supporter)
        fields.setdefault("joined_on", datetime.date(2026, 11, 4))
        return Member.objects.create(person=person or make_person(), **fields)

    return make


def person_with(make_person, number, kind=Person.DocumentType.DNI, **fields):
    return make_person(id_document_type=kind, id_document_number=number, **fields)


ANON_NAME = "SENTINELLA-ANON-NOM-7Q"
ANON_REF = "ANON-SENTINELLA-7Q"


def anonymised_member(make_person, make_member, number, document=""):
    """Soci d'una persona anonimitzada, amb el document buit o, si es dona, conservat."""
    fields = {"id_document_type": Person.DocumentType.DNI, "id_document_number": document}
    person = make_person(
        ANON_NAME,
        ANON_NAME,
        status=Person.Status.ANONYMISED,
        anonymous_ref=ANON_REF,
        **(fields if document else {}),
    )
    return make_member(
        person, member_number=number, status=Member.Status.LEFT, left_on=datetime.date(2024, 1, 1)
    )


class TestFileProfile:
    def test_correct_file(self, db):
        result = cluber.preview(build([record(1), record(2)]))
        assert result.rejected is None
        assert result.counts == {
            "rows": 2,
            "new": 2,
            "matching": 0,
            "ambiguous": 0,
            "conflict": 0,
            "with_errors": 0,
            "ready": 0,
            "left_in_cluber": 0,
        }
        first = result.rows[0]
        assert first.row == 2  # la capçalera és el registre 1
        # Només el que fa servir la previsualització: cap altra columna queda en memòria.
        assert first.data == {
            "member_number_text": "901",
            "member_number": 901,
            "id_document": dni(1),
            # 079 (A-25, RN-M01-95): el tipus es dedueix d'un DNI amb la lletra correcta.
            "id_document_type": "dni",
        }

    def test_ca_m01_107_a_valid_dni_or_nie_gives_the_type(self, db):
        # 079 (A-25, RN-M01-95): el tipus es dedueix quan el DNI o el NIE té la lletra correcta.
        row = only_row(cluber.preview(build([record(1, {"Quota": "Quota de soci ple dret"})])))
        assert not row.errors
        assert row.pending == []
        assert row.data["id_document_type"] == "dni"
        assert row.summary()["id_document_type"] == "dni"
        assert row.ready is True
        nie = only_row(cluber.preview(build([record(1, {"Document d'Identitat": "X1234567L"})])))
        assert nie.data["id_document_type"] == "nie" and "id_document_type" not in nie.pending

    @pytest.mark.parametrize("document", ["12345678A", "PASSAPORT01", "X1234567A"])
    def test_ca_m01_107_otherwise_the_type_stays_pending(self, db, document):
        values = {"Document d'Identitat": document, "Quota": "Quota de soci ple dret"}
        row = only_row(cluber.preview(build([record(1, values)])))
        assert row.pending == ["id_document_type"]
        assert "id_document_type" not in row.data
        assert row.summary()["id_document_type"] == ""
        assert row.ready is False

    def test_ca_m01_108_fingerprint_ignores_the_iban_and_the_encoding(self, db):
        # 079 (A-26, P-65 punt 1): SHA-256 de les columnes llegides, sense la d'IBAN.
        headers = [*cluber.KNOWN_HEADERS, "IBAN"]
        first = cluber.preview(build([record(1, {"IBAN": "ES0000000000000000000001"})], headers))
        second = cluber.preview(build([record(1, {"IBAN": "ES9999999999999999999999"})], headers))
        assert len(first.fingerprint) == 64
        assert first.fingerprint == second.fingerprint
        assert first.summary()["fingerprint"] == first.fingerprint
        other = cluber.preview(build([record(1, {"Ciutat": "Girona"})], headers))
        assert other.fingerprint != first.fingerprint
        plain = cluber.preview(build([record(1)]))
        with_bom = cluber.preview(build([record(1)], bom=True))
        assert plain.fingerprint == with_bom.fingerprint

    def test_bom_and_line_endings(self, db):
        plain = cluber.preview(build([record(1)]))
        for data in (build([record(1)], bom=True), build([record(1)], newline="\n")):
            result = cluber.preview(data)
            assert result.counts == plain.counts
            assert result.rows[0].data == plain.rows[0].data

    def test_sample_header_line_is_recognised(self, db):
        headers = next(csv.reader(io.StringIO(SAMPLE_HEADER_LINE), delimiter=";"))
        assert len(headers) == 32
        assert {"Professió;", "Titulacio;", "Especialitats;"} <= set(headers)
        result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected is None
        assert result.unknown_columns == []
        assert result.warnings == ["no_document_type"]

    def test_quotes_separators_and_multiline_fields(self, db):
        # L'adreça no es conserva: que la fila quedi ben llegida es veu en els camps de després.
        address = 'Carrer "Inventat"; 1\nPis 2'
        result = cluber.preview(build([record(1, {"Adreça": address}), record(2)]))
        assert result.counts["rows"] == 2
        assert not result.rows[0].errors
        assert result.rows[0].data["id_document"] == dni(1)
        assert result.rows[1].row == 3

    def test_blank_lines_are_skipped(self, db):
        data = build([record(1)]) + b"\r\n\r\n"
        assert cluber.preview(data).counts["rows"] == 1

    @pytest.mark.parametrize(
        ("data", "code"),
        [
            (b"", "empty"),
            (b"\xef\xbb\xbf", "empty"),
            (b" \r\n", "empty"),
            (build([]), "no_rows"),
            (b"N\x81 Soci;Nom", "encoding"),  # ni UTF-8 ni Windows-1252 (0x81 no hi és)
            (b'"Nom;Cognoms\r\nAnna;"Prova"x\r\n', "malformed"),
        ],
    )
    def test_rejected_files(self, db, data, code):
        result = cluber.preview(data)
        assert result.rejected == code
        assert result.rows == []

    def test_missing_required_header(self, db):
        headers = [h for h in cluber.KNOWN_HEADERS if h != "Document d'Identitat"]
        result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected == "missing_header"
        assert result.rejected_column == "Document d'Identitat"

    def test_repeated_header(self, db):
        headers = [*cluber.KNOWN_HEADERS, "Nom"]
        result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected == "duplicate_header"
        assert result.rejected_column == "Nom"

    def test_repeated_unknown_header_is_named_by_position(self, db):
        headers = [*cluber.KNOWN_HEADERS, "SENTINELLA-CAPCALERA-7Q", "SENTINELLA-CAPCALERA-7Q"]
        result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected == "duplicate_header"
        assert result.rejected_column == f"#{len(cluber.KNOWN_HEADERS) + 1}"
        assert "SENTINELLA-CAPCALERA" not in repr(result) + str(result.summary())

    @pytest.mark.parametrize("variant", ["nom", "​Nom", "No​m", "﻿Nom", " NOM "])
    def test_equivalent_headers_are_repeated(self, db, variant):
        # Mateixa representació que per a l'IBAN: sense U+FEFF ni U+200B, extrems i minúscules.
        headers = [*cluber.KNOWN_HEADERS, variant]
        result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected == "duplicate_header"

    def test_header_length_limit(self, db):
        ok = "SENTINELLA-CAPCALERA-7Q" + "x" * (cluber.MAX_FIELD - 23)
        assert len(ok) == cluber.MAX_FIELD
        result = cluber.preview(build([record(1)], headers=[*cluber.KNOWN_HEADERS, ok]))
        assert result.rejected is None
        headers = [*cluber.KNOWN_HEADERS, ok + "x"]
        with CaptureQueriesContext(connection) as queries:
            result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected == "field_too_long"
        assert (result.rejected_column, result.rejected_row) == (f"#{len(headers)}", 1)
        assert result.rows == []
        assert len(queries) == 1  # només CA-20.8
        assert "SENTINELLA-CAPCALERA" not in repr(result) + str(result.summary())

    def test_unknown_columns_are_a_warning(self, db):
        headers = [*cluber.KNOWN_HEADERS, "Columna nova"]
        result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected is None
        assert result.unknown_columns == ["Columna nova"]
        assert "unknown_columns" in result.warnings

    @pytest.mark.parametrize("delta", [1, -1])
    def test_row_with_more_or_fewer_fields(self, db, delta):
        data = build([record(1)]).decode("utf-8").rstrip("\r\n")
        data = data + ";x" if delta > 0 else data.rsplit(";", 1)[0]
        result = cluber.preview(data.encode("utf-8") + b"\r\n")
        row = only_row(result)
        assert row.errors == ["field_count"]
        assert row.data == {}
        assert row.ready is False


class TestLimits:
    def test_file_size_is_checked_before_decoding(self, db):
        data = b"\xff" * (cluber.MAX_BYTES + 1)  # ni tan sols és UTF-8
        assert cluber.preview(data).rejected == "too_large"

    def test_file_at_the_size_limit_is_read(self, db):
        data = build([record(1)])
        remaining = cluber.MAX_BYTES - len(data)
        data += b"\r\n" * (remaining // 2) + b"\n" * (remaining % 2)  # línies buides
        assert len(data) == cluber.MAX_BYTES
        assert cluber.preview(data).rejected is None

    def test_row_limit(self, db):
        records = [record(n) for n in range(1, cluber.MAX_ROWS + 2)]
        assert cluber.preview(build(records)).rejected == "too_many_rows"
        result = cluber.preview(build(records[:-1]))
        assert result.rejected is None
        assert result.counts["rows"] == cluber.MAX_ROWS

    # Les columnes que es llegeixen tenen el límit del camp de destinació (TestDocumentLength i
    # test_cluber_format.py); aquí, columnes que s'ignoren.
    @pytest.mark.parametrize("column", ["Informació addicional", "Província", "Telèfon fix"])
    def test_field_length_limit(self, db, column):
        long_ok = "a" * cluber.MAX_FIELD
        assert not only_row(cluber.preview(build([record(1, {column: long_ok})]))).errors
        row = only_row(cluber.preview(build([record(1, {column: long_ok + "a"})])))
        assert row.errors == ["field_too_long"]
        assert row.error_columns == [column]
        assert row.data == {}

    def test_field_limit_in_an_unknown_column(self, db):
        headers = [*cluber.KNOWN_HEADERS, "SENTINELLA-CAPCALERA-7Q"]
        values = {"SENTINELLA-CAPCALERA-7Q": "x" * (cluber.MAX_FIELD + 1)}
        result = cluber.preview(build([record(1, values)], headers=headers))
        row = only_row(result)
        assert row.error_columns == [f"#{len(headers)}"]
        assert "SENTINELLA-CAPCALERA" not in repr(result) + str(result.summary())

    def test_field_over_the_csv_module_limit(self, db):
        # Més llarg que el límit intern del mòdul csv (131.072), que no es canvia: el fitxer es
        # rebutja sencer i el resultat no en conté res.
        assert csv.field_size_limit() == 131_072
        value = "SENTINELLA-LLARG-7Q" * (131_072 // 19 + 1)
        assert len(value) > csv.field_size_limit()
        result = cluber.preview(build([record(1, {"Adreça": value})]))
        assert result.rejected == "malformed"
        assert result.rejected_row == 2
        assert result.rows == []
        assert "SENTINELLA-LLARG" not in repr(result) + str(result.summary())


class TestIban:
    """071: la columna d'IBAN es descarta en llegir; el fitxer no es rebutja (abans, RN-94)."""

    @pytest.mark.parametrize("header", ["IBAN", "iban", " Iban ", "IBAN "])
    @pytest.mark.parametrize("value", ["", "VALOR-INVENTAT"])
    def test_iban_column_is_discarded(self, db, header, value):
        headers = [*cluber.KNOWN_HEADERS, header]
        result = cluber.preview(build([record(1, {header: value})], headers=headers))
        assert result.rejected is None
        assert "iban_discarded" in result.warnings
        assert result.unknown_columns == []
        assert len(result.rows) == 1
        assert "VALOR-INVENTAT" not in repr(result) + repr(result.rows) + str(result.summary())

    def test_iban_as_first_column_after_bom(self, db):
        headers = ["IBAN", *cluber.KNOWN_HEADERS]
        result = cluber.preview(build([record(1)], headers=headers, bom=True))
        assert result.rejected is None and "iban_discarded" in result.warnings

    @pytest.mark.parametrize("header", ["Compte IBAN", "IBAN titular", "I.B.A.N."])
    def test_no_substring_search(self, db, header):
        # Comportament aprovat (sense àlies ni subcadena); risc conegut, documentat al pla.
        headers = [*cluber.KNOWN_HEADERS, header]
        result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected is None
        assert result.unknown_columns == [header]
        assert "iban_discarded" not in result.warnings

    @pytest.mark.parametrize("value", ["", "VALOR-INVENTAT"])
    @pytest.mark.parametrize(
        ("headers", "bom"),
        [
            (["\ufeffIBAN", *cluber.KNOWN_HEADERS], True),  # BOM doble a l'inici
            ([*cluber.KNOWN_HEADERS, "IB\u200bAN"], False),
            ([*cluber.KNOWN_HEADERS, "\u200bIBAN\u200b"], False),
            ([*cluber.KNOWN_HEADERS, " \ufeffiban "], False),
        ],
    )
    def test_invisible_characters_do_not_hide_the_iban_column(self, db, headers, bom, value):
        iban = next(h for h in headers if "IB" in h.upper())
        data = build([record(1, {iban: value})], headers=headers, bom=bom)
        if bom:
            assert data.startswith(b"\xef\xbb\xbf\xef\xbb\xbf")
        result = cluber.preview(data)
        assert result.rejected is None
        assert "iban_discarded" in result.warnings and result.unknown_columns == []
        assert "VALOR-INVENTAT" not in repr(result) + str(result.summary())


class TestMemberNumber:
    def test_leading_zeros_warn_and_compare_as_the_same_number(self, db):
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "00067"})])))
        assert row.data["member_number"] == 67
        assert row.data["member_number_text"] == "00067"
        assert "member_number_leading_zeros" in row.warnings
        assert not row.errors

    def test_67_and_00067_are_duplicates(self, db):
        records = [record(1, {"Nº Soci": "67"}), record(2, {"Nº Soci": "00067"})]
        result = cluber.preview(build(records))
        assert [r.errors for r in result.rows] == [
            ["duplicate_member_number"],
            ["duplicate_member_number"],
        ]

    def test_outer_spaces_and_upper_bound(self, db):
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": " 67 "})])))
        assert row.data["member_number"] == 67
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "2147483647"})])))
        assert row.data["member_number"] == 2147483647

    @pytest.mark.parametrize(
        "value",
        [
            "0",
            "00",
            "2147483648",
            "6.7",
            "67.0",
            "67,0",
            "-67",
            "+67",
            "6e1",
            "1E3",
            "6 7",
            "６７",
            "٦٧",
            "²",
            "0x43",
        ],
    )
    def test_invalid_forms(self, db, value):
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": value})])))
        assert row.errors == ["member_number_invalid"]
        assert "member_number" not in row.data
        assert row.ready is False

    def test_very_long_numbers_do_not_break_the_preview(self, db):
        # Python no converteix a enter més de 4.300 xifres: ha de ser un error de la fila.
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "9" * 5000})])))
        assert row.errors == ["member_number_invalid"]
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "0" * 5000 + "67"})])))
        assert row.data["member_number"] == 67
        assert "member_number_leading_zeros" in row.warnings

    def test_missing_number_is_pending(self, db):
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": ""})])))
        assert "member_number" in row.pending
        assert not row.errors


class TestDocumentLength:
    """El document normalitzat no supera la llargada de `Person.id_document_number`."""

    LIMIT = Person._meta.get_field("id_document_number").max_length

    def test_limit_accepted(self, db):
        row = only_row(cluber.preview(build([record(1, {DOCUMENT: "A" * self.LIMIT})])))
        assert not row.errors
        assert row.data["id_document"] == "A" * self.LIMIT

    def test_one_more_is_a_row_error_without_the_value(self, db):
        value = "SENTINELLA" + "B" * (self.LIMIT - 9)
        result = cluber.preview(build([record(1, {DOCUMENT: value})]))
        row = only_row(result)
        assert (row.errors, row.error_columns) == (["field_too_long"], [DOCUMENT])
        assert row.ready is False
        assert "SENTINELLA" not in repr(result) + str(result.summary())

    def test_length_counts_after_normalisation(self, db):
        value = "-".join(["AAAAA"] * 6) + "  ..."  # 34 caràcters; 30 sense separadors
        assert len(value) > self.LIMIT
        row = only_row(cluber.preview(build([record(1, {DOCUMENT: value})])))
        assert not row.errors
        assert row.data["id_document"] == "A" * self.LIMIT


class TestRowValues:
    def test_missing_values_are_pending_not_invented(self, db):
        values = {"Nom": "", "Cognoms": " ", "Email": "", "Telèfon": "", "Document d'Identitat": ""}
        row = only_row(cluber.preview(build([record(1, values)])))
        assert {"first_name", "last_name", "email", "phone", "id_document"} <= set(row.pending)
        assert "id_document_type" not in row.pending  # sense document, no cal el tipus
        assert row.data["id_document"] == ""
        assert not row.errors

    @pytest.mark.parametrize("email", ["-", "no-es-un-correu", "anna@"])
    def test_invalid_email_is_an_error(self, db, email):
        row = only_row(cluber.preview(build([record(1, {"Email": email})])))
        assert row.errors == ["email_invalid"]
        assert row.error_columns == ["Email"]

    def test_document_is_normalised_for_comparison(self, db):
        row = only_row(cluber.preview(build([record(1, {"Document d'Identitat": "0001-r"})])))
        assert row.data["id_document"] == "0001R"


class TestDuplicatesInTheFile:
    def test_same_document_marks_every_line(self, db):
        records = [
            record(1, {"Document d'Identitat": "00000001R"}),
            record(2, {"Document d'Identitat": "0000 0001-r"}),
            record(3),
        ]
        result = cluber.preview(build(records))
        assert [r.errors for r in result.rows] == [
            ["duplicate_document"],
            ["duplicate_document"],
            [],
        ]
        assert result.counts["with_errors"] == 2

    def test_identical_lines(self, db):
        result = cluber.preview(build([record(1), record(1)]))
        assert all(
            {"duplicate_document", "duplicate_member_number"} <= set(r.errors) for r in result.rows
        )


class TestMatchesWithTheDatabase:
    def test_document_of_any_type_matches_with_a_warning(self, db, make_person):
        person = person_with(make_person, dni(1), kind=Person.DocumentType.NIE)
        row = only_row(cluber.preview(build([record(1)])))
        assert row.identity == "matching"
        assert row.person_id == person.pk
        assert "match_without_document_type" in row.warnings
        assert Person.objects.count() == 1  # cap fusió ni cap assignació

    def test_two_people_with_the_number_is_ambiguous(self, db, make_person):
        person_with(make_person, dni(1), kind=Person.DocumentType.DNI)
        person_with(make_person, dni(1), kind=Person.DocumentType.PASSPORT)
        row = only_row(cluber.preview(build([record(1)])))
        assert row.identity == "ambiguous"
        assert row.person_id is None
        assert row.ready is False

    def test_member_number_matches(self, db, make_member):
        member = make_member(member_number=67)
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "00067"})])))
        assert row.identity == "matching"
        assert (row.person_id, row.member_id) == (member.person_id, member.pk)

    def test_document_and_number_of_the_same_person(self, db, make_person, make_member):
        member = make_member(person_with(make_person, dni(1)), member_number=67)
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "67"})])))
        assert row.identity == "matching"
        assert not row.errors
        assert row.member_id == member.pk

    def test_document_and_number_of_different_people(self, db, make_person, make_member):
        person_with(make_person, dni(1))
        make_member(member_number=67)
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "67"})])))
        assert row.identity == "conflict"
        assert row.errors == ["identity_conflict"]
        assert row.error_columns == [""]  # la relació entre tots dos, no un dels dos camps
        assert (row.person_id, row.member_id) == (None, None)

    def test_document_of_a_member_with_another_number(self, db, make_person, make_member):
        make_member(person_with(make_person, dni(1)), member_number=12)
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "67"})])))
        assert row.identity == "conflict"

    def test_number_of_a_member_with_another_document(self, db, make_person, make_member):
        make_member(person_with(make_person, dni(2)), member_number=67)
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "67"})])))
        assert row.identity == "conflict"
        # Regressió: abans s'indicava la columna del document, com si el document fos l'erroni.
        assert (row.errors, row.error_columns) == (["identity_conflict"], [""])

    def test_two_rows_can_resolve_to_the_same_person(self, db, make_person, make_member):
        # Decisió pendent abans de la confirmació (T-M01-25): aquí només es deixa constància
        # del comportament actual, sense fusió ni descart.
        person = person_with(make_person, dni(1))
        make_member(person, member_number=67)
        records = [
            record(1, {"Nº Soci": ""}),  # només pel document
            record(2, {"Nº Soci": "67", DOCUMENT: ""}),  # només pel número
        ]
        result = cluber.preview(build(records))
        assert [r.identity for r in result.rows] == ["matching", "matching"]
        assert {r.person_id for r in result.rows} == {person.pk}
        assert not any(r.errors for r in result.rows)

    def test_anonymised_people_do_not_match_by_document(self, db, make_person):
        person_with(
            make_person, dni(1), status=Person.Status.ANONYMISED, anonymous_ref="ANON-INVENTAT"
        )
        assert only_row(cluber.preview(build([record(1)]))).identity == "new"

    @pytest.mark.parametrize("account_status", [None, "pending", "disabled"])
    def test_former_member_not_anonymised_is_detected(
        self, db, make_person, make_member, account_status
    ):
        # «Activa» vol dir no anonimitzada: ni el compte ni la baixa del soci no hi compten.
        person = person_with(make_person, dni(1))
        if account_status:
            account = Account.objects.create_personal(person, "antiga@example.org")
            Account.objects.filter(pk=account.pk).update(status=account_status)
        member = make_member(
            person, member_number=67, status=Member.Status.LEFT, left_on=datetime.date(2025, 1, 1)
        )
        for number in ("67", ""):  # pel document i el número, i només pel document
            row = only_row(cluber.preview(build([record(1, {"Nº Soci": number})])))
            assert row.identity == "matching"
            assert (row.person_id, row.member_id) == (person.pk, member.pk)
        row = only_row(cluber.preview(build([record(2, {"Nº Soci": "67"})])))
        assert row.identity == "conflict"  # el número d'una antiga sòcia amb un altre document

    def test_queries_are_bounded(self, db, make_person):
        person_with(make_person, dni(3))
        data = build([record(n) for n in range(1, 51)])
        with CaptureQueriesContext(connection) as queries:
            cluber.preview(data)
        assert len(queries) <= 5  # CA-20.8, els tipus de soci i les tres de coincidències


class TestAnonymisedMemberNumber:
    """El número d'un soci d'una persona anonimitzada està ocupat: conflicte bloquejant."""

    def _check_blocked(self, result, *codes):
        row = only_row(result)
        assert row.identity == "conflict"
        assert set(row.errors) == {"member_number_unavailable", *codes}
        assert (row.person_id, row.member_id) == (None, None)
        assert row.ready is False
        counts = result.counts
        assert (counts["matching"], counts["ready"], counts["conflict"]) == (0, 0, 1)
        return row

    def test_empty_document_of_the_anonymised_person(self, db, make_person, make_member):
        anonymised_member(make_person, make_member, 67)
        self._check_blocked(cluber.preview(build([record(1, {"Nº Soci": "00067"})])))

    def test_row_without_document(self, db, make_person, make_member):
        anonymised_member(make_person, make_member, 67)
        values = {"Nº Soci": "67", "Document d'Identitat": ""}
        self._check_blocked(cluber.preview(build([record(1, values)])))

    def test_row_document_of_another_person(self, db, make_person, make_member):
        anonymised_member(make_person, make_member, 67)
        person_with(make_person, dni(1))
        result = cluber.preview(build([record(1, {"Nº Soci": "67"})]))
        self._check_blocked(result, "identity_conflict")  # els dos conflictes es mantenen

    def test_row_document_ambiguous(self, db, make_person, make_member):
        anonymised_member(make_person, make_member, 67)
        person_with(make_person, dni(1), kind=Person.DocumentType.DNI)
        person_with(make_person, dni(1), kind=Person.DocumentType.NIE)
        result = cluber.preview(build([record(1, {"Nº Soci": "67"})]))
        self._check_blocked(result, "identity_conflict")

    def test_anonymised_person_kept_the_same_document(self, db, make_person, make_member):
        # Encara que el document coincideixi, no és una coincidència utilitzable.
        anonymised_member(make_person, make_member, 67, document=dni(1))
        self._check_blocked(cluber.preview(build([record(1, {"Nº Soci": "67"})])))

    def test_nothing_about_the_anonymised_person_is_exposed(
        self, db, make_person, make_member, caplog
    ):
        caplog.set_level(logging.DEBUG)
        member = anonymised_member(make_person, make_member, 67)
        result = cluber.preview(build([record(1, {"Nº Soci": "67"})]))
        text = repr(result) + repr(result.rows) + str(result.summary()) + caplog.text
        for value in (ANON_NAME, ANON_REF, f"person_id={member.person_id}"):
            assert value not in text
        assert f"member_id={member.pk}" not in text
        assert cluber.MESSAGES["member_number_unavailable"]

    def test_the_anonymised_member_is_not_touched(self, db, make_person, make_member):
        member = anonymised_member(make_person, make_member, 67)
        before = (
            list(Person.objects.filter(pk=member.person_id).values()),
            list(Member.objects.filter(pk=member.pk).values()),
        )
        with CaptureQueriesContext(connection) as queries:
            cluber.preview(build([record(1, {"Nº Soci": "67"})]))
        assert all(q["sql"].lstrip().upper().startswith("SELECT") for q in queries)
        assert len(queries) <= 5  # CA-20.8, els tipus de soci i les tres de coincidències
        after = (
            list(Person.objects.filter(pk=member.person_id).values()),
            list(Member.objects.filter(pk=member.pk).values()),
        )
        assert after == before

    def test_former_member_not_anonymised_still_matches(self, db, make_person, make_member):
        # No regressió: la regla només val per a persones anonimitzades.
        person = person_with(make_person, dni(1))
        member = make_member(
            person, member_number=67, status=Member.Status.LEFT, left_on=datetime.date(2025, 1, 1)
        )
        result = cluber.preview(build([record(1, {"Nº Soci": "67"})]))
        row = only_row(result)
        assert row.identity == "matching"
        assert "member_number_unavailable" not in row.errors
        assert (row.person_id, row.member_id) == (person.pk, member.pk)
        assert result.counts["matching"] == 1


def make_batch(account, status, kind=ImportBatch.Kind.CLUBER):
    # Totes les dates surten d'un sol instant: amb crides separades a now(), `created_at` (que
    # es calcula dins de create()) podia quedar després de `confirmed_at` (CI #92 i #93).
    base = timezone.now()
    values = {
        "kind": kind,
        "status": status,
        "file_sha256": "0" * 64,
        "created_by": account,
        "created_at": base,
    }
    if status in (ImportBatch.Status.CONFIRMED, ImportBatch.Status.UNDONE):
        values.update(confirmed_by=account, confirmed_at=base + datetime.timedelta(minutes=1))
    if status == ImportBatch.Status.UNDONE:
        values.update(undone_by=account, undone_at=base + datetime.timedelta(minutes=2))
    return ImportBatch.objects.create(**values)


@pytest.mark.parametrize("status", ["preview", "confirmed", "undone", "rejected"])
def test_make_batch_chronology(db, admin_account, status):
    # Regressió del CI #92 i #93: cronologia determinista, sense dependre del rellotge.
    batch = make_batch(admin_account, status)
    batch.refresh_from_db()
    minute = datetime.timedelta(minutes=1)
    if batch.confirmed_at:
        assert batch.confirmed_at - batch.created_at == minute
    if batch.undone_at:
        assert batch.undone_at - batch.confirmed_at == minute


class TestAlreadyImported:
    """CA-20.8: amb una importació final de Cluber confirmada, una prova nova es rebutja."""

    def test_confirmed_cluber_batch_rejects_before_reading(self, db, admin_account):
        make_batch(admin_account, ImportBatch.Status.CONFIRMED)
        # Ni tan sols és UTF-8: si es descodifiqués, el rebuig seria «encoding».
        with CaptureQueriesContext(connection) as queries:
            result = cluber.preview(b"\xff\xfe" + build([record(1)]))
        assert result.rejected == "cluber_already_imported"
        assert result.rows == [] and result.catalogue == {} and result.unknown_columns == []
        assert len(queries) == 1
        assert queries[0]["sql"].lstrip().upper().startswith("SELECT")
        assert "cluber_already_imported" in cluber.MESSAGES

    def test_size_is_checked_first(self, db, admin_account):
        make_batch(admin_account, ImportBatch.Status.CONFIRMED)
        with CaptureQueriesContext(connection) as queries:
            result = cluber.preview(b"x" * (cluber.MAX_BYTES + 1))
        assert result.rejected == "too_large"
        assert len(queries) == 0

    @pytest.mark.parametrize(
        ("status", "kind"),
        [
            ("undone", "cluber"),
            ("preview", "cluber"),
            ("rejected", "cluber"),
            ("confirmed", "bank_statement"),
        ],
    )
    def test_other_batches_do_not_block(self, db, admin_account, status, kind):
        make_batch(admin_account, status, kind)
        result = cluber.preview(build([record(1)]))
        assert result.rejected is None
        assert result.counts["rows"] == 1

    def test_row_codes_of_the_service_are_allowed_in_lines(self):
        file_level = {
            "too_large",
            "encoding",
            "empty",
            "malformed",
            "iban_discarded",
            "duplicate_header",
            "missing_header",
            "no_rows",
            "too_many_rows",
            "no_document_type",
            "unknown_columns",
            "cluber_already_imported",
            # Excel (081, punt 23): de tot el fitxer
            "xlsx_invalid",
            "xlsx_active_content",
            "xlsx_formula",
            "xlsx_several_sheets",
        }
        # Els codis de la T-M01-24b («date_invalid», «total_price_differs») hi són des de la
        # migració core/0012 de la T-M01-25 (071).
        # «last_renewal» (T-M01-25b) no es desa a la línia fins que una migració de core l'afegeixi
        # (`final._codes`).
        assert set(cluber.MESSAGES) - file_level - {"last_renewal"} <= set(IMPORT_LINE_CODES)
        assert {"date_invalid", "total_price_differs"} <= set(IMPORT_LINE_CODES)


NUL_VALUE = "SENTINELLA-NUL-7Q\x00X"


def with_nul(where):
    """Fitxer correcte, amb un NUL al lloc indicat (dades inventades)."""
    headers = [*cluber.KNOWN_HEADERS, "Columna nova"]
    if where == "header":
        headers[1] = "No\x00m"
        return build([record(1)], headers=headers)
    column = {
        "document": "Document d'Identitat",
        "used": "Email",
        "excluded": "Informació addicional",
        "unknown": "Columna nova",
    }[where]
    return build([record(1, {column: NUL_VALUE}), record(2)], headers=headers)


class TestNulCharacter:
    """Un NUL fa rebutjar el fitxer sencer abans de llegir cap registre (abans, `DataError`)."""

    @pytest.mark.parametrize("where", ["document", "used", "excluded", "unknown", "header"])
    def test_rejected_before_any_row_or_match(self, db, caplog, where):
        caplog.set_level(logging.DEBUG)
        with CaptureQueriesContext(connection) as queries:
            result = cluber.preview(with_nul(where))
        assert result.rejected == "malformed"
        assert (result.rows, result.catalogue, result.unknown_columns) == ([], {}, [])
        # Només la consulta de CA-20.8: cap consulta de coincidències.
        assert len(queries) == 1
        assert '"core_importbatch"' in queries[0]["sql"]
        text = repr(result) + str(result.summary()) + caplog.text
        assert "SENTINELLA-NUL" not in text and "\x00" not in text

    def test_size_and_already_imported_keep_priority(self, db, admin_account):
        big = with_nul("document") + b" " * cluber.MAX_BYTES
        assert cluber.preview(big).rejected == "too_large"
        make_batch(admin_account, ImportBatch.Status.CONFIRMED)
        assert cluber.preview(with_nul("document")).rejected == "cluber_already_imported"


class TestExcludedColumnsAndCatalogue:
    def test_sentinels_never_reach_the_result_or_the_logs(self, db, caplog):
        caplog.set_level(logging.DEBUG)
        records = [record(1), record(2, {"Email": "-", "Nº Soci": "6.7"}), record(2)]
        result = cluber.preview(build(records))
        text = repr(result) + caplog.text
        for value in SENTINELS.values():
            assert value not in text

    def test_errors_carry_no_values(self, db):
        row = only_row(cluber.preview(build([record(1, {"Email": "-", "Nº Soci": "6.7"})])))
        assert set(row.errors) == {"email_invalid", "member_number_invalid"}
        assert set(row.error_columns) == {"Email", "Nº Soci"}
        assert all(code in cluber.MESSAGES for code in row.errors + row.warnings + row.pending)

    def test_catalogue_values_are_counted_but_not_logged(self, db, caplog):
        caplog.set_level(logging.DEBUG)
        records = [record(1), record(2), record(3, {"Quota": "Quota inventada B"})]
        result = cluber.preview(build(records))
        assert result.catalogue == {"Quota": {"Quota inventada A": 2, "Quota inventada B": 1}}
        assert "Quota inventada" not in caplog.text

    def test_ignored_columns_keep_no_catalogue(self, db):
        # 071: «Estat» i «Renovació» ja no es fan servir i no se'n conserva cap valor.
        records = [record(1, {"Estat": "SENTINELLA-ESTAT-7Q", "Renovació": "SENTINELLA-REN-7Q"})]
        result = cluber.preview(build(records))
        assert set(result.catalogue) == {"Quota"}
        assert "SENTINELLA" not in str(result.catalogue) + str(result.summary())

    def test_catalogue_detail_is_limited_and_the_omission_is_explicit(self, db):
        def with_quotas(count):
            return [record(n, {"Quota": f"Quota {n}"}) for n in range(1, count + 1)]

        result = cluber.preview(build(with_quotas(cluber.MAX_CATALOGUE)))
        assert len(result.catalogue["Quota"]) == cluber.MAX_CATALOGUE
        assert result.catalogue_omitted == {}
        result = cluber.preview(build(with_quotas(cluber.MAX_CATALOGUE + 1)))
        assert "Quota" not in result.catalogue
        assert result.catalogue_omitted == {"Quota": cluber.MAX_CATALOGUE + 1}
        assert result.summary()["catalogue_omitted"] == {"Quota": cluber.MAX_CATALOGUE + 1}


class TestSafeSummary:
    """`repr` i `summary()` sense valors del fitxer; l'objecte intern sí que en té alguns."""

    USED = {
        "Nº Soci": "00067",
        "Nom": "SENTINELLA-NOM-7Q",
        "Cognoms": "SENTINELLA-COGNOMS-7Q",
        "Telèfon": "34611122233",
        "Document d'Identitat": "SENTINELLA-DOC-7Q",
        "Email": "sentinella-correu-7q@example.org",
        "Adreça": "SENTINELLA-ADRECA-7Q",
        "Quota": "SENTINELLA-QUOTA-7Q",
    }
    HIDDEN = (
        "SENTINELLA",
        "SENTINELLADOC7Q",
        "sentinella-correu",
        "34611122233",
        "00067",
    )

    def _result(self):
        headers = [*cluber.KNOWN_HEADERS, "SENTINELLA-CAPCALERA-7Q"]
        records = [record(1, self.USED), record(2, {**self.USED, "Email": "-"})]
        return cluber.preview(build(records, headers=headers))

    def test_repr_and_summary_show_no_values(self, db):
        result = self._result()
        text = repr(result) + repr(result.rows) + str(result.summary())
        for value in self.HIDDEN:
            assert value not in text

    def test_internal_result_keeps_only_what_the_preview_uses(self, db):
        result = self._result()
        assert result.rows[0].data == {
            "member_number_text": "00067",
            "member_number": 67,
            "id_document": "SENTINELLADOC7Q",
        }
        assert result.catalogue["Quota"] == {"SENTINELLA-QUOTA-7Q": 2}
        assert result.unknown_columns == ["SENTINELLA-CAPCALERA-7Q"]

    def test_summary_contents(self, db):
        summary = self._result().summary()
        assert summary["rejected"] is None
        assert summary["counts"]["rows"] == 2
        assert summary["unknown_columns"] == 1
        assert summary["catalogue"]["Quota"] == 1  # nombre de valors diferents, sense valors
        # Les dues files tenen el mateix document i número; la segona, a més, un correu invàlid.
        assert summary["rows"][1] == {
            "row": 3,
            "identity": "new",
            "ready": False,
            "id_document_type": "",
            "errors": ["email_invalid", "duplicate_document", "duplicate_member_number"],
            "error_columns": ["Email", "Document d'Identitat", "Nº Soci"],
            "warnings": ["member_number_leading_zeros"],
            "pending": ["id_document_type", "member_type"],
            "fields": [
                "Member.cluber_id",
                "Member.joined_on",
                "Member.member_number",
                "Person.address",
                "Person.birth_date",
                "Person.first_name",
                "Person.id_document_number",
                "Person.last_name",
                "Person.phone",
                "last_renewal",
            ],
            "member_type": None,
            "member_type_by": None,
            "left_in_cluber": False,
        }
        assert summary["encoding"] == "utf-8"
        assert summary["type_names"] == {"supporter": "Simpatitzant", "full": "Ple dret"}


class TestNoWrites:
    """CA-M01-20 amb abast sobre `preview()`: cap escriptura ni cap efecte lateral."""

    @pytest.fixture
    def existing(self, make_person, make_member):
        make_member(person_with(make_person, dni(1)), member_number=901)
        make_member(person_with(make_person, dni(5)), member_number=12)
        anonymised_member(make_person, make_member, 77)
        # Lots i línies existents (un d'undone i un de previsualització, que no bloquegen).
        account = Account.objects.create_admin(make_person(), "lots.inventat", None)
        for status in (ImportBatch.Status.UNDONE, ImportBatch.Status.PREVIEW):
            batch = make_batch(account, status)
            ImportLine.objects.create(
                batch=batch, row=2, result="matching", person=Person.objects.first()
            )
            ImportLine.objects.create(batch=batch, row=3, result="error", codes=["field_count"])

    def _table_counts(self):
        with connection.cursor() as cursor:
            counts = {}
            for table in connection.introspection.table_names():
                cursor.execute(f'SELECT COUNT(*) FROM "{table}"')  # noqa: S608
                counts[table] = cursor.fetchone()[0]
            return counts

    def _snapshot(self):
        return (
            list(Person.objects.order_by("pk").values()),
            list(Member.objects.order_by("pk").values()),
            list(ImportBatch.objects.order_by("pk").values()),
            list(ImportLine.objects.order_by("pk").values()),
        )

    def _pg_state(self):
        # Evidència complementària: canvis de files de la transacció i valors de les seqüències.
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COALESCE(SUM(n_tup_ins + n_tup_upd + n_tup_del), 0)"
                " FROM pg_stat_xact_user_tables"
            )
            changes = cursor.fetchone()[0]
            cursor.execute("SELECT sequencename, last_value FROM pg_sequences ORDER BY 1")
            return changes, cursor.fetchall()

    def _files(self):
        return [
            build([record(1), record(2), record(3, {"Document d'Identitat": dni(5)})]),
            build([record(1), record(1)]),
            build([record(4, {"Nº Soci": "77"})]),  # número d'un soci d'una persona anonimitzada
            build([record(1)], headers=[*cluber.KNOWN_HEADERS, "IBAN"]),
            with_nul("document"),
            b"",
        ]

    def test_only_selects_and_nothing_changes(self, db, existing):
        before = (self._table_counts(), self._snapshot(), self._pg_state())
        for data in self._files():
            with CaptureQueriesContext(connection) as queries:
                cluber.preview(data)
            for query in queries:
                sql = query["sql"].lstrip().upper()
                assert sql.startswith("SELECT"), sql
                assert "FOR UPDATE" not in sql and "NEXTVAL" not in sql
        after = (self._table_counts(), self._snapshot(), self._pg_state())
        assert after == before

    def test_no_mail_and_no_files_opened(self, db, existing, monkeypatch):
        def no_files(*args, **kwargs):
            raise AssertionError("preview() no obre cap fitxer")

        monkeypatch.setattr(builtins, "open", no_files)
        monkeypatch.setattr(io, "open", no_files)
        for data in self._files():
            cluber.preview(data)
        assert mail.outbox == []
