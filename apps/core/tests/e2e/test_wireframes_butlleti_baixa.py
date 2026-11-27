"""Wireframe de la baixa del butlletí al navegador (T-M07-33): s'obre des del disc, sense connexió;
el selector «Demostració» mostra l'estat triat. Captures de cada pantalla."""

from pathlib import Path

import pytest
from django.conf import settings
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

WIREFRAME = Path(settings.BASE_DIR) / "design" / "wireframes" / "butlleti-baixa.html"


def test_the_unsubscribe_wireframe_opens_from_disk(page, review):
    page.context.set_offline(True)  # sense connexió: tot surt del disc
    page.goto(WIREFRAME.as_uri())
    expect(page.get_by_role("heading", name="Vols deixar de rebre el butlletí?")).to_be_visible()
    page.locator("#p-baixa summary").click()
    expect(page.get_by_role("button", name="Desa la preferència").first).to_be_visible()
    review("butlleti-baixa-wireframe")
    page.locator('#p-baixa input[value="fet"]').check()
    expect(page.get_by_role("heading", name="T'has donat de baixa")).to_be_visible()
    review("butlleti-baixa-wireframe-feta")
