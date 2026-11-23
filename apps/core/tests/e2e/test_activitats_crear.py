"""Crear i editar una activitat al navegador (T-M02-06b; vistes de la T-M02-40): el
responsable de cursos i sortides hi arriba pel menú, crea una sortida amb un lloc que porta el seu
preu estàndard, prova un preu diferent sense motiu i el desa amb motiu, i edita la fitxa.
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import datetime

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import catalogue
from apps.activities.models import Activity

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e


def test_manager_creates_and_edits_an_outing(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    place = catalogue.create_place(by=manager, name="Cala inventada")
    catalogue.change_place_price(
        place, by=manager, price_member_cents=4500, price_non_member_cents=6000,
        valid_from=datetime.date.today(), note="Preu inicial inventat.",
    )  # fmt: skip

    login_admin(page, live_server.url, manager.login)
    entry = menu_entry(page, "Cursos i sortides")
    entry.click()
    expect(page).to_have_url(f"{live_server.url}{reverse('administration:activities')}")
    expect(entry).to_have_attribute("aria-current", "page")
    expect(page.get_by_role("heading", name="Cursos i sortides")).to_be_visible()

    page.get_by_role("link", name="Sortida nova").click()
    expect(page.get_by_role("heading", name="Sortida nova")).to_be_visible()
    page.get_by_label("Tipus de sortida").select_option(label="Immersió")
    page.get_by_label("Títol").fill("Sortida inventada a la cala")
    page.get_by_label("Data d'inici").fill("2027-06-14")
    page.get_by_label("Data de final").fill("2027-06-14")
    page.get_by_label("Lloc", exact=True).select_option(index=1)
    expect(page.get_by_label("Lloc", exact=True)).to_contain_text("estàndard: 45,00")
    page.get_by_label("Data límit d'inscripció").fill("2027-06-10T20:00")
    page.get_by_label("Places").fill("10")
    page.get_by_label("Preu de soci").fill("50")
    page.get_by_label("Preu de no soci").fill("60")
    page.get_by_role("button", name="Desa l'activitat").click()
    expect(page.get_by_text("cal escriure'n el motiu")).to_be_visible()
    review("activitats-sortida-motiu")

    page.get_by_label("Motiu del preu diferent de l'estàndard").fill("Barca més cara (inventat).")
    page.get_by_role("button", name="Desa l'activitat").click()
    expect(page.get_by_text("Activitat creada en esborrany.")).to_be_visible()
    expect(page.get_by_text("Preu diferent de l'estàndard.")).to_be_visible()
    expect(entry).to_have_attribute("aria-current", "page")
    review("activitats-fitxa-creada")

    page.get_by_role("link", name="Edita", exact=True).click()
    page.get_by_label("Títol").fill("Sortida inventada a la cala (canviada)")
    page.get_by_role("button", name="Desa l'activitat").click()
    expect(page.get_by_text("Canvis desats.")).to_be_visible()
    assert Activity.objects.get().title == "Sortida inventada a la cala (canviada)"
