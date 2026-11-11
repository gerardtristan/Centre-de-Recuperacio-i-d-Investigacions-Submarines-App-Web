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

**Termini (CA-19.5, RN-90; decisió 085, G-1).** Les dades bloquejades es destrueixen quan han
passat `LOCKED_DATA_RETENTION_YEARS` anys (6) des del 31/12 de l'any de l'últim registre econòmic
de la persona (càrrec creat o pagament fet). Els registres econòmics no s'esborren mai: queden
lligats a la referència, sense cap dada personal (058, punt 7). Ho fa cada dia la tasca
`core.destroy_expired_locked_data`, amb una entrada al registre.

Base del termini, triada per l'equip per delegació del responsable i **sense validació d'una
gestoria**: 6 anys de conservació de la documentació comptable (Codi de comerç, article 30, per
analogia), que cobreix els 4 anys de prescripció tributària (Llei general tributària, article 66),
i el bloqueig «només pel termini de prescripció» de la LOPDGDD (article 32). És configurable. Si el
club registra mai donatius de 100 € o més, la Llei 10/2010 (articles 25 i 39) en demana 10 anys.
"""

import datetime
import json

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.utils.translation import gettext as _

from . import audit, charges, crypto
from .models import Charge, LockedIdentity, Payment, Person
from .permissions import has_perm

PERMISSION = "core.locked_data.view"  # M13
LOCKED = "locked_data.locked"
VIEWED = "locked_data.viewed"
DESTROYED = "locked_data.destroyed"
DESTROY_ORIGIN = "core.destroy_expired_locked_data"
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
    """Les persones amb dades bloquejades: només la referència i la data."""
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


# --- Termini de conservació (CA-19.5, RN-90; decisió 085, G-1) -----------------------------


def retention_years() -> int:
    """Es llegeix a cada crida: és un valor de configuració."""
    return int(settings.LOCKED_DATA_RETENTION_YEARS)


def last_record_date(locked: LockedIdentity) -> datetime.date:
    """Data de l'últim registre econòmic de la persona: l'últim càrrec creat o l'últim pagament
    fet. Si no n'hi ha cap (no hauria de passar), la del bloqueig."""
    person = locked.person_id
    moments = [
        Charge.objects.filter(person=person).aggregate(last=Max("created_at"))["last"],
        Payment.objects.filter(charge__person=person).aggregate(last=Max("paid_at"))["last"],
    ]
    last = max((m for m in moments if m is not None), default=locked.locked_at)
    return timezone.localtime(last).date()


def expires_on(locked: LockedIdentity) -> datetime.date:
    """Últim dia que es conserven: el 31/12 de l'any de l'últim registre més el termini."""
    return datetime.date(last_record_date(locked).year + retention_years(), 12, 31)


def destroy_expired(today=None) -> int:
    """Destrueix les dades bloquejades amb el termini vençut i en torna el nombre. Cada una, en
    la seva transacció i amb una entrada al registre amb la referència. Idempotent."""
    today = today or timezone.localdate()
    destroyed = 0
    for candidate in LockedIdentity.objects.select_related("person").order_by("pk"):
        if today <= expires_on(candidate):
            continue
        with transaction.atomic():
            locked = LockedIdentity.objects.select_for_update().filter(pk=candidate.pk).first()
            if locked is None:
                continue
            limit = expires_on(locked)
            if today <= limit:
                continue
            audit.record(
                DESTROYED,
                actor=audit.system(DESTROY_ORIGIN),
                target=candidate.person,
                details={
                    "reference": candidate.person.anonymous_ref,
                    "retention_years": retention_years(),
                    "last_record_year": limit.year - retention_years(),
                },
            )
            locked.delete()
        destroyed += 1
    return destroyed
