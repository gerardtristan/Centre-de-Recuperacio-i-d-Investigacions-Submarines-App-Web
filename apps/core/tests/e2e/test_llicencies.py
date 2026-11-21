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


def test_treasurer_adds_a_type_and_its_price(page, live_server, transactional_db, review):
    """Vistes v2 (T-M06-02; LC8): un tipus nou i el seu preu amb nota; el preu de soci és el de
    la federació i el de no soci hi afegeix el recàrrec."""
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    entry = menu_entry(page, "Llicències: tipus i preus")
    entry.click()
    expect(page.get_by_role("heading", name="Tipus i preus de llicència")).to_be_visible()
    page.get_by_label("Nom").fill("Aficionat anual (inventat)")
    page.get_by_label("Categoria").select_option(label="Aficionat")
    page.get_by_label("Durada").select_option(label="Any natural")
    page.get_by_role("button", name="Crea el tipus").click()
    expect(page.get_by_text("Tipus de llicència creat.")).to_be_visible()

    page.get_by_label("Tipus", exact=True).select_option(label="Aficionat anual (inventat)")
    page.get_by_label("Preu de la federació (preu de soci), en euros").fill("90,00")
    page.get_by_label("Recàrrec de no soci, en euros").fill("20,00")
    page.get_by_label("Per a llicències que comencin des del").fill("2026-01-01")
    page.get_by_role("button", name="Desa el preu").click()
    expect(
        page.get_by_text("Cal emplenar aquest camp.").first.or_(
            page.get_by_text("Aquest camp és obligatori.").first
        )
    ).to_be_visible()
    review("llicencies-preu-sense-nota")
    page.get_by_label("Nota").fill("Tarifa de la federació (inventada)")
    page.get_by_role("button", name="Desa el preu").click()
    expect(page.get_by_text("Preu desat.", exact=False)).to_be_visible()
    table = page.get_by_role("table", name="1 tipus de llicència, amb el preu d'avui")
    expect(table).to_contain_text("90,00 €")
    expect(table).to_contain_text("110,00 €")
    review("llicencies-preus")
