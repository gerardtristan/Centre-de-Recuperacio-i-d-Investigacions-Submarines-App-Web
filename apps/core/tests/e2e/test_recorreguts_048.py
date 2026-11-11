"""Recorreguts dels wireframes al navegador (T-M01-48; decisió 079, A-31): l'índex s'obre des
del disc (`file://`), sense connexió ni servidor, mostra l'avís de prototip i enllaça els
wireframes originals. Es desa a 1280, 390 i 320 px (clar i fosc).
"""

import re
from pathlib import Path

import pytest
from django.conf import settings
from playwright.sync_api import expect

from .conftest import CAPTURES

pytestmark = pytest.mark.e2e

INDEX = Path(settings.BASE_DIR) / "design" / "recorreguts" / "index.html"


def test_journeys_index_opens_from_disk_and_links_the_original_wireframes(page, review, request):
    page.context.set_offline(True)  # sense connexió: tot surt del disc
    page.goto(INDEX.as_uri())
    expect(page.get_by_text("Prototip de disseny, no és l'aplicació real")).to_be_visible()
    expect(page.get_by_role("heading", name="P-M01-A · Alta de soci")).to_be_visible()
    expect(page.get_by_role("heading", name="P-M01-G · Importació de Cluber")).to_be_visible()
    expect(page.locator("#P-M01-B .pas")).to_have_count(7)
    expect(page.locator("#P-M01-F").get_by_text("Sense wireframe")).to_be_visible()
    review("index")
    # La pàgina sencera és molt llarga: també la capçalera i un recorregut, per mirar-los bé.
    folder = CAPTURES / request.node.name
    for width in (1280, 390):
        page.set_viewport_size({"width": width, "height": 900})
        page.screenshot(path=folder / f"capcalera-{width}.png")
        page.locator("#P-M01-B").screenshot(path=folder / f"recorregut-b-{width}.png")
    page.set_viewport_size({"width": 1280, "height": 900})

    # Només amb el teclat: el primer enllaç de l'índex porta al seu recorregut.
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name=re.compile("^P-M01-A"))).to_be_focused()
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile(r"index\.html#P-M01-A$"))

    # L'enllaç d'un pas obre el wireframe original, a la seva àncora i amb el rol del pas.
    link = page.locator("#P-M01-G").get_by_role("link", name="admin.html#vista-socis-cluber")
    expect(link.first).to_have_attribute(
        "href", "../wireframes/admin.html#vista-socis-cluber&rol=admin"
    )
    page.locator("#P-M01-C").get_by_role("link", name="socis.html#baixa").click()
    expect(page).to_have_url(re.compile(r"design/wireframes/socis\.html#baixa$"))
    expect(page.get_by_role("heading", level=1, name="Sol·licita la baixa")).to_be_visible()
