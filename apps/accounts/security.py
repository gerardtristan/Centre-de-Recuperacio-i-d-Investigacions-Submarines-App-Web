"""Comprovació de credencials i límit d'intents (spec 00, RN-14, RN-18, RN-24; V-01).

Regles protegides (059): no són permisos editables.
"""

import ipaddress
import logging
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit

from .models import Account, FailedLogin, normalize_login

logger = logging.getLogger("cris.security")

# Els bloquejos els aplica la plataforma sola (V-01): al registre, l'actor és «sistema».
LOCKOUT_ACTOR = audit.system("login-attempt-limit")

# V-01
ACCOUNT_MAX_FAILURES = 5
ACCOUNT_LOCK = timedelta(minutes=15)
IP_MAX_FAILURES = 20
IP_WINDOW = timedelta(minutes=15)

AREA_PERSONAL = "personal"
AREA_ADMIN = "admin"
KIND_BY_AREA = {AREA_PERSONAL: Account.Kind.PERSONAL, AREA_ADMIN: Account.Kind.ADMIN}

# El mateix missatge per a identificador desconegut, contrasenya incorrecta, compte bloquejat
# o desactivat i origen bloquejat: no revela si el compte existeix.
GENERIC_ERROR = _(
    "Les dades no són correctes, o s'han fet massa intents. Torna-ho a provar d'aquí a una estona."
)
PENDING_ERROR = _(
    "Encara has de confirmar el correu. Obre l'enllaç que t'hem enviat per activar el compte."
)


def client_ip(request) -> str:
    """IP d'origen. Darrere de NUM_PROXIES proxies de confiança, la llegeix de
    X-Forwarded-For comptant des de la dreta; el que hi hagi més a l'esquerra ho pot
    escriure el client i no se'n fa cas."""
    remote = request.META.get("REMOTE_ADDR", "")
    if settings.NUM_PROXIES:
        forwarded = [
            ip.strip() for ip in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if ip
        ]
        if len(forwarded) >= settings.NUM_PROXIES:
            remote = forwarded[-settings.NUM_PROXIES]
    try:
        return str(ipaddress.ip_address(remote))
    except ValueError:
        return "0.0.0.0"  # noqa: S104 (valor de reserva, no és cap adreça d'escolta)


def ip_is_blocked(ip: str, now=None) -> bool:
    now = now or timezone.now()
    recent = FailedLogin.objects.filter(ip_address=ip, created_at__gt=now - IP_WINDOW)
    return recent.count() >= IP_MAX_FAILURES


def record_failure(request, area: str, account: Account | None, reason: str) -> None:
    """Desa l'intent fallit per a l'origen i, si hi ha compte, en compta un més seguit.
    Al cinquè, el compte queda bloquejat 15 minuts."""
    ip = client_ip(request)
    with transaction.atomic():
        FailedLogin.objects.create(ip_address=ip, account=account, area=area)
        # Qui ho prova no està identificat. L'identificador escrit no es guarda: podria ser
        # una dada personal o una contrasenya escrita al camp equivocat.
        audit.record(
            audit.Action.LOGIN_FAILED,
            actor=audit.ANONYMOUS,
            target=account,
            details={"area": area, "reason": reason},
            request=request,
        )
        if account is None:
            logger.info("login_failed area=%s ip=%s reason=%s", area, ip, reason)
        else:
            locked = Account.objects.select_for_update().get(pk=account.pk)
            locked.failed_login_count += 1
            if locked.failed_login_count >= ACCOUNT_MAX_FAILURES:
                locked.failed_login_count = 0
                locked.locked_until = timezone.now() + ACCOUNT_LOCK
                logger.warning("account_locked account=%s area=%s ip=%s", account.pk, area, ip)
                audit.record(
                    audit.Action.ACCOUNT_LOCKED,
                    actor=LOCKOUT_ACTOR,
                    target=account,
                    field="locked_until",
                    new=locked.locked_until,
                    details={"area": area},
                    request=request,
                )
            locked.save(update_fields=["failed_login_count", "locked_until", "updated_at"])
    if account is not None:
        account.refresh_from_db(fields=["failed_login_count", "locked_until"])
        logger.info("login_failed account=%s area=%s ip=%s reason=%s", account.pk, area, ip, reason)
    if ip_is_blocked(ip):
        logger.warning("ip_blocked ip=%s area=%s", ip, area)
        audit.record(
            audit.Action.IP_BLOCKED, actor=LOCKOUT_ACTOR, details={"area": area}, request=request
        )


def reset_failures(account: Account) -> None:
    if account.failed_login_count or account.locked_until:
        account.failed_login_count = 0
        account.locked_until = None
        account.save(update_fields=["failed_login_count", "locked_until", "updated_at"])


@dataclass
class CredentialCheck:
    account: Account | None = None
    error: str | None = None


def check_credentials(request, area: str, login: str, password: str) -> CredentialCheck:
    """Primer pas de l'entrada. Cada entrada només troba els comptes del seu tipus (RN-14):
    un compte d'administrador no existeix per a l'àrea de socis, i a l'inrevés."""
    if ip_is_blocked(client_ip(request)):
        return CredentialCheck(error=GENERIC_ERROR)

    account = (
        Account.objects.select_related("totp_device")
        .filter(login=normalize_login(login), kind=KIND_BY_AREA[area])
        .first()
    )
    if account is None:
        # Mateix cost que una comprovació real, perquè el temps de resposta no ho delati.
        Account().set_password(password)
        record_failure(request, area, None, "unknown_login")
        return CredentialCheck(error=GENERIC_ERROR)

    if account.is_locked(timezone.now()):
        record_failure(request, area, account, "locked")
        return CredentialCheck(error=GENERIC_ERROR)

    if not account.check_password(password):
        record_failure(request, area, account, "bad_password")
        return CredentialCheck(error=GENERIC_ERROR)

    if account.status == Account.Status.PENDING:
        # La contrasenya és correcta: dir-ho no revela res a qui no és el titular.
        return CredentialCheck(error=PENDING_ERROR)
    if account.status != Account.Status.ACTIVE:
        record_failure(request, area, account, "disabled")
        return CredentialCheck(error=GENERIC_ERROR)

    return CredentialCheck(account=account)
