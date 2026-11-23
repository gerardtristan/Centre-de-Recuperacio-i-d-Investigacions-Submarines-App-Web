"""Calendari dels ajuts (T-M09A-05; HU-M09A-03; `grants.calendar(from, to)` de M09-ajuts-8).

Només lectura: els tancaments de les convocatòries, les respostes previstes de les presentades,
les dates de justificació de les concedides (la pròrroga, si n'hi ha; RN-M09A-20) i les dates
límit dels requeriments d'esmena sense resposta. Cap dada personal: la convocatòria, l'organisme,
la referència de la sol·licitud i el seu estat."""

import datetime
from dataclasses import dataclass

from django.db.models import F
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from .models import GrantApplication, GrantCall, GrantRequirement

S = GrantApplication.Status
KINDS = {
    "close": _("Tancament de la convocatòria"),
    "response": _("Resposta prevista"),
    "justify": _("Justificació"),
    "requirement": _("Requeriment d'esmena"),
}


@dataclass(frozen=True)
class Event:
    day: datetime.date
    kind: str
    call: str
    body: str
    application: GrantApplication | None = None

    @property
    def label(self):
        return KINDS[self.kind]


def _name(call) -> str:
    return f"{call.name} {call.edition_label}".strip()


def calendar(start: datetime.date, end: datetime.date) -> list[Event]:
    """Els esdeveniments entre `start` i `end` (tots dos inclosos), per data i tipus."""
    span = (start, end)
    events = [
        Event(call.closes_on, "close", _name(call), call.body)
        for call in GrantCall.objects.filter(closes_on__range=span)
    ]
    applications = GrantApplication.objects.select_related("call")
    for application in applications.filter(status=S.SUBMITTED, expected_response_on__range=span):
        events.append(
            Event(application.expected_response_on, "response", _name(application.call),
                  application.call.body, application)
        )  # fmt: skip
    justify_on = Coalesce("justification_extended_to", F("call__justification_due_on"))
    granted = applications.annotate(justify_on=justify_on)
    for application in granted.filter(status=S.GRANTED, justify_on__range=span):
        events.append(
            Event(application.justify_on, "justify", _name(application.call),
                  application.call.body, application)
        )  # fmt: skip
    requirements = GrantRequirement.objects.filter(answered_on__isnull=True, due_on__range=span)
    for requirement in requirements.select_related("application__call"):
        application = requirement.application
        events.append(
            Event(requirement.due_on, "requirement", _name(application.call),
                  application.call.body, application)
        )  # fmt: skip
    order = list(KINDS)
    return sorted(events, key=lambda e: (e.day, order.index(e.kind), e.call))
