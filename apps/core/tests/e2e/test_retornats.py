"""Retornats al navegador (T-M05b-12 i 27; P-M05b-F; B4): el tresorer registra el retorn d'un
rebut amb el codi del banc i la comissió, veu la proposta i decideix el reintent; o puja el
fitxer de retornats del banc (pain.002, T-M05b-12b), en veu la previsualització i el confirma.
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.models import LegalText
from apps.members.tests.test_cards import make_member
from apps.payments import remittances, sepa_xml
from apps.payments.models import DirectDebitItem
from apps.payments.tests.test_bank_returns import pain002, tx
from apps.payments.tests.test_remittances import collection_date, iban, new_member
from apps.payments.tests.test_returns import settle
from conftest import PASSWORD

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def collected_item(settings):
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.CLUB_IBAN_TRANSFERENCIES = iban(999)
    text = LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")
    holder = make_member(first="Signant", number=9999, document="99999999R")
    signer = Account.objects.create_personal(holder.person, "signant@example.org", PASSWORD)
    new_member(427, signer=signer, text=text, cents=3500)
    treasurer = make_admin("tresoreria.prova", "treasurer")
    remittance = remittances.build_remittance("2026-12", collection_date(), treasurer)
    sepa_xml.remittance_file(remittance, treasurer)
    remittances.mark_remittance_sent(remittance, file_deleted=True, by=treasurer)
    settle(remittance, treasurer)
    return treasurer, DirectDebitItem.objects.get()


def test_treasurer_registers_a_return_and_confirms_the_retry(
    page, live_server, transactional_db, settings, review
):
    treasurer, item = collected_item(settings)
    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/pagaments/retornats/")
    expect(page.get_by_role("heading", name="Retornats", exact=True)).to_be_visible()
    expect(page.get_by_text("No hi ha cap retorn per decidir.")).to_be_visible()
    review("retornats-buit")
    page.get_by_label("Referència del rebut").fill(item.end_to_end_id)
    page.get_by_label("Codi de motiu").fill("AM04")
    page.get_by_label("Comissió de retorn (€)").fill("3,00")
    page.get_by_role("button", name="Registra el retorn").click()

    expect(page.get_by_role("status")).to_contain_text("Proposta: reintent")
    expect(page.get_by_role("button", name="Reintent (intent 2)")).to_be_visible()
    review("retornats-per-decidir")
    page.get_by_role("button", name="Reintent (intent 2)").click()

    expect(page.get_by_role("status")).to_contain_text("remesa següent")
    expect(page.get_by_text("No hi ha cap retorn per decidir.")).to_be_visible()


def test_treasurer_uploads_the_bank_returns_file(
    page, live_server, transactional_db, settings, review, tmp_path
):
    treasurer, item = collected_item(settings)
    path = tmp_path / "retornats.xml"
    path.write_bytes(pain002(tx(item.end_to_end_id, "MD01", amount="35.00"), tx("R-NO-EXISTEIX")))

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/pagaments/retornats/")
    page.get_by_label("Fitxer de retornats (XML)").set_input_files(path)
    page.get_by_role("button", name="Previsualitza").click()

    expect(page.get_by_text("Es registrarà 1 retorn.", exact=False)).to_be_visible()
    expect(page.get_by_text("Cap rebut amb aquesta referència")).to_be_visible()
    review("retornats-fitxer-previsualitzacio")
    page.get_by_role("button", name="Confirma els retorns").click()

    expect(page.get_by_role("status")).to_contain_text("Fitxer registrat: 1 retorn.")
    expect(page.get_by_text("No hi ha cap retorn per decidir.")).to_be_visible()
