"""Importació de l'extracte bancari en CSV (T-M00-01; spec 00, HU-21, RN-92 a RN-101 i V-06).

Tres passos (RN-92). Aquí, el primer: `preview` llegeix i valida el fitxer sense escriure cap
línia, i l'intent queda al registre d'activitat (RN-98), sense cap valor. Confirmar i desfer, i la
pantalla, són la segona part de la tasca.

- **Perfil:** el format del banc encara no se sap (P-45 punt 10, Q-24; P-89). Les columnes, el
  separador, el format de la data i el separador decimal surten de
  `settings.BANK_STATEMENT_CSV_PROFILE`. El fitxer ha de ser UTF-8 (`files.validate_upload`).
- **Què es desa** de cada línia nova: data, import i saldo en cèntims (amb signe) i el concepte,
  que és el que la conciliació necessita (V-06, RN-T14). La resta de columnes no es llegeixen.
- **Cap IBAN** (044): al concepte, tot el que sembla un IBAN o un número de compte o de targeta
  es tapa abans de mostrar-lo o desar-lo. Les línies amb error no guarden cap valor, només els
  codis; els missatges no repeteixen mai el contingut d'una cel·la.
- **Fitxer original** (RN-101): no es desa; només la seva empremta.
- Entre la previsualització i la confirmació, les línies normalitzades viatgen signades al
  formulari (`signing`), lligades al compte: el servidor no les desa abans de confirmar i no se'n
  pot canviar res.
"""

import csv
import datetime
import hashlib
import io
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from .. import audit
from ..models import ImportLine
from ..permissions import has_perm
from . import statement_lines

PERMISSION = "core.bank_statement.import"  # M9
MAX_LINES = 2000
_SALT = "apps.core.imports.bank_statement"

NEW, DUPLICATE, ERROR = "new", "duplicate", "error"
MASK = "[número tapat]"
# Mai cap número de compte fora del mandat xifrat (044). IBAN: dues lletres, dos dígits i la
# resta junta o en blocs separats per espais; després del primer bloc, un bloc sense cap dígit
# (com «CRIS» d'una referència que el segueix) ja no en forma part. També qualsevol tira de 12
# dígits o més (compte antic de 20 dígits, targeta).
_IBAN = re.compile(
    r"\b[A-Z]{2}\d{2}(?:[A-Z0-9]{11,30}|(?: ?[A-Z0-9]{4})(?: ?(?=[A-Z]*\d)[A-Z0-9]{1,4}){2,7})\b",
    re.IGNORECASE,
)
_LONG_NUMBER = re.compile(r"\d(?:[ -]?\d){11,}")
_LIMIT_CENTS = 10**12  # 10.000 milions d'euros: més és un error de lectura

MESSAGES = {
    "encoding": _("El fitxer no és text UTF-8. Desa'l en UTF-8 i torna-ho a provar."),
    "format": _("El fitxer no té les columnes de l'extracte que s'esperen."),
    "no_lines": _("El fitxer no té cap línia de moviments."),
    "too_many_lines": _("El fitxer té massa línies: parteix-lo en extractes més curts."),
}
LINE_MESSAGES = {
    "field_count": _("La línia no té el mateix nombre de columnes que la capçalera."),
    "date_invalid": _("La data no és vàlida."),
    "amount_invalid": _("L'import no és vàlid."),
    "balance_invalid": _("El saldo no és vàlid."),
}


class Rejected(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code
        self.message = MESSAGES[code]


def mask(text: str) -> str:
    """Concepte d'una línia, amb els números de compte i de targeta tapats."""
    text = " ".join(text.split())
    return _LONG_NUMBER.sub(MASK, _IBAN.sub(MASK, text))[
        : ImportLine._meta.get_field("concept").max_length
    ]


def _cents(text: str, decimal: str) -> int | None:
    thousands = "." if decimal == "," else ","
    text = "".join(text.split()).replace("€", "").replace(thousands, "").replace(decimal, ".")
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    if not value.is_finite() or value.as_tuple().exponent < -2 or abs(value) * 100 >= _LIMIT_CENTS:
        return None
    return int(value * 100)


def _line(row: int, cells: list, width: int, index: dict, profile: dict) -> dict:
    if len(cells) != width:
        return {"row": row, "codes": ["field_count"]}
    codes = []
    try:
        raw_date = cells[index["date"]].strip()
        value_date = datetime.datetime.strptime(raw_date, profile["date_format"]).date()
    except ValueError:
        value_date = None
        codes.append("date_invalid")
    amount = _cents(cells[index["amount"]], profile["decimal"])
    if amount is None:
        codes.append("amount_invalid")
    balance = None
    if "balance" in index:
        balance = _cents(cells[index["balance"]], profile["decimal"])
        if balance is None:
            codes.append("balance_invalid")
    if codes:  # sense cap valor de la línia
        return {"row": row, "codes": codes}
    return {
        "row": row,
        "date": value_date.isoformat(),
        "amount": amount,
        "concept": mask(cells[index["concept"]]),
        "balance": balance,
        "codes": [],
    }


def parse(data: bytes) -> list[dict]:
    """Línies normalitzades del fitxer, o `Rejected` si no és un extracte (CA-21.5)."""
    profile = settings.BANK_STATEMENT_CSV_PROFILE
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Rejected("encoding") from None
    columns = {
        key: profile[key] for key in ("date", "concept", "amount", "balance") if profile.get(key)
    }
    lines = []
    try:
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=profile["delimiter"])
        header = [name.strip().casefold() for name in next(reader, [])]
        try:
            index = {key: header.index(name.casefold()) for key, name in columns.items()}
        except ValueError:
            raise Rejected("format") from None
        for row, cells in enumerate(reader, start=2):
            if not any(cell.strip() for cell in cells):
                continue
            if len(lines) == MAX_LINES:
                raise Rejected("too_many_lines")
            lines.append(_line(row, cells, len(header), index, profile))
    except csv.Error:
        raise Rejected("format") from None
    if not lines:
        raise Rejected("no_lines")
    return lines


def _key(line: dict) -> tuple:
    return (line["date"], line["amount"], line["concept"], line["balance"])


def classify(lines: list[dict]) -> list[dict]:
    """Resultat de cada línia: amb error, duplicada (V-06: mateixa data, import, concepte i
    saldo que una línia d'un extracte confirmat o d'abans al mateix fitxer) o nova."""
    dates = {line["date"] for line in lines if not line["codes"]}
    known = {
        (value_date.isoformat(), amount, concept, balance)
        for value_date, amount, concept, balance in statement_lines()
        .filter(value_date__in=dates)
        .values_list("value_date", "amount_cents", "concept", "balance_cents")
    }
    for line in lines:
        if line["codes"]:
            line["result"] = ERROR
        elif _key(line) in known:
            line["result"] = DUPLICATE
        else:
            line["result"] = NEW
            known.add(_key(line))
    return lines


def _counts(lines: list[dict]) -> dict:
    return {
        result: sum(line["result"] == result for line in lines)
        for result in (NEW, DUPLICATE, ERROR)
    }


def _check(by) -> None:
    if not has_perm(by, PERMISSION):
        raise PermissionDenied


def preview(data: bytes, *, by, request=None) -> dict:
    """Pas 1 (CA-21.1, CA-21.2): línies validades i el testimoni per confirmar-les. No escriu
    cap línia; només l'intent, al registre."""
    _check(by)
    details = {"file_sha256": hashlib.sha256(data).hexdigest()}
    try:
        lines = classify(parse(data))
    except Rejected as exc:
        audit.record(
            audit.Action.BANK_STATEMENT_PREVIEW,
            actor=by,
            details={**details, "rejected": exc.code},
            request=request,
        )
        raise
    counts = _counts(lines)
    audit.record(
        audit.Action.BANK_STATEMENT_PREVIEW,
        actor=by,
        details={**details, "counts": counts},
        request=request,
    )
    payload = {"by": by.pk, "sha": details["file_sha256"], "lines": lines}
    token = signing.dumps(payload, salt=_SALT, compress=True)
    return {"lines": lines, "counts": counts, "token": token}
