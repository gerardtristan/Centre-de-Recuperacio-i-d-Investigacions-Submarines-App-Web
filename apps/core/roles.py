"""Serveis de rols i governança (decisió 059; RN-RP-03, 05, 11, 13, 14, 18 i 20; RN-26).

Aquí hi ha les regles; les pantalles són de la T-RP-02 i l'editor, de la T-RP-03. Cada canvi
deixa la seva entrada al registre d'activitat (RN-RP-08) dins la mateixa transacció, amb els
rols que tenia qui actua abans de canviar res (RN-RP-15). Mentre no existeixi el correu
(T-M01-10), els avisos per correu estan pendents.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.accounts.models import Account, RecoveryCode, TotpDevice

from . import audit
from .models import AccountRole, Role
from .permission_catalog import ADMINISTRATOR_ONLY, CATALOG
from .permissions import has_perm

NO_OPERATIONAL_ADMIN = gettext_lazy(
    "No es pot fer: la plataforma es quedaria sense cap administrador operatiu "
    "(actiu, amb doble factor, no bloquejat i que no sigui d'emergència)."
)
SECOND_TREASURER = gettext_lazy(
    "Ja hi ha un altre compte actiu amb el rol tresorer. El club treballa amb un sol tresorer "
    "(P-48); es pot desar igualment."
)


def operational_admins(now=None):
    """RN-RP-13: actiu, amb TOTP donat d'alta, no bloquejat, que no és d'emergència i amb el
    rol administrador actiu."""
    now = now or timezone.now()
    return (
        Account.objects.filter(
            kind=Account.Kind.ADMIN,
            status=Account.Status.ACTIVE,
            is_emergency=False,
            totp_device__confirmed_at__isnull=False,
            role_assignments__role__code=Role.Code.ADMINISTRATOR,
            role_assignments__removed_at__isnull=True,
        )
        .filter(Q(locked_until__isnull=True) | Q(locked_until__lte=now))
        .distinct()
    )


def admin_shortage_warning() -> bool:
    """Avís permanent a l'administració quan hi ha menys de dos administradors operatius."""
    return operational_admins().count() < 2


def _lock_operational_admins() -> set[int]:
    """Bloqueja les files dels administradors operatius fins al final de la transacció, de
    manera que dos canvis simultanis no puguin deixar la plataforma sense cap."""
    ids = list(operational_admins().values_list("pk", flat=True))
    return set(Account.objects.select_for_update().filter(pk__in=ids).values_list("pk", flat=True))


def _would_leave_no_operational_admin(account) -> bool:
    operational = _lock_operational_admins()
    return account.pk in operational and not (operational - {account.pk})


def _ensure_can_manage_accounts(by) -> None:
    # Sense permís, «no trobat» (CA-RP-03). M3 és protegit i exclusiu de l'administrador.
    if not has_perm(by, "core.accounts.manage"):
        raise Http404


def _active_assignment(account, role_code):
    return (
        AccountRole.objects.select_for_update()
        .filter(admin_account=account, role__code=role_code, removed_at__isnull=True)
        .first()
    )


@transaction.atomic
def assign_role(account: Account, role_code: str, *, by: Account) -> list[str]:
    """Assigna un rol de gestió a un compte d'administrador. Torna els avisos del resum."""
    _ensure_can_manage_accounts(by)
    role = Role.objects.filter(code=role_code, is_management=True).first()
    if role is None:
        raise ValidationError(_("Aquest rol no s'assigna a comptes d'administrador."))
    if account.kind != Account.Kind.ADMIN:
        raise ValidationError(_("Els rols només s'assignen a comptes d'administrador."))
    if _active_assignment(account, role_code):
        return []

    warnings = []
    if role_code == Role.Code.TREASURER:
        others = (
            AccountRole.objects.filter(
                role__code=Role.Code.TREASURER,
                removed_at__isnull=True,
                admin_account__status=Account.Status.ACTIVE,
            )
            .exclude(admin_account=account)
            .exists()
        )
        if others:
            warnings.append(SECOND_TREASURER)  # RN-RP-14: avís, no bloqueig

    audit.record(audit.Action.ROLE_ASSIGNED, actor=by, target=account, field="role", new=role_code)
    AccountRole.objects.create(admin_account=account, role=role, assigned_by=by)
    return warnings


@transaction.atomic
def remove_role(account: Account, role_code: str, *, by: Account) -> None:
    """Retira un rol. Té efecte a la petició següent (RN-RP-10). Si el compte es queda sense
    cap rol, se'n tanquen les sessions però continua actiu (RN-RP-11)."""
    _ensure_can_manage_accounts(by)
    assignment = _active_assignment(account, role_code)
    if assignment is None:
        raise ValidationError(_("El compte no té aquest rol."))
    if role_code == Role.Code.ADMINISTRATOR and _would_leave_no_operational_admin(account):
        raise ValidationError(NO_OPERATIONAL_ADMIN)

    audit.record(audit.Action.ROLE_REMOVED, actor=by, target=account, field="role", old=role_code)
    assignment.removed_at = timezone.now()
    assignment.removed_by = by
    assignment.save(update_fields=["removed_at", "removed_by"])
    if not AccountRole.objects.filter(admin_account=account, removed_at__isnull=True).exists():
        account.end_all_sessions()
    # RN-RP-12 (responsables orfes) s'aplicarà quan hi hagi activitats i sessions (02).


@transaction.atomic
def deactivate_admin_account(account: Account, *, by: Account) -> None:
    """Desactiva un compte d'administrador, també el propi (RN-RP-20). Se'n tanquen totes
    les sessions; el compte personal de la mateixa persona no es toca."""
    _ensure_can_manage_accounts(by)
    if account.kind != Account.Kind.ADMIN:
        raise ValidationError(_("Aquesta acció és per a comptes d'administrador."))
    if _would_leave_no_operational_admin(account):
        raise ValidationError(NO_OPERATIONAL_ADMIN)
    audit.record(
        audit.Action.ADMIN_ACCOUNT_DISABLED,
        actor=by,
        target=account,
        field="status",
        old=account.status,
        new=Account.Status.DISABLED,
    )
    account.status = Account.Status.DISABLED
    account.save(update_fields=["status", "updated_at"])
    account.end_all_sessions()


@transaction.atomic
def reset_totp(account: Account, *, by: Account, note: str = "") -> None:
    """Restableix el TOTP d'un altre compte d'administrador (M4; CA-08.3). Si és l'últim
    administrador operatiu, només ho pot fer un compte d'emergència, amb nota (RN-RP-18)."""
    if not has_perm(by, "core.accounts.reset_credentials"):
        raise Http404
    if by.pk == account.pk:
        raise ValidationError(_("Ningú no pot restablir el seu propi compte per aquesta via."))
    if account.kind != Account.Kind.ADMIN:
        raise ValidationError(_("Aquesta acció és per a comptes d'administrador."))
    if _would_leave_no_operational_admin(account):
        if not by.is_emergency:
            raise ValidationError(NO_OPERATIONAL_ADMIN)
        if not note.strip():
            raise ValidationError(_("Cal una nota per restablir el TOTP de l'últim administrador."))
    # RN-RP-18: compte d'emergència, compte afectat i nota. Cap secret (CA-14.4).
    audit.record(
        audit.Action.TOTP_RESET,
        actor=by,
        target=account,
        reason=note,
        details={"emergency": by.is_emergency},
    )
    TotpDevice.objects.filter(account=account).delete()
    RecoveryCode.objects.filter(account=account).delete()
    account.end_all_sessions()


def grant_initial_administrator(account: Account, *, origin: str = "createsuperuser") -> None:
    """Rol administrador per al primer compte, des del servidor. `origin` és l'ordre que el crea
    (`createsuperuser` o `seed_demo_data`) i queda al registre d'activitat com a actor sistema."""
    # Abans de crear el rol: un origen buit no ha de deixar un rol sense registre.
    actor = audit.system(origin)
    role = Role.objects.get(code=Role.Code.ADMINISTRATOR)
    _, created = AccountRole.objects.get_or_create(
        admin_account=account, role=role, removed_at=None
    )
    if created:
        audit.record(
            audit.Action.ROLE_ASSIGNED,
            actor=actor,
            target=account,
            field="role",
            new=Role.Code.ADMINISTRATOR,
        )


def validate_role_permissions(role_code: str, cells: dict[str, str]) -> None:
    """Comprova el conjunt de permisos editables que tindria un rol (per a l'editor de la
    T-RP-03 i per a les migracions de dades que canviïn la matriu). No afegeix res sol."""
    role = Role.objects.filter(code=role_code, is_management=True).first()
    if role is None:
        raise ValidationError(_("Els permisos només s'editen als rols de gestió."))
    errors = []
    for code, scope in cells.items():
        perm = CATALOG.get(code)
        if perm is None:
            errors.append(_("Permís desconegut: %(code)s.") % {"code": code})
        elif perm.protected or code in ADMINISTRATOR_ONLY:
            # CA-RP-03 i CA-RP-09: les regles protegides no es poden canviar.
            errors.append(
                _("«%(permission)s» és una regla protegida (%(rule)s).")
                % {"permission": perm.description, "rule": perm.protected_by}
            )
        elif scope not in perm.allowed_scopes:
            errors.append(
                _("«%(permission)s» no admet l'abast «%(scope)s».")
                % {"permission": perm.description, "scope": scope}
            )
        else:
            missing = [req for req in perm.requires if req not in cells]
            for req in missing:  # RN-RP-03: cap deducció
                errors.append(
                    _("«%(permission)s» demana també «%(required)s».")
                    % {"permission": perm.description, "required": CATALOG[req].description}
                )
    if errors:
        raise ValidationError(errors)
