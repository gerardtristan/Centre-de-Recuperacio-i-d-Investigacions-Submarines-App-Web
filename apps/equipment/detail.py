"""Bloc de material a «Les meves activitats» i a la fitxa de l'activitat (T-M03-15; C10, MT2 i MT7).

Es registra al 02 amb `extensions.register_detail_section`; les pantalles que el pinten són del 02
(T-M02-06 i T-M02-22). Què es veu (M03-4, «Per objecte»; RN-M02-45):

- A «Les meves activitats», el participant veu només el seu material: tipus, peça i talla o litres,
  d'on surt i l'estat. Cap cost ni preu.
- A la fitxa d'administració, qui té MT7 per a aquesta activitat (l'instructor, les seves sessions)
  veu el material de tots els participants, amb el nom. Tampoc cap cost: és de MT12.
- Sense res a mostrar o sense permís, el bloc no surt (`None`).
"""

from django.utils.translation import gettext_lazy as _

from apps.activities.extensions import PLACE_PERSONAL, DetailSection
from apps.core.permissions import has_perm

from .models import EquipmentAssignment

SECTION_KEY = "equipment.assigned"
PARTICIPANTS = "equipment.participants.view"  # MT7


def section_context(activity, *, place, viewer=None, person=None):
    rows = (
        EquipmentAssignment.objects.filter(activity=activity)
        .exclude(status=EquipmentAssignment.Status.CANCELLED)
        .select_related("equipment_type", "item", "centre", "enrolment__person")
        .order_by("enrolment_id", "equipment_type__name", "pk")
    )
    if place == PLACE_PERSONAL:
        if person is None:
            return None
        rows = rows.filter(enrolment__person=person)
    elif viewer is None or not has_perm(viewer, PARTICIPANTS, activity):
        return None
    rows = list(rows)
    if not rows:
        return None
    return {"activity": activity, "rows": rows, "with_people": place != PLACE_PERSONAL}


SECTION = DetailSection(
    key=SECTION_KEY,
    label=_("Material"),
    template_name="equipment/_material_activitat.html",
    context=section_context,
)
