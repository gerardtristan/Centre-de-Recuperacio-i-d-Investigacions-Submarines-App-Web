"""Cost de material previst d'una activitat (part de servei de la T-M02-40; RN-M02-43; CA-M02-45;
AC23).

- `copy_standard(activity)`: en crear l'activitat, `standard_material_cost_cents` i
  `material_cost_cents` prenen el cost estàndard per participant que calcula el 03
  (`extensions.standard_material_cost`); sense el 03, queden buits. La crida `services._create`
  després de desar-la, perquè el 03 ja hi hagi copiat el material típic.
- `set_material_cost(activity, cents, by=…, note=…)`: qui té AC23 el canvia; si difereix de
  l'estàndard, la nota és obligatòria. El canvi va al registre amb el valor anterior. És una
  previsió: no crea cap càrrec ni canvia cap import que pagui un participant.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _

from apps.core import audit

from . import extensions, permissions, states
from .models import Activity

MATERIAL_COST_CHANGED = "activities.activity.material_cost_changed"


def copy_standard(activity) -> Activity:
    standard = extensions.standard_material_cost(activity)
    if standard is not None:
        Activity.objects.filter(pk=activity.pk).update(
            standard_material_cost_cents=standard, material_cost_cents=standard
        )
        activity.standard_material_cost_cents = activity.material_cost_cents = standard
    return activity


@transaction.atomic
def set_material_cost(activity, cents, *, by, note="", request=None) -> Activity:
    # AC23: el responsable de cursos i sortides, només les seves activitats.
    permissions.require(by, permissions.MATERIAL_COST, activity, request=request)
    if isinstance(cents, bool) or not isinstance(cents, int) or cents < 0:
        raise ValidationError(_("El cost de material ha de ser un enter de cèntims, zero o més."))
    locked = Activity.objects.select_for_update().get(pk=activity.pk)
    if not states.is_editable(locked):
        raise ValidationError(_("Una activitat feta o cancel·lada no es canvia."))
    note = (note or "").strip()
    standard = locked.standard_material_cost_cents
    if standard is not None and cents != standard and not note:
        raise ValidationError(_("Cal dir per què el cost de material difereix de l'estàndard."))
    old = locked.material_cost_cents
    locked.material_cost_cents, locked.material_cost_note = cents, note
    locked.save(update_fields=["material_cost_cents", "material_cost_note", "updated_at"])
    audit.record(
        MATERIAL_COST_CHANGED,
        actor=by,
        target=locked,
        field="material_cost_cents",
        old=old,
        new=cents,
        reason=note,
        request=request,
    )
    activity.material_cost_cents, activity.material_cost_note = cents, note
    return activity
