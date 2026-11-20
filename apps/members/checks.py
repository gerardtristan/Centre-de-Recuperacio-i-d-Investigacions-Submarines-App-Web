"""Comprovacions d'arrencada del M01 (`manage.py check`). Claus del QR del carnet (079,
RN-M01-85): format correcte, clau activa existent i, on s'exigeixen, claus pròpies."""

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
