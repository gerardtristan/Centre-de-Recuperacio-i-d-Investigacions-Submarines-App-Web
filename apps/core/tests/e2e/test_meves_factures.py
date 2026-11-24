"""«Les meves factures» al navegador (T-M09-21 i 21b; MG10, propi): un soci veu només les seves
factures i en pot descarregar el PDF.
Pantalles a 1280, 390 i 320 px. Només dades inventades."""

import datetime

import pytest
from playwright.sync_api import expect

from apps.core import files
from apps.core.models import Person, PrivateFile
from apps.invoicing.models import Invoice

from .test_carnet_079 import login_personal

pytestmark = pytest.mark.e2e


def invoice(person, number, **extra):
    return Invoice.objects.create(
        series="F", number=number, issued_on=datetime.date(2027, 3, 1), customer_person=person,
        base_cents=9000, tax_cents=0, total_cents=9000, status=Invoice.Status.ISSUED, **extra,
    )  # fmt: skip


def pdf(person, number):
    """T-M09-21b: el PDF desat xifrat, com el desa la T-M09-19 (contingut inventat)."""
    return files.store(f"%PDF-1.4 {number}".encode(), owner=person,
                       kind=PrivateFile.Kind.ISSUED_INVOICE, content_type="application/pdf",
                       download_name=f"factura-{number}.pdf")  # fmt: skip


def test_a_member_sees_only_their_invoices(page, live_server, builder, member, review):
    account = builder.personal(member.person)
    invoice(member.person, "F-2027-0001", pdf_file=pdf(member.person, "F-2027-0001"))
    invoice(Person.objects.create(first_name="Altra", origin="web"), "F-2027-0002")
    login_personal(page, live_server.url, account)
    page.goto(f"{live_server.url}/socis/factures/")
    expect(page.get_by_role("heading", name="Les meves factures")).to_be_visible()
    table = page.get_by_role("table", name="1 factura, la més recent primer")
    expect(table).to_contain_text("F-2027-0001")
    expect(table).not_to_contain_text("F-2027-0002")
    expect(table.get_by_role("link", name="Descarrega la factura F-2027-0001")).to_be_visible()
    review("meves-factures")
