"""Intents de pagament: crear-los i canviar-ne l'estat (T-M05b-03; RN-M05b-02, 03 i 04).

S'obren intents amb targeta i amb Bizum, els dos mètodes que passen pel proveïdor (T-M05b-04), i
amb transferència (T-M05b-06). La domiciliació s'hi afegeix a la seva tasca; cap línia d'aquí toca
el mandat."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _

from apps.core import audit, business_settings
from apps.core.models import Charge

from .models import PaymentAttempt

# Els que tria el soci a la pantalla de pagament; la targeta guardada l'obre el sistema
# (`checkout.charge_saved_card`, T-M05b-15), i el manual, el rebut d'un pagament registrat a mà
# (`transfers.on_payment_saved`, P-12).
SCREEN_METHODS = frozenset(
    {PaymentAttempt.Method.CARD, PaymentAttempt.Method.BIZUM, PaymentAttempt.Method.TRANSFER}
)
ENABLED_METHODS = SCREEN_METHODS | {PaymentAttempt.Method.SAVED_CARD, PaymentAttempt.Method.MANUAL}


class MethodNotAllowed(Exception):
    """Mètode desconegut o que encara no es pot fer servir."""


class ChargeNotPayable(Exception):
    """El càrrec no és «pendent»: no s'hi obre cap intent."""


class AttemptInProgress(Exception):
    """RN-M05b-04: el càrrec ja té un intent en curs; el nou espera que acabi o caduqui."""


class AttemptAlreadyPaid(Exception):
    """RN-M05b-04: el càrrec ja té un intent pagat."""


# VC-17: minuts que la pantalla espera un Bizum. Només de la pantalla: la caducitat de l'ordre
# la fixa el proveïdor (P-45 punt 13).
BIZUM_UI_TIMEOUT = "payments.bizum_ui_timeout_minutes"

# Els dos índexs únics parcials de RN-M05b-04, amb l'error que en surt.
_CONFLICTS = {
    "payment_attempt_one_in_progress": AttemptInProgress,
    "payment_attempt_one_paid": AttemptAlreadyPaid,
}


@transaction.atomic
def create_attempt(
    charge: Charge, method: str, *, started_by=None, guest_link=None
) -> PaymentAttempt:
    """Obre un intent «creat» per a un càrrec pendent, amb l'import del càrrec (RN-M05b-02): no
    hi ha manera de passar-ne un altre. `started_by`: el compte que paga, o res si és el sistema
    o un convidat; `guest_link`: l'enllaç amb què paga el convidat (T-M05b-08)."""
    if method not in ENABLED_METHODS:
        raise MethodNotAllowed(method)
    charge = Charge.objects.get(pk=charge.pk)  # l'estat i l'import desats, no una còpia vella
    if charge.status != Charge.Status.PENDING:
        raise ChargeNotPayable(charge.status)
    # RN-M05b-24: un Bizum en curs conserva el termini amb què ha començat.
    timeout = (
        business_settings.get(BIZUM_UI_TIMEOUT) if method == PaymentAttempt.Method.BIZUM else None
    )
    attempt = PaymentAttempt.objects.create(
        charge=charge,
        method=method,
        amount_cents=charge.amount_cents,
        started_by=started_by,
        guest_link=guest_link,
        ui_timeout_minutes=timeout,
    )
    details = {"charge": charge.pk, "method": method, "amount_cents": attempt.amount_cents}
    if guest_link is not None:
        actor = audit.guest(guest_link.person, guest_link.pk)
    else:
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
