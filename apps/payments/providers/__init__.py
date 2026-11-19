"""Proveïdors de pagaments darrere d'un adaptador (decisió 043). Vegeu `base.PaymentProvider`."""

from dataclasses import replace

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from apps.core import business_settings

from .base import Capabilities, PaymentProvider, ProviderNotConfigured

# Codi de configuració → classe. El proveïdor real s'hi afegeix amb la T-M05a-05.
REGISTRY = {"fake": "apps.payments.providers.fake.FakeProvider"}


def get_provider() -> PaymentProvider:
    """La implementació configurada a `PAYMENTS_PROVIDER`. Sense configuració, no es cobra."""
    code = settings.PAYMENTS_PROVIDER
    if code not in REGISTRY:
        raise ProviderNotConfigured(code)
    return import_string(REGISTRY[code])()


# P-131 (095) i VC-14: els mètodes que el club té actius, un ajust per mètode que només edita
# l'Administrador amb un codi TOTP nou i nota (els crea `payments/0026`). Les claus i els secrets
# continuen a les variables d'entorn.
SWITCHES = "payments.provider"
# Capacitat → sufix de la clau («token» no pot sortir a cap camp del registre: RN-52).
SWITCH_NAMES = {"card": "card", "bizum": "bizum", "tokenization": "saved_card"}
SWITCH_LABELS = {"card": _("targeta"), "bizum": _("Bizum"), "saved_card": _("targeta guardada")}


def switch_key(capability: str) -> str:
    return f"{SWITCHES}.{SWITCH_NAMES[capability]}_enabled"


def switch_label(suffix: str) -> str:
    return SWITCH_LABELS[suffix.removesuffix("_enabled")]


def enabled_capabilities() -> Capabilities:
    """El que el proveïdor declara (`capabilities()`) i, a més, el club té actiu. És el que
    ofereixen les pantalles i el que accepta el cobrament (P-196: totes dues condicions)."""
    declared = get_provider().capabilities()
    active = {c: business_settings.get(switch_key(c)) for c in SWITCH_NAMES}
    return replace(declared, **{c: getattr(declared, c) and on for c, on in active.items()})
