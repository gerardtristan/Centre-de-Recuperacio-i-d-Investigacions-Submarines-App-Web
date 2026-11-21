"""Llicències al navegador (T-M06-09 i 10, vistes v1; LC4, LC5): la secretaria veu el llistat,
filtra les pagades, en marca una com a tramitada i la deixa vigent amb el número federatiu.
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import datetime

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core.models import Person
from apps.licences.models import Licence, LicenceType

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e
D = datetime.date


def licence(first, last, status, licence_type, **fields):
    person = Person.objects.create(first_name=first, last_name=last, origin="web")
    values = {
        "validity_rule": licence_type.validity_rule,
        "origin": "club",
        "price_kind": "member",
        "price_cents": 9000,
        "starts_on": D(2026, 3, 15),
        "expires_on": D(2026, 12, 31),
    }
    values.update(fields)
    return Licence.objects.create(person=person, licence_type=licence_type, status=status, **values)


def test_secretary_files_and_activates_a_licence(page, live_server, transactional_db, review):
    annual = LicenceType.objects.create(
        name="Aficionat anual (inventat)", category="amateur", validity_rule="calendar_year"
    )
    licence("Anna", "Vila Prova", "paid", annual)
    licence("Pere", "Roca Prova", "requested", annual)
    licence("Joan", "Bosch Prova", "active", annual, origin="external", price_kind=None,
            price_cents=None, federation_number="F-0001")  # fmt: skip
    secretary = make_admin("secretaria.prova", "secretary")

    login_admin(page, live_server.url, secretary.login)
    # Hi arriba pel menú: l'entrada només surt amb LC4.
    entry = menu_entry(page, "Llicències")
    entry.click()
    expect(page).to_have_url(f"{live_server.url}{reverse('administration:licences')}")
    expect(entry).to_have_attribute("aria-current", "page")
    expect(page.get_by_role("heading", name="Llicències federatives")).to_be_visible()
    expect(page.get_by_role("table", name="3 llicències, per cognoms")).to_be_visible()
    download = "Descarrega el fitxer per a la federació (1 pagada)"
    expect(page.get_by_role("button", name=download)).to_be_visible()
    review("llicencies-llistat")

    page.get_by_label("Estat").select_option(label="Pagada")
    page.get_by_role("button", name="Filtra").click()
    expect(page.get_by_role("table", name="1 llicència, per cognoms")).to_contain_text("Vila Prova")
    page.get_by_role("button", name="Marca tramitada").click()
    expect(page.get_by_text("Llicència marcada com a tramitada.")).to_be_visible()

    page.get_by_role("link", name="Vigent…").click()
    expect(page.get_by_role("heading", name="Deixa vigent una llicència")).to_be_visible()
    page.get_by_role("button", name="Sí, deixa-la vigent").click()
    expect(page.get_by_text("Aquest camp és obligatori.").first).to_be_visible()
    review("llicencia-vigent")
    page.get_by_label("Número federatiu").fill("F-0002")
    page.get_by_role("button", name="Sí, deixa-la vigent").click()
    expect(page.get_by_text("Llicència vigent.")).to_be_visible()
    assert Licence.objects.get(person__first_name="Anna").federation_number == "F-0002"
