"""Límits dels enllaços del correu: recuperació i reenviament de la verificació (decisió 065,
RN-M01-58). Són valors de seguretat al codi, com els de V-01 (`security.py`): les regles de
seguretat no s'editen des de l'app (059). Per ajustar-los cal una decisió nova que canviï
RN-M01-58 i, després, el valor d'aquest fitxer; les proves el llegeixen d'aquí.

- Per destinatari (adreça normalitzada) i finalitat: com a màxim 3 correus per hora i 6 cada
  24 hores, vinguin d'on vinguin les peticions.
- Per origen, conjunt per a les dues finalitats: quan arriba a 10 peticions acceptades en
  15 minuts, queda limitat 15 minuts comptats des de la desena.
- Una petició limitada per origen no es desa: no compta i no allarga res. Una de limitada
  per destinatari no envia res ni compta per al destinatari, però sí per a l'origen
  (decisió 066): així el límit d'origen avança igual tant si l'adreça té compte com si no.
- No té res a veure amb el comptador d'intents fallits de l'entrada (V-01).
"""

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.utils.crypto import salted_hmac

from apps.core.normalization import normalize_email

from .models import EmailLinkRequest
from .security import IP_MAX_FAILURES, IP_WINDOW


@dataclass(frozen=True)
class Window:
    max_count: int
    period: timedelta


RECIPIENT_WINDOWS = (Window(3, timedelta(hours=1)), Window(6, timedelta(hours=24)))
ORIGIN_WINDOW = Window(10, timedelta(minutes=15))
ORIGIN_COOLDOWN = timedelta(minutes=15)
# RN-M01-59: estat intermedi d'un compte pendent per demanar reenviaments (066: no és d'un sol ús).
RESEND_STATE = timedelta(minutes=10)
# El més llarg dels terminis: les peticions més velles ja no serveixen per a res i s'esborren.
RETENTION = max(window.period for window in (*RECIPIENT_WINDOWS, ORIGIN_WINDOW))


def recipient_key(email: str) -> str:
    """Empremta de l'adreça normalitzada: el registre de límits no guarda cap correu."""
    return salted_hmac(
        "apps.accounts.limits.recipient", normalize_email(email), algorithm="sha256"
    ).hexdigest()


def _advisory_lock(key: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [key])


def lock_origin(ip: str) -> None:
    """Dins d'una transacció: les peticions del mateix origen es comproven d'una en una, de
    manera que moltes alhora no passen més enllà del límit. Claus diferents de les de
    l'entrada: aquests límits no la frenen."""
    _advisory_lock(f"cris-email-links-ip:{ip}")


def lock_recipient(key: str) -> None:
    _advisory_lock(f"cris-email-links-to:{key}")


EMAIL_LINK_PURPOSES = (
    EmailLinkRequest.Purpose.RESET_PASSWORD,
    EmailLinkRequest.Purpose.VERIFY_EMAIL,
)


def origin_limited(
    ip: str,
    now=None,
    *,
    purposes=EMAIL_LINK_PURPOSES,
    window: Window = ORIGIN_WINDOW,
    cooldown: timedelta = ORIGIN_COOLDOWN,
) -> bool:
    now = now or timezone.now()
    latest = list(
        EmailLinkRequest.objects.filter(ip_address=ip, purpose__in=purposes)
        .order_by("-created_at")
        .values_list("created_at", flat=True)[: window.max_count]
    )
    if len(latest) < window.max_count:
        return False
    newest, oldest = latest[0], latest[-1]
    return newest - oldest <= window.period and now < newest + cooldown


def recipient_limited(key: str, purpose: str, now=None, *, windows=RECIPIENT_WINDOWS) -> bool:
    now = now or timezone.now()
    sent = EmailLinkRequest.objects.filter(recipient_hash=key, purpose=purpose)
    return any(
        sent.filter(created_at__gt=now - window.period).count() >= window.max_count
        for window in windows
    )


# --- Formulari «Fer-se soci» (T-M01-13) --------------------------------------------------------
# Mateix mecanisme, amb llindars PROVISIONALS de la configuració [A validar] i comptadors propis.
JOIN = EmailLinkRequest.Purpose.JOIN


def _join_origin_window() -> Window:
    # Mai més llarg que RETENTION: la tasca diària esborra les peticions més velles.
    minutes = timedelta(minutes=settings.JOIN_FORM_ORIGIN_MINUTES)
    return Window(settings.JOIN_FORM_ORIGIN_MAX, min(minutes, RETENTION))


def start_join(ip: str) -> EmailLinkRequest | None:
    """Dins d'una transacció. Torna la petició acceptada, o None si l'origen està limitat
    (aleshores no es desa res). D'un en un per origen, com els enllaços del correu."""
    lock_origin(ip)
    window = _join_origin_window()
    if origin_limited(ip, purposes=(JOIN,), window=window, cooldown=window.period):
        return None
    return EmailLinkRequest.objects.create(ip_address=ip, purpose=JOIN)


def join_receipt_allowed(accepted: EmailLinkRequest, email: str) -> bool:
    """Dins de la mateixa transacció: es pot enviar el rebut a aquesta adreça? Si sí, la
    petició en guarda l'empremta i compta per al destinatari."""
    key = recipient_key(email)
    lock_recipient(key)
    windows = (Window(settings.JOIN_FORM_RECIPIENT_MAX_PER_DAY, timedelta(hours=24)),)
    if recipient_limited(key, JOIN, windows=windows):
        return False
    accepted.recipient_hash = key
    accepted.save(update_fields=["recipient_hash"])
    return True


# --- Verificació pública del carnet (T-M01-20; RN-M01-28, CA-M01-16) ---------------------------
# Límit per origen de V-01 (`security.py`): 20 consultes en 15 minuts → 15 minuts. Compten totes,
# vàlides o no, perquè el límit no digui res del testimoni. Només es desa l'origen.
CARD_VERIFY = EmailLinkRequest.Purpose.CARD_VERIFY
CARD_VERIFY_WINDOW = Window(IP_MAX_FAILURES, IP_WINDOW)


def start_card_verification(ip: str) -> bool:
    """Dins d'una transacció. Fals si l'origen està limitat (aleshores no es desa res)."""
    lock_origin(ip)
    if origin_limited(
        ip, purposes=(CARD_VERIFY,), window=CARD_VERIFY_WINDOW, cooldown=CARD_VERIFY_WINDOW.period
    ):
        return False
    EmailLinkRequest.objects.create(ip_address=ip, purpose=CARD_VERIFY)
    return True


def purge_old(now=None) -> int:
    now = now or timezone.now()
    deleted, _ = EmailLinkRequest.objects.filter(created_at__lte=now - RETENTION).delete()
    return deleted
