"""Proves automàtiques. Només dades inventades."""

import os

# Valor fix només per a les proves: no protegeix res i no s'usa en cap altre entorn.
os.environ.setdefault("DJANGO_SECRET_KEY", "nomes-per-a-proves")

from .base import *  # noqa: E402, F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
