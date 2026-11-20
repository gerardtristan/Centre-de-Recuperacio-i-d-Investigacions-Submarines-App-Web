"""V17 (T-F1-01): cap marca interna («A validar…», «A verificar…») a les pantalles del soci.

Les plantilles de l'àrea del soci estenen `base.html`; les de l'administració, `base_admin.html`.
Les pantalles «En construcció» (`previews/`) només les veu qui té el permís i poden portar-la."""

from pathlib import Path

from django.conf import settings

TEMPLATES = Path(settings.BASE_DIR) / "templates"
MEMBER_AREA = '{% extends "base.html" %}'


def test_member_area_templates_carry_no_review_mark():
    sources = {
        str(path.relative_to(TEMPLATES)): path.read_text(encoding="utf-8")
        for path in TEMPLATES.rglob("*.html")
        if "previews" not in path.parts
    }
    member_area = {name: text for name, text in sources.items() if MEMBER_AREA in text}
    assert member_area, "no s'ha trobat cap plantilla de l'àrea del soci"
    assert [name for name, text in member_area.items() if "a-validar" in text] == []
