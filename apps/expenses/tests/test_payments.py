"""T-M09-05: pagar i anul·lar una despesa amb moviments de la 04 (CA-M09-02, CA-M09-03 i
CA-M09-22; RN-M09-11). Només dades inventades."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.models import AppendOnlyError, AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import services
from apps.expenses.models import Expense, ExpenseAnnulment, Supplier
from apps.expenses.tests.test_expenses import data
from apps.margins.models import Period
from apps.treasury.models import Movement, TreasuryAccount
from apps.treasury.services import PeriodClosed

pytestmark = pytest.mark.django_db
MID_OCTOBER, END_OCTOBER, FIRST_NOVEMBER = date(2026, 10, 15), date(2026, 10, 31), date(2026, 11, 1)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


@pytest.fixture
def bank():
    return TreasuryAccount.objects.get(name="Banc principal")


@pytest.fixture
def expense(treasurer):
    supplier = Supplier.objects.create(name="Nàutica Inventada SL")
    return services.record_expense(by=treasurer, **data(supplier))


def expense_movements():
    return Movement.objects.filter(kind=Movement.Kind.EXPENSE)


def test_ca_m09_02_pagar_crea_un_sol_moviment_amb_el_mateix_import_i_departament(
    expense, bank, treasurer
):
    paid = services.pay(expense, account=bank, value_date=MID_OCTOBER, by=treasurer)

    movement = expense_movements().get()
    assert (paid.status, paid.paid_movement) == ("paid", movement)
    assert (movement.amount_cents, movement.department, movement.cost_centre) == (
        25000,
        expense.department,
        None,
    )
    assert movement.value_date == MID_OCTOBER
    assert movement.concept == f"Despesa {expense.pk}: Sortida a les Medes"
    assert AuditEntry.objects.get(action=services.EXPENSE_PAID).details["movement"] == movement.pk

    with pytest.raises(services.AlreadyPaid):
        services.pay(expense, account=bank, value_date=MID_OCTOBER, by=treasurer)
    assert expense_movements().count() == 1


def test_un_pagament_dins_un_periode_tancat_es_rebutja_i_no_desa_res(expense, bank, treasurer):
    Period.objects.create(starts_on=date(2026, 10, 1), ends_on=END_OCTOBER, status="closed")
    with pytest.raises(PeriodClosed):
        services.pay(expense, account=bank, value_date=END_OCTOBER, by=treasurer)
    assert Expense.objects.get(pk=expense.pk).status == "to_pay"
    assert not expense_movements().exists()


def test_ca_m09_03_pagada_no_canvia_i_s_anulla_amb_contramoviment(expense, bank, treasurer):
    services.pay(expense, account=bank, value_date=MID_OCTOBER, by=treasurer)
    with pytest.raises(services.ExpenseLocked):
        services.update_expense(expense, by=treasurer, amount_cents=1)

    annulment = services.annul(expense, reason="Factura duplicada", by=treasurer)

    original = expense_movements().get()
    assert annulment.reversal_movement.reverses == original
    assert annulment.reversal_movement.amount_cents == 25000
    assert (annulment.reason, annulment.annulled_by) == ("Factura duplicada", treasurer)
    assert Expense.objects.get(pk=expense.pk).status == "annulled"
    assert Movement.objects.get(pk=original.pk).value_date == MID_OCTOBER
    entry = AuditEntry.objects.get(action=services.EXPENSE_ANNULLED)
    assert entry.reason == "Factura duplicada"
    with pytest.raises(services.ExpenseLocked):
        services.annul(expense, reason="Una altra vegada", by=treasurer)
    with pytest.raises(services.AlreadyPaid):
        services.pay(expense, account=bank, value_date=MID_OCTOBER, by=treasurer)


def test_una_despesa_per_pagar_s_anulla_sense_cap_moviment(expense, treasurer):
    annulment = services.annul(expense, reason="Registrada per error", by=treasurer)
    assert annulment.reversal_movement is None
    assert not Movement.objects.exists()


def test_anullar_demana_motiu(expense, treasurer):
    with pytest.raises(services.ExpenseRejected):
        services.annul(expense, reason="   ", by=treasurer)
    assert not ExpenseAnnulment.objects.exists()


def test_ca_m09_22_correccio_d_un_periode_tancat_al_periode_obert(expense, bank, treasurer):
    original = services.pay(
        expense, account=bank, value_date=MID_OCTOBER, by=treasurer
    ).paid_movement
    Period.objects.create(starts_on=date(2026, 10, 1), ends_on=END_OCTOBER, status="closed")

    with pytest.raises(PeriodClosed):
        services.annul(expense, reason="Import equivocat", by=treasurer, value_date=END_OCTOBER)
    assert Expense.objects.get(pk=expense.pk).status == "paid"
    assert not ExpenseAnnulment.objects.exists()

    annulment = services.annul(
        expense, reason="Import equivocat", by=treasurer, value_date=FIRST_NOVEMBER
    )
    corrected = services.record_expense(
        by=treasurer, **data(expense.supplier, invoice_number="F-2026-101-R", amount_cents=24000)
    )
    services.pay(corrected, account=bank, value_date=FIRST_NOVEMBER, by=treasurer)

    assert annulment.reversal_movement.value_date == FIRST_NOVEMBER
    assert Expense.objects.get(pk=corrected.pk).paid_movement.value_date == FIRST_NOVEMBER
    assert Movement.objects.get(pk=original.pk).value_date == MID_OCTOBER


@pytest.mark.parametrize("role", ["president", "secretary", "board", None])
def test_sense_mg2_no_paga_ni_anulla(make_admin, expense, bank, role):  # noqa: F811
    other = make_admin(*([role] if role else []))
    with pytest.raises(Http404):
        services.pay(expense, account=bank, value_date=MID_OCTOBER, by=other)
    with pytest.raises(Http404):
        services.annul(expense, reason="Motiu", by=other)
    assert Expense.objects.get(pk=expense.pk).status == "to_pay"


def test_l_administrador_paga_i_anulla(make_admin, expense, bank):  # noqa: F811
    admin = make_admin("administrator")
    services.pay(expense, account=bank, value_date=MID_OCTOBER, by=admin)
    services.annul(expense, reason="Factura duplicada", by=admin)
    assert Expense.objects.get(pk=expense.pk).status == "annulled"


def test_l_anullacio_nomes_s_afegeix(expense, treasurer):
    annulment = services.annul(expense, reason="Registrada per error", by=treasurer)
    annulment.reason = "Un altre motiu"
    with pytest.raises(AppendOnlyError):
        annulment.save()
    with pytest.raises(AppendOnlyError):
        annulment.delete()


def test_pagada_sempre_amb_moviment_i_per_pagar_mai(expense):
    with pytest.raises(IntegrityError), transaction.atomic():
        Expense.objects.filter(pk=expense.pk).update(status="paid")
