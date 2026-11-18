"""Antiguitat del soci (T-DX-60): mai «0 anys»; plural correcte; data aproximada amb «~»."""

from datetime import date
from types import SimpleNamespace

import pytest

from apps.members.templatetags.antiguitat import antiguitat

TODAY = date(2026, 11, 18)


def member(joined, approximate=False):
    return SimpleNamespace(joined_on=joined, joined_on_is_approximate=approximate)


@pytest.mark.parametrize(
    ("joined", "text"),
    [
        (date(2026, 3, 1), "Soci des de 2026"),
        (date(2025, 11, 19), "Soci des de 2025"),  # encara no fa un any sencer
        (date(2025, 11, 18), "Soci des de 2025 (1 any)"),
        (date(2024, 5, 2), "Soci des de 2024 (2 anys)"),
    ],
)
def test_years_only_from_one_full_year(joined, text):
    assert antiguitat(member(joined), TODAY) == text


def test_an_approximate_date_keeps_the_tilde_and_no_years():
    assert antiguitat(member(date(1987, 1, 1), approximate=True), TODAY) == "Soci des de ~1987"


def test_without_a_join_date_nothing():
    assert antiguitat(member(None), TODAY) == ""
