"""Exportació de Cluber en Excel (.xlsx): lectura segura i conversió a les mateixes files que el CSV
(decisió 081, punt 23; P-63; RN-M01-103; T-M01-50).

El fitxer .xlsx es converteix aquí en el CSV separat per «;» que ja llegeix `cluber.preview`, de
manera que **totes les regles de validació i d'importació són les mateixes** per als dos formats i
dos fitxers amb els mateixos valors donen el mateix resultat i la mateixa empremta.

Seguretat:
- Mida: el mateix màxim d'1 MiB que el CSV (`cluber.MAX_BYTES`), comprovat abans de llegir res.
- Bomba de compressió: abans d'obrir-lo amb openpyxl, el contingut descomprimit del zip no pot
  passar de `MAX_UNCOMPRESSED` ni tenir més de `MAX_ENTRIES` parts.
- Contingut actiu: un llibre amb macros (`xl/vbaProject.bin`) o amb enllaços externs
  (`xl/externalLinks/`) es rebutja. openpyxl no executa mai res; el XML es llegeix amb
  `defusedxml` (dependència declarada), que openpyxl fa servir si hi és.
- Fórmules: no s'executen ni se'n llegeix el valor desat. Una cel·la amb fórmula fa rebutjar el
  fitxer, amb la fila i la columna, perquè la secretaria el desi amb els valors.

Quin full es llegeix: el **full que té a la primera fila totes les columnes obligatòries** de
Cluber (`cluber.REQUIRED_HEADERS`). Si no n'hi ha cap, falta una columna obligatòria; si n'hi ha
més d'un, el fitxer es rebutja i cal deixar-ne només un. Els altres fulls no es llegeixen.

Valors: el text tal com és; les dates, en dd/mm/aaaa; els nombres enters, sense decimals; els
altres nombres, amb punt decimal; els booleans, «true» o «false»; les cel·les buides, buides. Un
número de soci amb zeros a l'esquerra desat com a nombre els perd (Excel ja no els té).
"""

import csv
import datetime
import io
import zipfile

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

ZIP_MAGIC = b"PK\x03\x04"
MAX_UNCOMPRESSED = 16 * 1024 * 1024
MAX_ENTRIES = 500
ACTIVE_PARTS = ("xl/vbaProject.bin", "xl/externalLinks/", "xl/activeX/")


class XlsxRejected(Exception):  # noqa: N818 (no és un error del programa)
    """El fitxer no es pot llegir. `code` és una clau de `cluber.MESSAGES`."""

    def __init__(self, code, *, column="", row=None):
        super().__init__(code)
        self.code, self.column, self.row = code, column, row


def is_xlsx(data: bytes) -> bool:
    return data[:4] == ZIP_MAGIC


def _check_container(data: bytes) -> None:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
        entries = archive.infolist()
    except (zipfile.BadZipFile, ValueError) as error:
        raise XlsxRejected("xlsx_invalid") from error
    names = [entry.filename for entry in entries]
    if len(entries) > MAX_ENTRIES or sum(entry.file_size for entry in entries) > MAX_UNCOMPRESSED:
        raise XlsxRejected("too_large")
    if "xl/workbook.xml" not in names:
        raise XlsxRejected("xlsx_invalid")
    if any(name.startswith(part) for name in names for part in ACTIVE_PARTS):
        raise XlsxRejected("xlsx_active_content")


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime.datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, datetime.date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, datetime.time):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _header(row) -> list[str]:
    values = [_text(cell.value).strip() for cell in row]
    while values and not values[-1]:
        values.pop()
    return values


def to_csv(data: bytes, *, required, iban_headers, header_key) -> bytes:
    """Converteix el full de dades en el CSV que llegeix `cluber.preview` (UTF-8, «;»). Les
    columnes d'IBAN es buiden aquí mateix, abans de cap altre tractament (071)."""
    _check_container(data)
    try:
        book = load_workbook(io.BytesIO(data), read_only=True, data_only=False, keep_links=False)
    except Exception as error:  # noqa: BLE001 (qualsevol error de lectura és un fitxer invàlid)
        raise XlsxRejected("xlsx_invalid") from error
    try:
        candidates = []
        closest = []  # columnes obligatòries que falten al full que en té més
        for sheet in book.worksheets:
            first = next(sheet.iter_rows(min_row=1, max_row=1), None)
            headers = _header(first) if first else []
            missing = [name for name in required if name not in headers]
            if not missing:
                candidates.append(sheet)
            elif not closest or len(missing) < len(closest):
                closest = missing
        if not candidates:
            raise XlsxRejected("missing_header", column=closest[0])
        if len(candidates) > 1:
            raise XlsxRejected("xlsx_several_sheets")
        sheet = candidates[0]
        out = io.StringIO()
        writer = csv.writer(out, delimiter=";", lineterminator="\n")
        width = None
        iban = set()
        for number, row in enumerate(sheet.iter_rows(), start=1):
            cells = list(row)
            for position, cell in enumerate(cells, start=1):
                if cell.data_type == "f":
                    raise XlsxRejected(
                        "xlsx_formula", column=get_column_letter(position), row=number
                    )
            values = [_text(cell.value) for cell in cells]
            if width is None:
                values = _header(cells)
                width = len(values)
                iban = {i for i, name in enumerate(values) if header_key(name) in iban_headers}
            else:
                if not any(v.strip() for v in values):
                    continue  # fila buida, com una línia buida del CSV
                extra = values[width:]
                values = values[:width] if not any(v.strip() for v in extra) else values
                values += [""] * (width - len(values))
                for i in iban:
                    values[i] = ""
            writer.writerow(values)
        return out.getvalue().encode("utf-8")
    finally:
        book.close()
