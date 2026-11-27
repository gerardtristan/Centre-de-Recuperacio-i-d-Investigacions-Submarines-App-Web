"""Navegació de l'àrea del soci (T-DX-148): si surt l'entrada «Butlletí». Amagar l'enllaç no és cap
control: la vista respon «no trobat» amb l'ajust apagat (`switched_on`, T-M07-13)."""

from django import template

from apps.core import business_settings
from apps.website import newsletter

register = template.Library()


@register.simple_tag
def newsletter_enabled():
    return bool(business_settings.get(newsletter.ENABLED))


@register.simple_tag
def newsletter_notice(user):
    """T-M07-34: si l'avís per subscriure's al butlletí surt a aquest compte."""
    return newsletter.show_member_notice(user)
