"""Proves automàtiques. Només dades inventades."""

import os

from cryptography.fernet import Fernet

# Valor fix només per a les proves: no protegeix res i no s'usa en cap altre entorn.
os.environ.setdefault("DJANGO_SECRET_KEY", "nomes-per-a-proves")
# Clau nova a cada execució: les proves no depenen de cap clau guardada.
os.environ.setdefault("FIELD_ENCRYPTION_KEYS", Fernet.generate_key().decode())

from .base import *  # noqa: E402, F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Correu en memòria de Django: cap correu surt de les proves.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
