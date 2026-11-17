"""Cobrament de la quota amb la targeta guardada (T-M05b-15; RN-M05b-20; P-302, opció per
defecte). Proveïdor fals, que guarda targetes (092), sense xarxa. Només dades inventades.

La tasca diària obre l'intent amb la targeta de la preferència; «pagat» només arriba amb la
notificació. Els avisos al soci i al tresorer són de la T-M05b-15b."""

from datetime import date, timedelta

import pytest
from django.db import connection, transaction
from django.db.models import F
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Payment, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member, pay
from apps.payments import attempts, checkout, guards, processing, returns
from apps.payments.models import (
    FeePaymentPreference,
    PaymentAttempt,
    SavedCardAttempt,
    SavedCardNotice,
)
from apps.payments.providers import base, fake
from apps.payments.tests.test_fee_method import active_account
from apps.payments.tests.test_preferences import card, prefer
from apps.payments.tests.test_processing import no_wait, notify, run_queue

pytestmark = pytest.mark.django_db
S = PaymentAttempt.Status
M = PaymentAttempt.Method


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = "https://socis.example.org"
    settings.SAVED_CARD_AUTO_CHARGE_ENABLED = True
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
    return due(add_fee(member), timezone.localdate())  # venç avui


def due(fee, day):
    fee.due_on = day
    fee.save(update_fields=["due_on"])
    return fee


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
    assert "/pagaments/prova/" not in str(list(OutgoingEmail.objects.values_list("body_text")))
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
    real = fake.FakeProvider._charge_saved_card

    def broken(self, *args):
        real(self, *args)  # el proveïdor cobra, però la resposta no arriba
        raise RuntimeError("la connexió ha caigut")

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", broken)
    checkout.charge_due_saved_cards()
    monkeypatch.undo()
    attempt = only_attempt(fee)
    assert attempt.status == S.IN_PROGRESS and attempt.provider_order_id  # desat abans

    checkout.charge_due_saved_cards()  # l'endemà: no es torna a cobrar
    assert len(fake._orders) == 1
    notify(attempt)
    assert run_queue() == ["processed"]
    assert Payment.objects.filter(charge=fee.charge).count() == 1


def test_an_expired_card_is_not_used_and_it_is_said_once(saved, fee):
    saved.expiry_month, saved.expiry_year = 12, 2025
    saved.save()

    checkout.charge_due_saved_cards()
    checkout.charge_due_saved_cards()

    assert not PaymentAttempt.objects.exists()
    assert AuditEntry.objects.filter(action=processing.OUTCOME).count() == 1
    assert OutgoingEmail.objects.filter(template="alternativa-pagament").count() == 1


def test_only_once_per_fee_and_only_when_due(saved, fee, member, monkeypatch):
    checkout.charge_due_saved_cards()
    assert checkout.charge_due_saved_cards() == 0  # ja en curs

    later = add_fee(member, period=2027)
    monkeypatch.setattr(checkout.timezone, "localdate", lambda *args: date(2026, 12, 31))
    assert checkout.charge_due_saved_cards() == 0
    assert not later.charge.attempts.exists()


def test_level_1_no_saved_card_is_charged(saved, fee, settings):
    settings.PAYMENTS_ENVIRONMENT = "live"
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False

    assert checkout.charge_due_saved_cards() == 0
    with pytest.raises(base.LiveChargesNotAllowed):
        checkout.charge_saved_card(fee.charge, saved)
    assert not PaymentAttempt.objects.exists()
    with pytest.raises(base.LiveChargesNotAllowed):  # tampoc amb un proveïdor passat
        checkout.charge_saved_card(fee.charge, saved, provider=object())
    assert AuditEntry.objects.filter(action=guards.REFUSED).count() == 2  # només les directes


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


def review_emails():
    return OutgoingEmail.objects.filter(template=processing.TREASURER_TEMPLATE)


def test_a_fee_paid_by_hand_before_the_call_is_not_charged(saved, fee, monkeypatch):
    real = checkout._open_saved_card_attempt

    def then_paid(*args, **kwargs):
        opened = real(*args, **kwargs)
        pay(fee)  # una altra via, entre les dues transaccions
        return opened

    monkeypatch.setattr(checkout, "_open_saved_card_attempt", then_paid)
    checkout.charge_due_saved_cards()

    assert only_attempt(fee).status == S.ABANDONED
    assert not fake._orders  # el proveïdor no ha rebut res


def test_a_provider_error_keeps_the_order_and_tells_the_treasurer(saved, fee, monkeypatch):
    def down(*args, **kwargs):
        raise base.ProviderError("temps esgotat")

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", down)
    checkout.charge_due_saved_cards()
    attempt = only_attempt(fee)
    assert attempt.status == S.IN_PROGRESS and attempt.provider_order_id
    assert AuditEntry.objects.filter(
        action=processing.TO_REVIEW, target_id=str(fee.charge.pk)
    ).exists()


# --- Vuitena revisió de #191 ---


def test_a_provider_without_order_ids_opens_nothing_and_tells_the_treasurer(
    saved, fee, monkeypatch, treasurer
):
    def unsupported(*args):
        raise base.NotSupported("tokenization")

    monkeypatch.setattr(fake.FakeProvider, "saved_card_order_id", unsupported)
    checkout.charge_due_saved_cards()

    assert not PaymentAttempt.objects.exists()
    AuditEntry.objects.get(action=processing.TO_REVIEW, target_id=str(fee.charge.pk))
    assert review_emails().exists()  # la referència és el càrrec del registre


def test_an_amount_changed_before_the_call_is_charged_the_next_day(saved, fee, monkeypatch):
    real = checkout._open_saved_card_attempt

    def then_changed(*args, **kwargs):
        opened = real(*args, **kwargs)
        Charge.objects.filter(pk=fee.charge.pk).update(amount_cents=F("amount_cents") + 500)
        return opened

    monkeypatch.setattr(checkout, "_open_saved_card_attempt", then_changed)
    checkout.charge_due_saved_cards()
    monkeypatch.undo()
    assert only_attempt(fee).status == S.ABANDONED and not fake._orders

    assert checkout.charge_due_saved_cards() == 1  # l'endemà, amb l'import corregit
    assert len(fake._orders) == 1


def test_the_card_is_checked_on_the_day_of_the_run(saved, fee, monkeypatch):
    saved.expiry_month, saved.expiry_year = 1, 2026
    saved.save()
    due(fee, date(2026, 1, 31))
    calls, real = [], checkout.timezone.localdate

    def midnight(*args):  # la tasca comença el 31/1 i la crida arriba passada la mitjanit
        if args:
            return real(*args)
        calls.append(1)
        return date(2026, 1, 31) if len(calls) == 1 else date(2026, 2, 1)

    monkeypatch.setattr(checkout.timezone, "localdate", midnight)
    checkout.charge_due_saved_cards()
    assert only_attempt(fee).status == S.IN_PROGRESS and len(fake._orders) == 1


# --- Novena revisió de #191 ---


def test_p_302_only_fees_due_within_the_window_are_charged(saved, member, treasurer):
    today = timezone.localdate()
    recent, old = (
        due(add_fee(member), today - timedelta(days=7)),
        due(add_fee(member, period=2025), today - timedelta(days=8)),
    )
    assert checkout.charge_due_saved_cards() == 1
    assert recent.charge.attempts.exists() and not old.charge.attempts.exists()
    assert SavedCardNotice.objects.get(charge=old.charge).case == checkout.ARREARS
    assert AuditEntry.objects.filter(
        action=processing.TO_REVIEW, target_id=str(old.charge.pk)
    ).exists()
    assert not review_emails().exists()  # cap correu al tresorer; el soci, l'alternativa
    assert alternatives().count() == 1
    assert old.charge.pk not in [c.pk for c, _card in checkout.due_saved_card_charges(today)]


def test_a_card_replaced_after_the_due_date_still_charges_the_fee(saved, member, account):
    fee = due(add_fee(member), timezone.localdate() - timedelta(days=3))
    saved.status = "removed"
    saved.save()
    new = card(member, provider_card_id="c-2")
    FeePaymentPreference.objects.filter(member=member).update(saved_card=new, since=timezone.now())
    assert checkout.charge_due_saved_cards() == 1 and fee.charge.attempts.exists()


def test_an_opening_error_is_told_once(saved, fee, monkeypatch, treasurer):
    def unsupported(*args):
        raise base.NotSupported("tokenization")

    monkeypatch.setattr(fake.FakeProvider, "saved_card_order_id", unsupported)
    checkout.charge_due_saved_cards()
    checkout.charge_due_saved_cards()
    assert review_emails().count() == 1


def test_no_card_is_the_preference_case(fee):
    assert (
        checkout._unusable(None, fee.charge, fake.FakeProvider(), timezone.localdate())
        == checkout.PREFERENCE
    )


def test_the_payment_screen_does_not_take_the_saved_card(saved, fee, account):
    with pytest.raises(attempts.MethodNotAllowed):
        checkout.start_payment(fee.charge, "saved_card", account)


def test_the_automatic_charge_is_off_by_default(saved, fee, settings, caplog):
    settings.SAVED_CARD_AUTO_CHARGE_ENABLED = False
    entries = AuditEntry.objects.count()
    assert checkout.charge_due_saved_cards() == 0
    assert not PaymentAttempt.objects.exists() and not SavedCardNotice.objects.exists()
    assert AuditEntry.objects.count() == entries and not caplog.records
    settings.SAVED_CARD_AUTO_CHARGE_ENABLED = True
    assert checkout.charge_due_saved_cards() == 1


# --- Avisos (T-M05b-15b): un sol punt d'entrada, `processing.saved_card_outcome` ---


def alternatives():
    return OutgoingEmail.objects.filter(template="alternativa-pagament")


def test_a_denial_tells_member_and_treasurer_once_with_the_references(saved, fee, treasurer):
    checkout.charge_due_saved_cards()
    notify(only_attempt(fee), base.DENIED)
    notify(only_attempt(fee), base.DENIED)  # repetida
    run_queue()

    (email,) = alternatives()
    assert "amb la teva targeta guardada" in email.body_text
    (notice,) = review_emails()
    assert (
        f"quota {fee.pk}, càrrec {fee.charge.pk}" in notice.body_text
        and "denegat" in notice.body_text
    )
    entry = AuditEntry.objects.get(action=processing.OUTCOME)
    assert entry.actor_origin == processing.SAVED_CARD_ACTOR


@pytest.mark.parametrize("who", ["no_email", "erased"])
def test_when_the_member_cannot_be_told_the_treasurer_knows_why(saved, fee, member, treasurer, who):
    saved.status = "removed"
    saved.save()
    if who == "no_email":
        Person.objects.filter(pk=member.person_id).update(contact_email="")
    else:
        Person.objects.filter(pk=member.person_id).update(
            status=Person.Status.ANONYMISED, anonymous_ref="anon-prova"
        )
    checkout.charge_due_saved_cards()

    assert not alternatives().exists()
    text = review_emails().get().body_text
    assert ("no té cap adreça" if who == "no_email" else "RGPD") in text


def test_a_failed_email_is_retried_the_next_day(saved, fee, monkeypatch, treasurer):
    saved.status = "removed"
    saved.save()
    real = returns.send_alternative

    def broken(*args, **kwargs):
        raise RuntimeError("correu caigut")

    monkeypatch.setattr(returns, "send_alternative", broken)
    checkout.charge_due_saved_cards()
    assert not SavedCardNotice.objects.get().notified and not review_emails().exists()

    monkeypatch.setattr(returns, "send_alternative", real)
    checkout.charge_due_saved_cards()
    assert SavedCardNotice.objects.get().notified and alternatives().count() == 1


def test_an_email_error_does_not_undo_closing_the_attempt(saved, fee, monkeypatch):
    monkeypatch.setattr(returns, "send_alternative", lambda *a, **k: 1 / 0)
    checkout.charge_due_saved_cards()
    notify(only_attempt(fee), base.DENIED)

    assert run_queue() == ["processed"]
    assert only_attempt(fee).status == S.FAILED


def test_an_unexpected_order_is_kept_and_reviewed(saved, fee, monkeypatch):
    real = fake.FakeProvider._charge_saved_card

    def other(self, charge, card, key):
        order = real(self, charge, card, key)
        fake._orders["fake-una-altra"] = fake._orders[order.external_id]
        return base.ProviderOrder("fake-una-altra", order.pay_url, None)

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", other)
    checkout.charge_due_saved_cards()
    attempt = only_attempt(fee)
    assert (attempt.status, attempt.provider_order_id) == (S.TO_REVIEW, "fake-una-altra")

    notify(attempt)  # la troba, però és a revisar: cap cobrament automàtic
    assert run_queue() == ["to_review"]
    assert not Payment.objects.filter(charge=fee.charge).exists()


def test_a_case_of_the_treasurer_tells_only_the_treasurer(saved, fee, member, treasurer):
    Member.objects.filter(pk=member.pk).update(status=Member.Status.LEFT)
    checkout.charge_due_saved_cards()

    assert not alternatives().exists()
    assert "ja no és sòcia" in review_emails().get().body_text


# --- Vuitena revisió de #198 ---


def broken(*args, **kwargs):
    raise RuntimeError("correu caigut")


def other_order(pay_url=False):
    real = fake.FakeProvider._charge_saved_card

    def other(self, charge, card, key):
        order = real(self, charge, card, key)
        fake._orders["fake-una-altra"] = fake._orders[order.external_id]
        return base.ProviderOrder(
            "fake-una-altra", "https://banc.example.org/3ds" if pay_url else None, None
        )

    return other


def test_an_email_error_never_undoes_the_review_of_an_unexpected_order(saved, fee, monkeypatch):
    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", other_order())
    monkeypatch.setattr(processing, "notify_treasurers", broken)
    attempt = checkout.charge_saved_card(fee.charge, saved)
    monkeypatch.undo()

    assert attempt.status == S.TO_REVIEW == only_attempt(fee).status  # el que torna, al dia
    notify(only_attempt(fee))
    assert run_queue() == ["to_review"]
    assert not Payment.objects.filter(charge=fee.charge).exists()


def test_an_unexpected_order_that_asks_for_authentication_is_closed(saved, fee, monkeypatch):
    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", other_order(pay_url=True))
    attempt = checkout.charge_saved_card(fee.charge, saved)
    assert attempt.status == S.ABANDONED
    assert SavedCardNotice.objects.get().case == "authentication"


def test_a_retry_says_nothing_about_a_fee_paid_in_between(saved, fee, monkeypatch, treasurer):
    saved.status = "removed"
    saved.save()
    monkeypatch.setattr(returns, "send_alternative", broken)
    checkout.charge_due_saved_cards()
    monkeypatch.undo()
    pay(fee)

    checkout.charge_due_saved_cards()
    assert not alternatives().exists() and not review_emails().exists()
    assert SavedCardNotice.objects.get().notified  # ja no cal


def test_emails_that_keep_failing_end_up_to_review(saved, fee, monkeypatch, treasurer):
    saved.status = "removed"
    saved.save()
    monkeypatch.setattr(returns, "send_alternative", broken)
    for _day in range(processing.NOTICE_TRIES + 1):
        checkout.charge_due_saved_cards()

    assert OutgoingEmail.objects.filter(template=processing.REVIEW_TEMPLATE).count() == 1
    checkout.charge_due_saved_cards()  # no hi torna
    assert OutgoingEmail.objects.filter(template=processing.REVIEW_TEMPLATE).count() == 1


@pytest.mark.parametrize("case", ["provider_error", "unexpected_order", "give_up"])
def test_the_treasurer_is_told_it_may_have_been_charged(saved, fee, treasurer, case):
    with transaction.atomic():
        processing.saved_card_outcome(fee.charge, case, card=saved)
    text = review_emails().get().body_text
    assert "pot ser que s'hagi cobrat" in text and "comprova-ho al proveïdor" in text
    assert "no s'ha cobrat" not in text


def test_a_charge_that_is_not_a_fee_has_no_empty_fee_reference(saved, member, treasurer):
    other = charges.create_charge(
        member.person, kind=Charge.Kind.FEE, amount_cents=4000, concept="Suplement",
        origin="members", by=audit.system("prova"),
    )  # fmt: skip
    with transaction.atomic():
        processing.saved_card_outcome(other, "not_fee", card=saved)
    text = review_emails().get().body_text
    assert f"càrrec {other.pk}" in text and "quota ," not in text


def test_the_provider_error_outcome_runs_with_the_charge_locked(saved, fee, monkeypatch):
    def down(*args, **kwargs):
        raise base.ProviderError("temps esgotat")

    monkeypatch.setattr(fake.FakeProvider, "_charge_saved_card", down)
    real, seen = processing.saved_card_outcome, []

    def spy(charge, case, **kwargs):
        last = connection.queries[-1]["sql"]
        seen.append('FROM "core_charge"' in last and "FOR UPDATE" in last)
        return real(charge, case, **kwargs)

    monkeypatch.setattr(processing, "saved_card_outcome", spy)
    with CaptureQueriesContext(connection), pytest.raises(base.ProviderError):
        checkout.charge_saved_card(fee.charge, saved)
    assert seen == [True]


def test_a_failure_without_its_card_still_settles_and_is_reviewed(saved, fee):
    checkout.charge_saved_card(fee.charge, saved)
    SavedCardAttempt.objects.all().delete()
    notify(only_attempt(fee), base.DENIED)

    assert run_queue() == ["processed"]
    assert only_attempt(fee).status == S.FAILED
    assert AuditEntry.objects.filter(action=processing.TO_REVIEW).exists()


def test_an_unknown_closing_state_goes_to_review_without_telling_the_member(saved, fee):
    attempt = checkout.charge_saved_card(fee.charge, saved)
    attempt = attempts.transition(attempt, S.ABANDONED, by=audit.system("prova"))
    with transaction.atomic():
        processing.on_saved_card_failed(attempt, fee.charge)
    assert not alternatives().exists()
    assert AuditEntry.objects.filter(action=processing.TO_REVIEW).exists()


def test_the_safety_net_keeps_why_it_gave_up(saved, fee, monkeypatch):
    checkout.charge_saved_card(fee.charge, saved)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE payments_paymentattempt SET created_at = created_at - %s",
            [timedelta(hours=200)],
        )

    def down(*args, **kwargs):
        raise base.ProviderError("temps esgotat")

    monkeypatch.setattr(fake.FakeProvider, "get_order", down)
    no_wait(monkeypatch)
    processing.safety_net()
    entry = AuditEntry.objects.get(action=processing.OUTCOME)
    assert "consultar l'ordre" in entry.details["detail"]
