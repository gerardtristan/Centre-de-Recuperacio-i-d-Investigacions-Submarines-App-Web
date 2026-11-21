"""«Les meves factures» al navegador (T-M09-21; MG10, propi): un soci veu només les seves factures.
Ruta encara no inclosa (torn del nucli): `apps.expenses.tests.urls`. Pantalles a 1280, 390 i 320
px. Només dades inventades."""

import datetime

import pytest
from playwright.sync_api import expect

from apps.core.models import Person
from apps.invoicing.models import Invoice

from .test_carnet_079 import login_personal

pytestmark = [pytest.mark.e2e, pytest.mark.urls("apps.expenses.tests.urls")]


def invoice(person, number):
    return Invoice.objects.create(
        series="F", number=number, issued_on=datetime.date(2027, 3, 1), customer_person=person,
        base_cents=9000, tax_cents=0, total_cents=9000, status=Invoice.Status.ISSUED,
    )  # fmt: skip


def test_a_member_sees_only_their_invoices(page, live_server, builder, member, review):
    account = builder.personal(member.person)
    invoice(member.person, "F-2027-0001")
    invoice(Person.objects.create(first_name="Altra", origin="web"), "F-2027-0002")
    login_personal(page, live_server.url, account)
    page.goto(f"{live_server.url}/socis/factures/")
    expect(page.get_by_role("heading", name="Les meves factures")).to_be_visible()
    table = page.get_by_role("table", name="1 factura, la més recent primer")
    expect(table).to_contain_text("F-2027-0001")
    expect(table).not_to_contain_text("F-2027-0002")
    review("meves-factures")
