"""Comprovació de credencials i límit d'intents (spec 00, RN-14, RN-18, RN-24; V-01).

Regles protegides (059): no són permisos editables.
"""

import ipaddress
import logging
import secrets
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit

from . import totp
from .models import Account, FailedLogin, TotpDevice, normalize_login

logger = logging.getLogger("cris.security")

# Els bloquejos els aplica la plataforma sola (V-01): al registre, l'actor és «sistema».
LOCKOUT_ACTOR = audit.system("login-attempt-limit")

# V-01
ACCOUNT_MAX_FAILURES = 5
ACCOUNT_LOCK = timedelta(minutes=15)
IP_MAX_FAILURES = 20
IP_WINDOW = timedelta(minutes=15)

# V-01: credencial temporal d'un restabliment per un altre administrador (HU-08).
TEMPORARY_PASSWORD_VALIDITY = timedelta(hours=24)
_TEMPORARY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sense 0/O ni 1/I

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


def _advisory_lock(key: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", [key])


def lock_account_attempts(account: Account) -> None:
    """Dins de `serialized_attempts`: espera el torn del compte i en torna a llegir l'estat,
    que una altra petició pot haver canviat mentre esperava."""
    _advisory_lock(f"cris-attempts-account:{account.pk}")
    account.refresh_from_db(
        fields=[
            "failed_login_count",
            "locked_until",
            "status",
            "password",
            "password_temporary_until",
        ]
    )


@contextmanager
def serialized_attempts(request, account: Account | None = None):
    """Una comprovació de credencials alhora per origen i per compte (C3, V-01).

    Sense això, moltes peticions simultànies llegeixen el comptador abans que cap altra hi
    hagi desat el seu intent, i s'avaluen més contrasenyes o codis dels que permet el límit
    (ho mostra la prova de càrrega de C3). Els bloquejos consultius de PostgreSQL duren fins al
    final de la transacció. Sempre l'origen primer i després el compte: amb aquest ordre fix,
    dues peticions no es poden esperar l'una a l'altra."""
    with transaction.atomic():
        _advisory_lock(f"cris-attempts-ip:{client_ip(request)}")
        if account is not None:
            lock_account_attempts(account)
        yield


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
                # RN-M01-80 (Q-088): es tanquen totes les sessions del compte, també la que fa
                # una reautenticació (vegeu `Account.end_all_sessions`).
                locked.session_epoch += 1
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
            locked.save(
                update_fields=["failed_login_count", "locked_until", "session_epoch", "updated_at"]
            )
    if account is not None:
        account.refresh_from_db(fields=["failed_login_count", "locked_until", "session_epoch"])
        logger.info("login_failed account=%s area=%s ip=%s reason=%s", account.pk, area, ip, reason)
    if ip_is_blocked(ip):
        logger.warning("ip_blocked ip=%s area=%s", ip, area)
        audit.record(
            audit.Action.IP_BLOCKED, actor=LOCKOUT_ACTOR, details={"area": area}, request=request
        )


def new_temporary_password() -> str:
    """Credencial temporal: 16 caràcters aleatoris (80 bits) en quatre grups, fàcils de dictar.
    Es mostra una sola vegada a qui fa el restabliment i no es desa enlloc més."""
    raw = "".join(secrets.choice(_TEMPORARY_ALPHABET) for _ in range(16))
    return "-".join(raw[i : i + 4] for i in range(0, 16, 4))


def reset_failures(account: Account) -> None:
    if account.failed_login_count or account.locked_until:
        account.failed_login_count = 0
        account.locked_until = None
        account.save(update_fields=["failed_login_count", "locked_until", "updated_at"])


WRONG_PASSWORD = _("Contrasenya incorrecta")
WRONG_CODE = _("Codi incorrecte")
TOO_MANY_ATTEMPTS = _("S'han fet massa intents. Torna-ho a provar d'aquí a una estona.")


def confirm_password_and_code(
    request,
    account: Account,
    area: str,
    password: str,
    code: str,
    *,
    code_only_with_totp: bool = False,
):
    """Torna a demanar la contrasenya i un codi TOTP vàlid a un compte amb sessió (CA-05.2).
    Torna None si tots dos són correctes, o el missatge d'error.

    Comprovació mínima amb les peces de l'entrada: els errors compten com a intents fallits
    del compte i de l'origen (V-01) i queden al registre; amb el compte o l'origen bloquejats
    no es comprova res. El missatge no diu quants intents queden. El codi no es comprova (ni
    es gasta) si la contrasenya és incorrecta. Aquí no hi ha cap finestra de temps.

    `code_only_with_totp`: el codi només es demana si el compte té TOTP actiu (reautenticació
    de la T-M00-05, `reauth.require_recent_auth`); per defecte, sense TOTP, falla."""
    with serialized_attempts(request, account):
        if ip_is_blocked(client_ip(request)) or account.is_locked(timezone.now()):
            return TOO_MANY_ATTEMPTS
        if not account.check_password(password):
            record_failure(request, area, account, "bad_password")
            return TOO_MANY_ATTEMPTS if account.is_locked(timezone.now()) else WRONG_PASSWORD
        device = account.totp_device if account.has_totp else None
        needs_code = device is not None or not code_only_with_totp
        if needs_code and (device is None or not totp.verify_code(device, code)):
            record_failure(request, area, account, "bad_code")
            return TOO_MANY_ATTEMPTS if account.is_locked(timezone.now()) else WRONG_CODE
        reset_failures(account)
        return None


def confirm_code(request, account: Account, area: str, code: str):
    """Torna a demanar un codi TOTP a un compte amb sessió (RN-M01-60: abans de restablir un
    altre compte). Torna None si és correcte, o el missatge d'error.

    El codi ha de ser nou: `totp.verify_code` no accepta cap interval igual o anterior a
    l'últim acceptat, tampoc el de l'entrada. Els errors compten per al bloqueig de V-01 i
    queden al registre; amb el compte o l'origen bloquejats no es comprova res."""
    with serialized_attempts(request, account):
        if ip_is_blocked(client_ip(request)) or account.is_locked(timezone.now()):
            return TOO_MANY_ATTEMPTS
        device = TotpDevice.objects.filter(account=account, confirmed_at__isnull=False).first()
        if device is None or not totp.verify_code(device, code):
            record_failure(request, area, account, "bad_code")
            return TOO_MANY_ATTEMPTS if account.is_locked(timezone.now()) else WRONG_CODE
        reset_failures(account)
        return None


@dataclass
class CredentialCheck:
    account: Account | None = None
    error: str | None = None
    # Compte pendent amb la contrasenya correcta: no té sessió, però se li pot oferir el
    # reenviament de la verificació (RN-M01-59).
    pending: Account | None = None


def check_credentials(request, area: str, login: str, password: str) -> CredentialCheck:
    """Primer pas de l'entrada. Cada entrada només troba els comptes del seu tipus (RN-14):
    un compte d'administrador no existeix per a l'àrea de socis, i a l'inrevés.

    Les comprovacions del mateix origen i del mateix compte van d'una en una
    (`serialized_attempts`)."""
    with serialized_attempts(request):
        return _check_credentials(request, area, login, password)


def _check_credentials(request, area: str, login: str, password: str) -> CredentialCheck:
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
    lock_account_attempts(account)

    if account.is_locked(timezone.now()):
        record_failure(request, area, account, "locked")
        return CredentialCheck(error=GENERIC_ERROR)

    if not account.check_password(password):
        record_failure(request, area, account, "bad_password")
        return CredentialCheck(error=GENERIC_ERROR)

    if account.status == Account.Status.PENDING:
        # La contrasenya és correcta: dir-ho no revela res a qui no és el titular.
        return CredentialCheck(error=PENDING_ERROR, pending=account)
    if account.status != Account.Status.ACTIVE:
        record_failure(request, area, account, "disabled")
        return CredentialCheck(error=GENERIC_ERROR)
    if account.temporary_password_expired(timezone.now()):
        # CA-08.1: la credencial temporal caduca (V-01). Cal un restabliment nou.
        record_failure(request, area, account, "temporary_expired")
        return CredentialCheck(error=GENERIC_ERROR)

    return CredentialCheck(account=account)
