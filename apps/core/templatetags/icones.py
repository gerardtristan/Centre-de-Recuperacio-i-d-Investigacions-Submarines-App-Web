"""{% icona "nom" %}: una icona de l'sprite (T-DX-58; sistema de disseny §6.20).

Sempre `aria-hidden` i fora de l'ordre del teclat: el text o el nom accessible de l'element que
la porta ja diu què és. Un nom que no és a la llista falla (també a les proves): així una icona
que no és a l'sprite no surt mai com un quadre buit."""

from django import template
from django.templatetags.static import static
from django.utils.html import format_html

from apps.core.icones import NAMES

register = template.Library()


@register.simple_tag
def icona(name, extra=""):
    if name not in NAMES:
        raise ValueError(f"Icona desconeguda: {name!r} (apps/core/icones.py)")
    classes = f"icona {extra}".strip()
    return format_html(
        '<svg class="{}" aria-hidden="true" focusable="false"><use href="{}#{}"></use></svg>',
        classes,
        static("img/icones.svg"),
        name,
    )
