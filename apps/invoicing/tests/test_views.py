"""«Les meves factures» (T-M09-21; MG10, propi): només les factures emeses a nom de la persona del
compte personal. Només dades inventades."""

import datetime

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.activities.tests.helpers import a_person, a_personal_account
from apps.core.tests.conftest import main_of
from apps.invoicing.models import Invoice

pytestmark = pytest.mark.django_db


def invoice(person, number, status=Invoice.Status.ISSUED, **extra):
    return Invoice.objects.create(
        series="F", number=number, issued_on=datetime.date(2027, 3, 1), customer_person=person,
        base_cents=9000, tax_cents=0, total_cents=9000, status=status, **extra,
    )  # fmt: skip


def test_t_m09_21_only_my_issued_invoices(login_as):
    account = a_personal_account(a_person("Sòcia"))
    invoice(account.person, "F-2027-0001")
    invoice(account.person, "", status=Invoice.Status.FAILED)
    invoice(a_person("Una altra"), "F-2027-0002")
    client = login_as(account, AREA_PERSONAL)
    html = main_of(client.get(reverse("invoicing:my_invoices")).content.decode())
    assert "F-2027-0001" in html and "90,00" in html
    assert "F-2027-0002" not in html  # d'una altra persona
    assert "1 factura, la més recent primer" in html


def test_without_a_personal_session_it_goes_to_the_login(client):
    response = client.get(reverse("invoicing:my_invoices"))
    assert response.status_code == 302 and "/entrar/" in response["Location"]
