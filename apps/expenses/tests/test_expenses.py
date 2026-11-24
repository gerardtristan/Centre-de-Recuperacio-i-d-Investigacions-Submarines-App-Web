"""T-M09-04: despesa per pagar, factura adjunta, estats i registre de canvis (CA-M09-01 i la
primera meitat de CA-M09-03). Només dades inventades."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.models import AuditEntry, Department, OutgoingEmail, PrivateFile
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import services
from apps.expenses.models import Expense, ExpenseCategory, Supplier
from apps.treasury.models import CostCentre
from apps.treasury.services import InvalidDepartment

pytestmark = pytest.mark.django_db


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin("treasurer")
    account.notification_email = "tresoreria@example.org"
    account.save()
    return account


@pytest.fixture
def boat():
    return Supplier.objects.create(name="Nàutica Inventada SL", tax_id="B00000000")


def data(supplier, **extra):
    return {
        "supplier": supplier,
        "invoice_number": "F-2026-101",
        "invoice_date": date(2026, 10, 15),
        "category": ExpenseCategory.objects.get(name="Embarcació"),
        "description": "Sortida a les Medes",
        "amount_cents": 25000,
        "department": Department.objects.get(name="General"),
        **extra,
    }


def invoice(person):
    return PrivateFile.objects.create(
        storage_key="prova-factura",
        kind=PrivateFile.Kind.PAYMENT_PROOF,
        owner=person,
        content_type="application/pdf",
        size_bytes=10,
        download_name="factura.pdf",
    )


def test_ca_m09_01_una_despesa_sense_factura_queda_per_pagar_i_surt_a_sense_factura(
    treasurer, boat
):
    expense = services.record_expense(by=treasurer, **data(boat))
    assert (expense.status, expense.recorded_by, expense.invoice_file) == (
        "to_pay",
        treasurer,
        None,
    )
    assert list(services.without_invoice()) == [expense]
    entry = AuditEntry.objects.get(action=services.EXPENSE_RECORDED)
    assert entry.details["amount_cents"] == 25000
    assert entry.details["supplier"] == boat.pk  # el proveïdor pot ser un autònom: només la clau


def test_amb_factura_no_es_sense_factura_i_una_anullada_tampoc(treasurer, boat):
    with_invoice = services.record_expense(by=treasurer, **data(boat))
    # Adjuntar el fitxer necessita un tipus de fitxer privat del nucli i el xifratge (T-M09-25).
    Expense.objects.filter(pk=with_invoice.pk).update(invoice_file=invoice(treasurer.person))
    annulled = services.record_expense(by=treasurer, **data(boat, invoice_number="F-2026-102"))
    Expense.objects.filter(pk=annulled.pk).update(status=Expense.Status.ANNULLED)
    assert with_invoice not in services.without_invoice()
    assert not services.without_invoice().exists()


def test_centre_de_cost_del_mateix_departament(treasurer, boat):
    general = Department.objects.get(name="General")
    centre = CostCentre.selectable().filter(department=general).first()
    expense = services.record_expense(by=treasurer, **data(boat, cost_centre=centre))
    assert expense.cost_centre == centre

    other = Department.objects.create(name="Medi ambient")
    with pytest.raises(InvalidDepartment):
        services.record_expense(
            by=treasurer, **data(boat, invoice_number="F-2", department=other, cost_centre=centre)
        )
    other.active = False
    other.save()
    with pytest.raises(InvalidDepartment):
        services.record_expense(by=treasurer, **data(boat, invoice_number="F-3", department=other))


@pytest.mark.parametrize(
    "extra",
    [
        {"amount_cents": 0},
        {"amount_cents": 250.0},
        {"amount_cents": True},
        {"tax_cents": -1},
        {"description": "   "},
        {"description": "x" * 201},
        {"invoice_number": "x" * 41},
    ],
)
def test_dades_que_no_valen(treasurer, boat, extra):
    with pytest.raises(services.ExpenseRejected):
        services.record_expense(by=treasurer, **data(boat, **extra))
    assert not Expense.objects.exists()


def test_proveidor_o_categoria_inactius(treasurer, boat):
    boat.active = False
    boat.save()
    with pytest.raises(services.ExpenseRejected):
        services.record_expense(by=treasurer, **data(boat))


def test_numero_de_factura_unic_per_proveidor_si_n_hi_ha(treasurer, boat):
    services.record_expense(by=treasurer, **data(boat))
    with pytest.raises(services.ExpenseRejected):
        services.record_expense(by=treasurer, **data(boat))
    other = Supplier.objects.create(name="Aire Inventat SCP")
    services.record_expense(by=treasurer, **data(other))
    services.record_expense(by=treasurer, **data(boat, invoice_number=""))
    services.record_expense(by=treasurer, **data(boat, invoice_number=" "))  # també buit
    assert Expense.objects.count() == 4


def test_camps_desconeguts(treasurer, boat):
    with pytest.raises(TypeError):
        services.record_expense(by=treasurer, status="paid", **data(boat))
    expense = services.record_expense(by=treasurer, **data(boat))
    with pytest.raises(TypeError):
        services.update_expense(expense, by=treasurer, status="paid")


def test_una_despesa_per_pagar_es_corregeix_i_cada_canvi_va_al_registre(treasurer, boat):
    expense = services.record_expense(by=treasurer, **data(boat))
    air = ExpenseCategory.objects.get(name="Aire")

    services.update_expense(
        expense, by=treasurer, amount_cents=26000, category=air, description="Sortida a les Medes"
    )

    entries = AuditEntry.objects.filter(action=services.EXPENSE_CHANGED)
    assert {(e.field, e.old_value, e.new_value) for e in entries} == {
        ("amount_cents", 25000, 26000),
        ("category", expense.category_id, air.pk),
    }
    assert Expense.objects.get(pk=expense.pk).amount_cents == 26000


def test_una_correccio_que_no_val_no_desa_res(treasurer, boat):
    expense = services.record_expense(by=treasurer, **data(boat))
    with pytest.raises(services.ExpenseRejected):
        services.update_expense(expense, by=treasurer, amount_cents=0)
    assert Expense.objects.get(pk=expense.pk).amount_cents == 25000


# La pagada: test_payments.py (CA-M09-03), perquè «pagada» porta el moviment de la 04.
@pytest.mark.parametrize("status", [Expense.Status.ANNULLED])
def test_ca_m09_03_una_despesa_pagada_o_anullada_no_canvia(treasurer, boat, status):
    expense = services.record_expense(by=treasurer, **data(boat))
    Expense.objects.filter(pk=expense.pk).update(status=status)
    with pytest.raises(services.ExpenseLocked):
        services.update_expense(expense, by=treasurer, amount_cents=1)
    assert Expense.objects.get(pk=expense.pk).amount_cents == 25000
    assert not AuditEntry.objects.filter(action=services.EXPENSE_CHANGED).exists()


@pytest.mark.parametrize("fields", [{"amount_cents": 0}, {"status": "lost"}])
def test_la_base_de_dades_rebutja_import_zero_i_estat_desconegut(treasurer, boat, fields):
    with pytest.raises(IntegrityError), transaction.atomic():
        Expense.objects.create(**{**data(boat), "recorded_by": treasurer, **fields})


def test_text_de_la_despesa(treasurer, boat):
    assert (
        str(services.record_expense(by=treasurer, **data(boat))) == "Sortida a les Medes (25000 c)"
    )


@pytest.mark.parametrize("role", ["secretary", "courses_manager", "board", None])
def test_sense_mg1_amb_abast_tot_no_registra_ni_corregeix(make_admin, treasurer, boat, role):  # noqa: F811
    # El responsable de cursos i sortides té «les seves activitats»: no val fins al repartiment.
    other = make_admin(*([role] if role else []))
    with pytest.raises(Http404):
        services.record_expense(by=other, **data(boat))
    expense = services.record_expense(by=treasurer, **data(boat))
    with pytest.raises(Http404):
        services.update_expense(expense, by=other, amount_cents=1)


@pytest.mark.parametrize("role", ["administrator", "president"])
def test_mg1_de_l_administrador_i_el_president(make_admin, boat, role):  # noqa: F811
    assert services.record_expense(by=make_admin(role), **data(boat)).status == "to_pay"


def test_ca_m09_01_el_tresorer_rep_un_sol_avis_sense_dades_del_proveidor(
    make_admin,  # noqa: F811
    treasurer,
    boat,
):
    make_admin("administrator")  # té MG2, però cap adreça d'avisos
    secretary = make_admin("secretary")
    secretary.notification_email = "secretaria@example.org"
    secretary.save()
    expense = services.record_expense(by=treasurer, **data(boat))
    sent = OutgoingEmail.objects.filter(template=services.NO_INVOICE_TEMPLATE)
    assert [e.to_address for e in sent] == ["tresoreria@example.org"]  # el secretari no té MG2
    assert str(expense.pk) in sent.get().body_text
    assert boat.name not in sent.get().body_text
    services.update_expense(expense, by=treasurer, amount_cents=26000)
    assert sent.count() == 1  # corregir-la no torna a avisar


def test_without_invoice_totals_for_the_dashboard_count_the_period(treasurer, boat):
    """T-M08-06: recompte i suma de les «sense factura» per la data de la factura (08)."""
    services.record_expense(by=treasurer, **data(boat, amount_cents=12345))
    services.record_expense(by=treasurer, **data(boat, invoice_number="F-2", amount_cents=655))
    services.record_expense(
        by=treasurer, **data(boat, invoice_number="F-3", invoice_date=date(2026, 11, 1))
    )
    with_invoice = services.record_expense(by=treasurer, **data(boat, invoice_number="F-4"))
    Expense.objects.filter(pk=with_invoice.pk).update(invoice_file=invoice(treasurer.person))
    october = (date(2026, 10, 1), date(2026, 10, 31))
    assert services.without_invoice_totals(*october) == (2, 13000)
    assert services.without_invoice_totals(date(2026, 9, 1), date(2026, 9, 30)) == (0, 0)
