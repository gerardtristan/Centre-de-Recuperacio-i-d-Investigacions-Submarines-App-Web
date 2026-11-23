"""Períodes del 09 al navegador (P-M09-G; MG11 i MG12; T-M09-16): el tresorer crea el primer
període, el tanca portant una despesa sense factura al següent amb un motiu, i l'administració el
reobre amb motiu. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import datetime

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.margins.tests.test_period_closing import an_expense

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_treasurer_closes_and_the_administrator_reopens(
    page, live_server, transactional_db, review
):
    treasurer = make_admin("tresorer.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:margin_periods')}")
    expect(page.get_by_role("heading", name="Tancament de períodes", exact=True)).to_be_visible()
    page.get_by_label("Comença el").fill("2026-11-01")
    page.get_by_role("button", name="Crea el període següent").click()
    expect(page.get_by_text("Període creat: del 01/11/2026 al 30/11/2026.")).to_be_visible()

    an_expense(treasurer, datetime.date(2026, 11, 10))
    page.reload()
    page.get_by_role("button", name="Tanca el període").click()
    expect(page.get_by_text("Encara no es pot tancar")).to_be_visible()
    page.get_by_label("Despesa sense factura: Sortida a les Medes.").fill(
        "La factura arriba el mes vinent"
    )
    review("periodes-llista-de-control")
    page.get_by_role("button", name="Tanca el període").click()
    expect(page.get_by_text("Període tancat.")).to_be_visible()

    page.context.clear_cookies()
    admin = make_admin("admin.prova", "administrator")
    login_admin(page, live_server.url, admin.login)
    page.goto(f"{live_server.url}{reverse('administration:margin_periods')}")
    page.get_by_label("Motiu de la reobertura").fill("Repartiment mal fet (inventat).")
    review("periodes-reobrir")
    page.get_by_role("button", name="Reobre el període").click()
    expect(page.get_by_text("Període reobert.")).to_be_visible()
