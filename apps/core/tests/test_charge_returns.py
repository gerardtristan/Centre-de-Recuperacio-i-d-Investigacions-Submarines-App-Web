"""Càrrec retornat al nucli: «pagat → retornat» i «retornat → pendent» (T-M05b-01; RN-67,
RN-M05b-14 i decisió 048; la part de la 00 de CA-M05b-18). Només dades inventades."""

from unittest import mock

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.http import Http404
from django.test.utils import CaptureQueriesContext

from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, Payment, PaymentCancellation, Role

pytestmark = pytest.mark.django_db
R = Role.Code
S = Charge.Status
DD = Payment.Method.DIRECT_DEBIT
SYSTEM = audit.system("payments.returns")
AM04 = "AM04: fons insuficients (prova)"


@pytest.fixture
def admin(make_admin):
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def treasurer(make_admin):
    return make_admin(R.TREASURER)


@pytest.fixture
def person(make_person):
    return make_person("Núria", "Coll")


def paid_fee(person, admin, method=DD):
    charge = charges.create_charge(
        person, kind="fee", amount_cents=9000, concept="Quota 2027", origin="members", by=admin
    )
    origin = "reconciliation" if method in (DD, Payment.Method.TRANSFER) else "provider"
    payment = charges.record_payment(charge, method=method, origin=origin, by=SYSTEM)
    return charge, payment


def returned_fee(person, admin, treasurer):
    charge, payment = paid_fee(person, admin)
    charges.mark_returned(charge, AM04, by=treasurer)
    return charge, payment


def status_rows():
    return AuditEntry.objects.filter(action="charges.status_changed").order_by("pk")


class TestMarkReturned:
    def test_ca_m05b_18_paid_to_returned_with_the_payment_cancelled(self, admin, treasurer, person):
        charge, payment = paid_fee(person, admin)
        done = charges.mark_returned(charge, f" {AM04} ", by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.RETURNED
        assert (done.payment, done.reason, done.cancelled_by) == (payment, AM04, treasurer)
        assert Payment.objects.filter(pk=payment.pk).exists()  # res no s'esborra
        assert charges.active_payments(charge) == []
        row = status_rows().last()
        assert (row.old_value, row.new_value, row.actor_account) == ("paid", "returned", treasurer)
        assert (row.reason.strip(), row.details) == (AM04, {"payment": payment.pk})
        cancelled = AuditEntry.objects.get(action=charges.PAYMENT_CANCELLED)
        assert cancelled.target_id == str(payment.pk)
        assert cancelled.details == {"charge": charge.pk, "origin": "RN-M05b-14"}

    def test_a_reason_is_required(self, admin, treasurer, person):
        charge, _payment = paid_fee(person, admin)
        with pytest.raises(ValidationError, match="motiu"):
            charges.mark_returned(charge, "  ", by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.PAID and not PaymentCancellation.objects.exists()

    @pytest.mark.parametrize("status", [S.PENDING, S.RETURNED, S.CANCELLED])
    def test_only_a_paid_charge(self, admin, treasurer, person, status):
        charge, _payment = paid_fee(person, admin)
        Charge.objects.filter(pk=charge.pk).update(status=status, cancel_reason="prova")
        with pytest.raises(ValidationError, match="pagat"):
            charges.mark_returned(charge, AM04, by=treasurer)
        assert not PaymentCancellation.objects.exists()

    @pytest.mark.parametrize(
        "method", [Payment.Method.CARD, Payment.Method.BIZUM, Payment.Method.TRANSFER]
    )
    def test_only_a_direct_debit(self, admin, treasurer, person, method):
        charge, _payment = paid_fee(person, admin, method=method)
        with pytest.raises(ValidationError, match="devolució"):
            charges.mark_returned(charge, AM04, by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.PAID and not PaymentCancellation.objects.exists()

    def test_only_the_treasurer(self, admin, treasurer, make_admin, person):
        charge, _payment = paid_fee(person, admin)
        for who in (admin, make_admin(R.SECRETARY), SYSTEM):
            with pytest.raises(Http404):
                charges.mark_returned(charge, AM04, by=who)
        charge.refresh_from_db()
        assert charge.status == S.PAID and not PaymentCancellation.objects.exists()

    def test_all_or_nothing(self, admin, treasurer, person):
        charge, _payment = paid_fee(person, admin)
        with (
            mock.patch.object(charges, "_transition", side_effect=RuntimeError("prova")),
            pytest.raises(RuntimeError),
        ):
            charges.mark_returned(charge, AM04, by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.PAID
        assert not PaymentCancellation.objects.exists()
        assert not AuditEntry.objects.filter(action=charges.PAYMENT_CANCELLED).exists()

    def test_the_charge_is_locked(self, admin, treasurer, person):
        charge, _payment = paid_fee(person, admin)
        with CaptureQueriesContext(connection) as queries:
            charges.mark_returned(charge, AM04, by=treasurer)
        first_read = next(q["sql"] for q in queries if 'FROM "core_charge"' in q["sql"])
        assert "FOR UPDATE" in first_read


class TestReopenReturned:
    def test_ca_m05b_18_returned_to_pending_with_a_reason(self, admin, treasurer, person):
        charge, _payment = returned_fee(person, admin, treasurer)
        charges.reopen_returned(charge, " Reintent a la remesa següent (prova) ", by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.PENDING
        row = status_rows().last()
        assert (row.old_value, row.new_value, row.actor_account) == (
            "returned",
            "pending",
            treasurer,
        )
        assert row.reason.strip() == "Reintent a la remesa següent (prova)"
        assert row.details == {"origin": "048"}

    def test_the_process_confirmed_by_the_treasurer_can_reopen(self, admin, treasurer, person):
        charge, _payment = returned_fee(person, admin, treasurer)
        charges.reopen_returned(charge, "Reintent confirmat (prova)", by=SYSTEM)
        charge.refresh_from_db()
        assert charge.status == S.PENDING
        row = status_rows().last()
        assert (row.actor_kind, row.actor_origin) == ("system", "payments.returns")

    def test_then_paid_again_only_the_new_payment_counts(self, admin, treasurer, person):
        charge, _old = returned_fee(person, admin, treasurer)
        charges.reopen_returned(charge, "Alternativa de pagament (prova)", by=treasurer)
        new = charges.record_payment(
            charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM
        )
        charge.refresh_from_db()
        assert charge.status == S.PAID
        assert charges.active_payments(charge) == [new]
        assert [r.new_value for r in status_rows()] == ["paid", "returned", "pending", "paid"]

    def test_a_reason_is_required(self, admin, treasurer, person):
        charge, _payment = returned_fee(person, admin, treasurer)
        with pytest.raises(ValidationError, match="motiu"):
            charges.reopen_returned(charge, " ", by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.RETURNED

    @pytest.mark.parametrize("status", [S.PENDING, S.PAID, S.CANCELLED])
    def test_only_a_returned_charge(self, admin, treasurer, person, status):
        charge, _payment = paid_fee(person, admin)
        Charge.objects.filter(pk=charge.pk).update(status=status, cancel_reason="prova")
        before = status_rows().count()
        with pytest.raises(ValidationError):
            charges.reopen_returned(charge, "Prova", by=treasurer)
        charge.refresh_from_db()
        assert charge.status == status and status_rows().count() == before

    def test_nobody_else(self, admin, treasurer, make_admin, person):
        charge, _payment = returned_fee(person, admin, treasurer)
        for who in (admin, make_admin(R.SECRETARY), audit.ANONYMOUS):
            with pytest.raises(Http404):
                charges.reopen_returned(charge, "Prova", by=who)
        charge.refresh_from_db()
        assert charge.status == S.RETURNED

    def test_the_rn_67_table_still_has_no_way_out_of_returned(self):
        assert not any(start == S.RETURNED for start, _new in charges.TRANSITIONS)
        assert charges.REOPEN_RETURNED == (S.RETURNED, S.PENDING)
