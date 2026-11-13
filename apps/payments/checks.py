"""Comprovacions d'arrencada dels pagaments (`manage.py check`): la configuració no pot deixar
cobrar per error (RN-M05a-11) ni fer servir el proveïdor fals amb l'entorn real."""

from django.conf import settings
from django.core.checks import Error, register

from .providers import REGISTRY
from .providers.base import ENVIRONMENTS, LIVE


@register()
def payments_settings(app_configs, **kwargs):
    errors = []
    code = settings.PAYMENTS_PROVIDER
    environment = settings.PAYMENTS_ENVIRONMENT
    if environment not in ENVIRONMENTS:
        errors.append(
            Error("PAYMENTS_ENVIRONMENT ha de ser «sandbox» o «live».", id="payments.E001")
        )
    if code and code not in REGISTRY:
        errors.append(Error("PAYMENTS_PROVIDER no és cap proveïdor conegut.", id="payments.E002"))
    if code == "fake" and environment == LIVE:
        errors.append(
            Error("El proveïdor fals no es pot fer servir amb l'entorn real.", id="payments.E003")
        )
    if settings.PAYMENTS_LIVE_CHARGES_ALLOWED and environment != LIVE:
        errors.append(
            Error(
                "PAYMENTS_LIVE_CHARGES_ALLOWED només té sentit amb l'entorn real.",
                id="payments.E004",
            )
        )
    return errors
