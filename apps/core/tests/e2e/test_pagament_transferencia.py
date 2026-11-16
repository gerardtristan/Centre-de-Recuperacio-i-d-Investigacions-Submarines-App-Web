"""Pagar per transferència al navegador (T-M05b-06; P-M05b-C; CA-M05b-10 i 11). Entorn de proves,
només dades inventades; l'IBAN del club és de proves.

El soci tria «Paga per transferència» i veu l'IBAN del club, l'import i la referència, cadascun
amb «Copia». La pantalla no dona res per pagat: el tresorer confirma la conciliació de la línia
de l'extracte (aquí, el servei de la 04, que encara no té pantalla) i, en tornar-hi, el soci veu
«Pagat» i el rebut."""

import pytest
from playwright.sync_api import expect

from apps.core.models import Charge
from apps.payments.models import PaymentAttempt
from apps.treasury import reconciliation
from apps.treasury.tests.test_reconciliation import lines, ref
from conftest import PASSWORD

from .conftest import make_admin
from .test_pagament_targeta import EMAIL, pending  # noqa: F401

pytestmark = pytest.mark.e2e


@pytest.fixture
def reconciler(transactional_db):
    """El tresorer, que té T4 a la configuració inicial (T-M04-12b)."""
    return make_admin("tresoreria.prova", "treasurer")


def test_ca_m05b_10_11_transfer_details_then_paid_with_receipt(
    page,
    live_server,
    settings,
    pending,  # noqa: F811
    reconciler,
    capture,
):
    settings.CLUB_IBAN_TRANSFERENCIES = "ES00 0000 0000 0000 0000 0000"
    settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
    fee, base_url = pending, live_server.url
    page.context.grant_permissions(["clipboard-read", "clipboard-write"], origin=base_url)
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{base_url}/socis/pagaments/{fee.charge.pk}/")
    status = page.locator("#estat-pagament")

    # CA-M05b-10: l'IBAN del club, l'import i la referència, cadascun copiable.
    page.get_by_role("button", name="Paga per transferència").click()
    expect(status).to_contain_text("Esperant la transferència")
    expect(status).to_contain_text("ES00 0000 0000 0000 0000 0000")
    expect(status).to_contain_text(ref(fee.charge))
    for name in ("Copia l'IBAN", "Copia l'import", "Copia la referència"):
        expect(page.get_by_role("button", name=name)).to_be_visible()
    expect(page.get_by_role("button", name="Paga per transferència")).to_have_count(0)
    page.get_by_role("button", name="Copia la referència").click()
    expect(page.get_by_role("button", name="Referència copiada")).to_be_visible()
    assert page.evaluate("navigator.clipboard.readText()") == ref(fee.charge)
    capture("1-esperant-la-transferencia")
    assert Charge.objects.get(pk=fee.charge.pk).status == Charge.Status.PENDING

    # El tresorer concilia la línia de l'extracte (P-M04-E): el càrrec és pagat.
    (line,) = lines(reconciler, (fee.charge.amount_cents, f"TRANSF {ref(fee.charge)} QUOTA"))
    reconciliation.refresh()
    reconciliation.confirm(line, by=reconciler)

    # CA-M05b-11: «Pagat» i el rebut.
    page.reload()
    expect(status).to_contain_text("Pagat")
    capture("2-pagat")
    page.get_by_role("link", name="Veure el rebut").click()
    expect(page.get_by_role("heading", level=1, name="Rebut")).to_be_visible()
    expect(page.locator("main")).to_contain_text("Transferència")
    capture("3-rebut")
    attempt = PaymentAttempt.objects.get(charge=fee.charge)
    assert (attempt.method, attempt.status) == ("transfer", "paid")
