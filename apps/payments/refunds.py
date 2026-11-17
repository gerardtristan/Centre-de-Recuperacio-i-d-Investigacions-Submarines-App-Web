"""Devolucions que fa el club (T-M05b-13; P-M05b-G; RN-M05b-17; RN-T11; CA-M05b-21 i CA-M05b-22).

El tresorer (B5) torna tot o part d'un pagament amb motiu. Targeta, i Bizum si el proveïdor ho
admet: per l'adaptador, amb la clau de la devolució. La resta (transferència, domiciliació,
Bizum sense devolució al proveïdor): el tresorer la fa des del banc i aquí la registra (P-228).

Idempotent per la clau (P-118, P-119): la devolució es desa «pendent» en una transacció pròpia
abans de fer res més. Si després alguna cosa falla, un reintent amb la mateixa clau la troba, el
proveïdor torna la mateixa devolució (CA-M05b-22) i la 04 només l'apunta una vegada, perquè
l'apunt, la crida al proveïdor i el «feta» van a la mateixa transacció.

Devolució total → càrrec «anul·lat» i rebut anul·lat amb una nota; parcial → el càrrec
continua «pagat» (RN-M05b-17). El correu al pagador i l'anotació al rebut: P-229.
"""

from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.core import audit, charges
from apps.core.models import Charge, Payment, validate_cents
from apps.core.permissions import has_perm
from apps.treasury import services as treasury

from .models import PaymentAttempt, Receipt, ReceiptCancellation, RefundRequest
from .providers import get_provider

REFUND = "payments.refund"  # B5, «Fer devolucions» (M05b-4)
REFUNDED = "payments.refunded"
DISCARDED = "payments.refund_discarded"
Channel, Status = RefundRequest.Channel, RefundRequest.Status


class RefundRejected(ValidationError):
    """La devolució no es pot fer: import, motiu, estat del càrrec o una clau ja feta servir."""


def refund(payment: Payment, amount_cents: int, *, reason: str, key: UUID, by) -> RefundRequest:
    """Torna `amount_cents` del pagament i torna la devolució feta. Amb una clau que ja està
    feta, la torna sense fer res més; amb una de pendent (un error abans), la completa. Un error
    del proveïdor deixa la devolució pendent: es torna a provar amb la mateixa clau."""
    if not has_perm(by, REFUND, write=True):
        raise Http404
    try:
        validate_cents(amount_cents)
    except ValidationError as error:
        raise RefundRejected(error.messages) from None
    reason = (reason or "").strip()
    if not reason:
        raise RefundRejected(_("Una devolució necessita el motiu."))
    request = _request(payment, amount_cents, reason, key, by)
    if request.status == Status.DONE:
        return request
    return _complete(request, by)


@transaction.atomic
def _request(payment, amount_cents, reason, key, by) -> RefundRequest:
    """La devolució d'aquesta clau, o una de nova «pendent». El pany del pagament fa que dues
    devolucions alhora no passin juntes de l'import cobrat (RN-T11)."""
    payment = Payment.objects.select_for_update().select_related("charge").get(pk=payment.pk)
    request = RefundRequest.objects.filter(key=key).first()
    if request is not None:
        if (request.payment_id, request.amount_cents) != (payment.pk, amount_cents):
            raise RefundRejected(_("Aquesta clau ja és d'una altra devolució."))
        if request.status == Status.DISCARDED:
            raise RefundRejected(_("Aquesta devolució està descartada: fes-ne una de nova."))
        return request
    if payment.charge.status != Charge.Status.PAID:
        raise RefundRejected(_("Només es torna un pagament d'un càrrec «pagat»."))
    if _refunded(payment) + amount_cents > payment.amount_cents:
        raise RefundRejected(_("La suma de les devolucions passaria de l'import cobrat."))
    return RefundRequest.objects.create(
        key=key,
        payment=payment,
        amount_cents=amount_cents,
        reason=reason,
        channel=_channel(payment),
        requested_by=by,
    )


@transaction.atomic
def _complete(request: RefundRequest, by) -> RefundRequest:
    """L'apunt a la 04, el càrrec, el rebut, el proveïdor i «feta», tot o res. El proveïdor va
    l'últim: si la 04 rebutja l'apunt, no es torna res; si el proveïdor falla, l'apunt es desfà i
    la devolució queda pendent; si falla després, el reintent rep del proveïdor la mateixa
    devolució (la clau) i l'apunta."""
    request = (
        RefundRequest.objects.select_for_update()
        .select_related("payment__charge")
        .get(pk=request.pk)
    )
    if request.status == Status.DONE:
        return request
    payment = request.payment
    treasury.record_refund(
        payment, request.amount_cents, reason=request.reason, by=by, refund_id=request.key
    )
    total = _refunded(payment, done_only=True) + request.amount_cents == payment.amount_cents
    if total:
        charges.cancel(payment.charge, request.reason, by=by)
        _cancel_receipt(payment.charge, request.reason)
    if request.channel == Channel.PROVIDER:
        done = get_provider().refund(payment, request.amount_cents, request.key)
        request.provider_refund_id = done.external_id
    request.status, request.done_at = Status.DONE, timezone.now()
    request.save(update_fields=["status", "done_at", "provider_refund_id"])
    audit.record(
        REFUNDED,
        actor=by,
        target=payment.charge,
        reason=request.reason,
        details={
            "payment": payment.pk,
            "amount_cents": request.amount_cents,
            "channel": request.channel,
            "total": total,
        },
    )
    return request


@transaction.atomic
def discard(request: RefundRequest, *, reason: str, by) -> RefundRequest:
    """Descarta amb motiu una devolució que s'ha quedat pendent (P-250, decisió 095): deixa de
    comptar per al límit de l'import (RN-T11) i la seva clau ja no es pot completar. No apunta
    res a la 04 ni crida el proveïdor. Una del proveïdor, el tresorer l'ha de comprovar abans al
    proveïdor: si s'hagués fet, descartar-la la deixaria sense apuntar. Només B5."""
    if not has_perm(by, REFUND, write=True):
        raise Http404
    reason = (reason or "").strip()
    if not reason:
        raise RefundRejected(_("Per descartar una devolució cal un motiu."))
    request = RefundRequest.objects.select_for_update().get(pk=request.pk)
    if request.status != Status.PENDING:
        raise RefundRejected(_("Només es descarta una devolució pendent."))
    request.status, request.discarded_at = Status.DISCARDED, timezone.now()
    request.discarded_by, request.discard_reason = by, reason
    request.save(update_fields=["status", "discarded_at", "discarded_by", "discard_reason"])
    audit.record(
        DISCARDED,
        actor=by,
        target=request.payment.charge,
        reason=reason,
        details={"payment": request.payment_id, "amount_cents": request.amount_cents},
    )
    return request


def _refunded(payment: Payment, *, done_only=False) -> int:
    """Cèntims ja tornats o en curs de tornar d'aquest pagament."""
    rows = RefundRequest.objects.filter(payment=payment).exclude(status=Status.DISCARDED)
    if done_only:
        rows = rows.filter(status=Status.DONE)
    return rows.aggregate(total=Sum("amount_cents"))["total"] or 0


def _channel(payment: Payment) -> str:
    method = Payment.Method
    if payment.method == method.CARD:
        return Channel.PROVIDER
    if payment.method == method.BIZUM and get_provider().capabilities().refund_bizum:
        return Channel.PROVIDER
    return Channel.BANK


def _cancel_receipt(charge: Charge, reason: str) -> None:
    """RN-M05b-17: el rebut de l'intent pagat queda anul·lat amb una nota; no s'esborra."""
    paid = PaymentAttempt.objects.filter(charge=charge, status=PaymentAttempt.Status.PAID)
    receipt = Receipt.objects.filter(attempt__in=paid, cancellation__isnull=True).first()
    if receipt is not None:
        ReceiptCancellation.objects.create(receipt=receipt, note=_("Devolució: %s") % reason)
