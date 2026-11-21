"""Avisos de venciment (T-M06-11, part de servei; RN-M06-12; CA-M06-08, 09, 24 i 26).

- `due(today)`: per a cada tram de `licences.reminder_days`, les llicències vigents (no les d'un
  dia) que caduquen just aquell dia de distància, sense una renovació en curs i sense l'avís
  d'aquell tram ja enviat. Una llicència només surt al tram que toca avui.
- `digest(today)`: el resum de la secretaria per tram, agrupat per data de venciment i
  categoria, i ordenat per data i nom.

Només lectura. L'enviament (els correus al titular i el resum, les files de `LicenceReminder` i
`LicenceReminderDigest`, en lots per la cua) necessita les plantilles de la PR del nucli del 06.
"""

import datetime
from itertools import groupby

from django.db.models import Exists, OuterRef
from django.utils import timezone

from apps.core import business_settings

from .models import Licence, LicenceReminder, ValidityRule

REMINDER_DAYS = "licences.reminder_days"  # VC-41
RENEWING = (
    Licence.Status.REQUESTED, Licence.Status.PAID, Licence.Status.FILED, Licence.Status.ACTIVE,
)  # fmt: skip


def due(today: datetime.date | None = None) -> dict[int, list[Licence]]:
    """{dies abans: [llicències]} per als trams de l'ajust, de més lluny a més a prop."""
    today = today or timezone.localdate()
    renewal = Licence.objects.filter(renewal_of=OuterRef("pk"), status__in=RENEWING)
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
            .exclude(Exists(renewal))
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
