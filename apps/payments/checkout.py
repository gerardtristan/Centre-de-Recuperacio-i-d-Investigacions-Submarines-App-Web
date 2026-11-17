"""Començar un pagament (T-M05b-04; P-M05b-A i B, pas 2; M05b-8; RN-M05b-02, 04 i 07).

Targeta, Bizum i transferència (T-M05b-06; P-M05b-C, passos 1 i 2), amb un compte o amb un enllaç
de convidat (T-M05b-08; decisió 021, RN-33 de la 00): les mateixes regles per a tots dos. Aquí no
es dona mai res per pagat: «pagat» només arriba amb la notificació verificada del proveïdor, amb
l'estat de l'ordre que el proveïdor torna (RN-M05b-05; T-M05b-05) o, per a la transferència, amb
la conciliació de la 04 (`transfers`)."""

import logging
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.accounts.models import Account
from apps.core import audit, guest_links
from apps.core.models import Charge, GuestLink, Person
from apps.members.models import Member
from apps.treasury import services as treasury

from . import attempts, processing
from .guards import charges_allowed, ensure_charges_allowed
from .models import (
    FeePaymentPreference,
    PaymentAttempt,
    SavedCard,
    SavedCardAttempt,
    SavedCardNotice,
)
from .providers import get_provider
from .providers.base import OrderUrls

# Què ha de fer la pantalla amb `PaymentStart.url`: enviar-hi el navegador o incrustar-la.
REDIRECT = "redirect"
IFRAME = "iframe"
TRANSFER_DETAILS = "transfer_details"  # la pantalla mostra l'IBAN, l'import i la referència

# On torna el navegador en sortir del proveïdor: la pantalla de pagament del càrrec (M05b-8,
# «Rutes»; `payments:charge`).
RETURN_PATH = "/socis/pagaments/{charge}/?tornada={result}"
# El convidat torna a la seva pantalla, sense cap identificador (`payments:guest_charge`).
GUEST_RETURN_PATH = "/pagaments/convidat/?tornada={result}"

S = PaymentAttempt.Status
BIZUM = PaymentAttempt.Method.BIZUM
SAVED_CARD = PaymentAttempt.Method.SAVED_CARD
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
    return "".join(settings.CLUB_IBAN_TRANSFERENCIES.split()).upper()


def _abandon_waiting_transfer(charge: Charge, actor) -> None:
    """P-136 (opció per defecte): una transferència que s'espera no té cap ordre al proveïdor, i
    la plataforma la pot deixar sola: triar targeta o Bizum la marca «abandonada» (RN-M05b-04).
    Si la transferència arriba igualment, la conciliació la veu d'un càrrec ja pagat i la deixa
    a revisar per tornar-la (LT6)."""
    waiting = PaymentAttempt.objects.filter(charge=charge, status=S.IN_PROGRESS, method=TRANSFER)
    for attempt in waiting:
        attempts.transition(attempt, S.ABANDONED, by=actor, reason="P-136: un altre mètode")


def _start_transfer(charge: Charge, actor, payer: dict) -> PaymentStart:
    """P-M05b-C, passos 1 i 2: l'intent queda «en curs» esperant l'extracte; no hi ha
    notificació. La referència és la del càrrec, que no canvia (RN-T20)."""
    iban = transfer_iban()
    if not iban:
        raise attempts.MethodNotAllowed(TRANSFER)
    if _in_progress(charge):
        raise attempts.AttemptInProgress
    attempt = attempts.create_attempt(charge, TRANSFER, **payer)
    attempt = attempts.transition(attempt, S.IN_PROGRESS, by=actor)
    return PaymentStart(
        attempt_id=attempt.pk,
        kind=TRANSFER_DETAILS,
        amount_cents=attempt.amount_cents,
        reference=treasury.transfer_reference(charge),
        club_iban=iban,
    )


def _owns(actor, charge) -> bool:
    if isinstance(actor, GuestLink):
        return _link_works(actor, charge)
    return isinstance(actor, Account) and actor.is_active and actor.person_id == charge.person_id


def _link_works(link: GuestLink, charge) -> bool:
    """V-02 i CA-02.2: l'enllaç només dona accés al seu càrrec i només mentre funciona. Es torna
    a llegir: un enllaç revocat o substituït fa un moment ja no obre cap intent nou (RN-31)."""
    stored = GuestLink.objects.select_related("person").filter(pk=link.pk).first()
    return (
        stored is not None
        and stored.charge_id == charge.pk
        and stored.person_id == charge.person_id
        and stored.is_live()
        and stored.person.status == Person.Status.ACTIVE
    )


def _payer(actor) -> tuple[object, dict]:
    """L'actor del registre i qui obre l'intent: el compte, o l'enllaç del convidat (que no té
    compte; al registre, «convidat» amb l'identificador intern de l'enllaç, CA-14.6)."""
    if isinstance(actor, GuestLink):
        return guest_links.actor(actor), {"guest_link": actor}
    return actor, {"started_by": actor}


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


def _urls(provider, charge, guest: bool) -> OrderUrls:
    site = settings.PUBLIC_SITE_URL
    back = site + (GUEST_RETURN_PATH if guest else RETURN_PATH)
    return OrderUrls(
        notification=site + reverse("payments:provider_notification", args=[provider.code]),
        return_ok=back.format(charge=charge.pk, result="ok"),
        return_ko=back.format(charge=charge.pk, result="ko"),
    )


def start_payment(charge: Charge, method: str, actor) -> PaymentStart:
    """`payments.start_payment`: obre l'intent i, al servidor, l'ordre del proveïdor amb
    l'import desat del càrrec i la clau d'idempotència de l'intent (RN-M05b-02). No rep cap
    import: no hi ha manera de passar-n'hi un.

    `actor`: el compte que paga, actiu i de la persona del càrrec, o l'enllaç de convidat del
    càrrec mentre funciona (T-M05b-08).

    Errors: `MethodNotAllowed`, `NotOwnCharge` i `ChargeNotPayable`, `AttemptInProgress`
    (RN-M05b-04: el nou s'espera), `LiveChargesNotAllowed` i els altres `ProviderError`. Amb
    qualsevol error no en queda res: ni intent ni ordre que algú pugui pagar."""
    # Nivell 1: tampoc cap transferència, que també és un cobrament real (RN-M05a-11). Abans de
    # la transacció, perquè la negativa quedi al registre (CA-M05a-09).
    ensure_charges_allowed("start_payment")
    if method not in attempts.SCREEN_METHODS:
        raise attempts.MethodNotAllowed(method)
    if _owns(actor, charge):
        _close_timed_out_bizum(charge)
    with transaction.atomic():
        # El càrrec queda bloquejat fins al final: dues peticions alhora van una darrere l'altra
        # i, mentre es parla amb el proveïdor, ningú no pot pagar ni anul·lar el càrrec.
        stored = Charge.objects.select_for_update().get(pk=charge.pk)
        if not _owns(actor, stored):
            raise NotOwnCharge
        by, payer = _payer(actor)
        if method == TRANSFER:
            return _start_transfer(stored, by, payer)
        provider = get_provider()
        capabilities = provider.capabilities()
        if not getattr(capabilities, method, False):
            raise attempts.MethodNotAllowed(method)
        _abandon_waiting_transfer(stored, by)
        if _in_progress(stored):
            raise attempts.AttemptInProgress
        attempt = attempts.create_attempt(stored, method, **payer)
        # Primer «en curs», que ocupa l'únic lloc del càrrec (índex únic), i després l'ordre:
        # si l'índex atura l'intent, el proveïdor no arriba a rebre res.
        attempt = attempts.transition(attempt, S.IN_PROGRESS, by=by)
        guest = isinstance(actor, GuestLink)
        order = provider.create_order(
            stored, method, _urls(provider, stored, guest), attempt.idempotency_key
        )
        attempt.provider_code = provider.code
        attempt.provider_order_id = order.external_id
        attempt.expires_at = order.expires_at
        attempt.save(
            update_fields=["provider_code", "provider_order_id", "expires_at", "updated_at"]
        )
        details = {"provider": provider.code, "order": order.external_id}
        audit.record("payments.order_created", actor=by, target=attempt, details=details)
    return PaymentStart(
        attempt_id=attempt.pk,
        kind=IFRAME if capabilities.embedded_field else REDIRECT,
        amount_cents=attempt.amount_cents,
        url=order.pay_url,
    )


class CardNotUsable(attempts.ChargeNotPayable):
    """La targeta guardada no pot cobrar aquesta quota; `case` diu per què (`CASES`)."""

    def __init__(self, case: str):
        super().__init__(case)
        self.case = case


class AlreadyAttempted(attempts.ChargeNotPayable):
    """La quota ja té un intent amb la targeta guardada (el primer cobrament; els reintents són
    de la T-M05b-24)."""


NOT_CHARGED = "payments.saved_card.not_charged"
SAVED_CARD_ACTOR = "payments.saved_card"
AUTHENTICATION = gettext_lazy("RN-M05b-20: el banc demana autenticació")
NOT_PENDING = gettext_lazy("La quota ha deixat d'estar pendent abans de cobrar-la.")
# Per què una targeta guardada no cobra una quota: el motiu per al tresorer i si s'avisa el soci
# (T-M05b-15b). Només la targeta que ja no serveix és cosa del soci; la resta, del tresorer.
CARD_CLOSED, NOT_MEMBER, PREFERENCE, PROVIDER, NOT_FEE, TRANSFER_WAITING = (
    "card_closed", "not_member", "preference", "provider", "not_fee", "transfer_waiting",
)  # fmt: skip
CASES = {
    CARD_CLOSED: (gettext_lazy("La targeta guardada ja no es pot fer servir."), True),
    NOT_MEMBER: (gettext_lazy("La persona ja no és sòcia activa ni impagada."), False),
    PREFERENCE: (gettext_lazy("La preferència de la quota ja no és aquesta targeta."), False),
    PROVIDER: (gettext_lazy("La targeta és d'un altre proveïdor."), False),
    NOT_FEE: (gettext_lazy("El càrrec no és una quota anual."), False),
    TRANSFER_WAITING: (
        gettext_lazy("Té una transferència en espera: no es cobra la targeta."),
        False,
    ),
}


def _expired(card: SavedCard, today) -> bool:
    if card.expiry_year is None or card.expiry_month is None:
        return False
    return (card.expiry_year, card.expiry_month) < (today.year, today.month)


def _unusable(card: SavedCard | None, charge: Charge, provider) -> str | None:
    """Per què la targeta no pot cobrar la quota (un cas de `CASES`), o None si pot: la targeta
    activa i no caducada, del proveïdor, de la preferència «targeta guardada» d'un soci actiu o
    impagat, per a una quota anual seva."""
    fee = getattr(charge, "annual_fee", None)
    if fee is None:
        return NOT_FEE
    if fee.member.status not in (Member.Status.ACTIVE, Member.Status.UNPAID):
        return NOT_MEMBER
    if not FeePaymentPreference.objects.filter(
        member_id=fee.member_id, method=SAVED_CARD, saved_card=card
    ).exists():
        return PREFERENCE
    if card.provider_code != provider.code:
        return PROVIDER
    if (
        card.status != SavedCard.Status.ACTIVE
        or card.person_id != charge.person_id
        or _expired(card, timezone.localdate())
    ):
        return CARD_CLOSED
    return None


def _open_saved_card_attempt(charge: Charge, card: SavedCard | None, provider):
    """Primera transacció, sota el bloqueig del càrrec i de la targeta (llegida de nou): les
    comprovacions i l'intent «en curs», amb la targeta i l'identificador que tindrà l'ordre al
    proveïdor, desats abans de cobrar. Així la notificació el troba encara que arribi abans que
    la resposta, i si la crida falla, la xarxa de seguretat pregunta per aquella ordre. Torna
    l'intent i la targeta."""
    by = audit.system(SAVED_CARD_ACTOR)
    with transaction.atomic():
        stored = Charge.objects.select_for_update().get(pk=charge.pk)
        if card is not None:
            card = SavedCard.objects.select_for_update().filter(pk=card.pk).first()
        if card is None:
            raise CardNotUsable(PREFERENCE)
        if case := _unusable(card, stored, provider):
            raise CardNotUsable(case)
        if stored.attempts.filter(method=SAVED_CARD).exists():
            raise AlreadyAttempted
        if stored.attempts.filter(status=S.IN_PROGRESS, method=TRANSFER).exists():
            raise CardNotUsable(TRANSFER_WAITING)  # si ja l'ha feta, pagaria dues vegades
        if _in_progress(stored):
            raise attempts.AttemptInProgress
        attempt = attempts.create_attempt(stored, SAVED_CARD)
        attempt = attempts.transition(attempt, S.IN_PROGRESS, by=by)
        attempt.provider_code = provider.code
        attempt.provider_order_id = provider.saved_card_order_id(attempt.idempotency_key)
        attempt.save(update_fields=["provider_code", "provider_order_id", "updated_at"])
        SavedCardAttempt.objects.create(attempt=attempt, card=card)
        return attempt, card


def _charge(attempt: PaymentAttempt, card: SavedCard, provider) -> PaymentAttempt:
    """Segona transacció, amb el mateix ordre de bloqueig que `settle` (càrrec i després intent):
    si la quota ja no és pendent o l'import ha canviat, l'intent es tanca sense cobrar; si no, es
    cobra l'import de l'intent. Una ordre diferent de l'esperada es desa (la seva notificació
    trobarà l'intent) i va «a revisar». Si el banc demana autenticació (RN-M05b-20, P-303),
    l'intent es tanca de seguida: ningú no la pot completar fora de sessió, i l'adreça no es desa
    ni s'envia enlloc."""
    by = audit.system(SAVED_CARD_ACTOR)
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=attempt.charge_id)
        attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        if attempt.status != S.IN_PROGRESS:
            return attempt
        if charge.status != Charge.Status.PENDING or charge.amount_cents != attempt.amount_cents:
            reason = str(NOT_PENDING)
            return attempts.transition(attempt, S.ABANDONED, by=by, reason=reason)
        order = provider.charge_saved_card(charge, card, attempt.idempotency_key)
        details = {"provider": attempt.provider_code, "order": order.external_id, "card": card.pk}
        audit.record("payments.order_created", actor=by, target=attempt, details=details)
        if order.external_id != attempt.provider_order_id:
            expected = attempt.provider_order_id
            attempt.provider_order_id = order.external_id
            attempt.save(update_fields=["provider_order_id", "updated_at"])
            reason = _("El proveïdor ha tornat l'ordre %(order)s en lloc de %(expected)s.") % {
                "order": order.external_id,
                "expected": expected,
            }
            processing.mark_for_review(None, attempt, reason)
        elif order.pay_url:
            attempt = attempts.transition(attempt, S.ABANDONED, by=by, reason=str(AUTHENTICATION))
    return attempt


def charge_saved_card(charge: Charge, card: SavedCard | None, *, provider=None) -> PaymentAttempt:
    """Cobra una quota amb la targeta guardada de la seva persona, sense que hi intervingui
    (T-M05b-15; RN-M05b-20). L'obre el sistema; «pagat» només arriba amb la notificació.
    `provider`: el de la tasca diària, que ja ha comprovat el nivell. Errors: `CardNotUsable`,
    `AlreadyAttempted`, `AttemptInProgress`, `LiveChargesNotAllowed` i els del proveïdor (amb
    l'intent «en curs» i la seva ordre, que tanca la xarxa de seguretat)."""
    if provider is None:
        ensure_charges_allowed("charge_saved_card")  # abans de cap transacció (CA-M05a-09)
        provider = get_provider()
    attempt, card = _open_saved_card_attempt(charge, card, provider)
    return _charge(attempt, card, provider)


def _not_charged(charge: Charge, card: SavedCard, case: str) -> None:
    """Una quota que aquesta targeta no pot cobrar, pel motiu `case`: al registre i «a revisar»
    per al tresorer, una sola vegada per càrrec, targeta i motiu (la marca, a la base de dades i
    sota el bloqueig del càrrec). La quota es continua provant cada dia: quan el motiu desapareix,
    es cobra. Els avisos al soci són de la T-M05b-15b."""
    with transaction.atomic():
        charge = Charge.objects.select_for_update().get(pk=charge.pk)
        notice, new = SavedCardNotice.objects.get_or_create(charge=charge, card=card, case=case)
        if not new:
            return
        reason = str(CASES[case][0])
        by = audit.system(SAVED_CARD_ACTOR)
        audit.record(NOT_CHARGED, actor=by, target=charge, reason=reason, details={"case": case})
        processing.mark_for_review(None, charge, reason)


def due_saved_card_charges(today):
    """Les quotes pendents que ja han vençut dels socis que paguen amb la targeta guardada, amb
    la targeta de la preferència (P-302: el dia del venciment). Què se'n fa ho decideix
    `charge_saved_card`, sota el bloqueig del càrrec."""
    preferences = FeePaymentPreference.objects.filter(method=SAVED_CARD)
    cards = {p.member_id: p.saved_card for p in preferences.select_related("saved_card")}
    due = (
        Charge.objects.filter(
            status=Charge.Status.PENDING,
            annual_fee__member_id__in=cards,
            annual_fee__due_on__lte=today,
        )
        .exclude(attempts__method=SAVED_CARD)
        .select_related("annual_fee")
        .order_by("pk")
    )
    return [(c, cards[c.annual_fee.member_id]) for c in due]


def charge_due_saved_cards() -> int:
    """La tasca diària: cobra cada quota de `due_saved_card_charges` i torna quantes ordres ha
    obert. Sense res per cobrar, no passa per la salvaguarda (cap negativa diària al registre);
    si no, una sola salvaguarda i un sol proveïdor per passada. Un error en un càrrec no atura
    els altres."""
    if not charges_allowed():
        return 0  # nivell 1: res a cobrar, i res al registre cada dia
    due = due_saved_card_charges(timezone.localdate())
    provider = get_provider() if due else None
    started = 0
    for charge, card in due:
        try:
            try:
                charge_saved_card(charge, card, provider=provider)
                started += 1
            except CardNotUsable as error:
                _not_charged(charge, card, error.case)
            except (attempts.ChargeNotPayable, attempts.AttemptInProgress):
                pass  # ja té un intent, o ja no és pendent
        except Exception:
            logger.exception("No s'ha pogut cobrar el càrrec %s amb la targeta guardada", charge.pk)
    return started
