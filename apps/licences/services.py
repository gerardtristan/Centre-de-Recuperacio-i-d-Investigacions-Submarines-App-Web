"""Serveis del 06 per a altres mòduls (M06-8). Cap altra app llegeix ni escriu els models del 06:
ho fa amb aquests serveis.

- `current(person, on)`: la llicència que cobreix una data (RN-M06-13). Només lectura, una sola
  consulta.
- `participant_status(account, person, on, context)`: el que pot veure de la llicència d'un
  participant l'instructor («vigent sí o no») o el responsable de l'activitat («vigent», «en
  tràmit» o «no») per a la data de la sessió o de l'activitat (RN-M06-22, LC10). Mai la data de
  venciment, el número federatiu, la categoria ni el document.
"""

import datetime
from dataclasses import dataclass

from django.db.models import TextChoices
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from apps.core.permission_catalog import SCOPE_ALL, SCOPE_OWN_SESSIONS
from apps.core.permissions import has_perm, scope_for

from .models import IN_PROGRESS, Licence

PARTICIPANT_PERMISSION = "licences.participant_status"  # LC10


class CurrentStatus(TextChoices):
    ACTIVE = "active", _("Vigent")
    IN_PROGRESS = "in_progress", _("En tràmit")


@dataclass(frozen=True)
class CurrentLicence:
    """Resposta de `current` (M06-8). Mai el model ni el número federatiu."""

    status: str
    licence_type: str
    category: str
    validity_rule: str
    expires_on: datetime.date
    origin: str


def current(person, on: datetime.date) -> CurrentLicence | None:
    """RN-M06-13: la llicència `active` que cobreix `on` (la que caduca més tard); si no n'hi ha
    cap, una `requested`, `paid` o `filed` que la cobriria, com a «en tràmit»; si no, `None`.
    Les cancel·lades i les no tramitades a temps no compten."""
    candidates = (
        Licence.objects.filter(
            person=person,
            starts_on__lte=on,
            expires_on__gte=on,
            status__in=[Licence.Status.ACTIVE, *IN_PROGRESS],
        )
        .select_related("licence_type")
        .order_by("-expires_on", "-pk")
    )
    chosen = None
    for licence in candidates:
        if licence.status == Licence.Status.ACTIVE:
            chosen = licence
            break
        chosen = chosen or licence
    if chosen is None:
        return None
    return CurrentLicence(
        status=CurrentStatus.ACTIVE
        if chosen.status == Licence.Status.ACTIVE
        else CurrentStatus.IN_PROGRESS,
        licence_type=chosen.licence_type.name,
        category=chosen.licence_type.category,
        validity_rule=chosen.validity_rule,
        expires_on=chosen.expires_on,
        origin=chosen.origin,
    )


class ParticipantStatus(TextChoices):
    VALID = "valid", _("Vigent")
    IN_PROGRESS = "in_progress", _("En tràmit")
    NO = "no", _("No")


def participant_status(account, person, on: datetime.date, context=None) -> str:
    """RN-M06-22 i LC10. `context` és la sessió o l'activitat del 02: amb l'abast «les seves
    sessions» o «les seves activitats», el permís només val si `context` cau dins l'abast (la
    comprovació la registra el 02 amb `register_scope_check`; si no n'hi ha, es nega). Sense
    permís, «no trobat». Que `person` sigui participant de `context` ho comprova el 02."""
    scope = scope_for(account, PARTICIPANT_PERMISSION)
    # Amb un abast per objecte, sense `context` no hi ha res a comprovar: es nega (`has_perm`
    # sense objecte diria que sí).
    if scope is None or (scope != SCOPE_ALL and context is None):
        raise Http404
    if not has_perm(account, PARTICIPANT_PERMISSION, obj=context):
        raise Http404
    info = current(person, on)
    if info is None:
        return ParticipantStatus.NO
    if info.status == CurrentStatus.ACTIVE:
        return ParticipantStatus.VALID
    # Per a l'instructor, una llicència en tràmit és «no» (RN-M06-22, CA-M06-27).
    if scope == SCOPE_OWN_SESSIONS:
        return ParticipantStatus.NO
    return ParticipantStatus.IN_PROGRESS
