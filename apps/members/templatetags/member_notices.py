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


@register.inclusion_tag("members/_home_resum.html", takes_context=True)
def member_home_summary(context):
    """Portada de l'àrea de socis (T-DX-17, D13): l'estat de la quota, els dies que queden i el
    carnet, només del soci de la sessió. Sense soci (compte personal sense alta), res."""
    from .. import roster
    from ..models import Member

    user = context.get("user")
    person = getattr(user, "person", None) if getattr(user, "is_authenticated", False) else None
    # Només al compte personal: el d'administrador no és la porta del soci (decisions 015 i 018).
    if person is None or getattr(user, "kind", None) != "personal":
        return {"show": False}
    member = Member.objects.filter(person=person).first()
    if member is None:
        return {"show": False}
    loaded = roster.with_fee_data(Member.objects.filter(pk=member.pk)).get()
    return {"show": True, "member": member, "fee": roster.fee_state(loaded)}
