"""Càrrec, pagament i departament: estructura bàsica (spec 00, HU-15 i HU-16, RN-60 a RN-76;
decisió 027). La 04 i el 05b hi construeixen al damunt sense canviar aquestes regles.

- L'estat d'un càrrec només canvia aquí, amb les transicions de RN-67, i cada canvi queda al
  registre d'activitat dins la mateixa transacció.
- «Pagat» només arriba des del proveïdor (notificació verificada, 05b) o d'una conciliació
  confirmada pel tresorer (04). El registre manual està bloquejat per P-12 (RN-72) i cap vista
  del navegador no crida `mark_paid` (RN-71, CA-15.7).
- Transicions que hi afegeixen altres tasques: «retornat → pendent» (048, T-M05b-01), que
  només fa `reopen_returned`, i «pagat → pendent» (045, T-M04-12), que només fa
  `revert_paid_transfer`.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone
from django.utils.formats import number_format
from django.utils.translation import gettext as _

from . import audit
from .models import (
    AuditEntry,
    Charge,
    Department,
    Payment,
    PaymentCancellation,
    validate_cents,
)
from .permissions import has_perm

S = Charge.Status

# RN-67. La resta de transicions es rebutgen (CA-15.4).
TRANSITIONS = {
    (S.PENDING, S.PAID),
    (S.PENDING, S.CANCELLED),
    (S.PAID, S.RETURNED),
    (S.PAID, S.CANCELLED),  # devolució total
}

# 045: «pagat → pendent», fora de TRANSITIONS perquè només la fa `revert_paid_transfer`.
REVERT_TRANSFER = (S.PAID, S.PENDING)
# 048 (RN-M05b-14): «retornat → pendent», fora de TRANSITIONS perquè només la fa `reopen_returned`.
REOPEN_RETURNED = (S.RETURNED, S.PENDING)

PAID_ORIGINS = {"provider", "reconciliation"}

RECONCILE = "treasury.reconcile"  # T4 (M04-4): conciliar i desfer una conciliació
RETURNS = "payments.returns"  # B4 (M05b-4): registrar retornats i decidir el reintent
PAYMENT_CANCELLED = "charges.payment_cancelled"

# S-M04-06: el centre de cost de les quotes, dins «General» (dades inicials de la T-M04-02).
FEES_COST_CENTRE = "Quotes de socis"


def euros(cents: int) -> str:
    """Un import en cèntims, per mostrar-lo: «120,00 €» en la llengua activa."""
    return f"{number_format(Decimal(cents) / 100, decimal_pos=2)} €"


def _ensure_can_manage_departments(by) -> None:
    if not has_perm(by, "core.departments.manage"):  # M7
        raise Http404


@transaction.atomic
def create_department(name: str, *, by) -> Department:
    _ensure_can_manage_departments(by)
    department = Department(name=name.strip())
    department.full_clean()
    department.save()
    audit.record("departments.created", actor=by, target=department, new=department.name)
    return department


@transaction.atomic
def deactivate_department(department: Department, *, by) -> None:
    """RN-75: un departament no s'esborra, es desactiva (CA-16.2)."""
    _ensure_can_manage_departments(by)
    if department.name == Department.GENERAL:
        # Hi van les quotes (CA-15.8): sense ell no se'n podria crear cap.
        raise ValidationError(_("El departament «General» no es pot desactivar."))
    if not department.active:
        return
    audit.record(
        "departments.deactivated", actor=by, target=department, field="active", old=True, new=False
    )
    department.active = False
    department.save(update_fields=["active"])


@transaction.atomic
def create_charge(
    person,
    *,
    kind: str,
    amount_cents: int,
    concept: str,
    origin: str,
    by,
    department=None,
    cost_centre=None,
) -> Charge:
    """Crea un càrrec pendent. Les quotes van sempre a «General / Quotes de socis» (CA-15.8,
    Q-18, S-M04-06). La resta porta el centre de cost que es triï, del seu departament, o cap."""
    # Abans de `full_clean`, que convertiria 12.5 en 12 sense dir res.
    validate_cents(amount_cents)
    if kind == Charge.Kind.FEE:
        general = Department.objects.get(name=Department.GENERAL)
        if department is not None and department != general:
            raise ValidationError(_("Les quotes van al departament «General»."))
        department = general
        fees = general.cost_centres.get(name=FEES_COST_CENTRE)
        if cost_centre is not None and cost_centre != fees:
            raise ValidationError(_("Les quotes van al centre de cost «Quotes de socis»."))
        cost_centre = fees
    if department is None:
        raise ValidationError(_("Tot càrrec necessita un departament (RN-62)."))
    charge = Charge(
        person=person,
        kind=kind,
        amount_cents=amount_cents,
        concept=concept.strip(),
        origin=origin,
        department=department,
        cost_centre=cost_centre,
    )
    charge.full_clean()
    charge.save()
    audit.record(
        "charges.created",
        actor=by,
        target=charge,
        details={
            "kind": kind,
            "amount_cents": amount_cents,
            "department": department.name,
            "cost_centre": cost_centre.name if cost_centre else None,
            "origin": origin,
        },
    )
    return charge


def _transition(
    charge: Charge, new_status: str, *, by, reason: str = "", details=None, allowed=TRANSITIONS
) -> Charge:
    locked = Charge.objects.select_for_update().get(pk=charge.pk)
    if (locked.status, new_status) not in allowed:
        raise ValidationError(
            _("Un càrrec «%(current)s» no pot passar a «%(new)s».")
            % {"current": locked.get_status_display(), "new": Charge.Status(new_status).label}
        )
    audit.record(
        "charges.status_changed",
        actor=by,
        target=locked,
        field="status",
        old=locked.status,
        new=new_status,
        reason=reason,
        details=details,
    )
    locked.status = new_status
    if new_status == S.CANCELLED:
        locked.cancel_reason = reason.strip()
        locked.cancel_category = (details or {}).get("category", "")
    locked.save(update_fields=["status", "cancel_reason", "cancel_category", "updated_at"])
    charge.refresh_from_db()
    return charge


@transaction.atomic
def mark_paid(charge: Charge, payment, *, origin: str, by) -> Charge:
    """Pendent → pagat. `origin`: «provider» (notificació verificada) o «reconciliation»
    (conciliació confirmada). `by` és qui ho confirma: el sistema o el tresorer."""
    if origin == "manual":
        raise ValidationError(_("El registre manual de cobraments està bloquejat fins a P-12."))
    if origin not in PAID_ORIGINS:
        raise ValidationError(
            _("Un càrrec només passa a pagat des del proveïdor o la conciliació.")
        )
    if payment.charge_id != charge.pk:
        raise ValidationError(_("El pagament no és d'aquest càrrec."))
    return _transition(charge, S.PAID, by=by, details={"origin": origin, "payment": payment.pk})


@transaction.atomic
@transaction.atomic
def record_payment(
    charge: Charge,
    *,
    method: str,
    origin: str,
    by,
    provider_status: str = "",
    provider_reference: str = "",
    transfer_reference: str = "",
) -> Payment:
    """Pagament confirmat (P-84): crea el pagament amb l'import del càrrec (RN-M05b-02) i passa
    el càrrec a pagat, tot o res. Les altres apps creen el pagament només per aquí. `origin`:
    «provider» o «reconciliation», com a `mark_paid`."""
    locked = Charge.objects.select_for_update().get(pk=charge.pk)
    payment = Payment.objects.create(
        charge=locked,
        method=method,
        amount_cents=locked.amount_cents,
        provider_status=provider_status,
        provider_reference=provider_reference,
        transfer_reference=transfer_reference,
        paid_at=timezone.now(),
    )
    mark_paid(locked, payment, origin=origin, by=by)
    return payment


def cancel(charge: Charge, reason: str, *, by, category: str = "") -> Charge:
    """Pendent o pagat (devolució total) → anul·lat, amb motiu (CA-15.5). `category`: buida o
    «exemption» (RN-M01-72); queda al càrrec i al registre."""
    if not reason.strip():
        raise ValidationError(_("Per anul·lar un càrrec cal un motiu."))
    if category and category not in Charge.CancelCategory.values:
        raise ValidationError(_("Categoria d'anul·lació desconeguda."))
    details = {"category": category} if category else None
    return _transition(charge, S.CANCELLED, by=by, reason=reason, details=details)


def active_payments(charge: Charge) -> list[Payment]:
    """Els pagaments del càrrec que compten: els que no tenen anul·lació (045). Amb la
    precàrrega `payments__cancellation` no fa cap consulta."""
    return [payment for payment in charge.payments.all() if not hasattr(payment, "cancellation")]


@transaction.atomic
def revert_paid_transfer(charge: Charge, reason: str, *, by) -> PaymentCancellation:
    """045 (CA-T10.5, CA-T10.6): «pagat → pendent» d'un càrrec que una transferència conciliada
    va posar en «pagat» per error. El pagament queda anul·lat amb el mateix motiu, tot o res i al
    registre. Només amb T4 (el tresorer); sense, «no trobat». Targeta, Bizum i domiciliació es
    corregeixen amb una devolució. No toca el soci ni el carnet (P-110), ni la tresoreria: el
    contramoviment i la línia de l'extracte són de qui crida (la conciliació de la 04)."""
    if not has_perm(by, RECONCILE, write=True):
        raise Http404
    if not reason.strip():
        raise ValidationError(_("Per tornar un càrrec a pendent cal un motiu."))
    locked = Charge.objects.select_for_update().get(pk=charge.pk)
    if locked.status != S.PAID:
        raise ValidationError(_("Només es pot tornar a pendent un càrrec pagat."))
    payments = active_payments(locked)
    # Una transferència només arriba a «pagat» per la conciliació (RN-T18; `mark_paid`).
    if len(payments) != 1 or payments[0].method != Payment.Method.TRANSFER:
        raise ValidationError(
            _("Només una transferència conciliada torna a pendent; la resta, amb una devolució.")
        )
    cancellation = _cancel_payment(payments[0], reason, by=by, origin="045")
    _transition(
        charge,
        S.PENDING,
        by=by,
        reason=reason,
        details={"origin": "045", "payment": payments[0].pk},
        allowed={REVERT_TRANSFER},
    )
    return cancellation


def _cancel_payment(payment: Payment, reason: str, *, by, origin: str) -> PaymentCancellation:
    """El pagament no es toca: una fila nova diu que ja no compta, amb el motiu i qui."""
    cancellation = PaymentCancellation.objects.create(
        payment=payment, reason=reason.strip(), cancelled_by=by
    )
    audit.record(
        PAYMENT_CANCELLED,
        actor=by,
        target=payment,
        reason=reason,
        details={"charge": payment.charge_id, "origin": origin},
    )
    return cancellation


def _can_handle_returns(by) -> bool:
    return has_perm(by, RETURNS, write=True)


@transaction.atomic
def mark_returned(charge: Charge, reason: str, *, by) -> PaymentCancellation:
    """RN-67 (CA-M05b-18): «pagat → retornat» quan el banc retorna un rebut domiciliat. `reason`:
    el codi i el motiu del banc. El pagament queda anul·lat amb el mateix motiu (P-240, opció per
    defecte): ja no compta per a la validesa del soci (RN-M05b-18) i, si el càrrec es reobre i es
    torna a pagar, només compta el pagament nou. Tot o res i al registre. Només el tresorer (B4);
    sense, «no trobat». Ni la sortida i la comissió del retorn (04) ni l'avís al soci
    (`members.on_fee_returned`) són d'aquí: els fa el flux de retornats del 05b (T-M05b-12)."""
    if not _can_handle_returns(by):
        raise Http404
    if not reason.strip():
        raise ValidationError(_("Per marcar un càrrec com a retornat cal un motiu."))
    locked = Charge.objects.select_for_update().get(pk=charge.pk)
    if locked.status != S.PAID:
        raise ValidationError(_("Només es pot marcar com a retornat un càrrec pagat."))
    payments = active_payments(locked)
    # Els retornats són de rebuts domiciliats (M05b-6, DirectDebitItem); la resta, devolució.
    if len(payments) != 1 or payments[0].method != Payment.Method.DIRECT_DEBIT:
        raise ValidationError(
            _("Només es retorna un rebut domiciliat; la resta es corregeix amb una devolució.")
        )
    cancellation = _cancel_payment(payments[0], reason, by=by, origin="RN-M05b-14")
    _transition(charge, S.RETURNED, by=by, reason=reason, details={"payment": payments[0].pk})
    return cancellation


@transaction.atomic
def reopen_returned(charge: Charge, reason: str, *, by) -> Charge:
    """048 (RN-M05b-14; CA-M05b-18): «retornat → pendent» quan el tresorer confirma un reintent a
    una remesa posterior o envia l'alternativa de pagament. Motiu obligatori i al registre. El
    retorn i la seva comissió ja són a la tresoreria i no es toquen; el pagament nou entra per
    `record_payment`, amb el seu ingrés. Només el tresorer (B4) o el procés que aplica el reintent
    que ell ha confirmat (un actor «sistema»); la resta, «no trobat». Quants intents i què es fa
    segons el codi del retorn (RN-M05b-15) és del 05b."""
    system = isinstance(by, audit.Actor) and by.kind == AuditEntry.ActorKind.SYSTEM
    if not (system or _can_handle_returns(by)):
        raise Http404
    if not reason.strip():
        raise ValidationError(_("Per tornar a pendent un càrrec retornat cal un motiu."))
    return _transition(
        charge,
        S.PENDING,
        by=by,
        reason=reason,
        details={"origin": "048"},
        allowed={REOPEN_RETURNED},
    )
