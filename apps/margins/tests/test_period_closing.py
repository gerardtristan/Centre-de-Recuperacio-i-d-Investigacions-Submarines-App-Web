"""T-M09-16: llista de control, tancament (també amb excepcions documentades), reobertura i marge
recalculat (P-M09-G; RN-M09-15, 16, 24 i 26; CA-M09-13, 14, 15 i 29). Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone

from apps.activities.models import Activity
from apps.activities.tests.helpers import an_outing
from apps.activities.tests.test_attendance import opened
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import allocation
from apps.expenses import services as expenses
from apps.expenses.models import Supplier
from apps.expenses.tests.test_expenses import data
from apps.margins import closing, period_closing, reports
from apps.margins.models import MarginSnapshot, Period, PeriodEvent
from apps.treasury import reconciliation
from apps.treasury.models import TreasuryAccount
from apps.treasury.services import PeriodClosed
from apps.treasury.tests.test_reconciliation import lines

pytestmark = pytest.mark.django_db
NOV = (datetime.date(2026, 11, 1), datetime.date(2026, 11, 30))
DEC = (datetime.date(2026, 12, 1), datetime.date(2026, 12, 31))
R = Role.Code


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(R.ADMINISTRATOR)


def period(days):
    return Period.objects.create(starts_on=days[0], ends_on=days[1])


def an_expense(treasurer, day, amount=5000):
    supplier = Supplier.objects.create(name=f"Proveïdor inventat {day} {amount}")
    return expenses.record_expense(
        by=treasurer, **data(supplier, invoice_date=day, amount_cents=amount)
    )


def keys(items):
    return [item["key"] for item in items]


def test_ca_m09_13_an_expense_without_invoice_blocks_closing(treasurer):
    november = period(NOV)
    spent = an_expense(treasurer, datetime.date(2026, 11, 10))
    assert keys(period_closing.checklist(november)) == [f"expense_without_invoice:{spent.pk}"]
    with pytest.raises(period_closing.PeriodNotReady) as error:
        period_closing.close(november, by=treasurer)
    assert error.value.items[0]["label"] == "Despesa sense factura: Sortida a les Medes."
    november.refresh_from_db()
    assert november.status == Period.Status.OPEN


def test_ca_m09_29_carried_lines_need_a_reason_each_and_reach_the_next_period(treasurer):
    november, december = period(NOV), period(DEC)
    first, second = lines(treasurer, (-1200, "Comissió inventada"), (-800, "Una altra"))
    reconciliation.refresh()
    items = period_closing.checklist(november)
    assert keys(items) == [f"statement_line:{first.pk}", f"statement_line:{second.pk}"]

    with pytest.raises(period_closing.PeriodNotReady) as error:
        period_closing.close(
            november, by=treasurer, exceptions={items[0]["key"]: "Es mira amb el banc."}
        )
    assert keys(error.value.items) == [items[1]["key"]]
    reasons = {items[0]["key"]: "Es mira amb el banc.", items[1]["key"]: "Falta el rebut."}
    event = period_closing.close(november, by=treasurer, exceptions=reasons)
    assert [(e["key"], e["reason"]) for e in event.exceptions] == list(reasons.items())
    entry = AuditEntry.objects.get(action=period_closing.PERIOD_CLOSED)
    assert len(entry.details["exceptions"]) == 2

    # Al període següent hi surten totes dues; no es tanca sense resoldre-les o tornar-les a portar.
    assert keys(period_closing.checklist(december)) == list(reasons)
    with pytest.raises(period_closing.PeriodNotReady):
        period_closing.close(december, by=treasurer)
    reconciliation.exclude(first, reason="Línia duplicada (inventat).", by=treasurer)
    assert keys(period_closing.checklist(december)) == [items[1]["key"]]
    period_closing.close(december, by=treasurer, exceptions={items[1]["key"]: "Encara falta."})


def test_periods_close_in_order_and_unknown_exceptions_are_rejected(treasurer):
    november, december = period(NOV), period(DEC)
    with pytest.raises(ValidationError):
        period_closing.close(december, by=treasurer)
    with pytest.raises(ValidationError):
        period_closing.close(november, by=treasurer, exceptions={"activity:999": "x"})
    period_closing.close(november, by=treasurer)
    with pytest.raises(ValidationError):  # ja és tancat
        period_closing.close(november, by=treasurer)


def test_ca_m09_14_a_closed_period_rejects_and_reopening_accepts(treasurer, admin):
    november = period(NOV)
    period_closing.close(november, by=treasurer)
    spent = an_expense(treasurer, datetime.date(2026, 11, 12))
    bank = TreasuryAccount.objects.get(name="Banc principal")
    with pytest.raises(PeriodClosed):
        expenses.pay(spent, account=bank, value_date=datetime.date(2026, 11, 12), by=treasurer)
    event = period_closing.reopen(november, by=admin, reason="Repartiment mal fet (inventat).")
    assert event.action == PeriodEvent.Action.REOPEN
    expenses.pay(spent, account=bank, value_date=datetime.date(2026, 11, 12), by=treasurer)
    entry = AuditEntry.objects.get(action=period_closing.PERIOD_REOPENED)
    assert (entry.old_value, entry.new_value, entry.reason) == (
        "closed", "open", "Repartiment mal fet (inventat).",
    )  # fmt: skip


def test_ca_m09_15_only_the_administrator_reopens_the_last_closed_period(treasurer, admin):
    november, december = period(NOV), period(DEC)
    period_closing.close(november, by=treasurer)
    period_closing.close(december, by=treasurer)
    with pytest.raises(Http404):
        period_closing.reopen(december, by=treasurer, reason="Vull canviar-ho.")
    with pytest.raises(ValidationError):
        period_closing.reopen(december, by=admin, reason="  ")
    with pytest.raises(ValidationError):  # la guarda de la 04 és una sola data (P-471)
        period_closing.reopen(november, by=admin, reason="Error de novembre.")
    period_closing.reopen(december, by=admin, reason="Error de desembre (inventat).")


def test_s_m09_13_reopening_emails_the_treasurer_and_the_board(make_admin, treasurer, admin):  # noqa: F811
    treasurer.notification_email = "tresoreria@example.org"
    treasurer.save()
    board = make_admin(R.BOARD)
    board.notification_email = "junta@example.org"
    board.save()
    secretary = make_admin(R.SECRETARY)  # ni tresorer ni junta: no el rep
    secretary.notification_email = "secretaria@example.org"
    secretary.save()
    november = period(NOV)
    period_closing.close(november, by=treasurer)
    assert not OutgoingEmail.objects.filter(template=period_closing.REOPENED_TEMPLATE).exists()
    period_closing.reopen(november, by=admin, reason="Repartiment mal fet (inventat).")
    sent = OutgoingEmail.objects.filter(template=period_closing.REOPENED_TEMPLATE)
    assert sorted(sent.values_list("to_address", flat=True)) == [
        "junta@example.org",
        "tresoreria@example.org",
    ]
    email = sent.first()
    assert "01/11/2026 – 30/11/2026" in email.subject
    assert "Repartiment mal fet (inventat)." in email.body_text


def test_a_done_activity_of_the_period_is_on_the_checklist(make_admin, treasurer):  # noqa: F811
    june = period((datetime.date(2027, 6, 1), datetime.date(2027, 6, 30)))
    activity = opened(an_outing(make_admin(R.COURSES_MANAGER)), Activity.Status.DONE)
    assert keys(period_closing.checklist(june)) == [f"activity:{activity.pk}"]
    assert "Activitat feta sense tancar" in period_closing.checklist(june)[0]["label"]


def test_a_reopened_period_lets_the_margin_be_recomputed_and_replaced(make_admin, treasurer, admin):  # noqa: F811, E501
    june = period((datetime.date(2027, 6, 1), datetime.date(2027, 6, 30)))
    activity = opened(an_outing(make_admin(R.COURSES_MANAGER)), Activity.Status.DONE)
    closed_at = timezone.make_aware(datetime.datetime(2027, 6, 20, 12))
    first = closing.close_activity(activity, by=treasurer, now=closed_at)
    assert first.margin_cents == 0
    with pytest.raises(ValidationError):  # el període no s'ha reobert
        period_closing.recompute_margin(activity, by=treasurer)

    later = closed_at + datetime.timedelta(days=5)
    period_closing.close(june, by=treasurer, now=later)
    period_closing.reopen(
        june, by=admin, reason="Faltava repartir l'embarcació (inventat).", now=later
    )
    spent = an_expense(treasurer, datetime.date(2027, 6, 14), amount=2500)
    allocation.allocate(spent, [activity], "equal", by=treasurer)
    with pytest.raises(Http404):  # MG7
        period_closing.recompute_margin(activity, by=make_admin(R.COURSES_MANAGER))
    second = period_closing.recompute_margin(activity, by=treasurer)

    assert (second.margin_cents, second.supersedes, second.reopen_reason) == (
        -2500, first, "Faltava repartir l'embarcació (inventat).",
    )  # fmt: skip
    assert closing.current(activity) == second
    assert MarginSnapshot.objects.filter(activity=activity).count() == 2
    assert reports.first_closed_at(second) == closed_at
    report = reports.department_report(activity.department, *(june.starts_on, june.ends_on))
    assert list(report.activity_margins_cents.values()) == [-2500]  # només el vigent
    assert not period_closing.late_movements(activity, june).exists()
