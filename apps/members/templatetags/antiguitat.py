"""Antiguitat del soci (T-DX-60): un sol text per a l'inici i el carnet. Menys d'un any sencer:
«Soci des de 2026», mai «0 anys»; a partir d'un any, «Soci des de 2025 (1 any)». Amb la data
d'alta aproximada, «~AAAA» i sense anys (RN-M01-23). Els anys són els del carnet (RN-M01-21)."""

from django import template
from django.utils.translation import gettext, ngettext

from .. import cards

register = template.Library()


@register.filter
def antiguitat(member, today=None) -> str:
    joined = getattr(member, "joined_on", None)
    if joined is None:
        return ""
    if member.joined_on_is_approximate:
        return gettext("Soci des de ~%(year)s") % {"year": joined.year}
    years = cards.years_of_membership(member, today)
    if years < 1:
        return gettext("Soci des de %(year)s") % {"year": joined.year}
    return ngettext(
        "Soci des de %(year)s (%(n)d any)", "Soci des de %(year)s (%(n)d anys)", years
    ) % {"year": joined.year, "n": years}
