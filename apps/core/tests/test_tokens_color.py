"""T-DX-02: paleta OKLCH dels estats (design-system §15.4, regles C5 i D10).

Llegeix tokens.css i comprova, als dos temes, que els colors d'estat tenen la mateixa
lluminositat per rol, que el text fa 4,5:1 i el decoratiu 3:1 sobre el fons, el contenidor,
el pou i el seu fons tenyit, i que cada hexadecimal de reserva és el mateix color que l'oklch().
"""

import math
import re
from pathlib import Path

import pytest
from django.conf import settings

TOKENS = (Path(settings.BASE_DIR) / "static" / "css" / "tokens.css").read_text(encoding="utf-8")
STATES = ("ok", "avis", "error", "info", "sistema")
BACKGROUNDS = {
    "light": ("#CCD0CF", "#9BA8AB", "#BCC3C4"),
    "dark": ("#11212D", "#253745", "#1B2C39"),
}
LLAUTO = "#f5c43a"


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _hex(value):
    value = value.lstrip("#")
    return [int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)]


def _oklch(value):
    lightness, chroma, hue = (float(x) for x in value.split())
    a, b = chroma * math.cos(math.radians(hue)), chroma * math.sin(math.radians(hue))
    l_ = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3
    linear = (
        4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
        -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
        -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_,
    )
    return [12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055 for c in linear]


def _contrast(a, b):
    def lum(rgb):
        r, g, bl = (_lin(min(1, max(0, c))) for c in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * bl

    high, low = sorted((lum(a), lum(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def _block(start, after=0):
    i = TOKENS.index(start, after)
    return TOKENS[i : TOKENS.index("}", i)]


def _values(block, pattern):
    return dict(re.findall(r"--c-([a-z]+(?:-text|-fons)?):\s*" + pattern, block))


def _palette(theme):
    """Els tokens de cada estat: hexadecimals de reserva i valors oklch()."""
    supports = TOKENS.index("@supports (color: oklch(0 0 0))")
    if theme == "light":
        hexes = _block(":root {\n  color-scheme: light;")
        oklch = _block(":root {", supports)
    else:
        hexes = _block(':root[data-theme="dark"] {\n  color-scheme: dark;')
        oklch = _block(':root[data-theme="dark"]', supports)
    return _values(hexes, r"(#[0-9A-Fa-f]{6})"), _values(oklch, r"oklch\(([^)]*)\)")


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_same_lightness_per_role(theme):
    _, oklch = _palette(theme)
    for suffix in ("", "-text", "-fons"):
        lightness = {float(oklch[s + suffix].split()[0]) for s in STATES if s + suffix in oklch}
        assert len(lightness) == 1, f"{theme}: L diferents a «{suffix or 'decoratiu'}»: {lightness}"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_contrast_of_status_colours(theme):
    _, oklch = _palette(theme)
    for state in STATES:
        tint = _oklch(oklch[state + "-fons"]) if state + "-fons" in oklch else _hex(LLAUTO)
        grounds = [_hex(b) for b in BACKGROUNDS[theme]] + [tint]
        text, decor = _oklch(oklch[state + "-text"]), _oklch(oklch[state])
        assert min(_contrast(text, g) for g in grounds) >= 4.5, f"{theme} {state}: text"
        assert min(_contrast(decor, g) for g in grounds) >= 3, f"{theme} {state}: decoratiu"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_hex_fallback_is_the_same_colour(theme):
    hexes, oklch = _palette(theme)
    for name, value in oklch.items():
        if name in hexes:
            pairs = zip(_hex(hexes[name]), _oklch(value), strict=True)
            assert all(abs(a - b) < 1.5 / 255 for a, b in pairs), name
