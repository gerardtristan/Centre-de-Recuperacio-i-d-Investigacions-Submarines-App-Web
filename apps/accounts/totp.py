"""Doble factor TOTP (RFC 6238) i codis de recuperació (spec 00, HU-07 i HU-09; V-01)."""

import hashlib
import hmac
import secrets
from datetime import timedelta

import pyotp
import qrcode
import qrcode.image.svg
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.crypto import decrypt, encrypt

from .models import Account, RecoveryCode, TotpDevice

RECOVERY_CODE_COUNT = 10  # V-01
# S'accepta el codi de l'interval anterior i del següent per tolerar el desajust del rellotge.
VALID_WINDOW = 1
_RECOVERY_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sense 0/O ni 1/I
# Secret TOTP de PROVA (074, punt 21): públic, el fan servir els comptes d'administració de
# `seed_demo_data`. No és cap secret; per això `verify_code` el rebutja sense DEBUG (075, punt 8).
DEMO_TOTP_SECRET = "PROVESCRISNOESSECRETPROVESCRIS22"  # noqa: S105 gitleaks:allow (TOTP de prova)


def start_enrolment(account: Account) -> TotpDevice:
    """Factor nou pendent de confirmar. Substitueix qualsevol factor anterior no confirmat."""
    TotpDevice.objects.filter(account=account, confirmed_at__isnull=True).delete()
    if TotpDevice.objects.filter(account=account).exists():
        raise ValueError("El compte ja té un factor TOTP confirmat.")
    return TotpDevice.objects.create(
        account=account, secret_encrypted=encrypt(pyotp.random_base32())
    )


def secret_of(device: TotpDevice) -> str:
    return decrypt(device.secret_encrypted)


def provisioning_uri(device: TotpDevice) -> str:
    return pyotp.TOTP(secret_of(device)).provisioning_uri(
        name=device.account.login, issuer_name=settings.TOTP_ISSUER_NAME
    )


def qr_svg(uri: str) -> str:
    image = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage, box_size=8)
    return image.to_string(encoding="unicode")


def verify_code(device: TotpDevice, code: str, now=None) -> bool:
    """Comprova el codi i en marca l'interval com a usat, de manera que el mateix codi
    (o un d'anterior) no torna a servir."""
    code = "".join((code or "").split())
    if not (code.isdigit() and len(code) == 6):
        return False
    secret = secret_of(device)
    if not settings.DEBUG and secret == DEMO_TOTP_SECRET:  # RN-M01-84: mai fora de desenvolupament
        return False
    now = now or timezone.now()
    totp = pyotp.TOTP(secret)
    with transaction.atomic():
        locked = TotpDevice.objects.select_for_update().get(pk=device.pk)
        for offset in range(-VALID_WINDOW, VALID_WINDOW + 1):
            moment = now + timedelta(seconds=totp.interval * offset)
            step = totp.timecode(moment)
            if locked.last_used_step is not None and step <= locked.last_used_step:
                continue
            if hmac.compare_digest(totp.at(moment), code):
                locked.last_used_step = step
                locked.save(update_fields=["last_used_step"])
                device.last_used_step = step
                return True
    return False


@transaction.atomic
def confirm_enrolment(
    device: TotpDevice, code: str, *, recovery_codes: bool = True
) -> list[str] | None:
    """Confirma l'alta amb un codi vàlid i genera els codis de recuperació nous, que es
    mostren una sola vegada (CA-09.1). Retorna None si el codi no és vàlid.

    Els comptes personals no en tenen (V-01 només en preveu per als d'administrador): amb
    `recovery_codes=False`, torna una llista buida. Què fa un soci que perd el mòbil és un
    pendent de la junta (pendents.md) que s'ha de resoldre abans de producció."""
    if not verify_code(device, code):
        return None
    device.confirmed_at = timezone.now()
    device.save(update_fields=["confirmed_at"])
    if not recovery_codes:
        return []
    return regenerate_recovery_codes(device.account)


@transaction.atomic
def disable(account: Account) -> None:
    """Treu el doble factor d'un compte (i els codis de recuperació que pogués tenir)."""
    TotpDevice.objects.filter(account=account).delete()
    RecoveryCode.objects.filter(account=account).delete()


def regenerate_recovery_codes(account: Account) -> list[str]:
    RecoveryCode.objects.filter(account=account).delete()
    codes = [_new_recovery_code() for _ in range(RECOVERY_CODE_COUNT)]
    RecoveryCode.objects.bulk_create(
        RecoveryCode(account=account, code_hash=_hash_recovery_code(code)) for code in codes
    )
    return codes


@transaction.atomic
def use_recovery_code(account: Account, code: str) -> bool:
    """Un codi vàlid permet entrar una vegada. Com que qui el fa servir ha perdut el mòbil,
    el factor TOTP s'esborra i s'ha de tornar a donar d'alta (CA-09.2)."""
    match = (
        RecoveryCode.objects.select_for_update()
        .filter(account=account, code_hash=_hash_recovery_code(code), used_at__isnull=True)
        .first()
    )
    if match is None:
        return False
    match.used_at = timezone.now()
    match.save(update_fields=["used_at"])
    TotpDevice.objects.filter(account=account).delete()
    return True


def _new_recovery_code() -> str:
    raw = "".join(secrets.choice(_RECOVERY_ALPHABET) for _ in range(16))
    return "-".join(raw[i : i + 4] for i in range(0, 16, 4))


def _hash_recovery_code(code: str) -> str:
    # 80 bits d'entropia: n'hi ha prou amb SHA-256, i els intents ja estan limitats (V-01).
    normalized = "".join((code or "").upper().split()).replace("-", "")
    return hashlib.sha256(normalized.encode()).hexdigest()
