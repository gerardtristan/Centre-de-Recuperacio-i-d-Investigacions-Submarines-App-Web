"""Començar un pagament (T-M05b-04; P-M05b-A, pas 2; M05b-8; RN-M05b-02 i 04).

Tall de targeta (decisió 089, D3): només targeta i només amb un compte. Bizum, la transferència
i el convidat (T-M05b-08) hi entren a la seva tasca. Aquí no es dona mai res per pagat: «pagat»
només arriba amb la notificació verificada del proveïdor (RN-M05b-05; T-M05b-05)."""

from dataclasses import dataclass

from django.conf import settings
from django.db import transaction
from django.urls import reverse

from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import Charge

from . import attempts
from .models import PaymentAttempt
from .providers import get_provider
from .providers.base import OrderUrls, ensure_charges_allowed

# Què ha de fer la pantalla amb `PaymentStart.url`: enviar-hi el navegador o incrustar-la.
REDIRECT = "redirect"
IFRAME = "iframe"

# On torna el navegador en sortir del proveïdor: la pantalla de pagament del càrrec (M05b-8,
# «Rutes»). La ruta arriba amb les vistes; fins llavors cap pantalla no crida `start_payment`.
RETURN_PATH = "/socis/pagaments/{charge}/?tornada={result}"

S = PaymentAttempt.Status


class NotOwnCharge(attempts.ChargeNotPayable):
    """M05b-4, «per objecte»: cadascú només paga els seus càrrecs, i amb un compte actiu."""


@dataclass(frozen=True)
class PaymentStart:
    """El que necessita la pantalla per continuar. Cap dada de targeta: la targeta s'escriu a
    la pàgina o al camp del proveïdor (CA-M05b-01). Les dades de la transferència (M05b-8) hi
    entren amb la T-M05b-06."""

    attempt_id: int
    kind: str
    amount_cents: int
    url: str | None = None


def _in_progress(charge) -> bool:
    waiting = (S.IN_PROGRESS, S.SENT_TO_BANK)
    return PaymentAttempt.objects.filter(charge=charge, status__in=waiting).exists()


def _urls(provider, charge) -> OrderUrls:
    site = settings.PUBLIC_SITE_URL
    back = site + RETURN_PATH
    return OrderUrls(
        notification=site + reverse("payments:provider_notification", args=[provider.code]),
        return_ok=back.format(charge=charge.pk, result="ok"),
        return_ko=back.format(charge=charge.pk, result="ko"),
    )


def start_payment(charge: Charge, method: str, actor) -> PaymentStart:
    """`payments.start_payment`: obre l'intent i, al servidor, l'ordre del proveïdor amb
    l'import desat del càrrec i la clau d'idempotència de l'intent (RN-M05b-02). No rep cap
    import: no hi ha manera de passar-n'hi un.

    `actor`: el compte que paga, actiu i de la persona del càrrec.

    Errors: `MethodNotAllowed`, `NotOwnCharge` i `ChargeNotPayable`, `AttemptInProgress`
    (RN-M05b-04: el nou s'espera), `LiveChargesNotAllowed` i els altres `ProviderError`. Amb
    qualsevol error no en queda res: ni intent ni ordre que algú pugui pagar."""
    if method not in attempts.ENABLED_METHODS:
        raise attempts.MethodNotAllowed(method)
    with transaction.atomic():
        # El càrrec queda bloquejat fins al final: dues peticions alhora van una darrere l'altra
        # i, mentre es parla amb el proveïdor, ningú no pot pagar ni anul·lar el càrrec.
        stored = Charge.objects.select_for_update().get(pk=charge.pk)
        own = isinstance(actor, Account) and actor.person_id == stored.person_id
        if not own or not actor.is_active:
            raise NotOwnCharge
        ensure_charges_allowed()
        provider = get_provider()
        capabilities = provider.capabilities()
        if not getattr(capabilities, method, False):
            raise attempts.MethodNotAllowed(method)
        if _in_progress(stored):
            raise attempts.AttemptInProgress
        attempt = attempts.create_attempt(stored, method, started_by=actor)
        # Primer «en curs», que ocupa l'únic lloc del càrrec (índex únic), i després l'ordre:
        # si l'índex atura l'intent, el proveïdor no arriba a rebre res.
        attempt = attempts.transition(attempt, S.IN_PROGRESS, by=actor)
        order = provider.create_order(
            stored, method, _urls(provider, stored), attempt.idempotency_key
        )
        attempt.provider_code = provider.code
        attempt.provider_order_id = order.external_id
        attempt.expires_at = order.expires_at
        attempt.save(
            update_fields=["provider_code", "provider_order_id", "expires_at", "updated_at"]
        )
        details = {"provider": provider.code, "order": order.external_id}
        audit.record("payments.order_created", actor=actor, target=attempt, details=details)
    return PaymentStart(
        attempt_id=attempt.pk,
        kind=IFRAME if capabilities.embedded_field else REDIRECT,
        amount_cents=attempt.amount_cents,
        url=order.pay_url,
    )
