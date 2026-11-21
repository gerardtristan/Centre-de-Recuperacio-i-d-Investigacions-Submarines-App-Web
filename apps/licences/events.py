"""Esdeveniments i avisos del 06 (T-M06-15; RN-M06-17; 052 i 054).

- `emit(licence, name)`: `licence.issued`, `renewed`, `expired` o `cancelled` amb la persona, el
  tipus, la durada, les dates, l'origen, la referència del 01, la `version` i `occurred_at`.
  Es crida dins la transacció del canvi: si es desfà, l'esdeveniment tampoc no existeix.
- `activated(licence)`: `licence.renewed` si renova una altra llicència; si no, `licence.issued`.
- `expire_due(today)`: la tasca diària; l'endemà del venciment, una sola vegada.
- `notify(permission, template, context)`: el correu als comptes que tenen ara el permís (la
  matriu vigent, mai un rol escrit al codi; 079).
"""

import datetime

from django.db import transaction
from django.utils import timezone

from apps.core import events as core_events
from apps.core import mail
from apps.core.permissions import accounts_with_perm

from .models import Licence


def known_expiry(licence: Licence) -> datetime.date | None:
    """La caducitat que veuen els altres mòduls: cap mentre no està confirmada (RN-M06-24)."""
    return licence.expires_on if licence.expiry_confirmed else None


def payload(licence: Licence) -> dict:
    expires = known_expiry(licence)
    return {
        "licence": licence.pk,
        "person": licence.person_id,
        "licence_type": licence.licence_type.name,
        "category": licence.licence_type.category,
        "validity_rule": licence.validity_rule,
        "starts_on": licence.starts_on.isoformat(),
        "expires_on": expires.isoformat() if expires else None,
        "origin": licence.origin,
        "m01_record_ref": licence.m01_record_ref,
        "version": licence.version,
        "occurred_at": timezone.now().isoformat(),
    }


def emit(licence: Licence, name: str):
    return core_events.emit(name, payload(licence))


def activated(licence: Licence):
    name = core_events.LICENCE_RENEWED if licence.renewal_of_id else core_events.LICENCE_ISSUED
    return emit(licence, name)


def expire_due(today: datetime.date | None = None) -> int:
    """`licence.expired` de les vigents que han caducat (`expires_on` anterior a avui)."""
    today = today or timezone.localdate()
    due = Licence.objects.filter(
        status=Licence.Status.ACTIVE,
        expiry_confirmed=True,
        expires_on__lt=today,
        expired_at__isnull=True,
    ).values_list("pk", flat=True)
    done = 0
    for pk in list(due):
        with transaction.atomic():
            licence = Licence.objects.select_for_update().get(pk=pk)
            if licence.expired_at is not None:
                continue  # una altra execució ja l'ha emès
            licence.expired_at = timezone.now()
            licence.save(update_fields=["expired_at", "updated_at"])
            emit(licence, core_events.LICENCE_EXPIRED)
            done += 1
    return done


def notify(permission: str, template: str, context: dict) -> int:
    sent = 0
    for account in accounts_with_perm(permission, write=True):
        if account.notification_email:
            mail.queue_email(
                template, to=account.notification_email, person=account.person, context=context
            )
            sent += 1
    return sent


def read_source() -> list[dict]:
    """La font de lectura que el 06 registra al 01 (`members.register_licence_source`, RN-M06-17;
    054): les llicències vigents i les cancel·lades, amb la versió. El 01 en tria les dels socis."""
    rows = []
    licences = Licence.objects.filter(
        status__in=[Licence.Status.ACTIVE, Licence.Status.CANCELLED]
    ).select_related("licence_type")
    for licence in licences:
        cancelled = licence.status == Licence.Status.CANCELLED
        rows.append({
            "licence": licence.pk, "person": licence.person_id,
            "licence_type": licence.licence_type.name, "starts_on": licence.starts_on,
            "expires_on": known_expiry(licence), "version": licence.version,
            "cancelled_on": timezone.localdate(licence.updated_at) if cancelled else None,
        })  # fmt: skip
    return rows
