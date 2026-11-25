"""Pantalles de les despeses (T-M09-06, part sense fitxer, i T-M09-15; CA-M09-01; MG1 i MG2).
Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Department, OutgoingEmail, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.expenses.models import Expense, ExpenseCategory, Supplier

pytestmark = pytest.mark.django_db
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


def test_dx107_ring_by_department_filter_and_total(as_role):
    # Gastos (T-DX-107): l'anell per departament és de tota la llista; el filtre tria les files i
    # el total és el de les files que es veuen.
    client = as_role(R.TREASURER)
    other = Department.objects.create(name="Departament inventat")
    client.post(reverse("administration:expense_new"), data())
    client.post(
        reverse("administration:expense_new"),
        data(
            invoice_number="F-2027-2", description="Compressor", amount="100", department=other.pk
        ),
    )
    url = reverse("administration:expenses_without_invoice")
    html = main_of(client.get(url).content.decode())
    assert "gastos-anell" in html and "350,50" in html  # total de les dues
    assert "Registra una despesa" in html
    html = main_of(client.get(url, {"departament": other.pk}).content.decode())
    assert "Compressor" in html and "Sortida a les Medes" not in html
    assert "Total del departament" in html and "100,00" in html
    html = main_of(client.get(url, {"departament": "x"}).content.decode())  # valor fora de llista
    assert "Compressor" in html and "Sortida a les Medes" in html


def test_without_mg2_the_new_expense_goes_to_its_documents_not_to_a_404(as_role):
    """Trobat a l'e2e de CA-M09-27 (T-M09-06): el president (MG1, sense MG2) que registrava una
    despesa anava a «Despeses sense factura», que no pot veure (404), i no arribava a adjuntar-hi
    la factura; i «Documents de la despesa» li ensenyava l'enllaç a aquella llista."""
    client = as_role(R.PRESIDENT)
    response = client.post(reverse("administration:expense_new"), data())
    expense = Expense.objects.get()
    documents = reverse("administration:expense_documents", args=[expense.pk])
    assert response.status_code == 302 and response.url == documents
    html = main_of(client.get(documents).content.decode())
    assert reverse("administration:expenses_without_invoice") not in html
    assert client.get(reverse("administration:expenses_without_invoice")).status_code == 404


def test_with_mg2_the_documents_page_links_back_to_the_list(as_role):
    client = as_role(R.TREASURER)
    client.post(reverse("administration:expense_new"), data())
    expense = Expense.objects.get()
    html = main_of(
        client.get(reverse("administration:expense_documents", args=[expense.pk])).content.decode()
    )
    assert reverse("administration:expenses_without_invoice") in html


def test_with_mg2_read_only_the_documents_page_also_links_back_to_the_list(as_role, monkeypatch):
    """Si MG2 admetés «Cons.» (avui el catàleg només li permet «tot»), la llista s'obriria i la
    redirecció hi portaria: l'enllaç de tornada també hi ha de ser (revisió de la #595)."""
    import dataclasses

    from apps.core import permissions
    from apps.core.models import RolePermission
    from apps.core.permission_catalog import SCOPE_ALL, SCOPE_READ

    pay = dataclasses.replace(
        permissions.CATALOG["expenses.pay"], allowed_scopes=(SCOPE_ALL, SCOPE_READ)
    )
    monkeypatch.setattr(permissions, "CATALOG", {**permissions.CATALOG, "expenses.pay": pay})

    RolePermission.objects.update_or_create(
        role=Role.objects.get(code=R.PRESIDENT), permission_code="expenses.pay",
        defaults={"scope": SCOPE_READ},
    )  # fmt: skip
    client = as_role(R.PRESIDENT)
    response = client.post(reverse("administration:expense_new"), data())
    assert response.url == reverse("administration:expenses_without_invoice")
    expense = Expense.objects.get()
    html = main_of(
        client.get(reverse("administration:expense_documents", args=[expense.pk])).content.decode()
    )
    assert reverse("administration:expenses_without_invoice") in html
