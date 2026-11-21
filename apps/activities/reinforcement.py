"""Classes de reforç (T-M02-18; P-M02-F passos 2 a 4; RN-M02-14 i RN-M02-15; CA-M02-18; AC10b i
AC11).

1. **Proposta** (AC10b; qui fa classe a l'activitat): l'instructor proposa una o més classes de
   reforç per a un alumne, amb un motiu pedagògic. **Sense dades de salut** (RN-M02-17).
2. **Confirmació** (AC11): el responsable la confirma i hi posa les sessions (data, lloc i
   instructor). Són sessions **només d'aquell alumne**: l'horari del grup no canvia. Es crea un
   càrrec «inscripció» a la mateixa activitat i departament, amb el preu de reforç de la fitxa
   del catàleg, i l'alumne rep l'avís amb les dates i el preu. O la rebutja, amb motiu.
3. Un curs pot passar a «fet» amb alumnes en reforç (RN-M02-14): les classes de reforç continuen
   lligades a la mateixa activitat.

**Preu** (RN-M02-15; supòsit S-M02-08, per confirmar per la junta): un sol import **per proposta
confirmada**, el `reinforcement_price_cents` de la fitxa. Si la fitxa no en té, no es pot
confirmar fins que se n'hi posi un (pot ser 0: llavors no hi ha càrrec).

**Concrecions d'implementació** (dins de les regles; al diari de la T-M02-18)

- Una inscripció només pot tenir una proposta per resoldre alhora.
- Es poden proposar d'1 a 10 classes; en confirmar, cal donar exactament aquest nombre de
  sessions.
- Ningú no proposa reforç per a la seva pròpia inscripció (conflicte d'interès).

- Les sessions de reforç compleixen els requisits per fer classe (RN-M02-26, T-M02-30) i van a
  un lloc actiu, com les del grup. No es copien en duplicar (RN-M02-21).

**Fora d'aquesta peça:** pagar el càrrec (05b; mentre no es pagui, surt a «Què falta per tancar»,
`closing.closing_blockers`), l'avís a l'alumne amb les dates i el preu (T-M02-21) i les
pantalles. Portat de la branca aparcada.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, charges
from apps.core.models import Charge

from . import assessment, permissions, sessions
from . import enrolment as enrolments
from .charges import CHARGE_ORIGIN
from .models import Activity, Enrolment, ReinforcementRequest, Session

S = Enrolment.Status
R = ReinforcementRequest.Status
PROPOSED = "activities.reinforcement.proposed"
CONFIRMED = "activities.reinforcement.confirmed"
REJECTED = "activities.reinforcement.rejected"
MAX_REASON = 500
MAX_CLASSES = 10
ALLOWED = (
    Activity.Status.OPEN,
    Activity.Status.REGISTRATION_CLOSED,
    Activity.Status.IN_PROGRESS,
    Activity.Status.DONE,
)


def _reason(text, message) -> str:
    text = (text or "").strip()
    if not text:
        raise ValidationError(message)
    if len(text) > MAX_REASON:
        raise ValidationError(
            _("El motiu no pot passar de %(max)s caràcters.") % {"max": MAX_REASON}
        )
    return text


def price_for(activity) -> int | None:
    """El preu d'una proposta de reforç d'aquest curs, o `None` si la fitxa no en té."""
    return activity.catalogue_entry.reinforcement_price_cents


def propose(enrolment, *, by, classes, reason, request=None) -> ReinforcementRequest:
    """L'instructor proposa classes de reforç per a un alumne (HU-M02-13)."""
    activity = enrolment.activity
    permissions.require(by, permissions.REINFORCEMENT_PROPOSE, activity, request=request)
    assessment.reject_own(by, enrolment, what="reinforcement", request=request)
    if activity.kind != Activity.Kind.COURSE:
        raise ValidationError(_("Només els cursos tenen classes de reforç."))
    if activity.status not in ALLOWED:
        raise ValidationError(_("Ara no es pot proposar reforç en aquesta activitat."))
    if isinstance(classes, bool) or not isinstance(classes, int) or not 1 <= classes <= MAX_CLASSES:
        raise ValidationError(
            _("El nombre de classes ha de ser entre 1 i %(max)s.") % {"max": MAX_CLASSES}
        )
    reason = _reason(reason, _("Cal explicar el motiu del reforç."))
    with transaction.atomic():
        row = Enrolment.objects.select_for_update(of=("self",)).get(pk=enrolment.pk)
        if row.status != S.CONFIRMED:
            raise ValidationError(_("Només es proposa reforç a qui té la inscripció confirmada."))
        if ReinforcementRequest.objects.filter(enrolment=row, status=R.PROPOSED).exists():
            raise ValidationError(_("Aquest alumne ja té una proposta de reforç per resoldre."))
        proposal = ReinforcementRequest.objects.create(
            enrolment=row, proposed_by=by, classes=classes, reason=reason, status=R.PROPOSED
        )
        audit.record(
            PROPOSED,
            actor=by,
            target=proposal,
            details={"enrolment": row.pk, "classes": classes},
            request=request,
        )
    return proposal


def _locked(proposal) -> ReinforcementRequest:
    locked = (
        ReinforcementRequest.objects.select_for_update(of=("self",))
        .select_related("enrolment__activity__catalogue_entry", "enrolment__person")
        .get(pk=proposal.pk)
    )
    if locked.status != R.PROPOSED:
        raise ValidationError(_("Aquesta proposta de reforç ja està resolta."))
    return locked


@transaction.atomic
def confirm(proposal, *, by, sessions_data, request=None) -> ReinforcementRequest:
    """El responsable confirma la proposta i en crea les sessions i el càrrec (CA-M02-18).
    `sessions_data`: una entrada per classe, amb `kind`, `starts_at`, `ends_at`, `place` i
    `instructors`."""
    permissions.require(by, permissions.REINFORCEMENT_DECIDE)
    locked = _locked(proposal)
    row = locked.enrolment
    activity = enrolments.lock(row.activity)
    if activity.status not in ALLOWED:
        raise ValidationError(_("Ara no es pot confirmar reforç en aquesta activitat."))
    if row.status != S.CONFIRMED:
        raise ValidationError(_("La inscripció d'aquest alumne ja no és confirmada."))
    sessions_data = list(sessions_data or [])
    if len(sessions_data) != locked.classes:
        raise ValidationError(
            _("Cal posar data a les %(count)s classes proposades.") % {"count": locked.classes}
        )
    price = price_for(activity)
    if price is None:
        raise ValidationError(
            _(
                "La fitxa d'aquest curs no té preu de reforç. Posa-n'hi un al catàleg (pot ser 0) "
                "abans de confirmar."
            )
        )
    created = []
    for raw in sessions_data:
        data = sessions._clean_session(
            {
                "kind": raw.get("kind"),
                "starts_at": raw.get("starts_at"),
                "ends_at": raw.get("ends_at"),
                "is_practice": True,
            }
        )
        if data["ends_at"] <= data["starts_at"]:
            raise ValidationError(_("La sessió ha d'acabar després de començar."))
        place = raw.get("place")
        sessions._place(place)
        people = sessions._instructors(raw.get("instructors") or ())
        sessions._check_requirements(people, data["starts_at"])
        session = Session.objects.create(
            activity=activity, reinforcement_for=row, place=place, **data
        )
        session.instructors.set(people)
        audit.record(
            sessions.SESSION_ADDED,
            actor=by,
            target=session,
            details={
                "activity": activity.pk,
                "kind": session.kind,
                "starts_at": session.starts_at.isoformat(),
                "place": place.pk,
                "instructors": sorted(p.pk for p in people),
                "reinforcement_for": row.pk,
            },
            request=request,
        )
        created.append(session)
    if price > 0:
        concept = _("Reforç: %(title)s") % {"title": activity.title}
        locked.charge = charges.create_charge(
            row.person,
            kind=Charge.Kind.ENROLMENT,
            amount_cents=price,
            concept=concept[: Charge._meta.get_field("concept").max_length],
            origin=CHARGE_ORIGIN,
            by=by,
            department=activity.department,
            cost_centre=activity.cost_centre,
        )
    locked.status = R.CONFIRMED
    locked.price_cents = price
    locked.decided_by = by
    locked.decided_at = timezone.now()
    locked.save()
    audit.record(
        CONFIRMED,
        actor=by,
        target=locked,
        field="status",
        old=R.PROPOSED,
        new=R.CONFIRMED,
        details={
            "sessions": [s.pk for s in created],
            "price_cents": price,
            "charge": locked.charge_id,
        },
        request=request,
    )
    return locked


@transaction.atomic
def reject(proposal, *, by, reason, request=None) -> ReinforcementRequest:
    permissions.require(by, permissions.REINFORCEMENT_DECIDE)
    reason = _reason(reason, _("Per rebutjar la proposta cal un motiu."))
    locked = _locked(proposal)
    locked.status = R.REJECTED
    locked.decided_by = by
    locked.decided_at = timezone.now()
    locked.decision_reason = reason
    locked.save()
    audit.record(
        REJECTED,
        actor=by,
        target=locked,
        field="status",
        old=R.PROPOSED,
        new=R.REJECTED,
        reason=reason,
        request=request,
    )
    return locked


def for_enrolment(enrolment):
    """Les propostes de reforç d'una inscripció, amb les seves sessions (per a «El meu progrés»)."""
    return ReinforcementRequest.objects.filter(enrolment=enrolment).order_by("created_at", "id")


def open_proposals():
    """Les propostes per resoldre, per a qui té AC11."""
    return (
        ReinforcementRequest.objects.filter(status=R.PROPOSED)
        .select_related("enrolment__activity", "enrolment__person", "proposed_by__person")
        .order_by("created_at", "id")
    )


def unpaid_charges(activity):
    """Càrrecs de reforç de l'activitat que encara no s'han pagat (RN-M02-22)."""
    return Charge.objects.filter(
        pk__in=ReinforcementRequest.objects.filter(
            enrolment__activity=activity, status=R.CONFIRMED, charge__isnull=False
        ).values("charge_id"),
        status=Charge.Status.PENDING,
    )
