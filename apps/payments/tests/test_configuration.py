"""Configuració dels pagaments: quin proveïdor es fa servir i què no pot arrencar (RN-M05a-11)."""

import pytest
from django.core.checks import run_checks

from apps.payments import services
from apps.payments.providers import base, get_provider
from apps.payments.providers.fake import FakeProvider


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
