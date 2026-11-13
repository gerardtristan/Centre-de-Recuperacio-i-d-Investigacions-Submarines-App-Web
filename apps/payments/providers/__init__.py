"""Proveïdors de pagaments darrere d'un adaptador (decisió 043). Vegeu `base.PaymentProvider`."""

from django.conf import settings
from django.utils.module_loading import import_string

from .base import PaymentProvider, ProviderNotConfigured

# Codi de configuració → classe. El proveïdor real s'hi afegeix amb la T-M05a-05.
REGISTRY = {"fake": "apps.payments.providers.fake.FakeProvider"}


def get_provider() -> PaymentProvider:
    """La implementació configurada a `PAYMENTS_PROVIDER`. Sense configuració, no es cobra."""
    code = settings.PAYMENTS_PROVIDER
    if code not in REGISTRY:
        raise ProviderNotConfigured(code)
    return import_string(REGISTRY[code])()
