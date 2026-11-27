"""Menú de la web pública (T-M07-21): `{% load website_menu %}{% menu_public %}` pinta
`website/_menu_public.html` amb el menú desat (`menus.public_menu`). La capçalera pública l'inclou
(DISSENY, T-DX-170)."""

from django import template

from .. import menus

register = template.Library()


@register.inclusion_tag("website/_menu_public.html", takes_context=True)
def menu_public(context):
    return {"menu": menus.public_menu(), "current": getattr(context.get("request"), "path", "")}
