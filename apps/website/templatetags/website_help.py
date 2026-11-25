"""«Mira com es fa» (T-M07-10; RN-M07-11, CA-M07-17): a qualsevol pantalla,
`{% load website_help %}` i `{% mira_com_es_fa %}` enllacen el tutorial publicat d'aquella pantalla
(pel nom de la ruta), o res si no n'hi ha."""

from django import template

from .. import help as faq

register = template.Library()


@register.inclusion_tag("website/_mira_com_es_fa.html", takes_context=True)
def mira_com_es_fa(context):
    match = getattr(context.get("request"), "resolver_match", None)
    return {"tutorial": faq.tutorial_for(match.view_name if match else "")}
