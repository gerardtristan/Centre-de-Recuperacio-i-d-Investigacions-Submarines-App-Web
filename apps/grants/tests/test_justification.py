"""T-M09A-09: despeses lligades a un ajut amb els límits (RN-M09A-10; CA-M09A-09, 10 i 21).
Només dades inventades."""

from datetime import date

import pytest
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.models import AuditEntry, Department
from apps.expenses import services as expenses
from apps.expenses.models import Expense, ExpenseCategory, Supplier
from apps.grants import justification as j
from apps.grants.models import GrantApplication, GrantExpenseLink
from apps.grants.tests.test_resolution import grant, submitted  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


@pytest.fixture
def granted(submitted, treasurer):  # noqa: F811
    return grant(submitted, treasurer)


def expense(by, amount=10000, number="F-1", **extra):
    fields = {
        "supplier": Supplier.objects.get_or_create(name="Nàutica Inventada SL")[0],
        "invoice_number": number,
        "invoice_date": date(2027, 5, 10),
        "category": ExpenseCategory.objects.get(name="Embarcació"),
        "description": "Sortida de mostreig",
        "amount_cents": amount,
        "department": Department.objects.get(name="General"),
        **extra,
    }
    return expenses.record_expense(by=by, **fields)


def test_lligar_una_despesa_del_departament_amb_l_import_imputat(granted, treasurer):
    link = j.link_expense(granted, expense(treasurer), 6000, by=treasurer)
    assert (link.amount_cents, link.removed_at, str(link)) == (
        6000,
        None,
        f"{link.expense_id}: 6000 c",
    )
    assert AuditEntry.objects.get(action=j.EXPENSE_LINKED).details["amount_cents"] == 6000


def test_ca_m09a_09_una_despesa_d_un_altre_departament_es_rebutja(granted, treasurer):
    other = Department.objects.create(name="Medi ambient")
    with pytest.raises(j.ExpenseOutOfScope):
        j.link_expense(granted, expense(treasurer, department=other), 1000, by=treasurer)


def test_fora_del_periode_subvencionable_o_anullada(granted, treasurer):
    call = granted.call
    call.eligible_expenses_from, call.eligible_expenses_to = date(2027, 5, 11), date(2027, 12, 31)
    call.save()
    with pytest.raises(j.ExpenseOutOfScope):
        j.link_expense(granted, expense(treasurer), 1000, by=treasurer)  # del 10/5
    call.eligible_expenses_from, call.eligible_expenses_to = date(2027, 1, 1), date(2027, 5, 9)
    call.save()
    with pytest.raises(j.ExpenseOutOfScope):
        j.link_expense(granted, expense(treasurer, number="F-2"), 1000, by=treasurer)
    call.eligible_expenses_to = None
    call.save()
    annulled = expense(treasurer, number="F-3")
    Expense.objects.filter(pk=annulled.pk).update(status=Expense.Status.ANNULLED)
    with pytest.raises(j.ExpenseOutOfScope):
        j.link_expense(granted, annulled, 1000, by=treasurer)


def test_ca_m09a_10_la_suma_entre_ajuts_no_passa_de_l_import(granted, treasurer, call, general):
    other = GrantApplication.objects.create(
        call=call,
        responsible=treasurer.person,
        department=general,
        created_by=treasurer,
        status="granted",
        submitted_on=date(2027, 2, 1),
        submission_ref="RE-2",
        amount_requested_cents=1,
    )
    shared = expense(treasurer, amount=10000)
    j.link_expense(other, shared, 8000, by=treasurer)
    with pytest.raises(j.OverImputed):
        j.link_expense(granted, shared, 3000, by=treasurer)
    assert j.link_expense(granted, shared, 2000, by=treasurer).amount_cents == 2000


@pytest.mark.parametrize("amount", [0, -1, 1.5, True])
def test_import_imputat_no_valid(granted, treasurer, amount):
    with pytest.raises(j.GrantError):
        j.link_expense(granted, expense(treasurer), amount, by=treasurer)


def test_la_mateixa_despesa_dues_vegades_al_mateix_ajut(granted, treasurer):
    item = expense(treasurer)
    j.link_expense(granted, item, 1000, by=treasurer)
    with pytest.raises(j.GrantError):
        j.link_expense(granted, item, 1000, by=treasurer)


def test_ca_m09a_21_baixa_conservada_i_tornar_a_lligar(granted, treasurer):
    item = expense(treasurer)
    first = j.link_expense(granted, item, 1000, by=treasurer)
    removed = j.unlink_expense(first, by=treasurer)
    assert (removed.removed_by, removed.removed_at is not None) == (treasurer, True)
    with pytest.raises(j.GrantError):
        j.unlink_expense(first, by=treasurer)
    again = j.link_expense(granted, item, 1500, by=treasurer)
    assert GrantExpenseLink.objects.filter(expense=item).count() == 2
    assert again.removed_at is None


def test_nomes_un_ajut_concedit_i_justificat_sense_requeriment_no(granted, submitted, treasurer):  # noqa: F811
    item = expense(treasurer)
    link = j.link_expense(granted, item, 1000, by=treasurer)
    GrantApplication.objects.filter(pk=granted.pk).update(
        status="justified", justified_on=date(2027, 9, 1)
    )
    with pytest.raises(j.AlreadyJustified):
        j.link_expense(granted, expense(treasurer, number="F-2"), 1000, by=treasurer)
    with pytest.raises(j.AlreadyJustified):
        j.unlink_expense(link, by=treasurer)
    GrantApplication.objects.filter(pk=granted.pk).update(status="submitted")
    with pytest.raises(j.GrantError):
        j.link_expense(granted, item, 1000, by=treasurer)


@pytest.mark.parametrize("role", ["board", "secretary", None])
def test_lligar_demana_aj7_per_escriure(granted, treasurer, make_admin, role):
    other = make_admin(*([role] if role else []))  # la Junta, només consulta
    with pytest.raises(Http404):
        j.link_expense(granted, expense(treasurer), 1000, by=other)


def test_la_base_de_dades_rebutja_dues_actives_i_baixa_sense_qui(granted, treasurer):
    link = j.link_expense(granted, expense(treasurer), 1000, by=treasurer)
    with pytest.raises(IntegrityError), transaction.atomic():
        GrantExpenseLink.objects.create(
            application=granted, expense=link.expense, amount_cents=1, created_by=treasurer
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        GrantExpenseLink.objects.filter(pk=link.pk).update(removed_at=link.created_at)
