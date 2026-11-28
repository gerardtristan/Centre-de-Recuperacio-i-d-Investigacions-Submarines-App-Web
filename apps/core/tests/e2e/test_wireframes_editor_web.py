"""Wireframes de l'editor de la web al navegador (T-M07-01): s'obren des del disc, sense connexió,
una pantalla cada vegada segons l'àncora, i el selector «Demostració» mostra l'estat triat. Captures
de les deu pantalles a 1280, 390 i 320 px (clar i fosc)."""

from pathlib import Path

import pytest
from django.conf import settings
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

WIREFRAME = Path(settings.BASE_DIR) / "design" / "wireframes" / "editor-web.html"
SCREENS = {
    "pagines": "Pàgines",
    "editor": "Editor: Portada",
    "biblioteca": "Afegeix un bloc",
    "patrons": "Insereix un patró",
    "publicar": "Revisa i publica",
    "versions": "Versions",
    "menu": "Menú principal",
    "capcalera": "Capçalera i peu",
    "fotos": "Tria una foto",
    "destacades": "Activitats destacades",
}


def test_the_editor_wireframes_open_from_disk(page, review):
    page.context.set_offline(True)  # sense connexió: tot surt del disc
    for anchor, title in SCREENS.items():
        page.goto(f"{WIREFRAME.as_uri()}#{anchor}")
        expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible()
        expect(page.locator(f"#{anchor} .nota-servidor")).to_be_visible()
        review(f"editor-web-{anchor}")
    page.goto(f"{WIREFRAME.as_uri()}#publicar")
    page.locator("#publicar [data-demo-estat]").select_option("caducada")
    expect(page.locator('#publicar [data-estat="caducada"]')).to_be_visible()
    expect(page.locator('#publicar .editor-partit[data-estat="normal"]')).to_be_hidden()
