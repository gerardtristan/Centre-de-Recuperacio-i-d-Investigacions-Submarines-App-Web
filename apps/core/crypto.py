"""Xifratge de camps sensibles (secrets TOTP; més endavant, el mandat de la 044).

Les claus surten de FIELD_ENCRYPTION_KEYS, separades per comes. La primera xifra; totes
desxifren, de manera que una clau nova es pot afegir al davant sense perdre les dades antigues.

Els fitxers privats xifrats (documents de justificació de la 051 i fotos de titulacions de la
104) fan servir una clau pròpia, FILE_ENCRYPTION_KEYS, amb la mateixa rotació
(`encrypt_bytes` i `decrypt_bytes`; T-M09-25a). Sense cap clau no es desa cap fitxer d'aquests.
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


@cache
def _file_fernet() -> MultiFernet:
    keys = settings.FILE_ENCRYPTION_KEYS
    if not keys:
        raise RuntimeError("Falta FILE_ENCRYPTION_KEYS.")
    return MultiFernet([Fernet(key) for key in keys])


def encrypt_bytes(content: bytes) -> bytes:
    return _file_fernet().encrypt(content)


def decrypt_bytes(token: bytes) -> bytes:
    return _file_fernet().decrypt(token)
