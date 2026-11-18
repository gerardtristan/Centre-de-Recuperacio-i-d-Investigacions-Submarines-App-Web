"""Decidir un intent «a revisar» (T-M05b-16b i 16c; 097, P-82 opció C; B6 amb edició, P-377).

El tresorer en tria el resultat amb una nota obligatòria:
- **Pagat** (RN-M05b-03: «a revisar → pagat»): el proveïdor l'ha cobrat. Es registra el
  pagament com ho fa una notificació (`processing.pay`: pagament, ingrés, rebut i, si és una
  quota, l'avís al 01), només si el càrrec encara és pendent; si ja és pagat, es rebutja (mai dos
  pagaments: el cobrament de més es torna amb una devolució).
- **Fallit** («a revisar → fallit»): no s'ha cobrat. No es mou cap diner.

Queda una fila nova (`ReviewClosure`: qui, quan i el resultat) i l'entrada al registre d'activitat
amb la nota, sobre el tancament (`privacy.audit_targets`: l'esborrat RGPD del pagador la
substitueix per la referència). El canvi d'estat de l'intent porta un motiu fix, sense la nota."""

from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.models import Charge
from apps.core.permissions import has_perm

from . import attempts, processing
from .models import PaymentAttempt, ReviewClosure

VIEW = "payments.view"  # B6
CLOSED = "payments.review_closed"
MAX_NOTE = 500
S = PaymentAttempt.Status


class NotClosable(Exception):
    """L'intent ja no és «a revisar» (ja s'ha decidit)."""


class ChargeNotPending(Exception):
    """«Pagat» amb el càrrec que ja no és pendent: es pagaria dues vegades."""


def close(attempt: PaymentAttempt, *, outcome: str, note: str, by) -> ReviewClosure:
    if not has_perm(by, VIEW, write=True):
        raise Http404
    if outcome not in ReviewClosure.OUTCOMES:
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
        if outcome == S.PAID and charge.status != Charge.Status.PENDING:
            raise ChargeNotPending
        closure = ReviewClosure.objects.create(attempt=locked, outcome=outcome, closed_by=by)
        reason = _("Decisió del tresorer (tancament %(id)s)") % {"id": closure.pk}
        if outcome == S.PAID:
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
