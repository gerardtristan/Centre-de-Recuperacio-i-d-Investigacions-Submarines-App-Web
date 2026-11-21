"""Adaptador de facturació (M09-8, T-M09-18; RN-M09-17 i 33). El 09 no numera mai: demana la
factura al servei homologat (Verifactu) a través d'aquest adaptador i en desa el número, el PDF i
el QR. Ara només hi ha el servei fictici. Quin servei real: P-293 (cap connexió sense el sí
escrit del propietari i dades només a la UE, 035)."""

from dataclasses import dataclass, field

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ProviderError(Exception):
    """El servei de facturació no ha respost o ha rebutjat la petició (L-M09-06)."""


@dataclass(frozen=True)
class InvoiceLineData:
    description: str
    quantity: int
    unit_cents: int
    total_cents: int


@dataclass(frozen=True)
class InvoiceData:
    """El que s'envia al servei: sèrie, client i línies; mai cap IBAN ni dada de salut."""

    series: str
    customer_name: str
    customer_tax_id: str
    base_cents: int
    tax_cents: int
    total_cents: int
    lines: tuple[InvoiceLineData, ...] = field(default_factory=tuple)
    rectifies_number: str = ""


@dataclass(frozen=True)
class IssuedInvoice:
    number: str
    pdf: bytes
    qr: str
    provider_ref: str


class InvoicingProvider:
    """Contracte: `issue` i `rectify` tornen una `IssuedInvoice` o llancen `ProviderError`;
    `status` torna l'estat de la factura al servei."""

    code = ""

    def issue(self, data: InvoiceData) -> IssuedInvoice:  # pragma: no cover - contracte
        raise NotImplementedError

    def rectify(self, data: InvoiceData) -> IssuedInvoice:  # pragma: no cover - contracte
        raise NotImplementedError

    def status(self, provider_ref: str) -> str:  # pragma: no cover - contracte
        raise NotImplementedError


def get_provider() -> InvoicingProvider:
    """El servei configurat (`INVOICING_PROVIDER`). Només n'hi ha el fictici (P-293)."""
    from .fake import FakeInvoicingProvider

    code = getattr(settings, "INVOICING_PROVIDER", "fake")
    if code != FakeInvoicingProvider.code:
        raise ImproperlyConfigured(f"Servei de facturació desconegut: {code}")
    return FakeInvoicingProvider()
