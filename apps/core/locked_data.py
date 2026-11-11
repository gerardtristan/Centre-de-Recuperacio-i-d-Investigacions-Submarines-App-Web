"""Dades bloquejades i la seva consulta (T-M00-04; M13 `core.locked_data.view`, protegit; decisió
028, punt 2; 058, punt 7; spec 00, CA-19.3 i RN-91).

**Què és «bloquejat».** Quan s'anonimitza una persona (`privacy.anonymise_person`), els seus
registres econòmics (càrrecs, pagaments i quotes) no s'esborren ni es modifiquen. La identitat que
hi surt, però, la llei obliga a conservar-la fins al termini legal: abans de buidar-la de la
persona, `lock` en desa una còpia xifrada a `LockedIdentity`. Només si la persona té algun
càrrec: sense registres econòmics, no es conserva res.

**Quins camps** (`FIELDS`): nom, cognoms i document, el mínim per identificar qui va pagar
[A validar: gestoria, Q-14]. Cap correu, telèfon, adreça ni data de naixement.

**Consulta (RN-91).** `consult` només amb M13 (tresorer i administrador, protegit: no s'edita des
de la matriu) i amb un motiu. Cada consulta queda al registre d'activitat amb el motiu i sense cap
valor. No hi ha cap altra lectura: ni llistat, ni cerca, ni exportació, ni la fitxa.

**Termini (CA-19.5, RN-90): PUNT D'EXTENSIÓ, sense codi.** Depèn de la Q-14. La data d'inici és
`LockedIdentity.locked_at`; la 058 (punt 7) diu que, passat el termini, s'anonimitzen (no es
destrueixen els registres econòmics).
"""

import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext as _

from . import audit, charges, crypto
from .models import Charge, LockedIdentity, Person
from .permissions import has_perm

PERMISSION = "core.locked_data.view"  # M13
LOCKED = "locked_data.locked"
VIEWED = "locked_data.viewed"
# [A validar: gestoria, Q-14] El mínim que identifica qui va pagar.
FIELDS = ("first_name", "last_name", "id_document_type", "id_document_number")


def lock(person: Person) -> LockedIdentity | None:
    """Desa la identitat de la persona, xifrada, si té registres econòmics. Es crida dins de
    l'anonimització, abans de buidar la persona. Torna `None` si no hi ha res a conservar."""
    if not Charge.objects.filter(person=person).exists():
        return None
    payload = {name: getattr(person, name) for name in FIELDS}
    locked, _created = LockedIdentity.objects.update_or_create(
        person=person, defaults={"payload_encrypted": crypto.encrypt(json.dumps(payload))}
    )
    return locked


def record_locked(person: Person, *, by, request=None) -> None:
    """L'entrada del registre: quins camps s'han bloquejat, mai quins valors."""
    audit.record(LOCKED, actor=by, target=person, details={"fields": list(FIELDS)}, request=request)


def locked_people():
    """Les persones amb dades bloquejades: només la referència anònima i la data."""
    return (
        LockedIdentity.objects.filter(person__status=Person.Status.ANONYMISED)
        .select_related("person")
        .order_by("-locked_at", "-pk")
    )


def can_consult(account, *, permissions=None) -> bool:
    return has_perm(account, PERMISSION, permissions=permissions)


def consult(locked: LockedIdentity, *, by, reason: str, request=None) -> dict:
    """Torna la identitat i els registres econòmics bloquejats. Sense M13, `PermissionDenied`;
    sense motiu, `ValidationError`. Cada consulta queda al registre amb el motiu."""
    if not can_consult(by):
        raise PermissionDenied
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Escriu el motiu de la consulta."))
    audit.record(VIEWED, actor=by, target=locked.person, reason=reason, request=request)
    identity = json.loads(crypto.decrypt(locked.payload_encrypted))
    records = []
    for charge in (
        Charge.objects.filter(person=locked.person)
        .select_related("department")
        .prefetch_related("payments")
        .order_by("created_at", "pk")
    ):
        records.append(
            {
                "charge": charge,
                "amount": charges.euros(charge.amount_cents),
                "payments": [
                    (payment, charges.euros(payment.amount_cents))
                    for payment in charge.payments.all()
                ],
            }
        )
    return {"identity": identity, "records": records}
