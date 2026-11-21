"""Llistat de llicències de la secretaria, amb filtres i venciments (T-M06-09; HU-M06-05; LC4 i
C6). Només lectura. La vista arriba amb la PR del nucli del 06.

- `licence_list(actor, ...)`: una fila per llicència amb l'estat que es veu (M06-5). El número
  federatiu, la categoria i el venciment només hi surten amb el camp C6 (059, CA-M06-33). Mai la
  data de naixement ni el document.
- `expiring(days, today)`: les vigents que caduquen d'aquí a `days` dies o menys (M06-8; per als
  trams de 60, 30 i 7 dies i per al 08).
"""

import datetime
from dataclasses import dataclass

from django.http import Http404
from django.utils import timezone

from apps.core import business_settings
from apps.core.permissions import effective_permissions, has_perm

from .models import Licence, ValidityRule

LIST_PERMISSION = "licences.list"  # LC4
DETAILS_FIELD = "licences.field.details"  # C6
TO_RENEW_DAYS = "licences.to_renew_days"  # VC-41


@dataclass(frozen=True)
class LicenceRow:
    licence_id: int
    person_id: int
    person_name: str
    licence_type: str
    status: str  # estat que es veu (`Licence.Display`)
    origin: str
    category: str | None  # només amb C6
    expires_on: datetime.date | None  # només amb C6
    federation_number: str | None  # només amb C6


def expiring(days: int, today: datetime.date | None = None):
    """Vigents (no les d'un dia) que caduquen entre avui i d'aquí a `days` dies, per data i nom."""
    today = today or timezone.localdate()
    return (
        Licence.objects.filter(
            status=Licence.Status.ACTIVE,
            expiry_confirmed=True,
            expires_on__gte=today,
            expires_on__lte=today + datetime.timedelta(days=days),
        )
        .exclude(validity_rule=ValidityRule.SINGLE_DAY)
        .select_related("person", "licence_type")
        .order_by("expires_on", "person__last_name", "person__first_name", "pk")
    )


def licence_list(
    actor, *, today=None, licence_type=None, category=None, status=None, expiring_within=None
) -> list[LicenceRow]:
    """LC4; sense permís, «no trobat». Filtres: tipus, categoria, estat que es veu i venciment
    (`expiring_within` dies). Filtrar per categoria o venciment demana C6."""
    perms = effective_permissions(actor)
    if not has_perm(actor, LIST_PERMISSION, permissions=perms):
        raise Http404
    details = has_perm(actor, DETAILS_FIELD, permissions=perms)
    if not details and (category is not None or expiring_within is not None):
        raise Http404
    today = today or timezone.localdate()
    if expiring_within is not None:
        licences = expiring(expiring_within, today)
    else:
        licences = Licence.objects.select_related("person", "licence_type").order_by(
            "person__last_name", "person__first_name", "-expires_on", "pk"
        )
    if licence_type is not None:
        licences = licences.filter(licence_type=licence_type)
    if category is not None:
        licences = licences.filter(licence_type__category=category)
    to_renew_days = business_settings.get(TO_RENEW_DAYS, today)
    rows = []
    for licence in licences:
        shown = licence.display_status(today, to_renew_days)
        if status is not None and shown != status:
            continue
        rows.append(
            LicenceRow(
                licence_id=licence.pk,
                person_id=licence.person_id,
                person_name=f"{licence.person.last_name}, {licence.person.first_name}".strip(", "),
                licence_type=licence.licence_type.name,
                status=shown,
                origin=licence.origin,
                category=licence.licence_type.category if details else None,
                expires_on=licence.expires_on if details and licence.expiry_confirmed else None,
                federation_number=(licence.federation_number or None) if details else None,
            )
        )
    return rows
