"""Transferència confirmada a la conciliació de la 04 → intent pagat i rebut (T-M05b-06; P-M05b-C,
pas 3; CA-M05b-11; RN-M05b-19).

La conciliació (`treasury.reconciliation.confirm`, T-M04-12) crea el pagament per transferència
amb `charges.record_payment`, que passa el càrrec a «pagat», i en registra l'ingrés. Aquí només
es fa la part del 05b, a la mateixa transacció: l'intent de transferència que s'esperava passa a
«pagat» (o se n'obre un, si el soci ha pagat sense passar per la pantalla) i s'emet el rebut,
amb el correu al pagador. Si alguna cosa falla, la conciliació es desfà sencera.

shortcut: escolta el `post_save` del pagament de la 00; quan existeixi l'esdeveniment
`charge.paid` (049, T-M05b-21), s'hi subscriu i aquest senyal se'n va."""

from django.db import transaction

from apps.core import audit
from apps.core.models import Payment

from . import attempts, receipts
from .models import PaymentAttempt

S = PaymentAttempt.Status
TRANSFER = PaymentAttempt.Method.TRANSFER
RECEIPT_PENDING = "payments.transfer_receipt_pending"


def on_payment_saved(sender, instance: Payment, created: bool, **kwargs) -> None:
    if not created or instance.method != Payment.Method.TRANSFER:
        return
    charge = instance.charge  # encara «pendent»: `record_payment` el passa a pagat després
    by = audit.system("payments")
    attempt = PaymentAttempt.objects.filter(charge=charge, method=TRANSFER, status=S.IN_PROGRESS)
    attempt = attempt.first()
    try:
        with transaction.atomic():
            if attempt is None:
                attempt = attempts.create_attempt(charge, TRANSFER)
                attempt = attempts.transition(attempt, S.IN_PROGRESS, by=by)
            attempt = attempts.transition(attempt, S.PAID, by=by)
    except attempts.AttemptInProgress:
        # P-137 (opció per defecte): una targeta o un Bizum encara en curs ocupa l'únic lloc del
        # càrrec. El càrrec queda pagat igualment; el rebut, no, i el tresorer ho veu al registre.
        reason = "P-137: transferència conciliada amb un altre intent en curs; sense rebut"
        audit.record(RECEIPT_PENDING, actor=by, target=charge, reason=reason)
        return
    receipts.issue(attempt)
