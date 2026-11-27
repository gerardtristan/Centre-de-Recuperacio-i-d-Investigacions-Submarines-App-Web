"""T-M07-33 (wireframe de la baixa del butlletí): cada pantalla porta la nota «Al servidor» i la
demostració; la baixa és el primer botó de la pàgina i l'únic principal, i les alternatives van
plegades a sota. Sense `style=` ni colors escrits a mà."""

import re
from pathlib import Path

from django.conf import settings

WIREFRAME = Path(settings.BASE_DIR) / "design" / "wireframes" / "butlleti-baixa.html"


def _screens(html):
    parts = re.split(r'<section id="(p-[a-z]+)" class="pantalla', html)[1:]
    return dict(zip(parts[::2], parts[1::2], strict=True))


def test_every_screen_states_its_server_controls():
    html = WIREFRAME.read_text(encoding="utf-8")
    screens = _screens(html)
    assert tuple(screens) == ("p-correu", "p-baixa", "p-enllac", "p-soci")
    for name, body in screens.items():
        assert 'class="demo nota-servidor"' in body, name
        assert 'class="demo"' in body, name
    assert " style=" not in html
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", html.split("<style>")[1].split("</style>")[0])


def test_unsubscribing_is_the_first_and_only_main_button_and_the_options_are_optional():
    baixa = _screens(WIREFRAME.read_text(encoding="utf-8"))["p-baixa"]
    inicial = baixa.split('data-estat="fet"')[0]
    assert inicial.count("boto-principal") == 1
    assert inicial.index("Dona'm de baixa") < inicial.index("<details")
    assert "<details open" not in inicial
