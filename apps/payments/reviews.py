"""Tancar un intent «a revisar» (T-M05b-16b; P-82, opció per defecte; B6 amb edició).

Tancar-lo només deixa constància que el tresorer l'ha revisat i per què: una fila nova
(`ReviewClosure`, qui i quan) i l'entrada al registre d'activitat amb la nota, sobre el tancament
(`privacy.audit_targets`: l'esborrat RGPD del pagador la substitueix per la referència).
L'intent es queda «a revisar» (RN-M05b-03 no en preveu cap sortida) i no es mou cap diner: una
devolució, un pagament a mà o una conciliació es fan a la seva pantalla."""

from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.permissions import has_perm

from .models import PaymentAttempt, ReviewClosure

VIEW = "payments.view"  # B6
CLOSED = "payments.review_closed"
MAX_NOTE = 500


class NotClosable(Exception):
    """L'intent no és «a revisar» o ja està tancat."""


def close(attempt: PaymentAttempt, *, note: str, by) -> ReviewClosure:
    if not has_perm(by, VIEW, write=True):
        raise Http404
    note = (note or "").strip()
    if not note:
        raise ValueError(_("Cal una nota per tancar-lo."))
    if len(note) > MAX_NOTE:
        raise ValueError(_("La nota no pot passar de %(max)s caràcters.") % {"max": MAX_NOTE})
    with transaction.atomic():
        locked = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        if locked.status != PaymentAttempt.Status.TO_REVIEW or hasattr(locked, "review_closure"):
            raise NotClosable
        closure = ReviewClosure.objects.create(attempt=locked, closed_by=by)
        audit.record(CLOSED, actor=by, target=closure, reason=note, details={"attempt": locked.pk})
    return closure
