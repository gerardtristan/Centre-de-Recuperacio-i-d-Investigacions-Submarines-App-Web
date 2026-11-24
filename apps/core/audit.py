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

Única modificació permesa (RN-89, decisió 028): en un esborrat RGPD, `substitute_identity`
substitueix el que identifica la persona per la seva referència.
"""

from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from django.db import connection
from django.db.models import Max, Q, QuerySet

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
    RESET_NOTICE = "auth.reset_notice"
    RECOVERY_CODE_USED = "auth.recovery_code_used"
    EMAIL_VERIFIED = "auth.email_verified"
    LOGIN_EMAIL_CHANGED = "auth.login_email_changed"  # RN-M01-79, amb el valor anterior
    EMAIL_LINK_SENT = "auth.email_link_sent"
    EMAIL_LINK_LIMITED = "auth.email_link_limited"
    PASSWORD_RESET = "auth.password_reset"  # noqa: S105 (nom d'una acció, no cap contrasenya)
    PASSWORD_RESET_BY_ADMIN = "auth.password_reset_by_admin"  # noqa: S105 (nom d'una acció)
    PASSWORD_CHANGED = "auth.password_changed"  # noqa: S105 (nom d'una acció)
    ROLE_ASSIGNED = "roles.assigned"
    ROLE_REMOVED = "roles.removed"
    PERMISSION_CHANGED = "roles.permission_changed"  # RN-RP-08: una entrada per cel·la (T-RP-03)
    ADMIN_ACCOUNT_DISABLED = "accounts.admin_disabled"
    FILE_URL_ISSUED = "files.url_issued"
    FILE_DELETED = "files.deleted"
    FILE_OPENED = "files.opened"  # un fitxer xifrat desxifrat per la vista (T-M09-25a)
    EMAIL_LIMIT_ALERT = "mail.daily_limit_alert"  # RN-A6: un sol avís al dia
    CLUBER_PREVIEW = "members.cluber_import.preview"
    CLUBER_IMPORT_CONFIRMED = "members.cluber_import.confirmed"
    BANK_STATEMENT_PREVIEW = "core.bank_statement.preview"  # T-M00-01 (RN-98)
    BANK_STATEMENT_CONFIRMED = "core.bank_statement.confirmed"
    BANK_STATEMENT_UNDONE = "core.bank_statement.undone"
    JOIN_REQUEST_CREATED = "members.join_request.created"
    JOIN_REQUEST_LIMITED = "members.join_request.limited"
    MEMBERS_EXPORTED = "members.list.exported"
    # T-M01-16. Fora de «members.*», però P20 els veu si la persona és sòcia (Q-079 de la 072).
    PROFILE_UPDATED = "persons.profile_updated"
    ERASURE_REQUESTED = "persons.erasure_requested"  # RN-M01-57 (T-M01-22, peça mínima)
    # T-M01-22 (HU-18, HU-19; RN-53: les sol·licituds RGPD queden al registre).
    ERASURE_APPROVED = "persons.erasure_approved"
    ERASURE_REJECTED = "persons.erasure_rejected"
    ERASURE_EXECUTED = "persons.erasure_executed"
    ERASURE_OWN_REJECTED = "persons.erasure_own_request_rejected"  # conflicte d'interès
    EXPORT_REQUESTED = "persons.export_requested"  # CA-18.1
    ACCOUNT_DISABLED_BY_ERASURE = "accounts.disabled_by_erasure"  # CA-19.1
    PERSONAL_AREA_NOT_FOUND = "members.personal_area.not_found"  # CA-M01-25


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


# --- Esborrat RGPD: única excepció a «només s'hi afegeixen files» (RN-51, RN-89; 028) --------

_SUBSTITUTION_SETTING = "cris.rgpd_anonymise"


@contextmanager
def identity_substitution():
    """Obre, només dins de la transacció en curs, l'excepció dels disparadors que protegeixen el
    registre d'activitat (core/0019) i l'historial dels socis (members/0018).

    L'excepció és acotada a la base de dades, no aquí: amb el paràmetre posat, els disparadors
    només accepten un UPDATE que deixi iguals l'acció, la data, l'objecte i l'actor i que hi
    escrigui la referència d'una persona ja anonimitzada (o buidi l'adreça IP). DELETE i
    TRUNCATE continuen rebutjats sempre. El paràmetre es torna a tancar en sortir; si la
    transacció es desfà, PostgreSQL el desfà amb ella."""
    if not connection.in_atomic_block:
        raise RuntimeError("La substitució de la identitat només es fa dins d'una transacció.")
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config(%s, 'on', true)", [_SUBSTITUTION_SETTING])
    yield
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config(%s, 'off', true)", [_SUBSTITUTION_SETTING])


def last_entry_id() -> int:
    return AuditEntry.objects.aggregate(last=Max("id"))["last"] or 0


def substitute_identity(person, targets: Mapping[str, Any], *, up_to: int) -> int:
    """Substitueix pel `anonymous_ref` de la persona el que la identifica a les entrades
    anteriors a l'esborrat (`id <= up_to`), sense tocar-ne l'acció, la data ni l'objecte
    (CA-19.4). Torna quantes entrades ha tocat.

    - On la persona és l'actor: l'adreça IP es buida. Qui actua ja és la referència
      (`actor_person` i el compte, que queden anonimitzats); els valors no es toquen, perquè
      poden ser dades d'altres persones.
    - Sobre els seus objectes no econòmics (`targets`: {tipus: identificadors}): el valor
      anterior, el valor nou i el motiu (text lliure) passen a ser la referència, i
      l'adreça IP es buida si l'actor era anònim (un intent d'entrada al seu compte).
    - Les entrades de càrrecs, pagaments i quotes no són a `targets`: queden bloquejades amb el
      registre econòmic (028, punt 2) i no porten cap dada personal pròpia.

    Les entrades que escriu el mateix esborrat (baixa, revocació, desactivació) són posteriors a
    `up_to`: només porten estats i motius fixos, i es conserven com a prova del que s'ha fet."""
    if person.status != Person.Status.ANONYMISED or not person.anonymous_ref:
        raise ValueError("La persona encara no està anonimitzada.")
    ref = person.anonymous_ref
    own = Q(pk__in=[])
    for label, ids in targets.items():
        own |= Q(target_type=label, target_id__in=[str(pk) for pk in ids])
    # Sense el gestor del model, que rebutja `update`: l'excepció la decideix el disparador.
    entries = QuerySet(AuditEntry).filter(id__lte=up_to)
    touched = set()

    def apply(queryset, **values):
        touched.update(queryset.values_list("pk", flat=True))
        queryset.update(**values)

    with identity_substitution():
        acted = Q(actor_person=person) | (own & Q(actor_kind=AuditEntry.ActorKind.ANONYMOUS))
        apply(entries.filter(acted, ip_address__isnull=False), ip_address=None)
        apply(entries.filter(own, old_value__isnull=False), old_value=ref)
        apply(entries.filter(own, new_value__isnull=False), new_value=ref)
        apply(entries.filter(own).exclude(reason=""), reason=ref)
    return len(touched)
