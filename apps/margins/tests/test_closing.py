"""T-M09-12: tancament econòmic i marge congelat (P-M09-D pas 5; RN-M09-07 i 12; CA-M09-10 i
11; MG7), amb el marge real de la T-M09-11 (ingressos, devolucions i comissions de la 04). Només
dades inventades."""

import pytest
from django.http import Http404

from apps.activities.models import Activity, Enrolment
from apps.activities.states import InvalidTransition
from apps.activities.tests.helpers import an_outing
from apps.activities.tests.test_attendance import enrolled, opened
from apps.core import audit
from apps.core.models import AppendOnlyError, AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import allocation, services
from apps.expenses.models import Expense, ExpenseAllocation, Supplier
from apps.expenses.tests.test_expenses import data, invoice
from apps.margins import calc, closing
from apps.margins import services as margins
from apps.treasury import services as treasury
from apps.treasury.tests.test_record_income import paid

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-t-m09-12")
A = Activity.Status


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def paid_enrolment(activity, amount=6000, fee=30):
    """Una inscripció confirmada amb el cobrament a la 04: ingrés i comissió."""
    row = enrolled(activity, "Pagada")
    payment = paid(row.person, kind="enrolment", amount=amount, department=activity.department)
    Enrolment.objects.filter(pk=row.pk).update(charge=payment.charge)
    treasury.record_income(payment, origin="provider", by=SYSTEM)
    treasury.record_fee(payment, fee, by=SYSTEM)
    return payment


def boat_invoice(treasurer, amount, *, with_invoice=True):
    supplier = Supplier.objects.create(name=f"Nàutica Inventada {amount}")
    expense = services.record_expense(by=treasurer, **data(supplier, amount_cents=amount))
    if with_invoice:  # adjuntar el fitxer és de la T-M09-25: aquí, directe a la fila
        Expense.objects.filter(pk=expense.pk).update(invoice_file=invoice(treasurer.person))
    return expense


@pytest.fixture
def done(manager):
    return opened(an_outing(manager), A.DONE)


def test_the_real_margin_uses_the_04_and_the_allocations(done, treasurer):
    for _ in range(2):
        paid_enrolment(done)
    allocation.allocate(boat_invoice(treasurer, 5000), [done], "equal", by=treasurer)
    margin = margins.activity_margin(done, calc.REAL)
    assert (margin.income_enrolments_cents, margin.direct_costs_cents) == (12000, 5000 + 60)
    assert (margin.margin_cents, margin.margin_pct_tenths, margin.per_participant_cents) == (
        6940, 578, 3470,
    )  # fmt: skip


def test_ca_m09_10_pending_enrolments_or_missing_invoices_block_closing(done, treasurer):
    enrolled(done, "Pendent", Enrolment.Status.PENDING_PAYMENT)
    allocation.allocate(
        boat_invoice(treasurer, 5000, with_invoice=False), [done], "equal", by=treasurer
    )
    with pytest.raises(closing.ClosingBlocked) as error:
        closing.close_activity(done, by=treasurer)
    assert error.value.reasons == [
        "Hi ha 1 inscripció pendent de pagament.",
        "Hi ha 1 despesa repartida a l'activitat sense factura.",
    ]
    done.refresh_from_db()
    assert done.status == A.DONE and closing.current(done) is None


def test_ca_m09_11_a_later_refund_does_not_change_the_frozen_margin(done, treasurer):
    payment = paid_enrolment(done)
    snapshot = closing.close_activity(done, by=treasurer)
    done.refresh_from_db()
    assert done.status == A.CLOSED
    assert (snapshot.margin_cents, snapshot.participants, snapshot.closed_by) == (
        6000 - 30, 1, treasurer,
    )  # fmt: skip
    assert AuditEntry.objects.filter(action=closing.ACTIVITY_CLOSED).count() == 1

    treasury.record_refund(payment, 6000, reason="Devolució tardana inventada.", by=SYSTEM)
    late = boat_invoice(treasurer, 700)
    allocation.allocate(late, [done], "equal", by=treasurer)  # factura tardana (L-M09-02)
    snapshot.refresh_from_db()
    assert closing.current(done).margin_cents == 5970  # congelat
    adjustments = closing.later_adjustments(snapshot)
    assert (adjustments.enrolments_cents, adjustments.costs_cents) == (-6000, 700)
    assert adjustments.margin_effect_cents == -6700
    with pytest.raises(AppendOnlyError):
        snapshot.save()
    # El que ja és dins el marge congelat no es torna a repartir.
    with pytest.raises(services.ExpenseRejected):
        allocation.allocate(late, None, "manual", by=treasurer, amounts={done: 600})
    assert ExpenseAllocation.objects.get(expense=late).amount_cents == 700


def test_mg7_only_the_treasurer_and_the_administrator(done, manager):
    with pytest.raises(Http404):
        closing.close_activity(done, by=manager)


def test_only_a_done_activity_is_closed(manager, treasurer):
    with pytest.raises(InvalidTransition):
        closing.close_activity(opened(an_outing(manager), A.OPEN), by=treasurer)
    assert closing.current(an_outing(manager)) is None
