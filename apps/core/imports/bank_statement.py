"""Importació de l'extracte bancari en CSV (T-M00-01; spec 00, HU-21, RN-92 a RN-101 i V-06).

Tres passos (RN-92): `preview` llegeix i valida el fitxer sense escriure cap línia; `confirm`
torna a mirar els duplicats i crea el lot confirmat amb les seves línies; `undo` el desfà si cap
línia no està conciliada. Els tres queden al registre d'activitat (RN-98), sense cap valor.

- **Perfil:** el format del banc encara no se sap (P-45 punt 10, Q-24; P-89). Les columnes, el
  separador, el format de la data i el separador decimal surten de
  `settings.BANK_STATEMENT_CSV_PROFILE`. El fitxer ha de ser UTF-8 (`files.validate_upload`).
- **Què es desa** de cada línia nova: data, import i saldo en cèntims (amb signe) i el concepte,
  que és el que la conciliació necessita (V-06, RN-T14). La resta de columnes no es llegeixen.
- **Cap IBAN** (044): al concepte, tot el que sembla un IBAN o un número de compte o de targeta
  es tapa abans de mostrar-lo o desar-lo. Les línies amb error no guarden cap valor, només els
  codis; els missatges no repeteixen mai el contingut d'una cel·la.
- **Norma 43** (T-M00-09; P-103): si la primera línia és un registre «11», el fitxer es llegeix
  com a quadern 43 de l'AEB (`_parse_norma43`) i en surten les mateixes línies normalitzades. Un
  sol compte, en euros; el número de compte de la capçalera no es llegeix mai.
- **Fitxer original** (RN-101): no es desa; només la seva empremta.
- Entre la previsualització i la confirmació, les línies normalitzades viatgen signades al
  formulari (`signing`), lligades al compte i amb caducitat: el servidor no les desa abans de
  confirmar i no se'n pot canviar res.
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
from django.db import connection, transaction
from django.dispatch import Signal
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .. import audit
from ..models import ImportBatch, ImportLine
from ..permissions import has_perm
from . import add_lines, open_confirmed, statement_lines

PERMISSION = "core.bank_statement.import"  # M9
MAX_BYTES = 1024 * 1024
MAX_LINES = 2000
TOKEN_MAX_AGE = 60 * 60  # segons
_SALT = "apps.core.imports.bank_statement"
# Lot confirmat o desfet, dins la mateixa transacció: la 04 torna a calcular l'estat de les
# línies a conciliar (T-M04-11).
changed = Signal()

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
    "expired": _("La previsualització ha caducat o no és vàlida: torna a pujar el fitxer."),
    "errors_not_excluded": _(
        "Hi ha línies amb error: marca que les vols excloure o corregeix el fitxer."
    ),
    "nothing_to_import": _("No hi ha cap línia nova per importar."),
    "norma43": _(
        "El fitxer Norma 43 no és complet o els totals no quadren: torna'l a descarregar del banc."
    ),
    "several_accounts": _("El fitxer té moviments de més d'un compte: descarrega'n un per compte."),
    "currency": _("L'extracte no és en euros."),
    "reason": _("Escriu el motiu."),
    "not_confirmed": _("Aquest extracte no està confirmat: no es pot desfer."),
    "reconciled": _("No es pot desfer: alguna línia de l'extracte ja està conciliada."),
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


def _n43_cents(sign: str, digits: str) -> int:
    """Import de 14 xifres amb dos decimals implícits; clau 1 = deure (surt), 2 = haver (entra)."""
    if sign not in ("1", "2") or not digits.isdigit() or int(digits) >= _LIMIT_CENTS:
        raise Rejected("norma43")
    return -int(digits) if sign == "1" else int(digits)


def _n43_count(digits: str) -> int:
    if not digits.isdigit():
        raise Rejected("norma43")
    return int(digits)


def _parse_norma43(text: str) -> list[dict]:
    """Quadern 43 de l'AEB: registres de 80 posicions (11 capçalera del compte, 22 moviment, 23
    concepte, 24 divisa, 33 final del compte, 88 final del fitxer). Un fitxer malmès o amb uns
    totals que no quadren es rebutja sencer: la línia no es pot excloure perquè el saldo de les
    següents en depèn. Data: la d'operació; saldo: l'inicial més els moviments (P-103)."""
    lines, state, balance = [], "start", 0
    totals = {"1": [0, 0], "2": [0, 0]}  # nombre i suma de càrrecs (1) i d'abonaments (2)
    for row, record in enumerate(text.splitlines(), start=1):
        record = record.rstrip().ljust(80)
        kind = record[:2]
        if kind == "  ":
            continue
        if kind == "11":
            if state != "start":
                raise Rejected("several_accounts" if state == "closed" else "norma43")
            if record[47:50] != "978":
                raise Rejected("currency")
            balance, state = _n43_cents(record[32], record[33:47]), "open"
        elif kind == "22" and state == "open":
            if len(lines) == MAX_LINES:
                raise Rejected("too_many_lines")
            try:
                value_date = datetime.datetime.strptime(record[10:16], "%y%m%d").date()
            except ValueError:
                raise Rejected("norma43") from None
            amount = _n43_cents(record[27], record[28:42])
            balance += amount
            totals[record[27]][0] += 1
            totals[record[27]][1] += abs(amount)
            lines.append(
                {
                    "row": row,
                    "date": value_date.isoformat(),
                    "amount": amount,
                    "parts": [record[64:80], record[52:64]],  # referències 2 i 1
                    "balance": balance,
                    "codes": [],
                }
            )
        elif kind == "23" and state == "open" and lines:
            lines[-1]["parts"][-2:-2] = [record[4:42], record[42:80]]
        elif kind == "24" and state == "open" and lines:
            continue  # equivalència en una altra divisa: l'import en euros ja és al 22
        elif kind == "33" and state == "open":
            expected = {
                "1": [_n43_count(record[20:25]), _n43_count(record[25:39])],
                "2": [_n43_count(record[39:44]), _n43_count(record[44:58])],
            }
            if expected != totals or _n43_cents(record[58], record[59:73]) != balance:
                raise Rejected("norma43")
            state = "closed"
        elif kind == "88" and state == "closed":
            state = "end"
        else:
            raise Rejected("norma43")
    if state not in ("closed", "end"):
        raise Rejected("norma43")
    for line in lines:
        parts = (part.strip() for part in line.pop("parts"))
        line["concept"] = mask(" ".join(part for part in parts if part.strip("0")))
    return lines


def parse(data: bytes) -> list[dict]:
    """Línies normalitzades del fitxer, o `Rejected` si no és un extracte (CA-21.5)."""
    profile = settings.BANK_STATEMENT_CSV_PROFILE
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise Rejected("encoding") from None
    if text.startswith("11"):
        lines = _parse_norma43(text)
        if not lines:
            raise Rejected("no_lines")
        return lines
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


def _stored(line: dict) -> dict:
    if line["result"] == NEW:
        return {
            "row": line["row"],
            "result": ImportLine.Result.NEW,
            "value_date": datetime.date.fromisoformat(line["date"]),
            "amount_cents": line["amount"],
            "concept": line["concept"],
            "balance_cents": line["balance"],
        }
    if line["result"] == DUPLICATE:
        return {"row": line["row"], "result": ImportLine.Result.DUPLICATE}
    return {"row": line["row"], "result": ImportLine.Result.EXCLUDED, "codes": line["codes"]}


@transaction.atomic
def confirm(token: str, *, by, exclude_errors=False, request=None) -> ImportBatch:
    """Pas 3 (CA-21.3): lot confirmat amb una línia per fila. Si es rebutja, no escriu res."""
    _check(by)
    try:
        payload = signing.loads(token, salt=_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        raise Rejected("expired") from None
    if payload["by"] != by.pk:
        raise Rejected("expired")
    with connection.cursor() as cursor:  # dues confirmacions alhora no dupliquen línies
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [_SALT])
    lines = classify(payload["lines"])
    counts = _counts(lines)
    if counts[ERROR] and not exclude_errors:
        raise Rejected("errors_not_excluded")
    if not counts[NEW]:
        raise Rejected("nothing_to_import")
    batch = open_confirmed(
        ImportBatch.Kind.BANK_STATEMENT,
        file_sha256=payload["sha"],
        by=by,
        counts={
            "new_count": counts[NEW],
            "duplicate_count": counts[DUPLICATE],
            "error_count": counts[ERROR],
            "excluded_count": counts[ERROR],
        },
    )
    add_lines(batch, [_stored(line) for line in lines])
    audit.record(
        audit.Action.BANK_STATEMENT_CONFIRMED,
        actor=by,
        target=batch,
        details={"counts": counts},
        request=request,
    )
    changed.send(sender=ImportBatch, batch=batch)
    return batch


def _reconciled(batch: ImportBatch) -> bool:
    # shortcut: qualsevol fila d'un altre model que apunti a una línia del lot bloqueja el desfer
    # (V-06), menys les relacions ocultes (l'estat de la línia de la 04 no és cap conciliació);
    # quan la T-M04-12 permeti desfer conciliacions, que compti només les vigents.
    return any(
        relation.related_model._default_manager.filter(
            **{f"{relation.field.name}__batch": batch}
        ).exists()
        for relation in ImportLine._meta.related_objects
    )


@transaction.atomic
def undo(batch: ImportBatch, *, by, reason: str, request=None) -> ImportBatch:
    """CA-21.4: el lot passa a desfet i les seves línies deixen de sortir a la conciliació.
    Les línies no s'esborren."""
    _check(by)
    if not reason.strip():
        raise Rejected("reason")
    batch = ImportBatch.objects.select_for_update().get(
        pk=batch.pk, kind=ImportBatch.Kind.BANK_STATEMENT
    )
    if batch.status != ImportBatch.Status.CONFIRMED:
        raise Rejected("not_confirmed")
    if _reconciled(batch):
        raise Rejected("reconciled")
    batch.status = ImportBatch.Status.UNDONE
    batch.undone_by, batch.undone_at = by, timezone.now()
    batch.save(update_fields=["status", "undone_by", "undone_at"])
    audit.record(
        audit.Action.BANK_STATEMENT_UNDONE,
        actor=by,
        target=batch,
        reason=reason,
        request=request,
    )
    changed.send(sender=ImportBatch, batch=batch)
    return batch
