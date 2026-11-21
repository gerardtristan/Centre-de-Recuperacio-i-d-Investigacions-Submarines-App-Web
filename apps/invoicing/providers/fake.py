"""Servei de facturació fictici (T-M09-18): per a les proves i el desenvolupament, sense xarxa.
Numera cada sèrie de manera correlativa a la memòria del procés i deixa forçar un salt, un número
repetit o una fallada per provar els controls del 09 (CA-M09-17, L-M09-06)."""

import hashlib

from . import InvoiceData, InvoicingProvider, IssuedInvoice, ProviderError


class FakeInvoicingProvider(InvoicingProvider):
    code = "fake"
    # Estat compartit del servei fictici (com ho seria al servei real), per sèrie.
    counters: dict[str, int] = {}
    issued: dict[str, str] = {}
    next_skip = 0  # quants números se salta la propera factura
    next_repeat = False  # la propera factura repeteix l'últim número
    fail_next = 0  # quantes peticions fallen a partir d'ara

    @classmethod
    def reset(cls) -> None:
        cls.counters, cls.issued = {}, {}
        cls.next_skip, cls.next_repeat, cls.fail_next = 0, False, 0

    def _number(self, series: str) -> str:
        cls = type(self)
        if cls.fail_next:
            cls.fail_next -= 1
            raise ProviderError("Servei fictici: no respon.")
        last = cls.counters.get(series, 0)
        n = last if cls.next_repeat and last else last + 1 + cls.next_skip
        cls.next_skip, cls.next_repeat = 0, False
        cls.counters[series] = max(n, last)
        return f"{series}-{n:06d}"

    def _issue(self, data: InvoiceData) -> IssuedInvoice:
        if data.total_cents != data.base_cents + data.tax_cents:
            raise ProviderError("Servei fictici: el total no quadra.")
        number = self._number(data.series)
        ref = f"FAKE-{number}"
        type(self).issued[ref] = "registered"
        digest = hashlib.sha256(f"{number}:{data.total_cents}".encode()).hexdigest()[:16]
        pdf = f"%PDF-1.4 factura ficticia {number}".encode()
        return IssuedInvoice(
            number=number, pdf=pdf, qr=f"fake-verifactu:{digest}", provider_ref=ref
        )

    def issue(self, data: InvoiceData) -> IssuedInvoice:
        return self._issue(data)

    def rectify(self, data: InvoiceData) -> IssuedInvoice:
        if not data.rectifies_number:
            raise ProviderError("Servei fictici: una rectificativa diu quina factura rectifica.")
        return self._issue(data)

    def status(self, provider_ref: str) -> str:
        return type(self).issued.get(provider_ref, "unknown")
