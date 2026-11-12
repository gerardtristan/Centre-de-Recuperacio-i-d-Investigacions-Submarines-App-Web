"""Terminis de pagament, ofertes de plaça i llista d'espera (T-M02-13; RN-M02-08 i RN-M02-09;
CA-M02-09 i CA-M02-27; AC16; decisió 088). Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import enrolment, extensions, services, states, tasks, waitlist
from apps.activities.models import Activity, Enrolment
from apps.core import audit
from apps.core.models import AuditEntry, Charge, GuestLink, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import (
    AFTER_DEADLINE,
    BEFORE_DEADLINE,
    CLOSES,
    REASON,
    a_member,
    a_personal_account,
    an_open_outing,
    at,
    pay,
)

pytestmark = pytest.mark.django_db

S = Enrolment.Status
ACCOUNT = Enrolment.Channel.ACCOUNT
NOW = BEFORE_DEADLINE  # 01/06/2027 9:00; la data límit és el 10/06/2027 a les 20:00
HOURS = datetime.timedelta(hours=1)
NOTHING = {"expired_unpaid": 0, "confirmed": 0, "expired_offers": 0, "offered": 0}


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


def enrol(activity, account=None, *, now=NOW):
    account = account or a_member()
    return enrolment.enrol(activity, account.person, channel=ACCOUNT, actor=account, now=now)


def full_with_waiting(manager, *, places=1, waiting=2, **fields):
    outing = an_open_outing(manager, max_places=places, **fields)
    inside = [enrol(outing) for _ in range(places)]
    queue = [enrol(outing) for _ in range(waiting)]
    return outing, inside, queue


def account_of(row):
    return row.person.accounts.get(kind="personal")


def reload(*rows):
    for row in rows:
        row.refresh_from_db()
    return rows


# --- CA-M02-09 i l'exemple numèric de RN-M02-07 --------------------------------------------------


def test_ca_m02_09_an_unpaid_enrolment_expires_and_the_first_waiting_gets_the_offer(manager):
    """12 places: 10 confirmades i 2 pendents → plena; la 13a espera (posició 1). Una pendent no
    paga en 72 hores → caduca, el càrrec s'anul·la i la posició 1 rep l'oferta, amb 48 hores."""
    outing = an_open_outing(manager, max_places=12)
    rows = [enrol(outing) for _ in range(12)]
    for row in rows[:10]:
        pay(row.charge)
        waitlist.activity_charges.on_charge_paid({"charge_id": row.charge_id})
    late = enrol(outing, now=NOW + HOURS)  # la 13a; el seu termini seria més tard
    assert (late.status, late.waitlist_position) == (S.WAITLISTED, 1)
    pay(rows[10].charge)
    waitlist.activity_charges.on_charge_paid({"charge_id": rows[10].charge_id})
    unpaid = rows[11]
    after = NOW + datetime.timedelta(hours=72)

    assert waitlist.run_deadlines(after - HOURS) == NOTHING
    done = waitlist.run_deadlines(after)

    assert done == {**NOTHING, "expired_unpaid": 1, "offered": 1}
    reload(unpaid, late)
    assert unpaid.status == S.EXPIRED and unpaid.payment_due_at is None
    assert unpaid.charge.status == Charge.Status.CANCELLED
    assert unpaid.charge.cancel_reason == waitlist.UNPAID_REASON
    assert late.status == S.OFFERED and late.waitlist_position is None
    assert late.offer_expires_at == after + datetime.timedelta(hours=48)
    assert late.charge is None  # el càrrec es crea quan l'accepta
    assert enrolment.occupied(outing) == 12  # una plaça oferta ocupa plaça
    expiry = AuditEntry.objects.get(
        action=enrolment.STATUS_CHANGED, target_id=str(unpaid.pk), new_value__contains="expired"
    )
    assert expiry.actor_kind == "system" and expiry.reason == waitlist.UNPAID_REASON
    # Idempotent: una segona passada no troba res a fer.
    assert waitlist.run_deadlines(after) == NOTHING


def test_a_paid_charge_the_module_did_not_know_about_is_confirmed_not_expired(manager):
    outing = an_open_outing(manager)
    row = enrol(outing)
    pay(row.charge)  # pagat, però l'esdeveniment encara no ha arribat

    done = waitlist.run_deadlines(row.payment_due_at + HOURS)

    row.refresh_from_db()
    assert done == {**NOTHING, "confirmed": 1}
    assert row.status == S.CONFIRMED and row.charge.status == Charge.Status.PAID


# --- Termini de l'oferta (RN-M02-09; CA-M02-27) --------------------------------------------------


def test_ca_m02_27_the_offer_term_follows_the_setting_and_never_passes_the_deadline(manager):
    outing, (inside,), (first, second) = full_with_waiting(manager)
    Setting.objects.create(
        key=services.OFFER_HOURS_KEY,
        module="activities",
        value_type=Setting.ValueType.INTEGER,
        initial_value=24,
        min_value=12,
        max_value=168,
    )
    assert waitlist.offer_hours() == 24
    assert waitlist.offer_deadline(outing, NOW) == NOW + datetime.timedelta(hours=24)
    near = CLOSES - datetime.timedelta(hours=5)
    assert waitlist.offer_deadline(outing, near) == CLOSES  # la data límit arriba abans

    waitlist.run_deadlines(inside.payment_due_at)

    first.refresh_from_db()
    assert first.offer_expires_at == inside.payment_due_at + datetime.timedelta(hours=24)


def test_without_the_setting_the_term_is_the_initial_48_hours(manager):
    assert waitlist.offer_hours() == 48


# --- Acceptar, rebutjar i deixar passar una oferta -----------------------------------------------


def offered(manager, **fields):
    outing, (inside,), queue = full_with_waiting(manager, **fields)
    when = (inside.payment_due_at or NOW) + HOURS
    if inside.status == S.CONFIRMED:  # gratuïta: s'allibera cancel·lant-la
        Enrolment.objects.filter(pk=inside.pk).update(status=S.CANCELLED, cancelled_reason=REASON)
    waitlist.run_deadlines(when)
    reload(*queue)
    return outing, queue, when


def test_accepting_an_offer_creates_the_charge_and_the_payment_term(manager):
    outing, (first, second), when = offered(manager)
    assert first.status == S.OFFERED and second.waitlist_position == 1

    row = waitlist.accept_offer(first, actor=account_of(first), now=when + HOURS)

    assert row.status == S.PENDING_PAYMENT and row.offer_expires_at is None
    assert row.charge.amount_cents == 4500 and row.charge.activity == outing
    assert row.payment_due_at == when + HOURS + datetime.timedelta(
        hours=outing.payment_window_hours
    )
    change = AuditEntry.objects.filter(
        action=enrolment.STATUS_CHANGED, target_id=str(row.pk)
    ).latest("id")
    assert "offered" in change.old_value and "pending_payment" in change.new_value
    assert change.actor_account == account_of(first)


def test_accepting_an_offer_of_a_free_activity_confirms_it(manager):
    outing, (first, _second), when = offered(
        manager, price_member_cents=0, price_non_member_cents=0
    )
    heard = []
    receiver = lambda sender, enrolment, **kw: heard.append(enrolment.pk)  # noqa: E731
    extensions.enrolment_confirmed.connect(receiver)
    try:
        row = waitlist.accept_offer(first, actor=account_of(first), now=when + HOURS)
    finally:
        extensions.enrolment_confirmed.disconnect(receiver)

    assert row.status == S.CONFIRMED and row.charge is None
    assert heard == [row.pk]


def test_an_offer_cannot_be_accepted_after_its_term_and_passes_to_the_next(manager):
    outing, (first, second), when = offered(manager)
    late = first.offer_expires_at + HOURS

    with pytest.raises(ValidationError, match="termini"):
        waitlist.accept_offer(first, actor=account_of(first), now=late)

    done = waitlist.run_deadlines(late)
    reload(first, second)
    assert done == {**NOTHING, "expired_offers": 1, "offered": 1}
    assert first.status == S.EXPIRED and first.offer_expires_at is None
    assert second.status == S.OFFERED
    assert not Charge.objects.filter(person=first.person).exists()


def test_declining_an_offer_passes_the_place_to_the_next(manager):
    outing, (first, second), when = offered(manager)

    row = waitlist.decline_offer(first, actor=account_of(first), now=when + HOURS)

    second.refresh_from_db()
    assert row.status == S.EXPIRED
    assert second.status == S.OFFERED
    assert second.offer_expires_at == when + HOURS + datetime.timedelta(hours=48)


def test_only_an_offered_enrolment_can_be_answered(manager):
    outing, _inside, (first, _second) = full_with_waiting(manager)
    with pytest.raises(ValidationError):
        waitlist.accept_offer(first, actor=account_of(first), now=NOW)
    with pytest.raises(ValidationError):
        waitlist.decline_offer(first, actor=account_of(first), now=NOW)


def test_who_can_answer_an_offer(make_admin, manager):  # noqa: F811
    """La mateixa persona (compte personal o enllaç de convidat) o qui inscriu presencialment
    (AC5). Ningú més."""
    outing, (first, second), when = offered(manager, places=1, waiting=2)
    stranger = a_member()
    moment = when + HOURS

    for actor in (stranger, make_admin("secretary"), make_admin("instructor"), None):
        with pytest.raises(Http404):
            waitlist.accept_offer(first, actor=actor, now=moment)
    guest_of_another = audit.guest(stranger.person, 1)
    with pytest.raises(Http404):
        waitlist.decline_offer(first, actor=guest_of_another, now=moment)
    first.refresh_from_db()
    assert first.status == S.OFFERED

    assert waitlist.accept_offer(first, actor=manager, now=moment).status == S.PENDING_PAYMENT


def test_a_guest_answers_the_own_offer_with_the_guest_actor(manager):
    outing, (first, _second), when = offered(manager)
    actor = audit.guest(first.person, 7)

    row = waitlist.accept_offer(first, actor=actor, now=when + HOURS)

    assert row.status == S.PENDING_PAYMENT
    assert not GuestLink.objects.exists()  # l'enllaç el crea la inscripció de convidat (T-M02-14)


# --- Amb les inscripcions tancades no s'ofereix res (088) ----------------------------------------


def test_after_the_deadline_a_freed_place_is_not_offered_until_registration_reopens(manager):
    outing, (inside,), (first, _second) = full_with_waiting(manager)
    states.advance_by_clock(now=AFTER_DEADLINE)

    done = waitlist.run_deadlines(AFTER_DEADLINE)

    reload(inside, first)
    assert done == {**NOTHING, "expired_unpaid": 1}
    assert inside.status == S.EXPIRED
    assert first.status == S.WAITLISTED and first.waitlist_position == 1

    reopened = at(2027, 6, 11, 10)
    states.reopen_registration(outing, by=manager, closes_at=at(2027, 6, 13, 20), now=reopened)
    assert waitlist.run_deadlines(reopened)["offered"] == 1
    first.refresh_from_db()
    assert first.status == S.OFFERED
    assert first.offer_expires_at == reopened + datetime.timedelta(hours=48)


def test_closing_by_hand_also_stops_the_offers(manager):
    outing, (inside,), (first, _second) = full_with_waiting(manager)
    states.close_registration(outing, by=manager, now=NOW)

    waitlist.run_deadlines(inside.payment_due_at + HOURS)

    first.refresh_from_db()
    assert first.status == S.WAITLISTED
    with pytest.raises(enrolment.ActivityNotOpen):
        waitlist.offer_to(first, by=manager, now=inside.payment_due_at + HOURS)


# --- A mà: ordre i oferta (AC16) -----------------------------------------------------------------


def test_the_manager_reorders_the_waiting_list_with_a_reason(manager):
    outing, _inside, queue = full_with_waiting(manager, waiting=4)
    a, b, c, d = queue

    with pytest.raises(ValidationError, match="motiu"):
        waitlist.move(d, 1, by=manager, reason="  ")
    with pytest.raises(ValidationError):
        waitlist.move(d, 5, by=manager, reason=REASON)
    with pytest.raises(ValidationError):
        waitlist.move(d, 0, by=manager, reason=REASON)

    waitlist.move(d, 2, by=manager, reason=REASON)

    assert list(enrolment.waitlist(outing)) == [a, d, b, c]
    assert [r.waitlist_position for r in enrolment.waitlist(outing)] == [1, 2, 3, 4]
    entry = AuditEntry.objects.get(action=waitlist.MOVED)
    assert (entry.old_value, entry.new_value, entry.reason) == (4, 2, REASON)
    assert entry.target_id == str(d.pk) and entry.actor_account == manager


def test_moving_someone_who_is_not_waiting_is_rejected(manager):
    outing, (inside,), _queue = full_with_waiting(manager)
    with pytest.raises(ValidationError):
        waitlist.move(inside, 1, by=manager, reason=REASON)


def test_the_manager_offers_a_free_place_by_hand(manager):
    outing, (inside,), (first, second) = full_with_waiting(manager)

    with pytest.raises(ValidationError, match="plaça lliure"):
        waitlist.offer_to(first, by=manager, now=NOW)

    Enrolment.objects.filter(pk=inside.pk).update(status=S.EXPIRED)
    with pytest.raises(ValidationError, match="motiu"):  # se salta l'ordre
        waitlist.offer_to(second, by=manager, now=NOW)
    row = waitlist.offer_to(second, by=manager, reason=REASON, now=NOW)

    first.refresh_from_db()
    assert row.status == S.OFFERED
    assert row.offer_expires_at == NOW + datetime.timedelta(hours=48)
    assert first.waitlist_position == 1
    change = AuditEntry.objects.filter(
        action=enrolment.STATUS_CHANGED, target_id=str(row.pk)
    ).latest("id")
    assert change.reason == REASON and change.actor_account == manager


@pytest.mark.parametrize(
    ("role", "allowed"),
    [
        ("courses_manager", True),
        ("treasurer", True),
        ("president", True),
        ("administrator", True),
        ("secretary", False),
        ("instructor", False),
        ("board", False),
        ("equipment_manager", False),
    ],
)
def test_ac16_only_some_roles_manage_the_waiting_list(
    make_admin,  # noqa: F811
    manager,
    role,
    allowed,
):
    outing, (inside,), (first, second) = full_with_waiting(manager)
    by = make_admin(role)

    if allowed:
        waitlist.move(second, 1, by=by, reason=REASON)
        assert list(enrolment.waitlist(outing)) == [second, first]
    else:
        with pytest.raises(Http404):
            waitlist.move(second, 1, by=by, reason=REASON)
        with pytest.raises(Http404):
            waitlist.offer_to(first, by=by, now=NOW)
        assert list(enrolment.waitlist(outing)) == [first, second]
    personal = a_personal_account()
    with pytest.raises(Http404):
        waitlist.move(first, 1, by=personal, reason=REASON)


# --- La tasca de la cua --------------------------------------------------------------------------


def test_the_deadlines_run_every_ten_minutes_on_the_queue():
    periodic = tasks.app.periodic_registry.periodic_tasks[("activities.enrolment_deadlines", "")]
    assert periodic.cron == "2-59/10 * * * *"
    tasks.enrolment_deadlines(timestamp=0)  # sense res a fer, no falla


def test_each_activity_is_handled_on_its_own(manager):
    one, (inside_one,), (wait_one, _x) = full_with_waiting(manager)
    two, (inside_two,), (wait_two, _y) = full_with_waiting(manager)
    Activity.objects.filter(pk=two.pk).update(status=Activity.Status.REGISTRATION_CLOSED)

    done = waitlist.run_deadlines(inside_one.payment_due_at + HOURS)

    reload(wait_one, wait_two)
    assert done == {**NOTHING, "expired_unpaid": 2, "offered": 1}
    assert wait_one.status == S.OFFERED and wait_two.status == S.WAITLISTED
