"""Material típic: plantilles, còpia a l'activitat en crear-la i en duplicar-la (T-M03-06;
RN-M03-17; CA-M03-10). Es connecta al 02 pel `post_save` de l'activitat i pel senyal
`activity_duplicated`; el 03 no escriu mai als models del 02."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from apps.core import audit

from .access import TYPICAL, require
from .models import ActivityTypicalEquipment, TypicalEquipmentTemplate

TEMPLATE_CHANGED = "equipment.typical_template_changed"
ACTIVITY_TYPICAL_CHANGED = "equipment.activity_typical_changed"


def _owner(activity) -> dict:
    if activity.catalogue_entry_id:
        return {"catalogue_entry_id": activity.catalogue_entry_id}
    return {"outing_type_id": activity.outing_type_id}


def template_lines(activity):
    return TypicalEquipmentTemplate.objects.filter(**_owner(activity)).select_related(
        "equipment_type"
    )


def lines_for(activity) -> list[tuple]:
    """(tipus, quantitat per participant): el de l'activitat o, si encara no en té, la plantilla."""
    own = ActivityTypicalEquipment.objects.filter(activity=activity).select_related(
        "equipment_type"
    )
    rows = list(own) or list(template_lines(activity))
    return [(row.equipment_type, row.quantity_per_participant) for row in rows]


def copy_from_template(activity) -> None:
    if ActivityTypicalEquipment.objects.filter(activity=activity).exists():
        return
    ActivityTypicalEquipment.objects.bulk_create(
        ActivityTypicalEquipment(
            activity=activity,
            equipment_type=line.equipment_type,
            quantity_per_participant=line.quantity_per_participant,
        )
        for line in template_lines(activity)
    )


def copy_from_original(original, copy) -> None:
    """En duplicar (026, RN-M02-21), la còpia té el material típic de l'original, no el de la
    plantilla (CA-M03-10). Les assignacions no es copien mai."""
    ActivityTypicalEquipment.objects.filter(activity=copy).delete()
    ActivityTypicalEquipment.objects.bulk_create(
        ActivityTypicalEquipment(
            activity=copy,
            equipment_type=line.equipment_type,
            quantity_per_participant=line.quantity_per_participant,
        )
        for line in ActivityTypicalEquipment.objects.filter(activity=original)
    )


def on_activity_saved(sender, instance, created, raw=False, **kwargs) -> None:
    if created and not raw:
        copy_from_template(instance)


def on_activity_duplicated(sender, original, copy, **kwargs) -> None:
    copy_from_original(original, copy)


def _quantity(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100:
        raise ValidationError(_("La quantitat per participant és un enter de 0 a 100."))
    return value


@transaction.atomic
def set_template_line(equipment_type, quantity, *, by, catalogue_entry=None, outing_type=None):
    """MT5: la quantitat d'un tipus a la plantilla d'una fitxa o d'un tipus de sortida; amb 0, la
    línia es treu. Cada canvi va al registre amb el valor anterior."""
    require(by, TYPICAL)
    if (catalogue_entry is None) == (outing_type is None):
        raise ValidationError(_("La plantilla és d'una fitxa o d'un tipus de sortida."))
    quantity = _quantity(quantity)
    owner = {"catalogue_entry": catalogue_entry, "outing_type": outing_type}
    line = (
        TypicalEquipmentTemplate.objects.select_for_update()
        .filter(**owner, equipment_type=equipment_type)
        .first()
    )
    old = line.quantity_per_participant if line else 0
    if quantity == 0:
        if line is not None:
            line.delete()
        line = None
    else:
        line = line or TypicalEquipmentTemplate(**owner, equipment_type=equipment_type)
        line.quantity_per_participant = quantity
        line.save()
    audit.record(
        TEMPLATE_CHANGED,
        actor=by,
        target=catalogue_entry or outing_type,
        field=equipment_type.name,
        old=old,
        new=quantity,
    )
    return line


@transaction.atomic
def set_activity_line(activity, equipment_type, quantity, *, by):
    """MT5: el material típic d'una activitat concreta; amb 0, la línia es treu."""
    require(by, TYPICAL)
    quantity = _quantity(quantity)
    line = (
        ActivityTypicalEquipment.objects.select_for_update()
        .filter(activity=activity, equipment_type=equipment_type)
        .first()
    )
    old = line.quantity_per_participant if line else 0
    if quantity == 0:
        if line is not None:
            line.delete()
        line = None
    else:
        line = line or ActivityTypicalEquipment(activity=activity, equipment_type=equipment_type)
        line.quantity_per_participant = quantity
        line.save()
    audit.record(
        ACTIVITY_TYPICAL_CHANGED,
        actor=by,
        target=activity,
        field=equipment_type.name,
        old=old,
        new=quantity,
    )
    return line
