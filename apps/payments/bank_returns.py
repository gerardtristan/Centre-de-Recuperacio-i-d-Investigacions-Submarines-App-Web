"""Fitxer de retornats del banc en pain.002 (banc fictici de la 092; T-M05b-12b; P-M05b-F).

El tresorer (B4 amb edició) puja el fitxer, en veu la previsualització i la confirma: cada rebut
rebutjat (`TxSts` = RJCT) es registra amb `returns.register_return`, com si l'hagués entrat a mà
amb la referència, el codi i la comissió. Tot o res: si un rebut ha canviat entre la
previsualització i la confirmació, no se'n registra cap.

- El fitxer no es desa; al registre d'activitat queda la seva empremta SHA-256 i el recompte.
- Un rebut que ja consta com a retornat surt com a «ja registrat» i no es torna a registrar.
- Si el fitxer porta l'import original i no quadra amb el rebut, la línia surt amb error; si no
  porta cap codi de motiu reconegut (per exemple, un de propi del banc), surt per entrar-la a mà.
- El fitxer sencer es rebutja si no és un pain.002 llegible o una referència hi surt dues vegades.

shortcut: format de l'estàndard ISO 20022 (pain.002.001.03 i posteriors, sense mirar la versió);
el que envia el banc de debò és [A verificar: P-45 punt 5]. Si en canvia el format, només canvia
`parse`.
"""

import hashlib
from collections import Counter
from decimal import Decimal, InvalidOperation

from defusedxml.ElementTree import ParseError, fromstring
from django.core import signing
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit, charges
from apps.core.permissions import has_perm

from . import returns
from .models import DirectDebitItem

SALT = "apps.payments.bank_returns"
TOKEN_MAX_AGE = 60 * 60  # segons: una previsualització d'abans de fa una hora ja no es confirma
READY, DONE, UNKNOWN, ERROR, BAD_CODE = "ready", "done", "unknown", "error", "bad_code"


class Rejected(Exception):
    """El fitxer sencer no es pot llegir; `message` es pot mostrar al tresorer."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class Stale(Exception):
    """La previsualització ha caducat o algun rebut ha canviat: cal tornar-la a fer."""


def _ensure_b4(by) -> None:
    if not has_perm(by, charges.RETURNS, write=True):
        raise Http404


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find(node, path: str):
    """Primer descendent per noms locals separats per «/», sense mirar l'espai de noms."""
    for name in path.split("/"):
        node = next((child for child in node if _local(child.tag) == name), None)
        if node is None:
            return None
    return node


def _text(node, path: str) -> str:
    found = _find(node, path)
    return (found.text or "").strip() if found is not None else ""


def _cents(node, path: str, *, zero_is_none=False) -> int | None:
    found = _find(node, path)
    if found is None:
        return None
    if found.get("Ccy", "EUR") != "EUR":
        raise Rejected(_("El fitxer porta imports en una moneda que no és l'euro."))
    try:
        value = Decimal((found.text or "").strip())
    except InvalidOperation:
        raise Rejected(_("El fitxer porta un import que no es pot llegir.")) from None
    if not value.is_finite() or value < 0 or value != value.quantize(Decimal("0.01")):
        raise Rejected(_("El fitxer porta un import que no es pot llegir."))
    if value == 0:
        if zero_is_none:
            return None
        raise Rejected(_("El fitxer porta un import que no es pot llegir."))
    return int(value * 100)


def parse(data: bytes) -> list[dict]:
    """Rebuts rebutjats del fitxer, en l'ordre en què hi surten."""
    try:
        root = fromstring(data)
    except (ParseError, ValueError):
        raise Rejected(_("No és un fitxer XML vàlid.")) from None
    report = _find(root, "CstmrPmtStsRpt")
    if _local(root.tag) != "Document" or report is None:
        raise Rejected(_("No és un fitxer de retornats del banc (pain.002)."))
    lines = []
    for group in report:
        if _local(group.tag) != "OrgnlPmtInfAndSts":
            continue
        for tx in group:
            if _local(tx.tag) != "TxInfAndSts" or _text(tx, "TxSts") != "RJCT":
                continue
            reference = _text(tx, "OrgnlEndToEndId")
            code = _text(tx, "StsRsnInf/Rsn/Cd").upper()
            if not reference:
                raise Rejected(_("Hi ha un rebut retornat sense referència."))
            lines.append(
                {
                    "end_to_end_id": reference,
                    "reason_code": code,
                    "amount_cents": _cents(tx, "OrgnlTxRef/Amt/InstdAmt"),
                    "fee_cents": _cents(tx, "ChrgsInf/Amt", zero_is_none=True),
                }
            )
    if not lines:
        raise Rejected(_("El fitxer no porta cap rebut retornat."))
    if max(Counter(line["end_to_end_id"] for line in lines).values()) > 1:
        raise Rejected(_("Una mateixa referència hi surt més d'una vegada."))
    return lines


def _classify(line: dict, item: DirectDebitItem | None) -> str:
    if item is None:
        return UNKNOWN
    if item.status == DirectDebitItem.Status.RETURNED:
        return DONE
    if item.status != DirectDebitItem.Status.COLLECTED or (
        line["amount_cents"] is not None and line["amount_cents"] != item.amount_cents
    ):
        return ERROR
    if not returns.CODE.fullmatch(line["reason_code"]):
        return BAD_CODE
    return READY


def preview(data: bytes, *, by) -> dict:
    """Línies amb el seu estat i el testimoni signat per confirmar les que estan a punt."""
    _ensure_b4(by)
    lines = parse(data)
    items = DirectDebitItem.objects.select_related("attempt__charge").in_bulk(
        [line["end_to_end_id"] for line in lines], field_name="end_to_end_id"
    )
    ready = []
    for line in lines:
        line["item"] = items.get(line["end_to_end_id"])
        line["status"] = _classify(line, line["item"])
        if line["status"] == READY:
            ready.append(
                [line["item"].pk, line["reason_code"], line["fee_cents"], line["end_to_end_id"]]
            )
    counts = Counter(line["status"] for line in lines)
    digest = hashlib.sha256(data).hexdigest()
    token = signing.dumps({"lines": ready, "sha256": digest}, salt=SALT) if ready else ""
    return {"lines": lines, "counts": counts, "token": token}


@transaction.atomic
def confirm(token: str, *, by) -> Counter:
    """Registra tots els rebuts de la previsualització o cap. Torna el recompte per proposta."""
    _ensure_b4(by)
    try:
        payload = signing.loads(token, salt=SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        raise Stale from None
    results = Counter()
    for item_pk, code, fee_cents, reference in payload["lines"]:
        item = DirectDebitItem.objects.filter(pk=item_pk, end_to_end_id=reference).first()
        if item is None:
            raise Stale
        try:
            results[returns.register_return(item, code, fee_cents=fee_cents, by=by)] += 1
        except returns.NotCollected:
            raise Stale from None
    audit.record(
        "payments.returns_file.imported",
        actor=by,
        details={"sha256": payload["sha256"], "registered": sum(results.values())},
    )
    return results
