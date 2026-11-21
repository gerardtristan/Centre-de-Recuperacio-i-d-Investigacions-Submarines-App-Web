"""T-M09-14: informe per departament i CSV (P-M09-E; RN-M09-08; S-M09-06; CA-M09-20). Només
dades inventades."""

from datetime import date

import pytest

from apps.core.models import Department
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import income
from apps.expenses import services as expenses
from apps.expenses.models import ExpenseCategory, Supplier
from apps.expenses.tests.test_expenses import invoice
from apps.margins import reports
from apps.treasury.models import TreasuryAccount

pytestmark = pytest.mark.django_db
OCTOBER = (date(2026, 10, 1), date(2026, 10, 31))


def test_ca_m09_20_l_ajut_en_una_linia_propia_i_el_total_del_departament():
    report = reports.DepartmentReport(
        department="Medi ambient",
        activity_margins_cents={"Sortida a les Medes": 13050, "Neteja de fons": 8200},
        expenses_without_activity_cents=4000,
        grants_cents=300000,
        other_income_cents=0,
    )
    assert (report.margins_total_cents, report.total_cents) == (21250, 317250)
    rows = reports.to_csv(report).splitlines()
    assert rows[0] == "Departament;Concepte;Import (cèntims)"
    assert "Medi ambient;Marge: Sortida a les Medes;13050" in rows
    assert "Medi ambient;Ajuts;300000" in rows  # una línia pròpia, fora dels marges
    assert rows[-1] == "Medi ambient;Total del departament;317250"


def test_un_text_que_sembla_una_formula_no_s_executa_al_csv():
    report = reports.DepartmentReport("=Dept", {"=SUM(A1)": 1}, 0, 0, 0)
    rows = reports.to_csv(report).splitlines()
    assert rows[1] == "'=Dept;Marge: =SUM(A1);1"


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def test_l_informe_del_departament_amb_les_dades_del_periode(treasurer):
    general = Department.objects.get(name="General")
    bank = TreasuryAccount.objects.get(name="Banc principal")
    supplier = Supplier.objects.create(name="Nàutica Inventada SL")
    category = ExpenseCategory.objects.get(name="Embarcació")
    for number, day in (("F-1", date(2026, 10, 15)), ("F-2", date(2026, 11, 2))):
        expense = expenses.record_expense(
            by=treasurer,
            supplier=supplier,
            invoice_number=number,
            invoice_date=day,
            category=category,
            description="Sortida",
            amount_cents=4000,
            department=general,
        )
        expenses.pay(expense, account=bank, value_date=day, by=treasurer)
    common = {"account": bank, "department": general, "by": treasurer}
    resolution = invoice(treasurer.person)
    income.record_other_income(kind="grant", payer="Diputació Inventada", amount_cents=300000,
                               value_date=date(2026, 10, 20), document_file=resolution,
                               **common)  # fmt: skip
    income.record_other_income(kind="sponsorship", payer="Empresa Inventada", amount_cents=5000,
                               value_date=date(2026, 10, 21), **common)  # fmt: skip

    report = reports.department_report(general, *OCTOBER)

    assert (report.expenses_without_activity_cents, report.grants_cents) == (4000, 300000)
    assert (report.other_income_cents, report.activity_margins_cents) == (5000, {})
    assert report.total_cents == 301000
