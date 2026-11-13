"""Serveis que el mòdul de pagaments ofereix a la resta de l'aplicació (M05a-8)."""

from .providers import get_provider
from .providers.base import PaymentProvider


def provider() -> PaymentProvider:
    """`payments.provider()`: l'adaptador del proveïdor configurat."""
    return get_provider()
