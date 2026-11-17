"""Remeses al navegador (T-M05b-09 i 10; C5, B3; P-M05b-E, passos 1 a 5): el tresorer
previsualitza la remesa, la confirma (els avisos previs surten per la cua), en veu el detall amb
l'IBAN emmascarat, descarrega el fitxer pain.008, la marca com a enviada i casa l'abonament del
banc (T-M05b-11b). Pantalles a 1280, 390 i 320 px (clar i fosc).
Només dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.models import LegalText
from apps.members.tests.test_cards import make_member
from apps.payments.tests.test_remittance_settlement import bank_line
from apps.payments.tests.test_remittances import iban, new_member
from conftest import PASSWORD

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_treasurer_previews_confirms_and_downloads_a_remittance(
    page, live_server, transactional_db, settings, review, page_checks
):
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.CLUB_IBAN_TRANSFERENCIES = iban(999)
    text = LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")
    holder = make_member(first="Signant", number=9999, document="99999999R")
    signer = Account.objects.create_personal(holder.person, "signant@example.org", PASSWORD)
    new_member(427, signer=signer, text=text, cents=3500)
    new_member(311, signer=signer, text=text)
    new_member(502, mandate=False)
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    # Hi arriba pel menú (T-DX-47): l'entrada només surt amb B3.
    entry = page.locator("#barra-lateral").get_by_role("link", name="Pagaments: remeses")
    entry.click()
    expect(page.get_by_role("heading", name="Remeses", exact=True)).to_be_visible()
    expect(page).to_have_url(f"{live_server.url}/{settings.ADMIN_URL_PATH}/pagaments/remeses/")
    expect(entry).to_have_attribute("aria-current", "page")
    expect(page.get_by_text("Encara no hi ha cap remesa.")).to_be_visible()
    page.get_by_label("Període").fill("2026-12")
    page.get_by_role("button", name="Previsualitza").click()

    expect(page.get_by_text("125,00 €")).to_be_visible()
    expect(page.get_by_text("Sense mandat actiu")).to_be_visible()
    expect(page.get_by_role("alert")).to_contain_text("Es crearan 2 rebuts")
    review("remeses-previsualitzacio")
    page.get_by_role("button", name="Sí, crea la remesa").click()

    expect(page.get_by_role("status")).to_contain_text("Remesa creada")
    expect(page.get_by_text("Avisada")).to_be_visible()
    expect(page.get_by_text("ES … 0427")).to_be_visible()
    assert iban(427) not in page.content()
    review("remeses-detall")

    page_checks.expect_download(f"/{settings.ADMIN_URL_PATH}/pagaments/remeses/")
    with page.expect_download() as download:
        page.get_by_role("button", name="Descarrega el fitxer pain.008").click()
    assert download.value.suggested_filename.endswith("-pain.008.001.02.xml")

    # Pas 6: enviada al banc, amb la confirmació de l'esborrat (044).
    page.reload()
    page.get_by_label("He esborrat el fitxer del dispositiu").check()
    page.get_by_role("button", name="Marca com a enviada al banc").click()
    expect(page.get_by_role("status")).to_contain_text("enviada al banc")

    # Pas 8: l'abonament arriba a l'extracte i el tresorer el casa (CA-T16.1).
    bank_line(12500, treasurer)
    page.get_by_role("button", name="Cerca l'abonament").click()
    page.get_by_role("button", name="Casa aquesta línia…").click()
    expect(page.get_by_role("alert")).to_contain_text("2 quotes passen a pagades")
    review("remeses-abonament-confirma")
    page.get_by_role("button", name="Sí, casa l'abonament").click()
    expect(page.get_by_role("status")).to_contain_text("Abonament casat")
    expect(page.get_by_text("Liquidada")).to_be_visible()
