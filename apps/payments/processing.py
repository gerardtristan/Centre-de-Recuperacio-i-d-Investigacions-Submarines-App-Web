"""Processament de les notificacions del proveïdor i xarxa de seguretat (T-M05b-05; P-M05b-D;
RN-M05b-03, 05, 06 i 08; CA-M05b-03 a 07; L-M05b-01).

Només una notificació verificada i desada (T-M05a-04) o la consulta de l'ordre al proveïdor (la
xarxa de seguretat) donen un intent per pagat; mai el navegador (RN-M05b-05). Tot o res: l'intent,
el pagament, el càrrec, l'ingrés de la tresoreria i l'estat del soci canvien a la mateixa
transacció.

Falta: el correu al soci i l'avís per correu al tresorer necessiten plantilles noves, que es
declaren a la 00 (`mail.TEMPLATE_PRIORITIES`); el rebut és la T-M05b-07. Mentrestant, el que va
«a revisar» queda a l'intent, a la notificació i al registre d'activitat (T-M05b-16 en fa la
llista)."""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, charges
from apps.core.models import Charge, Payment
from apps.members import services as members
from apps.treasury import services as treasury

from . import attempts
from .models import PaymentAttempt, ProviderEvent
from .providers import base, get_provider

logger = logging.getLogger(__name__)
R = ProviderEvent.Result
S = PaymentAttempt.Status
ORIGIN = "payments.processing"
TO_REVIEW = "payments.notification_to_review"
ERROR = "payments.notification_error"
# `safety_net_age_minutes` (VC-17; 60): passa a `PaymentSettings` amb la T-M05b-22.
SAFETY_NET_AGE = timedelta(minutes=60)
# Estat normalitzat del proveïdor → estat de l'intent que encara és «en curs».
_CLOSED_BY = {base.DENIED: S.FAILED, base.EXPIRED: S.EXPIRED}


def _system():
    return audit.system(ORIGIN)


def process_notification(event_id: int) -> str:
    """`payments.process_notification`: processa una notificació desada «rebuda» i en tanca el
    resultat. Idempotent: una de ja processada no es torna a processar (CA-M05b-04). Un error
    deixa la notificació en «error» i al registre; la xarxa de seguretat recupera l'ordre."""
    try:
        with transaction.atomic():
            event = ProviderEvent.objects.select_for_update().get(pk=event_id)
            if event.result != R.RECEIVED:
                return event.result
            result = _process(event)
            _close(event, result)
            return result
    except Exception as error:
        logger.exception("No s'ha pogut processar la notificació %s", event_id)
        with transaction.atomic():
            event = ProviderEvent.objects.select_for_update().get(pk=event_id)
            if event.result == R.RECEIVED:
                _close(event, R.ERROR)
                details = {"error": type(error).__name__}
                audit.record(ERROR, actor=_system(), target=event, details=details)
        return R.ERROR


def _close(event: ProviderEvent, result: str) -> None:
    event.result, event.processed_at = result, timezone.now()
    event.save(update_fields=["result", "processed_at"])


def _process(event: ProviderEvent) -> str:
    attempt = (
        PaymentAttempt.objects.filter(
            provider_code=event.provider_code, provider_order_id=event.order_id
        )
        .exclude(provider_order_id="")
        .first()
    )
    if attempt is None:
        return _review(None, event, _("La notificació no és de cap ordre coneguda."))
    state = base.OrderState(event.order_id, event.event_type, event.amount_cents, event.currency)
    return settle(attempt, state, source=event)


def settle(attempt: PaymentAttempt, state: base.OrderState, *, source=None) -> str:
    """Aplica a l'intent l'estat de la seva ordre al proveïdor, vingui d'una notificació
    verificada o de la consulta de la xarxa de seguretat. Torna el resultat de la notificació.
    Cap import ve de fora: el pagament i l'ingrés porten l'import del càrrec (RN-M05b-02)."""
    with transaction.atomic():
        # L'intent bloquejat: dues notificacions de la mateixa ordre van una darrere l'altra.
        attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        charge = Charge.objects.get(pk=attempt.charge_id)
        if state.status == base.PENDING or attempt.status == S.PAID:
            return R.PROCESSED  # encara no s'ha decidit, o ja és pagat (CA-M05b-04)
        if (state.amount_cents, state.currency) != (attempt.amount_cents, charge.currency):
            reason = _("L'import o la moneda de l'ordre no coincideixen amb l'intent.")
            return _review(attempt, source, reason)  # CA-M05b-05
        if state.status != base.PAID:
            if attempt.status == S.IN_PROGRESS:
                attempts.transition(attempt, _CLOSED_BY[state.status], by=_system())
            return R.PROCESSED
        if attempt.status != S.IN_PROGRESS:
            # P-82, opció per defecte: RN-M05b-03 no deixa tornar a obrir un intent tancat. El
            # cobrament el revisa el tresorer; l'intent i el càrrec no canvien.
            reason = _("Confirmació de pagament d'un intent que ja estava tancat.")
            return _review(attempt, source, reason)
        if charge.status != Charge.Status.PENDING:
            # RN-M05b-08 i CA-M05b-07: el càrrec ja s'havia pagat (o anul·lat) per una altra via.
            reason = _("Pagament duplicat: el càrrec ja no era pendent. Cal fer-ne la devolució.")
            return _review(attempt, source, reason)
        _pay(attempt, charge, state)
        return R.PROCESSED


def _pay(attempt: PaymentAttempt, charge: Charge, state: base.OrderState) -> None:
    """CA-M05b-03: intent i càrrec «pagat», pagament, ingrés amb departament i, si és una
    quota, l'avís al 01 (`members.on_fee_paid`, que activa el soci i n'emet el carnet)."""
    by = _system()
    attempt = attempts.transition(attempt, S.PAID, by=by)
    # shortcut: el 05b crea el pagament de la 00 perquè la 00 encara no té el servei (P-84).
    payment = Payment.objects.create(
        charge=charge,
        method=attempt.method,
        amount_cents=attempt.amount_cents,
        provider_status=state.status,
        provider_reference=state.external_id,
        paid_at=timezone.now(),
    )
    charges.mark_paid(charge, payment, origin="provider", by=by)
    treasury.record_income(payment, origin="provider", by=by)
    fee = getattr(charge, "annual_fee", None)
    if fee is not None:
        members.on_fee_paid(fee.pk)


def _review(attempt: PaymentAttempt | None, source, reason: str) -> str:
    """«A revisar»: l'intent en curs hi passa amb el motiu; si l'intent ja estava tancat o no
    n'hi ha, el motiu queda al registre, sobre la notificació o l'intent."""
    if attempt is not None and attempt.status == S.IN_PROGRESS:
        attempts.transition(attempt, S.TO_REVIEW, by=_system(), reason=reason)
    else:
        audit.record(TO_REVIEW, actor=_system(), target=source or attempt, reason=reason)
    return R.TO_REVIEW


def safety_net() -> None:
    """Xarxa de seguretat, cada dia: processa les notificacions que s'hagin quedat «rebudes» i
    consulta al proveïdor les ordres en curs de fa més de `SAFETY_NET_AGE` sense notificació.
    Si no es poden consultar, l'intent va «a revisar» (L-M05b-01). Un error en una ordre no
    atura les altres."""
    limit = timezone.now() - SAFETY_NET_AGE
    stuck = ProviderEvent.objects.filter(result=R.RECEIVED, received_at__lt=limit)
    for event_id in stuck.values_list("pk", flat=True):
        process_notification(event_id)
    provider = get_provider()
    stale = PaymentAttempt.objects.filter(
        status=S.IN_PROGRESS, provider_code=provider.code, created_at__lt=limit
    ).exclude(provider_order_id="")
    for attempt in stale:
        try:
            try:
                # Fora de la transacció: la consulta és una crida de xarxa.
                state = provider.get_order(attempt.provider_order_id)
            except base.ProviderError:
                with transaction.atomic():
                    _review(attempt, None, _("No s'ha pogut consultar l'ordre al proveïdor."))
                continue
            settle(attempt, state)
        except Exception:
            logger.exception("Xarxa de seguretat: no s'ha pogut tancar l'intent %s", attempt.pk)
