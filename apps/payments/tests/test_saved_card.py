"""Guardar una targeta per a les quotes (T-M05a-12; P-M05a-D; RN-M05a-10 i 12; CA-M05a-15; P-297 i
P-298, opcions per defecte). Proveïdor fals, que declara que guarda targetes (092), sense xarxa.
Només dades inventades.

El soci obre l'autenticació a la pantalla, el proveïdor envia la notificació signada a l'endpoint
i la cua la processa: només llavors hi ha targeta."""

import json
from dataclasses import replace
from datetime import timedelta

import pytest
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_PERSONAL
from apps.accounts.tests.test_reauth import NOT_IT
from apps.core.models import AuditEntry
from apps.members.models import Member
from apps.members.tests.test_cards import make_member
from apps.payments import cards, preferences, processing
from apps.payments.models import CardSetup, FeePaymentPreference, ProviderEvent, SavedCard
from apps.payments.providers import base, fake
from apps.payments.tests.test_fee_method import active_account
from apps.payments.tests.test_mandate_signing import age_session
from apps.payments.tests.test_processing import URL as NOTIFY
from apps.payments.tests.test_processing import no_wait, run_queue
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
URL = reverse("payments:saved_card")
CARD = base.ProviderCard("fake-card-referencia-opaca", "4821", 8, 2029)


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = "https://socis.example.org"
    settings.MANDATE_REAUTH_MINUTES = 15
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def member():
    return make_member()


@pytest.fixture
def account(member):
    return active_account(member.person, "anna.prova@example.org")


@pytest.fixture
def browser(login_as, account):
    return login_as(account, AREA_PERSONAL)


def order_of(setup):
    return setup.provider_order_id


def notify(order_id, status=base.PAID, *, card=None, event_id=None, **overrides):
    """El proveïdor avisa de l'autenticació a l'endpoint, com ho faria després de la pàgina."""
    body, headers = fake.FakeProvider().notification(order_id, status, card=card, event_id=event_id)
    if overrides:
        body = json.dumps({**json.loads(body), **overrides}, sort_keys=True).encode()
        headers = {fake.SIGNATURE_HEADER: fake.sign(body)}
    return Client().post(NOTIFY, data=body, content_type="application/json", headers=headers)


def start(browser):
    response = browser.post(URL)
    assert response.status_code == 302
    setup = CardSetup.objects.latest("pk")
    assert response.url == f"https://socis.example.org/pagaments/prova/{setup.provider_order_id}/"
    return setup


def test_ca_m05a_15_only_the_reference_last_digits_and_expiry_are_kept(browser, member, account):
    setup = start(browser)
    assert notify(order_of(setup), card=CARD).status_code == 200
    assert run_queue() == [ProviderEvent.Result.PROCESSED]

    saved = SavedCard.objects.get()
    assert (saved.person, saved.provider_code, saved.provider_card_id) == (
        member.person,
        "fake",
        CARD.card_ref,
    )
    assert (saved.last4, saved.expiry_month, saved.expiry_year, saved.status) == (
        "4821",
        8,
        2029,
        "active",
    )
    setup.refresh_from_db()
    assert (setup.status, setup.saved_card) == ("saved", saved)
    # P-298: la preferència passa a la targeta guardada, amb el compte que l'ha guardada.
    preference = FeePaymentPreference.objects.get(member=member)
    assert (preference.method, preference.saved_card, preference.set_by) == (
        "saved_card",
        saved,
        account,
    )
    page = browser.get(URL).content.decode()
    assert "… 4821" in page and "08/2029" in page
    # La referència del proveïdor no surt ni a la pantalla ni al registre d'activitat.
    assert CARD.card_ref not in page
    for entry in AuditEntry.objects.all():
        assert CARD.card_ref not in str((entry.details, entry.old_value, entry.new_value))
    assert AuditEntry.objects.filter(action=cards.STARTED, actor_account=account).exists()


def test_the_browser_return_saves_nothing(browser):
    start(browser)
    page = browser.get(URL + "?tornada=ok").content.decode()

    assert "Estem confirmant la targeta" in page
    assert not SavedCard.objects.exists()


def test_a_denied_authentication_saves_no_card(browser):
    setup = start(browser)
    notify(order_of(setup), base.DENIED)
    run_queue()

    setup.refresh_from_db()
    assert setup.status == "failed" and not SavedCard.objects.exists()
    assert "No s'ha guardat cap targeta" in browser.get(URL + "?tornada=ko").content.decode()


def test_a_repeated_notification_saves_one_card(browser):
    setup = start(browser)
    notify(order_of(setup), event_id="e-1")
    notify(order_of(setup), event_id="e-1")
    run_queue()

    assert SavedCard.objects.count() == 1


def test_p_297_a_new_card_replaces_the_active_one_with_an_audit_entry(browser, member):
    first = start(browser)
    notify(order_of(first))
    run_queue()
    second = start(browser)
    notify(order_of(second), card=CARD)
    run_queue()

    old, new = SavedCard.objects.order_by("pk")
    assert (old.status, new.status) == ("removed", "active")
    assert FeePaymentPreference.objects.get(member=member).saved_card == new
    entry = AuditEntry.objects.get(action=cards.REPLACED)
    assert (entry.target_id, entry.old_value, entry.new_value) == (str(old.pk), "active", "removed")


def test_starting_again_closes_the_earlier_setup(browser):
    first = start(browser)
    second = start(browser)

    first.refresh_from_db()
    assert (first.status, second.status) == ("failed", "in_progress")


def test_an_earlier_setup_that_finishes_late_does_not_replace_the_card(browser):
    first = start(browser)
    second = start(browser)
    notify(order_of(second), card=CARD)
    notify(order_of(first))

    assert run_queue() == [ProviderEvent.Result.PROCESSED, ProviderEvent.Result.TO_REVIEW]
    assert SavedCard.objects.get().provider_card_id == CARD.card_ref


def test_an_abandoned_setup_closes_after_the_safety_net_hours(browser, monkeypatch):
    setup = start(browser)
    no_wait(monkeypatch)
    processing.safety_net()
    setup.refresh_from_db()
    assert setup.status == "in_progress"  # encara a temps

    CardSetup.objects.filter(pk=setup.pk).update(created_at=timezone.now() - timedelta(hours=25))
    processing.safety_net()
    setup.refresh_from_db()
    assert setup.status == "failed"
    assert not cards.waiting(setup.person)


def test_if_the_card_cannot_be_read_the_safety_net_saves_it_later(browser, monkeypatch):
    setup = start(browser)
    notify(order_of(setup), card=CARD)
    real = fake.FakeProvider.get_card_setup

    def down(self, external_id):
        raise base.ProviderError("temps esgotat")

    monkeypatch.setattr(fake.FakeProvider, "get_card_setup", down)
    assert run_queue() == [ProviderEvent.Result.ERROR]
    assert not SavedCard.objects.exists()

    monkeypatch.setattr(fake.FakeProvider, "get_card_setup", real)
    no_wait(monkeypatch)
    processing.safety_net()
    assert SavedCard.objects.get().last4 == "4821"


def test_a_provider_error_on_start_is_a_message_not_a_500(browser, monkeypatch):
    def down(self, person, urls):
        raise base.ProviderError("caigut")

    monkeypatch.setattr(fake.FakeProvider, "_start_card_setup", down)
    response = browser.post(URL)

    assert response.status_code == 200
    assert "Ara no es pot guardar la targeta" in response.content.decode()
    assert not CardSetup.objects.exists()


def test_if_the_preference_cannot_change_the_card_is_kept_and_reviewed(
    browser, member, monkeypatch
):
    setup = start(browser)
    notify(order_of(setup), card=CARD)

    def refuse(*args, **kwargs):
        raise preferences.MethodNotOffered("saved_card")

    monkeypatch.setattr(preferences, "set_preference", refuse)
    assert run_queue() == [ProviderEvent.Result.TO_REVIEW]
    assert SavedCard.objects.get().status == "active"
    assert not FeePaymentPreference.objects.exists()


def test_an_unexpected_currency_goes_to_review(browser):
    setup = start(browser)
    notify(order_of(setup), currency="USD")

    assert run_queue() == [ProviderEvent.Result.TO_REVIEW]
    assert not SavedCard.objects.exists()


def test_an_unknown_status_from_the_provider_goes_to_review(browser):
    # La notificació del fals ja rebutja un estat desconegut; la consulta al proveïdor, no.
    setup = start(browser)
    state = base.OrderState(order_of(setup), "refunded", 0, "EUR")
    with transaction.atomic():
        assert cards.settle_setup(setup, state)
    setup.refresh_from_db()
    assert setup.status == "in_progress" and not SavedCard.objects.exists()


def test_a_setup_that_was_not_started_here_saves_nothing():
    order = fake.FakeProvider().start_card_setup(None, base.OrderUrls("n", "ok", "ko"))
    notify(order.external_id)

    assert run_queue() == [ProviderEvent.Result.TO_REVIEW]
    assert not SavedCard.objects.exists()


def test_an_authentication_with_an_amount_goes_to_review(browser):
    setup = start(browser)
    notify(order_of(setup), amount_cents=9000)

    assert run_queue() == [ProviderEvent.Result.TO_REVIEW]
    assert not SavedCard.objects.exists()


# --- Pantalla ---


def test_without_tokenization_the_route_does_not_exist(browser, monkeypatch):
    original = fake.FakeProvider.capabilities
    monkeypatch.setattr(
        fake.FakeProvider, "capabilities", lambda self: replace(original(self), tokenization=False)
    )
    assert browser.get(URL).status_code == 404
    assert browser.post(URL).status_code == 404
    assert not CardSetup.objects.exists()


@pytest.mark.parametrize("status", [Member.Status.PENDING, Member.Status.LEFT])
def test_only_an_active_or_unpaid_member_can_save_a_card(browser, member, status):
    Member.objects.filter(pk=member.pk).update(status=status)

    assert browser.get(URL).status_code == 404
    assert browser.post(URL).status_code == 404
    assert not CardSetup.objects.exists()


def test_rn_m05a_12_an_old_session_must_type_the_password(browser):
    age_session(browser, 16)
    assert 'name="password"' in browser.get(URL).content.decode()

    assert browser.post(URL, {"password": NOT_IT}).status_code == 200
    assert not CardSetup.objects.exists()
    assert browser.post(URL, {"password": PASSWORD}).status_code == 302
    assert CardSetup.objects.count() == 1


def test_choosing_saved_card_without_one_leads_to_the_card_page(browser):
    response = browser.post(reverse("payments:fee_method"), {"method": "saved_card"})

    assert response.url == URL
    assert not FeePaymentPreference.objects.exists()
