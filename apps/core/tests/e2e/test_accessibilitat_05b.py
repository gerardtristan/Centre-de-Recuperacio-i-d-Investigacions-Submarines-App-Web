"""Accessibilitat de les pantalles del 05b (cobraments) al navegador (checklist B8; ordre del
responsable del 17/11/2026, per la revisió de les portes del nivell 2).

Les mateixes comprovacions que la T-M01-28 (`test_accessibilitat_028.audit`: axe WCAG 2.0 a 2.2 A
i AA en clar i en fosc, estructura, noms accessibles i recorregut amb el tabulador), a 1280 i
390 px, amb dades inventades:
- administració: pagaments i «a revisar»; remeses (llista buida i amb una, previsualització,
  detall, enviada i la confirmació de l'abonament); retornats (per decidir i la previsualització
  del fitxer del banc); els ajustos de pagaments (apartat i un valor);
- soci: «Les meves quotes» i el detall, la pantalla de pagament (pendent amb targeta, Bizum i
  transferència; en curs; fallit; Bizum esperant i no confirmat a temps; les dades de la
  transferència; pagat), el rebut (també anul·lat) i la pantalla del convidat.
Les devolucions encara no tenen pantalla. La pàgina del proveïdor fals només existeix en proves.

Els informes es desen a `.e2e-captures/accessibilitat/`. La revisió amb lector de pantalla i en
dispositius reals continua pendent de persona (P-301)."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core import audit as core_audit
from apps.core import charges
from apps.core.models import LegalText, Person
from apps.members.tests.test_cards import make_member
from apps.payments import attempts, sepa_xml
from apps.payments.models import (
    DirectDebitRemittance,
    PaymentAttempt,
    Receipt,
    ReceiptCancellation,
)
from apps.payments.providers import fake
from apps.payments.tests.test_bank_returns import pain002, tx
from apps.payments.tests.test_remittance_settlement import bank_line
from apps.payments.tests.test_remittances import iban, new_member
from apps.treasury import reconciliation
from apps.treasury.tests.test_reconciliation import lines, ref
from conftest import PASSWORD

from .conftest import login_admin, make_admin
from .test_accessibilitat_028 import problems, save
from .test_accessibilitat_tresoreria import admin_url, screen
from .test_pagament_convidat import token  # noqa: F401 (fixture)
from .test_pagament_targeta import EMAIL, pending  # noqa: F401 (fixture)
from .test_pagaments_llistat import attempt
from .test_retornats import collected_item

pytestmark = pytest.mark.e2e
S = PaymentAttempt.Status
SETTING = "payments.bizum_ui_timeout_minutes"


def test_admin_payments_and_remittances(page, live_server, transactional_db, settings):
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.CLUB_IBAN_TRANSFERENCIES = iban(999)
    text = LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")
    holder = make_member(first="Signant", number=9999, document="99999999R")
    signer = Account.objects.create_personal(holder.person, "signant@example.org", PASSWORD)
    new_member(427, signer=signer, text=text, cents=3500)
    new_member(311, signer=signer, text=text)
    new_member(502, mandate=False)
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    attempt(person, "Quota 2027 (prova)", S.TO_REVIEW)
    attempt(person, "Quota d'un altre soci (prova)", S.IN_PROGRESS)
    treasurer = make_admin("tresoreria.prova", "treasurer")
    results, base = {}, live_server.url
    login_admin(page, base, treasurer.login)

    page.goto(admin_url(base, "payments_list"))
    expect(page.get_by_role("table", name="1 intent de pagament a revisar")).to_be_visible()
    screen(page, "pagaments-llistat", results)

    page.goto(admin_url(base, "payments_remittances"))
    screen(page, "remeses-buida", results)
    page.get_by_label("Període").fill("2026-12")
    page.get_by_role("button", name="Previsualitza").click()
    expect(page.get_by_role("alert")).to_contain_text("Es crearan 2 rebuts")
    screen(page, "remeses-previsualitzacio", results)
    page.get_by_role("button", name="Sí, crea la remesa").click()
    expect(page.get_by_role("status")).to_contain_text("Remesa creada")
    screen(page, "remesa-detall", results)

    # El fitxer, ja descarregat: sense, no es pot marcar com a enviada.
    sepa_xml.remittance_file(DirectDebitRemittance.objects.get(), treasurer)
    page.reload()
    page.get_by_label("He esborrat el fitxer del dispositiu").check()
    page.get_by_role("button", name="Marca com a enviada al banc").click()
    expect(page.get_by_role("status")).to_contain_text("enviada al banc")
    screen(page, "remesa-enviada", results)
    bank_line(12500, treasurer)
    page.get_by_role("button", name="Cerca l'abonament").click()
    page.get_by_role("button", name="Casa aquesta línia…").click()
    expect(page.get_by_role("alert")).to_contain_text("2 quotes passen a pagades")
    screen(page, "remesa-abonament-confirma", results)

    page.goto(admin_url(base, "payments_remittances"))
    screen(page, "remeses-amb-una", results)

    page.goto(admin_url(base, "settings_section", "payments"))
    screen(page, "ajustos-pagaments", results)
    page.goto(admin_url(base, "setting_detail", "payments", SETTING))
    screen(page, "ajust-pagaments", results)

    save(results, "05b-administracio")
    assert not problems(results), "\n".join(problems(results))


def test_admin_returns(page, live_server, transactional_db, settings, tmp_path):
    treasurer, item = collected_item(settings)
    results, base = {}, live_server.url
    login_admin(page, base, treasurer.login)
    page.goto(admin_url(base, "payments_returns"))
    screen(page, "retornats-buit", results)
    page.get_by_label("Referència del rebut").fill(item.end_to_end_id)
    page.get_by_label("Codi de motiu").fill("AM04")
    page.get_by_label("Comissió de retorn (€)").fill("3,00")
    page.get_by_role("button", name="Registra el retorn").click()
    expect(page.get_by_role("button", name="Reintent (intent 2)")).to_be_visible()
    screen(page, "retornats-per-decidir", results)

    path = tmp_path / "retornats.xml"
    path.write_bytes(pain002(tx("R-NO-EXISTEIX")))
    page.get_by_label("Fitxer de retornats (XML)").set_input_files(path)
    page.get_by_role("button", name="Previsualitza").click()
    expect(page.get_by_text("Cap rebut amb aquesta referència")).to_be_visible()
    screen(page, "retornats-fitxer-previsualitzacio", results)

    save(results, "05b-retornats")
    assert not problems(results), "\n".join(problems(results))


def test_member_payment_screens(page, live_server, settings, pending):  # noqa: F811
    fee, base = pending, live_server.url
    settings.CLUB_IBAN_TRANSFERENCIES = "ES00 0000 0000 0000 0000 0000"
    settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
    system = core_audit.system("proves-e2e")
    person = fee.charge.person
    bizum, card = (
        charges.create_charge(
            person,
            kind="fee",
            amount_cents=9000,
            concept=f"Quota {n} (prova)",
            origin="proves",
            by=system,
        )  # fmt: skip
        for n in ("Bizum", "targeta")
    )
    results = {}
    page.goto(f"{base}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()

    page.goto(f"{base}{reverse('members:fees')}")
    screen(page, "soci-les-meves-quotes", results)
    page.goto(f"{base}{reverse('members:fee_detail', args=[fee.pk])}")
    screen(page, "soci-quota-detall", results)

    def charge_page(charge):
        page.goto(f"{base}{reverse('payments:charge', args=[charge.pk])}")

    charge_page(fee.charge)
    expect(page.get_by_role("button", name="Paga amb Bizum")).to_be_visible()
    expect(page.get_by_role("button", name="Paga per transferència")).to_be_visible()
    screen(page, "soci-pagament-pendent", results)

    page.get_by_role("button", name="Paga per transferència").click()
    expect(page.get_by_role("button", name="Copia la referència")).to_be_visible()
    screen(page, "soci-pagament-transferencia", results)
    reconciler = make_admin("tresoreria.prova", "treasurer")
    (line,) = lines(reconciler, (fee.charge.amount_cents, f"TRANSF {ref(fee.charge)} QUOTA"))
    reconciliation.refresh()
    reconciliation.confirm(line, by=reconciler)
    page.reload()
    expect(page.locator("#estat-pagament")).to_contain_text("Pagat")
    screen(page, "soci-pagament-pagat", results)
    page.get_by_role("link", name="Veure el rebut").click()
    screen(page, "soci-rebut", results)
    receipt = Receipt.objects.get(attempt__charge=fee.charge)
    ReceiptCancellation.objects.create(receipt=receipt, note="Pagament duplicat (exemple).")
    page.reload()
    screen(page, "soci-rebut-anullat", results)

    charge_page(bizum)
    page.get_by_role("button", name="Paga amb Bizum").click()
    page.get_by_role("button", name="Torna sense confirmar").click()
    expect(page.locator("#estat-pagament")).to_contain_text("Esperant confirmació")
    screen(page, "soci-bizum-esperant", results)
    waiting = PaymentAttempt.objects.get(charge=bizum)
    waiting.created_at -= timedelta(minutes=15)
    waiting.save(update_fields=["created_at"])
    fake._bizum_expiry[waiting.provider_order_id] = timezone.now()
    charge_page(bizum)
    expect(page.locator("#estat-pagament")).to_contain_text("No s'ha confirmat a temps")
    screen(page, "soci-bizum-no-confirmat", results)

    charge_page(card)
    page.get_by_role("button", name="Paga amb targeta").click()
    page.get_by_role("button", name="Torna sense pagar").click()
    expect(page.get_by_text("Estem confirmant el pagament")).to_be_visible()
    screen(page, "soci-pagament-en-curs", results)
    attempts.transition(PaymentAttempt.objects.get(charge=card), S.FAILED, by=system)
    charge_page(card)
    expect(page.locator("#estat-pagament")).to_contain_text("No s'ha completat")
    screen(page, "soci-pagament-fallit", results)

    save(results, "05b-soci")
    assert not problems(results), "\n".join(problems(results))


def test_guest_payment_screen(page, live_server, token):  # noqa: F811
    results = {}
    page.goto(f"{live_server.url}/convidat/{token}/")
    page.get_by_role("link", name="Paga ara").click()
    expect(page.locator("#estat-pagament")).to_contain_text("Pendent")
    screen(page, "convidat-pagament-pendent", results)
    save(results, "05b-convidat")
    assert not problems(results), "\n".join(problems(results))
