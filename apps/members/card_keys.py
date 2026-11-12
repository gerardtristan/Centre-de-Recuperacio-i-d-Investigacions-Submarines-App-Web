"""Claus del QR del carnet (T-M01-19; decisió 079, A-01; RN-M01-85; especificació a
docs/planning.md#M01-079-qr).

El testimoni del carnet es calcula amb una clau del servidor i no es desa:

    testimoni = kid + "." + base64url(HMAC-SHA256(clau[kid], "cris-carnet:<soci>:<versió>"))

- `CARD_QR_KEYS`: llista «identificador:clau» (variables d'entorn; cap clau al repositori).
  `CARD_QR_ACTIVE_KEY`: la que es fa servir per emetre. Les altres es conserven perquè els
  carnets vigents es puguin continuar mostrant; verificar no fa servir cap clau.
- En local i a les proves, sense cap clau configurada, se'n deriva una («dev») de `SECRET_KEY`.
  Producció les exigeix (`CARD_QR_KEYS_REQUIRED`, prod.py) i la comprovació d'arrencada falla si
  falten o tenen un format incorrecte (`checks.py`).
- Cap dada personal entra al càlcul: només l'identificador intern del soci i la versió.
"""

import base64
import hashlib
import hmac
import re

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.crypto import salted_hmac

KID = re.compile(r"^[a-z0-9]{1,8}$")
MIN_KEY_CHARS = 32
DEV_KID = "dev"


def configured() -> dict[str, str]:
    """Les claus de la configuració, validades. Buit si no n'hi ha cap."""
    keys = {}
    for item in settings.CARD_QR_KEYS:
        kid, _, key = str(item).partition(":")
        if not KID.match(kid) or len(key) < MIN_KEY_CHARS:
            raise ImproperlyConfigured(
                "CARD_QR_KEYS: cada clau és «identificador:clau», amb un identificador d'1 a 8 "
                f"lletres minúscules o xifres i una clau de {MIN_KEY_CHARS} caràcters o més."
            )
        if kid in keys:
            raise ImproperlyConfigured(f"CARD_QR_KEYS: l'identificador «{kid}» està repetit.")
        keys[kid] = key
    return keys


def keys() -> dict[str, str]:
    found = configured()
    if found:
        return found
    if getattr(settings, "CARD_QR_KEYS_REQUIRED", False):
        raise ImproperlyConfigured("Falta CARD_QR_KEYS: aquest entorn exigeix claus pròpies.")
    # Només en local i a les proves: no protegeix res fora d'aquests entorns.
    return {DEV_KID: salted_hmac("apps.members.card_keys.dev", "qr").hexdigest()}


def active_key_id() -> str:
    available = keys()
    kid = settings.CARD_QR_ACTIVE_KEY or (DEV_KID if DEV_KID in available else "")
    if kid not in available:
        raise ImproperlyConfigured("CARD_QR_ACTIVE_KEY ha de ser una de les claus de CARD_QR_KEYS.")
    return kid


def token(member_id: int, version: int, kid: str) -> str | None:
    """El testimoni del carnet, o `None` si la clau ja no és a la configuració."""
    key = keys().get(kid)
    if key is None:
        return None
    message = f"cris-carnet:{member_id}:{version}".encode()
    digest = hmac.new(key.encode(), message, hashlib.sha256).digest()
    return f"{kid}.{base64.urlsafe_b64encode(digest).decode().rstrip('=')}"
