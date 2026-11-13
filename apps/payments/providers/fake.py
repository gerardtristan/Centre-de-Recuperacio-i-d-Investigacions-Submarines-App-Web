"""Proveïdor fals: sense xarxa, per a les proves i per al desenvolupament local (T-M05a-03).
Obre ordres, signa les notificacions amb HMAC i rebutja les que no quadren. Només arrenca amb
l'entorn de proves. Les ordres viuen en memòria, dins del procés."""

import hashlib
import hmac
import json
import logging
import urllib.request
from datetime import timedelta
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

logger = logging.getLogger(__name__)
_orders: dict[str, base.OrderState] = {}
_urls: dict[str, base.OrderUrls] = {}


def sign(body: bytes, key: str = SIGNING_KEY) -> str:
    return hmac.new(key.encode(), body, hashlib.sha256).hexdigest()


def reset() -> None:
    """Oblida les ordres en memòria (entre proves)."""
    _orders.clear()
    _urls.clear()


class FakeProvider(base.PaymentProvider):
    code = "fake"

    def __init__(self):
        if settings.PAYMENTS_ENVIRONMENT != base.SANDBOX:
            raise ImproperlyConfigured("El proveïdor fals no es pot fer servir amb l'entorn real.")

    def capabilities(self) -> base.Capabilities:
        return base.Capabilities(
            card=True, bizum=True, tokenization=False, refund_bizum=True, embedded_field=False
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
        return base.ProviderOrder(
            external_id=external_id,
            pay_url=f"{settings.PUBLIC_SITE_URL}{PAY_PATH}{external_id}/",
            expires_at=expires_at,
        )

    def get_order(self, external_id: str) -> base.OrderState:
        try:
            return _orders[external_id]
        except KeyError:
            raise base.ProviderError(f"Ordre desconeguda: {external_id}") from None

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
        if (
            notification.status not in base.ORDER_STATUSES
            or isinstance(amount, bool)
            or not isinstance(amount, int)
            or amount <= 0
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

    # --- El que faria el proveïdor de veritat: només per a proves i desenvolupament ---

    def notification(
        self, external_id: str, status: str, *, event_id: str | None = None, key: str = SIGNING_KEY
    ) -> tuple[bytes, dict]:
        """Cos i capçaleres de la notificació que enviaria el proveïdor per a aquesta ordre.
        Amb el mateix `event_id`, és la mateixa notificació repetida."""
        order = self.get_order(external_id)
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
