"""Edició del soci al navegador (T-M01-15b; 079, RN-M01-90): editar les dades i corregir la
data d'alta amb el motiu obligatori. Les pantalles es desen a 1280, 390 i 320 px (clar i fosc).
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.core.models import AuditEntry
from apps.members import member_edit

from .conftest import login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH


def test_edit_member_data_and_correct_the_join_date(page, live_server, secretary, member, review):
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{ADMIN}/socis/{member.pk}/")
    page.get_by_role("link", name="Edita les dades").click()
    expect(page.get_by_role("heading", name="Edita les dades")).to_be_visible()
    expect(
        page.get_by_text("El número de soci no es pot corregir des de l'aplicació.")
    ).to_be_visible()
    review("edita-dades")
    page.get_by_label("Cognoms").fill("Prova Corregit")
    page.get_by_role("button", name="Desa els canvis").click()
    expect(page.get_by_text("Canvis desats")).to_be_visible()
    expect(page.get_by_role("heading", level=1, name="Pere Prova Corregit")).to_be_visible()

    page.locator("summary", has_text="Més").click()  # T-DX-67: les accions rares, dins de «Més»
    page.get_by_role("link", name="Corregeix la data d'alta").click()
    expect(page.get_by_role("heading", name="Corregeix la data d'alta")).to_be_visible()
    review("data-alta")
    page.get_by_label("Data d'alta").fill("2001-02-03")
    page.get_by_label("La data és aproximada").check()
    # Sense motiu: el servidor ho rebutja i ho diu al camp.
    page.get_by_role("button", name="Desa la data").click()
    expect(page.get_by_text("Aquest camp és obligatori")).to_be_visible()
    review("data-alta-sense-motiu")
    # Amb el teclat: motiu i desar.
    page.get_by_label("Motiu de la correcció").focus()
    page.keyboard.type("Data recuperada del carnet antic (prova)")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Desa la data")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Canvis desats")).to_be_visible()
    expect(page.get_by_text("03/02/2001 (aproximada)")).to_be_visible()
    review("fitxa-corregida")
    entry = AuditEntry.objects.filter(
        action=member_edit.JOIN_DATE_CORRECTED, field="joined_on"
    ).get()
    assert entry.reason == "Data recuperada del carnet antic (prova)"
