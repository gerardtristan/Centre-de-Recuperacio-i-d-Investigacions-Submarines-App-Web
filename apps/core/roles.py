"""Serveis de rols i governança (decisió 059; RN-RP-03, 05, 11, 13, 14, 18 i 20; RN-26).

Aquí hi ha les regles; les pantalles són de la T-RP-02 i l'editor, de la T-RP-03. Cada canvi
deixa la seva entrada al registre d'activitat (RN-RP-08) dins la mateixa transacció, amb els
rols que tenia qui actua abans de canviar res (RN-RP-15). Assignar i retirar un rol avisa per
correu (RN-RP-09), i desactivar un compte, també (RN-RP-20). L'avís de RN-RP-18 continua pendent;
el de CA-08.4 al compte restablert, sí que s'envia.
"""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.accounts.models import Account, RecoveryCode, TotpDevice
from apps.accounts.security import TEMPORARY_PASSWORD_VALIDITY, new_temporary_password

from . import audit, mail
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
LAST_ROLE = gettext_lazy(
    "El compte es quedarà sense cap rol: se'n tancaran les sessions i continuarà actiu, sense "
    "accés a l'administració (RN-RP-11)."
)
ALREADY_DONE = gettext_lazy("No s'ha desat res: el canvi ja estava fet.")
ROLE_NOTICE_TEMPLATE = "avis-canvi-rol"
DEACTIVATION_NOTICE_TEMPLATE = "avis-desactivacio-admin"


class AlreadyDone(ValidationError):
    """El canvi ja estava fet (p. ex., un altre administrador s'hi ha avançat): no es desa res."""


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


def _lock_admin_accounts(account) -> None:
    """Bloqueja el compte afectat i tots els que tenen el rol administrador actiu, per ordre de
    pk: un sol ordre per a tots els serveis, perquè dos canvis alhora no es bloquegin entre ells
    (revisió de #216, punt 2)."""
    holders = AccountRole.objects.filter(
        role__code=Role.Code.ADMINISTRATOR, removed_at__isnull=True
    ).values("admin_account_id")
    list(
        Account.objects.select_for_update()
        .filter(Q(pk=account.pk) | Q(pk__in=holders))
        .order_by("pk")
        .values_list("pk", flat=True)
    )


def leaves_no_operational_admin(account, *, lock: bool = False) -> bool:
    """RN-RP-13: si treure-li l'accés deixaria la plataforma sense cap administrador operatiu.
    Amb `lock` (serveis), primer bloqueja els comptes i després torna a calcular qui és
    operatiu, de manera que un canvi que s'ha confirmat mentre s'esperava ja hi compti i dos
    canvis alhora no puguin deixar la plataforma sense cap. Sense, només és per al resum de la
    pantalla (CA-RP-06)."""
    if lock:
        _lock_admin_accounts(account)
    operational = set(operational_admins().values_list("pk", flat=True))
    return account.pk in operational and not (operational - {account.pk})


def administrators_to_notify(exclude=None):
    """Comptes actius amb el rol administrador i adreça de notificació, per ordre (avisos de
    CA-10.2 i RN-RP-20). `exclude`: el compte que no s'ha d'avisar."""
    found = (
        Account.objects.filter(
            kind=Account.Kind.ADMIN,
            status=Account.Status.ACTIVE,
            role_assignments__role__code=Role.Code.ADMINISTRATOR,
            role_assignments__removed_at__isnull=True,
        )
        .exclude(notification_email="")
        .distinct()
        .order_by("pk")
    )
    return found.exclude(pk=exclude.pk) if exclude is not None else found


def _other_active_treasurer(account) -> bool:
    return (
        AccountRole.objects.filter(
            role__code=Role.Code.TREASURER,
            removed_at__isnull=True,
            admin_account__status=Account.Status.ACTIVE,
        )
        .exclude(admin_account=account)
        .exists()
    )


def change_warnings(account, role_code: str, *, assign: bool) -> list:
    """Avisos del resum abans de desar (RN-RP-07): un sol tresorer (RN-RP-14) i el compte que es
    queda sense cap rol (RN-RP-11)."""
    if assign:
        return (
            [SECOND_TREASURER]
            if role_code == Role.Code.TREASURER and _other_active_treasurer(account)
            else []
        )
    others = AccountRole.objects.filter(admin_account=account, removed_at__isnull=True)
    return [] if others.exclude(role__code=role_code).exists() else [LAST_ROLE]


def _queue_notice(template: str, recipients, context: dict) -> None:
    """Posa a la cua l'avís a cada compte, en confirmar la transacció, fora dels bloquejos."""
    recipients = list(recipients)

    def queue():
        for recipient in recipients:
            mail.queue_email(
                template, to=recipient.notification_email, person=recipient.person, context=context
            )

    transaction.on_commit(queue)


def _notify_role_change(account, role, *, by, assigned: bool, note: str) -> None:
    """RN-RP-09: correu als comptes actius amb el rol administrador o President i al compte
    afectat, sigui quin sigui el seu estat. Noms d'usuari, rol, quan i la nota: cap dada personal
    de terceres persones."""
    context = {
        "username": account.login,
        "actor": by.login,
        "role": str(role),
        "assigned": assigned,
        "note": note,
        "when": timezone.now(),
    }
    holders = Q(
        status=Account.Status.ACTIVE,
        role_assignments__role__code__in=[Role.Code.ADMINISTRATOR, Role.Code.PRESIDENT],
        role_assignments__removed_at__isnull=True,
    )
    recipients = (
        Account.objects.filter(kind=Account.Kind.ADMIN)
        .filter(Q(pk=account.pk) | holders)
        .exclude(notification_email="")
        .select_related("person")
        .distinct()
    )
    _queue_notice(ROLE_NOTICE_TEMPLATE, recipients, context)


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
def assign_role(
    account: Account, role_code: str, *, by: Account, note: str = ""
) -> list[str] | None:
    """Assigna un rol de gestió a un compte d'administrador. Torna els avisos del resum, o None
    si ja el tenia (no es desa ni s'avisa res). La nota va al registre (RN-RP-08) i al correu
    (RN-RP-09); la pantalla l'exigeix."""
    _ensure_can_manage_accounts(by)
    role = Role.objects.filter(code=role_code, is_management=True).first()
    if role is None:
        raise ValidationError(_("Aquest rol no s'assigna a comptes d'administrador."))
    if account.kind != Account.Kind.ADMIN:
        raise ValidationError(_("Els rols només s'assignen a comptes d'administrador."))
    if account.status == Account.Status.DISABLED:
        raise ValidationError(_("Un compte desactivat no rep rols nous."))
    if _active_assignment(account, role_code):
        return None

    warnings = change_warnings(account, role_code, assign=True)  # RN-RP-14: avís, no bloqueig
    audit.record(
        audit.Action.ROLE_ASSIGNED,
        actor=by,
        target=account,
        field="role",
        new=role_code,
        reason=note,
    )
    AccountRole.objects.create(admin_account=account, role=role, assigned_by=by)
    _notify_role_change(account, role, by=by, assigned=True, note=note)
    return warnings


@transaction.atomic
def remove_role(account: Account, role_code: str, *, by: Account, note: str = "") -> None:
    """Retira un rol. Té efecte a la petició següent (RN-RP-10). Si el compte es queda sense
    cap rol, se'n tanquen les sessions però continua actiu (RN-RP-11). Si no el tenia,
    `AlreadyDone`."""
    _ensure_can_manage_accounts(by)
    assignment = _active_assignment(account, role_code)
    if assignment is None:
        raise AlreadyDone(ALREADY_DONE)
    if role_code == Role.Code.ADMINISTRATOR and leaves_no_operational_admin(account, lock=True):
        raise ValidationError(NO_OPERATIONAL_ADMIN)

    audit.record(
        audit.Action.ROLE_REMOVED,
        actor=by,
        target=account,
        field="role",
        old=role_code,
        reason=note,
    )
    assignment.removed_at = timezone.now()
    assignment.removed_by = by
    assignment.save(update_fields=["removed_at", "removed_by"])
    if not AccountRole.objects.filter(admin_account=account, removed_at__isnull=True).exists():
        account.end_all_sessions()
    _notify_role_change(account, assignment.role, by=by, assigned=False, note=note)
    # RN-RP-12 (responsables orfes) s'aplicarà quan hi hagi activitats i sessions (02).


@transaction.atomic
def deactivate_admin_account(account: Account, *, by: Account, note: str = "") -> None:
    """Desactiva un compte d'administrador, també el propi (RN-RP-20; CA-13.2). Se'n tanquen
    totes les sessions; el compte personal de la mateixa persona no es toca. Si ja estava
    desactivat, `AlreadyDone`. La nota va al registre i al correu; la pantalla l'exigeix."""
    _ensure_can_manage_accounts(by)
    if account.kind != Account.Kind.ADMIN:
        raise ValidationError(_("Aquesta acció és per a comptes d'administrador."))
    blocked = leaves_no_operational_admin(account, lock=True)  # també bloqueja el compte
    account.refresh_from_db()
    if account.status == Account.Status.DISABLED:
        raise AlreadyDone(ALREADY_DONE)
    if blocked:
        raise ValidationError(NO_OPERATIONAL_ADMIN)
    audit.record(
        audit.Action.ADMIN_ACCOUNT_DISABLED,
        actor=by,
        target=account,
        field="status",
        old=account.status,
        new=Account.Status.DISABLED,
        reason=note,
    )
    account.status = Account.Status.DISABLED
    account.save(update_fields=["status", "updated_at"])
    account.end_all_sessions()
    # RN-RP-20: els altres administradors i, si el desactiva un altre, el compte afectat
    # (RN-RP-09). El President, no (P-370, opció per defecte acceptada).
    recipients = list(administrators_to_notify(exclude=account).select_related("person"))
    if account.pk != by.pk and account.notification_email:
        recipients.append(account)
    context = {"username": account.login, "actor": by.login, "note": note, "when": timezone.now()}
    _queue_notice(DEACTIVATION_NOTICE_TEMPLATE, recipients, context)


@dataclass(frozen=True)
class ResetNotice:
    """Resultat de l'avís de CA-08.4, separat del restabliment (RN-M01-61). «A la cua» no vol
    dir lliurat: el resultat de l'enviament és al registre d'enviaments (`email_id`)."""

    queued: bool
    reason: str = ""
    email_id: int | None = None


NO_ADDRESS = gettext_lazy("sense adreça")
ANONYMISED = gettext_lazy("persona anonimitzada")


@transaction.atomic
def reset_totp(account: Account, *, by: Account, note: str = "") -> ResetNotice:
    """Restableix el TOTP d'un altre compte d'administrador (M4; CA-08.3), amb motiu
    obligatori (RN-M01-60). Si és l'últim administrador operatiu, només ho pot fer un compte
    d'emergència (RN-RP-18). El compte restablert rep l'avís de CA-08.4 si té on rebre'l.

    El codi TOTP nou de qui actua (RN-M01-60) el comprova la vista, a la mateixa petició."""
    _ensure_can_reset(account, by, note)
    if leaves_no_operational_admin(account, lock=True) and not by.is_emergency:
        raise ValidationError(NO_OPERATIONAL_ADMIN)
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
    return _notify_reset(account, by=by, second_factor=True)


def _ensure_can_reset(account: Account, by: Account, note: str) -> None:
    if not has_perm(by, "core.accounts.reset_credentials"):
        raise Http404
    if by.pk == account.pk:
        raise ValidationError(_("Ningú no pot restablir el seu propi compte per aquesta via."))
    if account.kind != Account.Kind.ADMIN:
        raise ValidationError(_("Aquesta acció és per a comptes d'administrador."))
    if not (note or "").strip():
        raise ValidationError(_("Cal un motiu per restablir l'accés d'un compte."))


@transaction.atomic
def reset_password(account: Account, *, by: Account, note: str = "") -> tuple[str, ResetNotice]:
    """Restableix la contrasenya d'un altre compte d'administrador (M4; HU-08, CA-08.1 i
    CA-08.2). Torna la credencial temporal, que caduca a les 24 hores (V-01) i que s'ha de
    canviar en entrar. Es mostra una sola vegada a qui ho fa: no es desa en clar, ni va al
    registre ni a cap correu (RN-17). Com es fa arribar a la persona: Q-03, obert.

    Motiu obligatori (RN-M01-60). La credencial anterior, si n'hi havia, deixa de valer. Es
    tanquen totes les sessions del compte i qualsevol entrada a mig fer. El TOTP, els codis de
    recuperació i el bloqueig per intents no es toquen."""
    _ensure_can_reset(account, by, note)
    account = Account.objects.select_for_update().get(pk=account.pk)
    credential = new_temporary_password()
    expires = timezone.now() + TEMPORARY_PASSWORD_VALIDITY
    # Què ha passat, per què i fins quan val la credencial; mai la credencial (CA-14.4, RN-52).
    audit.record(
        audit.Action.PASSWORD_RESET_BY_ADMIN, actor=by, target=account, reason=note, new=expires
    )
    account.set_password(credential)
    account.password_temporary_until = expires
    account.save(update_fields=["password", "password_temporary_until", "updated_at"])
    account.end_all_sessions()
    return credential, _notify_reset(account, by=by, second_factor=False)


def _notify_reset(account: Account, *, by: Account, second_factor: bool) -> ResetNotice:
    """CA-08.4: avís informatiu al correu de notificació, sense cap enllaç ni credencial. El
    resultat queda en una entrada pròpia del registre (RN-M01-61): «a la cua» o «no enviat»,
    amb el motiu. Sense adreça, no s'avisa ningú més (065)."""
    email = None
    if account.notification_email:
        email = mail.queue_email(
            "restabliment-acces",
            to=account.notification_email,
            person=account.person,
            context={"second_factor": second_factor, "when": timezone.localtime()},
        )
    if email is not None:
        notice = ResetNotice(queued=True, email_id=email.pk)
    else:
        reason = ANONYMISED if account.notification_email else NO_ADDRESS
        notice = ResetNotice(queued=False, reason=str(reason))
    audit.record(
        audit.Action.RESET_NOTICE,
        actor=by,
        target=account,
        reason=notice.reason,
        details={
            "result": "queued" if notice.queued else "not_sent",
            "email_id": notice.email_id,
            "second_factor": second_factor,
        },
    )
    return notice


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
