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
    """T-M01-43 (CA-M01-70): l'avís de renovació surt com a mínim un mes abans. Els dies del
    primer recordatori (VC-02) ara són un ajust de la base de dades i aquí no es poden llegir:
    que l'avís arribi abans que la quota és la pregunta P-360."""
    months = settings.MEMBER_RENEWAL_NOTICE_MONTHS
    if months < 1:
        return [
            Error(
                f"MEMBER_RENEWAL_NOTICE_MONTHS={months}: cal com a mínim 1 mes.",
                id="members.E002",
            )
        ]
    return []
