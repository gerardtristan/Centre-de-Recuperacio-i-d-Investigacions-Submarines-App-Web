"""T-M09-18: proves de contracte de l'adaptador de facturació amb el servei fictici. Sense xarxa
ni base de dades."""

import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.invoicing.providers import (
    InvoiceData,
    InvoiceLineData,
    InvoicingProvider,
    IssuedInvoice,
    ProviderError,
    get_provider,
)
from apps.invoicing.providers.fake import FakeInvoicingProvider


@pytest.fixture(autouse=True)
def fresh():
    FakeInvoicingProvider.reset()
    yield
    FakeInvoicingProvider.reset()


def data(series="F", total=6000, **extra):
    line = InvoiceLineData(
        description="Sortida inventada", quantity=1, unit_cents=total, total_cents=total
    )
    fields = {
        "series": series,
        "customer_name": "Persona Inventada",
        "customer_tax_id": "",
        "base_cents": total,
        "tax_cents": 0,
        "total_cents": total,
        "lines": (line,),
    }
    return InvoiceData(**{**fields, **extra})


def test_el_servei_configurat_es_el_fictici_i_compleix_el_contracte():
    provider = get_provider()
    assert isinstance(provider, InvoicingProvider)
    issued = provider.issue(data())
    assert isinstance(issued, IssuedInvoice)
    assert (issued.number, issued.provider_ref) == ("F-000001", "FAKE-F-000001")
    assert issued.pdf.startswith(b"%PDF")
    assert issued.qr.startswith("fake-verifactu:")
    assert provider.status(issued.provider_ref) == "registered"
    assert provider.status("FAKE-NO") == "unknown"


def test_numeracio_correlativa_per_serie():
    provider = get_provider()
    assert [provider.issue(data()).number for _ in range(2)] == ["F-000001", "F-000002"]
    rectified = provider.rectify(data(series="R", rectifies_number="F-000001"))
    assert rectified.number == "R-000001"


def test_es_poden_forcar_un_salt_un_numero_repetit_i_una_fallada():
    provider = get_provider()
    provider.issue(data())
    FakeInvoicingProvider.next_skip = 1
    assert provider.issue(data()).number == "F-000003"
    FakeInvoicingProvider.next_repeat = True
    assert provider.issue(data()).number == "F-000003"
    FakeInvoicingProvider.fail_next = 1
    with pytest.raises(ProviderError):
        provider.issue(data())
    assert provider.issue(data()).number == "F-000004"


def test_errors_de_contracte():
    provider = get_provider()
    with pytest.raises(ProviderError):
        provider.issue(data(base_cents=1))  # el total no quadra
    with pytest.raises(ProviderError):
        provider.rectify(data(series="R"))  # sense la factura que rectifica


def test_un_servei_desconegut_no_es_fa_servir(settings):
    settings.INVOICING_PROVIDER = "verifactu-real"
    with pytest.raises(ImproperlyConfigured):
        get_provider()
