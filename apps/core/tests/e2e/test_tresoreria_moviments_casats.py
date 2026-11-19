"""T-M04-12f al navegador (CA-T07.2; P-394): el tresorer casa la línia de l'ingrés en efectiu amb
la pota d'entrada del traspàs, des de la conciliació, i després ho desfà amb motiu; cap moviment
no canvia. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

from datetime import date

import pytest
from playwright.sync_api import expect

from apps.treasury import services
from apps.treasury.models import Movement, TreasuryAccount
from apps.treasury.tests.test_reconciliation import lines

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_treasurer_matches_the_cash_deposit_line_with_the_bank_leg(
    page, live_server, transactional_db, review
):
    treasurer = make_admin("tresoreria.prova", "treasurer")
    services.record_transfer(
        TreasuryAccount.objects.get(name="Caixa"),
        TreasuryAccount.objects.get(name="Banc principal"),
        15_000,
        value_date=date(2026, 11, 1),
        concept="Ingrés de l'efectiu de la caixa",
        by=treasurer,
    )
    lines(treasurer, (15_000, "INGRES EFECTIU OFICINA INVENTADA"))

    login_admin(page, live_server.url, treasurer.login)
    page.locator("#barra-lateral").get_by_role("link", name="Tresoreria: conciliació").click()
    row = page.get_by_role("row", name="02/11/2026")
    row.get_by_role("link", name="Casa amb moviments…").click()
    page.get_by_label("Ingrés de l'efectiu de la caixa").check()
    review("casa-moviments-tria")
    page.get_by_role("button", name="Revisa el casament").click()
    expect(page.get_by_text("Confirma el casament")).to_be_visible()
    review("casa-moviments-confirma")
    page.get_by_role("button", name="Sí, casa-la").click()
    expect(page.get_by_role("status")).to_contain_text("No s'ha mogut cap diner")
    expect(row).to_contain_text("Conciliada")
    expect(row).to_contain_text("Traspàs · Ingrés de l'efectiu de la caixa")
    review("casa-moviments-conciliada")

    row.get_by_text("Desfés…").click()
    row.get_by_label("Motiu per desfer-la").fill("Era un altre ingrés (prova)")
    row.get_by_role("button", name="Desfés la conciliació").click()
    expect(page.get_by_role("status")).to_contain_text("Els moviments no es toquen")
    expect(row.get_by_role("link", name="Casa amb moviments…")).to_be_visible()
    assert Movement.objects.count() == 2  # les dues potes, sense cap contramoviment
