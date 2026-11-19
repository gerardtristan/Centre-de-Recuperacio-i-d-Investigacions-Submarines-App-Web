"""Adaptador del proveïdor de pagaments (M05a-8; decisió 043; T-M05a-03).

La resta de l'aplicació només crida aquesta interfície. Cap mètode rep ni retorna dades de
targeta ni cap IBAN: només imports en cèntims, identificadors del proveïdor i referències opaques.
La salvaguarda del nivell 1 (RN-M05a-11; `apps/payments/guards.py`) la criden aquests mètodes i no
cada implementació.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

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
    # La referència de la transacció al proveïdor, si en dona: la liquidació pot venir amb
    # aquesta i no amb la nostra ordre (T-M05b-31).
    transaction_id: str = ""


@dataclass(frozen=True)
class ProviderNotification:
    event_id: str
    order_id: str
    status: str
    amount_cents: int
    currency: str
    # Referència opaca d'una targeta guardada al proveïdor; mai el número.
    card_ref: str | None = None
    transaction_id: str = ""  # com a `OrderState`


@dataclass(frozen=True)
class ProviderRefund:
    external_id: str
    amount_cents: int
    status: str


@dataclass(frozen=True)
class SettledOperation:
    """Un cobrament dins d'un abonament: l'ordre (la referència del pagament), l'import, la
    comissió si el proveïdor la detalla i la referència de la seva transacció si en dona. Una de
    les dues referències pot ser buida (T-M05b-31)."""

    order_id: str
    amount_cents: int
    fee_cents: int | None = None
    transaction_id: str = ""


@dataclass(frozen=True)
class ProviderSettlementReport:
    """Un abonament agrupat del proveïdor al banc (P-M05b-H; RN-T21). El format real és
    [A verificar: P-45 punt 9]: cada implementació hi tradueix el seu."""

    external_id: str
    settled_on: date
    gross_cents: int
    fees_cents: int
    net_cents: int
    operations: tuple[SettledOperation, ...]


@dataclass(frozen=True)
class ProviderCard:
    """Una targeta guardada al proveïdor (RN-M05a-10): la seva referència opaca i el que es
    mostra, si el proveïdor ho torna [A verificar: P-45 punt 6]. Mai el número ni el codi."""

    card_ref: str
    last4: str
    expiry_month: int | None = None
    expiry_year: int | None = None


@dataclass(frozen=True)
class Capabilities:
    card: bool
    bizum: bool
    tokenization: bool
    refund_bizum: bool
    embedded_field: bool


def _guard(operation: str) -> None:
    from ..guards import ensure_charges_allowed  # guards importa aquest mòdul

    ensure_charges_allowed(operation)


class PaymentProvider(ABC):
    """Interfície que implementa cada proveïdor. `code` l'identifica a les dades."""

    code: str
    # Adreces des d'on el proveïdor envia les notificacions, si en publica la llista
    # (CA-M05a-10). Buida: no es comprova l'origen, només la firma.
    allowed_ips: tuple[str, ...] = ()

    @abstractmethod
    def capabilities(self) -> Capabilities:
        """Què ofereix. Les pantalles només mostren el que el proveïdor declara."""

    def create_order(
        self, charge, method: str, urls: OrderUrls, idempotency_key: UUID
    ) -> ProviderOrder:
        """Obre una ordre de cobrament per a un càrrec. Amb la mateixa clau d'idempotència,
        torna la mateixa ordre."""
        _guard("create_order")
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

    def list_settlements(self, since: date) -> list[ProviderSettlementReport]:
        """Els abonaments al banc des de `since`, inclòs (P-M05b-H). Si el proveïdor no en
        dona, `NotSupported`: el tresorer casa la línia del banc per període (RN-T21)."""
        raise NotSupported("settlements")

    def start_card_setup(self, person, urls: OrderUrls) -> ProviderOrder:
        """Condicional (RN-M05a-10): obre l'autenticació inicial del titular per guardar una
        targeta (per exemple, una autorització de 0 € amb 3DS [A verificar: P-45 punt 6]) i
        torna l'ordre amb l'adreça on el titular l'escriu. No és cap cobrament: guardar-la és
        recollir el mètode, que el nivell 1 permet. La targeta arriba amb la notificació."""
        if not self.capabilities().tokenization:
            raise NotSupported("tokenization")
        return self._start_card_setup(person, urls)

    def _start_card_setup(self, person, urls: OrderUrls) -> ProviderOrder:
        raise NotSupported("tokenization")

    def get_card_setup(self, external_id: str) -> ProviderCard:
        """La targeta que ha guardat una autenticació acabada, consultada al proveïdor (servidor a
        servidor): mai la que digui el navegador."""
        raise NotSupported("tokenization")

    def charge_saved_card(self, charge, saved_card, idempotency_key: UUID) -> ProviderOrder:
        """Condicional: cobra amb una targeta guardada, sense el titular. És un cobrament: passa
        per la salvaguarda. `pay_url` buit: el resultat arriba amb la notificació; ple: el banc
        demana que el titular s'autentiqui en aquesta adreça (RN-M05b-20)."""
        _guard("charge_saved_card")
        if not self.capabilities().tokenization:
            raise NotSupported("tokenization")
        return self._charge_saved_card(charge, saved_card, idempotency_key)

    def _charge_saved_card(self, charge, saved_card, idempotency_key: UUID) -> ProviderOrder:
        raise NotSupported("tokenization")

    def saved_card_order_id(self, idempotency_key: UUID) -> str:
        """L'identificador que tindrà l'ordre de `charge_saved_card` amb aquesta clau, per desar-lo
        a l'intent abans de cobrar: la notificació el troba encara que arribi abans que la resposta.
        Sense, no es cobra cap targeta guardada [A verificar: P-45 punt 6]."""
        raise NotSupported("tokenization")
