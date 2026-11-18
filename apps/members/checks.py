"""Comprovacions d'arrencada del M01 (`manage.py check`). Claus del QR del carnet (079,
RN-M01-85): format correcte, clau activa existent i, on s'exigeixen, claus pròpies."""

from django.conf import settings
from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured

from . import card_keys


@register()
def card_qr_keys(app_configs, **kwargs):
    try:
        card_keys.active_key_id()
    except ImproperlyConfigured as error:
        return [Error(str(error), id="members.E001")]
    return []


@register()
def renewal_notice_before_fee(app_configs, **kwargs):
    """T-M01-43 (CA-M01-70): l'avís de renovació ha de sortir abans que es generi la quota, que
    es genera el dia del primer recordatori. Un mes en té com a mínim 28 dies."""
    months = settings.MEMBER_RENEWAL_NOTICE_MONTHS
    offsets = settings.MEMBER_FEE_REMINDER_OFFSETS
    lead = max(0, -min(offsets)) if offsets else 0
    if months < 1 or months * 28 < lead:
        return [
            Error(
                f"MEMBER_RENEWAL_NOTICE_MONTHS={months} no obre la finestra de l'avís de "
                f"renovació abans del primer recordatori ({-lead} dies, "
                "MEMBER_FEE_REMINDER_OFFSETS): cal com a mínim 1 mes i més dies que el primer "
                "recordatori.",
                id="members.E002",
            )
        ]
    return []
