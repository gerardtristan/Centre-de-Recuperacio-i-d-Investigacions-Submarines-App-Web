"""Començar un pagament (T-M05b-04; P-M05b-A i B, pas 2; M05b-8; RN-M05b-02, 04 i 07).

Targeta, Bizum i transferència (T-M05b-06; P-M05b-C, passos 1 i 2), i només amb un compte. El
convidat (T-M05b-08) hi entra a la seva tasca. Aquí no es dona mai res per pagat: «pagat» només
arriba amb la notificació verificada del proveïdor, amb l'estat de l'ordre que el proveïdor torna
(RN-M05b-05; T-M05b-05) o, per a la transferència, amb la conciliació de la 04 (`transfers`)."""

import logging
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import Charge
from apps.treasury import services as treasury

from . import attempts, processing
from .models import PaymentAttempt
from .providers import get_provider
from .providers.base import OrderUrls, ensure_charges_allowed

# Què ha de fer la pantalla amb `PaymentStart.url`: enviar-hi el navegador o incrustar-la.
REDIRECT = "redirect"
IFRAME = "iframe"
TRANSFER_DETAILS = "transfer_details"  # la pantalla mostra l'IBAN, l'import i la referència

# On torna el navegador en sortir del proveïdor: la pantalla de pagament del càrrec (M05b-8,
# «Rutes»; `payments:charge`).
RETURN_PATH = "/socis/pagaments/{charge}/?tornada={result}"

S = PaymentAttempt.Status
BIZUM = PaymentAttempt.Method.BIZUM
TRANSFER = PaymentAttempt.Method.TRANSFER
logger = logging.getLogger(__name__)

# Estats que veu el soci (M05b-5, «Estats visibles»), i «tancat» per a un càrrec anul·lat o
# retornat, que no es paga des d'aquesta pantalla. «No confirmat a temps» (RN-M05b-07) és un
# Bizum en curs que la pantalla ja no espera: l'intent continua en curs fins que el proveïdor el
# tanqui, i una confirmació que arribi tard es processa com qualsevol altra.
PENDING, IN_PROGRESS, PAID, FAILED, CLOSED = "pending", "in_progress", "paid", "failed", "closed"
TIMED_OUT = "timed_out"


class NotOwnCharge(attempts.ChargeNotPayable):
    """M05b-4, «per objecte»: cadascú només paga els seus càrrecs, i amb un compte actiu."""


@dataclass(frozen=True)
class PaymentStart:
    """El que necessita la pantalla per continuar. Cap dada de targeta: la targeta s'escriu a
    la pàgina o al camp del proveïdor (CA-M05b-01). La transferència porta l'IBAN del club i la
    referència del càrrec (M05b-8; CA-M05b-10)."""

    attempt_id: int
    kind: str
    amount_cents: int
    url: str | None = None
    reference: str | None = None
    club_iban: str | None = None


@dataclass(frozen=True)
class PaymentStatus:
    state: str
    attempt: PaymentAttempt | None  # l'últim intent, si n'hi ha


def payment_status(charge: Charge) -> PaymentStatus:
    """`payments.payment_status`: el que diu la base de dades, mai el navegador (RN-M05b-05).
    Un intent abandonat torna el càrrec a «pendent»; un de fallit o caducat, a «fallit»."""
    stored = Charge.objects.get(pk=charge.pk)
    last = stored.attempts.order_by("-created_at", "-pk").first()
    if stored.status == Charge.Status.PAID:
        return PaymentStatus(PAID, last)
    if stored.status != Charge.Status.PENDING:
        return PaymentStatus(CLOSED, last)
    status = last.status if last else None
    if status == S.IN_PROGRESS and _timed_out(last):
        return PaymentStatus(TIMED_OUT, last)
    if status in (S.IN_PROGRESS, S.SENT_TO_BANK):
        return PaymentStatus(IN_PROGRESS, last)
    if status in (S.FAILED, S.EXPIRED):
        return PaymentStatus(FAILED, last)
    return PaymentStatus(PENDING, last)


def _timed_out(attempt: PaymentAttempt) -> bool:
    """RN-M05b-07: un Bizum que fa més minuts dels que espera la pantalla (VC-17) que espera la
    confirmació. Valen els minuts desats a l'intent en obrir-lo (RN-M05b-24)."""
    if attempt.method != BIZUM:
        return False
    return attempt.created_at <= timezone.now() - timedelta(minutes=attempt.ui_timeout_minutes)


def transfer_iban() -> str:
    """L'IBAN del club per pagar per transferència (RN-T03; VC-09, `CLUB_IBAN_TRANSFERENCIES`),
    sense espais. Buit: la transferència no s'ofereix ni es pot començar (falla tancada)."""
    return "".join(getattr(settings, "CLUB_IBAN_TRANSFERENCIES", "").split()).upper()


def _abandon_waiting_transfer(charge: Charge, actor) -> None:
    """P-136 (opció per defecte): una transferència que s'espera no té cap ordre al proveïdor, i
    la plataforma la pot deixar sola: triar targeta o Bizum la marca «abandonada» (RN-M05b-04).
    Si la transferència arriba igualment, la conciliació la veu d'un càrrec ja pagat i la deixa
    a revisar per tornar-la (LT6)."""
    waiting = PaymentAttempt.objects.filter(charge=charge, status=S.IN_PROGRESS, method=TRANSFER)
    for attempt in waiting:
        attempts.transition(attempt, S.ABANDONED, by=actor, reason="P-136: un altre mètode")


def _start_transfer(charge: Charge, actor) -> PaymentStart:
    """P-M05b-C, passos 1 i 2: l'intent queda «en curs» esperant l'extracte; no hi ha
    notificació. La referència és la del càrrec, que no canvia (RN-T20)."""
    iban = transfer_iban()
    if not iban:
        raise attempts.MethodNotAllowed(TRANSFER)
    if _in_progress(charge):
        raise attempts.AttemptInProgress
    attempt = attempts.create_attempt(charge, TRANSFER, started_by=actor)
    attempt = attempts.transition(attempt, S.IN_PROGRESS, by=actor)
    return PaymentStart(
        attempt_id=attempt.pk,
        kind=TRANSFER_DETAILS,
        amount_cents=attempt.amount_cents,
        reference=treasury.transfer_reference(charge),
        club_iban=iban,
    )


def _owns(actor, charge) -> bool:
    return isinstance(actor, Account) and actor.is_active and actor.person_id == charge.person_id


def _close_timed_out_bizum(charge: Charge) -> None:
    """RN-M05b-04 i 07: un Bizum que la pantalla ja no espera només el tanca el proveïdor. Abans
    d'obrir un intent nou, se li pregunta l'estat de l'ordre i s'aplica com fa la xarxa de
    seguretat (`processing.settle`): caducada o denegada, l'intent es tanca i se'n pot obrir un
    altre; pagada, el càrrec queda pagat; encara oberta, el nou s'espera (`AttemptInProgress`).
    Fora de la transacció de `start_payment`, perquè el que es tanqui quedi fet encara que el nou
    intent no es pugui obrir. Si el proveïdor no respon, no canvia res."""
    attempt = (
        PaymentAttempt.objects.filter(charge=charge, status=S.IN_PROGRESS, method=BIZUM)
        .exclude(provider_order_id="")
        .first()
    )
    if attempt is None or not _timed_out(attempt):
        return
    try:
        provider = get_provider()
        if provider.code == attempt.provider_code:
            processing.settle(attempt, provider.get_order(attempt.provider_order_id))
    except Exception:
        logger.exception("No s'ha pogut consultar l'ordre de l'intent %s", attempt.pk)


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
    if _owns(actor, charge):
        _close_timed_out_bizum(charge)
    with transaction.atomic():
        # El càrrec queda bloquejat fins al final: dues peticions alhora van una darrere l'altra
        # i, mentre es parla amb el proveïdor, ningú no pot pagar ni anul·lar el càrrec.
        stored = Charge.objects.select_for_update().get(pk=charge.pk)
        if not _owns(actor, stored):
            raise NotOwnCharge
        # Nivell 1: tampoc cap transferència, que també és un cobrament real (RN-M05a-11).
        ensure_charges_allowed()
        if method == TRANSFER:
            return _start_transfer(stored, actor)
        provider = get_provider()
        capabilities = provider.capabilities()
        if not getattr(capabilities, method, False):
            raise attempts.MethodNotAllowed(method)
        _abandon_waiting_transfer(stored, actor)
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
