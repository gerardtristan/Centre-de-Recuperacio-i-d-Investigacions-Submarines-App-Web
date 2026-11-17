"""Tresoreria que mou diners, tercer tall de la T-M04-15: el tresorer fa un arqueig amb ajust,
registra un traspàs de la caixa al banc, anul·la l'ajust amb motiu i confirma una liquidació del
proveïdor. Tot en dos passos. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades
inventades."""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.core.models import Person
from apps.treasury.tests.test_record_income import new_transit
from apps.treasury.tests.test_settlements import collected, record_it

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_treasurer_counts_transfers_reverses_and_settles(
    page, live_server, transactional_db, review
):
    new_transit(settings.PAYMENTS_PROVIDER, "Trànsit del proveïdor de prova")
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    collected(person, 9000, "REF-A")
    collected(person, 3500, "REF-B")
    record_it()
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    base = f"{live_server.url}/{settings.ADMIN_URL_PATH}/tresoreria/"

    page.goto(base)
    page.get_by_role("link", name="Fes un arqueig de caixa").click()
    page.get_by_label("Caixa").select_option(label="Caixa")
    page.get_by_label("Import comptat (€)").fill("200,00")
    page.get_by_label("Motiu de l'ajust").fill("Recompte de prova")
    page.get_by_role("button", name="Revisa l'arqueig").click()
    expect(page.get_by_role("alert")).to_contain_text("Ajustos de caixa")
    review("tresoreria-arqueig-confirma")
    page.get_by_role("button", name="Sí, registra l'arqueig").click()
    expect(page.get_by_role("status")).to_contain_text("Arqueig registrat")

    page.goto(base)
    page.get_by_role("link", name="Registra un traspàs").click()
    page.get_by_label("Des del compte").select_option(label="Caixa")
    page.get_by_label("Cap al compte").select_option(label="Banc principal")
    page.get_by_label("Import (€)").fill("150,00")
    page.get_by_label("Concepte").fill("Ingrés de l'efectiu al banc")
    page.get_by_role("button", name="Revisa el traspàs").click()
    expect(page.get_by_role("alert")).to_contain_text("Sortiran 150,00 €")
    review("tresoreria-traspas-confirma")
    page.get_by_role("button", name="Sí, registra el traspàs").click()
    expect(page.get_by_role("status")).to_contain_text("Traspàs registrat")
    expect(page.get_by_text("−150,00 €")).to_be_visible()

    page.get_by_role("link", name="Anul·la…").first.click()
    page.get_by_label("Motiu").fill("Arqueig equivocat (prova)")
    page.get_by_role("button", name="Revisa l'anul·lació").click()
    page.get_by_role("button", name="Sí, anul·la el moviment").click()
    expect(page.get_by_role("status")).to_contain_text("Moviment anul·lat")
    review("tresoreria-moviment-anullat")

    page.goto(base + "liquidacions/")
    expect(page.get_by_text("LIQ-001")).to_be_visible()
    review("tresoreria-liquidacions")
    page.get_by_role("link", name="Confirma…").click()
    page.get_by_role("button", name="Sí, confirma-la").click()
    expect(page.get_by_role("status")).to_contain_text("Liquidació confirmada")
