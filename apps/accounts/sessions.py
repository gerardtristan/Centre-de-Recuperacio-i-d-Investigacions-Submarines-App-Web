"""Sessions de les dues entrades (spec 00, RN-14, RN-21; V-01).

Entre la contrasenya i el segon factor no hi ha sessió: només un estat pendent, de durada
curta, que guarda quin compte s'ha identificat. La sessió (`login`) es crea quan el segon
factor és correcte, de manera que un compte d'administrador sense TOTP no pot fer res (RN-21).
"""

import logging
import time

from django.conf import settings
from django.contrib.auth import login, logout
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.http import url_has_allowed_host_and_scheme

from apps.core import audit

from .models import Account
from .security import AREA_ADMIN, KIND_BY_AREA, client_ip, reset_failures

logger = logging.getLogger("cris.security")

# V-01. Decisió 081, punt 22: la pantalla «La sessió ha caducat» per inactivitat fa servir
# aquests mateixos temps (no n'hi ha cap altre): 30 minuts a l'administració, que veu les dades
# de tots els socis i els diners, amb un màxim de 8 hores; 14 dies a l'àrea de socis, que només
# mostra les dades pròpies i el carnet, i on les operacions sensibles ja demanen tornar a
# identificar-se (`reauth.py`).
ADMIN_IDLE_SECONDS = 30 * 60
ADMIN_MAX_AGE_SECONDS = 8 * 60 * 60
PERSONAL_IDLE_SECONDS = 14 * 24 * 60 * 60

# Galeta auxiliar (decisió 081, punt 22): només diu que en aquest navegador hi havia hagut una
# sessió, perquè quan caduca per inactivitat (i el navegador ja n'ha esborrat la galeta) la
# pàgina següent expliqui què ha passat en lloc de portar directament a l'entrada. Valor fix
# «1»: cap dada personal, cap identificador i cap capacitat d'autenticació. Dura el temps
# d'inactivitat de l'entrada més `SESSION_HINT_GRACE_SECONDS`, s'esborra en sortir i en
# mostrar la pàgina, i es renova amb l'activitat.
SESSION_HINT_COOKIE = "cris_sessio_previa"
SESSION_HINT_GRACE_SECONDS = 30 * 24 * 60 * 60

# Què compta com a activitat (decisió 081, punt 22): qualsevol petició a una pàgina protegida que
# fa la persona (navegar, enviar un formulari, una acció d'HTMX que ella provoca). No hi compten
# les precàrregues del navegador (`Sec-Purpose` o `Purpose: prefetch`) ni les peticions marcades
# com a automàtiques amb `AUTOMATIC_HEADER` (un sondeig periòdic d'HTMX l'ha de portar; una
# prova ho comprova a les plantilles). Aquestes es responen igual, però no allarguen la sessió.
# El service worker no fa cap petició pel seu compte: només respon les navegacions.
AUTOMATIC_HEADER = {"X-CRIS-Automatica": "1"}
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
        # Empremta de la contrasenya i de les sessions del compte: si un altre administrador
        # en restableix la contrasenya o el TOTP mentre aquest pas està a mig fer, l'estat
        # pendent deixa de valer (HU-08), igual que les sessions obertes.
        "hash": account.get_session_auth_hash(),
        "second_factor": False,
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
    if not constant_time_compare(data.get("hash", ""), account.get_session_auth_hash()):
        return None
    return account


def mark_second_factor(request) -> None:
    """El segon factor ja és correcte, però encara falta un pas (canviar la contrasenya
    temporal, CA-08.1) abans d'obrir la sessió."""
    data = request.session[_PENDING]
    data["second_factor"] = True
    request.session.modified = True


def second_factor_done(request) -> bool:
    return bool((request.session.get(_PENDING) or {}).get("second_factor"))


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
    audit.record(
        audit.Action.LOGIN_SUCCEEDED, actor=account, details={"area": area}, request=request
    )
    # CA-10.2: l'entrada d'un compte d'emergència es registra i s'avisa els administradors.
    from . import emergency

    emergency.record_use(account, area=area, request=request)


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


def idle_seconds(area: str) -> int:
    return ADMIN_IDLE_SECONDS if area == AREA_ADMIN else PERSONAL_IDLE_SECONDS


def is_user_activity(request) -> bool:
    """Cert si la petició la fa la persona i, per tant, allarga la sessió."""
    purpose = (request.headers.get("Sec-Purpose", "") + request.headers.get("Purpose", "")).lower()
    if "prefetch" in purpose:
        return False
    return not any(request.headers.get(name) for name in AUTOMATIC_HEADER)


def refresh_expiry(request, area: str) -> None:
    """Caducitat per inactivitat: es renova a cada petició que compta com a activitat."""
    request.session.set_expiry(idle_seconds(area))


def set_session_hint(response, area: str) -> None:
    response.set_cookie(
        SESSION_HINT_COOKIE,
        "1",
        max_age=idle_seconds(area) + SESSION_HINT_GRACE_SECONDS,
        path="/",
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite="Lax",
    )


def delete_session_hint(response) -> None:
    response.delete_cookie(SESSION_HINT_COOKIE, path="/", samesite="Lax")


def had_session(request) -> bool:
    return request.COOKIES.get(SESSION_HINT_COOKIE) == "1"
