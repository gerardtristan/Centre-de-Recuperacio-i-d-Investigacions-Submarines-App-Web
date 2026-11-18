"""Rebut d'un pagament confirmat i correu al pagador (T-M05b-07; RN-M05b-19; CA-M05b-03).

- El rebut s'emet a la mateixa transacció que dona l'intent per pagat (`processing.pay`): si
  es desfà, no queda ni el rebut ni el número ni el correu. Una notificació repetida no arriba
  aquí (l'intent ja és pagat, CA-M05b-04), i l'únic de `Receipt.attempt` ho garanteix igualment.
- Número `R-AAAA-NNNNNN` (S-M05b-11): correlatiu dins de cada any, sense forats.
- És un rebut, no una factura (P-47). El PDF el fa el navegador des de la pàgina del rebut,
  com el carnet (079, A-20): no es desa cap fitxer (P-85, opció per defecte).
"""

from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.core import charges, mail
from apps.members import recipients

from .models import PaymentAttempt, Receipt, ReceiptCounter

PAID_TEMPLATE = "pagament-confirmat"


class NotPaid(Exception):
    """L'intent no és «pagat»: no té rebut."""


def issue(attempt: PaymentAttempt) -> Receipt:
    """Emet el rebut de l'intent pagat i en posa el correu a la cua, a la transacció de qui el
    crida."""
    if attempt.status != PaymentAttempt.Status.PAID:
        raise NotPaid
    issued_at = timezone.now()
    year = timezone.localtime(issued_at).year
    with transaction.atomic():
        ReceiptCounter.objects.get_or_create(year=year)
        counter = ReceiptCounter.objects.select_for_update().get(year=year)
        counter.last_number += 1
        counter.save(update_fields=["last_number"])
        number = f"R-{year}-{counter.last_number:06d}"
        receipt = Receipt.objects.create(attempt=attempt, number=number, issued_at=issued_at)
        _mail_payer(receipt)
    return receipt


def _mail_payer(receipt: Receipt) -> None:
    """CA-M05b-03: el correu al pagador (al representant, si és menor: RN-M01-78). Només el
    concepte, l'import i el número; el rebut s'obre a la plataforma, amb sessió (el convidat, amb
    l'enllaç obert en aquest navegador)."""
    charge = receipt.attempt.charge
    to = recipients.email_for(charge.person)
    if not to:
        return
    # El convidat no té compte: el seu rebut s'obre amb l'enllaç de la 00 (T-M05b-08; P-280).
    if receipt.attempt.guest_link_id:
        link = reverse("payments:guest_receipt")
    else:
        link = reverse("payments:receipt", args=[receipt.attempt_id])
    context = {
        "concept": charge.concept,
        "amount": charges.euros(charge.amount_cents),
        "number": receipt.number,
        "link": settings.PUBLIC_SITE_URL + link,
    }
    mail.queue_email(PAID_TEMPLATE, to=to, person=charge.person, context=context)
