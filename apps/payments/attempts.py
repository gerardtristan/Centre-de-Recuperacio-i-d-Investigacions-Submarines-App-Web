"""Intents de pagament: crear-los i canviar-ne l'estat (T-M05b-03; RN-M05b-02, 03 i 04).

Tall de targeta (decisió 089, D3): només s'obren intents amb targeta. Els altres mètodes s'hi
afegeixen a la seva tasca; cap línia d'aquí toca el mandat."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.models import Charge

from .models import PaymentAttempt

ENABLED_METHODS = frozenset({PaymentAttempt.Method.CARD})


class MethodNotAllowed(Exception):
    """Mètode desconegut o que encara no es pot fer servir."""


class ChargeNotPayable(Exception):
    """El càrrec no és «pendent»: no s'hi obre cap intent."""


class AttemptInProgress(Exception):
    """RN-M05b-04: el càrrec ja té un intent en curs; el nou espera que acabi o caduqui."""


class AttemptAlreadyPaid(Exception):
    """RN-M05b-04: el càrrec ja té un intent pagat."""


# Els dos índexs únics parcials de RN-M05b-04, amb l'error que en surt.
_CONFLICTS = {
    "payment_attempt_one_in_progress": AttemptInProgress,
    "payment_attempt_one_paid": AttemptAlreadyPaid,
}


@transaction.atomic
def create_attempt(charge: Charge, method: str, *, started_by=None) -> PaymentAttempt:
    """Obre un intent «creat» per a un càrrec pendent, amb l'import del càrrec (RN-M05b-02): no
    hi ha manera de passar-ne un altre. `started_by`: el compte que paga, o res si és el sistema."""
    if method not in ENABLED_METHODS:
        raise MethodNotAllowed(method)
    charge = Charge.objects.get(pk=charge.pk)  # l'estat i l'import desats, no una còpia vella
    if charge.status != Charge.Status.PENDING:
        raise ChargeNotPayable(charge.status)
    attempt = PaymentAttempt.objects.create(
        charge=charge, method=method, amount_cents=charge.amount_cents, started_by=started_by
    )
    details = {"charge": charge.pk, "method": method, "amount_cents": attempt.amount_cents}
    actor = started_by or audit.system("payments")
    audit.record("payments.attempt_created", actor=actor, target=attempt, details=details)
    return attempt


@transaction.atomic
def transition(attempt: PaymentAttempt, new_status: str, *, by, reason: str = "") -> PaymentAttempt:
    """Canvia l'estat segons RN-M05b-03 i ho deixa al registre d'activitat, dins la mateixa
    transacció. `by`: un compte o un actor del registre (`audit.system`, `audit.guest`).
    «A revisar» demana el motiu."""
    locked = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
    change = {"field": "status", "old": locked.status, "new": new_status, "reason": reason}
    locked.check_transition(locked.status, new_status)
    fields = ["status", "updated_at"]
    if new_status == PaymentAttempt.Status.TO_REVIEW:
        if not reason.strip():
            raise ValidationError(_("Per deixar un intent «a revisar» cal un motiu."))
        locked.review_reason = reason.strip()
        fields.append("review_reason")
    locked.status = new_status
    try:
        with transaction.atomic():
            locked.save(update_fields=fields)
    except IntegrityError as error:
        name = getattr(getattr(error.__cause__, "diag", None), "constraint_name", None)
        if name not in _CONFLICTS:
            raise
        raise _CONFLICTS[name] from error
    audit.record("payments.attempt_status_changed", actor=by, target=locked, **change)
    return locked
