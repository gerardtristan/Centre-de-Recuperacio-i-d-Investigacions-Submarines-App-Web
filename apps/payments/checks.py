"""Comprovacions d'arrencada dels pagaments (`manage.py check`): la configuració no pot deixar
cobrar per error (RN-M05a-11), fer servir el proveïdor fals amb l'entorn real ni portar una clau
del mandat mal formada (044)."""

from django.conf import settings
from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured

from . import crypto
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
    try:
        crypto._parse(tuple(settings.MANDATE_ENCRYPTION_KEYS))
    except ImproperlyConfigured as error:
        errors.append(Error(str(error), id="payments.E005"))
    return errors


def refuse_fake_integrations() -> None:
    """Decisió 092: el proveïdor fictici no arrenca a producció ni amb l'entorn real. Es crida a
    `ready()`, de manera que cap procés (web, cua, `manage.py`) no arrenca: les comprovacions de
    `check` no corren amb el servidor web."""
    forbidden = settings.FAKE_INTEGRATIONS_FORBIDDEN or settings.PAYMENTS_ENVIRONMENT == LIVE
    if settings.PAYMENTS_PROVIDER == "fake" and forbidden:
        raise ImproperlyConfigured(
            "Decisió 092: el proveïdor de pagaments fictici no es pot fer servir a producció "
            "ni amb l'entorn real. Configura PAYMENTS_PROVIDER amb el proveïdor real."
        )
