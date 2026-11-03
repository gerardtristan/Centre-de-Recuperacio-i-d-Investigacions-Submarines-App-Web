"""Límits dels enllaços del correu: recuperació i reenviament de la verificació (decisió 065,
RN-M01-58). Són valors de seguretat al codi, com els de V-01 (`security.py`): les regles de
seguretat no s'editen des de l'app (059). Per ajustar-los cal una decisió nova que canviï
RN-M01-58 i, després, el valor d'aquest fitxer; les proves el llegeixen d'aquí.

- Per destinatari (adreça normalitzada) i finalitat: com a màxim 3 correus per hora i 6 cada
  24 hores, vinguin d'on vinguin les peticions.
- Per origen, conjunt per a les dues finalitats: quan arriba a 10 peticions acceptades en
  15 minuts, queda limitat 15 minuts comptats des de la desena.
- Només es desen les peticions acceptades: una de limitada no compta i no allarga res.
- No té res a veure amb el comptador d'intents fallits de l'entrada (V-01).
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db import connection
from django.utils import timezone
from django.utils.crypto import salted_hmac

from apps.core.normalization import normalize_email

from .models import EmailLinkRequest


@dataclass(frozen=True)
class Window:
    max_count: int
    period: timedelta


RECIPIENT_WINDOWS = (Window(3, timedelta(hours=1)), Window(6, timedelta(hours=24)))
ORIGIN_WINDOW = Window(10, timedelta(minutes=15))
ORIGIN_COOLDOWN = timedelta(minutes=15)
# RN-M01-59: estat intermedi d'un compte pendent per demanar un reenviament (un de sol).
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


def origin_limited(ip: str, now=None) -> bool:
    now = now or timezone.now()
    latest = list(
        EmailLinkRequest.objects.filter(ip_address=ip)
        .order_by("-created_at")
        .values_list("created_at", flat=True)[: ORIGIN_WINDOW.max_count]
    )
    if len(latest) < ORIGIN_WINDOW.max_count:
        return False
    newest, oldest = latest[0], latest[-1]
    return newest - oldest <= ORIGIN_WINDOW.period and now < newest + ORIGIN_COOLDOWN


def recipient_limited(key: str, purpose: str, now=None) -> bool:
    now = now or timezone.now()
    sent = EmailLinkRequest.objects.filter(recipient_hash=key, purpose=purpose)
    return any(
        sent.filter(created_at__gt=now - window.period).count() >= window.max_count
        for window in RECIPIENT_WINDOWS
    )


def purge_old(now=None) -> int:
    now = now or timezone.now()
    deleted, _ = EmailLinkRequest.objects.filter(created_at__lte=now - RETENTION).delete()
    return deleted
