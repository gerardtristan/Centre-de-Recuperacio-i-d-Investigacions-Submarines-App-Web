"""T-M09-11b: marge real amb el material del 03 (RN-M09-01 a 05; RN-M03-10; CA-M09-07 i 08): la
sortida a les Medes de l'exemple de M09-7. Només dades inventades."""

import pytest

from apps.activities.models import Activity, Enrolment
from apps.activities.tests.test_attendance import enrolled, opened
from apps.core import audit
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, handover, inventory
from apps.equipment.models import CentreRate, DiveCentre, UsageRate
from apps.equipment.tests.test_assignments import JUNE, keeper, kind, manager, outing  # noqa: F401
from apps.expenses import allocation
from apps.expenses import services as expenses
from apps.expenses.models import ExpenseCategory, Supplier
from apps.expenses.tests.test_expenses import data
from apps.margins import calc
from apps.margins import services as margins
from apps.treasury import services as treasury
from apps.treasury.tests.test_record_income import paid

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-t-m09-11b")


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def spend(treasurer, category, amount, activity):
    supplier = Supplier.objects.create(name=f"Proveïdor inventat {category} {amount}")
    category = ExpenseCategory.objects.get(name=category)
    spent = expenses.record_expense(
        by=treasurer, **data(supplier, category=category, amount_cents=amount)
    )
    allocation.allocate(spent, [activity], "equal", by=treasurer)


@pytest.fixture
def medes(manager, keeper, treasurer):  # noqa: F811
    """10 participants a 6000; embarcació 25.000; aire 12.000; 3 equips llogats a 2500; 7
    ampolles del club a 350 per dia."""
    activity = outing(manager, days=1)
    rows = []
    for i in range(10):
        row = enrolled(activity, f"P{i}")
        payment = paid(row.person, kind="enrolment", amount=6000, department=activity.department)
        Enrolment.objects.filter(pk=row.pk).update(charge=payment.charge)
        treasury.record_income(payment, origin="provider", by=SYSTEM)
        rows.append(row)
    spend(treasurer, "Embarcació", 25000, activity)
    spend(treasurer, "Aire", 12000, activity)
    centre = DiveCentre.objects.create(name="Centre de les Medes (inventat)")
    CentreRate.objects.create(
        centre=centre, label="Equip complet", equipment_type=kind("Jaquet"), cost_cents=2500,
        member_price_cents=3000, valid_from=JUNE, created_by=keeper,
    )  # fmt: skip
    UsageRate.objects.create(
        equipment_type=kind("Ampolla"), cost_per_day_cents=350, valid_from=JUNE
    )
    for row in rows[:3]:
        rented = assignments.assign_rented(row, kind("Jaquet"), centre, by=keeper)
        handover.deliver(rented, by=keeper)
    for row in rows[3:]:
        tank = inventory.create_item(
            equipment_type=kind("Ampolla"), by=keeper, litres=12, next_review_on=JUNE
        )
        handover.deliver(assignments.assign_club(row, tank, by=keeper), by=keeper)
    return opened(activity, Activity.Status.DONE)


def test_ca_m09_07_the_medes_outing(medes):
    margin = margins.activity_margin(medes, calc.REAL)
    assert margin.breakdown["rental"] == {"source": "estimated", "cents": 7500}
    assert (margin.material_cost_cents, margin.breakdown["material_source"]) == (2450, "real")
    assert (margin.margin_cents, margin.margin_pct_tenths, margin.per_participant_cents) == (
        13050, 218, 1305,
    )  # fmt: skip


def test_ca_m09_08_the_centre_invoice_replaces_the_estimate(medes, treasurer):
    spend(treasurer, "Lloguer", 7800, medes)
    margin = margins.activity_margin(medes, calc.REAL)
    assert margin.breakdown["rental"] == {
        "source": "invoiced", "cents": 7800, "deviation_cents": 300,
    }  # fmt: skip
    assert "Lloguer" not in margin.breakdown["costs_by_category"]  # mai totes dues
    assert margin.margin_cents == 13050 - 300 == 12750
    forecast = margins.activity_margin(medes)
    assert forecast.breakdown["rental"]["cents"] == 7800
    assert forecast.material_cost_cents == 2450  # el real del club, no el previst del 02
