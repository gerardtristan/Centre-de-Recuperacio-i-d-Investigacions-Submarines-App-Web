"""Monograma (T-DX-18; recurs a design/extern/; design-system §6.19): l'avatar per defecte del soci.

Es dibuixa només a partir de `Member.avatar_seed`, la llavor aleatòria fixada en l'alta (RN-M01-30,
T-M01-11): mai a partir del nom ni de cap altra dada personal, així que corregir el nom no el canvia
i el dibuix no revela res de la persona. La mateixa llavor dona sempre el mateix SVG.

Els colors no surten d'aquí: cada forma porta una classe (`monograma-fons`, `monograma-c1`…) i la
paleta (`monograma-paleta-N`) els treu dels tokens a `static/css/monograma.css`."""

import hashlib
import math

from django import template
from django.utils.safestring import mark_safe

from .member_notices import session_member

register = template.Library()

PATTERNS = ("blocs", "ones", "mosaic")
PALETTES = 4
# Radis de cada cantonada (en meitats de casella): quadrat, cercle (x2), quart, fulla i cúpula.
SHAPES = (
    (0, 0, 0, 0), (1, 1, 1, 1), (1, 1, 1, 1), (2, 0, 0, 0), (0, 2, 0, 0), (0, 0, 2, 0),
    (0, 0, 0, 2), (2, 0, 2, 0), (0, 2, 0, 2), (1, 1, 0, 0), (0, 1, 1, 0), (0, 0, 1, 1),
    (1, 0, 0, 1),
)  # fmt: skip
COLOURS = (1, 2, 3, 4, 1, 3)  # el primer i el tercer color hi surten més


def _n(value):
    return f"{round(value, 2):g}"


def _rounded_square(x, y, s, a, b, c, d):
    """Un quadrat amb un radi diferent a cada cantonada; els que no hi caben es redueixen."""
    f = min(1, *(s / max(0.001, p + q) for p, q in ((a, b), (b, c), (c, d), (d, a))))
    a, b, c, d = a * f, b * f, c * f, d * f

    def arc(r, x2, y2):
        return f"A{_n(r)} {_n(r)} 0 0 1 {_n(x2)} {_n(y2)}" if r > 0.05 else f"L{_n(x2)} {_n(y2)}"

    return (
        f"M{_n(x + a)} {_n(y)}H{_n(x + s - b)}{arc(b, x + s, y + b)}V{_n(y + s - c)}"
        f"{arc(c, x + s - c, y + s)}H{_n(x + d)}{arc(d, x, y + s - d)}"
        f"V{_n(y + a)}{arc(a, x + a, y)}Z"
    )


def _blocs(r):
    """3 × 3 formes arrodonides; la tercera columna és el mirall de la primera."""
    cells = {}
    for row in range(3):
        for col in range(2):
            cells[row, col] = (SHAPES[int(r() * len(SHAPES))], COLOURS[int(r() * 6)])
        (a, b, c, d), colour = cells[row, 0]
        cells[row, 2] = ((b, a, d, c), colour)
    return [
        f'<path class="monograma-c{colour}"'
        f' d="{_rounded_square(col * 40, row * 40, 40, *(k * 20 for k in shape))}"/>'
        for (row, col), (shape, colour) in sorted(cells.items())
    ]


def _ones(r):
    """Un sol i tres capes d'ones."""
    cx, cy, radius = 24 + r() * 72, 22 + r() * 22, 13 + r() * 10
    parts = [f'<circle class="monograma-c2" cx="{_n(cx)}" cy="{_n(cy)}" r="{_n(radius)}"/>']
    for i, colour in enumerate((1, 3, 4)):
        y0, amp, freq, phase = 52 + i * 22 + r() * 8, 4 + r() * 8, 1 + r() * 1.5, r() * 2 * math.pi
        points = "L".join(
            f"{x} {_n(y0 + amp * math.sin(2 * math.pi * freq * x / 120 + phase))}"
            for x in range(-3, 124, 6)
        )
        parts.append(f'<path class="monograma-c{colour}" d="M{points}L123 123L-3 123Z"/>')
    return parts


def _mosaic(r):
    """Una trama simètrica de 5 × 5."""
    cells = {}
    for row in range(5):
        for col in range(3):
            on, radius = r() < 0.68, (0.22, 0.5, 0.5, 0.35)[int(r() * 4)]
            cells[row, col] = (on, radius, COLOURS[int(r() * 6)])
    if sum(on for on, _, _ in cells.values()) < 5:
        for row in range(5):
            cells[row, 1] = (True, *cells[row, 1][1:])
    for row in range(5):
        cells[row, 3], cells[row, 4] = cells[row, 1], cells[row, 0]
    size = 24 * 0.84
    gap = (24 - size) / 2
    return [
        f'<rect class="monograma-c{colour}" x="{_n(col * 24 + gap)}" y="{_n(row * 24 + gap)}"'
        f' width="{_n(size)}" height="{_n(size)}" rx="{_n(radius * size)}"/>'
        for (row, col), (on, radius, colour) in sorted(cells.items())
        if on
    ]


def render(seed):
    """L'SVG de l'avatar per a una llavor; sense llavor, res."""
    if not seed:
        return ""
    digest = iter(hashlib.sha512(seed.encode()).digest())
    pattern, palette = PATTERNS[next(digest) % len(PATTERNS)], next(digest) % PALETTES

    def r():
        return next(digest) / 256

    shapes = {"blocs": _blocs, "ones": _ones, "mosaic": _mosaic}[pattern](r)
    # Decoratiu: el nom que hi ha al costat ja és el text (cap `title`, cap dada al dibuix). L'SVG
    # només porta números calculats aquí i classes fixes: cap dada de l'usuari.
    return mark_safe(  # noqa: S308
        f'<svg class="monograma monograma-paleta-{palette}" data-patro="{pattern}"'
        f' viewBox="0 0 120 120" aria-hidden="true" focusable="false">'
        f'<rect class="monograma-fons" width="120" height="120"/>{"".join(shapes)}</svg>'
    )


@register.simple_tag
def monograma(seed):
    return render(seed)


@register.simple_tag(takes_context=True)
def session_monograma(context):
    """L'avatar del soci de la sessió, només al compte personal (com la portada, T-DX-17)."""
    member = session_member(context)
    return render(member.avatar_seed) if member else ""
