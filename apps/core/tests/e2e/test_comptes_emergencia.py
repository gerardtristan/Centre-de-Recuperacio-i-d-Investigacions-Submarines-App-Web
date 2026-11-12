"""Avís de comptes d'emergència al navegador (T-M00-03; CA-10.1): un administrador sense dos
comptes d'emergència a punt veu l'avís a l'inici i a la llista de comptes, on el compte
d'emergència surt marcat. Pantalles a 1280, 390 i 320 px (clar i fosc).
"""

import pytest
from playwright.sync_api import expect

from apps.accounts import emergency
from conftest import PASSWORD

from .conftest import login_admin

pytestmark = pytest.mark.e2e


def test_administrator_sees_the_emergency_warning(page, live_server, texts, review):
    emergency.create("emergencia.prova", PASSWORD)
    login_admin(page, live_server.url, texts.login)
    expect(page.get_by_text("Falten comptes d'emergència.")).to_be_visible()
    review("inici-avis")
    page.get_by_role("main").get_by_role("link", name="Comptes d'administrador").click()
    expect(page.get_by_text("Falten comptes d'emergència.")).to_be_visible()
    expect(page.get_by_text("Emergència", exact=True)).to_be_visible()
    review("comptes-avis")
