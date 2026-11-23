"""Proves automàtiques. Només dades inventades."""

import os
import tempfile

from cryptography.fernet import Fernet

# Valor fix només per a les proves: no protegeix res i no s'usa en cap altre entorn.
os.environ.setdefault("DJANGO_SECRET_KEY", "nomes-per-a-proves")
# Clau nova a cada execució: les proves no depenen de cap clau guardada.
os.environ.setdefault("FIELD_ENCRYPTION_KEYS", Fernet.generate_key().decode())
os.environ.setdefault("MANDATE_ENCRYPTION_KEYS", "1:" + Fernet.generate_key().decode())

from .base import *  # noqa: E402, F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Correu en memòria de Django: cap correu surt de les proves.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Fitxers privats en una carpeta temporal, fora del repositori.
STORAGES = {
    **STORAGES,  # noqa: F405
    "private": {
        "BACKEND": "apps.core.files.LocalSignedStorage",
        "OPTIONS": {"location": tempfile.mkdtemp(prefix="cris-fitxers-proves-")},
    },
}

# Proveïdor de pagaments fals, sense xarxa (T-M05a-03): cap prova surt cap a fora.
PAYMENTS_PROVIDER = "fake"
PAYMENTS_ENVIRONMENT = "sandbox"
PAYMENTS_LIVE_CHARGES_ALLOWED = False

# Com al CI: el .env local no encén «En construcció»; la prova que ho vol ho diu (T-DX-91).
SHOW_UNDER_CONSTRUCTION = False
