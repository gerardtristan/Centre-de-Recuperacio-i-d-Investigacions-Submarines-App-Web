"""Menú, capçalera i peu de la web a l'administració (WP9; T-M07-21) al navegador: el President hi
afegeix un grup amb un enllaç extern `https:` (un `http:` dona l'error) i desa la capçalera i el
peu. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.website.models import Menu, MenuItem

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_president_edits_the_menu_and_the_header(page, live_server, transactional_db, review):
    Menu.objects.get_or_create(code="principal", defaults={"name": "Menú principal"})
    president = make_admin("presidencia.prova", "president")
    login_admin(page, live_server.url, president.login)
    page.goto(f"{live_server.url}{reverse('administration:website_menu')}")
    expect(page.get_by_role("heading", name="Menú, capçalera i peu")).to_be_visible()
    page.locator("main").get_by_role("link", name="Enllaç nou").click()
    page.get_by_label("Text", exact=True).fill("El club")
    page.get_by_label("Ordre").fill("7")
    page.get_by_role("button", name="Desa").click()
    expect(page.get_by_text("Enllaç desat.")).to_be_visible()
    page.locator("main").get_by_role("link", name="Enllaç nou").click()
    page.get_by_label("Text", exact=True).fill("Federació")
    page.get_by_label("Adreça").fill("http://federacio.exemple.cat/")
    page.get_by_label("Dins de").select_option(label="El club")
    page.get_by_role("button", name="Desa").click()
    expect(page.get_by_text("Només una adreça de la plataforma").first).to_be_visible()
    review("menu-enllac-errata")
    page.get_by_label("Adreça").fill("https://federacio.exemple.cat/")
    page.get_by_role("button", name="Desa").click()
    expect(page.get_by_text("Enllaç desat.")).to_be_visible()
    assert MenuItem.objects.get(label="Federació").parent.label == "El club"
    page.get_by_label("Text de la capçalera").fill("Club de busseig de Barcelona")
    page.get_by_label("Text del peu").fill("Carrer inventat, 1 · Barcelona")
    page.get_by_role("button", name="Desa la capçalera i el peu").click()
    expect(page.get_by_text("Capçalera i peu desats.")).to_be_visible()
    expect(page.get_by_text("Versió 1,")).to_be_visible()
    review("menu-llista")
