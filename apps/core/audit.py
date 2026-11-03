"""Servei del registre d'activitat (spec 00, HU-14, RN-50 a RN-53; RN-RP-08 i RN-RP-15).

Qualsevol mòdul registra una acció amb `record` (una entrada) o `record_changes` (una
entrada per camp que canvia). L'actor pot ser:
- un compte (`Account`): es guarden el compte concret, la seva persona i, si és d'administrador,
  els rols actius en aquell moment (CA-14.2, RN-RP-15);
- `system("nom-de-la-tasca")` per a tasques i notificacions de proveïdors (CA-14.5);
- `guest(persona, id_enllaç)` per a accions amb un enllaç de convidat; mai el testimoni (CA-14.6);
- `ANONYMOUS` quan no hi ha ningú identificat (p. ex. un identificador d'entrada desconegut).

Les entrades es creen dins de la transacció de l'acció: si l'acció es desfà, l'entrada també.
Cap secret als valors (RN-52): els noms de camp i de detall que en semblen es rebutgen.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .models import AccountRole, AuditEntry, Person


class Action:
    """Accions registrades. Cada mòdul hi afegeix les seves quan les necessita."""

    LOGIN_SUCCEEDED = "auth.login_succeeded"
    LOGIN_FAILED = "auth.login_failed"
    ACCOUNT_LOCKED = "auth.account_locked"
    IP_BLOCKED = "auth.ip_blocked"
    LOGOUT = "auth.logout"
    TOTP_ENROLLED = "auth.totp_enrolled"
    TOTP_RESET = "auth.totp_reset"
    TOTP_DISABLED = "auth.totp_disabled"
    RECOVERY_CODE_USED = "auth.recovery_code_used"
    EMAIL_VERIFIED = "auth.email_verified"
    PASSWORD_RESET = "auth.password_reset"  # noqa: S105 (nom d'una acció, no cap contrasenya)
    PASSWORD_RESET_BY_ADMIN = "auth.password_reset_by_admin"  # noqa: S105 (nom d'una acció)
    PASSWORD_CHANGED = "auth.password_changed"  # noqa: S105 (nom d'una acció)
    ROLE_ASSIGNED = "roles.assigned"
    ROLE_REMOVED = "roles.removed"
    ADMIN_ACCOUNT_DISABLED = "accounts.admin_disabled"
    FILE_URL_ISSUED = "files.url_issued"
    FILE_DELETED = "files.deleted"


@dataclass(frozen=True)
class Actor:
    kind: str
    person: Person | None = None
    origin: str = ""


ANONYMOUS = Actor(AuditEntry.ActorKind.ANONYMOUS)


def system(origin: str) -> Actor:
    if not origin.strip():
        raise ValueError("Un actor «sistema» necessita l'origen (CA-14.5).")
    return Actor(AuditEntry.ActorKind.SYSTEM, origin=origin.strip())


def guest(person: Person, link_id: int) -> Actor:
    """Rep l'identificador intern de l'enllaç (un enter), mai el testimoni (CA-14.6)."""
    if not isinstance(link_id, int):
        raise TypeError("Cal l'identificador intern de l'enllaç, no el testimoni.")
    return Actor(AuditEntry.ActorKind.GUEST, person=person, origin=f"guest_link:{link_id}")


# RN-52: cap secret al registre. Un camp o detall amb un d'aquests noms és un error de
# programació. L'IBAN tampoc no surt mai fora del mandat xifrat (044).
_SECRET_NAME_PARTS = ("password", "secret", "token", "recovery_code", "code_hash", "iban")


def _check_no_secrets(names) -> None:
    for name in names:
        lowered = str(name).lower()
        if any(part in lowered for part in _SECRET_NAME_PARTS):
            raise ValueError(f"El registre d'activitat no guarda secrets: «{name}» (RN-52).")


def _active_roles(account) -> list[str]:
    # Rols assignats i no retirats en aquest moment, també si el compte està desactivat:
    # és el que el compte tenia quan ha actuat (RN-RP-15).
    return sorted(
        AccountRole.objects.filter(
            admin_account=account, removed_at__isnull=True, role__is_management=True
        ).values_list("role__code", flat=True)
    )


def _actor_fields(actor) -> dict[str, Any]:
    from apps.accounts.models import Account

    if actor is None:
        actor = ANONYMOUS
    if isinstance(actor, Account):
        return {
            "actor_kind": AuditEntry.ActorKind.ACCOUNT,
            "actor_account": actor,
            "actor_person_id": actor.person_id,
            "actor_roles": _active_roles(actor) if actor.kind == Account.Kind.ADMIN else [],
        }
    if isinstance(actor, Actor):
        return {
            "actor_kind": actor.kind,
            "actor_person": actor.person,
            "actor_origin": actor.origin,
        }
    raise TypeError(f"Actor no admès al registre d'activitat: {actor!r}")


def _target_fields(target) -> dict[str, str]:
    if target is None:
        return {}
    return {"target_type": target._meta.label_lower, "target_id": str(target.pk)}


def _ip(request) -> str | None:
    if request is None:
        return None
    from apps.accounts.security import client_ip

    return client_ip(request)


def record(
    action: str,
    *,
    actor=None,
    target=None,
    field: str = "",
    old: Any = None,
    new: Any = None,
    reason: str = "",
    details: Mapping[str, Any] | None = None,
    request=None,
) -> AuditEntry:
    """Registra una acció. `actor` és un `Account`, un `Actor` o `None` (sense identificar)."""
    details = dict(details or {})
    _check_no_secrets([field, *details])
    return AuditEntry.objects.create(
        action=action,
        field=field,
        old_value=old,
        new_value=new,
        reason=reason.strip(),
        details=details,
        ip_address=_ip(request),
        **_actor_fields(actor),
        **_target_fields(target),
    )


def record_changes(
    action: str,
    *,
    actor,
    target,
    changes: Mapping[str, tuple[Any, Any]],
    reason: str = "",
    request=None,
) -> list[AuditEntry]:
    """Una entrada per cada camp que canvia: `changes` és {camp: (valor anterior, valor nou)}.
    Els camps que no canvien no deixen entrada (CA-14.1)."""
    changed = {name: values for name, values in changes.items() if values[0] != values[1]}
    _check_no_secrets(changed)
    if not changed:
        return []
    common = {
        "action": action,
        "reason": reason.strip(),
        "ip_address": _ip(request),
        **_actor_fields(actor),
        **_target_fields(target),
    }
    return AuditEntry.objects.bulk_create(
        AuditEntry(field=name, old_value=old, new_value=new, **common)
        for name, (old, new) in changed.items()
    )
