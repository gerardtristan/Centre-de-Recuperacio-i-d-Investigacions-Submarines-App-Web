"""Marge d'una activitat amb les dades dels mòduls (T-M09-11; RN-M09-01 a 06; RN-M02-43). Aquí
només hi ha la part prevista, amb les inscripcions vives del 02 i els repartiments de despeses
(T-M09-07) com a costos reals; el marge real (ingressos i comissions de la 04, lloguers i cost
d'ús del material) espera la T-M03-13. Lectura: qui el mostra comprova MG6."""

from django.db.models import Count, Sum

from apps.activities.models import Activity, Enrolment
from apps.expenses.allocation import allocated_costs

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
    if kind != calc.FORECAST:
        raise NotImplementedError("El marge real arriba amb la T-M09-07 i la T-M03-13.")
    income, participants = _live_enrolments(activity)
    per_participant = activity.material_cost_cents
    return calc.compute(
        calc.MarginInputs(
            enrolments_cents=income,
            # shortcut: tots els repartiments compten com a costos per categoria, també la factura
            # del centre de lloguer; separar-la (RN-M09-04, sense duplicar) és de la T-M03-13.
            real_costs_cents=allocated_costs(activity),
            planned_costs_cents=planned_costs(activity),
            material_planned_cents=(
                None if per_participant is None else per_participant * participants
            ),
            participants=participants,
        ),
        calc.FORECAST,
    )
