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

from apps.core.models import Person
from apps.members.imports import cluber
from apps.members.models import Member, MembershipType

LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"

# Valors dels camps exclosos: no han d'aparèixer mai al resultat ni als registres.
SENTINELS = {
    "Soci titular": "SENTINELLA-TITULAR-7Q",
    "Informació addicional": "SENTINELLA-INFO-ADDICIONAL-7Q",
    "Professió;": "SENTINELLA-PROFESSIO-7Q",
    "Polítiques de privadesa": "SENTINELLA-POLITIQUES-7Q",
    "Data de Naixament": "SENTINELLA-NAIXEMENT-7Q",
    "Mètode de pagament": "SENTINELLA-METODE-7Q",
    "Identificador": "SENTINELLA-IDENTIFICADOR-7Q",
    "idInterno": "SENTINELLA-IDINTERNO-7Q",
}

# La línia de capçalera de la mostra parcial, sense la columna IBAN (que la rebutjaria):
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


def dni(n):
    """Document amb el format d'un DNI i la lletra correcta, inventat."""
    return f"{n:08d}{LETTERS[n % 23]}"


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
        }
        first = result.rows[0]
        assert first.row == 2  # la capçalera és el registre 1
        assert first.data["first_name"] == "Anna"
        assert first.data["id_document"] == dni(1)
        assert first.data["member_number"] == 901

    def test_no_row_is_ready_without_approved_equivalences(self, db):
        row = only_row(cluber.preview(build([record(1)])))
        assert not row.errors
        assert {"member_type", "member_status", "joined_on", "id_document_type"} <= set(row.pending)
        assert row.ready is False

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
        address = 'Carrer "Inventat"; 1\nPis 2'
        result = cluber.preview(build([record(1, {"Adreça": address}), record(2)]))
        assert result.counts["rows"] == 2
        assert result.rows[0].data["address"] == address
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
            ("Nº Soci;Nom".encode("cp1252"), "encoding"),
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

    def test_field_length_limit(self, db):
        long_ok = "a" * cluber.MAX_FIELD
        assert not only_row(cluber.preview(build([record(1, {"Adreça": long_ok})]))).errors
        row = only_row(cluber.preview(build([record(1, {"Adreça": long_ok + "a"})])))
        assert row.errors == ["field_too_long"]
        assert row.error_columns == ["Adreça"]
        assert row.data == {}


class TestIban:
    @pytest.mark.parametrize("header", ["IBAN", "iban", " Iban ", "IBAN "])
    @pytest.mark.parametrize("value", ["", "VALOR-INVENTAT"])
    def test_iban_column_rejects_the_whole_file(self, db, header, value):
        headers = [*cluber.KNOWN_HEADERS, header]
        result = cluber.preview(build([record(1, {header: value})], headers=headers))
        assert result.rejected == "iban_column"
        assert result.rows == []
        assert "VALOR-INVENTAT" not in repr(result)

    def test_iban_as_first_column_after_bom(self, db):
        headers = ["IBAN", *cluber.KNOWN_HEADERS]
        result = cluber.preview(build([record(1)], headers=headers, bom=True))
        assert result.rejected == "iban_column"

    def test_rejected_before_processing_data_rows(self, db):
        # Després de la capçalera hi ha una fila amb unes cometes sense tancar: si es
        # processés, el resultat seria «malformed». Tampoc no es fa cap consulta.
        header = build([], headers=[*cluber.KNOWN_HEADERS, "IBAN"])
        data = header + b'901;"sense tancar\r\n'
        with CaptureQueriesContext(connection) as queries:
            result = cluber.preview(data)
        assert result.rejected == "iban_column"
        assert len(queries) == 0

    @pytest.mark.parametrize("header", ["Compte IBAN", "IBAN titular", "I.B.A.N."])
    def test_no_substring_search(self, db, header):
        # Comportament aprovat (sense àlies ni subcadena); risc conegut, documentat al pla.
        headers = [*cluber.KNOWN_HEADERS, header]
        result = cluber.preview(build([record(1)], headers=headers))
        assert result.rejected is None
        assert result.unknown_columns == [header]


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

    def test_missing_number_is_pending(self, db):
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": ""})])))
        assert "member_number" in row.pending
        assert not row.errors


class TestRowValues:
    def test_missing_values_are_pending_not_invented(self, db):
        values = {"Nom": "", "Cognoms": " ", "Email": "", "Telèfon": "", "Document d'Identitat": ""}
        row = only_row(cluber.preview(build([record(1, values)])))
        assert {"first_name", "last_name", "email", "phone", "id_document"} <= set(row.pending)
        assert "id_document_type" not in row.pending  # sense document, no cal el tipus
        assert row.data["first_name"] == "" and row.data["email"] == ""
        assert not row.errors

    @pytest.mark.parametrize("email", ["-", "no-es-un-correu", "anna@"])
    def test_invalid_email_is_an_error(self, db, email):
        row = only_row(cluber.preview(build([record(1, {"Email": email})])))
        assert row.errors == ["email_invalid"]
        assert row.error_columns == ["Email"]

    def test_values_keep_their_text(self, db):
        values = {"Telèfon": "34600000001", "Document d'Identitat": "0001-r"}
        row = only_row(cluber.preview(build([record(1, values)])))
        assert row.data["phone"] == "34600000001"  # sense afegir cap «+»
        assert row.data["id_document"] == "0001R"
        assert row.data["id_document_text"] == "0001-r"


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
        assert (row.person_id, row.member_id) == (None, None)

    def test_document_of_a_member_with_another_number(self, db, make_person, make_member):
        make_member(person_with(make_person, dni(1)), member_number=12)
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "67"})])))
        assert row.identity == "conflict"

    def test_number_of_a_member_with_another_document(self, db, make_person, make_member):
        make_member(person_with(make_person, dni(2)), member_number=67)
        row = only_row(cluber.preview(build([record(1, {"Nº Soci": "67"})])))
        assert row.identity == "conflict"

    def test_anonymised_people_do_not_match_by_document(self, db, make_person):
        person_with(
            make_person, dni(1), status=Person.Status.ANONYMISED, anonymous_ref="ANON-INVENTAT"
        )
        assert only_row(cluber.preview(build([record(1)]))).identity == "new"

    def test_queries_are_bounded(self, db, make_person):
        person_with(make_person, dni(3))
        data = build([record(n) for n in range(1, 51)])
        with CaptureQueriesContext(connection) as queries:
            cluber.preview(data)
        assert len(queries) <= 3


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
        records = [record(1), record(2), record(3, {"Estat": "Estat inventat B"})]
        result = cluber.preview(build(records))
        assert result.catalogue["Estat"] == {"Estat inventat A": 2, "Estat inventat B": 1}
        assert result.catalogue["Quota"] == {"Quota inventada A": 3}
        assert "Estat inventat" not in caplog.text

    def test_a_column_with_too_many_values_is_not_a_catalogue(self, db):
        records = [record(n, {"Estat": f"Estat {n}"}) for n in range(1, cluber.MAX_CATALOGUE + 2)]
        result = cluber.preview(build(records))
        assert result.catalogue["Estat"] == cluber.MAX_CATALOGUE + 1  # només el recompte


class TestNoWrites:
    """CA-M01-20 amb abast sobre `preview()`: cap escriptura ni cap efecte lateral."""

    @pytest.fixture
    def existing(self, make_person, make_member):
        make_member(person_with(make_person, dni(1)), member_number=901)
        make_member(person_with(make_person, dni(5)), member_number=12)

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
            build([record(1)], headers=[*cluber.KNOWN_HEADERS, "IBAN"]),
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
