"""Editor de permisos des del navegador (T-RP-03; RN-RP-06 a 09; CA-RP-04 i 05): l'administrador
obre «Rols i permisos» des del menú, dona M7 a la secretaria, en veu el resum amb el compte
afectat i l'avís de diners, i el desa amb la nota, el codi TOTP i la casella. Pantalles a 1280,
390 i 320 px (clar i fosc). Només dades inventades.
"""

from datetime import datetime

import pyotp
import pytest
from playwright.sync_api import expect

from .conftest import TOTP_KEY, login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e


def test_administrator_changes_a_permission(page, live_server, texts, review):
    make_admin("sara.prova", "secretary")
    login_admin(page, live_server.url, texts.login)
    menu_entry(page, "Rols i permisos").click()
    expect(page.get_by_role("heading", name="Rols i permisos")).to_be_visible()
    review("permisos-matriu")

    page.get_by_label("Rol", exact=True).select_option(label="Secretaria")
    page.get_by_role("button", name="Mostra", exact=True).click()

    page.get_by_label("M7 · Secretaria").select_option(label="Sí")
    page.get_by_role("button", name="Mostra el resum").click()
    expect(page.get_by_text("abans: —")).to_be_visible()
    expect(page.get_by_text("sara.prova")).to_be_visible()
    review("permisos-resum")

    page.get_by_label("Nota").fill("Acord de junta")
    page.get_by_label("El teu codi TOTP").fill(
        pyotp.TOTP(TOTP_KEY).at(datetime.now(), counter_offset=1)
    )
    page.get_by_label("He revisat el resum i els comptes afectats").check()
    page.get_by_role("button", name="Desa els canvis").click()
    expect(page.get_by_text("Desada la versió")).to_be_visible()
    expect(page.get_by_label("M7 · Secretaria")).to_have_value("all")
    review("permisos-desat")
