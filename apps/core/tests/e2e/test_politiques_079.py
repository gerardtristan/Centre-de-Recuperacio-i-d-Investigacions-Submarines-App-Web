"""Polítiques a la primera entrada d'un soci importat de Cluber, al navegador (T-M01-25; 079,
A-27 punt 4; CA-M01-109). Les pantalles es desen a 1280, 390 i 320 px (clar i fosc) i les dues
caselles i el botó es fan només amb el teclat.
"""

import pytest
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.models import Consent, Person
from conftest import PASSWORD

pytestmark = pytest.mark.e2e


def test_imported_member_accepts_the_policies_at_first_login(page, live_server, texts, review):
    person = Person.objects.create(
        first_name="Marina", last_name="Cluber Inventada", origin=Person.Origin.CLUBER_IMPORT
    )
    account = Account.objects.create_personal(person, "marina.cluber@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("heading", name="Accepta les polítiques")).to_be_visible()
    review("politiques")

    page.goto(f"{live_server.url}/socis/perfil/")  # cap altra pàgina sense acceptar
    expect(page.get_by_role("heading", name="Accepta les polítiques")).to_be_visible()

    page.get_by_role("button", name="Accepta i continua").click()  # sense marcar res
    expect(page.get_by_text("Cal que l'acceptis per continuar.").first).to_be_visible()
    review("politiques-error")

    boxes = page.locator('input[type="checkbox"]')
    boxes.nth(0).focus()
    page.keyboard.press("Space")
    boxes.nth(1).focus()
    page.keyboard.press("Space")
    page.get_by_role("button", name="Accepta i continua").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Ja pots fer servir l'àrea de socis.")).to_be_visible()
    expect(page.get_by_role("heading", name="El meu perfil")).to_be_visible()
    assert Consent.objects.filter(person=person, action=Consent.Action.GRANTED).count() == 2
