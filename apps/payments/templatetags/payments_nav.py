"""Navegació de l'àrea del soci (T-DX-45): si la signatura del mandat està encesa. Amagar l'enllaç
no és cap control: la vista respon «no trobat» amb l'ajust apagat (T-M05a-09)."""

from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def mandate_signing_enabled():
    return settings.MANDATE_SIGNING_ENABLED
