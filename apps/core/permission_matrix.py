"""Editor de permisos dels rols (T-RP-03; 059 i 060; RN-RP-03 a 11; CA-RP-04, 05, 07, 09 i 10).

La matriu són les cel·les editables (rol de gestió × permís no protegit) de `RolePermission`.
Desar un canvi, aquí, dins d'una transacció:
- comprova el permís M3b (protegit, només l'administrador; la resta, «no trobat»);
- rebutja cap canvi si la matriu ha canviat des que s'ha obert (versió de base) i bloqueja
  l'última versió perquè dos desaments alhora no es trepitgin;
- valida cada rol que canvia (`roles.validate_role_permissions`: regles protegides, abasts
  admesos i `requires`, sense afegir res sol);
- desa les cel·les, una entrada per cel·la al registre (RN-RP-08), una `PermissionMatrixVersion`
  nova, el correu de RN-RP-09 i, si s'amplia l'accés a diners o a dades personals, el tancament
  de les sessions dels comptes afectats (RN-RP-11, CA-RP-10).
El TOTP de qui desa (RN-RP-06) el comprova la vista, a la mateixa petició.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.accounts.models import Account

from . import audit, roles
from .models import AccountRole, PermissionMatrixVersion, Role, RolePermission
from .permission_catalog import CATALOG, PERMISSIONS, editable_initial_cells
from .permissions import has_perm

EDIT = "core.permissions.edit"
NOTICE_TEMPLATE = "avis-canvi-permisos"
STALE = gettext_lazy(
    "Un altre administrador ha canviat la matriu mentre la tenies oberta. No s'ha desat res: "
    "torna-la a obrir i refés el canvi."
)
NOTHING = gettext_lazy("No hi ha cap canvi per desar.")


def editable_permissions():
    """Files de l'editor: els permisos no protegits, en l'ordre del catàleg."""
    return [perm for perm in PERMISSIONS if not perm.protected]


def management_roles():
    return list(Role.objects.filter(is_management=True).order_by("pk"))


def current_cells() -> dict[tuple[str, str], str]:
    return {
        (role, code): scope
        for role, code, scope in RolePermission.objects.values_list(
            "role__code", "permission_code", "scope"
        )
    }


def initial_cells() -> dict[tuple[str, str], str]:
    """«Tornar a la configuració inicial» (RN-RP-08): la columna inicial del catàleg."""
    return {(role, code): scope for role, code, scope in editable_initial_cells()}


def latest_version() -> int:
    return PermissionMatrixVersion.objects.aggregate(n=Max("number"))["n"] or 0


def diff(before: dict, after: dict) -> list[dict]:
    return [
        {"role": role, "permission": code, "before": before.get(key), "after": after.get(key)}
        for key in sorted(set(before) | set(after))
        if before.get(key) != after.get(key)
        for role, code in (key,)
    ]


def affected_accounts(changes: list[dict]):
    """Comptes d'administrador actius amb algun dels rols que canvien (RN-RP-07)."""
    changed_roles = {cell["role"] for cell in changes}
    return (
        Account.objects.filter(
            kind=Account.Kind.ADMIN,
            status=Account.Status.ACTIVE,
            role_assignments__role__code__in=changed_roles,
            role_assignments__removed_at__isnull=True,
        )
        .distinct()
        .order_by("login")
    )


def sensitive(cell: dict) -> bool:
    """Toca diners, dades personals o un camp sensible (avís de RN-RP-07)."""
    perm = CATALOG[cell["permission"]]
    return perm.touches_money or perm.touches_personal_data or perm.kind == "field"


def widens(cell: dict) -> bool:
    """El canvi dona més accés a diners o a dades personals (RN-RP-11, CA-RP-10): un permís
    nou o un abast més ampli (primer a `allowed_scopes`)."""
    after, before = cell["after"], cell["before"]
    if after is None or not sensitive(cell):
        return False
    order = CATALOG[cell["permission"]].allowed_scopes
    return before is None or order.index(after) < order.index(before)


def _validate(proposed: dict, changes: list[dict]) -> None:
    errors = []
    for role in sorted({cell["role"] for cell in changes}):
        cells = {code: scope for (r, code), scope in proposed.items() if r == role}
        try:
            roles.validate_role_permissions(role, cells)
        except ValidationError as exc:
            label = str(Role.Code(role).label)
            errors += [f"{label}: {message}" for message in exc.messages]
    if errors:
        raise ValidationError(errors)


def check(proposed: dict, *, base_version: int, current: dict | None = None) -> list[dict]:
    """Les cel·les que canvien, o ValidationError si no es pot desar: la matriu ha canviat des
    que s'ha obert, no hi ha cap canvi o un rol no passa la validació. La vista ho mira abans
    de demanar el TOTP; `save` ho torna a mirar amb la versió bloquejada."""
    if latest_version() != base_version:
        raise ValidationError(STALE)
    changes = diff(current_cells() if current is None else current, proposed)
    if not changes:
        raise ValidationError(NOTHING)
    _validate(proposed, changes)  # CA-RP-07 i CA-RP-09
    return changes


@transaction.atomic
def save(proposed: dict, *, by: Account, note: str, base_version: int) -> PermissionMatrixVersion:
    """Desa la matriu `proposed` ({(rol, permís): abast}) i torna la versió nova."""
    if not has_perm(by, EDIT):
        raise Http404  # CA-RP-03: sense M3b, «no trobat»
    note = (note or "").strip()
    if not note:
        raise ValidationError(_("Escriu la nota del canvi."))  # CA-RP-04
    list(PermissionMatrixVersion.objects.select_for_update().values_list("pk", flat=True))
    changes = check(proposed, base_version=base_version)

    affected = list(affected_accounts(changes))
    roles_by_code = {role.code: role for role in management_roles()}
    for cell in changes:
        role = roles_by_code[cell["role"]]
        if cell["after"] is None:
            RolePermission.objects.filter(role=role, permission_code=cell["permission"]).delete()
        else:
            RolePermission.objects.update_or_create(
                role=role, permission_code=cell["permission"], defaults={"scope": cell["after"]}
            )
        audit.record(
            audit.Action.PERMISSION_CHANGED,
            actor=by,
            field="permission",
            old=cell["before"],
            new=cell["after"],
            reason=note,
            details={"role": cell["role"], "permission": cell["permission"]},
        )
    version = PermissionMatrixVersion.objects.create(
        number=base_version + 1,
        changed_by=by,
        note=note,
        diff=changes,
        affected_accounts=[account.pk for account in affected],
    )
    # RN-RP-11: tornen a entrar amb TOTP. Qui desa l'acaba d'escriure: no se li tanca la sessió.
    widened_roles = {cell["role"] for cell in changes if widens(cell)}
    if widened_roles:
        holders = AccountRole.objects.filter(
            role__code__in=widened_roles, removed_at__isnull=True
        ).values("admin_account_id")
        for account in Account.objects.filter(pk__in=holders).exclude(pk=by.pk):
            account.end_all_sessions()
    _notify(version, by=by, affected=affected)
    return version


def describe(cell: dict) -> dict:
    """Una cel·la amb noms en català, per al resum i el correu (cap dada personal)."""
    perm = CATALOG[cell["permission"]]
    return {
        "role": str(Role.Code(cell["role"]).label),
        "ref": perm.ref,
        "permission": str(perm.description),
        "before": scope_label(cell["before"]),
        "after": scope_label(cell["after"]),
        "sensitive": sensitive(cell),
    }


SCOPE_LABELS = {
    None: gettext_lazy("—"),
    "all": gettext_lazy("Sí"),
    "read": gettext_lazy("Cons."),
    "read_minimal": gettext_lazy("Cons. (dades mínimes)"),
    "own_activities": gettext_lazy("Les seves activitats"),
    "own_sessions": gettext_lazy("Les seves sessions"),
}


def scope_label(scope) -> str:
    return str(SCOPE_LABELS[scope])


def _notify(version, *, by, affected) -> None:
    """RN-RP-09: administradors, comptes afectats i President. Què ha canviat i qui ho ha fet,
    amb noms d'usuari, rols i permisos: cap dada personal de terceres persones."""
    recipients = {account.pk: account for account in roles.administrators_to_notify()}
    presidents = Account.objects.filter(
        kind=Account.Kind.ADMIN,
        status=Account.Status.ACTIVE,
        role_assignments__role__code=Role.Code.PRESIDENT,
        role_assignments__removed_at__isnull=True,
    )
    for account in [*presidents, *affected]:
        if account.notification_email:
            recipients.setdefault(account.pk, account)
    context = {
        "actor": by.login,
        "number": version.number,
        "note": version.note,
        "when": timezone.now(),
        "cells": [describe(cell) for cell in version.diff],
    }
    roles.queue_notice(NOTICE_TEMPLATE, recipients.values(), context)
