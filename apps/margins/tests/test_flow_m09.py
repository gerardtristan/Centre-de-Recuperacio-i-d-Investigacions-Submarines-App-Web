"""T-M09-23: prova de principi a fi del 09 a nivell de servei: inscripcions pagades (proveïdor
fictici, 092) → despeses amb factura, pagades i repartides → activitat feta → tancament amb el marge
congelat → informe del departament → tancament del període amb la llista de control (T-M09-16), que
rebutja un registre nou amb data d'aquell mes. Només dades inventades."""

import datetime

import pytest

from apps.activities import enrolment, states
from apps.activities.tests.helpers import BEFORE_DEADLINE, PUBLISHED, a_member, an_outing, moment
from apps.core import audit, charges, events
from apps.core.models import Department, Event, Payment, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import allocation
from apps.expenses import services as expenses
from apps.expenses.models import Expense, ExpenseCategory, Supplier
from apps.expenses.tests.test_expenses import invoice
from apps.margins import calc, closing, period_closing, reports
from apps.margins import services as margins
from apps.margins.models import Period
from apps.treasury import services as treasury
from apps.treasury.models import TreasuryAccount
from apps.treasury.services import PeriodClosed

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-t-m09-23")
JUNE = (datetime.date(2027, 6, 1), datetime.date(2027, 6, 30))
PRICE, FEE = 4500, 30


def pay(row):
    charges.record_payment(row.charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
    events.deliver(Event.objects.get(name=events.CHARGE_PAID, payload__charge=row.charge_id).pk)
    payment = Payment.objects.get(charge=row.charge)
    treasury.record_income(payment, origin="provider", by=SYSTEM)
    treasury.record_fee(payment, FEE, by=SYSTEM)


def paid_expense(treasurer, category, amount, day, document, number):
    spent = expenses.record_expense(
        by=treasurer, supplier=Supplier.objects.get_or_create(name="Proveïdor inventat SL")[0],
        invoice_number=number, invoice_date=day,
        category=ExpenseCategory.objects.get(name=category), description=f"{category} (inventat)",
        amount_cents=amount, department=Department.objects.get(name=Department.GENERAL),
    )  # fmt: skip
    Expense.objects.filter(pk=spent.pk).update(invoice_file=document)  # fitxer: T-M09-25
    bank = TreasuryAccount.objects.get(name="Banc principal")
    return expenses.pay(spent, account=bank, value_date=day, by=treasurer)


def test_t_m09_23_from_the_enrolment_to_the_closed_period(make_admin):  # noqa: F811
    manager, treasurer = make_admin(Role.Code.COURSES_MANAGER), make_admin(Role.Code.TREASURER)
    activity = an_outing(manager)  # 14 i 15 de juny de 2027, preu de soci 4500
    states.publish(activity, by=manager, now=PUBLISHED)
    for i in range(3):
        account = a_member(f"Sòcia {i}")
        pay(enrolment.enrol(
            activity, account.person, channel="account", actor=account, now=BEFORE_DEADLINE
        ))  # fmt: skip

    document = invoice(treasurer.person)
    day = datetime.date(2027, 6, 10)
    boat = paid_expense(treasurer, "Embarcació", 6000, day, document, "F-1")
    allocation.allocate(boat, None, "manual", by=treasurer, amounts={activity: 5000})
    paid_expense(treasurer, "Altres", 1500, day, document, "F-2")  # sense activitat

    forecast = margins.activity_margin(activity)
    assert forecast.margin_cents == 3 * PRICE - 5000

    states.mark_done(activity, by=manager, now=moment(2027, 6, 16, 12))
    snapshot = closing.close_activity(activity, by=treasurer, now=moment(2027, 6, 20, 12))
    assert snapshot.margin_cents == 3 * PRICE - 5000 - 3 * FEE == 8410
    assert margins.activity_margin(activity, calc.REAL).margin_cents == 8410

    report = reports.department_report(activity.department, *JUNE)
    assert list(report.activity_margins_cents.values()) == [8410]
    # 6000 + 1500 pagades; 5000 ja són al marge de l'activitat.
    assert report.expenses_without_activity_cents == 2500
    assert report.total_cents == 8410 - 2500
    assert "8410" in reports.to_csv(report)

    june = Period.objects.create(starts_on=JUNE[0], ends_on=JUNE[1])
    # Les dues despeses pagades encara no s'han conciliat amb l'extracte: es porten al mes
    # següent amb motiu (excepcions documentades, RN-M09-26).
    pending = period_closing.checklist(june)
    assert {item["key"].split(":")[0] for item in pending} == {"expense_unreconciled"}
    with pytest.raises(period_closing.PeriodNotReady):
        period_closing.close(june, by=treasurer)
    reasons = {item["key"]: "Falta l'extracte de juny (inventat)." for item in pending}
    period_closing.close(june, by=treasurer, exceptions=reasons)
    late = expenses.record_expense(
        by=treasurer, supplier=Supplier.objects.get(name="Proveïdor inventat SL"),
        invoice_number="F-3", invoice_date=day, category=ExpenseCategory.objects.get(name="Aire"),
        description="Aire (inventat)", amount_cents=900,
        department=Department.objects.get(name=Department.GENERAL),
    )  # fmt: skip
    with pytest.raises(PeriodClosed):
        expenses.pay(
            late, account=TreasuryAccount.objects.get(name="Banc principal"), value_date=day,
            by=treasurer,
        )  # fmt: skip
