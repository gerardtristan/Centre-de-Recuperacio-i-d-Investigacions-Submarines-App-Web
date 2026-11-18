"""Transferència confirmada a la conciliació de la 04 → intent pagat i rebut (T-M05b-06; P-M05b-C,
pas 3; CA-M05b-11; RN-M05b-19).

La conciliació (`treasury.reconciliation.confirm`, T-M04-12) crea el pagament per transferència
amb `charges.record_payment`, que passa el càrrec a «pagat», i en registra l'ingrés. Aquí només
es fa la part del 05b, a la mateixa transacció: l'intent de transferència que s'esperava passa a
«pagat» (o se n'obre un, si el soci ha pagat sense passar per la pantalla) i s'emet el rebut,
amb el correu al pagador. Si alguna cosa falla, la conciliació es desfà sencera.

A l'inrevés (045; T-M05b-29): quan el tresorer torna a pendent un càrrec que una transferència
conciliada va pagar per error (`charges.revert_paid_transfer`), l'intent pagat passa a
«cancel·lat» (P-122) i el seu rebut queda anul·lat amb una nota, a la mateixa transacció. Res
s'esborra, i el càrrec es pot tornar a pagar amb un intent i un rebut nous.

shortcut: escolta el `post_save` del pagament i de l'anul·lació de la 00. `charge.paid` (049,
T-M05b-21) ja existeix, però es lliura per la cua, després de confirmar-se la conciliació, i el
rebut ha de sortir a la mateixa transacció que el pagament (T-M05b-07); l'anul·lació no és cap
esdeveniment aprovat. Es mou quan es respongui la P-246."""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core import audit
from apps.core.models import Payment, PaymentCancellation

from . import attempts, receipts
from .models import PaymentAttempt, Receipt, ReceiptCancellation

S = PaymentAttempt.Status
RECEIPT_ON_SAVE = (Payment.Method.TRANSFER, Payment.Method.MANUAL)
RECEIPT_PENDING = "payments.transfer_receipt_pending"
RECEIPT_CANCELLED = "payments.receipt_cancelled"


def on_payment_saved(sender, instance: Payment, created: bool, **kwargs) -> None:
    """També el pagament registrat a mà (P-12; `charges.record_manual_payment`): un intent
    «manual» que neix pagat, amb el seu rebut, igual que una transferència sense intent. Un
    pagament a mà no conviu amb cap altre intent en curs (cobrament doble) i, sense rebut, no es
    desa: el `ValidationError` desfà tot el registre."""
    if not created or instance.method not in RECEIPT_ON_SAVE:
        return
    method = instance.method
    manual = method == Payment.Method.MANUAL
    if manual:  # la 00 ja ho ha comprovat; aquí, per si de cas, dins la mateixa transacció
        attempts.ensure_manual_payment_allowed(instance.charge)
    charge = instance.charge  # encara «pendent»: `record_payment` el passa a pagat després
    by = audit.system("payments")
    attempt = PaymentAttempt.objects.filter(charge=charge, method=method, status=S.IN_PROGRESS)
    attempt = attempt.first()
    try:
        with transaction.atomic():
            if attempt is None:
                attempt = attempts.create_attempt(charge, method)
                attempt = attempts.transition(attempt, S.IN_PROGRESS, by=by)
            attempt = attempts.transition(attempt, S.PAID, by=by)
    except (attempts.AttemptAlreadyPaid, attempts.ChargeNotPayable):
        if manual:
            raise ValidationError(attempts.MANUAL_ALREADY_PAID) from None
        raise
    except attempts.AttemptInProgress:
        if manual:
            raise ValidationError(attempts.MANUAL_IN_FLIGHT) from None
        # P-137 (opció per defecte): una targeta o un Bizum encara en curs ocupa l'únic lloc del
        # càrrec. El càrrec queda pagat igualment; el rebut, no, i el tresorer ho veu al registre.
        reason = "P-137: pagament confirmat amb un altre intent en curs; sense rebut"
        audit.record(RECEIPT_PENDING, actor=by, target=charge, reason=reason)
        return
    receipts.issue(attempt)


def on_cancellation_saved(sender, instance: PaymentCancellation, created: bool, **kwargs) -> None:
    """Una transferència (045) o un pagament a mà (P-12) anul·lats: l'intent pagat passa a
    «cancel·lat» i el rebut queda anul·lat amb una nota."""
    payment = instance.payment
    if not created or payment.method not in RECEIPT_ON_SAVE:
        return
    paid = PaymentAttempt.objects.filter(
        charge=payment.charge, method=payment.method, status=S.PAID
    )
    attempt = paid.first()
    if attempt is None:  # P-137: la transferència es va conciliar sense intent pagat ni rebut
        return
    by, reason = instance.cancelled_by, instance.reason
    attempt = attempts.transition(attempt, S.CANCELLED, by=by, reason=reason)
    receipt = Receipt.objects.filter(attempt=attempt).first()
    if receipt is not None:
        origin = "045" if payment.method == Payment.Method.TRANSFER else "P-12"
        ReceiptCancellation.objects.create(receipt=receipt, note=f"{origin}: {reason}")
        audit.record(RECEIPT_CANCELLED, actor=by, target=receipt, reason=reason)
