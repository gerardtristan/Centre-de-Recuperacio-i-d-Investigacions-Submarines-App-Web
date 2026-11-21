"""Terminis de pagament, ofertes de plaça i caducitat (T-M02-13; RN-M02-08 i RN-M02-09; CA-M02-09 i
CA-M02-27; L-M02-01). Portat de la branca aparcada. Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import deadlines, enrolment, states, tasks
from apps.activities.models import Enrolment
from apps.core import business_settings
from apps.core.models import AuditEntry, Charge, Role, Setting, SettingVersion
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import checkout
from apps.payments.models import PaymentAttempt
from apps.payments.providers import fake
from apps.treasury.demo_data import iban

from .helpers import BEFORE_DEADLINE, CLOSES, a_member, an_open_outing

pytestmark = pytest.mark.django_db

S = Enrolment.Status
NOW = BEFORE_DEADLINE
LATER = NOW + datetime.timedelta(hours=73)  # passat el termini de 72 hores


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.fixture(autouse=True)
def club(settings):
    settings.CLUB_IBAN_TRANSFERENCIES = iban(999)
    settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
    fake.reset()
    yield
    fake.reset()


def enrol(activity, account=None, *, now=NOW):
    account = account or a_member()
    return enrolment.enrol(activity, account.person, channel="account", actor=account, now=now)


def full_with_queue(manager, places=1, waiting=1):
    outing = an_open_outing(manager, max_places=places)
    taken = [enrol(outing) for _ in range(places)]
    queue = [enrol(outing) for _ in range(waiting)]
    return outing, taken, queue


def fresh(*rows):
    for row in rows:
        row.refresh_from_db()
    return rows


# --- CA-M02-09: termini de pagament ----------------------------------------------------------


def test_ca_m02_09_unpaid_in_time_expires_cancels_the_charge_and_offers_the_place(manager):
    outing, (unpaid,), (first,) = full_with_queue(manager)

    assert deadlines.run_deadlines(now=NOW) == {
        "expired_unpaid": 0,
        "expired_offers": 0,
        "offered": 0,
    }
    done = deadlines.run_deadlines(now=LATER)

    unpaid, first = fresh(unpaid, first)
    assert done == {"expired_unpaid": 1, "expired_offers": 0, "offered": 1}
    assert (unpaid.status, unpaid.payment_due_at) == (S.EXPIRED, None)
    assert unpaid.charge.status == Charge.Status.CANCELLED
    assert unpaid.charge.cancel_reason == deadlines.UNPAID_REASON
    entry = AuditEntry.objects.get(action="charges.status_changed", target_id=str(unpaid.charge_id))
    assert (entry.new_value, entry.actor_kind) == ("cancelled", "system")
    assert (first.status, first.waitlist_position) == (S.OFFERED, None)
    assert first.offer_expires_at == LATER + datetime.timedelta(hours=48)
    assert enrolment.occupied(outing) == 1
    assert deadlines.run_deadlines(now=LATER) == {
        "expired_unpaid": 0,
        "expired_offers": 0,
        "offered": 0,
    }


def test_a_paid_charge_does_not_expire(manager):
    """L-M02-01: si el càrrec ja és pagat, la confirma el subscriptor de `charge.paid`."""
    outing, (paid,), _ = full_with_queue(manager)
    Charge.objects.filter(pk=paid.charge_id).update(status=Charge.Status.PAID)

    assert deadlines.run_deadlines(now=LATER)["expired_unpaid"] == 0
    (paid,) = fresh(paid)
    assert paid.status == S.PENDING_PAYMENT


def test_rn_m02_08_a_card_payment_in_progress_extends_the_deadline_but_a_transfer_does_not(manager):
    outing = an_open_outing(manager, max_places=3)
    card_payer, transfer_payer = a_member("Targeta"), a_member("Transferència")
    by_card, by_transfer = enrol(outing, card_payer), enrol(outing, transfer_payer)
    checkout.start_payment(by_card.charge, PaymentAttempt.Method.CARD, card_payer)
    checkout.start_payment(by_transfer.charge, PaymentAttempt.Method.TRANSFER, transfer_payer)

    deadlines.run_deadlines(now=LATER)

    by_card, by_transfer = fresh(by_card, by_transfer)
    assert by_card.status == S.PENDING_PAYMENT
    assert by_transfer.status == S.EXPIRED


# --- Ofertes (RN-M02-09; CA-M02-27) ------------------------------------------------------------


def test_ca_m02_27_the_offer_lasts_the_setting_hours_or_until_the_deadline(manager):
    setting = Setting.objects.get(key=deadlines.OFFER_HOURS_KEY)
    SettingVersion.objects.create(setting=setting, value=24, changed_by=manager, note="Prova.")
    outing = an_open_outing(manager)

    assert deadlines.offer_deadline(outing, NOW) == NOW + datetime.timedelta(hours=24)
    late = CLOSES - datetime.timedelta(hours=3)
    assert deadlines.offer_deadline(outing, late) == CLOSES
    for wrong in (11, 169):
        with pytest.raises(ValidationError):
            business_settings.validate_value(setting, wrong)


def test_accepting_an_offer_creates_the_charge_and_the_payment_deadline(manager):
    outing = an_open_outing(manager, max_places=1)
    enrol(outing)
    account = a_member("Espera")
    first = enrol(outing, account)
    deadlines.run_deadlines(now=LATER)
    (first,) = fresh(first)

    accepted = deadlines.accept_offer(first, actor=account, now=LATER)

    assert (accepted.status, accepted.offer_expires_at) == (S.PENDING_PAYMENT, None)
    assert accepted.charge.amount_cents == 4500 and accepted.charge.status == Charge.Status.PENDING
    assert accepted.payment_due_at == LATER + datetime.timedelta(hours=72)
    change = AuditEntry.objects.filter(action=enrolment.STATUS_CHANGED, target_id=str(first.pk))
    assert list(change.values_list("old_value", "new_value")) == [
        ("waitlisted", "offered"),
        ("offered", "pending_payment"),
    ]


def test_declining_or_letting_the_offer_expire_passes_the_place_on(manager):
    outing, _, (first, second, third) = full_with_queue(manager, waiting=3)
    deadlines.run_deadlines(now=LATER)
    first, second = fresh(first, second)
    assert (first.status, second.waitlist_position) == (S.OFFERED, 1)

    deadlines.decline_offer(first, actor=manager, now=LATER)  # AC5 també respon
    first, second, third = fresh(first, second, third)
    assert (first.status, second.status, third.waitlist_position) == (S.EXPIRED, S.OFFERED, 1)

    deadlines.run_deadlines(now=second.offer_expires_at)
    second, third = fresh(second, third)
    assert (second.status, third.status) == (S.EXPIRED, S.OFFERED)


def test_only_the_person_or_ac5_answers_an_offer_and_not_after_the_deadline(make_admin, manager):  # noqa: F811
    outing, _, (first,) = full_with_queue(manager)
    deadlines.run_deadlines(now=LATER)
    (first,) = fresh(first)
    for stranger in (a_member("Una altra"), make_admin("secretary")):
        with pytest.raises(Http404):
            deadlines.accept_offer(first, actor=stranger, now=LATER)
    with pytest.raises(ValidationError):
        deadlines.accept_offer(first, actor=manager, now=first.offer_expires_at)
    (first,) = fresh(first)
    assert first.status == S.OFFERED


def test_with_registration_closed_no_place_is_offered(manager):
    outing, _, (first,) = full_with_queue(manager)
    states.close_registration(outing, by=manager, now=NOW)

    assert deadlines.run_deadlines(now=LATER) == {
        "expired_unpaid": 1,
        "expired_offers": 0,
        "offered": 0,
    }
    (first,) = fresh(first)
    assert (first.status, first.waitlist_position) == (S.WAITLISTED, 1)


def test_rn_m02_03_only_the_listed_transitions_exist(manager):
    assert {(str(a), str(b)) for a, b in enrolment.TRANSITIONS} == {
        ("pending_payment", "confirmed"),
        ("pending_payment", "expired"),
        ("pending_payment", "cancelled"),
        ("waitlisted", "offered"),
        ("waitlisted", "cancelled"),
        ("waitlisted", "expired"),
        ("offered", "pending_payment"),
        ("offered", "confirmed"),  # només una activitat gratuïta (L-M02-06)
        ("offered", "expired"),
        ("confirmed", "cancelled"),
    }
    row = enrol(an_open_outing(manager))
    Enrolment.objects.filter(pk=row.pk).update(status=S.CONFIRMED)
    (row,) = fresh(row)
    with pytest.raises(ValidationError):  # una confirmada no torna a pendent de pagament
        enrolment.change_status(row, S.PENDING_PAYMENT, actor=manager)


def test_the_queue_task_calls_the_service(monkeypatch):
    seen = []
    monkeypatch.setattr(deadlines, "run_deadlines", lambda: seen.append(True) or {})
    tasks.run_deadlines(timestamp=0)
    assert seen == [True]
