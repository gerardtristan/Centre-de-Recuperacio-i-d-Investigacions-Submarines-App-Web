"""Textos d'ajuda editables de les pantalles (T-M00-08e; `apps/core/texts.py`)."""

from django import template

from .. import texts

register = template.Library()


@register.simple_tag
def text_ajuda(key):
    """La pregunta (del codi) i la resposta vigent (l'editada o la per defecte) d'un plafó
    «Ajuda». Es fa servir amb `as` i la plantilla l'escapa: és text pla."""
    return {"question": texts.HELP[key].question, "text": texts.current(key)}
