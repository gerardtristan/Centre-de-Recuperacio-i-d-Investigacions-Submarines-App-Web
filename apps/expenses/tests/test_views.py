"""Pantalles de les despeses (T-M09-06, part sense fitxer, i T-M09-15; CA-M09-01; MG1 i MG2). Les
rutes encara no són a `apps.accounts.admin_urls` (torn del nucli): les proves fan servir
`apps.expenses.tests.urls`. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Department, OutgoingEmail, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.expenses.models import Expense, ExpenseCategory, Supplier

pytestmark = [pytest.mark.django_db, pytest.mark.urls("apps.expenses.tests.urls")]
R = Role.Code


@pytest.fixture
def as_role(login_as, make_admin):  # noqa: F811
    def login(role):
        account = make_admin(role)
        account.notification_email = "tresoreria@example.org"
        account.save()
        return login_as(account, AREA_ADMIN)

    return login


def data(**extra):
    return {
        "supplier": Supplier.objects.create(name="Nàutica Inventada SL").pk,
        "invoice_number": "F-2027-1",
        "invoice_date": "2027-06-10",
        "category": ExpenseCategory.objects.get(name="Embarcació").pk,
        "description": "Sortida a les Medes",
        "amount": "250,50",
        "tax": "",
        "department": Department.objects.get(name="General").pk,
        **extra,
    }


def test_ca_m09_01_a_new_expense_is_without_invoice_and_listed(as_role):
    client = as_role(R.TREASURER)
    assert "Registra una despesa" in main_of(
        client.get(reverse("administration:expense_new")).content.decode()
    )
    response = client.post(reverse("administration:expense_new"), data(), follow=True)
    expense = Expense.objects.get()
    assert (expense.amount_cents, expense.tax_cents, expense.status) == (25050, None, "to_pay")
    html = main_of(response.content.decode())
    assert "Despeses sense factura" in html and "Sortida a les Medes" in html
    assert "250,50" in html and "Despesa registrada" in html
    assert OutgoingEmail.objects.exists()  # l'avís de la despesa sense factura


def test_invalid_data_shows_the_errors_and_saves_nothing(as_role):
    response = as_role(R.TREASURER).post(
        reverse("administration:expense_new"), data(department="", amount="-1")
    )
    assert response.status_code == 200 and not Expense.objects.exists()
    assert "Aquest camp és obligatori." in response.content.decode()


@pytest.mark.parametrize("role", [R.SECRETARY, R.INSTRUCTOR])
def test_without_mg1_or_mg2_not_found(as_role, role):
    client = as_role(role)
    assert client.get(reverse("administration:expense_new")).status_code == 404
    assert client.get(reverse("administration:expenses_without_invoice")).status_code == 404


def test_the_courses_manager_cannot_record_without_an_activity(as_role):
    # MG1 amb l'abast «les seves activitats»: sense repartiment, el servei respon «no trobat».
    response = as_role(R.COURSES_MANAGER).post(reverse("administration:expense_new"), data())
    assert response.status_code == 404 and not Expense.objects.exists()
