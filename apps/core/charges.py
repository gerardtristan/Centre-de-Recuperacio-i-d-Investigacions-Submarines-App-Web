"""Càrrec, pagament i departament: estructura bàsica (spec 00, HU-15 i HU-16, RN-60 a RN-76;
decisió 027). La 04 i el 05b hi construeixen al damunt sense canviar aquestes regles.

- L'estat d'un càrrec només canvia aquí, amb les transicions de RN-67, i cada canvi queda al
  registre d'activitat dins la mateixa transacció.
- «Pagat» només arriba des del proveïdor (notificació verificada, 05b) o d'una conciliació
  confirmada pel tresorer (04). El registre manual està bloquejat per P-12 (RN-72) i cap vista
  del navegador no crida `mark_paid` (RN-71, CA-15.7).
- Transicions que hi afegeixen altres tasques: «retornat → pendent» (048, T-M05b-01) i
  «pagat → pendent» (045, T-M04-12).
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.formats import number_format
from django.utils.translation import gettext as _

from . import audit
from .models import Charge, Department, validate_cents
from .permissions import has_perm

S = Charge.Status

# RN-67. La resta de transicions es rebutgen (CA-15.4).
TRANSITIONS = {
    (S.PENDING, S.PAID),
    (S.PENDING, S.CANCELLED),
    (S.PAID, S.RETURNED),
    (S.PAID, S.CANCELLED),  # devolució total
}

PAID_ORIGINS = {"provider", "reconciliation"}


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
    person, *, kind: str, amount_cents: int, concept: str, origin: str, by, department=None
) -> Charge:
    """Crea un càrrec pendent. Les quotes van sempre a «General» (CA-15.8; Q-18)."""
    # Abans de `full_clean`, que convertiria 12.5 en 12 sense dir res.
    validate_cents(amount_cents)
    if kind == Charge.Kind.FEE:
        general = Department.objects.get(name=Department.GENERAL)
        if department is not None and department != general:
            raise ValidationError(_("Les quotes van al departament «General»."))
        department = general
    if department is None:
        raise ValidationError(_("Tot càrrec necessita un departament (RN-62)."))
    charge = Charge(
        person=person,
        kind=kind,
        amount_cents=amount_cents,
        concept=concept.strip(),
        origin=origin,
        department=department,
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
            "origin": origin,
        },
    )
    return charge


def _transition(charge: Charge, new_status: str, *, by, reason: str = "", details=None) -> Charge:
    locked = Charge.objects.select_for_update().get(pk=charge.pk)
    if (locked.status, new_status) not in TRANSITIONS:
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
def cancel(charge: Charge, reason: str, *, by, category: str = "") -> Charge:
    """Pendent o pagat (devolució total) → anul·lat, amb motiu (CA-15.5). `category`: buida o
    «exemption» (RN-M01-72); queda al càrrec i al registre."""
    if not reason.strip():
        raise ValidationError(_("Per anul·lar un càrrec cal un motiu."))
    if category and category not in Charge.CancelCategory.values:
        raise ValidationError(_("Categoria d'anul·lació desconeguda."))
    details = {"category": category} if category else None
    return _transition(charge, S.CANCELLED, by=by, reason=reason, details=details)
