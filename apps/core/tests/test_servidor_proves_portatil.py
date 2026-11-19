"""Servidor de proves al portàtil (decisió 099; docs/guies/servidor-de-proves-al-portatil.md):
la configuració de proves mai no cobra ni envia correus a fora, i els secrets que es generen al
portàtil són vàlids i es poden llegir tal qual des de Docker Compose."""

import base64
import importlib

import pytest
from cryptography.fernet import Fernet

from apps.accounts.totp import DEMO_TOTP_SECRET
from deploy.proves import genera_secrets


@pytest.fixture
def staging(monkeypatch):
    for name in ("DJANGO_ALLOWED_HOSTS", "DJANGO_CSRF_TRUSTED_ORIGINS", "DJANGO_SSL_REDIRECT"):
        monkeypatch.delenv(name, raising=False)
    return importlib.reload(importlib.import_module("config.settings.staging"))


def test_staging_never_charges_nor_sends_mail_outside(staging):
    assert staging.DEBUG is False
    assert staging.PAYMENTS_PROVIDER == "fake"
    assert staging.PAYMENTS_ENVIRONMENT == "sandbox"
    assert staging.PAYMENTS_LIVE_CHARGES_ALLOWED is False
    assert staging.EMAIL_HOST == "mailpit"
    assert staging.SESSION_COOKIE_SECURE and staging.CSRF_COOKIE_SECURE


def test_staging_accepts_only_the_tunnels_and_the_laptop(staging):
    assert staging.ALLOWED_HOSTS == ["localhost", "127.0.0.1", ".trycloudflare.com", ".ts.net"]
    assert staging.CSRF_TRUSTED_ORIGINS == ["https://*.trycloudflare.com", "https://*.ts.net"]
    # Túnel i Caddy: dos salts davant de Django (V-01).
    assert staging.NUM_PROXIES == 2


def test_generated_secrets_are_valid_and_compose_safe():
    first, second = genera_secrets.genera(), genera_secrets.genera()
    for name, value in first.items():
        assert value and "$" not in value and '"' not in value and "\n" not in value, name
        assert value != second[name] or name == "CARD_QR_ACTIVE_KEY", name
    Fernet(first["FIELD_ENCRYPTION_KEYS"])
    version, key = first["MANDATE_ENCRYPTION_KEYS"].split(":")
    assert version == "1"
    Fernet(key)
    assert first["CARD_QR_KEYS"].startswith("k1:") and len(first["CARD_QR_KEYS"]) > 3 + 32
    totp = first["STAGING_TOTP_SECRET"]
    assert len(totp) >= 32 and totp != DEMO_TOTP_SECRET
    base64.b32decode(totp)
    assert first["DATABASE_URL"] == f"postgres://cris:{first['POSTGRES_PASSWORD']}@db:5432/cris"
