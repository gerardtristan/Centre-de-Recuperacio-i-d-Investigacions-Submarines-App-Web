"""Inventari de peces: alta, dades, estats, baixa i historial (T-M03-03; RN-M03-04 i 05). Cap
altra app escriu aquests models. Tot amb MT3 (T-M03-18)."""

import datetime
import re

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext_lazy as _

from apps.core import audit
from apps.core.models import AuditEntry

from .access import INVENTORY, require
from .measures import clean_measure
from .models import EquipmentItem

ITEM_CREATED = "equipment.item_created"
ITEM_CHANGED = "equipment.item_changed"
ITEM_STATUS = "equipment.item_status_changed"
EDITABLE = ("size", "litres", "purchased_on", "purchase_cost_cents", "next_review_on", "notes")
S = EquipmentItem.Status
# RN-M03-04: disponible ⇄ en revisió; disponible → baixa; en revisió → baixa.
TRANSITIONS = {S.AVAILABLE: {S.IN_REVIEW, S.RETIRED}, S.IN_REVIEW: {S.AVAILABLE, S.RETIRED}}
# El format dels codis és codi (VC-30): MAT-0001, MAT-0002…
CODE = re.compile(r"^MAT-(\d+)$")


def next_code() -> str:
    codes = EquipmentItem.objects.filter(code__startswith="MAT-").values_list("code", flat=True)
    numbers = [int(match.group(1)) for code in codes if (match := CODE.match(code))]
    return f"MAT-{max(numbers, default=0) + 1:04d}"


def _check(item) -> None:
    item.size, item.litres = clean_measure(item.type, item.size, item.litres)
    if item.type.requires_review and not isinstance(item.next_review_on, datetime.date):
        raise ValidationError(_("Aquest tipus de material porta la data de la propera revisió."))
    cost = item.purchase_cost_cents
    if cost is not None and (isinstance(cost, bool) or not isinstance(cost, int) or cost < 0):
        raise ValidationError(_("El cost de compra és un enter de cèntims, zero o més."))
    item.notes = (item.notes or "").strip()


def _audit_value(value):
    if isinstance(value, datetime.date):
        return value.isoformat()
    return str(value) if value is not None and not isinstance(value, (int, str)) else value


@transaction.atomic
def create_item(*, equipment_type, by, code="", **fields) -> EquipmentItem:
    """Alta d'una peça. Sense codi, el següent `MAT-NNNN`."""
    require(by, INVENTORY)
    unknown = set(fields) - set(EDITABLE)
    if unknown:
        raise TypeError(f"Camps desconeguts: {sorted(unknown)}")
    if not equipment_type.active:
        raise ValidationError(_("Aquest tipus de material està desactivat."))
    code = (code or "").strip() or next_code()
    if len(code) > 20:
        raise ValidationError(_("El codi té 20 caràcters com a màxim."))
    item = EquipmentItem(code=code, type=equipment_type, **fields)
    _check(item)
    try:
        with transaction.atomic():
            item.save()
    except IntegrityError as error:
        raise ValidationError(_("Ja hi ha una peça amb aquest codi.")) from error
    audit.record(ITEM_CREATED, actor=by, target=item, details={"type": equipment_type.name})
    return item


@transaction.atomic
def update_item(item, *, by, **changes) -> EquipmentItem:
    """Les dades d'una peça (el codi i el tipus no canvien). Una peça donada de baixa no es toca."""
    require(by, INVENTORY)
    unknown = set(changes) - set(EDITABLE)
    if unknown:
        raise TypeError(f"Camps desconeguts: {sorted(unknown)}")
    item = EquipmentItem.objects.select_for_update().select_related("type").get(pk=item.pk)
    if item.status == S.RETIRED:
        raise ValidationError(_("Una peça donada de baixa no es modifica."))
    before = {name: _audit_value(getattr(item, name)) for name in changes}
    for name, value in changes.items():
        setattr(item, name, value)
    _check(item)
    item.save()
    audit.record_changes(
        ITEM_CHANGED,
        actor=by,
        target=item,
        changes={name: (before[name], _audit_value(getattr(item, name))) for name in changes},
    )
    return item


@transaction.atomic
def change_status(item, to_status, *, by, reason="") -> EquipmentItem:
    """RN-M03-04. Donar de baixa porta el motiu; una peça donada de baixa no torna."""
    require(by, INVENTORY)
    item = EquipmentItem.objects.select_for_update().get(pk=item.pk)
    return _set_status(item, to_status, by=by, reason=reason)


def _set_status(item, to_status, *, by, reason="") -> EquipmentItem:
    """El canvi d'estat, amb la peça ja bloquejada (també el fan servir les revisions)."""
    reason = (reason or "").strip()
    if to_status not in TRANSITIONS.get(item.status, ()):
        raise ValidationError(_("Aquest canvi d'estat no és permès."))
    if to_status == S.RETIRED:
        if not reason:
            raise ValidationError(_("Per donar de baixa una peça cal escriure'n el motiu."))
        item.retired_reason = reason
    old = item.status
    item.status = to_status
    item.save()
    audit.record(
        ITEM_STATUS, actor=by, target=item, field="status", old=old, new=to_status, reason=reason
    )
    return item


def history(item):
    """L'historial d'una peça: les entrades del registre d'activitat, de la més antiga."""
    return AuditEntry.objects.filter(
        target_type=EquipmentItem._meta.label_lower, target_id=str(item.pk)
    ).order_by("pk")
