"""Decidir un intent «a revisar» (T-M05b-16b i 16c; 097, P-82 opció C; B6 amb edició, P-377).

El tresorer en tria el resultat amb una nota obligatòria:
- **Pagat** (RN-M05b-03: «a revisar → pagat»): el proveïdor l'ha cobrat. Es registra el
  pagament com ho fa una notificació (`processing.pay`: pagament, ingrés, rebut i, si és una
  quota, l'avís al 01). Demana també M14 (pagament a mà) i les seves guardes: el càrrec pendent i
  no és seu, cap altre intent que el pugui cobrar, i que l'import quadri (CA-M05b-05); si no, es
  rebutja (mai dos pagaments ni un import que no s'ha cobrat).
- **Fallit** («a revisar → fallit»): no s'ha cobrat. No es mou cap diner.

Queda una fila nova (`ReviewClosure`: qui, quan i el resultat) i l'entrada al registre d'activitat
amb la nota, sobre el tancament (`privacy.audit_targets`: l'esborrat RGPD del pagador la
substitueix per la referència). El canvi d'estat de l'intent porta un motiu fix, sense la nota."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit, charges
from apps.core.charges import MANUAL_PAYMENT
from apps.core.models import Charge
from apps.core.permissions import has_perm

from . import attempts, processing
from .models import PaymentAttempt, ReviewClosure, ReviewCode

VIEW = "payments.view"  # B6
CLOSED = "payments.review_closed"
MAX_NOTE = 500
S = PaymentAttempt.Status
OUTCOME = ReviewClosure.Outcome


class NotClosable(Exception):
    """L'intent ja no és «a revisar» (ja s'ha decidit)."""


class PaidRefused(Exception):
    """«Pagat» no es pot triar; el missatge diu per què."""


def close(attempt: PaymentAttempt, *, outcome: str, note: str, by) -> ReviewClosure:
    if not has_perm(by, VIEW, write=True):
        raise Http404
    if outcome not in ReviewClosure.OUTCOMES:  # «sense decisió» no es tria
        raise ValueError(_("Tria si s'ha pagat o ha fallat."))
    note = (note or "").strip()
    if not note:
        raise ValueError(_("Cal una nota per tancar-lo."))
    if len(note) > MAX_NOTE:
        raise ValueError(_("La nota no pot passar de %(max)s caràcters.") % {"max": MAX_NOTE})
    with transaction.atomic():
        # El càrrec i després l'intent, en el mateix ordre que `processing.settle`.
        charge = Charge.objects.select_for_update().get(pk=attempt.charge_id)
        locked = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        if locked.status != S.TO_REVIEW:
            raise NotClosable
        if outcome == OUTCOME.PAID:
            _check_paid(locked, charge, by)
        closure = ReviewClosure.objects.create(
            attempt=locked, outcome=outcome, review_reason=locked.review_reason, closed_by=by
        )
        reason = _("Decisió del tresorer (tancament %(id)s)") % {"id": closure.pk}
        if outcome == OUTCOME.PAID:
            processing.pay(
                locked,
                charge,
                by=by,
                status=S.PAID,
                reference=locked.provider_order_id,
                reason=reason,
            )
        else:
            attempts.transition(locked, S.FAILED, by=by, reason=reason)
        details = {"attempt": locked.pk, "outcome": outcome}
        audit.record(CLOSED, actor=by, target=closure, reason=note, details=details)
    return closure


def can_record_paid(account, charge) -> bool:
    """«Pagat» registra un pagament: a més de B6 amb edició, cal M14 (pagament a mà)."""
    return has_perm(account, MANUAL_PAYMENT, charge, write=True)


def _check_paid(attempt, charge, by) -> None:
    """M14 i les guardes del pagament a mà (P-12; `charges.check_manual_payment`, la mateixa
    llista), i l'import: mai dos pagaments ni un import que no s'ha cobrat."""
    if not can_record_paid(by, charge):
        raise Http404
    if charge.status != Charge.Status.PENDING:
        raise PaidRefused(
            _(
                "El càrrec ja no és pendent: no es pot registrar un altre pagament. Si el "
                "proveïdor l'ha cobrat, tria «Fallit» i fes-ne la devolució."
            )
        )
    if attempt.review_code == ReviewCode.AMOUNT:
        raise PaidRefused(
            _(
                "L'import cobrat no és el del càrrec: no es pot donar per pagat. Tria «Fallit» "
                "i registra el que s'hagi cobrat amb un pagament a mà o una devolució."
            )
        )
    try:
        charges.check_manual_payment(charge, by, deciding=attempt)
    except ValidationError as error:
        raise PaidRefused(" ".join(error.messages)) from None
