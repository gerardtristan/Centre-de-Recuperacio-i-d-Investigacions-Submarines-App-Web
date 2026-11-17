"""Cobrament de la quota amb la targeta guardada (T-M05b-15; RN-M05b-20; P-302, opció per
defecte). Proveïdor fals, que guarda targetes (092), sense xarxa. Només dades inventades.

La tasca diària obre l'intent amb la targeta de la preferència; «pagat» només arriba amb la
notificació. Els avisos al soci i al tresorer són de la T-M05b-15b."""

from datetime import date, timedelta

import pytest
from django.db import connection
from django.test import Client

from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Payment, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_cards import add_fee, make_member, pay
from apps.payments import attempts, checkout, guards, processing
from apps.payments.models import FeePaymentPreference, PaymentAttempt, SavedCardNotice
from apps.payments.providers import base, fake
from apps.payments.tests import test_guest_payment
from apps.payments.tests.test_fee_method import active_account
from apps.payments.tests.test_preferences import card, prefer
from apps.payments.tests.test_processing import URL as NOTIFY_URL
from apps.payments.tests.test_processing import no_wait, notify, run_queue

pytestmark = pytest.mark.django_db
S = PaymentAttempt.Status
M = PaymentAttempt.Method


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = "https://socis.example.org"
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def member():
    member = make_member()
    member.person.contact_email = "anna.prova@example.org"
    member.person.save()
    return member


@pytest.fixture
def saved(member):
    account = active_account(member.person, "anna.prova@example.org")
    saved = card(member, expiry_month=8, expiry_year=2029)
    prefer(member, account, "saved_card", saved_card=saved)
    return saved


@pytest.fixture
def account(saved, member):
    return member.person.accounts.get()


@pytest.fixture
def fee(member):
    return add_fee(member)  # venç l'1/1/2026


def only_attempt(fee):
    return PaymentAttempt.objects.get(charge=fee.charge)


def test_rn_m05b_20_the_due_fee_is_charged_without_the_member_and_paid_by_the_notification(
    saved, fee
):
    assert checkout.charge_due_saved_cards() == 1
    attempt = only_attempt(fee)
    assert (attempt.method, attempt.status, attempt.started_by) == (
        M.SAVED_CARD,
        S.IN_PROGRESS,
        None,
    )
    assert attempt.amount_cents == fee.charge.amount_cents
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PENDING  # encara no: només amb la notificació

    notify(attempt)
    assert run_queue() == ["processed"]
    attempt.refresh_from_db()
    fee.charge.refresh_from_db()
    assert (attempt.status, fee.charge.status) == (S.PAID, Charge.Status.PAID)
    # Per a la 00 i la tresoreria, una targeta guardada és una targeta.
    assert Payment.objects.get(charge=fee.charge).method == Payment.Method.CARD


def test_rn_m05b_20_authentication_keeps_the_attempt_and_sends_only_that_link(
    saved, fee, account, settings
):
    settings.CLUB_IBAN_TRANSFERENCIES = test_guest_payment.IBAN
    fake.FakeProvider().require_authentication(saved.provider_card_id)

    checkout.charge_due_saved_cards()

    attempt = only_attempt(fee)
    fee.charge.refresh_from_db()
    assert (attempt.status, fee.charge.status) == (S.IN_PROGRESS, Charge.Status.PENDING)
    # Mentre espera, el soci no pot pagar d'una altra manera: cap segon cobrament possible.
    for method in ("card", "transfer"):
        with pytest.raises(attempts.AttemptInProgress):
            checkout.start_payment(fee.charge, method, account)
    notify(attempt)  # la confirma tard
    run_queue()
    assert Payment.objects.filter(charge=fee.charge).count() == 1


def test_a_denied_charge_leaves_the_fee_pending(saved, fee):
    checkout.charge_due_saved_cards()
    notify(only_attempt(fee), base.DENIED)
    run_queue()

    fee.charge.refresh_from_db()
    assert (only_attempt(fee).status, fee.charge.status) == (S.FAILED, Charge.Status.PENDING)


def test_a_failure_after_the_provider_call_does_not_charge_twice(saved, fee, monkeypatch):
    real = checkout._save_order

    def broken(*args, **kwargs):
        raise RuntimeError("la base de dades ha caigut")

    monkeypatch.setattr(checkout, "_save_order", broken)
    checkout.charge_due_saved_cards()
    attempt = only_attempt(fee)
    assert (attempt.status, attempt.provider_order_id) == (S.IN_PROGRESS, "")

    monkeypatch.setattr(checkout, "_save_order", real)
    checkout.charge_due_saved_cards()  # la mateixa clau: la mateixa ordre
    assert len(fake._orders) == 1
    attempt = only_attempt(fee)
    assert attempt.provider_order_id
    notify(attempt)
    assert run_queue() == ["processed"]
    assert Payment.objects.filter(charge=fee.charge).count() == 1


def test_only_the_first_saved_card_attempt_per_fee(saved, fee):
    checkout.charge_saved_card(fee.charge, saved)
    notify(only_attempt(fee), base.DENIED)
    run_queue()

    with pytest.raises(checkout.AlreadyAttempted):
        checkout.charge_saved_card(fee.charge, saved)
    assert fee.charge.attempts.count() == 1


def test_an_expired_card_is_not_used_and_it_is_said_once(saved, fee):
    saved.expiry_month, saved.expiry_year = 12, 2025
    saved.save()

    checkout.charge_due_saved_cards()
    checkout.charge_due_saved_cards()

    assert not PaymentAttempt.objects.exists()
    assert AuditEntry.objects.filter(action=checkout.NOT_CHARGED).count() == 1
    assert not OutgoingEmail.objects.filter(template="alternativa-pagament").exists()  # 15b


def test_only_annual_fees(saved, member):
    other = charges.create_charge(
        member.person, kind=Charge.Kind.FEE, amount_cents=4000, concept="Suplement",
        origin="members", by=audit.system("prova"),
    )  # fmt: skip
    with pytest.raises(checkout.CardNotUsable):
        checkout.charge_saved_card(other, saved)
    assert not PaymentAttempt.objects.exists()


def test_only_once_per_fee_and_only_when_due(saved, fee, member, monkeypatch):
    checkout.charge_due_saved_cards()
    assert checkout.charge_due_saved_cards() == 0  # ja en curs

    later = add_fee(member, period=2027)
    monkeypatch.setattr(checkout.timezone, "localdate", lambda: date(2026, 12, 31))
    assert checkout.charge_due_saved_cards() == 0
    assert not later.charge.attempts.exists()


@pytest.mark.parametrize("how", ["pay_each_time", "removed"])
def test_no_charge_without_an_active_saved_card_preference(saved, fee, member, how):
    if how == "removed":
        saved.status = "removed"
        saved.save()
    else:
        FeePaymentPreference.objects.filter(member=member).update(
            method="pay_each_time", saved_card=None
        )
    assert checkout.charge_due_saved_cards() == 0
    assert not PaymentAttempt.objects.exists()


def test_a_card_of_another_person_is_not_used(saved, member):
    other = make_member(first="Pau", number=1288, document="87654321X")
    other_fee = add_fee(other)
    with pytest.raises(checkout.CardNotUsable):
        checkout.charge_saved_card(other_fee.charge, saved)
    assert not PaymentAttempt.objects.exists()


def test_level_1_no_saved_card_is_charged(saved, fee, settings):
    settings.PAYMENTS_ENVIRONMENT = "live"
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False

    assert checkout.charge_due_saved_cards() == 0
    with pytest.raises(base.LiveChargesNotAllowed):
        checkout.charge_saved_card(fee.charge, saved)
    assert not PaymentAttempt.objects.exists()
    assert AuditEntry.objects.filter(action=guards.REFUSED).count() == 2


def test_the_member_cannot_choose_saved_card_on_the_payment_screen():
    assert M.SAVED_CARD not in attempts.SCREEN_METHODS


# --- Segona revisió de #191 ---


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin(Role.Code.TREASURER)
    account.notification_email = "tresoreria@example.org"
    account.save()
    return account


def unfinished(fee, monkeypatch):
    """Un intent que no va arribar a desar l'ordre (la crida al proveïdor va fallar)."""

    def broken(*args, **kwargs):
        raise base.ProviderError("temps esgotat")

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", broken)
    checkout.charge_due_saved_cards()
    monkeypatch.undo()
    attempt = only_attempt(fee)
    assert (attempt.status, attempt.provider_order_id) == (S.IN_PROGRESS, "")
    return attempt


def test_an_unfinished_attempt_is_closed_when_the_card_no_longer_works(
    saved, fee, account, monkeypatch, treasurer
):
    attempt = unfinished(fee, monkeypatch)
    saved.status = "removed"
    saved.save()

    checkout.charge_due_saved_cards()
    attempt.refresh_from_db()
    assert attempt.status == S.TO_REVIEW
    # Potser el proveïdor ja ha cobrat: el tresorer ho revisa, i cap alternativa al soci.
    assert review_emails().exists()
    assert not OutgoingEmail.objects.filter(template="alternativa-pagament").exists()
    checkout.start_payment(fee.charge, "card", account)  # el soci ja pot pagar


def test_the_safety_net_closes_an_old_unfinished_attempt(saved, fee, member, monkeypatch):
    attempt = unfinished(fee, monkeypatch)
    FeePaymentPreference.objects.filter(member=member).update(
        method="pay_each_time", saved_card=None
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE payments_paymentattempt SET created_at = created_at - %s",
            [timedelta(hours=25)],
        )
    processing.safety_net()
    attempt.refresh_from_db()
    assert attempt.status == S.TO_REVIEW


def test_an_attempt_in_progress_is_skipped_quietly(saved, fee, account, monkeypatch, caplog):
    due = checkout.due_saved_card_charges(date(2026, 6, 1))
    checkout.start_payment(fee.charge, "card", account)
    monkeypatch.setattr(checkout, "due_saved_card_charges", lambda today: due)

    assert checkout.charge_due_saved_cards() == 0
    assert not [r for r in caplog.records if r.levelname == "ERROR"]


def test_level_1_without_due_fees_writes_nothing(settings):
    settings.PAYMENTS_ENVIRONMENT = "live"
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False

    assert checkout.charge_due_saved_cards() == 0
    assert not AuditEntry.objects.filter(action=guards.REFUSED).exists()


# --- Tercera revisió de #191: camins de doble cobrament ---


def review_emails():
    return OutgoingEmail.objects.filter(template="avis-pagament-revisar")


def test_an_unfinished_attempt_is_not_resumed_for_a_paid_fee(saved, fee, monkeypatch):
    attempt = unfinished(fee, monkeypatch)
    pay(fee)

    with pytest.raises(attempts.ChargeNotPayable):
        checkout.charge_saved_card(fee.charge, saved)
    attempt.refresh_from_db()
    assert attempt.status == S.TO_REVIEW and not fake._orders


def test_an_unfinished_attempt_is_not_resumed_with_another_card(
    saved, fee, member, account, monkeypatch
):
    attempt = unfinished(fee, monkeypatch)
    saved.status = "removed"
    saved.save()
    new = card(member, provider_card_id="c-2")
    FeePaymentPreference.objects.filter(member=member).update(saved_card=new)

    checkout.charge_due_saved_cards()
    attempt.refresh_from_db()
    assert attempt.status == S.TO_REVIEW and not fake._orders


def test_a_notification_before_the_order_is_saved_waits_for_the_safety_net(saved, fee, monkeypatch):
    real = fake.FakeProvider._charge_saved_card

    def fast_bank(self, charge, card, key):
        order = real(self, charge, card, key)
        body, headers = self.notification(order.external_id, base.PAID)
        Client().post(NOTIFY_URL, data=body, content_type="application/json", headers=headers)
        assert run_queue() == ["received"]  # encara no troba l'intent: s'espera
        return order

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", fast_bank)
    checkout.charge_due_saved_cards()
    monkeypatch.undo()
    no_wait(monkeypatch)
    processing.safety_net()

    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PAID
    assert Payment.objects.filter(charge=fee.charge).count() == 1


def test_a_waiting_transfer_is_not_charged_by_card_and_the_treasurer_is_told_once(
    saved, fee, account, settings, treasurer
):
    settings.CLUB_IBAN_TRANSFERENCIES = test_guest_payment.IBAN
    checkout.start_payment(fee.charge, "transfer", account)

    checkout.charge_due_saved_cards()
    checkout.charge_due_saved_cards()

    assert not fee.charge.attempts.filter(method=M.SAVED_CARD).exists()
    assert SavedCardNotice.objects.filter(charge=fee.charge).count() == 1
    assert not OutgoingEmail.objects.filter(template="alternativa-pagament").exists()


def test_no_alternative_for_a_fee_paid_by_hand_in_between(saved, fee, monkeypatch):
    checkout.charge_due_saved_cards()
    attempt = only_attempt(fee)
    pay(fee)
    notify(attempt, base.DENIED)
    run_queue()

    assert not OutgoingEmail.objects.filter(template="alternativa-pagament").exists()


def test_the_safety_net_only_closes_unfinished_attempts_of_its_provider(saved, fee, monkeypatch):
    attempt = unfinished(fee, monkeypatch)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE payments_paymentattempt SET provider_code = 'altre', "
            "created_at = created_at - %s",
            [timedelta(hours=25)],
        )
    processing.safety_net()
    attempt.refresh_from_db()
    assert attempt.status == S.IN_PROGRESS


def test_the_not_charged_marker_is_on_the_fee(saved, fee):
    saved.status = "removed"
    saved.save()
    checkout.charge_due_saved_cards()

    assert SavedCardNotice.objects.filter(charge=fee.charge).exists()
    assert checkout.due_saved_card_charges(date(2026, 6, 1)) == []
