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


def test_rn_m05b_20_authentication_closes_the_attempt_at_once(saved, fee, account):
    """P-303: ningú no pot autenticar una ordre fora de sessió; l'intent es tanca i l'adreça del
    banc no es desa ni s'envia. El soci pot pagar d'una altra manera i res no cobra dues vegades."""
    fake.FakeProvider().require_authentication(saved.provider_card_id)

    checkout.charge_due_saved_cards()

    attempt = only_attempt(fee)
    assert (attempt.status, attempt.review_reason) == (S.ABANDONED, "")
    assert "/pagaments/prova/" not in str(list(AuditEntry.objects.values_list("details", "reason")))
    assert not OutgoingEmail.objects.exists()
    start = checkout.start_payment(fee.charge, "card", account)
    notify(PaymentAttempt.objects.get(pk=start.attempt_id))
    notify(attempt, event_id="tard")  # una confirmació tardana de l'ordre tancada
    run_queue()
    assert Payment.objects.filter(charge=fee.charge).count() == 1


def test_a_denied_charge_leaves_the_fee_pending(saved, fee):
    checkout.charge_due_saved_cards()
    notify(only_attempt(fee), base.DENIED)
    run_queue()

    fee.charge.refresh_from_db()
    assert (only_attempt(fee).status, fee.charge.status) == (S.FAILED, Charge.Status.PENDING)


def test_a_failure_after_the_provider_call_does_not_charge_twice(saved, fee, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("la base de dades ha caigut")

    monkeypatch.setattr(checkout, "_save_order", broken)
    checkout.charge_due_saved_cards()
    monkeypatch.undo()
    attempt = only_attempt(fee)
    assert attempt.status == S.IN_PROGRESS and attempt.provider_order_id  # desat abans

    checkout.charge_due_saved_cards()  # l'endemà: no es torna a cobrar
    assert len(fake._orders) == 1
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


def test_a_call_that_never_reached_the_provider_is_closed_by_the_safety_net(
    saved, fee, account, monkeypatch, treasurer
):
    def down(*args, **kwargs):
        raise base.ProviderError("temps esgotat")

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", down)
    checkout.charge_due_saved_cards()
    monkeypatch.undo()
    attempt = only_attempt(fee)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE payments_paymentattempt SET created_at = created_at - %s",
            [timedelta(hours=25)],
        )
    no_wait(monkeypatch)
    processing.safety_net()  # el proveïdor no coneix l'ordre: passades les hores, «a revisar»

    attempt.refresh_from_db()
    assert attempt.status == S.TO_REVIEW
    assert review_emails().exists()
    assert not OutgoingEmail.objects.filter(template="alternativa-pagament").exists()
    checkout.start_payment(fee.charge, "card", account)  # el soci ja pot pagar


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


def review_emails():
    return OutgoingEmail.objects.filter(template="avis-pagament-revisar")


def test_a_notification_before_the_response_finds_its_attempt(saved, fee, monkeypatch):
    real = fake.FakeProvider._charge_saved_card

    def fast_bank(self, charge, card, key):
        order = real(self, charge, card, key)
        body, headers = self.notification(order.external_id, base.PAID)
        Client().post(NOTIFY_URL, data=body, content_type="application/json", headers=headers)
        assert run_queue() == ["processed"]  # l'intent ja porta l'ordre
        return order

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", fast_bank)
    checkout.charge_due_saved_cards()

    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PAID
    assert Payment.objects.filter(charge=fee.charge).count() == 1


def test_a_waiting_transfer_is_abandoned_like_start_payment(saved, fee, account, settings):
    settings.CLUB_IBAN_TRANSFERENCIES = test_guest_payment.IBAN
    start = checkout.start_payment(fee.charge, "transfer", account)

    checkout.charge_due_saved_cards()

    assert PaymentAttempt.objects.get(pk=start.attempt_id).status == S.ABANDONED  # P-136
    assert fee.charge.attempts.get(method=M.SAVED_CARD).status == S.IN_PROGRESS


def test_no_alternative_for_a_fee_paid_by_hand_in_between(saved, fee, monkeypatch):
    checkout.charge_due_saved_cards()
    attempt = only_attempt(fee)
    pay(fee)
    notify(attempt, base.DENIED)
    run_queue()

    assert not OutgoingEmail.objects.filter(template="alternativa-pagament").exists()


def test_the_notice_is_per_card_and_a_new_card_is_charged(saved, fee, member):
    saved.status = "removed"
    saved.save()
    checkout.charge_due_saved_cards()
    checkout.charge_due_saved_cards()
    assert SavedCardNotice.objects.filter(charge=fee.charge, card=saved).count() == 1

    new = card(member, provider_card_id="c-2")
    FeePaymentPreference.objects.filter(member=member).update(saved_card=new)
    assert checkout.charge_due_saved_cards() == 1


def test_an_unexpected_order_goes_to_review(saved, fee, monkeypatch):
    real = fake.FakeProvider._charge_saved_card

    def other(self, charge, card, key):
        order = real(self, charge, card, key)
        return base.ProviderOrder("fake-una-altra", order.pay_url, None)

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", other)
    checkout.charge_due_saved_cards()
    assert only_attempt(fee).status == S.TO_REVIEW
