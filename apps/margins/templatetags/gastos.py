"""Gastos (T-DX-33 i T-DX-106; recurs a design/extern/; design-system §6.23): l'anell de segments
amb el total al mig i la llegenda «nom · N %». Els imports arriben en cèntims i el servidor en fa
els segments (sobre `pathLength="100"`): el navegador només els pinta, sense `style=`."""

from django import template
from django.utils.translation import gettext as _

from apps.core.charges import euros

register = template.Library()

# Colors de l'anell a tokens.css (`gastos-seg-1` a `-5`); la resta s'ajunta a «Altres» (D16).
MAX_SEGMENTS = 5


@register.inclusion_tag("_gastos_anell.html")
def anell_gastos(segments, label):
    """`segments`: parelles (nom, cèntims). Sense cap import positiu, no hi ha anell."""
    parts = sorted(((name, cents) for name, cents in segments if cents > 0), key=lambda p: -p[1])
    if len(parts) > MAX_SEGMENTS:
        rest = sum(cents for _name, cents in parts[MAX_SEGMENTS - 1 :])
        parts = [*parts[: MAX_SEGMENTS - 1], (_("Altres"), rest)]
    total = sum(cents for _name, cents in parts)
    rows, start = [], 0.0
    for index, (name, cents) in enumerate(parts, start=1):
        share = cents * 100 / total
        rows.append(
            {
                "name": name,
                "amount": euros(cents),
                "share": round(share),
                "dash": f"{max(share - 1, 0.5):.2f} 100",  # un petit buit entre segments
                "offset": f"{-start:.2f}",
                "segment": index,
            }
        )
        start += share
    return {"rows": rows, "total": euros(total) if total else None, "label": label}
