"""Llesca 2 («el primer euro», `docs/plans/pla-acceleracio.md` §3): el flux sencer al navegador,
de la quota pendent al carnet vàlid, pagant amb targeta (P-M05b-A i P-M05b-D del pla).

Són els trams de la llesca 1 (`test_flux_fer_se_soci.join_flow`: sol·licitud, aprovació,
compte, quota pendent, soci actiu, carnet i verificació pública) amb el pagament fet pel soci:

4. El soci, a «Les meves quotes», prem «Paga ara» i «Paga amb targeta» (CA-M05b-01); a la
   pàgina del proveïdor fals, «Paga». El proveïdor envia la notificació signada a la plataforma i
   torna el navegador: «Estem confirmant el pagament» i el càrrec encara és pendent (CA-M05b-02).
5. La cua processa la notificació (T-M05b-05): intent i càrrec pagats, pagament, ingrés a la
   tresoreria al compte de trànsit del proveïdor i soci actiu amb carnet (CA-M05b-03). La
   pantalla del soci passa a «Pagat» sola (HTMX).

La cua la fa córrer la prova, com `run_queue` de `apps/payments/tests/test_processing.py`: és el
que faria el procés de la cua. Només dades inventades; proveïdor fals, entorn de proves.
"""

import re
from urllib.parse import urlsplit

import pyotp
import pytest
from django.utils import timezone
from playwright.sync_api import expect
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.accounts.models import TotpDevice
from apps.core.models import Charge, Payment
from apps.payments import processing
from apps.payments.models import PaymentAttempt, ProviderEvent
from apps.payments.providers import fake
from apps.treasury.models import Movement, TreasuryAccount

from .conftest import TOTP_KEY, login_admin
from .test_flux_fer_se_soci import join_flow, login_personal

pytestmark = pytest.mark.e2e

TREASURER = "tresoreria.prova"  # el de `join_flow`, que el crea al tram 4


@pytest.fixture
def card_payments(settings, live_server):
    """Proveïdor fals amb la tornada i l'avís a aquest servidor. Torna el compte de trànsit del
    proveïdor on va l'ingrés (RN-T08), que ningú no crea a mà: ja hi és des de `migrate`
    (T-M04-17)."""
    settings.PUBLIC_SITE_URL = live_server.url
    fake.reset()
    yield TreasuryAccount.objects.get(kind="transit", provider_code="fake")
    fake.reset()


def run_queue():
    """El que fa el procés de la cua amb les notificacions pendents."""
    jobs = ProcrastinateJob.objects.filter(task_name="payments.process_notification")
    return [processing.process_notification(job.args["event_id"]) for job in jobs.order_by("id")]


def test_llesca_2_from_the_pending_fee_to_the_valid_card_paying_by_card(
    page, live_server, builder, secretary, member, card_payments, capture
):
    def pay_by_card(page, builder, fee):
        url = urlsplit(page.url)
        base_url = f"{url.scheme}://{url.netloc}"
        page.context.clear_cookies()  # el soci, al seu navegador

        # 4. El soci paga amb targeta a la pàgina del proveïdor (CA-M05b-01).
        login_personal(page, base_url)
        page.get_by_role("navigation", name="Compte personal").get_by_role(
            "link", name="Les meves quotes"
        ).click()
        page.get_by_role("link", name=re.compile("^Detall")).click()
        page.get_by_role("link", name="Paga ara").click()
        page.get_by_role("button", name="Paga amb targeta").click()
        expect(page.get_by_role("heading", name="Pagament de proves")).to_be_visible()
        capture("4-pagina-del-proveidor")
        page.get_by_role("button", name="Paga", exact=True).click()

        # CA-M05b-02: la tornada diu que s'està confirmant; el càrrec no ha canviat.
        expect(page).to_have_url(re.compile(r"\?tornada=ok$"))
        expect(page.get_by_text("Estem confirmant el pagament")).to_be_visible()
        capture("4-tornada-confirmant")
        fee.charge.refresh_from_db()
        assert fee.charge.status == Charge.Status.PENDING
        assert ProviderEvent.objects.get().result == ProviderEvent.Result.RECEIVED

        # 5. La cua processa la notificació signada (CA-M05b-03); la pantalla ho mostra sola.
        assert run_queue() == [ProviderEvent.Result.PROCESSED]
        expect(page.locator("#estat-pagament")).to_contain_text("Pagat", timeout=10_000)
        capture("5-pagat")
        attempt = PaymentAttempt.objects.get(charge=fee.charge)
        payment = Payment.objects.get(charge=fee.charge)
        assert attempt.status == PaymentAttempt.Status.PAID
        assert payment.amount_cents == fee.charge.amount_cents
        income = Movement.objects.get(kind=Movement.Kind.INCOME, payment=payment)
        assert (income.account, income.amount_cents) == (card_payments, fee.charge.amount_cents)
        page.context.clear_cookies()

        # Torna la tresoreria, on la deixa el tram 4 de la llesca 1. Un codi TOTP no serveix dues
        # vegades: s'espera el següent si el de l'entrada anterior encara és vigent.
        device = TotpDevice.objects.get(account__login=TREASURER)
        while pyotp.TOTP(TOTP_KEY).timecode(timezone.now()) <= device.last_used_step:
            page.wait_for_timeout(1000)
        login_admin(page, base_url, TREASURER)

    join_flow(page, live_server.url, builder, secretary, member, pay_by_card, capture)
