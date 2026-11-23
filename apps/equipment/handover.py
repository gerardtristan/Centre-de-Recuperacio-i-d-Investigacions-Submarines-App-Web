"""Lliurar, retornar i quantitats reals (T-M03-09 i T-M03-12; P-M03-D passos 6-7; P-M03-E;
RN-M03-12; HU-M03-11; MT6 i MT10).

- Transicions (RN-M03-12): `planned → delivered → returned`; `planned → not_used / cancelled`;
  `delivered → not_used` (no s'ha fet servir). Cada canvi queda al registre amb l'estat anterior.
- En retornar una peça del club, torna a estar disponible o passa a revisió (no es pot assignar).
- `mark_not_used` és la quantitat real (MT10): una assignació que no s'ha fet servir no compta al
  cost (RN-M03-09) ni al registre de la persona.
- `used_by(person)`: per activitat, el material fet servir (lliurat o retornat): tipus, talla o
  litres i origen. Només de la mateixa persona; qui el mostri respon de fer-ho només a ella.
"""

import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit, business_settings

from . import inventory, rental_charges
from .access import require
from .models import EquipmentAssignment, EquipmentItem

ASSIGN = "equipment.assignments.manage"  # MT6
ACTUAL = "equipment.actual_quantities"  # MT10
STATUS_CHANGED = "equipment.assignment_status_changed"
S = EquipmentAssignment.Status
TRANSITIONS = {
    S.PLANNED: {S.DELIVERED, S.NOT_USED, S.CANCELLED},
    S.DELIVERED: {S.RETURNED, S.NOT_USED},
}
USED = (S.DELIVERED, S.RETURNED)


def _move(assignment, to, *, by, code, reason="", **fields) -> EquipmentAssignment:
    require(by, code, assignment.session or assignment.activity)
    with transaction.atomic():
        row = EquipmentAssignment.objects.select_for_update().get(pk=assignment.pk)
        if to not in TRANSITIONS.get(row.status, ()):
            raise ValidationError(_("Aquest canvi d'estat de l'assignació no és permès."))
        old, row.status = row.status, to
        for name, value in fields.items():
            setattr(row, name, value)
        row.save()
        audit.record(
            STATUS_CHANGED, actor=by, target=row, field="status", old=old, new=to, reason=reason
        )
    return row


def deliver(assignment, *, by, now=None) -> EquipmentAssignment:
    return _move(assignment, S.DELIVERED, by=by, code=ASSIGN, delivered_at=now or timezone.now())


def give_back(assignment, *, by, to_review=False, note="", now=None) -> EquipmentAssignment:
    """Retorna la peça (P-M03-D pas 7): disponible o a revisió."""
    note = (note or "").strip()
    with transaction.atomic():
        row = _move(
            assignment, S.RETURNED, by=by, code=ASSIGN, reason=note,
            returned_at=now or timezone.now(),
        )  # fmt: skip
        if row.item_id and to_review:
            item = EquipmentItem.objects.select_for_update().get(pk=row.item_id)
            inventory._set_status(item, EquipmentItem.Status.IN_REVIEW, by=by, reason=note)
    return row


def mark_not_used(assignment, *, by) -> EquipmentAssignment:
    """No s'ha fet servir (P-M03-E pas 1; MT10)."""
    return _move(assignment, S.NOT_USED, by=by, code=ACTUAL)


def cancel(assignment, *, by, reason) -> EquipmentAssignment:
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError(_("Cal el motiu de la cancel·lació."))
    assignment = _move(assignment, S.CANCELLED, by=by, code=ASSIGN, reason=reason)
    rental_charges.void_for(assignment, reason, by=by)  # T-M03-16
    return assignment


def used_by(person) -> list[dict]:
    """`equipment.used_by` (M03-8): per activitat, el material fet servir per la persona."""
    rows = (
        EquipmentAssignment.objects.filter(enrolment__person=person, status__in=USED)
        .select_related("activity", "equipment_type", "item")
        .order_by("activity__starts_on", "activity_id", "equipment_type__name", "pk")
    )
    found: dict[int, dict] = {}
    for row in rows:
        entry = found.setdefault(row.activity_id, {"activity": row.activity, "items": []})
        entry["items"].append({
            "type": row.equipment_type.name,
            "size": row.item.size if row.item else "",
            "litres": row.item.litres if row.item else None,
            "origin": row.origin,
        })  # fmt: skip
    return list(found.values())


UNRETURNED_DAYS = "equipment.unreturned_after_days"  # VC-29


def unreturned(today):
    """RN-M03-14: assignacions lliurades i no retornades quan ja han passat els dies de l'ajust
    `equipment.unreturned_after_days` des de l'últim dia (de l'activitat o de la sessió). Les farà
    servir l'avís diari del responsable (plantilla i tasca de la cua, torn del nucli)."""
    days = business_settings.get(UNRETURNED_DAYS, today)
    limit = today - datetime.timedelta(days=days)
    return (
        EquipmentAssignment.objects.filter(status=S.DELIVERED, period__endswith__lte=limit)
        .select_related("activity", "item", "equipment_type")
        .order_by("activity__ends_on", "pk")
    )
