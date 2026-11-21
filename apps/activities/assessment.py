"""Avaluació per pràctica i «El meu progrés» (T-M02-17; P-M02-F pas 1; RN-M02-17; HU-M02-12 i
HU-M02-14; AC10a; C3). Portat de la branca aparcada.

- **Qui avalua.** Només qui fa classe a la sessió (AC10a amb l'abast «les seves sessions»,
  RN-RP-04). Fora, «no trobat» i registre.
- **Què.** A cada sessió **pràctica**, per a cada alumne confirmat: assolit, no assolit o
  necessita reforç, amb una observació curta. **Sense dades de salut** (RN-M02-17).
- **Conflicte d'interès** (M02-4): ningú no s'avalua a si mateix. Es rebutja i queda al registre.
- Es pot corregir; cada canvi queda al registre amb el valor anterior. La mateixa avaluació
  reenviada no escriu res.
- **«El meu progrés»** (`progress`): el que l'alumne veu de la seva pròpia inscripció. Cap dada
  d'altres alumnes.

**Concrecions:** només s'avalua qui té la inscripció confirmada, i no abans del dia de la sessió.

**Fora d'aquesta peça:** les classes de reforç (T-M02-18) i les pantalles.
"""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit

from . import permissions
from .models import Activity, Enrolment, PracticeAssessment, Session

S = Enrolment.Status
ASSESSED = "activities.assessment.recorded"
OWN_REJECTED = "activities.assessment.own_rejected"
MAX_NOTES = PracticeAssessment._meta.get_field("notes").max_length
ASSESSABLE = (
    Activity.Status.OPEN,
    Activity.Status.REGISTRATION_CLOSED,
    Activity.Status.IN_PROGRESS,
    Activity.Status.DONE,
)


@dataclass(frozen=True)
class SheetRow:
    enrolment_id: int
    name: str
    result: str | None
    result_label: str
    notes: str


def reject_own(by, enrolment, *, what, request=None) -> None:
    """Conflicte d'interès (M02-4): ningú no s'avalua ni es posa apte a si mateix. Es crida
    abans d'obrir cap transacció, perquè l'intent quedi al registre."""
    if getattr(by, "person_id", None) == enrolment.person_id:
        audit.record(
            OWN_REJECTED, actor=by, target=enrolment, details={"what": what}, request=request
        )
        raise ValidationError(_("No pots avaluar la teva pròpia inscripció."))


def students(session):
    """Els alumnes confirmats de l'activitat de la sessió."""
    rows = Enrolment.objects.filter(activity_id=session.activity_id, status=S.CONFIRMED)
    return rows.select_related("person").order_by("person__last_name", "person__first_name", "id")


def can_assess_now(session, today=None) -> bool:
    today = today or timezone.localdate()
    return (
        session.activity.status in ASSESSABLE
        and not session.cancelled
        and session.is_practice
        and timezone.localdate(session.starts_at) <= today
    )


def assess(session, enrolment, *, result, notes="", by, today=None, request=None):
    """Desa l'avaluació d'un alumne en una pràctica (HU-M02-12)."""
    permissions.require(by, permissions.ASSESSMENT, session, request=request)
    if session.activity_id != enrolment.activity_id:
        raise Http404
    if not session.is_practice:
        raise ValidationError(_("Només s'avaluen les sessions pràctiques."))
    reject_own(by, enrolment, what="assessment", request=request)
    if result not in PracticeAssessment.Result.values:
        raise ValidationError(_("Resultat desconegut."))
    notes = (notes or "").strip()
    if len(notes) > MAX_NOTES:
        raise ValidationError(
            _("L'observació no pot passar de %(max)s caràcters.") % {"max": MAX_NOTES}
        )
    if not can_assess_now(session, today):
        raise ValidationError(_("Encara no es pot avaluar aquesta sessió."))
    with transaction.atomic():
        row = Enrolment.objects.select_for_update(of=("self",)).get(pk=enrolment.pk)
        if row.status != S.CONFIRMED:
            raise ValidationError(_("Només s'avalua qui té la inscripció confirmada."))
        current = PracticeAssessment.objects.filter(session=session, enrolment=row).first()
        if current is not None and (current.result, current.notes) == (result, notes):
            return current
        old = current.result if current is not None else None
        current = current or PracticeAssessment(session=session, enrolment=row)
        current.result, current.notes = result, notes
        current.recorded_by, current.recorded_at = by, timezone.now()
        current.save()
        audit.record(
            ASSESSED, actor=by, target=current, field="result", old=old, new=result,
            details={"enrolment": row.pk, "session": session.pk}, request=request,
        )  # fmt: skip
        return current


def sheet(session, *, viewer, request=None) -> tuple[SheetRow, ...]:
    """Els alumnes d'una pràctica amb la seva avaluació, per a qui hi fa classe."""
    permissions.require(viewer, permissions.ASSESSMENT, session, write=False, request=request)
    marks = {a.enrolment_id: a for a in PracticeAssessment.objects.filter(session=session)}
    rows = []
    for row in students(session):
        mark = marks.get(row.pk)
        rows.append(
            SheetRow(
                enrolment_id=row.pk,
                name=f"{row.person.first_name} {row.person.last_name}".strip(),
                result=mark.result if mark else None,
                result_label=str(mark.get_result_display()) if mark else "",
                notes=mark.notes if mark else "",
            )
        )
    return tuple(rows)


def practice_sessions(viewer):
    """Les sessions pràctiques que `viewer` pot avaluar (les seves)."""
    return (
        permissions.sessions_for(viewer, permissions.ASSESSMENT)
        .filter(is_practice=True, cancelled=False)
        .exclude(activity__status__in=(Activity.Status.DRAFT, Activity.Status.CANCELLED))
        .select_related("activity")
        .order_by("starts_at", "id")
    )


def progress(enrolment) -> list[dict]:
    """«El meu progrés» (HU-M02-14): les pràctiques de l'activitat amb el resultat i
    l'observació de l'alumne. Només dades de la mateixa inscripció. Qui crida comprova que és
    seva (compte personal propi)."""
    marks = {a.session_id: a for a in PracticeAssessment.objects.filter(enrolment=enrolment)}
    sessions = Session.objects.filter(
        activity_id=enrolment.activity_id, is_practice=True, cancelled=False
    ).order_by("starts_at", "id")
    return [
        {
            "session": session,
            "result": marks[session.pk].result if session.pk in marks else None,
            "result_label": (
                str(marks[session.pk].get_result_display()) if session.pk in marks else ""
            ),
            "notes": marks[session.pk].notes if session.pk in marks else "",
        }
        for session in sessions
    ]
