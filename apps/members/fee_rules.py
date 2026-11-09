"""Edat i quota d'una alta (068 i 070; RN-M01-62 a RN-M01-65 i RN-M01-67 a RN-M01-69), sense
tocar dades.

Funcions pures amb la data local de Barcelona:
- qui és menor i quins tipus pot triar (18 i 14 anys complerts el dia de la sol·licitud);
- el primer any de quota d'un menor (any de naixement + 15) i l'exempció per edat (068);
- la quota és **íntegra**: l'import anual del tipus, sense prorrata ni regla per mesos (070).
  Es renova 12 mesos després del pagament confirmat; això, i el pagament en tres quotes, són de
  la T-M01-18 i la T-M01-19, no d'aquí.

És una previsió per mostrar al formulari: no crea cap quota ni calcula cap renovació.
"""

from dataclasses import dataclass
from datetime import date

from django.utils import timezone

from apps.core.persons import age_on

ADULT_AGE = 18
FULL_TYPE_MIN_AGE = 14  # des dels 14 anys complerts, simpatitzant o ple dret (RN-M01-64)
FEE_START_OFFSET = 15  # primer any de quota = any de naixement + 15 (RN-M01-65)
MAX_AGE = 120  # data de naixement versemblant
SUPPORTER = "supporter"


def local_today(now=None) -> date:
    """Data local de Barcelona (TIME_ZONE): el 31/12 a les 23:30 UTC ja és l'1 de gener."""
    return timezone.localdate(now)


def first_fee_year(birth_date: date) -> int:
    return birth_date.year + FEE_START_OFFSET


def is_minor(age: int) -> bool:
    return age < ADULT_AGE


def may_choose(type_code: str, age: int) -> bool:
    """Per sota dels 14 anys, només simpatitzant (RN-M01-64)."""
    return age >= FULL_TYPE_MIN_AGE or type_code == SUPPORTER


@dataclass(frozen=True)
class FeePreview:
    """Què es mostra d'un tipus en una alta. `kind`:
    - "exempt": sense quota fins al 31/12 de `until_year` (068);
    - "full": quota anual íntegra del tipus (`cents`), que es confirma en aprovar l'alta (070)."""

    kind: str
    cents: int | None = None
    until_year: int | None = None


def fee_preview(birth_date: date, annual_fee_cents: int, on: date) -> FeePreview:
    start = first_fee_year(birth_date)
    if on.year < start:  # l'exempció per edat té prioritat (068)
        return FeePreview("exempt", until_year=start - 1)
    return FeePreview("full", cents=annual_fee_cents)


def age_today(birth_date: date, on: date | None = None) -> int:
    return age_on(birth_date, on or local_today())
