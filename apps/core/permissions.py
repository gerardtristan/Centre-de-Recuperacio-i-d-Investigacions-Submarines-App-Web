"""Motor de permisos (decisió 059; RN-RP-01 a RN-RP-05).

Ordre de la comprovació: rol, després objecte, després camps.
- Només els comptes d'administrador actius tenen permisos de rol. El compte personal no
  n'hereta cap (059, punt 4.2): les seves accions són «pròpies» i les comprova cada mòdul.
- Els permisos es calculen a cada crida a partir dels rols actius i de la matriu vigent; mai
  no es guarden a la sessió. Dins d'una mateixa petició es poden reaprofitar amb
  `request_permissions`.
- `is_superuser` no hi té cap efecte: mana la matriu.
- Sense permís, la resposta és «no trobat» (Http404), sense revelar si l'objecte existeix.
"""

from collections.abc import Callable
from functools import wraps

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404

from .models import AccountRole, Role, RolePermission
from .permission_catalog import (
    ADMINISTRATOR_ONLY,
    CATALOG,
    KNOWN_SCOPES,
    READ_ONLY_SCOPES,
    SCOPE_ALL,
)

_REQUEST_CACHE_ATTR = "_cris_permissions"

# Comprovacions d'abast per objecte, que registra cada mòdul (p. ex. el 02 per a
# «les seves sessions»). Un abast sense comprovació registrada no deixa passar cap objecte.
_SCOPE_CHECKS: dict[str, Callable[[object, object], bool]] = {}


def register_scope_check(scope: str, check: Callable[[object, object], bool]) -> None:
    if scope not in KNOWN_SCOPES or scope == SCOPE_ALL:
        raise ImproperlyConfigured(f"Abast desconegut o que no necessita comprovació: {scope}")
    _SCOPE_CHECKS[scope] = check


def _permission(code):
    try:
        return CATALOG[code]
    except KeyError:
        # Un codi mal escrit no ha de negar en silenci: és un error de programació.
        raise ImproperlyConfigured(f"Permís desconegut: {code}") from None


def active_role_codes(account) -> set[str]:
    if not _is_admin_with_access(account):
        return set()
    return set(
        AccountRole.objects.filter(
            admin_account=account, removed_at__isnull=True, role__is_management=True
        ).values_list("role__code", flat=True)
    )


def effective_permissions(account) -> dict[str, str]:
    """Permís → abast efectiu: unió dels rols actius, amb l'abast més ampli (RN-RP-02)."""
    roles = active_role_codes(account)
    if not roles:
        return {}
    granted: dict[str, list[str]] = {}
    rows = RolePermission.objects.filter(role__code__in=roles).values_list(
        "role__code", "permission_code", "scope"
    )
    for role, code, scope in rows:
        perm = CATALOG.get(code)
        # Defensa en profunditat: una fila d'un permís protegit, desconegut, amb un abast
        # no admès o que dona a un altre rol la gestió d'usuaris no té cap efecte.
        if perm is None or perm.protected or scope not in perm.allowed_scopes:
            continue
        if code in ADMINISTRATOR_ONLY and role != Role.Code.ADMINISTRATOR:
            continue
        granted.setdefault(code, []).append(scope)
    for perm in CATALOG.values():
        if perm.protected:
            for role, scope in perm.initial.items():
                if role in roles:
                    granted.setdefault(perm.code, []).append(scope)
    return {
        code: min(scopes, key=CATALOG[code].allowed_scopes.index)
        for code, scopes in granted.items()
    }


def request_permissions(request) -> dict[str, str]:
    """Els permisos del compte de la petició, calculats una sola vegada per petició."""
    cached = getattr(request, _REQUEST_CACHE_ATTR, None)
    if cached is None:
        cached = effective_permissions(getattr(request, "user", None))
        setattr(request, _REQUEST_CACHE_ATTR, cached)
    return cached


def scope_for(account, code, *, permissions=None) -> str | None:
    _permission(code)
    perms = effective_permissions(account) if permissions is None else permissions
    return perms.get(code)


def has_perm(account, code, obj=None, *, write=False, permissions=None) -> bool:
    """Té el compte el permís `code`? Amb `obj`, també ha de caure dins l'abast. Amb
    `write`, un abast de només consulta («Cons.») no hi val."""
    scope = scope_for(account, code, permissions=permissions)
    if scope is None:
        return False
    if write and scope in READ_ONLY_SCOPES:
        return False
    if obj is None or scope in {SCOPE_ALL, *READ_ONLY_SCOPES}:
        return True
    check = _SCOPE_CHECKS.get(scope)
    return bool(check and check(account, obj))


def require_perm(request, code, obj=None, *, write=False) -> str:
    """Com `has_perm`, però amb Http404 si no hi ha permís. Torna l'abast efectiu."""
    perms = request_permissions(request)
    if not has_perm(request.user, code, obj, write=write, permissions=perms):
        raise Http404
    return perms[code]


def permission_required(code, *, write=False):
    """Decorador de vistes d'administració: sense permís, «no trobat»."""
    _permission(code)

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            require_perm(request, code, write=write)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


def _is_admin_with_access(account) -> bool:
    from apps.accounts.models import Account

    return (
        account is not None
        and getattr(account, "is_authenticated", False)
        and isinstance(account, Account)
        and account.kind == Account.Kind.ADMIN
        and account.is_active
    )


def accounts_with_perm(code, *, write=False) -> list:
    """Comptes d'administrador actius que tenen ara el permís `code` (amb `write`, un abast que
    no sigui només de consulta), per ordre. Per als avisos que van «a qui pot fer X» (079,
    RN-M01-89): la llista surt de la matriu vigent, mai d'un rol escrit al codi."""
    from apps.accounts.models import Account

    _permission(code)
    accounts = (
        Account.objects.filter(
            kind=Account.Kind.ADMIN,
            status=Account.Status.ACTIVE,
            role_assignments__removed_at__isnull=True,
        )
        .select_related("person")
        .distinct()
        .order_by("pk")
    )
    return [account for account in accounts if has_perm(account, code, write=write)]
