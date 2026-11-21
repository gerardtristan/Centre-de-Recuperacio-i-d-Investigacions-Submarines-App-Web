"""Cancel·lacions i propostes de devolució (T-M02-15; RN-M02-12 i RN-M02-13; CA-M02-14 i 15).
Només dades inventades; el pagament i la devolució passen pel 05b amb el proveïdor fictici.
"""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import cancellation, enrolment
from apps.activities.models import Activity, Enrolment, RefundProposal
from apps.core import events
from apps.core.models import AuditEntry, Charge, Event, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import checkout
from apps.payments.models import PaymentAttempt, RefundRequest
from apps.payments.providers import fake
from apps.payments.tests.test_processing import notify, run_queue

from .helpers import AFTER_DEADLINE, BEFORE_DEADLINE, a_member, an_open_outing

pytestmark = pytest.mark.django_db

S = Enrolment.Status
NOW = BEFORE_DEADLINE
REASON = "Motiu inventat de proves"


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


@pytest.fixture(autouse=True)
def provider():
    fake.reset()
    yield
    fake.reset()


def enrol(activity, account=None):
    account = account or a_member()
    row = enrolment.enrol(activity, account.person, channel="account", actor=account, now=NOW)
    return row, account


def pay(row, account):
    start = checkout.start_payment(row.charge, PaymentAttempt.Method.CARD, account)
    attempt = PaymentAttempt.objects.get(pk=start.attempt_id)
    notify(attempt, event_id=f"ev-{attempt.pk}")
    run_queue()
    for event in Event.objects.filter(name=events.CHARGE_PAID, payload__charge=row.charge_id):
        events.deliver(event.pk)
    row.refresh_from_db()
    assert row.status == S.CONFIRMED
    return row


def fresh(*rows):
    for row in rows:
        row.refresh_from_db()
    return rows


# --- CA-M02-14: el participant cancel·la ---------------------------------------------------------


def test_ca_m02_14_a_paid_enrolment_cancelled_leaves_a_proposal_and_no_refund(manager):
    outing = an_open_outing(manager)
    row, account = enrol(outing)
    pay(row, account)

    proposal = cancellation.cancel_enrolment(row, by=account, reason=REASON, now=NOW)

    (row,) = fresh(row)
    assert (row.status, row.cancelled_reason, row.cancelled_by) == (S.CANCELLED, REASON, account)
    assert (proposal.status, proposal.amount_cents, proposal.charge) == (
        "proposed",
        4500,
        row.charge,
    )
    assert proposal.proposed_by is None
    assert row.charge.status == Charge.Status.PAID  # cap devolució sense el tresorer
    assert not RefundRequest.objects.exists()


def test_the_treasurer_refunds_through_the_05b_once(manager, treasurer):
    outing = an_open_outing(manager)
    row, account = enrol(outing)
    pay(row, account)
    proposal = cancellation.cancel_enrolment(row, by=account, reason=REASON, now=NOW)

    done = cancellation.decide_refund(
        proposal, approve=True, note="Devolució inventada.", by=treasurer
    )
    again = cancellation.decide_refund
    with pytest.raises(ValidationError):
        again(done, approve=True, note="Una altra vegada.", by=treasurer)

    assert (done.status, done.decided_by) == ("done", treasurer)
    assert done.refund == RefundRequest.objects.get()
    assert done.refund.amount_cents == 4500
    entry = AuditEntry.objects.get(action=cancellation.REFUND_DECIDED)
    assert (entry.old_value, entry.new_value) == ("proposed", "done")


def test_the_treasurer_can_reject_with_a_note_and_only_ac18_decides(make_admin, manager, treasurer):  # noqa: F811
    outing = an_open_outing(manager)
    row, account = enrol(outing)
    pay(row, account)
    proposal = cancellation.cancel_enrolment(row, by=account, reason=REASON, now=NOW)

    for who in (manager, make_admin("secretary"), account):
        with pytest.raises(Http404):
            cancellation.decide_refund(proposal, approve=True, note="No.", by=who)
    with pytest.raises(ValidationError):
        cancellation.decide_refund(proposal, approve=False, note=" ", by=treasurer)
    rejected = cancellation.decide_refund(
        proposal, approve=False, note="Fora de termini.", by=treasurer
    )
    assert (rejected.status, rejected.refund) == ("rejected", None)


def test_a_pending_enrolment_cancelled_cancels_its_charge_and_offers_the_place(manager):
    outing = an_open_outing(manager, max_places=1)
    row, account = enrol(outing)
    waiting, _ = enrol(outing)

    assert cancellation.cancel_enrolment(row, by=account, reason=REASON, now=NOW) is None

    row, waiting = fresh(row, waiting)
    assert row.status == S.CANCELLED and row.charge.status == Charge.Status.CANCELLED
    assert waiting.status == S.OFFERED


def test_rn_m02_12_only_before_the_deadline_and_only_the_person_or_ac5(make_admin, manager):  # noqa: F811
    outing = an_open_outing(manager)
    row, account = enrol(outing)
    for stranger in (a_member("Una altra"), make_admin("secretary")):
        with pytest.raises(Http404):
            cancellation.cancel_enrolment(row, by=stranger, reason=REASON, now=NOW)
    with pytest.raises(ValidationError, match="data límit"):
        cancellation.cancel_enrolment(row, by=account, reason=REASON, now=AFTER_DEADLINE)
    with pytest.raises(ValidationError, match="motiu"):
        cancellation.cancel_enrolment(row, by=account, reason="", now=NOW)
    cancellation.cancel_enrolment(row, by=manager, reason=REASON, now=NOW)  # AC5 en nom seu
    (row,) = fresh(row)
    assert row.status == S.CANCELLED


def test_leaving_the_waiting_list_renumbers_it(manager):
    outing = an_open_outing(manager, max_places=1)
    enrol(outing)
    (first, first_account), (second, _) = enrol(outing), enrol(outing)

    cancellation.cancel_enrolment(first, by=first_account, reason=REASON, now=NOW)

    first, second = fresh(first, second)
    assert (first.status, first.waitlist_position) == (S.CANCELLED, None)
    assert second.waitlist_position == 1


def test_a_payment_in_progress_stops_the_cancellation(manager):
    """Conservador fins a la T-M02-36 (RN-M02-37): es torna a provar quan acaba el pagament."""
    outing = an_open_outing(manager)
    row, account = enrol(outing)
    checkout.start_payment(row.charge, PaymentAttempt.Method.CARD, account)
    with pytest.raises(cancellation.PaymentInProgress):
        cancellation.cancel_enrolment(row, by=account, reason=REASON, now=NOW)
    with pytest.raises(cancellation.PaymentInProgress):
        cancellation.cancel_activity(outing, by=manager, reason=REASON, now=NOW)
    (row,) = fresh(row)
    outing.refresh_from_db()
    assert (row.status, outing.status) == (S.PENDING_PAYMENT, Activity.Status.OPEN)


# --- CA-M02-15: el club cancel·la l'activitat ----------------------------------------------------


def test_ca_m02_15_cancelling_the_activity_proposes_100_percent_and_cancels_pending(manager):
    outing = an_open_outing(manager, max_places=3)
    paid = [pay(*enrol(outing)) for _ in range(2)]
    pending, _ = enrol(outing)
    waiting, _ = enrol(outing)

    proposals = cancellation.cancel_activity(outing, by=manager, reason="Mala mar.", now=NOW)

    outing.refresh_from_db()
    assert outing.status == Activity.Status.CANCELLED
    assert sorted(p.enrolment_id for p in proposals) == sorted(r.pk for r in paid)
    assert {p.amount_cents for p in proposals} == {4500}
    assert RefundProposal.objects.count() == 2
    pending, waiting = fresh(pending, waiting)
    assert pending.status == S.CANCELLED and pending.charge.status == Charge.Status.CANCELLED
    assert waiting.status == S.CANCELLED
    assert not Enrolment.objects.filter(activity=outing, status__in=Enrolment.LIVE).exists()


def test_cancelling_the_activity_needs_ac7_and_a_reason(make_admin, manager):  # noqa: F811
    outing = an_open_outing(manager)
    with pytest.raises(Http404):
        cancellation.cancel_activity(outing, by=make_admin("secretary"), reason=REASON, now=NOW)
    with pytest.raises(ValidationError):
        cancellation.cancel_activity(outing, by=manager, reason="", now=NOW)
