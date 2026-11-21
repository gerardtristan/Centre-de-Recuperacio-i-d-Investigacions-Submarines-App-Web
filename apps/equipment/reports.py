"""Informes del 03, part de servei (T-M03-19): cost per participant i per activitat, material més
fet servir i revisions properes. Les pantalles, l'exportació i la impressió són de les vistes.

- `activity_costs`: MT12 (el responsable de cursos i sortides, només les seves activitats; la
  junta, consulta). Cap nom: el cost per participant va per número d'inscripció.
- `most_used`: MT4. Peces fetes servir (lliurades o retornades) per tipus i origen en un període.
- `upcoming_reviews`: MT11. Les peces amb la revisió dins el termini de l'ajust o vençudes.
"""

from django.db.models import Count
from django.http import Http404

from apps.core.permissions import has_perm

from .costs import activity_material_cost
from .models import EquipmentAssignment
from .reviews import due_items

COSTS = "equipment.costs.view"  # MT12
STOCK = "equipment.stock.view"  # MT4
REVIEWS = "equipment.reviews.manage"  # MT11


def _require(viewer, code, obj=None) -> None:
    if not has_perm(viewer, code, write=False) or (
        obj is not None and not has_perm(viewer, code, obj, write=False)
    ):
        raise Http404


def activity_costs(activity, *, viewer):
    _require(viewer, COSTS, activity)
    return activity_material_cost(activity)


def most_used(starts_on, ends_on, *, viewer) -> list[dict]:
    """Per tipus i origen, quantes assignacions fetes servir tenen dies dins el període."""
    _require(viewer, STOCK)
    rows = (
        EquipmentAssignment.objects.filter(
            status__in=(EquipmentAssignment.Status.DELIVERED, EquipmentAssignment.Status.RETURNED),
            period__overlap=(starts_on, ends_on),
        )
        .values("equipment_type__name", "origin")
        .annotate(uses=Count("pk"))
        .order_by("-uses", "equipment_type__name", "origin")
    )
    return [
        {"type": r["equipment_type__name"], "origin": r["origin"], "uses": r["uses"]} for r in rows
    ]


def upcoming_reviews(today, *, viewer):
    _require(viewer, REVIEWS)
    return due_items(today)
