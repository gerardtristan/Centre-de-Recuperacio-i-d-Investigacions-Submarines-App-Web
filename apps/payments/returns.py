"""Rebuts domiciliats retornats: codi de motiu, reintent i alternativa (T-M05b-12; P-M05b-F;
RN-M05b-14, 15 i 18; CA-M05b-18 a 20).

- `register_return`: el tresorer (B4) registra el retorn d'un rebut cobrat amb el codi del banc.
  Tot o res: càrrec «retornat» i pagament anul·lat (00), la sortida i la comissió de retorn
  (04), l'intent «cancel·lat» i el rebut anul·lat amb una nota (P-290), l'avís a qui edita les
  quotes (01) i, si el compte és tancat o no hi ha mandat, el mandat «bloquejat». Torna la
  proposta segons el codi (RN-M05b-15; codis desconeguts, P-291).
- `confirm`: el tresorer confirma o canvia la proposta (P-M05b-F, passos 4 i 5; P-292). El
  càrrec torna a «pendent» amb el motiu (048) i, amb l'alternativa, el soci rep el correu amb
  l'enllaç per pagar i, si el mandat s'ha bloquejat, el de signar-ne un de nou. Amb el reintent,
  la quota torna a la remesa següent; com a molt `payments.max_direct_debit_attempts` rebuts per
  càrrec (VC-16).

shortcut: entrada manual del codi; el lector del fitxer de retornats del banc (pain.002, banc
fals de la 092) ve després, perquè el format real és [A verificar: P-45 punt 5].
"""

import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, business_settings, charges, mail
from apps.members import recipients
from apps.members import services as members
from apps.treasury import services as treasury

from . import attempts
from .models import DirectDebitItem, PaymentAttempt, Receipt, ReceiptCancellation, SepaMandate

MAX_ATTEMPTS = "payments.max_direct_debit_attempts"  # VC-16, RN-M05b-15
ALTERNATIVE_TEMPLATE = "alternativa-pagament"

RETRY, ALTERNATIVE = "retry", "alternative"
# RN-M05b-15: els codis d'exemple de la regla. Quins arriben de veritat, [A verificar: banc].
INSUFFICIENT_FUNDS = frozenset({"AM04"})
NO_MANDATE = frozenset({"AC04", "MD01"})
CODE = re.compile(r"[A-Z0-9]{4}")
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


def max_attempts() -> int:
    """Rebuts domiciliats per càrrec com a molt, amb el valor vigent avui (VC-16)."""
    return business_settings.get(MAX_ATTEMPTS)


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
    `confirm`. Sense B4, «no trobat» (`charges.mark_returned`)."""
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
    treasury.record_return(cancellation.payment, fee_cents, by=by)
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
    if code in NO_MANDATE and mandate.status == SepaMandate.Status.ACTIVE:
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
    proposal = RETRY if code in INSUFFICIENT_FUNDS and can_retry(item) else ALTERNATIVE
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
    return proposal


@transaction.atomic
def confirm(item: DirectDebitItem, decision: str, *, by, note: str = "") -> bool:
    """P-M05b-F, passos 4 i 5 (048): reintent o alternativa. Torna si s'ha posat a la cua el
    correu de l'alternativa (sense adreça o amb el reintent, no)."""
    if decision not in (RETRY, ALTERNATIVE):
        raise ValueError(decision)
    item = DirectDebitItem.objects.select_related("attempt__charge__person", "mandate").get(
        pk=item.pk
    )
    charge = item.attempt.charge
    latest = DirectDebitItem.objects.filter(attempt__charge=charge).latest("pk")
    if item.status != DirectDebitItem.Status.RETURNED or latest.pk != item.pk:
        raise NotReturned
    if decision == RETRY and not can_retry(item):
        raise RetryNotAllowed
    default = (
        _("Reintent a la remesa següent") if decision == RETRY else _("Alternativa de pagament")
    )
    charges.reopen_returned(charge, note.strip() or default, by=by)
    sent = False
    if decision == ALTERNATIVE:
        sent = _send_alternative(
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


def _send_alternative(charge, *, new_mandate: bool) -> bool:
    """L'enllaç per pagar amb targeta, Bizum o transferència i, si cal, el de signar un mandat
    nou. Cap IBAN ni codi del banc al correu."""
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
    }
    return (
        mail.queue_email(ALTERNATIVE_TEMPLATE, to=to, person=charge.person, context=context)
        is not None
    )
