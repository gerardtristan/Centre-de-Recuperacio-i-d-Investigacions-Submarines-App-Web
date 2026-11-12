"""Importació de Cluber en Excel (.xlsx) (decisió 081, punt 23; P-63; RN-M01-103; T-M01-50).

El .xlsx passa per les mateixes regles que el CSV: el resultat i l'empremta són els mateixos amb
els mateixos valors. Cap fórmula ni macro no s'executa; un fitxer amb fórmules, macros, enllaços
externs, més d'un full de dades o mal format es rebutja amb un missatge clar. Només dades
inventades.
"""

import datetime
import io
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from openpyxl import Workbook

from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.imports import cluber, cluber_sample, xlsx
from apps.members.tests.test_cluber_preview import build, record
from apps.members.tests.test_cluber_views import URL, admin_client

pytestmark = pytest.mark.django_db

XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def workbook_bytes(headers, rows, *, extra_sheets=(), title="Socis"):
    """Llibre amb un full de dades i, si cal, altres fulls `(títol, files)`."""
    book = Workbook()
    sheet = book.active
    sheet.title = title
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    for name, other_rows in extra_sheets:
        other = book.create_sheet(name)
        for row in other_rows:
            other.append(row)
    out = io.BytesIO()
    book.save(out)
    return out.getvalue()


def as_rows(records, headers):
    return [[r.get(h, "") for h in headers] for r in records]


def comparable(summary):
    return {k: v for k, v in summary.items() if k not in ("encoding", "format")}


def add_part(data, name, content=b"x"):
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(out, "w") as target:
        for item in source.infolist():
            target.writestr(item, source.read(item.filename))
        target.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
    return out.getvalue()


# --- Mateixes regles i mateix resultat ----------------------------------------------------------


def test_the_same_sample_gives_the_same_result_in_csv_and_xlsx():
    records = cluber_sample.sample_records(40)
    headers = cluber_sample.real_headers()
    from_csv = cluber.preview(cluber_sample.to_file(records))
    from_xlsx = cluber.preview(workbook_bytes(headers, as_rows(records, headers)))
    assert from_csv.rejected is None and from_xlsx.rejected is None
    assert from_xlsx.source_format == "xlsx" and from_csv.source_format == "csv"
    assert from_xlsx.encoding is None
    assert comparable(from_xlsx.summary()) == comparable(from_csv.summary())
    assert from_xlsx.fingerprint == from_csv.fingerprint
    assert "iban_discarded" in from_xlsx.warnings


def test_excel_numbers_and_dates_are_read_like_the_csv_text():
    headers = list(cluber.KNOWN_HEADERS)
    text = record(1, {"Data alta/renovació": "05/10/2026", "Data de Naixament": "09/04/1988"})
    typed = dict(text)
    typed["Nº Soci"] = 901
    typed["Data alta/renovació"] = datetime.datetime(2026, 10, 5)
    typed["Data de Naixament"] = datetime.date(1988, 4, 9)
    typed["Preu total"] = 35.0
    from_csv = cluber.preview(build([text]))
    from_xlsx = cluber.preview(workbook_bytes(headers, as_rows([typed], headers)))
    assert comparable(from_xlsx.summary()) == comparable(from_csv.summary())


def test_iban_values_are_dropped_while_converting():
    headers = cluber_sample.real_headers()
    records = cluber_sample.sample_records(3)
    converted = xlsx.to_csv(
        workbook_bytes(headers, as_rows(records, headers)),
        required=cluber.REQUIRED_HEADERS,
        iban_headers=cluber.IBAN_HEADERS,
        header_key=cluber._header_key,
    )
    assert cluber_sample.FALSE_IBAN.encode() not in converted


def test_wrong_data_gives_the_same_row_errors_as_the_csv():
    headers = list(cluber.KNOWN_HEADERS)
    bad = record(1, {"Email": "no-es-un-correu", "Data alta/renovació": "31/02/2026"})
    from_csv = cluber.preview(build([bad]))
    from_xlsx = cluber.preview(workbook_bytes(headers, as_rows([bad], headers)))
    assert from_xlsx.rows[0].errors == from_csv.rows[0].errors
    assert "email_invalid" in from_xlsx.rows[0].errors


def test_empty_rows_are_skipped_and_an_extra_cell_is_a_row_error():
    headers = list(cluber.KNOWN_HEADERS)
    rows = as_rows([record(1), record(2)], headers)
    rows.insert(1, [None] * len(headers))
    rows[-1] = [*rows[-1], "cel·la de més"]
    result = cluber.preview(workbook_bytes(headers, rows))
    assert [r.row for r in result.rows] == [2, 3]
    assert result.rows[1].errors == ["field_count"]


def test_missing_column_is_reported_by_name():
    headers = [h for h in cluber.KNOWN_HEADERS if h != "Cognoms"]
    result = cluber.preview(workbook_bytes(headers, as_rows([record(1)], headers)))
    assert (result.rejected, result.rejected_column) == ("missing_header", "Cognoms")


# --- Full de dades ---------------------------------------------------------------------------


def test_only_the_sheet_with_the_cluber_columns_is_read():
    headers = list(cluber.KNOWN_HEADERS)
    notes = [["Notes de la secretaria"], ["Una fila que no és de cap soci"]]
    result = cluber.preview(
        workbook_bytes(
            headers, as_rows([record(1)], headers), extra_sheets=[("Notes", notes)], title="Dades"
        )
    )
    assert result.rejected is None and len(result.rows) == 1


def test_two_sheets_with_cluber_columns_are_rejected():
    headers = list(cluber.KNOWN_HEADERS)
    rows = as_rows([record(1)], headers)
    data = workbook_bytes(headers, rows, extra_sheets=[("Còpia", [headers, *rows])])
    assert cluber.preview(data).rejected == "xlsx_several_sheets"


# --- Contingut actiu, fórmules i fitxers incorrectes -------------------------------------------


def test_a_formula_is_never_run_and_rejects_the_file_with_its_position():
    headers = list(cluber.KNOWN_HEADERS)
    rows = as_rows([record(1)], headers)
    rows[0][headers.index("Nom")] = '=HYPERLINK("https://exemple.invalid","Anna")'
    result = cluber.preview(workbook_bytes(headers, rows))
    assert (result.rejected, result.rejected_row) == ("xlsx_formula", 2)
    assert result.rejected_column == "B"
    assert not result.rows


@pytest.mark.parametrize(
    "part", ["xl/vbaProject.bin", "xl/externalLinks/externalLink1.xml", "xl/activeX/activeX1.xml"]
)
def test_macros_and_external_links_are_rejected(part):
    headers = list(cluber.KNOWN_HEADERS)
    data = add_part(workbook_bytes(headers, as_rows([record(1)], headers)), part)
    assert cluber.preview(data).rejected == "xlsx_active_content"


def test_a_broken_excel_file_is_rejected():
    assert cluber.preview(xlsx.ZIP_MAGIC + b"no es un zip").rejected == "xlsx_invalid"
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        archive.writestr("altres.txt", "res")
    assert cluber.preview(out.getvalue()).rejected == "xlsx_invalid"


def test_size_limits_also_apply_to_excel():
    assert cluber.preview(xlsx.ZIP_MAGIC + b"0" * cluber.MAX_BYTES).rejected == "too_large"
    headers = list(cluber.KNOWN_HEADERS)
    bomb = add_part(
        workbook_bytes(headers, as_rows([record(1)], headers)),
        "xl/media/gran.bin",
        b"\0" * (xlsx.MAX_UNCOMPRESSED + 1),
    )
    assert len(bomb) < cluber.MAX_BYTES
    assert cluber.preview(bomb).rejected == "too_large"


def test_every_rejection_has_a_message():
    for code in ("xlsx_invalid", "xlsx_active_content", "xlsx_formula", "xlsx_several_sheets"):
        assert cluber.MESSAGES[code]


# --- Pantalla de la prova -----------------------------------------------------------------------


def test_the_preview_screen_accepts_an_excel_file(make_admin):  # noqa: F811
    client = admin_client(make_admin("administrator"))
    headers = list(cluber.KNOWN_HEADERS)
    upload = SimpleUploadedFile(
        "socis.xlsx", workbook_bytes(headers, as_rows([record(1)], headers)), XLSX_TYPE
    )
    response = client.post(reverse(URL), {"fitxer": upload})
    assert response.status_code == 200
    html = response.content.decode()
    assert "Format: Excel (.xlsx)." in html
    assert ".xlsx" in html  # el camp del fitxer l'accepta
    entry = AuditEntry.objects.get(action="members.cluber_import.preview")
    assert entry.details["rejected"] is None


def test_the_preview_screen_explains_a_rejected_excel_file(make_admin):  # noqa: F811
    client = admin_client(make_admin("administrator"))
    headers = list(cluber.KNOWN_HEADERS)
    rows = as_rows([record(1)], headers)
    rows[0][0] = "=1+1"
    upload = SimpleUploadedFile("socis.xlsx", workbook_bytes(headers, rows), XLSX_TYPE)
    html = client.post(reverse(URL), {"fitxer": upload}).content.decode()
    assert "El fitxer Excel té fórmules." in html.replace("&#x27;", "'")
