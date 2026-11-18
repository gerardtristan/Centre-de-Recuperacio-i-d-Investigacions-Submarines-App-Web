"""Valors del 01 que són ajustos (T-M01-32; addenda de la 055 i ampliació de la 091).

Cada funció llegeix el valor vigent a la data donada (avui, si no se'n dona cap) amb la peça
comuna (`apps.core.business_settings`): cap valor de negoci al codi (RN-M01-46 i RN-M01-106).
La pantalla és la comuna (apartat «members»). Les claus les crea `members/0022`; els permisos,
el catàleg i `core/0046`.
"""

from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.utils.translation import ngettext

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
        # Només un tipus creat sense la pantalla (als tests): la pantalla de tipus (T-M01-52)
        # crea l'ajust amb el tipus, i fa servir el preu inicial del tipus.
        return membership_type.annual_fee_cents


def fee_reminder_offsets() -> list[int]:
    """RN-M01-14 i 106: dies respecte del venciment, en ordre."""
    return sorted(business_settings.get(FEE_REMINDER_OFFSETS))


def check_reminders(offsets) -> None:
    """P-360, opció B: la quota es genera el dia del primer recordatori, i l'avís de renovació
    (T-M01-43, `MEMBER_RENEWAL_NOTICE_MONTHS` abans) ha de sortir abans. Un mes en té com a
    mínim 28 dies. La registra `apps.MembersConfig.ready` per a VC-02."""
    months = django_settings.MEMBER_RENEWAL_NOTICE_MONTHS
    limit = months * 28
    if -min(offsets) > limit:
        message = ngettext(
            "El primer recordatori pot ser com a màxim %(days)s dies abans del venciment: "
            "l'avís de renovació, %(months)s mes abans, ha de sortir abans que es generi la "
            "quota.",
            "El primer recordatori pot ser com a màxim %(days)s dies abans del venciment: "
            "l'avís de renovació, %(months)s mesos abans, ha de sortir abans que es generi la "
            "quota.",
            months,
        )
        raise ValidationError(message % {"days": limit, "months": months})


def supplement_due_days() -> int:
    return business_settings.get(SUPPLEMENT_DUE_DAYS)


def card_back_text() -> str:
    return business_settings.get(CARD_BACK_TEXT)


def classic_member_years() -> int:
    return business_settings.get(CLASSIC_MEMBER_YEARS)
