"""Correccions de la revisió de pantalles al navegador (T-M01-45). Una prova per incidència, amb
el número del punt de la fila del pla. Les pantalles es desen a 1280, 390 i 320 px (clar i
fosc) i es comprova que a 320 px no es desplaça de costat.
"""

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

NARROW = {"width": 320, "height": 800}


@pytest.fixture(autouse=True)
def _no_motion(page):
    """Sense transicions: la captura en fosc es fa just després de canviar el tema."""
    page.emulate_media(reduced_motion="reduce")


def test_point_2_theme_selector_shows_its_labels_at_320(page, live_server, review):
    page.set_viewport_size(NARROW)
    page.goto(f"{live_server.url}/entrar/")
    selector = page.locator(".selector-tema")
    expect(selector).to_be_visible()
    for label in ("Sistema", "Clar", "Fosc"):
        text = selector.locator(".text-opcio", has_text=label)
        expect(text).to_be_visible()
        assert text.bounding_box()["width"] > 10, label  # no és el text amagat d'1 px
    review("entrada-selector-tema")
