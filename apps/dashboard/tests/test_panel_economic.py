"""Panell econòmic (T-M08-06; CA-M08-04 per al 04, el 09 i els ajuts; CA-M08-10; RN-M08-04;
HU-M08-02). Les lectures dels mòduls se substitueixen per valors coneguts: cada xifra del panell
és la que torna el servei, i la suma dels departaments és el total."""

import datetime
from types import SimpleNamespace

import pytest
from django.utils import timezone

from apps.dashboard import panels
from apps.margins.reports import DepartmentReport

pytestmark = pytest.mark.django_db
NOW = timezone.make_aware(datetime.datetime(2027, 3, 15, 12))
Q1 = (datetime.date(2027, 1, 1), datetime.date(2027, 3, 31))
REPORTS = {
    "General": DepartmentReport("General", {"Sortida A": 30000, "Curs B": -5000}, 4000, 12345, 0),
    "Escola": DepartmentReport("Escola", {"Curs C": 1000}, 0, 0, 655),
}
ZERO = DepartmentReport("", {}, 0, 0, 0)


@pytest.fixture
def services(monkeypatch):
    calls = []

    def report(department, starts_on, ends_on):
        calls.append((department.name, starts_on, ends_on))
        return REPORTS.get(department.name, ZERO)

    from apps.core.models import Department

    Department.objects.get_or_create(name="Escola")
    monkeypatch.setattr(panels, "department_report", report)
    monkeypatch.setattr(
        panels.grants_totals, "granted_by_department",
        lambda s, e: {"General": 100000, "Escola": 2} if (s, e) == Q1 else {},
    )  # fmt: skip
    monkeypatch.setattr(
        panels.expenses, "without_invoice_totals", lambda s, e: (3, 4500) if (s, e) == Q1 else 0
    )
    accounts = [
        SimpleNamespace(name="Banc", active=True, balance_cents=250000),
        SimpleNamespace(name="Caixa", active=True, balance_cents=0),
        SimpleNamespace(name="Antic", active=False, balance_cents=0),
        SimpleNamespace(name="Trànsit", active=False, balance_cents=-120),
    ]
    day = NOW.date()
    monkeypatch.setattr(panels.treasury, "balances", lambda on: accounts if on == day else [])
    return SimpleNamespace(calls=calls)


def cents(breakdown):
    return {key: cell.value for key, cell in breakdown.cells.items()}


def test_ca_m08_04_economic_panel_reads_each_service(services):
    blocks = panels.panel("economic", *Q1, now=NOW)
    assert list(blocks) == [
        "activity_margin", "department_income", "department_expenses", "grants_granted",
        "expenses_without_invoice", "expenses_without_invoice_amount", "treasury_balances",
    ]  # fmt: skip
    assert blocks["activity_margin"].value == 30000 - 5000 + 1000  # suma dels marges del 09
    (income,) = blocks["department_income"].breakdowns
    assert cents(income) == {"Escola": 655, "General": 12345}
    (expenses,) = blocks["department_expenses"].breakdowns
    assert cents(expenses) == {"General": 4000}
    (granted,) = blocks["grants_granted"].breakdowns
    assert cents(granted) == {"General": 100000, "Escola": 2}  # imports: no s'amaga res
    assert blocks["expenses_without_invoice"].value == 3
    assert blocks["expenses_without_invoice_amount"].value == 4500
    (balances,) = blocks["treasury_balances"].breakdowns
    assert cents(balances) == {"Banc": 250000, "Caixa": 0, "Trànsit": -120}  # «Antic» no surt
    assert balances.total.value == 249880


def test_hu_m08_02_department_figures_add_up_to_the_09_report(services):
    """El marge, els ingressos i les despeses d'un departament donen el total de l'informe."""
    blocks = panels.panel("economic", *Q1, now=NOW)
    (income,) = blocks["department_income"].breakdowns
    (expenses,) = blocks["department_expenses"].breakdowns
    for name, report in REPORTS.items():
        assert (
            report.margins_total_cents + cents(income).get(name, 0) - cents(expenses).get(name, 0)
        ) == report.total_cents
    assert blocks["activity_margin"].value + income.total.value - expenses.total.value == sum(
        report.total_cents for report in REPORTS.values()
    )


def test_each_department_report_is_read_once_for_the_period(services):
    panels.panel("economic", *Q1, now=NOW)
    names = [name for name, *_ in services.calls]
    assert len(names) == len(set(names)) and {"General", "Escola"} <= set(names)
    assert all((s, e) == Q1 for _, s, e in services.calls)


def test_ca_m08_10_amounts_in_euros_and_the_total(services):
    (income,) = panels.panel("economic", *Q1, now=NOW)["department_income"].breakdowns
    code = "department_income"
    assert [panels.text(code, cell, 3) for cell in income.cells.values()] == ["6,55 €", "123,45 €"]
    assert panels.text(code, income.total, 3) == "130,00 €"


def test_text_of_counts_percentages_and_missing_values():
    assert panels.text("occupancy", 55, 3) == "55 %"
    assert panels.text("occupancy", None, 3) == "—"
    assert panels.text("active_members", 163, 3) == "163"
    cell = panels.privacy.Cell(2, panels.privacy.BELOW)
    assert panels.text("active_by_type", cell, 3) == "menys de 3"


def test_ca_m08_09_a_failing_module_only_breaks_its_block(services, monkeypatch):
    def broken(on):
        raise RuntimeError("servei caigut")

    monkeypatch.setattr(panels.treasury, "balances", broken)
    blocks = panels.panel("economic", *Q1, now=NOW)
    assert blocks["treasury_balances"].error
    assert blocks["activity_margin"].value == 26000


def test_rn_m08_01_real_services_on_an_empty_database_only_return_numbers():
    for block in panels.panel("economic", *Q1, now=NOW).values():
        assert not block.error, block.code
        assert block.value is None or isinstance(block.value, int)
        for breakdown in block.breakdowns:
            assert all(isinstance(c.value, int) for c in breakdown.cells.values())
