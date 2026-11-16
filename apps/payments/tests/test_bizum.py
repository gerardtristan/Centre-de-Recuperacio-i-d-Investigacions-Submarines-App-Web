"""Pagar amb Bizum (T-M05b-04, la resta; P-M05b-B; RN-M05b-04, 05, 07 i 08; CA-M05b-06).
Proveïdor fals, sense xarxa. Només dades inventades i cap telèfon.

Els 15 minuts (l'ajust inicial de VC-17) són de la pantalla (RN-M05b-07): l'intent no es tanca
a la pantalla, i el nou només s'obre quan el proveïdor diu que l'ordre ja no és oberta. La
caducitat real del proveïdor és la P-45 punt 13; el fals fa caducar l'ordre sola."""

import re
from datetime import timedelta
from uuid import uuid4

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_PERSONAL
from apps.core.models import Charge, Payment
from apps.payments import checkout
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.providers import base, fake
from apps.payments.tests.test_checkout import SITE, new_charge
from apps.payments.tests.test_payment_screen import CONFIRMING, finish, screen
from apps.payments.tests.test_processing import notify, run_queue, transit  # noqa: F401

pytestmark = pytest.mark.django_db
S = Attempt.Status
WAITING = "Esperant confirmació a l'app del teu banc"
TIMED_OUT = "No s'ha confirmat a temps"


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = SITE
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def charge(personal_account):
    return new_charge(personal_account.person)


@pytest.fixture
def member(login_as, personal_account):
    return login_as(personal_account, AREA_PERSONAL)


def pay_bizum(client, charge):
    return client.post(reverse("payments:pay_bizum", args=[charge.pk]))


def minutes_pass(attempt, minutes=15, *, provider_closes=True):
    """Passen `minutes` des que es va obrir l'intent; amb `provider_closes`, el proveïdor ja ha
    fet caducar l'ordre (el fals la fa caducar sola)."""
    attempt.created_at -= timedelta(minutes=minutes)
    attempt.save(update_fields=["created_at"])
    if provider_closes:
        fake._bizum_expiry[attempt.provider_order_id] = timezone.now()


class TestStart:
    def test_the_order_is_bizum_with_the_charge_amount_and_the_provider_expiry(
        self, charge, personal_account
    ):
        start = checkout.start_payment(charge, "bizum", personal_account)

        attempt = Attempt.objects.get()
        assert (attempt.method, attempt.status, attempt.amount_cents) == (
            "bizum",
            S.IN_PROGRESS,
            9000,
        )
        assert attempt.expires_at == fake._bizum_expiry[attempt.provider_order_id]
        assert (start.kind, start.url) == (
            checkout.REDIRECT,
            f"{SITE}{fake.PAY_PATH}{attempt.provider_order_id}/",
        )
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PENDING  # RN-M05b-05

    def test_not_offered_if_the_provider_does_not_offer_it(self, member, charge, monkeypatch):
        monkeypatch.setattr(
            fake.FakeProvider,
            "capabilities",
            lambda self: base.Capabilities(
                card=True, bizum=False, tokenization=False, refund_bizum=False, embedded_field=False
            ),
        )
        assert "Paga amb Bizum" not in member.get(screen(charge)).content.decode()
        response = pay_bizum(member, charge)
        assert response["Location"] == screen(charge) and not Attempt.objects.exists()
        assert "Ara no es pot pagar amb Bizum" in member.get(screen(charge)).content.decode()

    def test_the_charge_of_someone_else_is_not_found(self, member, make_person):
        other = new_charge(make_person("Pau", "Inventat"))
        assert pay_bizum(member, other).status_code == 404
        assert not Attempt.objects.exists()


class TestWaiting:
    def test_the_screen_waits_for_the_bank_app_and_asks_again(self, member, charge):
        response = pay_bizum(member, charge)
        attempt = Attempt.objects.get()
        assert response["Location"] == f"{SITE}{fake.PAY_PATH}{attempt.provider_order_id}/"

        html = member.get(screen(charge) + "?tornada=ko").content.decode()
        assert WAITING in html and 'hx-trigger="every 3s"' in html
        assert "Paga amb" not in html and CONFIRMING not in html
        assert not re.search(r'<input[^>]*type="tel"', html)  # cap telèfon a la plataforma

    def test_before_15_minutes_a_new_one_waits_and_the_provider_is_not_asked(
        self, member, charge, monkeypatch
    ):
        pay_bizum(member, charge)
        minutes_pass(Attempt.objects.get(), 14)
        monkeypatch.setattr(fake.FakeProvider, "get_order", lambda *a: pytest.fail("consultat"))
        assert pay_bizum(member, charge)["Location"] == screen(charge)
        assert Attempt.objects.count() == 1


class TestCaM05b06TimedOut:
    def test_after_15_minutes_not_confirmed_in_time_and_the_charge_stays_pending(
        self, member, charge
    ):
        pay_bizum(member, charge)
        attempt = Attempt.objects.get()
        minutes_pass(attempt, provider_closes=False)

        assert checkout.payment_status(charge).state == checkout.TIMED_OUT
        status = reverse("payments:attempt_status", args=[attempt.pk])
        html = member.get(status, headers={"HX-Request": "true"}).content.decode()
        assert TIMED_OUT in html and "hx-trigger" not in html  # ja no es torna a demanar
        assert "Paga amb Bizum" in html and "Paga amb targeta" in html
        charge.refresh_from_db()
        attempt.refresh_from_db()
        # RN-M05b-07: la pantalla no tanca res; l'intent el tanca el proveïdor.
        assert (charge.status, attempt.status) == (Charge.Status.PENDING, S.IN_PROGRESS)

    def test_a_card_does_not_time_out_on_the_screen(self, charge, personal_account):
        checkout.start_payment(charge, "card", personal_account)
        minutes_pass(Attempt.objects.get(), 60, provider_closes=False)
        assert checkout.payment_status(charge).state == checkout.IN_PROGRESS

    @pytest.mark.parametrize("again", ["bizum", "card"])
    def test_it_can_be_tried_again_once_the_provider_has_closed_the_order(
        self, member, charge, again
    ):
        pay_bizum(member, charge)
        first = Attempt.objects.get()
        minutes_pass(first)

        member.post(reverse(f"payments:pay_{again}", args=[charge.pk]))

        first.refresh_from_db()
        new = Attempt.objects.get(status=S.IN_PROGRESS)
        assert first.status == S.EXPIRED and new.method == again
        assert len(fake._orders) == 2
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PENDING

    def test_if_the_provider_still_has_it_open_the_new_one_waits(self, member, charge):
        """El proveïdor real pot fer caducar l'ordre més tard que la pantalla (P-45 punt 13)."""
        pay_bizum(member, charge)
        minutes_pass(Attempt.objects.get(), provider_closes=False)

        response = pay_bizum(member, charge)

        assert response["Location"] == screen(charge)
        assert Attempt.objects.get().status == S.IN_PROGRESS and len(fake._orders) == 1
        html = member.get(screen(charge)).content.decode()
        assert "El pagament anterior encara no s&#x27;ha tancat" in html

    def test_if_the_provider_cannot_be_asked_nothing_changes(self, member, charge, monkeypatch):
        pay_bizum(member, charge)
        minutes_pass(Attempt.objects.get())
        monkeypatch.setattr(
            fake.FakeProvider, "get_order", lambda *a: (_ for _ in ()).throw(base.ProviderError)
        )
        assert pay_bizum(member, charge)["Location"] == screen(charge)
        assert Attempt.objects.get().status == S.IN_PROGRESS

    def test_if_the_provider_says_paid_it_is_paid_and_nothing_new_starts(
        self,
        member,
        charge,
        transit,  # noqa: F811
    ):
        pay_bizum(member, charge)
        attempt = Attempt.objects.get()
        minutes_pass(attempt, provider_closes=False)
        fake.FakeProvider().notification(attempt.provider_order_id, base.PAID)  # confirmat al banc

        pay_bizum(member, charge)

        attempt.refresh_from_db()
        charge.refresh_from_db()
        assert (attempt.status, charge.status) == (S.PAID, Charge.Status.PAID)
        assert Attempt.objects.count() == 1 and Payment.objects.get().method == "bizum"
        assert "Pagat" in member.get(screen(charge)).content.decode()

    def test_rn_m05b_08_a_late_confirmation_is_accepted_while_the_charge_is_pending(
        self,
        member,
        charge,
        transit,  # noqa: F811
    ):
        pay_bizum(member, charge)
        attempt = Attempt.objects.get()
        minutes_pass(attempt, provider_closes=False)

        notify(attempt)
        run_queue()

        charge.refresh_from_db()
        assert charge.status == Charge.Status.PAID

    def test_a_failed_bizum_shows_failed_and_can_be_tried_again(self, member, charge):
        pay_bizum(member, charge)
        finish(Attempt.objects.get(), S.FAILED)
        html = member.get(screen(charge)).content.decode()
        assert "No s'ha completat" in html and "Paga amb Bizum" in html


class TestFakeProviderPage:
    def test_bizum_is_confirmed_as_in_the_bank_app_without_a_phone(self, member, charge):
        pay_bizum(member, charge)
        order = Attempt.objects.get().provider_order_id
        html = Client().get(reverse("payments:fake_pay", args=[order])).content.decode()
        assert "Confirma a l'app del banc" in html and "90,00" in html
        assert not re.search(r'<input[^>]*type="(text|number|tel|password)"', html)

    def test_an_unconfirmed_bizum_expires_at_the_provider(self, charge):
        provider = fake.FakeProvider()
        urls = base.OrderUrls("n", "ok", "ko")
        order = provider.create_order(charge, base.BIZUM, urls, uuid4())
        assert provider.get_order(order.external_id).status == base.PENDING
        fake._bizum_expiry[order.external_id] = timezone.now()
        assert provider.get_order(order.external_id).status == base.EXPIRED
        url = reverse("payments:fake_pay", args=[order.external_id])
        assert Client().get(url).status_code == 404  # ja no es pot confirmar
