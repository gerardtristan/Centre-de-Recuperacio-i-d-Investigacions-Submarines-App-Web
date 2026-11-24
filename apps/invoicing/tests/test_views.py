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


def test_t_m09_21b_i_download_my_pdf_and_not_another_persons(login_as):
    from apps.core import files
    from apps.core.models import PrivateFile

    account = a_personal_account(a_person("Sòcia"))
    other = a_person("Una altra")

    def stored(person, number):
        return files.store(f"%PDF-1.4 {number}".encode(), owner=person,
                           kind=PrivateFile.Kind.ISSUED_INVOICE, content_type="application/pdf",
                           download_name=f"factura-{number}.pdf")  # fmt: skip

    mine = invoice(account.person, "F-2027-0001", pdf_file=stored(account.person, "F-2027-0001"))
    invoice(account.person, "F-2027-0003")  # encara sense PDF
    theirs = stored(other, "F-2027-0002")
    client = login_as(account, AREA_PERSONAL)
    html = main_of(client.get(reverse("invoicing:my_invoices")).content.decode())
    assert html.count(">Descarrega<") == 1 and "Encara no disponible" in html
    response = client.get(reverse("core:private_file", args=[mine.pdf_file_id]))
    assert response.content == b"%PDF-1.4 F-2027-0001"
    assert "attachment" in response["Content-Disposition"]
    assert client.get(reverse("core:private_file", args=[theirs.pk])).status_code == 404
