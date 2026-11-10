"""Reautenticació d'un compte amb sessió (T-M00-05; RN-M01-57, RN-M05a-12; V-01).

Punts d'ús: esborrar el compte (T-M01-22, `minutes=0`), demanar el canvi del correu d'entrada
(T-M01-16, `minutes=0`; RN-M01-81) i, quan es construeixi, el 05a (T-M05a-09, `minutes=15`).
"""

import time

from django.core.exceptions import PermissionDenied

from .models import Account
from .security import AREA_ADMIN, AREA_PERSONAL, confirm_password_and_code
from .sessions import AUTH_AT_SESSION_KEY

# Hora de l'última reautenticació correcta. Va a part de `auth_at`, que fixa el màxim de 8 hores
# de la sessió d'administració des de l'entrada (V-01) i no s'ha d'allargar.
REAUTH_AT_SESSION_KEY = "reauth_at"


def last_auth_at(request) -> float:
    """Hora (epoch) de l'última autenticació de la sessió: l'entrada o l'última reautenticació."""
    session = request.session
    return max(session.get(AUTH_AT_SESSION_KEY, 0), session.get(REAUTH_AT_SESSION_KEY, 0))


def is_recent(request, minutes: int) -> bool:
    """Si la sessió s'ha autenticat fa `minutes` minuts o menys. Amb 0, mai."""
    return minutes > 0 and time.time() - last_auth_at(request) <= minutes * 60


def require_recent_auth(request, minutes: int, *, password: str = "", code: str = ""):
    """Torna None si el compte de la sessió (`request.user`) s'ha autenticat prou recentment, o
    el missatge d'error.

    - `minutes=0`: sempre, a la mateixa petició (RN-M01-57). `minutes=N`: n'hi ha prou amb una
      autenticació (entrada o reautenticació) de fa N minuts o menys; si no, es comproven les
      credencials.
    - Es demana la contrasenya i, **només si el compte té TOTP actiu**, el codi.
    - Errors: compten per al bloqueig de V-01 i queden al registre (`confirm_password_and_code`);
      el missatge és «Contrasenya incorrecta», «Codi incorrecte» o el de massa intents, i no diu
      quants en queden. Si el compte queda bloquejat, se'n tanquen totes les sessions
      (RN-M01-80, a `security.record_failure`).
    - Un compte que no és actiu no es comprova: PermissionDenied (el middleware ja no li dona
      sessió; és una segona barrera).
    """
    account = request.user
    if not account.is_active:
        raise PermissionDenied
    if is_recent(request, minutes):
        return None
    area = AREA_ADMIN if account.kind == Account.Kind.ADMIN else AREA_PERSONAL
    error = confirm_password_and_code(
        request, account, area, password or "", code or "", code_only_with_totp=True
    )
    if error is None:
        request.session[REAUTH_AT_SESSION_KEY] = time.time()
    return error
