"""Saldos amb volum (T-M04-04; RNF-T7: el saldo d'un compte en menys d'un segon amb 50.000
moviments; CA-T02.1). CA-T02.2 (trànsit liquidat) és a `test_settlements.py`. Només dades
inventades, creades d'un cop a la base de dades perquè la prova no alenteixi la suite."""

import time
from datetime import date, timedelta

import pytest
from django.db import connection

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury.balances import balance, balances
from apps.treasury.models import CostCentre, Movement, TreasuryAccount
from apps.treasury.tests.test_views import ACCOUNTS, client_for

pytestmark = pytest.mark.django_db
VOLUME = 50_000
START = date(2026, 1, 1)
ON = date(2026, 12, 31)
LIMIT_SECONDS = 1.0  # RNF-T7


def fill(cash, bank):
    """50.000 ajustos d'arqueig inventats, repartits entre la caixa i el banc, amb entrades i
    sortides i dates de valor fins a febrer de 2027 (n'hi ha després de `ON`)."""
    centre = CostCentre.objects.get(name="Ajustos de caixa")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO treasury_movement (
                account_id, direction, amount_cents, value_date, recorded_at, kind, concept,
                department_id, cost_centre_id, reason
            )
            SELECT
                CASE WHEN mod(i, 2) = 0 THEN %(cash)s ELSE %(bank)s END,
                CASE WHEN mod(i, 3) = 0 THEN 'out' ELSE 'in' END,
                mod(i, 997) + 1,
                %(start)s::date + mod(i, 400),
                now(), 'cash_adjustment', 'Prova de volum', %(department)s, %(centre)s,
                'Dades inventades'
            FROM generate_series(1, %(volume)s) AS i
            """,
            {
                "cash": cash.pk,
                "bank": bank.pk,
                "start": START,
                "department": centre.department_id,
                "centre": centre.pk,
                "volume": VOLUME,
            },
        )


def expected(account_is_cash: bool, on: date) -> int:
    """El mateix repartiment, sumat a Python."""
    total = 0
    for i in range(1, VOLUME + 1):
        if (i % 2 == 0) != account_is_cash or START + timedelta(days=i % 400) > on:
            continue
        amount = i % 997 + 1
        total += -amount if i % 3 == 0 else amount
    return total


def timed(call):
    started = time.perf_counter()
    result = call()
    return result, time.perf_counter() - started


def test_rnf_t7_balances_of_50_000_movements_in_under_a_second(make_admin):  # noqa: F811
    # Una sola prova: omplir la taula és el que costa (uns 2 s), i es fa una vegada.
    cash = TreasuryAccount.objects.get(name="Caixa")
    bank = TreasuryAccount.objects.get(name="Banc principal")
    fill(cash, bank)
    assert Movement.objects.count() == VOLUME

    found, seconds = timed(lambda: balance(cash, ON))
    assert found == expected(True, ON)
    assert seconds < LIMIT_SECONDS
    assert balance(bank, ON) == expected(False, ON)

    rows, seconds = timed(lambda: {a.pk: a.balance_cents for a in balances(ON)})
    assert (rows[cash.pk], rows[bank.pk]) == (expected(True, ON), expected(False, ON))
    assert seconds < LIMIT_SECONDS

    client = client_for(make_admin("treasurer"))
    response, seconds = timed(lambda: client.get(ACCOUNTS, {"on": ON.isoformat()}))
    assert response.status_code == 200
    assert seconds < LIMIT_SECONDS

    # CA-T02.1: la data de valor decideix (n'hi ha després de `ON`).
    end = date(2027, 12, 31)
    assert balance(cash, START - timedelta(days=1)) == 0
    assert balance(cash, end) == expected(True, end) != found
