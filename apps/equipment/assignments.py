"""Assignar material a un participant (T-M03-08; P-M03-D passos 1-3; RN-M03-01, 02, 03, 06 i 08;
CA-M03-02, 03, 04 i 06; MT6).

- **Del club** (`assign_club`): una peça disponible de la talla. No es pot assignar una peça en
  revisió o de baixa (CA-M03-03), ni una amb la revisió vençuda abans de l'últim dia (CA-M03-04).
  Dues assignacions vives de la mateixa peça amb dies que es toquin les rebutja la base de dades
  (restricció d'exclusió, RN-M03-02; CA-M03-02). Cost per al club: dies × cost d'ús vigent el
  primer dia (RN-M03-08).
- **Llogat** (`assign_rented`): la tarifa vigent el primer dia al centre (actiu) per a aquell tipus;
  es copien el preu de cost i el preu per al participant (de soci o de no soci, segons el preu de la
  inscripció; sense preu de no soci, el de soci [A validar: junta, S-M03-01]; RN-M03-06).
  Sense centre, el que proposa el lloc (`places.proposed_centre_for`, RN-M03-24; CA-M03-23).
- **Propi** (`assign_own`): cost 0.
- Només per a inscripcions confirmades. Amb l'abast «les seves sessions» (instructor), només a les
  activitats on fa classe. Cada assignació queda al registre.

`available_items` dona les peces que es poden oferir (CA-M03-06). El càrrec del lloguer al
participant (RN-M03-11) és de la T-M03-11, que espera la resposta de la junta.
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.backends.postgresql.psycopg_any import DateRange
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.activities.models import Enrolment
from apps.core import audit

from .access import require
from .centres import rate_on
from .costs import usage_cost_on
from .models import EquipmentAssignment, EquipmentItem
from .places import proposed_centre_for

ASSIGN = "equipment.assignments.manage"  # MT6
ASSIGNED = "equipment.assignment_created"
ORIGIN = EquipmentAssignment.Origin


def days_of(activity, session=None) -> tuple:
    """(Primer, últim) dia de l'activitat o de la sessió d'una classe de reforç."""
    if session is not None:
        day = session.starts_at.date()
        return day, day
    return activity.starts_on, activity.ends_on


def period_of(activity, session=None) -> DateRange:
    first, last = days_of(activity, session)
    return DateRange(first, last, "[]")


def busy(period):
    """Assignacions vives de peces del club amb dies que es toquen amb `period`."""
    return EquipmentAssignment.objects.filter(
        item__isnull=False, status__in=EquipmentAssignment.LIVE, period__overlap=period
    )


def available_items(activity, equipment_type, *, size="", litres=None, session=None):
    """Peces que es poden oferir: disponibles, de la talla, sense revisió vençuda i lliures."""
    last = days_of(activity, session)[1]
    items = EquipmentItem.objects.filter(
        type=equipment_type, status=EquipmentItem.Status.AVAILABLE
    ).exclude(pk__in=busy(period_of(activity, session)).values("item"))
    items = items.filter(Q(next_review_on__isnull=True) | Q(next_review_on__gte=last))
    if size:
        items = items.filter(size=size)
    if litres is not None:
        items = items.filter(litres=litres)
    return items.order_by("code")


def _confirmed(enrolment, by, session):
    activity = enrolment.activity
    require(by, ASSIGN, session or activity)
    enrolment = Enrolment.objects.select_for_update().get(pk=enrolment.pk)
    if enrolment.status != Enrolment.Status.CONFIRMED:
        raise ValidationError(_("Només s'assigna material a una inscripció confirmada."))
    if session is not None and session.activity_id != activity.pk:
        raise ValidationError(_("Aquesta sessió no és de l'activitat."))
    return enrolment


def _create(enrolment, *, by, session, **fields) -> EquipmentAssignment:
    note = (fields.pop("note", "") or "").strip()
    try:
        with transaction.atomic():
            assignment = EquipmentAssignment.objects.create(
                activity=enrolment.activity, enrolment=enrolment, session=session,
                period=period_of(enrolment.activity, session), created_by=by, note=note, **fields,
            )  # fmt: skip
    except IntegrityError as error:
        if "assignment_item_no_overlap" in str(error):
            raise ValidationError(_("Aquesta peça ja és assignada aquells dies.")) from error
        raise
    audit.record(
        ASSIGNED, actor=by, target=assignment,
        details={"activity": enrolment.activity_id, "origin": assignment.origin,
                 "item": assignment.item_id, "cost_cents": assignment.cost_cents},
    )  # fmt: skip
    return assignment


@transaction.atomic
def assign_club(enrolment, item, *, by, session=None, note="") -> EquipmentAssignment:
    enrolment = _confirmed(enrolment, by, session)
    item = EquipmentItem.objects.select_for_update().get(pk=item.pk)
    if item.status != EquipmentItem.Status.AVAILABLE:
        raise ValidationError(_("Aquesta peça no està disponible."))
    first, last = days_of(enrolment.activity, session)
    if item.next_review_on is not None and item.next_review_on < last:
        raise ValidationError(_("Aquesta peça té la revisió vençuda abans de l'últim dia."))
    cost = ((last - first).days + 1) * usage_cost_on(item.type, first)
    return _create(
        enrolment, by=by, session=session, equipment_type=item.type, origin=ORIGIN.CLUB, item=item,
        cost_cents=cost, participant_price_cents=0, note=note,
    )  # fmt: skip


@transaction.atomic
def assign_rented(
    enrolment, equipment_type, centre=None, *, by, session=None, note=""
) -> EquipmentAssignment:
    """Sense centre, el proposat pel lloc (RN-M03-24, T-M03-26); es pot triar qualsevol altre."""
    enrolment = _confirmed(enrolment, by, session)
    centre = centre or proposed_centre_for(enrolment.activity, session)
    if centre is None:
        raise ValidationError(_("Tria el centre on es lloga el material."))
    rate = rate_on(centre, equipment_type, days_of(enrolment.activity, session)[0])
    if rate is None:
        raise ValidationError(_("Aquest centre no té cap tarifa vigent per a aquest material."))
    price = rate.member_price_cents
    if enrolment.price_kind == Enrolment.PriceKind.NON_MEMBER and rate.non_member_price_cents:
        price = rate.non_member_price_cents
    return _create(
        enrolment, by=by, session=session, equipment_type=equipment_type, origin=ORIGIN.RENTED,
        centre=centre, rate=rate, cost_cents=rate.cost_cents, participant_price_cents=price,
        note=note,
    )  # fmt: skip


@transaction.atomic
def assign_own(enrolment, equipment_type, *, by, session=None) -> EquipmentAssignment:
    enrolment = _confirmed(enrolment, by, session)
    return _create(
        enrolment, by=by, session=session, equipment_type=equipment_type, origin=ORIGIN.OWN,
        cost_cents=0, participant_price_cents=0,
    )  # fmt: skip
