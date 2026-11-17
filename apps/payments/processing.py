"""Processament de les notificacions del proveïdor i xarxa de seguretat (T-M05b-05; P-M05b-D;
RN-M05b-03, 05, 06 i 08; CA-M05b-03 a 07; L-M05b-01).

Només una notificació verificada i desada (T-M05a-04) o la consulta de l'ordre al proveïdor (la
xarxa de seguretat) donen un intent per pagat; mai el navegador (RN-M05b-05). Tot o res: l'intent,
el pagament, el càrrec, l'ingrés de la tresoreria i l'estat del soci canvien a la mateixa
transacció.

En pagar-se, el rebut i el correu al pagador (`receipts.issue`, T-M05b-07). El que va «a
revisar» queda a l'intent, a la notificació i al registre d'activitat (T-M05b-16 en fa la
llista), i qui té el permís de la tresoreria en rep l'avís per correu (CA-M05b-05; P-86, opció
per defecte)."""

import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.core import audit, business_settings, charges, mail
from apps.core.models import Charge, Person
from apps.core.permissions import accounts_with_perm
from apps.members import services as members
from apps.treasury import services as treasury

from . import attempts, cards, receipts, returns
from .models import PaymentAttempt, ProviderEvent, SavedCardAttempt, SavedCardNotice
from .providers import base, get_provider

logger = logging.getLogger(__name__)
R = ProviderEvent.Result
S = PaymentAttempt.Status
ORIGIN = "payments.processing"
TO_REVIEW = "payments.notification_to_review"
ERROR = "payments.notification_error"
REVIEW_TEMPLATE = "avis-pagament-revisar"
# Resultats de la targeta guardada (T-M05b-15b): el motiu; a qui s'avisa el soci (l'alternativa)
# i què no queda «a revisar». El tresorer en rep sempre l'avís, amb la quota i el càrrec.
TREASURER_TEMPLATE = "quota-targeta-revisar"
SAVED_CARD_ACTOR = "payments.saved_card"
OUTCOME = "payments.saved_card.outcome"
OUTCOMES = {
    "denied": gettext_lazy("El banc ha denegat el cobrament amb la targeta guardada."),
    "order_expired": gettext_lazy("L'ordre del cobrament amb la targeta guardada ha caducat."),
    "authentication": gettext_lazy("El banc demana autenticació per cobrar amb la targeta."),
    "amount_changed": gettext_lazy("L'import de la quota ha canviat abans de cobrar-la."),
    "provider_error": gettext_lazy("El proveïdor no ha respost en cobrar amb la targeta."),
    "unexpected_order": gettext_lazy("El proveïdor ha tornat una ordre diferent de l'esperada."),
    "give_up": gettext_lazy("La xarxa de seguretat no ha pogut tancar l'intent."),
    "card_closed": gettext_lazy("La targeta guardada ja no es pot fer servir."),
    "not_member": gettext_lazy("La persona ja no és sòcia activa ni impagada."),
    "preference": gettext_lazy("La preferència de la quota ja no és aquesta targeta."),
    "provider": gettext_lazy("La targeta és d'un altre proveïdor."),
    "not_fee": gettext_lazy("El càrrec no és una quota anual."),
    "other_person": gettext_lazy("Dades incoherents: la targeta és d'una altra persona."),
    "transfer_waiting": gettext_lazy("Té una transferència en espera: no es cobra la targeta."),
    "arrears": gettext_lazy("La quota va vèncer fa massa dies: es paga des de la pantalla."),
    "open_failed": gettext_lazy("No s'ha pogut obrir l'intent al proveïdor."),
}
TELL_MEMBER = {"denied", "order_expired", "authentication", "card_closed"}
NOT_REVIEWED = {"denied", "order_expired", "authentication"}  # la resta, «a revisar»
REVIEW_PERMISSION = "treasury.view"  # T1; P-86, opció per defecte
# VC-17: minuts sense notificació abans que la xarxa de seguretat pregunti al proveïdor.
SAFETY_NET_AGE = "payments.safety_net_age_minutes"
# VC-17 (decisió 093): una ordre que la xarxa no pot tancar es torna a provar l'endemà; passades
# aquestes hores va «a revisar» (L-M05b-01). Així una caiguda curta del proveïdor no tanca un
# intent que potser es pagarà i obre la porta a pagar dues vegades.
SAFETY_NET_GIVE_UP = "payments.safety_net_give_up_hours"
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
        setup = cards.setup_for(event)  # guardar una targeta (T-M05a-12)
        if setup is None:
            return _review(None, event, _("La notificació no és de cap ordre coneguda."))
        state = base.OrderState(
            event.order_id, event.event_type, event.amount_cents, event.currency
        )
        reason = cards.settle_setup(setup, state)
        return _review(None, event, reason) if reason else R.PROCESSED
    state = base.OrderState(event.order_id, event.event_type, event.amount_cents, event.currency)
    return settle(attempt, state, source=event)


def settle(attempt: PaymentAttempt, state: base.OrderState, *, source=None) -> str:
    """Aplica a l'intent l'estat de la seva ordre al proveïdor, vingui d'una notificació
    verificada o de la consulta de la xarxa de seguretat. Torna el resultat de la notificació.
    Cap import ve de fora: el pagament i l'ingrés porten l'import del càrrec (RN-M05b-02)."""
    with transaction.atomic():
        # El càrrec i després l'intent, bloquejats en el mateix ordre que `start_payment`: una
        # conciliació o una altra notificació del mateix càrrec van una darrere l'altra.
        charge = Charge.objects.select_for_update().get(pk=attempt.charge_id)
        attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        if state.status == base.PENDING or attempt.status == S.PAID:
            return R.PROCESSED  # encara no s'ha decidit, o ja és pagat (CA-M05b-04)
        if (state.amount_cents, state.currency) != (attempt.amount_cents, charge.currency):
            reason = _("L'import o la moneda de l'ordre no coincideixen amb l'intent.")
            return _review(attempt, source, reason)  # CA-M05b-05
        if state.status not in (base.PAID, *_CLOSED_BY):
            return _review(attempt, source, _("El proveïdor torna un estat desconegut."))
        if state.status != base.PAID:
            if attempt.status == S.IN_PROGRESS:
                attempt = attempts.transition(attempt, _CLOSED_BY[state.status], by=_system())
                if attempt.method == PaymentAttempt.Method.SAVED_CARD:
                    on_saved_card_failed(attempt, charge)  # «alternativa de pagament si falla»
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
    payment = charges.record_payment(
        charge,
        # Per a la 00 i la tresoreria, una targeta guardada és una targeta.
        method=attempt.payment_method,
        origin="provider",
        by=by,
        provider_status=state.status,
        provider_reference=state.external_id,
    )
    treasury.record_income(payment, origin="provider", by=by)
    receipts.issue(attempt)
    fee = getattr(charge, "annual_fee", None)
    if fee is not None:
        members.on_fee_paid(fee.pk)


def _review_entry(attempt, source, reason: str) -> None:
    if attempt is not None and attempt.status == S.IN_PROGRESS:
        attempts.transition(attempt, S.TO_REVIEW, by=_system(), reason=reason)
    else:
        audit.record(TO_REVIEW, actor=_system(), target=source or attempt, reason=reason)


def mark_for_review(attempt, source, reason: str) -> str:
    """«A revisar»: l'intent en curs hi passa amb el motiu; si l'intent ja estava tancat o no
    n'hi ha, el motiu queda al registre (`TO_REVIEW`, d'on surt la llista «a revisar»), sobre la
    notificació, el càrrec o l'intent. I l'avís al tresorer."""
    _review_entry(attempt, source, reason)
    _mail_review(attempt, source, reason)
    return R.TO_REVIEW


_review = mark_for_review


def _mail_review(attempt, source, reason: str) -> None:
    """L'avís al tresorer (CA-M05b-05): el motiu i les referències internes, cap dada personal.
    Un sol correu per adreça; va a la mateixa transacció que el canvi."""
    context = {
        "reason": reason,
        "attempt_id": attempt.pk if attempt else None,
        "event_id": source.pk if isinstance(source, ProviderEvent) else None,
    }
    notify_treasurers(REVIEW_TEMPLATE, context)


def notify_treasurers(template: str, context: dict) -> None:
    """Un correu a cada adreça de qui té el permís de la tresoreria (P-86), a la transacció de
    qui el crida. `context`: només referències internes, cap dada personal."""
    sent = set()
    for account in accounts_with_perm(REVIEW_PERMISSION):
        address = account.notification_email
        if address and address not in sent:
            mail.queue_email(template, to=address, person=account.person, context=context)
            sent.add(address)


def saved_card_outcome(charge: Charge, case: str, *, card, attempt=None) -> None:
    """Punt d'entrada únic dels resultats de la targeta guardada (T-M05b-15b; `OUTCOMES`): una fila
    per càrrec, targeta i motiu, a la transacció de qui crida, i els avisos."""
    notice, _new = SavedCardNotice.objects.get_or_create(charge=charge, card=card, case=case)
    if not notice.notified:
        _notify(notice, attempt)


def _notify(notice: SavedCardNotice, attempt=None) -> None:
    """La marca, el «a revisar» i els missatges, junts: si un correu falla, no queda res d'això i
    `retry_outcomes` ho torna a provar l'endemà. No desfà mai el que ha fet qui crida."""
    reason = OUTCOMES[notice.case]
    member, review = notice.case in TELL_MEMBER, notice.case not in NOT_REVIEWED
    charge = notice.charge
    try:
        with transaction.atomic():
            if review:
                _review_entry(attempt, charge, str(reason))
            sent = member and returns.send_alternative(
                charge, new_mandate=False, saved_card=True, unusable=notice.case == "card_closed"
            )
            erased = charge.person.status == Person.Status.ANONYMISED
            fee = getattr(charge, "annual_fee", None)
            context = {
                "concept": charge.concept,
                "charge_id": charge.pk,
                "fee_id": fee.pk if fee else "",
                "reason": reason,
                "erased": erased,
                "no_email": member and not sent and not erased,
                "member_told": sent,
            }
            notify_treasurers(TREASURER_TEMPLATE, context)
            details = {"charge": charge.pk, "case": notice.case, "sent": sent}
            by = audit.system(SAVED_CARD_ACTOR)
            audit.record(OUTCOME, actor=by, target=attempt or charge, details=details)
            notice.notified = True
            notice.save(update_fields=["notified"])
    except Exception:
        logger.exception("No s'han pogut enviar els avisos del càrrec %s", charge.pk)


def retry_outcomes() -> None:
    """Els avisos que no van sortir (un correu que va fallar), de nou."""
    for notice in SavedCardNotice.objects.filter(notified=False).select_related("charge"):
        _notify(notice)


def _card_of(attempt: PaymentAttempt):
    return SavedCardAttempt.objects.get(attempt=attempt).card


def on_saved_card_failed(attempt: PaymentAttempt, charge: Charge) -> None:
    """Un intent amb la targeta guardada que es tanca sense pagar, amb el càrrec ja bloquejat per
    `settle`: l'alternativa, si la quota continua pendent."""
    if charge.status == Charge.Status.PENDING:
        case = "order_expired" if attempt.status == S.EXPIRED else "denied"
        saved_card_outcome(charge, case, card=_card_of(attempt))


def safety_net() -> None:
    """Xarxa de seguretat, cada dia: processa les notificacions que s'hagin quedat «rebudes» i
    consulta al proveïdor les ordres en curs de fa més de `SAFETY_NET_AGE` minuts (ajust) sense
    notificació.
    Si no es pot consultar o tancar, es torna a provar l'endemà i, passades `SAFETY_NET_GIVE_UP`
    hores (ajust), l'intent va «a revisar» (L-M05b-01). Un error en una ordre no atura les altres.
    """
    limit = timezone.now() - timedelta(minutes=business_settings.get(SAFETY_NET_AGE))
    stuck = ProviderEvent.objects.filter(result=R.RECEIVED, received_at__lt=limit)
    for event_id in stuck.values_list("pk", flat=True):
        process_notification(event_id)
    provider = get_provider()
    stale = PaymentAttempt.objects.filter(
        status=S.IN_PROGRESS, provider_code=provider.code, created_at__lt=limit
    ).exclude(provider_order_id="")
    give_up = timezone.now() - timedelta(hours=business_settings.get(SAFETY_NET_GIVE_UP))
    for attempt in stale.order_by("pk"):
        try:
            # Fora de la transacció: la consulta és una crida de xarxa.
            state = provider.get_order(attempt.provider_order_id)
        except base.ProviderError:
            _give_up(attempt, give_up, _("No s'ha pogut consultar l'ordre al proveïdor."))
            continue
        try:
            settle(attempt, state)
        except Exception:
            logger.exception("Xarxa de seguretat: no s'ha pogut tancar l'intent %s", attempt.pk)
            _give_up(attempt, give_up, _("La xarxa de seguretat no ha pogut tancar l'intent."))
    for setup in cards.stale_setups(provider.code, limit):
        # Les autenticacions de targeta igual (T-M05a-12): es torna a consultar l'ordre i la
        # targeta, i la que no es tanca passades les hores es dona per abandonada.
        try:
            state = provider.get_order(setup.provider_order_id)
            with transaction.atomic():
                if reason := cards.settle_setup(setup, state):
                    _review(None, setup, reason)
        except Exception:
            logger.exception("Xarxa de seguretat: no s'ha pogut tancar l'autenticació %s", setup.pk)
        cards.give_up(setup, give_up)


def _give_up(attempt: PaymentAttempt, give_up, reason: str) -> None:
    """Passades `SAFETY_NET_GIVE_UP` hores, l'intent que no es pot tancar va «a revisar» perquè
    el tresorer el vegi; abans, es deixa en curs per tornar-hi l'endemà."""
    if attempt.created_at >= give_up:
        return
    try:
        with transaction.atomic():
            if attempt.method == PaymentAttempt.Method.SAVED_CARD:
                charge = Charge.objects.select_for_update().get(pk=attempt.charge_id)
                saved_card_outcome(charge, "give_up", card=_card_of(attempt), attempt=attempt)
            else:
                _review(attempt, None, reason)
    except Exception:
        logger.exception(
            "Xarxa de seguretat: no s'ha pogut deixar a revisar l'intent %s", attempt.pk
        )
