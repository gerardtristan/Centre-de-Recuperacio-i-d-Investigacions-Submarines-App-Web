"""Dashboard al navegador (T-M08-09): el tresorer obre el panell general, canvia al panell econòmic
amb el trimestre i veu el panell de comunicació. Pantalles a 1280, 390 i 320 px. Dades
inventades."""

import pytest
from django.core.cache import cache
from django.urls import reverse
from playwright.sync_api import expect

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_treasurer_opens_the_dashboard(page, live_server, transactional_db, review):
    cache.clear()
    treasurer = make_admin("tresorer.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:dashboard')}")
    expect(page.get_by_role("heading", name="Panell General")).to_be_visible()
    expect(page.get_by_text("Què vol dir?").first).to_be_visible()
    review("dashboard-general")
    page.locator("main").get_by_role("link", name="Econòmic", exact=True).click()
    page.get_by_label("Període").select_option("quarter")
    page.get_by_role("button", name="Mostra").click()
    expect(page.get_by_role("heading", name="Panell Econòmic")).to_be_visible()
    review("dashboard-economic")
    page.locator("main").get_by_role("link", name="Comunicació", exact=True).click()
    # T-M08-08: el panell de comunicació ja té els blocs del 07 (cap subscriptor: «menys de 3»).
    expect(page.get_by_text("Subscriptors confirmats").first).to_be_visible()
