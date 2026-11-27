"""T-M07-01 (wireframes de l'editor de la web): les deu pantalles de l'encàrrec, i cadascuna porta
la nota «Al servidor» (el control real), la demostració dels estats i els avisos d'error, d'accés
denegat i de sessió caducada (CLAUDE.md, «Disseny amb seguretat i privacitat»). Sense `style=`."""

import re
from pathlib import Path

from django.conf import settings

WIREFRAME = Path(settings.BASE_DIR) / "design" / "wireframes" / "editor-web.html"
SCREENS = (
    "pagines", "editor", "biblioteca", "patrons", "publicar",
    "versions", "menu", "capcalera", "fotos", "destacades",
)  # fmt: skip


def _views(html):
    parts = re.split(r'<section id="([a-z]+)" class="vista"', html)[1:]
    return dict(zip(parts[::2], parts[1::2], strict=True))


def test_every_screen_states_its_server_controls_and_its_error_states():
    html = WIREFRAME.read_text(encoding="utf-8")
    views = _views(html)
    assert tuple(views) == SCREENS
    for name, body in views.items():
        assert 'class="demo nota-servidor"' in body, name
        assert "data-demo-estat" in body, name
        for state in ("error", "denegat", "caducada"):
            assert f'data-estat="{state}"' in body, (name, state)
    assert " style=" not in html
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", html.split("<style>")[1].split("</style>")[0])
