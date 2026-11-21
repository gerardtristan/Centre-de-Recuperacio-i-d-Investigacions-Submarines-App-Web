"""Cost de material estàndard d'una activitat, per participant (T-M03-27; RN-M03-25; CA-M03-24).
El 02 el copia a l'activitat com a cost de material previst (RN-M02-43); no crea cap assignació
ni cap càrrec. La fórmula és una proposta [A validar: tresorer].

Es registra al 02 com a calculador (`extensions.register_material_cost_calculator`)."""

from dataclasses import dataclass, field

from .centres import rate_on
from .models import EquipmentAssignment, UsageRate
from .places import proposed_centre
from .typical import lines_for


def usage_cost_on(equipment_type, on) -> int:
    """RN-M03-08: el cost d'ús per dia vigent en una data; sense cap fila, 0."""
    rate = (
        UsageRate.objects.filter(equipment_type=equipment_type, valid_from__lte=on)
        .order_by("-valid_from")
        .first()
    )
    return rate.cost_per_day_cents if rate else 0


def standard_material_cost(activity) -> int:
    """Per a cada línia del material típic: quantitat × preu de cost de la tarifa vigent el
    primer dia al centre habitual del lloc; si no n'hi ha, quantitat × cost d'ús del club × dies.
    Sense material típic, 0."""
    centre = proposed_centre(activity.place)
    days = (activity.ends_on - activity.starts_on).days + 1
    total = 0
    for equipment_type, quantity in lines_for(activity):
        rate = rate_on(centre, equipment_type, activity.starts_on) if centre else None
        if rate is not None:
            total += quantity * rate.cost_cents
        else:
            total += quantity * usage_cost_on(equipment_type, activity.starts_on) * days
    return total


@dataclass(frozen=True)
class ActivityMaterialCost:
    """`equipment.activity_material_cost` (M03-8): el que necessita el marge del 09."""

    club_use_cents: int  # RN-M03-08 i 10: cost d'ús del material del club fet servir
    rental_cost_estimated_cents: int  # preu de cost dels lloguers (mentre no hi ha factura)
    rental_participant_cents: int  # el que paguen els participants pels lloguers
    per_participant: dict = field(default_factory=dict)  # inscripció → cèntims (RN-M03-09)

    @property
    def rental_margin_cents(self) -> int:
        """RN-M03-07: preu per al participant − preu de cost (pot ser negatiu)."""
        return self.rental_participant_cents - self.rental_cost_estimated_cents


def activity_material_cost(activity) -> ActivityMaterialCost:
    """Cost de material d'una activitat (T-M03-13; RN-M03-07 a 10; CA-M03-08). Lectura: qui el
    mostra comprova MT12; el 09 el fa servir per al marge.

    - Cost per participant: les seves assignacions fetes servir (lliurades o retornades); les no
      fetes servir i les cancel·lades no compten (RN-M03-09).
    - Lloguers: els vius o retornats (previstos, lliurats o retornats), al preu copiat de la tarifa.
    """
    rows = EquipmentAssignment.objects.filter(activity=activity).exclude(
        status__in=(EquipmentAssignment.Status.NOT_USED, EquipmentAssignment.Status.CANCELLED)
    )
    used = (EquipmentAssignment.Status.DELIVERED, EquipmentAssignment.Status.RETURNED)
    club = rental_cost = rental_price = 0
    per_participant: dict = {}
    for row in rows:
        if row.origin == EquipmentAssignment.Origin.RENTED:
            rental_cost += row.cost_cents
            rental_price += row.participant_price_cents
        if row.status in used:
            if row.origin == EquipmentAssignment.Origin.CLUB:
                club += row.cost_cents
            per_participant[row.enrolment_id] = per_participant.get(row.enrolment_id, 0)
            per_participant[row.enrolment_id] += row.cost_cents
    return ActivityMaterialCost(club, rental_cost, rental_price, per_participant)


def rentals_for(activity, centre):
    """`equipment.rentals_for` (M03-8): els lloguers vius o retornats de l'activitat en un centre,
    per casar la factura del centre (09)."""
    return (
        EquipmentAssignment.objects.filter(activity=activity, centre=centre)
        .exclude(
            status__in=(EquipmentAssignment.Status.NOT_USED, EquipmentAssignment.Status.CANCELLED)
        )
        .select_related("equipment_type", "rate")
    )
