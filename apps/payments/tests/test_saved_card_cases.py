"""Casos del cobrament amb la targeta guardada (T-M05b-15): les proves de la 15a que, per mida,
viuen aquí, i les de la vuitena i la novena revisió de la 15c (soci pendent i arreus).
Proveïdor fals; només dades inventades."""

# ruff: noqa: F811

import pytest
from django.test import Client
from django.utils import timezone

from apps.core import audit, charges
from apps.core import privacy as core_privacy
from apps.core.models import Charge, OutgoingEmail, Payment, Person, Role
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member, pay
from apps.payments import attempts, checkout
from apps.payments.models import FeePaymentPreference, PaymentAttempt, SavedCard, SavedCardNotice
from apps.payments.providers import base, fake
from apps.payments.tests import test_guest_payment
from apps.payments.tests.test_fee_method import active_account
from apps.payments.tests.test_preferences import card, prefer
from apps.payments.tests.test_processing import URL as NOTIFY_URL
from apps.payments.tests.test_processing import notify, run_queue
from apps.payments.tests.test_saved_card_charge import (  # noqa: F401 (fixtures)
    account,
    clean_orders,
    due,
    fee,
    make_admin,
    member,
    only_attempt,
    review_emails,
    saved,
    treasurer,
)

pytestmark = pytest.mark.django_db
M = PaymentAttempt.Method
S = PaymentAttempt.Status


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


def test_an_error_on_one_fee_does_not_stop_the_run(saved, fee, monkeypatch):
    other = make_member(first="Pau", number=1288, document="87654321X")
    other_fee = due(add_fee(other), timezone.localdate())
    account = active_account(other.person, "pau.prova@example.org")
    prefer(other, account, "saved_card", saved_card=card(other, provider_card_id="c-9"))
    saved.status = "removed"
    saved.save()

    def broken(*args, **kwargs):
        raise RuntimeError("avís trencat")

    monkeypatch.setattr(checkout, "_not_charged", broken)
    checkout.charge_due_saved_cards()
    assert other_fee.charge.attempts.filter(method=M.SAVED_CARD).exists()


@pytest.mark.parametrize(
    ("how", "case"),
    [
        ("preference", checkout.PREFERENCE),
        (Member.Status.LEFT, checkout.NOT_MEMBER),
        (Member.Status.PENDING, checkout.PENDING_MEMBER),  # P-309, opció per defecte: no
    ],
)
def test_only_the_card_of_the_preference_of_an_active_member(saved, fee, member, how, case):
    if how == "preference":
        FeePaymentPreference.objects.filter(member=member).update(
            method="pay_each_time", saved_card=None
        )
    else:
        Member.objects.filter(pk=member.pk).update(status=how)
    with pytest.raises(checkout.CardNotUsable) as error:
        checkout.charge_saved_card(fee.charge, saved)
    assert error.value.case == case


def test_the_erasure_works_with_saved_cards(saved, fee, member, make_admin):  # noqa: F811
    checkout.charge_due_saved_cards()
    notify(only_attempt(fee))
    run_queue()
    core_privacy.anonymise_person(member.person, by=make_admin(Role.Code.ADMINISTRATOR))

    member.person.refresh_from_db()
    assert member.person.status == Person.Status.ANONYMISED
    assert SavedCard.objects.filter(pk=saved.pk).exists()  # mai no s'esborra


def test_a_card_of_another_person_is_incoherent_data(saved, fee):
    SavedCard.objects.filter(pk=saved.pk).update(
        person=make_member(number=1288, document="87654321X").person
    )
    with pytest.raises(checkout.CardNotUsable) as error:
        checkout.charge_saved_card(fee.charge, saved)
    assert error.value.case == checkout.OTHER_PERSON


# --- Vuitena revisió de #200 ---


def test_a_pending_member_is_not_charged_and_the_treasurer_hears_once(saved, fee, member):
    Member.objects.filter(pk=member.pk).update(status=Member.Status.PENDING)
    checkout.charge_due_saved_cards()
    checkout.charge_due_saved_cards()

    assert not fake._orders
    assert SavedCardNotice.objects.get().case == checkout.PENDING_MEMBER


def test_a_closed_card_is_said_before_the_arrears(saved, member):
    add_fee(member, period=2025)  # fora de la finestra (P-302)
    saved.status = "removed"
    saved.save()
    checkout.charge_due_saved_cards()
    assert SavedCardNotice.objects.get().case == checkout.CARD_CLOSED


def test_a_fee_in_arrears_leaves_the_daily_list_once_said(saved, member):
    old = add_fee(member, period=2025)
    checkout.charge_due_saved_cards()
    assert SavedCardNotice.objects.get(charge=old.charge).case == checkout.ARREARS
    due = checkout.due_saved_card_charges(timezone.localdate())
    assert old.charge.pk not in [c.pk for c, _card in due]


# --- Proves de la 15a que, per mida, viuen aquí (novena revisió) ---


def test_only_annual_fees(saved, member):
    other = charges.create_charge(
        member.person, kind=Charge.Kind.FEE, amount_cents=4000, concept="Suplement",
        origin="members", by=audit.system("prova"),
    )  # fmt: skip
    with pytest.raises(checkout.CardNotUsable):
        checkout.charge_saved_card(other, saved)
    assert not PaymentAttempt.objects.exists()


def test_a_waiting_transfer_is_not_charged_said_once_and_charged_when_it_goes(
    saved, fee, account, settings, treasurer
):
    settings.CLUB_IBAN_TRANSFERENCIES = test_guest_payment.IBAN
    start = checkout.start_payment(fee.charge, "transfer", account)

    checkout.charge_due_saved_cards()
    checkout.charge_due_saved_cards()

    transfer = PaymentAttempt.objects.get(pk=start.attempt_id)
    assert transfer.status == S.IN_PROGRESS
    assert not fee.charge.attempts.filter(method=M.SAVED_CARD).exists()
    assert SavedCardNotice.objects.filter(charge=fee.charge).count() == 1
    assert "transferència en espera" in review_emails().get().body_text

    attempts.transition(transfer, S.ABANDONED, by=audit.system("prova"))
    assert checkout.charge_due_saved_cards() == 1  # l'avís no la treu de la llista


def test_only_the_first_saved_card_attempt_per_fee(saved, fee):
    checkout.charge_saved_card(fee.charge, saved)
    notify(only_attempt(fee), base.DENIED)
    run_queue()

    with pytest.raises(checkout.AlreadyAttempted):
        checkout.charge_saved_card(fee.charge, saved)
    assert fee.charge.attempts.count() == 1
