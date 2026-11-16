"""Corregir una transferència conciliada amb el càrrec equivocat, al nucli (decisió 045;
T-M04-12c; CA-T10.5 i CA-T10.6). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, transaction
from django.http import Http404

from apps.core import audit, charges
from apps.core.models import (
    AppendOnlyError,
    AuditEntry,
    Charge,
    Payment,
    PaymentCancellation,
    Role,
)

pytestmark = pytest.mark.django_db
R = Role.Code
S = Charge.Status
SYSTEM = audit.system("provider-webhook")


@pytest.fixture
def admin(make_admin):
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def treasurer(make_admin):
    return make_admin(R.TREASURER)


@pytest.fixture
def person(make_person):
    return make_person("Núria", "Coll")


@pytest.fixture
def courses(admin):
    return charges.create_department("Cursos", by=admin)


def new_charge(person, by, kind="enrolment", amount_cents=12000, department=None):
    return charges.create_charge(
        person,
        kind=kind,
        amount_cents=amount_cents,
        concept="Curs Open Water",
        origin="activities",
        department=department,
        by=by,
    )


class TestRevertPaidTransfer:
    """045 (T-M04-12c; CA-T10.5, CA-T10.6): «pagat → pendent» només per a una transferència
    conciliada, amb motiu, i el pagament anul·lat. La 04 hi afegeix el contramoviment."""

    def paid(self, person, admin, treasurer, courses, method=Payment.Method.TRANSFER):
        charge = new_charge(person, admin, department=courses)
        origin = "reconciliation" if method == Payment.Method.TRANSFER else "provider"
        by = treasurer if origin == "reconciliation" else SYSTEM
        payment = charges.record_payment(charge, method=method, origin=origin, by=by)
        return charge, payment

    def test_ca_t10_5_back_to_pending_with_the_payment_cancelled(
        self, admin, treasurer, person, courses
    ):
        charge, payment = self.paid(person, admin, treasurer, courses)
        done = charges.revert_paid_transfer(charge, " Càrrec equivocat (prova) ", by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.PENDING
        assert (done.payment, done.reason, done.cancelled_by) == (
            payment,
            "Càrrec equivocat (prova)",
            treasurer,
        )
        assert Payment.objects.filter(pk=payment.pk).exists()  # res no s'esborra
        row = AuditEntry.objects.filter(action="charges.status_changed").last()
        assert (row.old_value, row.new_value, row.actor_account) == ("paid", "pending", treasurer)
        assert row.reason.strip() == "Càrrec equivocat (prova)"
        assert row.details == {"origin": "045", "payment": payment.pk}
        cancelled = AuditEntry.objects.get(action=charges.PAYMENT_CANCELLED)
        assert (cancelled.target_id, cancelled.actor_account) == (str(payment.pk), treasurer)

    def test_the_charge_can_then_be_paid_again(self, admin, treasurer, person, courses):
        charge, _payment = self.paid(person, admin, treasurer, courses)
        charges.revert_paid_transfer(charge, "Càrrec equivocat (prova)", by=treasurer)
        charges.record_payment(charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
        charge.refresh_from_db()
        assert charge.status == S.PAID
        # Només compta el pagament que no està anul·lat: ara, la targeta.
        assert [p.method for p in charges.active_payments(charge)] == ["card"]
        with pytest.raises(ValidationError, match="devolució"):
            charges.revert_paid_transfer(charge, "Un altre error (prova)", by=treasurer)

    def test_the_charge_can_then_be_paid_again_by_transfer(self, admin, treasurer, person, courses):
        # T-M05b-29: el 05b cancel·la l'intent pagat i anul·la el rebut (payments/transfers.py).
        charge, _payment = self.paid(person, admin, treasurer, courses)
        charges.revert_paid_transfer(charge, "Càrrec equivocat (prova)", by=treasurer)
        charges.record_payment(
            charge, method=Payment.Method.TRANSFER, origin="reconciliation", by=treasurer
        )
        charge.refresh_from_db()
        assert charge.status == S.PAID

    @pytest.mark.parametrize(
        "method", [Payment.Method.CARD, Payment.Method.BIZUM, Payment.Method.DIRECT_DEBIT]
    )
    def test_ca_t10_6_other_methods_are_rejected(self, admin, treasurer, person, courses, method):
        charge = new_charge(person, admin, kind="fee", amount_cents=9000)
        charges.record_payment(charge, method=method, origin="provider", by=SYSTEM)
        with pytest.raises(ValidationError, match="devolució"):
            charges.revert_paid_transfer(charge, "Prova", by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.PAID
        assert not PaymentCancellation.objects.exists()

    @pytest.mark.parametrize("status", [S.PENDING, S.RETURNED, S.CANCELLED])
    def test_only_a_paid_charge(self, admin, treasurer, person, courses, status):
        charge, _payment = self.paid(person, admin, treasurer, courses)
        Charge.objects.filter(pk=charge.pk).update(status=status, cancel_reason="prova")
        with pytest.raises(ValidationError):
            charges.revert_paid_transfer(charge, "Prova", by=treasurer)
        assert not PaymentCancellation.objects.exists()

    def test_a_reason_is_required(self, admin, treasurer, person, courses):
        charge, _payment = self.paid(person, admin, treasurer, courses)
        with pytest.raises(ValidationError, match="motiu"):
            charges.revert_paid_transfer(charge, "  ", by=treasurer)
        charge.refresh_from_db()
        assert charge.status == S.PAID

    def test_only_with_t4(self, admin, treasurer, make_admin, person, courses):
        charge, _payment = self.paid(person, admin, treasurer, courses)
        for who in (admin, make_admin(R.SECRETARY), SYSTEM):
            with pytest.raises(Http404):
                charges.revert_paid_transfer(charge, "Prova", by=who)
        charge.refresh_from_db()
        assert charge.status == S.PAID and not PaymentCancellation.objects.exists()

    def test_cancellations_are_append_only_also_in_sql(self, admin, treasurer, person, courses):
        charge, _payment = self.paid(person, admin, treasurer, courses)
        done = charges.revert_paid_transfer(charge, "Prova", by=treasurer)
        with pytest.raises(AppendOnlyError):
            done.save()
        for sql in (
            "UPDATE core_paymentcancellation SET reason = 'x'",
            "DELETE FROM core_paymentcancellation",
            "TRUNCATE core_paymentcancellation",
        ):
            with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
                cur.execute(sql)
