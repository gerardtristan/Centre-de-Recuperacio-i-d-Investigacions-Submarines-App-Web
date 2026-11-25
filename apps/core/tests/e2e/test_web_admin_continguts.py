"""Notícies (WP2; T-M07-08b) i preguntes freqüents (WP4; T-M07-09b) a l'administració, al
navegador: el President redacta, publica i retira una notícia, i la Junta crea un tema, una
pregunta i la publica. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_president_publishes_and_retires_news(page, live_server, transactional_db, review):
    president = make_admin("presidencia.prova", "president")
    login_admin(page, live_server.url, president.login)
    page.goto(f"{live_server.url}{reverse('administration:website_news')}")
    expect(page.get_by_role("heading", name="Notícies", exact=True)).to_be_visible()
    page.locator("main").get_by_role("link", name="Notícia nova").click()
    page.get_by_label("Títol").fill("Sortida a les Medes (inventada)")
    page.get_by_label("Adreça").fill("sortida-medes")
    page.get_by_label("Data").fill("2026-11-25")
    page.get_by_label("Cos").fill("Ens veiem al port a les 9.")
    page.get_by_role("button", name="Desa", exact=True).click()
    expect(page.get_by_text("Notícia desada.")).to_be_visible()
    review("noticies-fitxa")
    page.get_by_role("button", name="Publica la notícia").click()
    expect(page.get_by_text("Notícia publicada.")).to_be_visible()
    review("noticies-llista")
    page.locator("main").get_by_role("link", name="Sortida a les Medes (inventada)").click()
    page.get_by_label("Motiu de la retirada").fill("Sortida anul·lada (inventat)")
    page.get_by_role("button", name="Retira la notícia").click()
    expect(page.get_by_text("Notícia retirada.")).to_be_visible()


def test_the_board_writes_and_publishes_a_question(page, live_server, transactional_db, review):
    board = make_admin("junta.prova", "board")
    login_admin(page, live_server.url, board.login)
    page.goto(f"{live_server.url}{reverse('administration:website_help')}")
    expect(page.get_by_role("heading", name="Preguntes freqüents", exact=True)).to_be_visible()
    page.get_by_label("Nom").fill("Quotes")
    page.get_by_role("button", name="Crea el tema").click()
    expect(page.get_by_text("Tema creat.")).to_be_visible()
    page.locator("main").get_by_role("link", name="Pregunta nova").click()
    page.get_by_label("Tema").select_option(label="Quotes")
    page.get_by_label("Pregunta").fill("Quan es paga la quota?")
    page.get_by_label("Resposta").fill("Al gener (inventat).")
    page.get_by_role("button", name="Desa", exact=True).click()
    expect(page.get_by_text("Pregunta desada.")).to_be_visible()
    review("ajuda-pregunta")
    page.locator("main").get_by_role("link", name="Preguntes freqüents").click()
    page.get_by_role("button", name="Publica-la").click()
    expect(page.get_by_text("Pregunta publicada.")).to_be_visible()
    review("ajuda-llista")
