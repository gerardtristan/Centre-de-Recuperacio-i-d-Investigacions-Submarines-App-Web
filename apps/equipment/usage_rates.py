"""Cost d'ús del material del club per tipus (T-M03-22b; VC-28; RN-M03-08 i RN-AJ-04).

- Qui el canvia: `settings.edit.equipment.usage_rates` (el tresorer, `core/0071`); qui el veu:
  l'apartat «Material» dels ajustos (`settings.section.equipment`). Sense permís, «no trobat».
- Un canvi és una fila nova de `UsageRate` amb data d'entrada en vigor no anterior a avui i nota:
  les files velles no es toquen i les assignacions ja fetes conserven el cost que van copiar.
- Va al registre (valor anterior i nou) i avisa el tresorer i la junta (`notify_money_change`).
La pantalla és la de l'apartat d'ajustos del 03 (T-M03-22, amb el nucli).
"""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings
from apps.core.charges import euros
from apps.core.permissions import has_perm

from .centres import _cents, _check_version
from .costs import usage_cost_on
from .models import EquipmentType, UsageRate

EDIT = "settings.edit.equipment.usage_rates"  # VC-28
SECTION = "equipment"
CHANGED = "equipment.usage_rate_changed"


def _per_day(cents: int) -> str:
    return _("%(amount)s per dia") % {"amount": euros(cents)}


def rates(*, viewer, today=None) -> list[dict]:
    """Per tipus actiu: el cost vigent avui i el canvi previst més proper, si n'hi ha."""
    if not business_settings.can_view(viewer, SECTION):
        raise Http404
    today = today or timezone.localdate()
    rows = []
    for kind in EquipmentType.objects.filter(active=True).order_by("name"):
        upcoming = (
            UsageRate.objects.filter(equipment_type=kind, valid_from__gt=today)
            .order_by("valid_from")
            .first()
        )
        rows.append({"type": kind, "cents": usage_cost_on(kind, today), "upcoming": upcoming})
    return rows


@transaction.atomic
def set_rate(equipment_type, *, cost_per_day_cents, valid_from, note, by, today=None) -> UsageRate:
    if not has_perm(by, EDIT, write=True):
        raise Http404
    today = today or timezone.localdate()
    note = _check_version(valid_from, note, today)
    cents = _cents(cost_per_day_cents)
    previous = usage_cost_on(equipment_type, valid_from)
    try:
        with transaction.atomic():
            rate = UsageRate.objects.create(
                equipment_type=equipment_type, cost_per_day_cents=cents, valid_from=valid_from
            )
    except IntegrityError as error:
        raise ValidationError(
            _("Aquest tipus ja té un cost d'ús que comença aquell dia.")
        ) from error
    audit.record(
        CHANGED, actor=by, target=rate, field="cost_per_day_cents", old=previous, new=cents,
        reason=note, details={"type": equipment_type.name, "valid_from": str(valid_from)},
    )  # fmt: skip
    business_settings.notify_money_change(
        what=_("Cost d'ús: %(type)s") % {"type": equipment_type.name},
        previous=_per_day(previous), new=_per_day(cents), changed_by=by, note=note,
        effective_from=valid_from,
    )  # fmt: skip
    return rate
