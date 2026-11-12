"""Normalització de les dades que es comparen per detectar duplicats (V-03)."""

import re


def normalize_document(value: str) -> str:
    """Sense espais, guions ni punts, i en majúscules: «0000 0000-t» → «00000000T»."""
    return re.sub(r"[\s.\-]", "", value or "").upper()


def normalize_phone(value: str) -> str:
    """Només xifres i el «+» inicial: «+34 600-00.00.00» → «+34600000000»."""
    value = (value or "").strip()
    digits = re.sub(r"\D", "", value)
    return f"+{digits}" if value.startswith("+") else digits


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()
