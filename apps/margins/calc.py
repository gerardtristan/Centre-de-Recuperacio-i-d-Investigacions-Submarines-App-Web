"""Càlcul del marge d'una activitat (T-M09-10; RN-M09-01 a 06, 13 i 22; RN-M02-43): una funció
pura, sense base de dades. Tot en cèntims (enters); el marge té signe i no hi ha cap coma
flotant. Els serveis del 09 (T-M09-11) hi porten les dades del 02, el 03, la 04 i el 09.

Marge = inscripcions + altres ingressos directes - costos directes - cost de material.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

FORECAST = "forecast"
REAL = "real"


@dataclass(frozen=True)
class MarginInputs:
    # RN-M09-02 (real) o preus de les inscripcions vives (previst, RN-M09-06).
    enrolments_cents: int
    # RN-M09-03: altres càrrecs pagats de l'activitat i patrocinis amb activitat; mai ajuts.
    other_direct_income_cents: int = 0
    # Repartiments de despeses a l'activitat per categoria, sense la factura del centre de lloguer.
    real_costs_cents: Mapping[str, int] = field(default_factory=dict)
    # PlannedCost per categoria (T-M09-09); només compten al marge previst.
    planned_costs_cents: Mapping[str, int] = field(default_factory=dict)
    # Comissions dels cobraments de l'activitat: sempre les reals (RN-M09-06).
    commissions_cents: int = 0
    # Lloguer de material (RN-M09-04, RN-M03-10): la factura del centre si s'ha registrat
    # (també la de cancel·lació, RN-M09-32) i, si no, l'estimació del 03; mai totes dues.
    rental_invoiced_cents: int | None = None
    rental_estimated_cents: int = 0
    # Cost d'ús del material del club del 03 (`club_use_cents`, RN-M09-05); None si no n'hi ha.
    material_real_cents: int | None = None
    # Cost de material previst de l'activitat (02, RN-M02-43); None sense el 03.
    material_planned_cents: int | None = None
    # Assistents o, si no hi ha llista, confirmats (RN-M09-13).
    participants: int = 0


@dataclass(frozen=True)
class Margin:
    kind: str
    income_enrolments_cents: int
    other_direct_income_cents: int
    direct_costs_cents: int
    material_cost_cents: int
    margin_cents: int
    margin_pct_tenths: int | None
    per_participant_cents: int | None
    participants: int
    breakdown: dict


def _round_half_up(numerator: int, denominator: int) -> int:
    # Meitat lluny del zero: -21,75 % fa -21,8 %, com el positiu (P-470).
    return int((Decimal(numerator) / Decimal(denominator)).quantize(Decimal(1), ROUND_HALF_UP))


def _check(name: str, value) -> None:
    # RN-M09-22: cèntims enters i mai negatius a l'entrada; només el marge té signe.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} ha de ser un enter de cèntims")
    if value < 0:
        raise ValueError(f"{name} no pot ser negatiu")


def compute(inputs: MarginInputs, kind: str) -> Margin:
    """Marge previst (`forecast`, activitat no tancada) o real (`real`, en tancar-la)."""
    if kind not in (FORECAST, REAL):
        raise ValueError(f"tipus de marge desconegut: {kind}")
    for name in ("enrolments_cents", "other_direct_income_cents", "commissions_cents"):
        _check(name, getattr(inputs, name))
    _check("rental_estimated_cents", inputs.rental_estimated_cents)
    _check("participants", inputs.participants)
    for name in ("rental_invoiced_cents", "material_real_cents", "material_planned_cents"):
        if getattr(inputs, name) is not None:
            _check(name, getattr(inputs, name))
    for source in (inputs.real_costs_cents, inputs.planned_costs_cents):
        for category, cents in source.items():
            _check(f"cost «{category}»", cents)

    # RN-M09-06: al previst, per a cada categoria, els reals si n'hi ha i, si no, els previstos.
    costs = dict(inputs.real_costs_cents)
    if kind == FORECAST:
        for category, cents in inputs.planned_costs_cents.items():
            costs.setdefault(category, cents)

    if inputs.rental_invoiced_cents is not None:
        rental = {
            "source": "invoiced",
            "cents": inputs.rental_invoiced_cents,
            "deviation_cents": inputs.rental_invoiced_cents - inputs.rental_estimated_cents,
        }
    else:
        rental = {"source": "estimated", "cents": inputs.rental_estimated_cents}

    # RN-M02-43: el previst del 02 només al marge previst i mentre no hi ha cost real del 03.
    if inputs.material_real_cents is not None:
        material, material_source = inputs.material_real_cents, "real"
    elif kind == FORECAST and inputs.material_planned_cents is not None:
        material, material_source = inputs.material_planned_cents, "planned"
    else:
        material, material_source = 0, "none"

    direct_costs = sum(costs.values()) + inputs.commissions_cents + rental["cents"]
    income = inputs.enrolments_cents + inputs.other_direct_income_cents
    margin = income - direct_costs - material
    participants = inputs.participants
    return Margin(
        kind=kind,
        income_enrolments_cents=inputs.enrolments_cents,
        other_direct_income_cents=inputs.other_direct_income_cents,
        direct_costs_cents=direct_costs,
        material_cost_cents=material,
        margin_cents=margin,
        # RN-M09-13: una xifra decimal (dècimes de punt); sense ingressos, no es mostra.
        margin_pct_tenths=_round_half_up(margin * 1000, income) if income else None,
        per_participant_cents=_round_half_up(margin, participants) if participants else None,
        participants=participants,
        breakdown={
            "costs_by_category": costs,
            "commissions_cents": inputs.commissions_cents,
            "rental": rental,
            "material_source": material_source,
        },
    )
