"""Importació de l'extracte bancari, primera part: lectura, validació i previsualització (T-M00-01;
spec 00, HU-21, CA-21.1, CA-21.2 i CA-21.5; RN-92, RN-96, RN-98, RN-101; V-06). Només dades
inventades: cap IBAN, nom ni concepte real.
"""

import datetime
import json

import pytest
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction

from apps.core import imports
from apps.core.imports import bank_statement as bs
from apps.core.models import IMPORT_LINE_CODES, AuditEntry, ImportBatch, ImportLine
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db

# IBAN de mostra de la documentació (no és de ningú), un compte antic i una targeta de proves.
IBAN = "ES91 2100 0418 4502 0005 1332"
OLD_ACCOUNT = "2100-0418-45-0200051332"
CARD = "4111 1111 1111 1111"
HEADER = "Data;Concepte;Import;Saldo;IBAN contrapart"
CARD_ROW = f"04/11/2026;PAGAMENT TARGETA {CARD};-7,00;1.030,70;"


def csv_file(*rows, header=HEADER):
    return "\n".join([header, *rows]).encode("utf-8")


STATEMENT = csv_file(
    f"02/11/2026;TRANSF CRIS-AB2CD-K DE PROVA INVENTADA {IBAN};50,00;1.050,00;{IBAN}",
    f"03/11/2026;REBUT LLUM {OLD_ACCOUNT};-12,30;1.037,70;",
    CARD_ROW,
)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def imported(by, *lines, status="confirmed"):
    """Lot d'extracte ja confirmat amb aquestes línies noves (confirmar és de la segona part)."""
    batch = imports.open_confirmed(
        "bank_statement", file_sha256="0" * 64, by=by, counts={"new_count": len(lines)}
    )
    imports.add_lines(
        batch, [{"row": n, "result": "new", **line} for n, line in enumerate(lines, start=2)]
    )
    if status != "confirmed":
        ImportBatch.objects.filter(pk=batch.pk).update(
            status=status, undone_by=by, undone_at=batch.confirmed_at
        )
    return batch


def card_line(**changes):
    return {
        "value_date": datetime.date(2026, 11, 4),
        "amount_cents": -700,
        "concept": f"PAGAMENT TARGETA {bs.MASK}",
        "balance_cents": 103070,
        **changes,
    }


def stored(line):
    return {
        "value_date": datetime.date.fromisoformat(line["date"]),
        "amount_cents": line["amount"],
        "concept": line["concept"],
        "balance_cents": line["balance"],
    }


def leaks_account_numbers(text):
    digits = "".join(text.split()).replace("-", "")
    return any("".join(n.split()).replace("-", "") in digits for n in (IBAN, OLD_ACCOUNT, CARD))


class TestPreview:
    def test_ca_21_1_validated_lines_and_nothing_written(self, treasurer):
        result = bs.preview(STATEMENT, by=treasurer)
        assert [(x["row"], x["date"], x["amount"], x["balance"]) for x in result["lines"]] == [
            (2, "2026-11-02", 5000, 105000),
            (3, "2026-11-03", -1230, 103770),
            (4, "2026-11-04", -700, 103070),
        ]
        assert result["lines"][0]["concept"] == f"TRANSF CRIS-AB2CD-K DE PROVA INVENTADA {bs.MASK}"
        assert result["counts"] == {"new": 3, "duplicate": 0, "error": 0}
        assert not ImportBatch.objects.exists() and not ImportLine.objects.exists()
        entry = AuditEntry.objects.get(action=bs.audit.Action.BANK_STATEMENT_PREVIEW)
        assert entry.actor_account == treasurer
        assert entry.details["counts"] == result["counts"]
        assert len(entry.details["file_sha256"]) == 64  # RN-101: només l'empremta

    def test_no_iban_account_or_card_number_in_lines_token_or_log(self, treasurer):
        result = bs.preview(STATEMENT, by=treasurer)
        assert all(bs.MASK in line["concept"] for line in result["lines"])
        payload = signing.loads(result["token"], salt=bs._SALT)
        assert payload["by"] == treasurer.pk
        assert not leaks_account_numbers(json.dumps(payload))
        for entry in AuditEntry.objects.all():
            assert not leaks_account_numbers(json.dumps(entry.details))

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("Pagament ES9121000418450200051332 fet", f"Pagament {bs.MASK} fet"),
            ("compte 2100 0418 45 0200051332", f"compte {bs.MASK}"),
            (f"{IBAN} CRIS-AB2CD-K", f"{bs.MASK} CRIS-AB2CD-K"),
            ("de NL91 ABNA 0417 1643 00 x", f"de {bs.MASK} x"),
            ("gb29 nwbk 6016 1331 9268 19 FET", f"{bs.MASK} FET"),
            ("ES12 nota de la quota 2026", "ES12 nota de la quota 2026"),
            ("  CRIS-AB2CD-K   Joan  Inventat\n", "CRIS-AB2CD-K Joan Inventat"),
            ("Factura 2026-123", "Factura 2026-123"),
        ],
    )
    def test_mask(self, text, expected):
        assert bs.mask(text) == expected

    def test_mask_cuts_to_the_column(self):
        assert len(bs.mask("x" * 400)) == ImportLine._meta.get_field("concept").max_length

    def test_lines_with_errors_keep_no_values(self, treasurer):
        data = csv_file(
            "31/02/2026;Data impossible;5,00;1,00;",
            "01/11/2026;Import dolent;5,0,0;1,00;",
            "01/11/2026;Saldo dolent;5,00;;",
            "01/11/2026;Falta una columna;5,00",
            "01/11/2026;Correcta;5,00;6,00;",
        )
        lines = bs.preview(data, by=treasurer)["lines"]
        assert [line["codes"] for line in lines] == [
            ["date_invalid"],
            ["amount_invalid"],
            ["balance_invalid"],
            ["field_count"],
            [],
        ]
        assert [line["result"] for line in lines] == ["error"] * 4 + ["new"]
        assert all(set(line) == {"row", "codes", "result"} for line in lines[:4])
        assert set(bs.LINE_MESSAGES) <= set(IMPORT_LINE_CODES)

    def test_blank_lines_are_skipped_and_header_is_case_insensitive(self, treasurer):
        data = csv_file("", "01/11/2026;Quota;5,00;6,00;", " ; ; ; ; ", header=HEADER.upper())
        assert [line["row"] for line in bs.preview(data, by=treasurer)["lines"]] == [3]

    def test_profile_without_balance(self, treasurer, settings):
        settings.BANK_STATEMENT_CSV_PROFILE = {
            **settings.BANK_STATEMENT_CSV_PROFILE,
            "balance": "",
            "delimiter": ",",
            "decimal": ".",
            "date_format": "%Y-%m-%d",
        }
        data = b'Data,Concepte,Import\n2026-11-01,Quota,"1,234.50"\n'
        (line,) = bs.preview(data, by=treasurer)["lines"]
        assert (line["date"], line["amount"], line["balance"]) == ("2026-11-01", 123450, None)

    def test_needs_m9(self, make_admin):  # noqa: F811
        for role in ("administrator", "secretary", "president"):
            with pytest.raises(PermissionDenied):
                bs.preview(STATEMENT, by=make_admin(role))
        assert not AuditEntry.objects.filter(action=bs.audit.Action.BANK_STATEMENT_PREVIEW)


class TestDuplicates:
    def test_ca_21_2_lines_of_a_confirmed_statement_are_duplicates(self, treasurer):
        imported(treasurer, card_line())
        data = csv_file(
            CARD_ROW,
            "05/11/2026;Quota inventada;30,00;1.060,70;",
            "05/11/2026;Quota inventada;30,00;1.060,70;",  # repetida al mateix fitxer
        )
        result = bs.preview(data, by=treasurer)
        assert [line["result"] for line in result["lines"]] == ["duplicate", "new", "duplicate"]
        assert result["counts"] == {"new": 1, "duplicate": 2, "error": 0}

    @pytest.mark.parametrize(
        "change",
        [
            {"value_date": datetime.date(2026, 11, 5)},
            {"amount_cents": -701},
            {"concept": "ALTRE CONCEPTE"},
            {"balance_cents": 103071},
        ],
    )
    def test_v_06_any_difference_makes_it_new(self, treasurer, change):
        imported(treasurer, card_line(**change))
        (line,) = bs.preview(csv_file(CARD_ROW), by=treasurer)["lines"]
        assert line["result"] == "new"

    def test_l19_same_file_twice_is_all_duplicates(self, treasurer):
        imported(treasurer, *map(stored, bs.preview(STATEMENT, by=treasurer)["lines"]))
        counts = bs.preview(STATEMENT, by=treasurer)["counts"]
        assert counts == {"new": 0, "duplicate": 3, "error": 0}

    def test_lines_of_an_undone_statement_are_not_duplicates(self, treasurer):
        imported(treasurer, card_line(), status="undone")
        assert not imports.statement_lines().exists()
        (line,) = bs.preview(csv_file(CARD_ROW), by=treasurer)["lines"]
        assert line["result"] == "new"

    def test_statement_lines_by_batch(self, treasurer):
        first = imported(treasurer, card_line())
        imported(treasurer, card_line(amount_cents=-1))
        assert [x.amount_cents for x in imports.statement_lines(first)] == [-700]
        assert imports.statement_lines().count() == 2


class TestCents:
    @pytest.mark.parametrize(
        ("text", "cents"),
        [
            ("50,00", 5000),
            ("-12,30", -1230),
            ("+7", 700),
            ("12,3", 1230),
            ("1.234,56", 123456),
            (" 1 234,56 € ", 123456),
            ("0,01", 1),
            ("-0,01", -1),
            ("99.999.999,99", 9999999999),
            ("12,345", None),
            ("abc", None),
            ("", None),
            ("NaN", None),
            ("Infinity", None),
            ("10.000.000.000,00", None),
        ],
    )
    def test_cents(self, text, cents):
        assert bs._cents(text, ",") == cents


class TestRejectedFiles:
    """CA-21.5: un error clar i no s'escriu res (CK B9). La pujada (mida i tipus) la valida la
    pantalla amb `files.validate_upload`, a la segona part."""

    @pytest.mark.parametrize(
        ("data", "code"),
        [
            (b"Fecha;Concepto;Importe\n01/11/2026;x;1\n", "format"),
            (b"", "format"),
            (HEADER.encode() + b"\n\n ; \n", "no_lines"),
            (b'Data;Concepte;Import;Saldo\n01/11/2026;"' + b"x" * 140_000 + b'";1;1\n', "format"),
            (STATEMENT + b"\n" + b"x" * 70_000 + b"\xff", "encoding"),
        ],
        ids=["columns", "empty", "header-only", "huge-field", "late-non-utf8"],
    )
    def test_ca_21_5_clear_error_and_nothing_written(self, treasurer, data, code):
        with pytest.raises(bs.Rejected) as info:
            bs.preview(data, by=treasurer)
        assert info.value.code == code and info.value.message == bs.MESSAGES[code]
        assert not ImportBatch.objects.exists() and not ImportLine.objects.exists()
        entry = AuditEntry.objects.get(action=bs.audit.Action.BANK_STATEMENT_PREVIEW)
        assert entry.details["rejected"] == code

    def test_too_many_lines(self, treasurer, monkeypatch):
        monkeypatch.setattr(bs, "MAX_LINES", 2)
        with pytest.raises(bs.Rejected) as info:
            bs.preview(STATEMENT, by=treasurer)
        assert info.value.code == "too_many_lines"


class TestLineColumns:
    def test_statement_values_only_on_new_lines(self, treasurer):
        batch = imported(treasurer, card_line())
        for values in (
            {"result": "duplicate", "amount_cents": 1},
            {"result": "new", "concept": "x"},
        ):
            with pytest.raises(IntegrityError) as info, transaction.atomic():
                ImportLine.objects.create(batch=batch, row=99, **values)
            name = info.value.__cause__.diag.constraint_name
            assert name == "importline_statement_values_only_new"
