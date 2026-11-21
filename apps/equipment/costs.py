"""Cost de material estàndard d'una activitat, per participant (T-M03-27; RN-M03-25; CA-M03-24).
El 02 el copia a l'activitat com a cost de material previst (RN-M02-43); no crea cap assignació
ni cap càrrec. La fórmula és una proposta [A validar: tresorer].

El registre al 02 com a calculador espera el punt d'extensió del 02 (T-M02-40, carril B)."""

from .centres import rate_on
from .models import TypicalEquipmentTemplate, UsageRate
from .places import proposed_centre


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
    owner = (
        {"catalogue_entry_id": activity.catalogue_entry_id}
        if activity.catalogue_entry_id
        else {"outing_type_id": activity.outing_type_id}
    )
    lines = TypicalEquipmentTemplate.objects.filter(**owner).select_related("equipment_type")
    centre = proposed_centre(activity.place)
    days = (activity.ends_on - activity.starts_on).days + 1
    total = 0
    for line in lines:
        rate = rate_on(centre, line.equipment_type, activity.starts_on) if centre else None
        if rate is not None:
            total += line.quantity_per_participant * rate.cost_cents
        else:
            usage = usage_cost_on(line.equipment_type, activity.starts_on)
            total += line.quantity_per_participant * usage * days
    return total
