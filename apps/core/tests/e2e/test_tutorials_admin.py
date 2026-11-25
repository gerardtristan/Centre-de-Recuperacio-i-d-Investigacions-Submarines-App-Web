"""Tutorials a l'administració (WP4; T-M07-10b) al navegador: la Junta en crea un (sense publicar),
el publica i el retira. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.website.models import Tutorial

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_board_writes_publishes_and_retires_a_tutorial(
    page, live_server, transactional_db, review
):
    board = make_admin("junta.prova", "board")
    login_admin(page, live_server.url, board.login)
    page.goto(f"{live_server.url}{reverse('administration:website_tutorials')}")
    expect(page.get_by_role("heading", name="Tutorials", exact=True)).to_be_visible()
    page.locator("main").get_by_role("link", name="Tutorial nou").click()
    page.get_by_label("Títol").fill("Com pagar la quota")
    page.get_by_label("Adreça").fill("pagar-la-quota")
    page.get_by_label("Passos").fill("Obre «Les meves quotes».\nPrem «Paga amb targeta».")
    page.get_by_label("Pantalla").fill("payments:no_existeix")
    page.get_by_role("button", name="Desa").click()
    expect(page.get_by_text("Aquesta pantalla no existeix.").first).to_be_visible()
    review("tutorial-admin-errata")
    page.get_by_label("Pantalla").fill("payments:charge")
    page.get_by_role("button", name="Desa").click()
    expect(page.get_by_text("Tutorial desat.")).to_be_visible()
    page.locator("main").get_by_role("link", name="Tutorials").click()
    page.get_by_role("button", name="Publica'l").click()
    expect(page.get_by_text("Tutorial publicat.")).to_be_visible()
    review("tutorial-admin-llista")
    assert Tutorial.objects.get().published
    page.get_by_role("button", name="Retira'l").click()
    expect(page.get_by_text("Tutorial retirat.")).to_be_visible()
    assert not Tutorial.objects.get().published
