"""Fitxer pain.008 d'una remesa (T-M05b-10; P-M05b-E, pas 5; RN-M05b-12; CA-M05b-15).

- Es genera a demanda, en memòria, i no es desa enlloc (RN-M05b-12, 044): `remittance_file`
  torna els bytes, en desa l'empremta a la remesa i ho deixa al registre amb qui l'ha generat.
- Els IBAN es desxifren només aquí dins (`_debtor_iban`), per escriure'ls al fitxer; cap error,
  registre ni entrada del registre d'activitat no en porta cap.
- Versió pain.008.001.02, SEPA Core, per al banc fictici (092). La versió i els detalls del banc
  real són [A verificar: P-45 punt 5] ([P-233](docs/decisions/pendents.md)). La validació
  (`check`) comprova les regles de l'esquema que fa servir el fitxer; la validació contra l'XSD
  oficial espera la versió del banc ([P-234](docs/decisions/pendents.md)).
"""

import hashlib
import re
import unicodedata
import xml.etree.ElementTree as ET
from decimal import Decimal

from defusedxml.ElementTree import fromstring
from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.utils import timezone

from apps.core import audit
from apps.core.permissions import has_perm

from . import crypto
from .checkout import transfer_iban
from .guards import requires_charges
from .mandates import validate_iban
from .models import DirectDebitItem, DirectDebitRemittance, SepaMandate

FILE_FORMAT = "pain.008.001.02"
NAMESPACE = f"urn:iso:std:iso:20022:tech:xsd:{FILE_FORMAT}"
# Nom del creditor tal com el té el banc [A verificar: banc, P-233].
CREDITOR_NAME = "CENTRE DE RECUPERACIO I D INVESTIGACIONS SUBMARINES"
NOT_PROVIDED = "NOTPROVIDED"  # entitat del deutor desconeguda: només IBAN (EPC, des del 2016)
# Joc de caràcters SEPA (EPC217-08): la resta es translitera o es canvia per un espai.
_NOT_SEPA = re.compile(r"[^A-Za-z0-9/\-?:().,'+ ]")
_DECIMAL = re.compile(r"^[0-9]{1,15}\.[0-9]{2}$")


class RemittanceNotReady(Exception):
    """Només una remesa «avisada» (tots els deutors amb l'avís previ) té fitxer."""


class NotConfigured(Exception):
    """Falta l'identificador de creditor o el compte del club."""


class MandateNoLongerActive(Exception):
    """Un mandat de la remesa ja no és actiu (revocat o bloquejat després de l'avís previ;
    L-M05b-03, [P-236](docs/decisions/pendents.md)). Porta les referències, mai l'IBAN."""


class InvalidFile(Exception):
    """El fitxer no compleix l'esquema. El missatge no porta cap IBAN."""


def sepa_text(value: str, limit: int) -> str:
    """Text en el joc de caràcters SEPA: sense accents i com a molt `limit` caràcters."""
    plain = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(_NOT_SEPA.sub(" ", plain).split())[:limit]


def _cents(cents: int) -> str:
    return f"{cents // 100}.{cents % 100:02d}"


def _sub(parent, path: str, text: str | None = None, **attrs):
    """Crea la cadena d'elements de `path` («A/B/C») i posa el text a l'últim."""
    node = parent
    for name in path.split("/"):
        node = ET.SubElement(node, name)
    if text is not None:
        node.text = text
    node.attrib.update(attrs)
    return node


def _debtor_iban(mandate: SepaMandate) -> str:
    bank = mandate.bank_account
    return crypto.decrypt(bank.key_version, bank.iban_ciphertext)


def build(remittance: DirectDebitRemittance, items, *, creditor: str, creditor_iban: str) -> bytes:
    total = sum(item.amount_cents for item in items)
    count, now = str(len(items)), timezone.localtime()
    ET.register_namespace("", NAMESPACE)
    root = ET.Element(f"{{{NAMESPACE}}}Document")
    body = _sub(root, "CstmrDrctDbtInitn")
    header = _sub(body, "GrpHdr")
    _sub(header, "MsgId", f"CRIS-REM{remittance.pk:06d}-{now:%Y%m%d%H%M%S}")
    _sub(header, "CreDtTm", f"{now:%Y-%m-%dT%H:%M:%S}")
    _sub(header, "NbOfTxs", count)
    _sub(header, "CtrlSum", _cents(total))
    party = _sub(header, "InitgPty")
    _sub(party, "Nm", CREDITOR_NAME[:70])
    _sub(party, "Id/OrgId/Othr/Id", creditor)

    info = _sub(body, "PmtInf")
    _sub(info, "PmtInfId", f"CRIS-REM{remittance.pk:06d}")
    _sub(info, "PmtMtd", "DD")
    _sub(info, "BtchBookg", "true")
    _sub(info, "NbOfTxs", count)
    _sub(info, "CtrlSum", _cents(total))
    kind = _sub(info, "PmtTpInf")
    _sub(kind, "SvcLvl/Cd", "SEPA")
    _sub(kind, "LclInstrm/Cd", "CORE")
    # Recurrent també el primer cobrament (EPC, des del 2016); si el banc demana FRST: P-233.
    _sub(kind, "SeqTp", "RCUR")
    _sub(info, "ReqdColltnDt", remittance.collection_date.isoformat())
    _sub(info, "Cdtr/Nm", CREDITOR_NAME[:70])
    _sub(info, "CdtrAcct/Id/IBAN", creditor_iban)
    _sub(info, "CdtrAgt/FinInstnId/Othr/Id", NOT_PROVIDED)
    _sub(info, "ChrgBr", "SLEV")
    scheme = _sub(info, "CdtrSchmeId/Id/PrvtId/Othr")
    _sub(scheme, "Id", creditor)
    _sub(scheme, "SchmeNm/Prtry", "SEPA")

    for item in items:
        tx = _sub(info, "DrctDbtTxInf")
        _sub(tx, "PmtId/EndToEndId", item.end_to_end_id)
        _sub(tx, "InstdAmt", _cents(item.amount_cents), Ccy="EUR")
        mandate = _sub(tx, "DrctDbtTx/MndtRltdInf")
        _sub(mandate, "MndtId", item.mandate.reference)
        _sub(mandate, "DtOfSgntr", timezone.localdate(item.mandate.signed_at).isoformat())
        _sub(tx, "DbtrAgt/FinInstnId/Othr/Id", NOT_PROVIDED)
        _sub(tx, "Dbtr/Nm", sepa_text(item.mandate.holder_name, 70))
        _sub(tx, "DbtrAcct/Id/IBAN", _debtor_iban(item.mandate))
        _sub(tx, "RmtInf/Ustrd", sepa_text(item.attempt.charge.concept, 140))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def check(content: bytes) -> None:
    """Les regles de l'esquema pain.008.001.02 que fa servir el fitxer: espai de noms, recomptes
    i sumes de control, imports, IBAN (format i dígits de control), longituds i joc de caràcters,
    identificadors d'extrem a extrem únics. `InvalidFile` si alguna falla."""
    ns = {"p": NAMESPACE}
    try:
        root = fromstring(content)
    except Exception as error:
        raise InvalidFile("El fitxer no és XML vàlid.") from error
    if root.tag != f"{{{NAMESPACE}}}Document":
        raise InvalidFile("L'arrel no és un document pain.008.001.02.")

    def texts(path):
        return [node.text or "" for node in root.findall(path, ns)]

    txs = root.findall(".//p:DrctDbtTxInf", ns)
    amounts = texts(".//p:DrctDbtTxInf/p:InstdAmt")
    if not txs or any(not _DECIMAL.match(a) or Decimal(a) <= 0 for a in amounts):
        raise InvalidFile("Cap rebut o algun import no és vàlid.")
    total = str(sum(Decimal(a) for a in amounts))
    for level in ("p:CstmrDrctDbtInitn/p:GrpHdr", "p:CstmrDrctDbtInitn/p:PmtInf"):
        if texts(f"{level}/p:NbOfTxs") != [str(len(txs))] or texts(f"{level}/p:CtrlSum") != [total]:
            raise InvalidFile("El recompte o la suma de control no quadren.")
    if {n.get("Ccy") for n in root.findall(".//p:InstdAmt", ns)} != {"EUR"}:
        raise InvalidFile("La moneda ha de ser EUR.")
    for iban in texts(".//p:IBAN"):
        try:
            validate_iban(iban)
        except Exception as error:
            raise InvalidFile("Hi ha un IBAN que no és vàlid.") from error
    ids = texts(".//p:EndToEndId")
    if len(set(ids)) != len(ids):
        raise InvalidFile("Hi ha identificadors d'extrem a extrem repetits.")
    limits = {"MsgId": 35, "PmtInfId": 35, "EndToEndId": 35, "MndtId": 35, "Nm": 70, "Ustrd": 140}
    for name, limit in limits.items():
        for value in texts(f".//p:{name}"):
            if not value or len(value) > limit or _NOT_SEPA.search(value):
                raise InvalidFile(f"El camp {name} és buit, massa llarg o té caràcters no SEPA.")


@requires_charges("remittance_file")
@transaction.atomic
def remittance_file(remittance: DirectDebitRemittance, actor) -> bytes:
    """`payments.remittance_file` (M05b-8): el fitxer de la remesa, en memòria. En desa
    l'empremta i ho registra; no desa el fitxer. Sense B3, «no trobat» (T-M05b-25)."""
    if not has_perm(actor, "payments.remittances", write=True):
        raise Http404
    remittance = DirectDebitRemittance.objects.select_for_update().get(pk=remittance.pk)
    if remittance.status != DirectDebitRemittance.Status.NOTIFIED:
        raise RemittanceNotReady(remittance.status)
    # El compte que rep les remeses és el de les transferències (P-235).
    creditor, creditor_iban = settings.SEPA_CREDITOR_IDENTIFIER, transfer_iban()
    if not creditor or not creditor_iban:
        raise NotConfigured
    items = list(
        remittance.items.filter(status=DirectDebitItem.Status.INCLUDED)
        .select_related("mandate__bank_account", "attempt__charge")
        .order_by("pk")
    )
    stale = [i.mandate.reference for i in items if i.mandate.status != SepaMandate.Status.ACTIVE]
    if stale:
        raise MandateNoLongerActive(stale)
    content = build(remittance, items, creditor=creditor, creditor_iban=creditor_iban)
    check(content)
    remittance.file_hash = hashlib.sha256(content).hexdigest()
    remittance.file_format = FILE_FORMAT
    remittance.save(update_fields=["file_hash", "file_format"])
    audit.record(
        "payments.remittance.file_generated",
        actor=actor,
        target=remittance,
        details={"sha256": remittance.file_hash, "items": len(items), "format": FILE_FORMAT},
    )
    return content
