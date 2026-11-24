"""Avisos de venciment (T-M06-11; RN-M06-12; CA-M06-08, 09, 24 i 26).

- `due(today)`: per a cada tram de `licences.reminder_days`, les llicències vigents (no les d'un
  dia) que caduquen just aquell dia de distància, sense una renovació en curs i sense l'avís
  d'aquell tram ja enviat. Una llicència només surt al tram que toca avui.
- `digest(today)`: el resum de la secretaria per tram, agrupat per data de venciment i
  categoria, i ordenat per data i nom.

Enviament (la tasca diària `licences.send_reminders` i els lots `licences.send_reminder_batch`):
- `plan(today)`: el resum de cada tram a qui tramita (LC5), un sol cop per dia i tram
  (`LicenceReminderDigest`), i els lots de llicències per avisar, de `LICENCE_REMINDER_BATCH_SIZE`.
- `send_batch(days_before, licence_ids)`: l'avís a cada titular d'un lot, un sol cop per
  llicència i tram (`LicenceReminder`), si encara és vigent i no té cap renovació en curs.
Si la tasca es repeteix el mateix dia, no s'envia res més (CA-M06-24).
"""

import datetime
from itertools import groupby

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.urls import reverse
from django.utils import timezone

from apps.accounts.invitations import has_personal_account
from apps.core import business_settings, mail
from apps.members import recipients

from . import events as licence_events
from .models import Licence, LicenceReminder, LicenceReminderDigest, ValidityRule

REMINDER_DAYS = "licences.reminder_days"  # VC-41
REMINDER_TEMPLATE = "avis-venciment-llicencia"
DIGEST_TEMPLATE = "resum-venciments-llicencies"
DIGEST_PERMISSION = "licences.file"  # LC5: qui tramita (la secretaria a la matriu inicial)
RENEWING = (
    Licence.Status.REQUESTED, Licence.Status.PAID, Licence.Status.FILED, Licence.Status.ACTIVE,
)  # fmt: skip


def _renewal():
    return Licence.objects.filter(renewal_of=OuterRef("pk"), status__in=RENEWING)


def due(today: datetime.date | None = None) -> dict[int, list[Licence]]:
    """{dies abans: [llicències]} per als trams de l'ajust, de més lluny a més a prop."""
    today = today or timezone.localdate()
    result = {}
    for days in sorted(set(business_settings.get(REMINDER_DAYS, today)), reverse=True):
        sent = LicenceReminder.objects.filter(licence=OuterRef("pk"), days_before=days)
        result[days] = list(
            Licence.objects.filter(
                status=Licence.Status.ACTIVE,
                expiry_confirmed=True,  # RN-M06-24: cap avís mentre és pendent de confirmar
                expires_on=today + datetime.timedelta(days=days),
            )
            .exclude(validity_rule=ValidityRule.SINGLE_DAY)
            .exclude(Exists(_renewal()))
            .exclude(Exists(sent))
            .select_related("person", "licence_type")
            .order_by("person__last_name", "person__first_name", "pk")
        )
    return result


def digest(today: datetime.date | None = None) -> dict[int, list[tuple[tuple, list[Licence]]]]:
    """{dies abans: [((venciment, categoria), [llicències per nom])]} dels trams amb alguna."""
    groups = {}
    for days, licences in due(today).items():
        if not licences:
            continue

        def key(licence):
            return (licence.expires_on, licence.licence_type.category)

        ordered = sorted(licences, key=lambda lic: (*key(lic), lic.person.last_name,
                                                     lic.person.first_name, lic.pk))  # fmt: skip
        groups[days] = [(group, list(items)) for group, items in groupby(ordered, key=key)]
    return groups


def _date(day: datetime.date) -> str:
    return f"{day:%d/%m/%Y}"


def _send_digest(today: datetime.date, days: int, groups) -> None:
    context = {
        "days_before": days,
        "total": sum(len(items) for _group, items in groups),
        "groups": [
            {
                "expires_on": _date(expires_on),
                "category": items[0].licence_type.get_category_display(),
                "count": len(items),
            }
            for (expires_on, _category), items in groups
        ],
    }
    try:
        with transaction.atomic():
            sent = licence_events.notify(DIGEST_PERMISSION, DIGEST_TEMPLATE, context)
            LicenceReminderDigest.objects.create(
                day=today, days_before=days, count=context["total"], sent_to=sent
            )
    except IntegrityError:
        pass  # una altra execució del mateix dia ja l'ha enviat: es desfan els correus


def plan(today: datetime.date | None = None) -> list[tuple[int, list[int]]]:
    """Envia els resums que falten d'avui i torna els lots `(dies abans, [llicències])`."""
    today = today or timezone.localdate()
    size = settings.LICENCE_REMINDER_BATCH_SIZE
    batches = []
    for days, groups in digest(today).items():
        if not LicenceReminderDigest.objects.filter(day=today, days_before=days).exists():
            _send_digest(today, days, groups)
        ids = [licence.pk for _group, items in groups for licence in items]
        batches += [(days, ids[i : i + size]) for i in range(0, len(ids), size)]
    return batches


def _link(person) -> str:
    # Sense compte personal (un convidat), la pàgina pública per demanar-la (P-502).
    name = "licences:mine" if has_personal_account(person) else "licences:public"
    return settings.PUBLIC_SITE_URL + reverse(name)


def send_batch(days_before: int, licence_ids: list[int]) -> int:
    sent = 0
    for pk in licence_ids:
        try:
            with transaction.atomic():
                licence = (
                    Licence.objects.select_for_update(of=("self",))
                    .select_related("person", "licence_type")
                    .filter(pk=pk, status=Licence.Status.ACTIVE, expiry_confirmed=True)
                    .exclude(Exists(_renewal()))
                    .first()
                )
                if licence is None or licence.reminders.filter(days_before=days_before).exists():
                    continue  # ja no és vigent, es renova o ja està avisada
                LicenceReminder.objects.create(licence=licence, days_before=days_before)
                to = recipients.email_for(licence.person)
                if to:
                    context = {
                        "licence_type": licence.licence_type.name,
                        "expires_on": _date(licence.expires_on),
                        "days_before": days_before,
                        "link": _link(licence.person),
                    }
                    sent += mail.queue_email(
                        REMINDER_TEMPLATE, to=to, person=licence.person, context=context
                    ) is not None  # fmt: skip
        except IntegrityError:
            continue  # un altre lot l'ha avisada alhora
    return sent
