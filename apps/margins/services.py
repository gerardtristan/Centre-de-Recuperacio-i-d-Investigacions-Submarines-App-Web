"""Marge d'una activitat amb les dades dels mòduls (T-M09-11; RN-M09-01 a 06; RN-M02-43). Aquí
només hi ha la part prevista: el marge real (repartiments de despeses, comissions, lloguers i
cost d'ús del material) espera la T-M09-07 i la T-M03-13. Lectura: qui el mostra comprova MG6."""

from apps.activities.models import Activity

from . import calc
from .planned import planned_costs


def _live_enrolments(activity) -> tuple[int, int]:
    """(Preus de les inscripcions vives en cèntims, nombre d'inscripcions vives), RN-M09-06.
    shortcut: les inscripcions del 02 encara no existeixen i això torna (0, 0); quan arribin, se
    sumen aquí els preus de les pendents de pagament i les pagades."""
    return 0, 0


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
            planned_costs_cents=planned_costs(activity),
            material_planned_cents=(
                None if per_participant is None else per_participant * participants
            ),
            participants=participants,
        ),
        calc.FORECAST,
    )
