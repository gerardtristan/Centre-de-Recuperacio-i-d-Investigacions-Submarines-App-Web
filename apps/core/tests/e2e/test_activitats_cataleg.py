"""Catàleg de cursos al navegador (T-M02-05b): el responsable de cursos i sortides hi arriba des de
«Cursos i sortides», crea una fitxa i hi posa uns preus nous que entren en vigor demà, amb motiu.
Després, a la mateixa pàgina, crea i desactiva un tipus de sortida i crea un subtipus (T-M02-05c).
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import datetime
import re

import pytest
from playwright.sync_api import expect

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e


def test_manager_creates_an_entry_and_its_prices(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    login_admin(page, live_server.url, manager.login)
    entry = menu_entry(page, "Catàleg de cursos")
    entry.click()
    expect(entry).to_have_attribute("aria-current", "page")
    page.get_by_role("link", name="Fitxa nova").click()
    page.get_by_label("Catàleg").select_option(label="Curs")
    page.get_by_label("Nom").fill("Curs inventat de pantalla")
    page.get_by_label("Preu de soci").fill("45")
    page.get_by_label("Preu de no soci").fill("60")
    page.get_by_label("Places per defecte").fill("6")
    page.get_by_label("Departament").select_option(index=1)
    page.get_by_role("button", name="Crea la fitxa").click()
    expect(page.get_by_text("Fitxa creada.")).to_be_visible()

    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    form = page.locator("form", has=page.get_by_role("button", name="Desa els preus"))
    form.get_by_label("Preu de soci").fill("50")
    form.get_by_label("Preu de no soci").fill("65")
    form.get_by_label("Vigent des del").fill(tomorrow.isoformat())
    form.get_by_label("Motiu del canvi").fill("Pujada de la federació (inventat).")
    page.get_by_role("button", name="Desa els preus").click()
    expect(page.get_by_text("Preus desats.")).to_be_visible()
    expect(page.get_by_role("table")).to_contain_text("Futur")
    review("cataleg-fitxa")
    page.get_by_role("link", name="Tornar al catàleg").click()
    expect(page.get_by_role("table").first).to_contain_text("Curs inventat de pantalla")
    review("cataleg-llista")

    # T-M02-05c: tipus de sortida i subtipus a la mateixa pàgina
    page.locator("#id_tipus-name").fill("Tipus inventat")
    page.locator("#id_tipus-default_department").select_option(index=1)
    page.get_by_role("button", name="Crea el tipus").click()
    expect(page.get_by_role("rowheader", name="Tipus inventat")).to_be_visible()
    row = page.get_by_role("row", name=re.compile("Tipus inventat"))
    row.get_by_role("button", name=re.compile("^Desactiva")).click()
    expect(page.get_by_text("Les sortides ja creades no canvien.")).to_be_visible()
    page.locator("#id_subtipus-name").fill("Subtipus inventat")
    page.get_by_role("button", name="Crea el subtipus").click()
    expect(page.get_by_role("rowheader", name="Subtipus inventat")).to_be_visible()
    page.evaluate("window.scrollTo(0, 0)")  # la capçalera de les taules és enganxosa
    review("cataleg-tipus")
