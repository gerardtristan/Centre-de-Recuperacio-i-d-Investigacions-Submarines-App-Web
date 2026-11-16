"""El rebut al navegador (T-M05b-07; RN-M05b-19; CA-M05b-03). Proveïdor fals, entorn de proves,
només dades inventades.

El soci paga la quota amb targeta a la pàgina del proveïdor fals; la cua processa la notificació
signada i la pantalla de pagament passa a «Pagat» amb l'enllaç al rebut. El rebut porta el
número, el concepte, l'import, el departament, la data i el mètode, i es desa com a PDF des del
navegador (P-85). La quota pagada porta a la pantalla de pagament."""

import re

import pytest
from django.utils import timezone
from playwright.sync_api import expect

from apps.core.models import OutgoingEmail
from apps.treasury.models import TreasuryAccount
from conftest import PASSWORD

from .test_flux_primer_euro import run_queue
from .test_pagament_targeta import EMAIL, pending  # noqa: F401 (fixture)

pytestmark = pytest.mark.e2e


def test_rn_m05b_19_the_member_pays_and_opens_the_receipt(page, live_server, pending, capture):  # noqa: F811
    fee, base_url = pending, live_server.url
    # El compte de trànsit del proveïdor (RN-T08) ja hi és des de `migrate` (T-M04-17).
    transit = TreasuryAccount.objects.filter(kind="transit", provider_code="fake", active=True)
    assert transit.exists()
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.get_by_role("navigation", name="Compte personal").get_by_role(
        "link", name="Les meves quotes"
    ).click()
    page.get_by_role("link", name=re.compile("^Detall")).click()
    page.get_by_role("link", name="Paga ara").click()
    page.get_by_role("button", name="Paga amb targeta").click()
    page.get_by_role("button", name="Paga", exact=True).click()
    expect(page.get_by_text("Estem confirmant el pagament")).to_be_visible()

    # La cua processa la notificació: pagat, rebut i correu (CA-M05b-03).
    assert run_queue() == ["processed"]
    expect(page.locator("#estat-pagament")).to_contain_text("Pagat", timeout=10_000)
    capture("1-pagat-amb-el-rebut")
    number = f"R-{timezone.localdate().year}-000001"
    assert OutgoingEmail.objects.filter(template="pagament-confirmat").count() == 1

    page.get_by_role("link", name="Veure el rebut").click()
    expect(page.get_by_role("heading", level=1, name="Rebut")).to_be_visible()
    main = page.locator("main")
    for text in (number, fee.charge.concept, "General", "Targeta", "No és una factura"):
        expect(main).to_contain_text(text)
    expect(page.get_by_role("button", name="Desa com a PDF")).to_be_visible()
    capture("2-rebut")

    # Des de la quota pagada, a la pantalla de pagament.
    page.goto(f"{base_url}/socis/quotes/{fee.pk}/")
    capture("3-quota-pagada")
    page.get_by_role("link", name="Veure el pagament").click()
    expect(page.get_by_role("link", name="Veure el rebut")).to_be_visible()
