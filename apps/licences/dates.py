"""Caducitat d'una llicència (RN-M06-02; per als 365 dies, RN-M06-23 de l'addenda de la 058).
Funció pura: cap consulta ni cap ajust."""

import datetime

from .models import ValidityRule


def expires_on(starts_on: datetime.date, validity_rule: str) -> datetime.date:
    if validity_rule == ValidityRule.CALENDAR_YEAR:
        return datetime.date(starts_on.year, 12, 31)
    if validity_rule == ValidityRule.DAYS_365:
        try:
            return starts_on.replace(year=starts_on.year + 1) - datetime.timedelta(days=1)
        except ValueError:  # Comença el 29/02: caduca el 28/02 de l'any següent.
            return datetime.date(starts_on.year + 1, 2, 28)
    if validity_rule == ValidityRule.SINGLE_DAY:
        return starts_on
    raise ValueError(f"Regla de validesa desconeguda: «{validity_rule}».")
