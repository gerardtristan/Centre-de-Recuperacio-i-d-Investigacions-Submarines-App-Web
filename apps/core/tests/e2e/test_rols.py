"""Assignar un rol des del navegador (T-RP-02; RN-RP-07 i 14; CA-RP-14): l'administrador obre els
rols d'un compte des de la llista, en veu el resum amb l'avís d'un sol tresorer i el desa amb la
nota, el codi TOTP i la casella de revisió. Pantalles a 1280, 390 i 320 px (clar i fosc). Només
dades inventades.
"""

from datetime import datetime

import pyotp
import pytest
from playwright.sync_api import expect

from .conftest import TOTP_KEY, login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_administrator_assigns_a_role(page, live_server, texts, review):
    make_admin("tresoreria.prova", "treasurer")
    make_admin("bernat.prova", "instructor")
    login_admin(page, live_server.url, texts.login)
    page.get_by_role("main").get_by_role("link", name="Comptes d'administrador").click()
    page.get_by_role("link", name="Rols de bernat.prova").click()
    expect(page.get_by_role("heading", name="Rols de bernat.prova")).to_be_visible()
    review("rols-compte")

    page.get_by_label("Assigna un rol").select_option(label="Tresorer")
    page.get_by_role("button", name="Mostra el resum").click()
    expect(page.get_by_text("Ja hi ha un altre compte actiu amb el rol tresorer.")).to_be_visible()
    review("rols-resum")

    page.get_by_label("Nota").fill("Relleu acordat a la junta")
    # Un codi d'un interval posterior al de l'entrada: el mateix no es pot fer servir dues vegades.
    page.get_by_label("El teu codi TOTP").fill(
        pyotp.TOTP(TOTP_KEY).at(datetime.now(), counter_offset=1)
    )
    page.get_by_label("He revisat el resum i el compte afectat").check()
    page.get_by_role("button", name="Assigna el rol").click()
    expect(page.get_by_text("Canvi desat.")).to_be_visible()
    expect(page.get_by_role("cell", name="Tresorer")).to_be_visible()
    review("rols-desat")
