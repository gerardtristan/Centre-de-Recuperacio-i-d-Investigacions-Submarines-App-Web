"""Stock en una data (T-M03-04; P-M03-A pas 4; RN-M03-16; CA-M03-15; MT4).

Per tipus i talla (o litres), el recompte de peces disponibles, assignades, en ús i en revisió. Les
de baixa no hi compten. Cada peça surt en un sol estat, per aquest ordre: en revisió (estat de la
peça), en ús (assignació lliurada i no retornada que ja ha començat), assignada (assignació prevista
que inclou la data) i, si no, disponible. Així, disponibles + assignades + en ús + en revisió =
peces que no són de baixa (CA-M03-15).
"""

from dataclasses import dataclass

from django.http import Http404

from apps.core.permissions import has_perm

from .models import EquipmentAssignment, EquipmentItem

VIEW = "equipment.stock.view"  # MT4
ITEM = EquipmentItem.Status
A = EquipmentAssignment.Status


@dataclass
class StockLine:
    equipment_type: str
    measure: str  # talla, litres o buit
    available: int = 0
    assigned: int = 0
    in_use: int = 0
    in_review: int = 0

    @property
    def total(self) -> int:
        return self.available + self.assigned + self.in_use + self.in_review


def _measure(item) -> str:
    return item.size or (f"{item.litres} l" if item.litres is not None else "")


def stock(on, *, viewer, equipment_type=None) -> list[StockLine]:
    """`equipment.stock(on, filters)` (M03-8). Sense MT4 (ni de consulta), «no trobat»."""
    if not has_perm(viewer, VIEW, write=False):
        raise Http404
    return _lines(on, equipment_type)


def in_use_count(on) -> int:
    """Per al dashboard (08): peces en ús o assignades en una data. Consulta agregada sense
    permís: el permís DB1 el comprova la vista del dashboard (T-M08-09). Com `stock`, llegeix
    l'estat d'avui de les peces (en revisió, de baixa) i de les assignacions: només és fiable per
    a avui o una data futura; el dashboard només el fa servir per al període en curs (P-644)."""
    return sum(line.in_use + line.assigned for line in _lines(on))


def _lines(on, equipment_type=None) -> list[StockLine]:
    items = EquipmentItem.objects.exclude(status=ITEM.RETIRED).select_related("type")
    if equipment_type is not None:
        items = items.filter(type=equipment_type)
    live = EquipmentAssignment.objects.filter(item__in=items)
    in_use = set(
        live.filter(status=A.DELIVERED, period__startswith__lte=on).values_list("item", flat=True)
    )
    assigned = set(
        live.filter(status=A.PLANNED, period__contains=on).values_list("item", flat=True)
    )
    lines: dict[tuple, StockLine] = {}
    for item in items.order_by("type__name", "size", "litres", "code"):
        key = (item.type.name, _measure(item))
        line = lines.setdefault(key, StockLine(*key))
        if item.status == ITEM.IN_REVIEW:
            line.in_review += 1
        elif item.pk in in_use:
            line.in_use += 1
        elif item.pk in assigned:
            line.assigned += 1
        else:
            line.available += 1
    return list(lines.values())
