"""Vigencia (T-DX-13; recurs a design/extern/; design-system §6.15): els dies que queden d'una quota
o d'una llicència sobre una regla, amb els dies d'avís marcats. El compte enrere el calcula el
servidor amb la data local (mai el rellotge del navegador) a partir de la data que ja dona el
servidor: «Pagada fins al» (070, P-71) o la caducitat de la llicència.

Els dies d'avís de la quota són els dels recordatoris (VC-02, l'ajust de la T-M01-32, els que van
abans del venciment o el mateix dia): no hi ha cap valor nou al codi. La llicència no en té cap de
definit, i la regla no n'hi posa."""

from django import template

from .. import settings as member_settings
from ..fee_rules import local_today

register = template.Library()

# Escala del dibuix, no una regla de negoci: a partir de 60 dies la barra és plena. Si un dia d'avís
# és més llunyà, l'escala s'hi allarga.
WINDOW_DAYS = 60


def fee_warning_days() -> list[int]:
    offsets = member_settings.fee_reminder_offsets()
    return sorted({-offset for offset in offsets if offset <= 0}, reverse=True)


@register.inclusion_tag("members/_vigencia.html")
def vigencia(until, kind="quota"):
    if until is None:
        return {"show": False}
    days = (until - local_today()).days
    marks = fee_warning_days() if kind == "quota" else []
    window = max([WINDOW_DAYS, *marks])
    if days < 0:
        level = "error"
    elif marks and days <= marks[0]:
        level = "avis"
    else:
        level = "ok"
    return {
        "show": True,
        "days": days,
        "ago": -days,
        "window": window,
        "bar": min(max(days, 0), window),
        "marks": [m for m in marks if m > 0],
        "level": level,
        "until": until,
        "kind": kind,
    }
