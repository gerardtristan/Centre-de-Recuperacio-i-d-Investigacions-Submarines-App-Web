"""Recordatori d'una transferència que no arriba (T-M05b-22c; RN-M05b-09; P-M05b-C, pas 4; P-407,
opció A).

Una transferència que s'espera és un intent «en curs» amb el mètode transferència
(`checkout._start_transfer`). Si no ha arribat en `payments.transfer_reminder_days` dies (VC-16:
30, de 7 a 60, l'edita el Tresorer), la tasca diària el tanca com a «caducat»: el càrrec, que
no ha deixat mai de ser «pendent», es queda sense intent obert i es pot tornar a pagar. Al
pagador li surt un recordatori amb la referència de la transferència i l'enllaç per pagar; cap
IBAN. Tot en una transacció per intent: el canvi d'estat és la marca que impedeix un segon
correu (una segona passada ja no el troba «en curs»). Si la transferència arriba després, la
conciliació paga l'intent caducat (RN-M05b-03: «caducat → pagat»).

Text del correu provisional [A validar: tresorer] (RN-M05b-09)."""

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.core import audit, business_settings, charges, mail
from apps.members import recipients
from apps.treasury import services as treasury

from . import attempts
from .models import PaymentAttempt

logger = logging.getLogger(__name__)

DAYS = "payments.transfer_reminder_days"  # VC-16
TEMPLATE = "recordatori-transferencia"
SENT = "payments.transfer_reminder_sent"
S, M = PaymentAttempt.Status, PaymentAttempt.Method


def send_due(now=None) -> int:
    """Tanca les transferències que fa massa que s'esperen i n'envia el recordatori. Torna quantes
    n'ha tancat."""
    now = now or timezone.now()
    limit = now - timedelta(days=business_settings.get(DAYS))
    due = PaymentAttempt.objects.filter(
        method=M.TRANSFER, status=S.IN_PROGRESS, created_at__lte=limit
    ).values_list("pk", flat=True)
    closed = 0
    for attempt_id in list(due):
        try:
            closed += _close(attempt_id, limit)
        except Exception:  # un intent que falla no atura els altres
            logger.exception("Recordatori de transferència: intent %s", attempt_id)
    return closed


def _close(attempt_id: int, limit) -> int:
    with transaction.atomic():
        attempt = (
            PaymentAttempt.objects.select_for_update(skip_locked=True)
            .select_related("charge__person")
            .filter(pk=attempt_id, method=M.TRANSFER, status=S.IN_PROGRESS, created_at__lte=limit)
            .first()
        )
        if attempt is None:
            return 0
        actor = audit.system("payments.transfer_reminders")
        attempts.transition(
            attempt, S.EXPIRED, by=actor, reason="RN-M05b-09: la transferència no ha arribat"
        )
        sent = _send(attempt.charge)
        audit.record(SENT, actor=actor, target=attempt, details={"email_sent": sent})
    return 1


def _send(charge) -> bool:
    """La referència de la transferència i l'enllaç per pagar; cap IBAN."""
    to = recipients.email_for(charge.person)
    if not to:
        return False
    context = {
        "concept": charge.concept,
        "amount": charges.euros(charge.amount_cents),
        "reference": treasury.transfer_reference(charge),
        "link": settings.PUBLIC_SITE_URL + reverse("payments:charge", args=[charge.pk]),
    }
    return mail.queue_email(TEMPLATE, to=to, person=charge.person, context=context) is not None
