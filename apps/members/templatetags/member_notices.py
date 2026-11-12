"""Avisos del M01 a l'inici de l'àrea de socis (T-M01-35; RN-M01-55, CA-M01-43). La 00 no
importa cap mòdul: la plantilla d'inici carrega aquesta etiqueta."""

from django import template

from .. import birth_date

register = template.Library()


@register.inclusion_tag("members/_birth_date_notice.html", takes_context=True)
def birth_date_notice(context):
    user = context.get("user")
    person = getattr(user, "person", None) if getattr(user, "is_authenticated", False) else None
    return {"show": person is not None and birth_date.missing_for(person)}
