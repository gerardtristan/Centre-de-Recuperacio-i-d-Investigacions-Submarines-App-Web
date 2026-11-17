# ruff: noqa: F811
"""Deposito (T-DX-12): a la transferència en espera, «Copia-ho tot» copia les tres dades d'un cop
(IBAN del club, import i referència), una per línia. Cap dada personal."""

import pytest

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments.tests.test_transfer import (  # noqa: F401 (fixtures)
    charge,
    configured,
    member,
    pay_by_transfer,
    screen,
)
from apps.treasury.tests.test_reconciliation import ref

pytestmark = pytest.mark.django_db


def test_copy_all_carries_the_three_values_one_per_line(charge, member):
    pay_by_transfer(member, charge)
    page = screen(member, charge)
    expected = f"IBAN: ES0000000000000000000000&#10;Import: 90,00&#10;Concepte: {ref(charge)}"
    assert f'data-copia="{expected}"' in page
    assert "Copia-ho tot" in page and 'data-copiat="Dades copiades"' in page
