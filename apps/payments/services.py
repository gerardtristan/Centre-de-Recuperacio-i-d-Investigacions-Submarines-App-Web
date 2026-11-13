"""Serveis que el mòdul de pagaments ofereix a la resta de l'aplicació (M05a-8 i M05b-8)."""

from .checkout import PaymentStart, start_payment
from .processing import process_notification
from .providers import get_provider
from .providers.base import PaymentProvider

__all__ = ["PaymentStart", "process_notification", "provider", "start_payment"]


def provider() -> PaymentProvider:
    """`payments.provider()`: l'adaptador del proveïdor configurat."""
    return get_provider()
