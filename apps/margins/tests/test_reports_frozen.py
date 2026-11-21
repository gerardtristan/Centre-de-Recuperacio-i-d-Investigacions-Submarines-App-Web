"""T-M09-14 (segona part): marges congelats a l'informe per departament, agrupats per activitat,
subtipus o projecte, i la part repartida fora de les despeses sense activitat (P-M09-E; S-M09-06;
exemple «Departament de medi ambient» de M09-7). Només dades inventades."""

import datetime

import pytest
from django.utils import timezone

from apps.activities.models import Activity
from apps.activities.tests.helpers import a_project, an_outing, cleaning, general, outing_type
from apps.activities.tests.test_attendance import opened
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import allocation, income
from apps.expenses import services as expenses
from apps.expenses.models import ExpenseCategory, Supplier
from apps.expenses.tests.test_expenses import invoice
from apps.margins import reports
from apps.margins.models import MarginSnapshot
from apps.treasury.models import TreasuryAccount

pytestmark = pytest.mark.django_db
OCTOBER = (datetime.date(2026, 10, 1), datetime.date(2026, 10, 31))


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def frozen(activity, margin, by, day=datetime.date(2026, 10, 20), **fields):
    return MarginSnapshot.objects.create(
        activity=activity, income_enrolments_cents=0, other_direct_income_cents=0,
        direct_costs_cents=0, material_cost_cents=0, margin_cents=margin, participants=0,
        breakdown={}, closed_by=by,
        closed_at=timezone.make_aware(datetime.datetime.combine(day, datetime.time(12))),
        **fields,
    )  # fmt: skip


def environmental(manager, project):
    return opened(
        an_outing(manager, outing_type=outing_type("Medi ambient"), subtype=cleaning(),
                  project=project),
        Activity.Status.CLOSED,
    )  # fmt: skip


def test_the_environment_department_example(treasurer, manager):
    project = a_project()
    first, second = environmental(manager, project), environmental(manager, project)
    frozen(first, 13050, treasurer)
    frozen(second, 8200, treasurer)
    frozen(environmental(manager, project), 99999, treasurer, day=datetime.date(2026, 11, 2))
    bank = TreasuryAccount.objects.get(name="Banc principal")
    spent = expenses.record_expense(
        by=treasurer, supplier=Supplier.objects.create(name="Bus Inventat SL"),
        invoice_number="F-9", invoice_date=datetime.date(2026, 10, 5),
        category=ExpenseCategory.objects.get(name="Embarcació"), description="Bus",
        amount_cents=10000, department=general(),
    )  # fmt: skip
    expenses.pay(spent, account=bank, value_date=datetime.date(2026, 10, 6), by=treasurer)
    # 6000 repartits a una activitat (ja dins el seu marge): no tornen a sortir sense activitat.
    allocation.allocate(
        spent, None, "manual", by=treasurer, amounts={opened(an_outing(manager)): 6000}
    )
    income.record_other_income(
        kind="grant", payer="Organisme Inventat", amount_cents=300000, account=bank,
        value_date=datetime.date(2026, 10, 20), department=general(),
        document_file=invoice(treasurer.person), by=treasurer,
    )  # fmt: skip

    report = reports.department_report(general(), *OCTOBER)

    assert sorted(report.activity_margins_cents.values()) == [8200, 13050]  # el de novembre no
    assert report.margins_total_cents == 21250
    assert report.expenses_without_activity_cents == 4000
    assert report.total_cents == 21250 - 4000 + 300000 == 317250
    by_project = reports.department_report(general(), *OCTOBER, group_by="project")
    assert by_project.activity_margins_cents == {project.name: 21250}
    by_subtype = reports.department_report(general(), *OCTOBER, group_by="subtype")
    assert by_subtype.activity_margins_cents == {"Neteja": 21250}
    assert "General;Marge: Neteja;21250" in reports.to_csv(by_subtype)


def test_a_superseded_margin_does_not_count_and_the_grouping_is_checked(treasurer, manager):
    activity = environmental(manager, None)
    old = frozen(activity, 1000, treasurer)
    frozen(activity, 1500, treasurer, supersedes=old, reopen_reason="Repartiment mal fet.")
    report = reports.department_report(general(), *OCTOBER, group_by="subtype")
    assert report.activity_margins_cents == {"Neteja": 1500}
    assert reports.department_report(
        general(), *OCTOBER, group_by="project"
    ).activity_margins_cents == {"Sense projecte": 1500}
    with pytest.raises(ValueError):
        reports.department_report(general(), *OCTOBER, group_by="persona")
