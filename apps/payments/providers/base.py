"""Adaptador del proveïdor de pagaments (M05a-8; decisió 043; T-M05a-03).

La resta de l'aplicació només crida aquesta interfície. Cap mètode rep ni retorna dades de
targeta ni cap IBAN: només imports en cèntims, identificadors del proveïdor i referències opaques.
La salvaguarda del nivell 1 (RN-M05a-11) és aquí i no a cada implementació.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from django.conf import settings

SANDBOX = "sandbox"
LIVE = "live"
ENVIRONMENTS = (SANDBOX, LIVE)

# Mètodes que passen pel proveïdor. La transferència i la domiciliació no hi passen (05b).
CARD = "card"
BIZUM = "bizum"
ORDER_METHODS = (CARD, BIZUM)

# Estats normalitzats d'una ordre: cada implementació hi tradueix els del seu proveïdor.
PAID = "paid"
DENIED = "denied"
PENDING = "pending"
EXPIRED = "expired"
ORDER_STATUSES = (PAID, DENIED, PENDING, EXPIRED)


class ProviderError(Exception):
    """Qualsevol error de l'adaptador."""


class ProviderNotConfigured(ProviderError):
    """No hi ha cap proveïdor configurat: no es pot cobrar res."""


class LiveChargesNotAllowed(ProviderError):
    """Entorn real sense autorització per cobrar (nivell 1, RN-M05a-11)."""


class NotSupported(ProviderError):
    """El proveïdor no ofereix aquesta operació o aquest mètode (vegeu `capabilities`)."""


class InvalidSignature(ProviderError):
    """La notificació no porta una firma vàlida: no se'n pot llegir res."""


class MalformedNotification(ProviderError):
    """La firma és vàlida però el contingut no es pot interpretar: va «a revisar»."""


@dataclass(frozen=True)
class OrderUrls:
    """On avisa el proveïdor (servidor a servidor) i on torna el navegador."""

    notification: str
    return_ok: str
    return_ko: str


@dataclass(frozen=True)
class ProviderOrder:
    external_id: str
    pay_url: str
    expires_at: datetime | None


@dataclass(frozen=True)
class OrderState:
    external_id: str
    status: str
    amount_cents: int
    currency: str


@dataclass(frozen=True)
class ProviderNotification:
    event_id: str
    order_id: str
    status: str
    amount_cents: int
    currency: str
    # Referència opaca d'una targeta guardada al proveïdor; mai el número.
    card_ref: str | None = None


@dataclass(frozen=True)
class ProviderRefund:
    external_id: str
    amount_cents: int
    status: str


@dataclass(frozen=True)
class Capabilities:
    card: bool
    bizum: bool
    tokenization: bool
    refund_bizum: bool
    embedded_field: bool


def ensure_charges_allowed() -> None:
    """RN-M05a-11: amb l'entorn real, cap cobrament sense `PAYMENTS_LIVE_CHARGES_ALLOWED`.
    Falla tancada: un entorn que no és «sandbox» es tracta com el real."""
    if settings.PAYMENTS_ENVIRONMENT == SANDBOX:
        return
    if settings.PAYMENTS_ENVIRONMENT == LIVE and settings.PAYMENTS_LIVE_CHARGES_ALLOWED:
        return
    raise LiveChargesNotAllowed


class PaymentProvider(ABC):
    """Interfície que implementa cada proveïdor. `code` l'identifica a les dades."""

    code: str

    @abstractmethod
    def capabilities(self) -> Capabilities:
        """Què ofereix. Les pantalles només mostren el que el proveïdor declara."""

    def create_order(
        self, charge, method: str, urls: OrderUrls, idempotency_key: UUID
    ) -> ProviderOrder:
        """Obre una ordre de cobrament per a un càrrec. Amb la mateixa clau d'idempotència,
        torna la mateixa ordre."""
        ensure_charges_allowed()
        if method not in ORDER_METHODS or not getattr(self.capabilities(), method):
            raise NotSupported(method)
        return self._create_order(charge, method, urls, idempotency_key)

    @abstractmethod
    def _create_order(
        self, charge, method: str, urls: OrderUrls, idempotency_key: UUID
    ) -> ProviderOrder: ...

    @abstractmethod
    def verify_notification(self, request) -> ProviderNotification:
        """Comprova la firma de la petició i en llegeix el contingut. `InvalidSignature` si
        la firma falta o no quadra; `MalformedNotification` si el contingut no s'entén."""

    @abstractmethod
    def get_order(self, external_id: str) -> OrderState:
        """Estat actual d'una ordre, per a la xarxa de seguretat del 05b."""

    @abstractmethod
    def refund(self, payment, amount_cents: int, idempotency_key: UUID) -> ProviderRefund:
        """Torna tot o part d'un pagament. No és un cobrament: no passa per la salvaguarda."""

    def start_card_setup(self, person, urls: OrderUrls) -> str:
        """Condicional (RN-M05a-10): adreça on el titular autentica la targeta."""
        raise NotSupported("tokenization")

    def charge_saved_card(self, charge, saved_card, idempotency_key: UUID) -> ProviderOrder:
        """Condicional: cobra amb una targeta guardada. És un cobrament: passa per la
        salvaguarda."""
        ensure_charges_allowed()
        if not self.capabilities().tokenization:
            raise NotSupported("tokenization")
        return self._charge_saved_card(charge, saved_card, idempotency_key)

    def _charge_saved_card(self, charge, saved_card, idempotency_key: UUID) -> ProviderOrder:
        raise NotSupported("tokenization")
