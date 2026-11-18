"""Rebuts domiciliats retornats: codi de motiu, reintent i alternativa (T-M05b-12; P-M05b-F;
RN-M05b-14, 15 i 18; CA-M05b-18 a 20).

- `register_return`: el tresorer (B4) registra el retorn d'un rebut cobrat amb el codi del banc.
  Tot o res: càrrec «retornat» i pagament anul·lat (00), la sortida i la comissió de retorn
  (04), l'intent «cancel·lat» i el rebut anul·lat amb una nota (P-290), l'avís a qui edita les
  quotes (01) i, si el codi és a `payments.return_codes_block_mandate`, el mandat «bloquejat».
  Torna la proposta segons el codi (RN-M05b-15): reintent amb els de
  `payments.return_codes_retry` i alternativa amb la resta, també els desconeguts. Les dues
  llistes són ajustos que edita el tresorer (P-291, 095; provisional fins que ho confirmi el
  banc) i es llegeixen en registrar el retorn. Si no queda cap reintent
  possible (intents esgotats o sense mandat actiu), l'alternativa ja s'aplica i s'envia en
  registrar-lo, amb el tresorer com a autor, i torna `SENT` (CA-M05b-19, 20 i 32; P-292).
- `confirm`: el tresorer confirma o canvia la proposta (P-M05b-F, passos 4 i 5; P-292). El
  càrrec torna a «pendent» amb el motiu (048) i, amb l'alternativa, el soci rep el correu amb
  l'enllaç per pagar i, si el mandat s'ha bloquejat, el de signar-ne un de nou. Amb el reintent,
  la quota torna a la remesa següent; com a molt `payments.max_direct_debit_attempts` rebuts per
  càrrec (VC-16).

El fitxer de retornats del banc (pain.002) passa per aquí mateix: `bank_returns` (T-M05b-12b).
"""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, charges, mail
from apps.core.models import Charge, Setting
from apps.core.permissions import has_perm
from apps.members import recipients
from apps.members import services as members
from apps.treasury import services as treasury
from apps.treasury.models import Movement

from . import attempts
from .models import DirectDebitItem, PaymentAttempt, Receipt, ReceiptCancellation, SepaMandate

MAX_ATTEMPTS = "payments.max_direct_debit_attempts"  # VC-16, RN-M05b-15
ALTERNATIVE_TEMPLATE = "alternativa-pagament"

RETRY, ALTERNATIVE, SENT = "retry", "alternative", "alternative_sent"
# P-291 (095): quins codis proposen un reintent i quins bloquegen el mandat són ajustos; d'entrada,
# els exemples de RN-M05b-15. Un codi que no és a cap llista va a l'alternativa.
RETRY_CODES = "payments.return_codes_retry"
BLOCK_CODES = "payments.return_codes_block_mandate"
CODE = re.compile(r"[A-Z0-9]{4}")
SEPARATORS = re.compile(r"[\s,;]+")
LABELS = {
    "AM04": "fons insuficients",
    "MS02": "refús del deutor",
    "MD06": "refús del deutor",
    "AC04": "compte tancat",
    "MD01": "sense mandat",
}


class NotCollected(Exception):
    """El rebut no consta com a cobrat: no hi ha res a retornar."""


class NotReturned(Exception):
    """El rebut no és l'últim retorn del càrrec, o el càrrec ja no és «retornat»."""


class RetryNotAllowed(Exception):
    """RN-M05b-15: intents esgotats o sense mandat actiu."""


def _ensure_b4(by) -> None:
    if not has_perm(by, charges.RETURNS, write=True):
        raise Http404


def max_attempts() -> int:
    """Rebuts domiciliats per càrrec com a molt, amb el valor vigent avui (VC-16)."""
    return business_settings.get(MAX_ATTEMPTS)


RETURN_CODE_LISTS = (RETRY_CODES, BLOCK_CODES)


def _split(value) -> list[str]:
    return [code for code in SEPARATORS.split(value.upper()) if code]


def normalise_codes(value):
    """Forma canònica: majúscules, ordenats i separats per «, » (P-291). Un valor que no és un
    text el rebutja la peça d'ajustos."""
    return ", ".join(sorted(_split(value))) if isinstance(value, str) else value


def codes(key: str) -> set[str]:
    """Els codis d'una llista, amb el valor vigent avui (P-291). Sense l'ajust, cap codi."""
    try:
        return set(_split(business_settings.get(key)))
    except Setting.DoesNotExist:
        return set()


def check_codes(key: str):
    """La comprovació d'una llista (P-291), que `apps.PaymentsConfig.ready` registra a la peça
    d'ajustos: codis de quatre lletres o xifres, sense repetir, i cap que ja sigui a una altra
    de les llistes de `RETURN_CODE_LISTS`."""

    def check(value: str) -> None:
        found = _split(value)
        if not all(CODE.fullmatch(code) for code in found):
            raise ValidationError(
                _(
                    "Cada codi té quatre lletres o xifres. Separa'ls amb comes, espais o "
                    "punts i comes."
                )
            )
        if len(set(found)) != len(found):
            raise ValidationError(_("La llista no pot tenir codis repetits."))
        others = set().union(*(codes(other) for other in RETURN_CODE_LISTS if other != key))
        if both := sorted(set(found) & others):
            raise ValidationError(
                _("Un codi només pot tenir una acció: %(codes)s ja és a una altra llista.")
                % {"codes": ", ".join(both)}
            )

    return check


def can_retry(item: DirectDebitItem) -> bool:
    active = SepaMandate.objects.filter(
        member_id=item.mandate.member_id, status=SepaMandate.Status.ACTIVE
    )
    return item.attempt_number < max_attempts() and active.exists()


@transaction.atomic
def register_return(
    item: DirectDebitItem, reason_code: str, *, fee_cents: int | None = None, by
) -> str:
    """P-M05b-F, passos 1 a 3. Torna `RETRY` o `ALTERNATIVE`; el tresorer la confirma amb
    `confirm`. Sense B4, «no trobat», abans de mirar res (T-M05b-25)."""
    _ensure_b4(by)
    retry_codes, block_codes = codes(RETRY_CODES), codes(BLOCK_CODES)  # un sol cop (P-291)
    code = (reason_code or "").strip().upper()
    if not CODE.fullmatch(code):
        raise ValidationError(_("El codi de motiu del banc té quatre lletres o xifres."))
    item = (
        DirectDebitItem.objects.select_for_update()
        .select_related("attempt__charge", "mandate")
        .get(pk=item.pk)
    )
    if item.status != DirectDebitItem.Status.COLLECTED:
        raise NotCollected(item.status)
    charge = item.attempt.charge
    reason = f"{code}: {LABELS.get(code, 'motiu del banc')}"
    cancellation = charges.mark_returned(charge, reason, by=by)
    payment = cancellation.payment
    treasury.record_return(payment, fee_cents, by=by, account=_settled_into(payment))
    attempt = attempts.transition(
        item.attempt, PaymentAttempt.Status.CANCELLED, by=by, reason=reason
    )
    receipt = Receipt.objects.filter(attempt=attempt).first()
    if receipt is not None:
        ReceiptCancellation.objects.create(receipt=receipt, note=f"Rebut retornat: {reason}")
    item.status = DirectDebitItem.Status.RETURNED
    item.return_reason_code, item.returned_on = code, timezone.localdate()
    item.save(update_fields=["status", "return_reason_code", "returned_on"])
    mandate = item.mandate
    if code in block_codes and mandate.status == SepaMandate.Status.ACTIVE:
        mandate.status = SepaMandate.Status.BLOCKED
        mandate.save(update_fields=["status"])
        audit.record(
            "payments.mandate.blocked",
            actor=by,
            target=mandate,
            field="status",
            old=SepaMandate.Status.ACTIVE,
            new=SepaMandate.Status.BLOCKED,
            reason=reason,
            details={"reference": mandate.reference},
        )
    fee = getattr(charge, "annual_fee", None)
    if fee is not None:
        members.on_fee_returned(fee.pk)  # RN-M05b-18: avís; l'impagat és manual (040)
    proposal = RETRY if code in retry_codes and can_retry(item) else ALTERNATIVE
    audit.record(
        "payments.return.registered",
        actor=by,
        target=item,
        reason=reason,
        details={
            "code": code,
            "proposal": proposal,
            "attempt_number": item.attempt_number,
            "fee_cents": fee_cents,
        },
    )
    if proposal == ALTERNATIVE and not can_retry(item):
        confirm(item, ALTERNATIVE, by=by, note=_("Cap reintent possible: alternativa de pagament"))
        return SENT
    return proposal


@transaction.atomic
def confirm(item: DirectDebitItem, decision: str, *, by, note: str = "") -> bool:
    """P-M05b-F, passos 4 i 5 (048): reintent o alternativa. Torna si s'ha posat a la cua el
    correu de l'alternativa (sense adreça o amb el reintent, no). Sense B4, «no trobat»."""
    _ensure_b4(by)
    if decision not in (RETRY, ALTERNATIVE):
        raise ValueError(decision)
    item = DirectDebitItem.objects.select_related("attempt__charge__person", "mandate").get(
        pk=item.pk
    )
    charge = item.attempt.charge
    latest = DirectDebitItem.objects.filter(attempt__charge=charge).latest("pk")
    returned = item.status == DirectDebitItem.Status.RETURNED and latest.pk == item.pk
    if not returned or charge.status != Charge.Status.RETURNED:
        raise NotReturned
    if decision == RETRY and not can_retry(item):
        raise RetryNotAllowed
    default = (
        _("Reintent a la remesa següent") if decision == RETRY else _("Alternativa de pagament")
    )
    charges.reopen_returned(charge, note.strip() or default, by=by)
    sent = False
    if decision == ALTERNATIVE:
        sent = send_alternative(
            charge, new_mandate=item.mandate.status == SepaMandate.Status.BLOCKED
        )
    audit.record(
        "payments.return.confirmed",
        actor=by,
        target=item,
        reason=note.strip() or default,
        details={"decision": decision, "email_queued": sent},
    )
    return sent


def _settled_into(payment):
    """P-286 (opció C): un rebut cobrat ja és d'una remesa liquidada, de manera que el net ha
    passat del trànsit «Remeses SEPA» al banc (RN-T24); el retorn i la comissió surten d'allà,
    on els carrega el banc."""
    transfer = Movement.objects.get(
        kind=Movement.Kind.TRANSFER,
        direction=Movement.Direction.IN,
        settlement__items__payment=payment,
    )
    return transfer.account


def send_alternative(
    charge, *, new_mandate: bool, saved_card: bool = False, unusable: bool = False
) -> bool:
    """L'enllaç per pagar amb targeta, Bizum o transferència i, si cal, el de signar un mandat
    nou. Cap IBAN ni codi del banc al correu. `saved_card`: no s'ha pogut cobrar amb la targeta
    guardada (T-M05b-15b), en lloc d'un rebut retornat; `unusable`: la targeta ja no serveix i no
    s'ha intentat cap cobrament."""
    to = recipients.email_for(charge.person)
    if not to:
        return False
    context = {
        "concept": charge.concept,
        "amount": charges.euros(charge.amount_cents),
        "link": settings.PUBLIC_SITE_URL + reverse("payments:charge", args=[charge.pk]),
        "mandate_link": (
            settings.PUBLIC_SITE_URL + reverse("payments:mandate") if new_mandate else ""
        ),
        "saved_card": saved_card,
        "unusable": unusable,
    }
    return (
        mail.queue_email(ALTERNATIVE_TEMPLATE, to=to, person=charge.person, context=context)
        is not None
    )
