"""Transferència de principi a fi al navegador (T-M05b-18; P-M05b-C i P-M04-E; decisió 092, banc
fictici): el soci tria «Paga per transferència»; el tresorer importa l'extracte del banc per la
pantalla (CSV), en confirma la importació i, a la conciliació, «Confirma» la línia proposada; el
soci veu «Pagat» i el rebut. Després el tresorer desfà la conciliació amb el motiu (045) i el
càrrec torna a estar pendent. Només dades inventades; l'IBAN del club és de proves."""

import datetime

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core.models import Charge
from apps.treasury.balances import balance
from apps.treasury.demo_data import _csv
from apps.treasury.models import TreasuryAccount
from apps.treasury.tests.test_reconciliation import ref
from conftest import PASSWORD

from .conftest import login_admin, make_admin
from .test_pagament_targeta import EMAIL, pending  # noqa: F401

pytestmark = pytest.mark.e2e


def test_transfer_imported_reconciled_undone_through_the_screens(
    page,
    live_server,
    settings,
    pending,  # noqa: F811
    capture,
    tmp_path,
):
    settings.CLUB_IBAN_TRANSFERENCIES = "ES00 0000 0000 0000 0000 0000"
    settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
    fee, base_url = pending, live_server.url
    treasurer = make_admin("tresoreria.prova", "treasurer")

    # El soci tria la transferència.
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{base_url}{reverse('payments:charge', args=[fee.charge.pk])}")
    page.get_by_role("button", name="Paga per transferència").click()
    expect(page.locator("#estat-pagament")).to_contain_text("Esperant la transferència")
    member_cookies = page.context.cookies()

    # El tresorer importa l'extracte del banc fictici per la pantalla.
    statement = tmp_path / "extracte.csv"
    text = f"TRANSF {ref(fee.charge)} QUOTA"
    statement.write_bytes(_csv(datetime.date.today(), [(0, text, fee.charge.amount_cents)]))
    page.context.clear_cookies()
    login_admin(page, base_url, treasurer.login)
    page.goto(f"{base_url}{reverse('administration:bank_statement')}")
    page.get_by_label("Fitxer de l'extracte del banc (CSV o Norma 43)").set_input_files(statement)
    page.get_by_role("button", name="Previsualitza").click()
    page.get_by_role("button", name="Confirma la importació").click()
    expect(page.get_by_text("Extracte importat")).to_be_visible()
    capture("1-extracte-importat")

    # Conciliació: la línia és proposada amb el càrrec; «Confirma».
    page.goto(f"{base_url}{reverse('administration:treasury_reconciliation')}")
    row = page.get_by_role("row").filter(has_text=ref(fee.charge))
    expect(row).to_contain_text("Proposada")
    capture("2-proposada")
    row.get_by_role("button", name="Confirma").click()
    row = page.get_by_role("row").filter(has_text=ref(fee.charge))
    expect(row).to_contain_text("Conciliada")
    assert Charge.objects.get(pk=fee.charge.pk).status == Charge.Status.PAID
    bank = TreasuryAccount.objects.get(name="Banc principal")
    assert balance(bank, datetime.date.today()) == fee.charge.amount_cents
    capture("3-conciliada")

    # El soci veu «Pagat» i el rebut.
    admin_cookies = page.context.cookies()
    page.context.clear_cookies()
    page.context.add_cookies(member_cookies)
    page.goto(f"{base_url}{reverse('payments:charge', args=[fee.charge.pk])}")
    expect(page.locator("#estat-pagament")).to_contain_text("Pagat")
    page.get_by_role("link", name="Veure el rebut").click()
    expect(page.get_by_role("heading", level=1, name="Rebut")).to_be_visible()

    # El tresorer la desfà amb el motiu (045): el càrrec torna a pendent i el banc, a zero.
    page.context.clear_cookies()
    page.context.add_cookies(admin_cookies)
    page.goto(f"{base_url}{reverse('administration:treasury_reconciliation')}")
    row = page.get_by_role("row").filter(has_text=ref(fee.charge))
    row.get_by_text("Desfés…").click()
    row.get_by_label("Motiu per desfer-la").fill("Era d'un altre soci (dada de prova).")
    row.get_by_role("button", name="Desfés la conciliació").click()
    expect(page.get_by_role("row").filter(has_text=ref(fee.charge))).not_to_contain_text(
        "Conciliada"
    )
    capture("4-desfeta")
    assert Charge.objects.get(pk=fee.charge.pk).status == Charge.Status.PENDING
    assert balance(bank, datetime.date.today()) == 0
