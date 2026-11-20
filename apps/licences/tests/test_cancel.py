"""Cancel·lar una llicència i proposta de devolució (T-M06-12; CA-M06-13; RN-M06-09; LC6, LC7)."""

import pytest
from django.http import Http404

from apps.core import audit, charges, events
from apps.core.models import AuditEntry, Charge, Event, Payment, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import services
from apps.licences.models import Licence, LicenceRefundProposal
from apps.licences.services import (
    AlreadyDecided,
    CannotCancel,
    MissingReason,
    cancel,
    decide_refund,
)
from apps.licences.tests.test_request import ask, options, priced, soci  # noqa: F401 (fixtures)
from apps.payments.models import RefundRequest
from apps.treasury import services as treasury

R = Role.Code
SYSTEM = audit.system("proves-t-m06-12")
P = LicenceRefundProposal.Status


@pytest.fixture
def requested(options, soci, annual, priced):  # noqa: F811
    return ask(soci, annual)


@pytest.fixture
def paid(requested):
    """Pagada amb targeta (proveïdor fals), amb l'ingrés a la 04 i `charge.paid` lliurat."""
    payment = charges.record_payment(
        requested.charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM
    )
    treasury.record_income(payment, origin="provider", by=SYSTEM)
    events.deliver(Event.objects.get(payload__charge=requested.charge_id).pk)
    requested.refresh_from_db()
    assert requested.status == Licence.Status.PAID
    return requested


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin(R.SECRETARY)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


def test_a_requested_licence_cancels_its_pending_charge(requested, secretary):
    cancel(requested, "Duplicada", actor=secretary)
    requested.refresh_from_db()
    assert (requested.status, requested.cancellation_reason) == ("cancelled", "Duplicada")
    assert requested.charge.status == Charge.Status.CANCELLED
    assert not LicenceRefundProposal.objects.exists()
    entry = AuditEntry.objects.get(action=services.ACTION_CANCELLED)
    assert (entry.old_value, entry.new_value, entry.reason) == (
        "requested",
        "cancelled",
        "Duplicada",
    )


def test_ca_m06_13_a_paid_licence_gets_a_proposal_and_no_automatic_refund(paid, secretary):
    cancel(paid, "Es dona de baixa", actor=secretary)
    proposal = LicenceRefundProposal.objects.get(licence=paid)
    assert (proposal.status, proposal.amount_cents, proposal.reason) == (
        "proposed", 9000, "Es dona de baixa",
    )  # fmt: skip
    paid.charge.refresh_from_db()
    assert paid.charge.status == Charge.Status.PAID
    assert not RefundRequest.objects.exists()


def test_a_filed_licence_can_be_cancelled_too(paid, secretary):
    Licence.objects.filter(pk=paid.pk).update(status="filed")
    cancel(paid, "La federació no la tramita", actor=secretary)
    assert LicenceRefundProposal.objects.filter(licence=paid).exists()


def test_an_active_licence_is_left_to_expire(requested, secretary):
    Licence.objects.filter(pk=requested.pk).update(status="active")
    with pytest.raises(CannotCancel):
        cancel(requested, "Motiu", actor=secretary)


def test_a_reason_is_required(requested, secretary):
    with pytest.raises(MissingReason):
        cancel(requested, "  ", actor=secretary)


@pytest.mark.parametrize("role", [R.TREASURER, R.COURSES_MANAGER, R.INSTRUCTOR, None])
def test_only_lc6_cancels(requested, soci, make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        cancel(requested, "Motiu", actor=make_admin(*([role] if role else [])))
    with pytest.raises(Http404):
        cancel(requested, "Motiu", actor=soci)  # ni el titular


def test_the_treasurer_refunds_through_the_05b_once(paid, secretary, treasurer):
    cancel(paid, "Es dona de baixa", actor=secretary)
    proposal = paid.refund_proposal
    done = decide_refund(proposal, approve=True, note="Devolució total", actor=treasurer)
    assert (done.status, done.decided_by, done.decision_note) == (
        "done",
        treasurer,
        "Devolució total",
    )
    (refund,) = RefundRequest.objects.all()
    assert (refund.key, refund.amount_cents, refund.status) == (proposal.refund_key, 9000, "done")
    paid.charge.refresh_from_db()
    assert paid.charge.status == Charge.Status.CANCELLED  # devolució total (RN-M05b-17)
    with pytest.raises(AlreadyDecided):
        decide_refund(done, approve=True, note="Una altra vegada", actor=treasurer)
    assert RefundRequest.objects.count() == 1


def test_the_treasurer_can_reject_it_with_a_note(paid, secretary, treasurer):
    cancel(paid, "Es dona de baixa", actor=secretary)
    with pytest.raises(MissingReason):
        decide_refund(paid.refund_proposal, approve=False, note="", actor=treasurer)
    rejected = decide_refund(
        paid.refund_proposal, approve=False, note="Ja s'ha tramitat", actor=treasurer
    )
    assert rejected.status == P.REJECTED
    assert not RefundRequest.objects.exists()
    entry = AuditEntry.objects.get(action=services.ACTION_REFUND_DECIDED)
    assert (entry.new_value, entry.reason) == ("rejected", "Ja s'ha tramitat")


def test_a_decision_taken_meanwhile_is_kept(paid, secretary, treasurer):
    cancel(paid, "Es dona de baixa", actor=secretary)
    stale = paid.refund_proposal
    LicenceRefundProposal.objects.filter(pk=stale.pk).update(
        status="rejected", decided_by=treasurer
    )
    assert decide_refund(stale, approve=False, note="Tard", actor=treasurer).status == "rejected"
    assert not AuditEntry.objects.filter(action=services.ACTION_REFUND_DECIDED).exists()


@pytest.mark.parametrize("role", [R.SECRETARY, R.ADMINISTRATOR, None])
def test_only_lc7_decides(paid, secretary, make_admin, role):  # noqa: F811
    cancel(paid, "Es dona de baixa", actor=secretary)
    with pytest.raises(Http404):
        decide_refund(paid.refund_proposal, approve=True, note="Nota",
                      actor=make_admin(*([role] if role else [])))  # fmt: skip


def test_str(paid, secretary):
    cancel(paid, "Es dona de baixa", actor=secretary)
    assert str(paid.refund_proposal).endswith("· Proposada")


def test_a_charge_already_cancelled_elsewhere_is_left_alone(requested, secretary):
    charges.cancel(requested.charge, "Caducat sense pagar (L-M06-03)", by=SYSTEM)
    cancel(requested, "No l'ha pagada", actor=secretary)
    requested.refresh_from_db()
    assert requested.status == "cancelled"
    assert not LicenceRefundProposal.objects.exists()
