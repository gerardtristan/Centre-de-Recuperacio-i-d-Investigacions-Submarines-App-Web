"""Sessions de les dues entrades (spec 00, RN-14, RN-21; V-01).

Entre la contrasenya i el segon factor no hi ha sessió: només un estat pendent, de durada
curta, que guarda quin compte s'ha identificat. La sessió (`login`) es crea quan el segon
factor és correcte, de manera que un compte d'administrador sense TOTP no pot fer res (RN-21).
"""

import logging
import time

from django.contrib.auth import login, logout
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Account
from .security import AREA_ADMIN, KIND_BY_AREA, client_ip, reset_failures

logger = logging.getLogger("cris.security")

# V-01
ADMIN_IDLE_SECONDS = 30 * 60
ADMIN_MAX_AGE_SECONDS = 8 * 60 * 60
PERSONAL_IDLE_SECONDS = 14 * 24 * 60 * 60
# Supòsit (la spec no en diu res): temps per escriure el codi o escanejar el QR.
PENDING_SECONDS = 10 * 60

_PENDING = "pending_auth"
AREA_SESSION_KEY = "auth_area"
AUTH_AT_SESSION_KEY = "auth_at"
_BACKEND = "django.contrib.auth.backends.ModelBackend"


def safe_next(request, url: str | None) -> str | None:
    if url and url_has_allowed_host_and_scheme(
        url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return url
    return None


def start_pending(request, account: Account, area: str, next_url: str | None) -> None:
    # Una sessió anterior (d'un altre compte o de l'altra entrada) no es reaprofita.
    if request.user.is_authenticated:
        logout(request)
    request.session.cycle_key()
    request.session[_PENDING] = {
        "account": account.pk,
        "area": area,
        "at": time.time(),
        "next": safe_next(request, next_url),
    }


def pending_account(request, area: str) -> Account | None:
    data = request.session.get(_PENDING)
    if not data or data.get("area") != area or time.time() - data["at"] > PENDING_SECONDS:
        return None
    account = (
        Account.objects.select_related("totp_device")
        .filter(pk=data["account"], kind=KIND_BY_AREA[area], status=Account.Status.ACTIVE)
        .first()
    )
    if account is None or account.is_locked(timezone.now()):
        return None
    return account


def pending_next(request) -> str | None:
    return (request.session.get(_PENDING) or {}).get("next")


def clear_pending(request) -> None:
    request.session.pop(_PENDING, None)


def complete_login(request, account: Account, area: str) -> None:
    clear_pending(request)
    login(request, account, backend=_BACKEND)  # canvia la clau de sessió
    request.session[AREA_SESSION_KEY] = area
    request.session[AUTH_AT_SESSION_KEY] = time.time()
    refresh_expiry(request, area)
    reset_failures(account)
    logger.info("login_ok account=%s area=%s ip=%s", account.pk, area, client_ip(request))


def session_area_is_valid(request, area: str) -> bool:
    """Una sessió només val per a l'entrada on s'ha obert i per al tipus de compte d'aquesta
    entrada; la d'administració, com a màxim 8 hores des de l'entrada (V-01)."""
    user = request.user
    if not user.is_authenticated or not user.is_active:
        return False
    if request.session.get(AREA_SESSION_KEY) != area or user.kind != KIND_BY_AREA[area]:
        return False
    if area == AREA_ADMIN:
        auth_at = request.session.get(AUTH_AT_SESSION_KEY, 0)
        if time.time() - auth_at > ADMIN_MAX_AGE_SECONDS:
            logger.info("admin_session_max_age account=%s", user.pk)
            logout(request)
            return False
    return True


def refresh_expiry(request, area: str) -> None:
    """Caducitat per inactivitat: es renova a cada petició."""
    seconds = ADMIN_IDLE_SECONDS if area == AREA_ADMIN else PERSONAL_IDLE_SECONDS
    request.session.set_expiry(seconds)
