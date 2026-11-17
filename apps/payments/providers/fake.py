"""Proveïdor fals: sense xarxa, per a les proves i per al desenvolupament local (T-M05a-03).
Obre ordres, signa les notificacions amb HMAC i rebutja les que no quadren. Només arrenca amb
l'entorn de proves. Les ordres viuen en memòria, dins del procés."""

import hashlib
import hmac
import json
import logging
import urllib.request
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from . import base

# Valor únic de les credencials de proves del projecte (CLAUDE.md): no protegeix res.
SIGNING_KEY = "contrasenya-de-proves-1954"
SIGNATURE_HEADER = "X-Fake-Signature"
BIZUM_MINUTES = 15
# La pàgina de pagament de prova (T-M05b-04): `views.fake_pay_view`.
PAY_PATH = "/pagaments/prova/"
# Ordres per guardar una targeta: una autorització de 0 € (format [A verificar: P-45 punt 6]).
SETUP_PREFIX = "fake-setup-"

logger = logging.getLogger(__name__)
_orders: dict[str, base.OrderState] = {}
_urls: dict[str, base.OrderUrls] = {}
# Quan caduca cada ordre de Bizum que el titular no confirma a l'app del banc.
_bizum_expiry: dict[str, datetime] = {}
# Els abonaments al banc que ha fet el proveïdor (`settle`), en l'ordre en què els ha fet.
_settlements: list[base.ProviderSettlementReport] = []
# La targeta que ha guardat cada autenticació acabada.
_cards: dict[str, base.ProviderCard] = {}
# Targetes amb què el banc demana autenticació per cobrar (RN-M05b-20; `require_authentication`).
_authentication: set[str] = set()


def sign(body: bytes, key: str = SIGNING_KEY) -> str:
    return hmac.new(key.encode(), body, hashlib.sha256).hexdigest()


def reset() -> None:
    """Oblida les ordres i els abonaments en memòria (entre proves)."""
    _orders.clear()
    _urls.clear()
    _bizum_expiry.clear()
    _settlements.clear()
    _cards.clear()
    _authentication.clear()


class FakeProvider(base.PaymentProvider):
    code = "fake"

    def __init__(self):
        if settings.PAYMENTS_ENVIRONMENT != base.SANDBOX:
            raise ImproperlyConfigured("El proveïdor fals no es pot fer servir amb l'entorn real.")

    def capabilities(self) -> base.Capabilities:
        return base.Capabilities(
            card=True, bizum=True, tokenization=True, refund_bizum=True, embedded_field=False
        )

    def _create_order(self, charge, method, urls, idempotency_key: UUID) -> base.ProviderOrder:
        external_id = f"fake-{idempotency_key.hex}"
        _orders.setdefault(
            external_id,
            base.OrderState(external_id, base.PENDING, charge.amount_cents, charge.currency),
        )
        _urls.setdefault(external_id, urls)
        expires_at = (
            timezone.now() + timedelta(minutes=BIZUM_MINUTES) if method == base.BIZUM else None
        )
        if expires_at:
            expires_at = _bizum_expiry.setdefault(external_id, expires_at)
        return base.ProviderOrder(
            external_id=external_id,
            pay_url=f"{settings.PUBLIC_SITE_URL}{PAY_PATH}{external_id}/",
            expires_at=expires_at,
        )

    def _start_card_setup(self, person, urls) -> base.ProviderOrder:
        external_id = f"{SETUP_PREFIX}{uuid4().hex}"
        _orders[external_id] = base.OrderState(external_id, base.PENDING, 0, "EUR")
        _urls[external_id] = urls
        pay_url = f"{settings.PUBLIC_SITE_URL}{PAY_PATH}{external_id}/"
        return base.ProviderOrder(external_id=external_id, pay_url=pay_url, expires_at=None)

    def _charge_saved_card(self, charge, saved_card, idempotency_key: UUID) -> base.ProviderOrder:
        """Pagament directe amb la targeta guardada: l'ordre queda oberta fins a la notificació.
        Si el banc demana autenticació, l'ordre porta l'adreça on el titular s'ha d'autenticar
        (format [A verificar: P-45 punt 6])."""
        external_id = f"fake-{idempotency_key.hex}"
        _orders.setdefault(
            external_id,
            base.OrderState(external_id, base.PENDING, charge.amount_cents, charge.currency),
        )
        needs_auth = saved_card.provider_card_id in _authentication
        pay_url = f"{settings.PUBLIC_SITE_URL}{PAY_PATH}{external_id}/" if needs_auth else ""
        return base.ProviderOrder(external_id=external_id, pay_url=pay_url, expires_at=None)

    def get_card_setup(self, external_id: str) -> base.ProviderCard:
        try:
            return _cards[external_id]
        except KeyError:
            raise base.ProviderError(f"Cap targeta guardada amb l'ordre {external_id}") from None

    def get_order(self, external_id: str) -> base.OrderState:
        try:
            order = _orders[external_id]
        except KeyError:
            raise base.ProviderError(f"Ordre desconeguda: {external_id}") from None
        # Un Bizum sense confirmar caduca sol. Com ho fa el proveïdor real és P-45 punt 13.
        expiry = _bizum_expiry.get(external_id)
        if order.status == base.PENDING and expiry and timezone.now() >= expiry:
            order = _orders[external_id] = base.OrderState(
                external_id, base.EXPIRED, order.amount_cents, order.currency
            )
        return order

    def is_bizum(self, external_id: str) -> bool:
        return external_id in _bizum_expiry

    def verify_notification(self, request) -> base.ProviderNotification:
        body = request.body
        signature = request.headers.get(SIGNATURE_HEADER, "")
        # En bytes: `compare_digest` no accepta text amb caràcters que no siguin ASCII.
        if not signature or not hmac.compare_digest(signature.encode(), sign(body).encode()):
            raise base.InvalidSignature
        try:
            data = json.loads(body)
            notification = base.ProviderNotification(
                event_id=str(data["event_id"]),
                order_id=str(data["order_id"]),
                status=str(data["status"]),
                amount_cents=data["amount_cents"],
                currency=str(data["currency"]),
                card_ref=data.get("card_ref"),
            )
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            raise base.MalformedNotification(type(error).__name__) from None
        amount = notification.amount_cents
        # Només l'autorització per guardar una targeta pot ser de 0 €.
        least = 0 if notification.order_id.startswith(SETUP_PREFIX) else 1
        if (
            notification.status not in base.ORDER_STATUSES
            or isinstance(amount, bool)
            or not isinstance(amount, int)
            or amount < least
        ):
            raise base.MalformedNotification("contingut")
        return notification

    def refund(self, payment, amount_cents: int, idempotency_key: UUID) -> base.ProviderRefund:
        if isinstance(amount_cents, bool) or not isinstance(amount_cents, int):
            raise ValueError("L'import ha de ser un enter en cèntims.")
        if not 0 < amount_cents <= payment.amount_cents:
            raise ValueError("L'import de la devolució ha de ser positiu i no superar el pagat.")
        return base.ProviderRefund(
            external_id=f"fake-refund-{idempotency_key.hex}",
            amount_cents=amount_cents,
            status="done",
        )

    def list_settlements(self, since) -> list[base.ProviderSettlementReport]:
        return [report for report in _settlements if report.settled_on >= since]

    # --- El que faria el proveïdor de veritat: només per a proves i desenvolupament ---

    def notification(
        self,
        external_id: str,
        status: str,
        *,
        event_id: str | None = None,
        key: str = SIGNING_KEY,
        card: base.ProviderCard | None = None,
    ) -> tuple[bytes, dict]:
        """Cos i capçaleres de la notificació que enviaria el proveïdor per a aquesta ordre.
        Amb el mateix `event_id`, és la mateixa notificació repetida. Una autenticació de
        targeta acceptada la guarda (`card`, o una d'inventada que caduca d'aquí a tres anys)."""
        order = self.get_order(external_id)
        if status == base.PAID and external_id.startswith(SETUP_PREFIX):
            year = timezone.localdate().year + 3
            _cards.setdefault(
                external_id, card or base.ProviderCard(f"fake-card-{uuid4().hex}", "4242", 12, year)
            )
        _orders[external_id] = base.OrderState(
            external_id, status, order.amount_cents, order.currency
        )
        body = json.dumps(
            {
                "event_id": event_id or uuid4().hex,
                "order_id": external_id,
                "status": status,
                "amount_cents": order.amount_cents,
                "currency": order.currency,
            },
            sort_keys=True,
        ).encode()
        return body, {SIGNATURE_HEADER: sign(body, key)}

    def require_authentication(self, card_ref: str) -> None:
        """El banc d'aquesta targeta demanarà autenticació en el proper cobrament."""
        _authentication.add(card_ref)

    def settle(
        self, operations, *, fees_cents: int, settled_on=None, external_id: str | None = None
    ) -> base.ProviderSettlementReport:
        """L'abonament agrupat que faria el proveïdor al banc: les operacions (ordre, import),
        el brut, les comissions sense detall i el net. Format triat per l'equip, [A verificar:
        P-45 punt 9]."""
        operations = tuple(base.SettledOperation(order, amount) for order, amount in operations)
        gross = sum(operation.amount_cents for operation in operations)
        report = base.ProviderSettlementReport(
            external_id=external_id or f"fake-settlement-{uuid4().hex}",
            settled_on=settled_on or timezone.localdate(),
            gross_cents=gross,
            fees_cents=fees_cents,
            net_cents=gross - fees_cents,
            operations=operations,
        )
        _settlements.append(report)
        return report

    def complete(self, external_id: str, status: str) -> str:
        """El que fa la pàgina de pagament de prova quan la persona hi tria un resultat: envia
        la notificació signada a la plataforma, servidor a servidor, i torna l'adreça on va el
        navegador. Amb `PENDING` no envia res: la persona ha tancat la pàgina sense pagar."""
        urls = _urls[external_id]
        if status != base.PENDING:
            body, headers = self.notification(external_id, status)
            headers = {**headers, "Content-Type": "application/json"}
            # L'adreça és la de la plataforma (`PUBLIC_SITE_URL`), mai una que arribi de fora.
            request = urllib.request.Request(urls.notification, body, headers, method="POST")  # noqa: S310
            try:
                urllib.request.urlopen(request, timeout=10).close()  # noqa: S310
            except OSError:
                # Com un proveïdor de veritat: la tornada del navegador no depèn de l'avís.
                logger.warning("No s'ha pogut enviar la notificació de l'ordre %s", external_id)
        return urls.return_ok if status == base.PAID else urls.return_ko
