"""Navegació de l'àrea del soci (T-DX-59; sistema de disseny §6.12): dues preguntes petites que
la plantilla no pot fer sola. Amagar una entrada no és cap control: cada vista ho torna a
comprovar."""

from django import template
from django.urls import NoReverseMatch, reverse

from apps.core.models import Charge
from apps.core.under_construction import can_see

from .. import cards
from ..models import AnnualFee

register = template.Library()


@register.simple_tag(takes_context=True)
def preview_url(context, name):
    """L'adreça d'una pantalla «En construcció» si existeix i qui mira la pot veure; si no, ""."""
    try:
        url = reverse(name)
    except NoReverseMatch:
        return ""
    return url if can_see(context["request"]) else ""


@register.simple_tag(takes_context=True)
def has_pending_fee(context):
    """Si el soci de la sessió té alguna quota pendent de pagar (una consulta, només les seves)."""
    user = context.get("user")
    if not getattr(user, "is_authenticated", False) or getattr(user, "kind", None) != "personal":
        return False  # el compte d'administrador no és la porta del soci (decisions 015 i 018)
    return AnnualFee.objects.filter(
        member__person_id=user.person_id, charge__status=Charge.Status.PENDING
    ).exists()


@register.simple_tag
def may_request_new_card(member):
    """«Demana un carnet nou», amb la mateixa regla que la pàgina del carnet (`cards`). `member`
    és el soci de la sessió (`user.person.member`); la vista ho torna a comprovar en demanar-lo."""
    return bool(member) and cards.may_request_new_card(cards.load_member(member.pk))
