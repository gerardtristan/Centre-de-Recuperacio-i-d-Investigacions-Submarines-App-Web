"""Xifratge de camps sensibles (secrets TOTP; més endavant, el mandat de la 044).

Les claus surten de FIELD_ENCRYPTION_KEYS, separades per comes. La primera xifra; totes
desxifren, de manera que una clau nova es pot afegir al davant sense perdre les dades antigues.
"""

from functools import cache

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings


@cache
def _fernet() -> MultiFernet:
    keys = settings.FIELD_ENCRYPTION_KEYS
    if not keys:
        raise RuntimeError("Falta FIELD_ENCRYPTION_KEYS.")
    return MultiFernet([Fernet(key) for key in keys])


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
