"""Pagar amb Bizum al navegador (T-M05b-04; P-M05b-B; RN-M05b-07; CA-M05b-06). Proveïdor fals,
entorn de proves, només dades inventades i cap telèfon.

El soci tria Bizum, a la pàgina del proveïdor fals no el confirma i torna: la pantalla espera la
confirmació a l'app del banc. Passats 15 minuts (la prova n'avança el rellotge de l'intent i fa
caducar l'ordre al proveïdor fals), HTMX hi posa «No s'ha confirmat a temps» i el càrrec
continua pendent. Es torna a provar, es confirma i la cua processa la notificació: «Pagat»."""

import re
from datetime import timedelta

import pytest
from django.utils import timezone
from playwright.sync_api import expect

from apps.core.models import Charge
from apps.payments.models import PaymentAttempt
from apps.payments.providers import fake
from apps.treasury.models import TreasuryAccount
from conftest import PASSWORD

from .test_flux_primer_euro import run_queue
from .test_pagament_targeta import EMAIL, POLL, pending  # noqa: F401

pytestmark = pytest.mark.e2e
S = PaymentAttempt.Status


def test_ca_m05b_06_bizum_waits_times_out_and_can_be_tried_again(
    page,
    live_server,
    pending,  # noqa: F811
    capture,
):
    fee, base_url = pending, live_server.url
    # El compte de trànsit del proveïdor (RN-T08) ja hi és des de `migrate` (T-M04-17).
    transit = TreasuryAccount.objects.filter(kind="transit", provider_code="fake", active=True)
    assert transit.exists()
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{base_url}/socis/pagaments/{fee.charge.pk}/")
    status = page.locator("#estat-pagament")
    expect(page.get_by_role("button", name="Paga amb Bizum")).to_be_visible()
    capture("1-pendent-amb-bizum")

    # La pàgina del proveïdor fa el paper de l'app del banc; cap camp per al telèfon.
    page.get_by_role("button", name="Paga amb Bizum").click()
    expect(page.get_by_role("button", name="Confirma a l'app del banc")).to_be_visible()
    expect(page.locator("main input:not([type=hidden])")).to_have_count(0)
    capture("2-pagina-del-proveidor-bizum")

    page.get_by_role("button", name="Torna sense confirmar").click()
    expect(status).to_contain_text("Esperant confirmació a l'app del teu banc")
    expect(page.get_by_role("button", name="Paga amb Bizum")).to_have_count(0)
    capture("3-esperant-confirmacio")

    # CA-M05b-06: passen 15 minuts i el proveïdor fa caducar l'ordre.
    attempt = PaymentAttempt.objects.get(charge=fee.charge)
    attempt.created_at -= timedelta(minutes=15)
    attempt.save(update_fields=["created_at"])
    fake._bizum_expiry[attempt.provider_order_id] = timezone.now()
    expect(status).to_contain_text("No s'ha confirmat a temps", timeout=POLL)
    expect(page.get_by_role("button", name="Paga amb Bizum")).to_be_visible()
    capture("4-no-confirmat-a-temps")
    assert Charge.objects.get(pk=fee.charge.pk).status == Charge.Status.PENDING

    # Es torna a provar: el proveïdor diu que l'ordre ha caducat, i se n'obre una de nova.
    page.get_by_role("button", name="Paga amb Bizum").click()
    page.get_by_role("button", name="Confirma a l'app del banc").click()
    expect(page).to_have_url(re.compile(r"\?tornada=ok$"))
    attempt.refresh_from_db()
    assert attempt.status == S.EXPIRED
    assert PaymentAttempt.objects.get(status=S.IN_PROGRESS).method == "bizum"

    # Mai pel navegador: només la notificació processada el dona per pagat (RN-M05b-05).
    assert run_queue() == ["processed"]
    expect(status).to_contain_text("Pagat", timeout=POLL)
    capture("5-pagat")
