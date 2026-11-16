"""Extracte bancari en Norma 43 (quadern 43 de l'AEB; T-M00-09, P-103). Només dades inventades:
el compte de la capçalera és de zeros i cap concepte és real.
"""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core import files
from apps.core.imports import bank_statement as bs

pytestmark = pytest.mark.django_db

CARD = "4111 1111 1111 1111"


def header(balance=100000, sign="2", currency="978"):
    return f"11{'0' * 18}261101261130{sign}{balance:014d}{currency}3{'CRIS PROVES':<26}{'':3}"


def movement(amount, *, sign="2", date="261102", ref1="0" * 12, ref2=""):
    return f"22{'':4}0000{date}{date}02000{sign}{amount:014d}{'0' * 10}{ref1:>12}{ref2:<16}"


def concept(text, number=1):
    return f"23{number:02d}{text:<76}"


def footer(debits, credits, balance, sign="2"):
    debit_total = sum(debits)
    credit_total = sum(credits)
    return (
        f"33{'0' * 18}{len(debits):05d}{debit_total:014d}{len(credits):05d}{credit_total:014d}"
        f"{sign}{balance:014d}978{'':4}"
    )


def n43(*records):
    assert all(len(record) == 80 for record in records)
    return "\r\n".join(records).encode("ascii")


STATEMENT = n43(
    header(),
    movement(5000, ref2="CRIS-AB2CD-K"),
    concept("TRANSF DE PROVA INVENTADA"),
    movement(700, sign="1"),
    concept(f"PAGAMENT TARGETA {CARD}"),
    footer([700], [5000], 104300),
    "88" + "9" * 18 + "000006" + " " * 54,
)


def test_reads_movements_with_running_balance_and_masked_concept():
    lines = bs.parse(STATEMENT)
    assert [(line["row"], line["date"], line["amount"], line["balance"]) for line in lines] == [
        (2, "2026-11-02", 5000, 105000),
        (4, "2026-11-02", -700, 104300),
    ]
    assert lines[0]["concept"] == "TRANSF DE PROVA INVENTADA CRIS-AB2CD-K"
    assert lines[1]["concept"] == f"PAGAMENT TARGETA {bs.MASK}"
    assert all(line["codes"] == [] for line in lines)


def test_debit_opening_balance_is_negative():
    data = n43(header(1000, sign="1"), movement(300), footer([], [300], 700, sign="1"))
    assert bs.parse(data)[0]["balance"] == -700


@pytest.mark.parametrize(
    "records",
    [
        (header(), movement(5000), footer([], [4000], 105000)),  # total d'abonaments
        (header(), movement(5000), footer([], [5000], 999999)),  # saldo final
        (header(), movement(5000)),  # sense registre 33
        (header(), movement(5000, date="261340"), footer([], [5000], 105000)),  # data
        (header(), movement(5000, sign="3"), footer([], [5000], 105000)),  # clau
        (header(), concept("SENSE MOVIMENT"), footer([], [], 100000)),  # 23 sense 22
        (header(), "99" + " " * 78, footer([], [], 100000)),  # registre desconegut
    ],
)
def test_broken_file_is_rejected_whole(records):
    with pytest.raises(bs.Rejected) as exc:
        bs.parse(n43(*records))
    assert exc.value.code == "norma43"


def test_one_account_and_euros_only():
    block = (header(), movement(5000), footer([], [5000], 105000))
    with pytest.raises(bs.Rejected) as exc:
        bs.parse(n43(*block, *block))
    assert exc.value.code == "several_accounts"
    with pytest.raises(bs.Rejected) as exc:
        bs.parse(n43(header(currency="840"), movement(5000), footer([], [5000], 105000)))
    assert exc.value.code == "currency"


def test_no_movements():
    with pytest.raises(bs.Rejected) as exc:
        bs.parse(n43(header(), footer([], [], 100000)))
    assert exc.value.code == "no_lines"


def test_preview_and_confirm_store_lines_and_detect_duplicates(make_admin):
    admin = make_admin("treasurer")
    result = bs.preview(STATEMENT, by=admin)
    assert result["counts"] == {"new": 2, "duplicate": 0, "error": 0}
    batch = bs.confirm(result["token"], by=admin)
    assert sorted(batch.lines.values_list("amount_cents", flat=True)) == [-700, 5000]
    assert bs.preview(STATEMENT, by=admin)["counts"] == {"new": 0, "duplicate": 2, "error": 0}


@pytest.mark.parametrize("name", ["extracte.n43", "extracte.TXT", "extracte.csv"])
def test_upload_accepts_text_with_statement_extensions(name):
    upload = SimpleUploadedFile(name, STATEMENT)
    assert files.validate_upload(upload, allowed=files.BANK_STATEMENT_TYPES)


def test_plain_text_is_not_an_import_or_an_attachment():
    upload = SimpleUploadedFile("extracte.n43", STATEMENT)
    for allowed in (files.IMPORT_TYPES, files.UPLOAD_TYPES):
        with pytest.raises(ValidationError):
            files.validate_upload(upload, allowed=allowed)
