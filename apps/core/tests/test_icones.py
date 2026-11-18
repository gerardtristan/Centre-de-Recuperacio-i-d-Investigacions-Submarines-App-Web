"""Joc d'icones (T-DX-58; sistema de disseny §6.20)."""

import re
from pathlib import Path

import pytest
from django.conf import settings
from django.template import Context, Template

from apps.core.icones import LUCIDE_VERSION, NAMES

STATIC = Path(settings.BASE_DIR) / "static" / "img"
SPRITE = (STATIC / "icones.svg").read_text(encoding="utf-8")


def test_the_sprite_has_exactly_the_listed_icons_and_only_shapes():
    assert re.findall(r'<symbol id="([^"]+)"', SPRITE) == list(NAMES)
    assert len(set(NAMES)) == len(NAMES)
    assert not re.search(r"<script|on\w+=|href=|<foreignObject|style=", SPRITE)
    assert "stroke-width" not in SPRITE  # el gruix el posa el CSS (--icona-gruix)


def test_licence_and_origin_are_documented():
    assert (STATIC / "LICENSE-lucide.txt").read_text(encoding="utf-8").startswith("ISC License")
    readme = (STATIC / "README.md").read_text(encoding="utf-8")
    assert f"lucide-static-{LUCIDE_VERSION}.tgz" in readme
    assert re.search(r"\b[0-9a-f]{64}\b", readme)  # SHA-256 del paquet


def test_tag_renders_a_hidden_icon_from_the_sprite():
    html = Template('{% load icones %}{% icona "house" "gran" %}').render(Context())
    assert html.startswith('<svg class="icona gran" aria-hidden="true" focusable="false">')
    assert re.search(r'<use href="/static/img/icones\.svg#house"></use>', html)


def test_unknown_icon_fails():
    with pytest.raises(ValueError):
        Template('{% load icones %}{% icona "no-existeix" %}').render(Context())
