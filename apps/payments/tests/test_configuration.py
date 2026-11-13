"""Configuració dels pagaments: quin proveïdor es fa servir i què no pot arrencar (RN-M05a-11)."""

import os
import secrets
import subprocess
import sys

import pytest
from cryptography.fernet import Fernet
from django.apps import apps
from django.conf import settings as django_settings
from django.core.checks import run_checks
from django.core.exceptions import ImproperlyConfigured

from apps.payments import checks, services
from apps.payments.providers import base, get_provider
from apps.payments.providers.fake import FakeProvider
from conftest import PASSWORD


def payment_errors():
    return {error.id for error in run_checks() if error.id.startswith("payments.")}


def test_tests_use_the_fake_provider():
    assert isinstance(services.provider(), FakeProvider)
    assert isinstance(get_provider(), base.PaymentProvider)


@pytest.mark.parametrize("code", ["", "desconegut"])
def test_without_a_known_provider_nothing_can_be_charged(settings, code):
    settings.PAYMENTS_PROVIDER = code
    with pytest.raises(base.ProviderNotConfigured):
        services.provider()


def test_test_configuration_passes_the_checks():
    assert payment_errors() == set()


def test_no_provider_passes_the_checks(settings):
    settings.PAYMENTS_PROVIDER = ""
    assert payment_errors() == set()


def test_unknown_environment_is_an_error(settings):
    settings.PAYMENTS_ENVIRONMENT = "produccio"
    assert payment_errors() == {"payments.E001"}


def test_unknown_provider_is_an_error(settings):
    settings.PAYMENTS_PROVIDER = "desconegut"
    assert payment_errors() == {"payments.E002"}


def test_fake_provider_with_the_real_environment_is_an_error(settings):
    settings.PAYMENTS_ENVIRONMENT = "live"
    assert payment_errors() == {"payments.E003"}


def test_live_charges_without_the_real_environment_is_an_error(settings):
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = True
    assert payment_errors() == {"payments.E004"}


def test_safeguard_lets_charges_through_only_when_allowed(settings):
    base.ensure_charges_allowed()  # entorn de proves: cap restricció
    settings.PAYMENTS_ENVIRONMENT = "live"
    with pytest.raises(base.LiveChargesNotAllowed):
        base.ensure_charges_allowed()
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = True
    base.ensure_charges_allowed()


@pytest.mark.parametrize("environment", ["LIVE", "produccio", "", None])
def test_safeguard_treats_an_unknown_environment_as_the_real_one(settings, environment):
    settings.PAYMENTS_ENVIRONMENT = environment
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = True
    with pytest.raises(base.LiveChargesNotAllowed):
        base.ensure_charges_allowed()


# --- Decisió 092: el proveïdor fictici no arrenca a producció ---------------------------------


@pytest.mark.parametrize(
    ("forbidden", "environment"), [(True, "sandbox"), (False, "live"), (True, "live")]
)
def test_092_the_fake_provider_refuses_to_start_in_production_or_live(
    settings, forbidden, environment
):
    settings.FAKE_INTEGRATIONS_FORBIDDEN = forbidden
    settings.PAYMENTS_ENVIRONMENT = environment
    with pytest.raises(ImproperlyConfigured):
        checks.refuse_fake_integrations()
    with pytest.raises(ImproperlyConfigured):  # ho fa en arrencar l'aplicació
        apps.get_app_config("payments").ready()


def test_092_outside_production_the_fake_provider_starts(settings):
    checks.refuse_fake_integrations()  # proves: fals, entorn de proves, no prohibit
    settings.FAKE_INTEGRATIONS_FORBIDDEN = True
    settings.PAYMENTS_PROVIDER = ""
    checks.refuse_fake_integrations()  # producció sense el fals: arrenca


def _start_production(provider):
    """Arrenca Django amb la configuració de producció en un procés a part, amb valors
    inventats generats aquí (cap secret real). No connecta amb cap base ni envia res."""
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.prod",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
        "FIELD_ENCRYPTION_KEYS": Fernet.generate_key().decode(),
        "CARD_QR_KEYS": f"ci:{secrets.token_urlsafe(32)}",
        "CARD_QR_ACTIVE_KEY": "ci",
        "DJANGO_ALLOWED_HOSTS": "cris1954.cat",
        "EMAIL_HOST": "smtp.example.invalid",
        "EMAIL_HOST_USER": "proves",
        "EMAIL_HOST_PASSWORD": PASSWORD,
        "S3_BUCKET_FITXERS": "cris-ci",
        "S3_ENDPOINT_URL": "https://s3.example.invalid",
        "S3_ACCESS_KEY_ID": "proves",
        "S3_SECRET_ACCESS_KEY": PASSWORD,
        "PAYMENTS_PROVIDER": provider,
        "PAYMENTS_ENVIRONMENT": "sandbox",
    }
    env.setdefault("DATABASE_URL", "postgres://cris:cris-ci@localhost:5432/cris")
    return subprocess.run(  # noqa: S603 (ordre fixa d'aquesta prova)
        [sys.executable, "-c", "import django; django.setup()"],
        cwd=django_settings.BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_092_production_does_not_start_with_the_fake_provider():
    refused = _start_production("fake")
    assert refused.returncode != 0
    assert "ImproperlyConfigured" in refused.stderr and "092" in refused.stderr
    assert _start_production("").returncode == 0
