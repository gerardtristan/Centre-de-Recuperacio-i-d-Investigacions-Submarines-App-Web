"""T-M09-19: el PDF de la factura emesa, desat xifrat (ISSUED_INVOICE; 051; P-592). El PDF el
torna el servei (aquí, el fictici). Només dades inventades."""

import pytest
from django.core.files.storage import storages

from apps.core import files
from apps.core.models import AuditEntry, PrivateFile
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.invoicing import services
from apps.invoicing.models import Invoice
from apps.invoicing.providers.fake import FakeInvoicingProvider
from apps.invoicing.tests.test_invoices import COMPANY, deliver_last, pay

pytestmark = pytest.mark.django_db
LINES = [("Lloguer de la sala", 1, 12000)]


@pytest.fixture(autouse=True)
def enabled(monkeypatch):
    FakeInvoicingProvider.reset()
    monkeypatch.setattr(services, "enabled_kinds", lambda on=None: {"enrolment"})
    yield
    FakeInvoicingProvider.reset()


def raw(file):
    with storages["private"].open(file.storage_key, "rb") as handle:
        return handle.read()


def test_the_pdf_of_a_paid_charge_is_stored_encrypted_for_the_customer(make_admin):  # noqa: F811
    charge = pay()
    deliver_last()
    invoice = Invoice.objects.get()
    file = invoice.pdf_file
    assert (file.kind, file.owner, file.content_type, file.download_name) == (
        PrivateFile.Kind.ISSUED_INVOICE, charge.person, "application/pdf", "factura-F-000001.pdf",
    )  # fmt: skip
    expected = b"%PDF-1.4 factura ficticia F-000001"
    assert raw(file) != expected  # xifrat a l'emmagatzematge
    assert files.open_decrypted(make_admin("treasurer"), file) == expected  # MG9


def test_a_company_invoice_belongs_to_who_requested_it(make_admin):  # noqa: F811
    treasurer = make_admin("treasurer")
    invoice = services.issue_manual(**COMPANY, lines=LINES, by=treasurer)
    assert invoice.pdf_file.owner == treasurer.person  # P-592


def test_a_failed_invoice_gets_its_pdf_when_it_is_retried(make_admin):  # noqa: F811
    treasurer = make_admin("treasurer")
    FakeInvoicingProvider.fail_next = 1
    invoice = services.issue_manual(**COMPANY, lines=LINES, by=treasurer)
    assert (invoice.status, invoice.pdf_file) == (Invoice.Status.FAILED, None)
    assert services.retry_failed() == 1
    invoice.refresh_from_db()
    assert invoice.pdf_file.owner == treasurer.person


def test_if_the_pdf_cannot_be_stored_the_invoice_stays_issued(make_admin, monkeypatch):  # noqa: F811
    def broken(*args, **kwargs):
        raise OSError("emmagatzematge no disponible")

    monkeypatch.setattr(files, "store", broken)
    invoice = services.issue_manual(**COMPANY, lines=LINES, by=make_admin("treasurer"))
    invoice.refresh_from_db()
    assert (invoice.status, invoice.number, invoice.pdf_file) == ("issued", "F-000001", None)
    entry = AuditEntry.objects.get(action=services.PDF_NOT_STORED)
    assert "no disponible" in entry.details["error"]


def test_without_an_owner_nothing_is_stored(monkeypatch):
    monkeypatch.setattr(services, "_pdf_owner", lambda invoice: None)
    pay()
    deliver_last()
    assert Invoice.objects.get().pdf_file is None
    assert AuditEntry.objects.filter(action=services.PDF_NOT_STORED).exists()
