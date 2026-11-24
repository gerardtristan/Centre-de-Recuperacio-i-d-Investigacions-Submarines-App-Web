"""Estructura de la tresoreria: centres de cost i comptes (T-M04-22; P-410 i P-411, decisió 105;
VC-08). Crear, reanomenar i desactivar, amb registre (qui, quan, valor anterior). Res no
s'esborra (RN-T04, RN-T23).

- Centres de cost: T3 (`treasury.cost_centres.manage`). «General / Quotes de socis» i
  «General / Ajustos de caixa» són entrades del sistema que el codi busca pel nom: no es
  reanomenen ni es desactiven (P-411). Un departament desactivat no admet centres nous.
- Comptes: T2 (`treasury.accounts.manage`). Des d'aquí només es creen comptes de banc o de
  caixa; els de trànsit els crea el mòdul de pagaments (`services.create_transit_account`).
  D'un compte de banc només es guarden els quatre darrers dígits (RN-T03).

Els departaments són de la 00 (`apps.core.charges`: crear, reanomenar i desactivar, M7).
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404
from django.utils.translation import gettext as _

from apps.core import audit
from apps.core.charges import FEES_COST_CENTRE
from apps.core.models import Department
from apps.core.permissions import has_perm

from .models import CostCentre, TreasuryAccount
from .services import CASH_ADJUSTMENTS

COST_CENTRES = "treasury.cost_centres.manage"  # T3
ACCOUNTS = "treasury.accounts.manage"  # T2
SYSTEM_COST_CENTRES = {(Department.GENERAL, FEES_COST_CENTRE), CASH_ADJUSTMENTS}  # P-411
MANUAL_KINDS = (TreasuryAccount.Kind.BANK, TreasuryAccount.Kind.CASH)


def _require(by, code) -> None:
    if not has_perm(by, code, write=True):
        raise Http404


def is_system(cost_centre: CostCentre) -> bool:
    return (cost_centre.department.name, cost_centre.name) in SYSTEM_COST_CENTRES


def _save(obj, fields=None):
    obj.full_clean()
    obj.save(update_fields=fields)
    return obj


@transaction.atomic
def create_cost_centre(department: Department, name: str, *, by) -> CostCentre:
    _require(by, COST_CENTRES)
    if not department.active:
        raise ValidationError(_("Aquest departament està desactivat: no admet centres nous."))
    centre = _save(CostCentre(department=department, name=name.strip()))
    audit.record("treasury.cost_centre_created", actor=by, target=centre, new=str(centre))
    return centre


@transaction.atomic
def rename_cost_centre(centre: CostCentre, name: str, *, by) -> CostCentre:
    _require(by, COST_CENTRES)
    if is_system(centre):
        raise ValidationError(_("Aquest centre de cost és del sistema: no es reanomena."))
    old, centre.name = centre.name, name.strip()
    if centre.name != old:
        _save(centre, ["name"])
        audit.record("treasury.cost_centre_renamed", actor=by, target=centre, field="name",
                     old=old, new=centre.name)  # fmt: skip
    return centre


@transaction.atomic
def deactivate_cost_centre(centre: CostCentre, *, by) -> CostCentre:
    """CA-T14.2: un de desactivat no es pot triar per a càrrecs ni moviments nous."""
    _require(by, COST_CENTRES)
    if is_system(centre):
        raise ValidationError(_("Aquest centre de cost és del sistema: no es desactiva."))
    if centre.active:
        centre.active = False
        centre.save(update_fields=["active"])
        audit.record("treasury.cost_centre_deactivated", actor=by, target=centre,
                     field="active", old=True, new=False)  # fmt: skip
    return centre


@transaction.atomic
def create_account(name: str, kind: str, *, last4=None, by) -> TreasuryAccount:
    _require(by, ACCOUNTS)
    if kind not in MANUAL_KINDS:
        raise ValidationError(_("Des d'aquí només es creen comptes de banc o de caixa."))
    last4 = (last4 or "").strip() or None
    if kind == TreasuryAccount.Kind.BANK and last4 is None:
        raise ValidationError(_("Un compte de banc necessita els quatre darrers dígits."))
    account = _save(TreasuryAccount(name=name.strip(), kind=kind, last4=last4))
    audit.record("treasury.account_created", actor=by, target=account,
                 details={"kind": kind, "name": account.name})  # fmt: skip
    return account


@transaction.atomic
def rename_account(account: TreasuryAccount, name: str, *, by) -> TreasuryAccount:
    _require(by, ACCOUNTS)
    old, account.name = account.name, name.strip()
    if account.name != old:
        _save(account, ["name"])
        audit.record("treasury.account_renamed", actor=by, target=account, field="name",
                     old=old, new=account.name)  # fmt: skip
    return account


@transaction.atomic
def deactivate_account(account: TreasuryAccount, *, by) -> TreasuryAccount:
    """RN-T04: no s'esborra; els moviments i el saldo es continuen veient."""
    _require(by, ACCOUNTS)
    if account.active:
        account.active = False
        account.save(update_fields=["active"])
        audit.record("treasury.account_deactivated", actor=by, target=account,
                     field="active", old=True, new=False)  # fmt: skip
    return account
