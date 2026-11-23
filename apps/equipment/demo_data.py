"""Dades inventades del 03 per a `seed_demo_data` (part de la T-M03-20). Mai en producció: les crida
l'ordre, que ja es nega a córrer fora de desenvolupament o amb una base que no és buida.

Tot passa pels serveis del 03 (amb el registre d'activitat): dos centres inventats amb tarifes,
el material típic de les sortides d'immersió, peces de l'inventari (ampolles, reguladors, jaquets
i neoprens de diverses talles), una revisió prevista i, si el 02 ja ha creat les seves activitats
inventades (l'ordre el crida abans), assignacions a les inscripcions confirmades: una de llogada a
la sortida oberta i, al curs en marxa, una peça lliurada i una de retornada. Cap dada personal.

Fora d'aquí: el cost d'ús per tipus, que es canvia a la pantalla d'ajustos (T-M03-22).
"""

import datetime

from django.utils import timezone

from apps.activities.models import Activity, Enrolment, OutingType

from . import assignments, centres, handover, inventory, reviews, typical
from .models import EquipmentReview, EquipmentType

CENTRES = (
    ("Centre de busseig Inventat Nord", 2500, 3000, 3500),
    ("Centre de busseig Inventat Sud", 2300, 2900, None),
)
TYPICAL = (("Jaquet", 1), ("Regulador", 1), ("Ampolla", 1), ("Ploms", 1), ("Neoprè", 1))
SIZES = ("S", "M", "M", "L", "XL")


def create(*, admin, today=None) -> dict:
    """Crea les dades del 03 amb el compte `admin` (té MT3, MT5, MT8 i MT11). Torna un resum."""
    today = today or timezone.localdate()
    kind = {t.name: t for t in EquipmentType.objects.all()}
    first_centre = None
    for name, cost, member, non_member in CENTRES:
        centre = centres.create_centre(by=admin, name=name)
        first_centre = first_centre or centre
        centres.add_rate(
            centre, label="Equip complet", equipment_type=kind["Jaquet"], cost_cents=cost,
            member_price_cents=member, non_member_price_cents=non_member, valid_from=today,
            note="Tarifa inventada de prova.", by=admin, today=today,
        )  # fmt: skip
    diving = OutingType.objects.get(name="Immersió")
    for name, quantity in TYPICAL:
        typical.set_template_line(kind[name], quantity, by=admin, outing_type=diving)
    items = []
    for n, litres in enumerate((12, 12, 15, 15, 10, 12)):
        items.append(
            inventory.create_item(
                equipment_type=kind["Ampolla"],
                by=admin,
                litres=litres,
                next_review_on=today + datetime.timedelta(days=60 + 45 * n),
            )  # fmt: skip
        )
    for n in range(3):
        items.append(
            inventory.create_item(
                equipment_type=kind["Regulador"],
                by=admin,
                next_review_on=today + datetime.timedelta(days=20 + 120 * n),
            )  # fmt: skip
        )
    for size in SIZES:
        items.append(inventory.create_item(equipment_type=kind["Jaquet"], by=admin, size=size))
        items.append(inventory.create_item(equipment_type=kind["Neoprè"], by=admin, size=size))
    # El primer regulador té la revisió a prop: surt a l'avís i a «Revisions properes».
    regulator = next(i for i in items if i.type.name == "Regulador")
    reviews.schedule_review(
        regulator, kind=EquipmentReview.Kind.REGULATOR_SERVICE, due_on=regulator.next_review_on,
        by=admin, provider="Taller inventat",
    )  # fmt: skip
    return {
        "centres": len(CENTRES), "items": len(items), "typical": len(TYPICAL), "reviews": 1,
        "assignments": _assignments(admin, kind, items, first_centre),
    }  # fmt: skip


def _assignments(admin, kind, items, centre) -> int:
    """La primera inscripció confirmada de la sortida oberta, amb material llogat; les dues primeres
    del curs en marxa, amb una peça del club lliurada i una de retornada. Sense el 02, cap."""

    def confirmed(status):
        return list(
            Enrolment.objects.filter(
                status=Enrolment.Status.CONFIRMED, activity__status=status
            ).order_by("activity_id", "pk")
        )  # fmt: skip

    made = 0
    for row in confirmed(Activity.Status.OPEN)[:1]:
        assignments.assign_rented(row, kind["Jaquet"], centre, by=admin, note="Dada de prova.")
        made += 1
    running = confirmed(Activity.Status.IN_PROGRESS)[:2]
    pieces = [next(i for i in items if i.type.name == name) for name in ("Neoprè", "Jaquet")]
    for n, (row, item) in enumerate(zip(running, pieces, strict=False)):
        given = handover.deliver(assignments.assign_club(row, item, by=admin), by=admin)
        if n:
            handover.give_back(given, by=admin)
        made += 1
    return made
