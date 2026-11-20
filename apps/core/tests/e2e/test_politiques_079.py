"""Polítiques a la primera entrada d'un soci importat de Cluber, al navegador (T-M01-25; 079,
A-27 punt 4; CA-M01-109). Les pantalles es desen a 1280, 390 i 320 px (clar i fosc) i les dues
caselles i el botó es fan només amb el teclat. També la prova de l'exportació de Cluber amb un Excel
inventat (T-M01-50), que no tenia captures (T-F1-01).
"""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.models import Consent, Person
from apps.members.imports.cluber_sample import real_headers, sample_records
from apps.members.tests.test_cluber_xlsx_081 import XLSX_TYPE, as_rows, workbook_bytes
from conftest import PASSWORD

from .conftest import login_admin

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
    # V10: el resum d'errors (Errata), amb un enllaç a cada casella.
    errata = page.locator(".errata")
    expect(errata).to_be_focused()
    expect(errata.get_by_role("heading")).to_have_text("Hi ha 2 errors")
    expect(errata.locator("a.errata-element")).to_have_count(2)
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


def test_cluber_trial_with_an_excel_file(page, live_server, texts, review):
    login_admin(page, live_server.url, texts.login)
    page.goto(f"{live_server.url}{reverse('administration:cluber_preview')}")
    review("cluber-buida")
    headers = real_headers()
    page.get_by_label("Fitxer CSV de Cluber").set_input_files(
        {
            "name": "socis-inventats.xlsx",
            "mimeType": XLSX_TYPE,
            "buffer": workbook_bytes(headers, as_rows(sample_records(12), headers)),
        }
    )
    page.get_by_role("button", name="Valida el fitxer (prova)").click()
    expect(page.get_by_text("Format: Excel (.xlsx).")).to_be_visible()
    review("cluber-excel")
