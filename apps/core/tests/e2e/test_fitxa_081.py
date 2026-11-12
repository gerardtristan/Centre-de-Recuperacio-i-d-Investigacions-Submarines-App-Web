"""Fitxa del soci al navegador, decisió 081 (punts 16 i 24): la data de naixement «declarada, sense
comprovar» i l'acció per marcar-la com a comprovada; el restabliment presencial del doble factor
del compte personal. Tot amb el teclat. Pantalles a 1280, 390 i 320 px, en clar i en fosc. Només
dades inventades.
"""

from datetime import datetime

import pyotp
import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.accounts.models import TotpDevice
from apps.accounts.tests.test_personal_totp import with_totp

from .conftest import TOTP_KEY, login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH


@pytest.fixture(autouse=True)
def _no_motion(page):
    page.emulate_media(reduced_motion="reduce")


def test_birth_date_check_and_in_person_second_factor_reset(
    page, live_server, builder, member, secretary, review
):
    account = builder.personal(member.person)
    with_totp(account)
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{ADMIN}/socis/{member.pk}/")
    expect(page.get_by_text("(declarada, sense comprovar)")).to_be_visible()
    review("fitxa-data-declarada")

    # Marcar la data com a comprovada: desplegable, casella i botó, amb el teclat.
    page.get_by_text("Marca la data com a comprovada…").focus()
    page.keyboard.press("Enter")
    page.get_by_label("He comprovat la data de naixement amb el document").check()
    page.get_by_role("button", name="Marca-la com a comprovada").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Data de naixement marcada com a comprovada.")).to_be_visible()
    expect(page.get_by_text("(comprovada el ")).to_be_visible()

    # Restabliment presencial del doble factor.
    page.get_by_role("link", name="Restableix el doble factor del compte…").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Restableix el doble factor")).to_be_visible()
    review("restabliment-doble-factor")
    page.get_by_label("Número del document que t'ha mostrat").fill(member.person.id_document_number)
    page.get_by_label("He comprovat en persona la identitat del titular").check()
    page.get_by_label("Motiu").fill("Ha perdut el mòbil (motiu inventat).")
    page.get_by_label("El teu codi TOTP").fill(
        pyotp.TOTP(TOTP_KEY).at(datetime.now(), counter_offset=1)
    )
    page.get_by_role("button", name="Restableix el doble factor").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Doble factor restablert.")).to_be_visible()
    assert not TotpDevice.objects.filter(account=account).exists()
    expect(page.get_by_role("link", name="Restableix el doble factor del compte…")).to_have_count(0)
