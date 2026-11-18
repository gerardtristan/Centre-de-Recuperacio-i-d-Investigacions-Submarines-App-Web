"""Valors del 01 que són ajustos (T-M01-32; addenda de la 055 i ampliació de la 091).

Cada funció llegeix el valor vigent a la data donada (avui, si no se'n dona cap) amb la peça
comuna (`apps.core.business_settings`): cap valor de negoci al codi (RN-M01-46 i RN-M01-106).
La pantalla és la comuna (apartat «members»). Les claus les crea `members/0022`; els permisos,
el catàleg i `core/0046`.
"""

from apps.core import business_settings
from apps.core.models import Setting

FEE_REMINDER_OFFSETS = "members.fee_reminder_offsets"  # VC-02 (091)
CARD_BACK_TEXT = "members.card_back_text"  # VC-03
CLASSIC_MEMBER_YEARS = "members.classic_member_years"  # VC-04 (0 = sense insígnia)
SUPPLEMENT_DUE_DAYS = "members.type_change_supplement_due_days"  # VC-53 (091)


def price_key(membership_type) -> str:
    """VC-01 (RN-M01-45): un ajust per tipus, amb versions i data d'entrada en vigor."""
    return f"members.annual_fee_cents.{membership_type.code}"


def annual_fee_cents(membership_type, at=None) -> int:
    """Preu del tipus vigent a la data `at` (RN-M01-13 i 45). Una quota creada no el torna a
    llegir: el seu càrrec guarda l'import."""
    try:
        return business_settings.get(price_key(membership_type), at)
    except Setting.DoesNotExist:
        # shortcut: un tipus sense ajust (només als tests) fa servir el preu inicial del tipus;
        # la T-M01-52, que crearà tipus des dels ajustos, crearà l'ajust amb el tipus.
        return membership_type.annual_fee_cents


def fee_reminder_offsets(at=None) -> list[int]:
    """RN-M01-14 i 106: dies respecte del venciment, en ordre."""
    return sorted(business_settings.get(FEE_REMINDER_OFFSETS, at))


def supplement_due_days(at=None) -> int:
    return business_settings.get(SUPPLEMENT_DUE_DAYS, at)


def card_back_text() -> str:
    return business_settings.get(CARD_BACK_TEXT)


def classic_member_years() -> int:
    return business_settings.get(CLASSIC_MEMBER_YEARS)
