"""Requeriments d'esmena i pròrroga de la justificació (T-M09A-15; RN-M09A-19, 20 i 22;
CA-M09A-17, 22 i 25). Un requeriment és un esdeveniment: la sol·licitud manté el seu estat.

Els avisos (el primer, immediat, i els de 7 i 2 dies) són de la T-M09A-06, que necessita les
plantilles de correu del nucli; aquí no se n'envia cap."""

from datetime import date, timedelta

from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.core import audit

from .models import GrantApplication, GrantRequirement
from .services import GrantError, _check_responsible, require

AMENDMENTS = "grants.applications.amendments"  # AJ13
REQUIREMENT_RECORDED = "grants.requirement_recorded"
REQUIREMENT_ANSWERED = "grants.requirement_answered"
REQUIREMENT_DUE_CHANGED = "grants.requirement_due_changed"
EXTENSION_SET = "grants.justification_extension_set"
S = GrantApplication.Status
# Un requeriment arriba quan la sol·licitud ja s'ha presentat.
WITH_REQUIREMENTS = (S.SUBMITTED, S.GRANTED, S.DENIED, S.JUSTIFIED)


class InvalidDates(GrantError):
    """La data límit (o la resposta) no pot ser d'abans de la rebuda."""


class MissingReason(GrantError):
    """Cal el motiu: un requeriment del club, un canvi de data límit o una pròrroga."""


class RequirementNotOpen(GrantError):
    """El requeriment ja està respost (o no és d'aquesta sol·licitud)."""


def _date(value, label):
    if not isinstance(value, date):
        raise InvalidDates(_("Cal %(field)s.") % {"field": label})
    return value


def is_open(requirement, application) -> bool:
    return (
        requirement is not None
        and requirement.application_id == application.pk
        and requirement.answered_on is None
    )


@transaction.atomic
def record_requirement(
    application,
    *,
    origin,
    received_on,
    description,
    responsible,
    by,
    due_on=None,
    origin_reason="",
) -> GrantRequirement:
    """`grants.record_requirement` (CA-M09A-17 i 25): l'organisme el demana o el club l'obre
    (amb motiu obligatori). La sol·licitud continua en el seu estat."""
    application = (
        GrantApplication.objects.select_for_update().select_related("call").get(pk=application.pk)
    )
    require(by, AMENDMENTS, application)
    if application.status not in WITH_REQUIREMENTS:
        raise GrantError(_("Un requeriment arriba quan la sol·licitud ja s'ha presentat."))
    if origin not in GrantRequirement.Origin.values:
        raise GrantError(_("L'origen és l'organisme o una iniciativa del club."))
    origin_reason, description = (origin_reason or "").strip(), (description or "").strip()
    if origin == GrantRequirement.Origin.CLUB and not origin_reason:
        raise MissingReason(_("Un requeriment d'iniciativa del club porta el motiu."))
    if not description:
        raise GrantError(_("Descriu què demana el requeriment."))
    received_on = _date(received_on, _("la data de rebuda"))
    term = application.call.amendment_term_days
    if due_on is None and term:  # RN-M09A-23: la proposta, que la persona pot canviar
        due_on = received_on + timedelta(days=term)
    if _date(due_on, _("la data límit")) < received_on:
        raise InvalidDates(_("La data límit no pot ser d'abans de la rebuda."))
    _check_responsible(responsible)
    requirement = GrantRequirement.objects.create(
        application=application,
        origin=origin,
        origin_reason=origin_reason if origin == GrantRequirement.Origin.CLUB else "",
        received_on=received_on,
        due_on=due_on,
        description=description,
        responsible=responsible,
        created_by=by,
    )
    audit.record(
        REQUIREMENT_RECORDED,
        actor=by,
        target=requirement,
        reason=origin_reason,
        details={"application": application.pk, "origin": origin, "due_on": due_on.isoformat()},
    )
    return requirement


def _open_requirement(requirement, by) -> GrantRequirement:
    requirement = (
        GrantRequirement.objects.select_for_update()
        .select_related("application")
        .get(pk=requirement.pk)
    )
    require(by, AMENDMENTS, requirement.application)
    if requirement.answered_on is not None:
        raise RequirementNotOpen(_("Aquest requeriment ja està respost."))
    return requirement


@transaction.atomic
def answer_requirement(requirement, *, answered_on, by) -> GrantRequirement:
    """`grants.answer_requirement`: la resposta tanca el requeriment (no hi ha més avisos)."""
    requirement = _open_requirement(requirement, by)
    if _date(answered_on, _("la data de resposta")) < requirement.received_on:
        raise InvalidDates(_("La resposta no pot ser d'abans de la rebuda."))
    requirement.answered_on = answered_on
    requirement.save()
    audit.record(
        REQUIREMENT_ANSWERED,
        actor=by,
        target=requirement,
        field="answered_on",
        new=answered_on.isoformat(),
    )
    return requirement


@transaction.atomic
def change_requirement_due_on(requirement, *, due_on, reason, by) -> GrantRequirement:
    """`grants.change_requirement_due_on` (RN-M09A-22, CA-M09A-22): amb motiu, al registre amb
    el valor anterior. Els avisos que falten es recalcularan sobre la data nova (T-M09A-06)."""
    requirement = _open_requirement(requirement, by)
    reason = (reason or "").strip()
    if not reason:
        raise MissingReason(_("Per canviar la data límit cal escriure'n el motiu."))
    if _date(due_on, _("la data límit")) < requirement.received_on:
        raise InvalidDates(_("La data límit no pot ser d'abans de la rebuda."))
    old = requirement.due_on
    requirement.due_on = due_on
    requirement.save()
    audit.record(
        REQUIREMENT_DUE_CHANGED,
        actor=by,
        target=requirement,
        field="due_on",
        old=old.isoformat(),
        new=due_on.isoformat(),
        reason=reason,
    )
    return requirement


@transaction.atomic
def set_justification_extension(application, *, extended_to, reason, by) -> GrantApplication:
    """`grants.set_justification_extension` (RN-M09A-20, CA-M09A-19): la pròrroga substitueix la
    data de justificació de la convocatòria per a aquesta sol·licitud; cada canvi, amb motiu."""
    application = GrantApplication.objects.select_for_update().get(pk=application.pk)
    require(by, AMENDMENTS, application)
    reason = (reason or "").strip()
    if not reason:
        raise MissingReason(_("Una pròrroga porta el motiu."))
    old = application.justification_extended_to
    application.justification_extended_to = _date(extended_to, _("la data de la pròrroga"))
    application.save()
    audit.record(
        EXTENSION_SET,
        actor=by,
        target=application,
        field="justification_extended_to",
        old=old.isoformat() if old else None,
        new=extended_to.isoformat(),
        reason=reason,
    )
    return application
