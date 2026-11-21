"""La mida d'una peça segons el seu tipus (RN-M03-05; CA-M03-01): una ampolla porta litres (un
número positiu amb un decimal com a màxim); un tipus amb talla, una talla en text curt; la resta,
res. La fa servir l'inventari de peces (T-M03-03)."""

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import EquipmentType


def clean_measure(
    equipment_type: EquipmentType, size="", litres=None
) -> tuple[str, Decimal | None]:
    """Torna `(talla, litres)` nets o llança `ValidationError`."""
    size = (size or "").strip()
    sizing = equipment_type.sizing
    if sizing == EquipmentType.Sizing.LITRES:
        try:
            value = Decimal(str(litres))
        except (InvalidOperation, ValueError):
            value = None
        if (
            value is None
            or not value.is_finite()
            or not 0 < value < 1000
            or value != value.quantize(Decimal("0.1"))
        ):
            raise ValidationError(
                _("Una ampolla porta els litres: més de 0 i un decimal com a màxim.")
            )
        if size:
            raise ValidationError(_("Aquest tipus no porta talla."))
        return "", value.quantize(Decimal("0.1"))
    if litres is not None:
        raise ValidationError(_("Aquest tipus no porta litres."))
    if sizing == EquipmentType.Sizing.SIZE:
        if not size or len(size) > 10:
            raise ValidationError(_("Cal la talla (10 caràcters com a màxim)."))
        return size, None
    if size:
        raise ValidationError(_("Aquest tipus no porta talla."))
    return "", None
