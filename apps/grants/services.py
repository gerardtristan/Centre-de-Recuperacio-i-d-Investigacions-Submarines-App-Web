"""Ajuts: sol·licitud, elegibilitat i transicions (M09-ajuts-5 a 8; T-M09A-03 i T-M09A-04). Cap
altra app escriu als models de `grants`. Cada servei comprova el permís (AJ1 a AJ13, T-M09-30) i
el de la Junta, només sobre les sol·licituds de què és responsable."""

from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
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
CLOSE = "grants.applications.close"  # AJ8
UNDO = "grants.applications.undo"  # AJ9

APPLICATION_CREATED = "grants.application_created"
ELIGIBILITY_REVIEWED = "grants.eligibility_reviewed"
APPLICATION_TRANSITIONED = "grants.application_transitioned"
DOCUMENT_CHANGED = "grants.document_changed"

# Qui pot ser responsable d'una sol·licitud (M09-ajuts-4; S-M09A-01): llista de rols, codi.
RESPONSIBLE_ROLES = frozenset({Role.Code.TREASURER, Role.Code.BOARD, Role.Code.ADMINISTRATOR})
S = GrantApplication.Status


class GrantError(ValidationError):
    """A la petició li falta alguna dada o en té alguna que no val."""


class EligibilityNotReviewed(GrantError):
    """RN-M09A-03: sense la revisió d'una persona, la sol·licitud no passa a «en preparació»."""


class InvalidTransition(GrantError):
    """RN-M09A-01: aquest canvi d'estat no és permès."""


class MissingDocuments(GrantError):
    """RN-M09A-02 (CA-M09A-05): falten documents requerits per marcar a punt."""


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


# RN-M09A-01. Concedida i denegada (resolució, T-M09A-07) i justificada (paquet, T-M09A-10)
# s'afegeixen amb les seves tasques, que porten les dades que demanen.
TRANSITIONS = {
    S.DETECTED: {S.PREPARING, S.CLOSED},
    S.PREPARING: {S.SUBMITTED, S.CLOSED},
    S.JUSTIFIED: {S.CLOSED},
}
EDITABLE_DOCUMENTS = (S.DETECTED, S.PREPARING)


def _date(value, label):
    if not isinstance(value, date):
        raise GrantError(_("Cal %(field)s.") % {"field": label})
    return value


@transaction.atomic
def transition(application, to_status, *, by, reason="", **data) -> GrantApplication:
    """`grants.transition` (M09-8). Presentar demana `submitted_on`, `submission_ref`,
    `amount_requested_cents` i tots els documents a punt; tancar sense presentar-la, el motiu."""
    application = (
        GrantApplication.objects.select_for_update().select_related("call").get(pk=application.pk)
    )
    old, reason = application.status, (reason or "").strip()
    require(by, CLOSE if old == S.JUSTIFIED else PREPARE, application)
    if to_status not in TRANSITIONS.get(old, ()):
        raise InvalidTransition(_("Aquest canvi d'estat no és permès."))
    call = application.call
    if to_status == S.PREPARING:
        if call.eligibility_status == GrantCall.Eligibility.PENDING:
            raise EligibilityNotReviewed(_("Primer cal revisar l'elegibilitat de la convocatòria."))
        if call.eligibility_status == GrantCall.Eligibility.NOT_ELIGIBLE:
            raise InvalidTransition(_("La convocatòria no és elegible."))
    elif to_status == S.SUBMITTED:
        _submit(application, call, data)
    elif old in EDITABLE_DOCUMENTS:  # tancar sense presentar-la
        if not reason:
            raise GrantError(_("Escriu per què no es presenta."))
        application.closed_reason = reason
    _move(application, to_status, reason=reason, by=by)
    return application


def _submit(application, call, data) -> None:
    submitted_on = _date(data.get("submitted_on"), _("la data de presentació"))
    ref = (data.get("submission_ref") or "").strip()
    amount = data.get("amount_requested_cents")
    if not ref or len(ref) > 60:
        raise GrantError(_("Cal el número de registre d'entrada (60 caràcters com a màxim)."))
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise GrantError(_("Cal l'import demanat, en cèntims."))
    missing = [d.name for d in application.documents.all() if not d.ready]
    if missing:
        raise MissingDocuments(
            _("Falten documents per marcar a punt: %(names)s.") % {"names": ", ".join(missing)}
        )
    application.submitted_on, application.submission_ref = submitted_on, ref
    application.amount_requested_cents = amount
    # RN-M09A-05: amb el termini publicat, es calcula; si no, la que escrigui el responsable.
    if call.max_resolution_days:
        application.expected_response_on = submitted_on + timedelta(days=call.max_resolution_days)
    elif data.get("expected_response_on") is not None:
        application.expected_response_on = _date(
            data["expected_response_on"], _("la data prevista de resposta")
        )


@transaction.atomic
def undo_last_transition(application, *, reason, by) -> GrantApplication:
    """AJ9 (RN-M09A-01): l'administrador desfà l'última transició amb motiu; queda com una
    transició nova. Les dades que s'hi havien posat no s'esborren."""
    require(by, UNDO)
    reason = (reason or "").strip()
    if not reason:
        raise GrantError(_("Per desfer un canvi d'estat cal escriure'n el motiu."))
    application = GrantApplication.objects.select_for_update().get(pk=application.pk)
    last = application.transitions.order_by("pk").last()
    if last is None:
        raise InvalidTransition(_("Aquesta sol·licitud no té cap canvi d'estat per desfer."))
    _move(application, last.from_status, reason=reason, by=by)
    return application


def _editable_document(document, by) -> ApplicationDocument:
    document = (
        ApplicationDocument.objects.select_for_update()
        .select_related("application")
        .get(pk=document.pk)
    )
    require(by, PREPARE, document.application)
    if document.application.status not in EDITABLE_DOCUMENTS:
        raise GrantError(_("Els documents es preparen abans de presentar la sol·licitud."))
    return document


@transaction.atomic
def set_document_ready(document, *, ready: bool, by) -> ApplicationDocument:
    """P-M09A-C, pas 1: marcar un document a punt (o treure-li la marca), al registre."""
    document = _editable_document(document, by)
    old, document.ready, document.uploaded_by = document.ready, bool(ready), by
    document.save()
    audit.record(
        DOCUMENT_CHANGED, actor=by, target=document, field="ready", old=old, new=document.ready
    )
    return document


@transaction.atomic
def add_document(application, *, name: str, by) -> ApplicationDocument:
    """Un document que no era a la convocatòria."""
    application = GrantApplication.objects.select_for_update().get(pk=application.pk)
    require(by, PREPARE, application)
    if application.status not in EDITABLE_DOCUMENTS:
        raise GrantError(_("Els documents es preparen abans de presentar la sol·licitud."))
    name = (name or "").strip()
    if not name or len(name) > 200:
        raise GrantError(_("Cal el nom del document (200 caràcters com a màxim)."))
    try:
        with transaction.atomic():
            document = ApplicationDocument.objects.create(application=application, name=name)
    except IntegrityError as error:
        raise GrantError(_("La sol·licitud ja té un document amb aquest nom.")) from error
    audit.record(DOCUMENT_CHANGED, actor=by, target=document, field="name", new=name)
    return document
