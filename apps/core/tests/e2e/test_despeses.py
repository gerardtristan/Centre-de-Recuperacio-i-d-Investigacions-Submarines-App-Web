"""Despeses al navegador (T-M09-06, part sense fitxer, i T-M09-15; MG1 i MG2): el tresorer registra
una despesa des del mòbil i la veu a «Despeses sense factura». Les rutes encara no són al menú
(torn del nucli): s'hi entra per l'adreça amb `apps.expenses.tests.urls`. Pantalles a 1280, 390 i
320 px. Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.expenses.models import Expense, Supplier

from .conftest import login_admin, make_admin

pytestmark = [pytest.mark.e2e, pytest.mark.urls("apps.expenses.tests.urls")]


def test_the_treasurer_records_an_expense(page, live_server, transactional_db, review):
    Supplier.objects.create(name="Nàutica Inventada SL")
    treasurer = make_admin("tresorer.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)

    page.goto(f"{live_server.url}{reverse('administration:expense_new')}")
    expect(page.get_by_role("heading", name="Registra una despesa")).to_be_visible()
    page.get_by_role("button", name="Registra la despesa").click()
    expect(page.get_by_text("Aquest camp és obligatori.").first).to_be_visible()
    review("despesa-nova-errors")

    page.get_by_label("Proveïdor").select_option(label="Nàutica Inventada SL")
    page.get_by_label("Número de factura").fill("F-2027-1")
    page.get_by_label("Data de la factura").fill("2027-06-10")
    page.get_by_label("Categoria").select_option(label="Embarcació")
    page.get_by_label("Descripció").fill("Sortida a les Medes")
    page.get_by_label("Import (€)").fill("250,50")
    page.get_by_label("Departament").select_option(label="General")
    review("despesa-nova")
    page.get_by_role("button", name="Registra la despesa").click()

    expect(page.get_by_role("heading", name="Despeses sense factura")).to_be_visible()
    expect(page.get_by_text("Despesa registrada")).to_be_visible()
    expect(
        page.get_by_role("table", name="1 despesa sense factura, la més antiga primer")
    ).to_contain_text("Sortida a les Medes")
    review("despeses-sense-factura")
    assert Expense.objects.get().amount_cents == 25050
