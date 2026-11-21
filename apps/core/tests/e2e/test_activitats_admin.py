"""Activitats a l'administració al navegador (T-M02-06a): el responsable de cursos i sortides hi
arriba pel menú, filtra el llistat i obre la fitxa d'una sortida amb un preu diferent de
l'estàndard. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import datetime
import re

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.activities import catalogue, services
from apps.activities.models import OutingType

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e


def test_manager_finds_an_outing_and_opens_its_page(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    place = catalogue.create_place(by=manager, name="Cala inventada")
    catalogue.change_place_price(
        place, by=manager, price_member_cents=4500, price_non_member_cents=6000,
        valid_from=timezone.localdate(), note="Preu inicial inventat.",
    )  # fmt: skip
    services.create_outing(
        by=manager, outing_type=OutingType.objects.get(name="Immersió"), place=place,
        title="Sortida inventada a la cala", starts_on=datetime.date(2027, 6, 14),
        ends_on=datetime.date(2027, 6, 14), max_places=10, responsible=manager.person,
        registration_closes_at=timezone.make_aware(datetime.datetime(2027, 6, 10, 20)),
        price_member_cents=5000, price_non_member_cents=6000,
        price_override_note="Barca més cara (inventat).",
    )  # fmt: skip

    login_admin(page, live_server.url, manager.login)
    entry = menu_entry(page, "Cursos i sortides")
    entry.click()
    expect(page).to_have_url(f"{live_server.url}{reverse('administration:activities')}")
    expect(entry).to_have_attribute("aria-current", "page")
    expect(page.get_by_role("table", name="1 activitat")).to_contain_text("Cala inventada")
    review("activitats-llistat")

    page.get_by_label("Estat").select_option(label="Oberta")
    page.get_by_role("button", name="Filtra").click()
    expect(page.get_by_text("Cap activitat coincideix amb els filtres.")).to_be_visible()
    page.get_by_role("link", name="Treu els filtres").click()

    page.get_by_role("link", name=re.compile(r"^Fitxa")).click()
    expect(page.get_by_role("heading", name="Sortida inventada a la cala")).to_be_visible()
    expect(page.get_by_text("Preu diferent de l'estàndard.")).to_be_visible()
    expect(page.get_by_text("Barca més cara (inventat).")).to_be_visible()
    expect(entry).to_have_attribute("aria-current", "page")
    review("activitats-fitxa")
