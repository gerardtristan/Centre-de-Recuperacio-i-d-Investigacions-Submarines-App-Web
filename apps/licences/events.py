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


def payload(licence: Licence) -> dict:
    return {
        "licence": licence.pk,
        "person": licence.person_id,
        "licence_type": licence.licence_type.name,
        "category": licence.licence_type.category,
        "validity_rule": licence.validity_rule,
        "starts_on": licence.starts_on.isoformat(),
        "expires_on": licence.expires_on.isoformat(),
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
        status=Licence.Status.ACTIVE, expires_on__lt=today, expired_at__isnull=True
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
