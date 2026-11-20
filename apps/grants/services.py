"""Ajuts: sol·licitud, elegibilitat i transicions (M09-ajuts-5 a 8; T-M09A-03 i T-M09A-04). Cap
altra app escriu als models de `grants`. Cada servei comprova el permís (AJ1 a AJ13, T-M09-30) i
el de la Junta, només sobre les sol·licituds de què és responsable."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import Role
from apps.core.permissions import active_role_codes, has_perm
from apps.treasury.models import CostCentre

from .models import ApplicationDocument, ApplicationTransition, GrantApplication, GrantCall

ELIGIBILITY = "grants.eligibility"  # AJ2
PREPARE = "grants.applications.prepare"  # AJ4

APPLICATION_CREATED = "grants.application_created"
ELIGIBILITY_REVIEWED = "grants.eligibility_reviewed"
APPLICATION_TRANSITIONED = "grants.application_transitioned"

# Qui pot ser responsable d'una sol·licitud (M09-ajuts-4; S-M09A-01): llista de rols, codi.
RESPONSIBLE_ROLES = frozenset({Role.Code.TREASURER, Role.Code.BOARD, Role.Code.ADMINISTRATOR})
S = GrantApplication.Status


class GrantError(ValidationError):
    """A la petició li falta alguna dada o en té alguna que no val."""


class EligibilityNotReviewed(GrantError):
    """RN-M09A-03: sense la revisió d'una persona, la sol·licitud no passa a «en preparació»."""


def require(by, code, obj=None) -> None:
    if not has_perm(by, code, obj, write=True):
        raise Http404


def _check_responsible(person) -> None:
    accounts = Account.objects.filter(person=person, kind=Account.Kind.ADMIN)
    if not any(RESPONSIBLE_ROLES & active_role_codes(account) for account in accounts):
        raise GrantError(_("El responsable ha de tenir el rol de tresorer, junta o administrador."))


def _move(application, to_status, *, reason, by) -> None:
    """Un canvi d'estat: la transició (només INSERT), l'estat i el registre (RN-M09A-16)."""
    old = application.status
    ApplicationTransition.objects.create(
        application=application, from_status=old, to_status=to_status, reason=reason, actor=by
    )
    application.status = to_status
    application.save()
    audit.record(
        APPLICATION_TRANSITIONED,
        actor=by,
        target=application,
        field="status",
        old=old,
        new=to_status,
        reason=reason,
    )


@transaction.atomic
def create_application(
    call: GrantCall,
    *,
    responsible,
    department,
    by,
    cost_centre=None,
    amount_requested_cents=None,
) -> GrantApplication:
    """P-M09A-A, pas 2: sol·licitud «detectada» amb els documents requerits de la convocatòria."""
    application = GrantApplication(
        call=call,
        responsible=responsible,
        department=department,
        cost_centre=cost_centre,
        amount_requested_cents=amount_requested_cents,
        created_by=by,
    )
    require(by, PREPARE, application)
    _check_responsible(responsible)
    if amount_requested_cents is not None and (
        isinstance(amount_requested_cents, bool)
        or not isinstance(amount_requested_cents, int)
        or amount_requested_cents < 0
    ):
        raise GrantError(_("L'import ha de ser un enter de cèntims, zero o més."))
    if not department.active or (
        cost_centre is not None
        and not CostCentre.selectable().filter(pk=cost_centre.pk, department=department).exists()
    ):
        raise GrantError(_("Tria un departament actiu i un centre de cost seu."))
    application.save()
    ApplicationDocument.objects.bulk_create(
        ApplicationDocument(application=application, name=document.name)
        for document in call.documents.all()
    )
    audit.record(
        APPLICATION_CREATED,
        actor=by,
        target=application,
        details={"call": call.pk, "department": department.name},
    )
    return application


@transaction.atomic
def review_eligibility(call: GrantCall, *, status: str, notes: str, by) -> GrantCall:
    """P-M09A-B (RN-M09A-03, CA-M09A-04): una persona marca la convocatòria elegible o no, amb
    notes. Si no ho és, les sol·licituds detectades o en preparació es tanquen amb el motiu."""
    require(by, ELIGIBILITY)
    notes = (notes or "").strip()
    if status not in (GrantCall.Eligibility.ELIGIBLE, GrantCall.Eligibility.NOT_ELIGIBLE):
        raise GrantError(_("L'elegibilitat és «elegible» o «no elegible»."))
    if not notes:
        raise GrantError(_("Escriu per què és o no és elegible."))
    call = GrantCall.objects.select_for_update().get(pk=call.pk)
    old = call.eligibility_status
    call.eligibility_status, call.eligibility_notes = status, notes
    call.eligibility_reviewed_by, call.eligibility_reviewed_at = by, timezone.now()
    call.save()
    audit.record(
        ELIGIBILITY_REVIEWED,
        actor=by,
        target=call,
        field="eligibility_status",
        old=old,
        new=status,
        reason=notes,
    )
    if status == GrantCall.Eligibility.NOT_ELIGIBLE:
        reason = f"{_('No elegible')}: {notes}"
        for application in call.applications.select_for_update().filter(
            status__in=[S.DETECTED, S.PREPARING]
        ):
            application.closed_reason = reason
            _move(application, S.CLOSED, reason=reason, by=by)
    return call
