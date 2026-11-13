"""Recepció de les notificacions del proveïdor (arquitectura §4.2, punts 1 a 3; T-M05a-04).

Verifica, desa, la posa a la cua i respon. No processa res: el que queda «rebut» ho processa la
cua (`processing.process_notification`, T-M05b-05), i la xarxa de seguretat recull el que no
s'hagi processat a temps."""

import hashlib
from dataclasses import dataclass
from datetime import timedelta

from django.db import DataError, IntegrityError, transaction
from django.utils import timezone

from apps.accounts.security import client_ip

from .models import ProviderEvent
from .providers.base import InvalidSignature, MalformedNotification, PaymentProvider
from .tasks import process_notification

R = ProviderEvent.Result

# Un origen sense firma vàlida no pot omplir la taula: com a molt, tants rebuigs desats per
# període. Passat el límit, es continua responent amb error, sense desar-ne cap més.
REJECTED_MAX = 60
REJECTED_PERIOD = timedelta(minutes=10)


@dataclass(frozen=True)
class Received:
    http_status: int
    event: ProviderEvent | None


def _reject(provider: PaymentProvider, body_hash: str) -> Received:
    """CA-M05a-10: es respon amb error, no es processa i queda registrada com a rebutjada."""
    recent = ProviderEvent.objects.filter(
        result=R.REJECTED_SIGNATURE, received_at__gt=timezone.now() - REJECTED_PERIOD
    )
    if recent.count() < REJECTED_MAX:
        ProviderEvent.objects.create(
            provider_code=provider.code, payload_hash=body_hash, result=R.REJECTED_SIGNATURE
        )
    return Received(400, None)


def receive(provider: PaymentProvider, request) -> Received:
    body_hash = hashlib.sha256(request.body).hexdigest()
    if provider.allowed_ips and client_ip(request) not in provider.allowed_ips:
        return _reject(provider, body_hash)
    try:
        notification = provider.verify_notification(request)
    except InvalidSignature:
        return _reject(provider, body_hash)
    except MalformedNotification:
        # Ve del proveïdor (la firma és bona) però no s'entén: es desa perquè algú la miri i es
        # respon correcte perquè el proveïdor no la torni a enviar.
        event = ProviderEvent.objects.create(
            provider_code=provider.code, payload_hash=body_hash, result=R.TO_REVIEW
        )
        return Received(200, event)

    fields = {
        "provider_code": provider.code,
        "external_id": notification.event_id,
        "event_type": notification.status,
        "payload_hash": body_hash,
        "order_id": notification.order_id,
        "amount_cents": notification.amount_cents,
        "currency": notification.currency,
    }
    try:
        with transaction.atomic():
            event = ProviderEvent.objects.create(**fields)
            # A la mateixa transacció: la feina de la cua existeix si i només si la fila hi és.
            process_notification.defer(event_id=event.pk)
    except IntegrityError:
        # CA-M05a-11: ja la teníem. Es respon correcte i no es torna a processar.
        ProviderEvent.objects.create(**fields, result=R.IGNORED_DUPLICATE)
        return Received(200, None)
    except DataError:
        # Signada, però amb un valor que no hi cap (un identificador massa llarg, un import
        # impossible): a revisar, sense desar-ne els camps, i el proveïdor no l'ha de repetir.
        event = ProviderEvent.objects.create(
            provider_code=provider.code, payload_hash=body_hash, result=R.TO_REVIEW
        )
    return Received(200, event)
