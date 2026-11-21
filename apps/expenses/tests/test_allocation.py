"""T-M09-07: repartiment d'una despesa entre activitats amb arrodoniment (P-M09-B; RN-M09-10;
CA-M09-04, 05 i 06; MG3). Només dades inventades."""

import datetime
import itertools

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.activities import attendance
from apps.activities.models import Activity, Enrolment
from apps.activities.tests.helpers import an_outing
from apps.activities.tests.test_attendance import DAY, enrolled, opened
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import allocation, services
from apps.expenses.models import ExpenseAllocation, Supplier
from apps.expenses.tests.test_expenses import data
from apps.margins import planned
from apps.margins import services as margins

pytestmark = pytest.mark.django_db
M = ExpenseAllocation.Method


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def expense(treasurer, amount):
    supplier = Supplier.objects.create(name="Nàutica Inventada SL")
    return services.record_expense(by=treasurer, **data(supplier, amount_cents=amount))


def outing(manager, people, *, starts=DAY, present=None):
    """Una sortida feta amb `people` inscripcions confirmades; amb `present`, llista passada."""
    activity = opened(an_outing(manager, starts_on=starts, ends_on=starts), Activity.Status.DONE)
    rows = [enrolled(activity, f"Persona {i}") for i in range(people)]
    for row in rows[: present or 0]:
        attendance.mark(row, present=True, by=manager, today=starts)
    return activity


def amounts(rows):
    return {row.activity_id: row.amount_cents for row in rows}


def test_ca_m09_04_by_attendees(treasurer, manager):
    # 12 i 20 inscrits, però hi van anar 10 i 15: compten els assistents.
    first, second = outing(manager, 12, present=10), outing(manager, 20, present=15)
    rows = allocation.allocate(
        expense(treasurer, 50000), [first, second], M.PARTICIPANTS, by=treasurer
    )
    assert amounts(rows) == {first.pk: 20000, second.pk: 30000}


def test_ca_m09_05_the_spare_cent_goes_to_the_oldest(treasurer, manager):
    later = DAY + datetime.timedelta(days=7)
    newer, oldest, middle = (
        outing(manager, 7, starts=later + datetime.timedelta(days=7)),
        outing(manager, 7),
        outing(manager, 7, starts=later),
    )
    rows = allocation.allocate(
        expense(treasurer, 10000), [newer, oldest, middle], M.PARTICIPANTS, by=treasurer
    )
    assert amounts(rows) == {oldest.pk: 3334, middle.pk: 3333, newer.pk: 3333}
    assert sum(amounts(rows).values()) == 10000


def test_equal_parts_give_the_spare_cents_to_the_biggest(treasurer, manager):
    small, big = outing(manager, 2), outing(manager, 9)
    rows = allocation.allocate(expense(treasurer, 1001), [small, big], M.EQUAL, by=treasurer)
    assert amounts(rows) == {small.pk: 500, big.pk: 501}


def test_ca_m09_06_more_than_the_amount_is_rejected(treasurer, manager):
    first, second = outing(manager, 1), outing(manager, 1)
    spent = expense(treasurer, 10000)
    with pytest.raises(allocation.AllocationExceedsAmount):
        allocation.allocate(
            spent, None, M.MANUAL, by=treasurer, amounts={first: 6000, second: 4001}
        )
    assert not ExpenseAllocation.objects.exists()
    # Menys de l'import sí: la resta queda al departament, sense activitat (P-M09-B pas 3).
    rows = allocation.allocate(spent, None, M.MANUAL, by=treasurer, amounts={first: 6000})
    assert amounts(rows) == {first.pk: 6000}


def test_reallocating_replaces_and_logs_the_previous_split(treasurer, manager):
    first, second = outing(manager, 1), outing(manager, 3)
    spent = expense(treasurer, 4000)
    allocation.allocate(spent, [first, second], M.PARTICIPANTS, by=treasurer)
    allocation.allocate(spent, None, M.MANUAL, by=treasurer, amounts={second: 4000})
    assert amounts(ExpenseAllocation.objects.all()) == {second.pk: 4000}
    entries = AuditEntry.objects.filter(action=allocation.ALLOCATED).order_by("id")
    assert [(e.old_value, e.new_value) for e in entries] == [
        (None, {str(first.pk): 1000, str(second.pk): 3000}),
        ({str(first.pk): 1000, str(second.pk): 3000}, {str(second.pk): 4000}),
    ]


def test_invalid_splits_are_rejected(treasurer, manager):
    empty, full = outing(manager, 0), outing(manager, 2)
    spent = expense(treasurer, 1000)
    for kwargs in (
        {"activities": [empty], "method": M.PARTICIPANTS},  # sense participants
        {"activities": [], "method": M.EQUAL},
        {"activities": [full], "method": "a ull"},
        {"activities": None, "method": M.MANUAL, "amounts": {full: 0}},
        {"activities": None, "method": M.MANUAL, "amounts": {full: True}},
        {"activities": None, "method": M.MANUAL, "amounts": {}},
    ):
        with pytest.raises(services.ExpenseRejected):
            allocation.allocate(spent, by=treasurer, **kwargs)
    # Una activitat sense participants, al costat d'una altra, rep zero: es rebutja.
    with pytest.raises(services.ExpenseRejected):
        allocation.allocate(spent, [empty, full], M.PARTICIPANTS, by=treasurer)
    services.annul(spent, by=treasurer, reason="Factura duplicada (motiu inventat).")
    with pytest.raises(services.ExpenseRejected):
        allocation.allocate(spent, [full], M.EQUAL, by=treasurer)


def test_mg3_only_the_treasurer_and_the_administrator(treasurer, manager):
    with pytest.raises(Http404):
        allocation.allocate(expense(treasurer, 1000), [outing(manager, 1)], M.EQUAL, by=manager)


def test_one_allocation_per_expense_and_activity_also_in_the_database(treasurer, manager):
    activity = outing(manager, 1)
    rows = allocation.allocate(expense(treasurer, 1000), [activity], M.EQUAL, by=treasurer)
    with transaction.atomic(), pytest.raises(IntegrityError):
        ExpenseAllocation.objects.create(
            expense=rows[0].expense, activity=activity, amount_cents=1, method=M.MANUAL,
            created_by=treasurer,
        )  # fmt: skip


@pytest.mark.parametrize(
    "amount,weights",
    list(itertools.product((1, 2, 999, 10000, 123457), ((1,), (7, 7, 7), (3, 0, 5), (1, 2, 3, 4)))),
)
def test_split_always_sums_the_amount_and_never_moves_more_than_a_cent(amount, weights):
    parts = allocation.split(
        amount, list(weights), sorted(range(len(weights)), key=lambda i: -weights[i])
    )
    assert sum(parts) == amount
    total = sum(weights)
    assert all(abs(p * total - amount * w) < total for p, w in zip(parts, weights, strict=True))


def test_t_m09_11_the_forecast_uses_live_enrolments_and_allocations(treasurer, manager):
    activity = outing(manager, 2)  # 2 confirmades a 4500
    enrolled(activity, "Pendent", Enrolment.Status.PENDING_PAYMENT)
    enrolled(activity, "Espera", Enrolment.Status.WAITLISTED)  # no compta
    spent = expense(treasurer, 25000)  # «Embarcació»
    planned.set_planned_cost(activity, spent.category, 30000, by=treasurer)
    allocation.allocate(spent, [activity], M.EQUAL, by=treasurer)
    margin = margins.activity_margin(activity)
    assert (margin.income_enrolments_cents, margin.participants) == (3 * 4500, 3)
    assert margin.breakdown["costs_by_category"] == {"Embarcació": 25000}  # el real, no el previst
    services.annul(spent, by=treasurer, reason="Motiu inventat.")
    assert margins.activity_margin(activity).breakdown["costs_by_category"] == {"Embarcació": 30000}
