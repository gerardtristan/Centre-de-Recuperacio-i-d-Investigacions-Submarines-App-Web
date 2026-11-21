"""Marge d'una activitat amb les dades dels mòduls (T-M09-11; RN-M09-01 a 06; RN-M02-43).

- **Previst:** inscripcions vives del 02, costos previstos, repartiments de despeses (T-M09-07)
  com a costos reals i cost de material previst.
- **Real** (RN-M09-02 i 04): ingressos de la 04 dels càrrecs de les inscripcions menys les seves
  devolucions i retorns (un moviment anul·lat no compta, RN-T25), comissions d'aquests cobraments,
  repartiments i participants del 02 (assistents o confirmades).
- **Material** (RN-M09-04 i 05; RN-M03-10; T-M09-11b): el lloguer és la factura del centre
  repartida a l'activitat (categories `is_material_rental`) i, mentre no n'hi ha, l'estimació del
  03; mai totes dues. El cost de material és el cost d'ús del material del club del 03.

shortcut: els altres ingressos directes (altres càrrecs i patrocinis amb activitat) compten zero
fins que el càrrec o l'ingrés portin l'activitat. Lectura: qui el mostra comprova MG6."""

from django.db.models import Count, Q, Sum

from apps.activities import attendance
from apps.activities.models import Activity, Enrolment
from apps.equipment.costs import activity_material_cost
from apps.expenses.allocation import allocated_costs, rental_invoiced
from apps.treasury.models import Movement

from . import calc
from .planned import planned_costs


def _live_enrolments(activity) -> tuple[int, int]:
    """(Preus de les inscripcions vives en cèntims, nombre d'inscripcions vives), RN-M09-06: les
    pendents de pagament i les confirmades (pagades o gratuïtes)."""
    live = Enrolment.objects.filter(
        activity=activity, status__in=(Enrolment.Status.PENDING_PAYMENT, Enrolment.Status.CONFIRMED)
    ).aggregate(cents=Sum("price_cents"), n=Count("id"))
    return live["cents"] or 0, live["n"]


def activity_margin(activity: Activity, kind: str = calc.FORECAST) -> calc.Margin:
    """`margins.activity_margin` (M09-8). Al previst: inscripcions vives, costos previstos per
    categoria, cost de material previst del 02 per participant (RN-M02-43) i, quan n'hi hagi,
    els costos i les comissions reals."""
    if kind == calc.REAL:
        return calc.compute(real_inputs(activity), calc.REAL)
    income, participants = _live_enrolments(activity)
    per_participant = activity.material_cost_cents
    material = activity_material_cost(activity)
    return calc.compute(
        calc.MarginInputs(
            enrolments_cents=income,
            real_costs_cents=allocated_costs(activity),
            planned_costs_cents=planned_costs(activity),
            rental_invoiced_cents=rental_invoiced(activity),
            rental_estimated_cents=material.rental_cost_estimated_cents,
            # RN-M02-43: el previst del 02 només mentre no hi ha cost real del material del club.
            material_real_cents=material.club_use_cents or None,
            material_planned_cents=(
                None if per_participant is None else per_participant * participants
            ),
            participants=participants,
        ),
        calc.FORECAST,
    )


def activity_movements(activity):
    """Els moviments vigents de la 04 dels cobraments de les inscripcions de l'activitat."""
    charges = Enrolment.objects.filter(activity=activity, charge__isnull=False).values("charge")
    return Movement.objects.filter(payment__charge__in=charges, reversal__isnull=True).exclude(
        kind=Movement.Kind.REVERSAL
    )


def signed_income(movements) -> tuple[int, int]:
    """(Ingressos menys devolucions i retorns, comissions), en cèntims."""
    K = Movement.Kind
    totals = movements.aggregate(
        income=Sum("amount_cents", filter=Q(kind=K.INCOME)),
        back=Sum("amount_cents", filter=Q(kind__in=(K.REFUND, K.RETURN))),
        fees=Sum("amount_cents", filter=Q(kind=K.FEE)),
    )
    return (totals["income"] or 0) - (totals["back"] or 0), totals["fees"] or 0


def real_inputs(activity) -> calc.MarginInputs:
    enrolments, commissions = signed_income(activity_movements(activity))
    material = activity_material_cost(activity)
    return calc.MarginInputs(
        enrolments_cents=max(enrolments, 0),
        real_costs_cents=allocated_costs(activity),
        commissions_cents=commissions,
        rental_invoiced_cents=rental_invoiced(activity),
        rental_estimated_cents=material.rental_cost_estimated_cents,
        material_real_cents=material.club_use_cents,
        participants=attendance.participants(activity),
    )
