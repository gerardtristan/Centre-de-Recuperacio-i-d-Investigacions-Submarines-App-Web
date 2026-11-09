"""Secció «Llicència» de la fitxa del soci (T-M01-23). És una etiqueta d'inclusió perquè la vista
de la fitxa no hagi de canviar: les dades i els permisos es calculen aquí, amb els permisos de la
petició. Sense P19, la secció no rep cap fila."""

from django import template

from apps.core.permissions import request_permissions
from apps.members import licences

register = template.Library()


@register.inclusion_tag("members/_licence_records.html", takes_context=True)
def licence_records(context, member):
    request = context["request"]
    perms = request_permissions(request)
    visible = licences.can_view(request.user, perms)
    return {
        "member": member,
        "visible": visible,
        "records": member.licence_records.order_by("-issued_on", "-id") if visible else [],
        "can_manage": licences.can_manage(request.user, perms),
        "own": member.person_id == request.user.person_id,
    }
