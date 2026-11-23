"""Apartat «Llocs» al navegador (T-M02-39): el responsable de cursos i sortides hi arriba des de
«Cursos i sortides», crea un lloc, li posa un preu estàndard que entra en vigor demà (amb motiu)
i el desactiva. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import datetime

import pytest
from playwright.sync_api import expect

from apps.activities.models import Place

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e


def test_manager_creates_a_place_and_sets_its_price(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    login_admin(page, live_server.url, manager.login)
    menu_entry(page, "Cursos i sortides").click()
    page.get_by_role("link", name="Llocs", exact=True).click()
    expect(page.get_by_role("heading", name="Llocs", exact=True)).to_be_visible()

    page.get_by_role("link", name="Lloc nou").click()
    page.get_by_label("Nom").fill("Cala inventada")
    page.get_by_label("Notes internes").fill("Aparcar a dalt (inventat).")
    page.get_by_role("button", name="Crea el lloc").click()
    expect(page.get_by_text("Lloc creat.")).to_be_visible()

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    page.get_by_label("Preu de soci").fill("45")
    page.get_by_label("Preu de no soci").fill("60")
    page.get_by_label("Vigent des del").fill(tomorrow.isoformat())
    page.get_by_role("button", name="Desa el preu").click()
    expect(page.locator("[data-errata]")).to_be_visible()  # sense motiu
    page.get_by_label("Motiu del canvi").fill("Preu de la barca d'enguany (inventat).")
    page.get_by_role("button", name="Desa el preu").click()
    expect(page.get_by_text("Preu estàndard desat.")).to_be_visible()
    expect(page.get_by_role("table")).to_contain_text("Futur")
    review("llocs-fitxa")

    page.get_by_role("button", name="Desactiva el lloc").click()
    expect(page.get_by_text("Lloc desactivat.")).to_be_visible()
    assert not Place.objects.get().active
    page.get_by_role("link", name="Tornar als llocs").click()
    expect(page.get_by_role("table")).to_contain_text("Inactiu")
    review("llocs-llista")
