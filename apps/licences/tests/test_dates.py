"""Caducitat d'una llicència (T-M06-03; CA-M06-28 de la 058 i CA-M06-02)."""

import datetime

import pytest

from apps.licences.dates import expires_on
from apps.licences.models import ValidityRule

D = datetime.date


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (D(2026, 3, 15), D(2027, 3, 14)),
        (D(2027, 3, 15), D(2028, 3, 14)),
        (D(2027, 3, 1), D(2028, 2, 29)),
        (D(2028, 1, 1), D(2028, 12, 31)),
        (D(2028, 2, 29), D(2029, 2, 28)),
    ],
)
def test_365_days_ca_m06_28(start, end):
    assert expires_on(start, ValidityRule.DAYS_365) == end


def test_365_days_is_the_same_day_next_year_minus_one_for_every_day():
    # RN-M06-23 per a tots els dies de 2026 a 2029 (dos anys de traspàs pel mig).
    day = D(2026, 1, 1)
    while day < D(2030, 1, 1):
        end = expires_on(day, ValidityRule.DAYS_365)
        if (day.month, day.day) == (2, 29):
            assert end == D(day.year + 1, 2, 28)
        else:
            assert end + datetime.timedelta(days=1) == day.replace(year=day.year + 1)
        day += datetime.timedelta(days=1)


@pytest.mark.parametrize("start", [D(2027, 3, 15), D(2027, 1, 1), D(2027, 12, 31), D(2028, 2, 29)])
def test_calendar_year_ca_m06_02(start):
    assert expires_on(start, ValidityRule.CALENDAR_YEAR) == D(start.year, 12, 31)


def test_single_day_ends_the_same_day():
    assert expires_on(D(2027, 3, 15), ValidityRule.SINGLE_DAY) == D(2027, 3, 15)


def test_unknown_rule_is_rejected():
    with pytest.raises(ValueError, match="desconeguda"):
        expires_on(D(2027, 3, 15), "two_years")
