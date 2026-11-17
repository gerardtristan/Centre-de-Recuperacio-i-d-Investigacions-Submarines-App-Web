"""Dades inventades de la tresoreria (T-M04-18: «es carreguen amb una ordre»). `seed_demo_data`
en una base buida deixa les pantalles de la tresoreria amb dades: moviments de més d'un
departament, dos extractes (CSV i Norma 43) amb línies proposades, conciliades i excloses, les
tres menes de liquidació i una remesa avisada i una en esborrany. Només dades inventades."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.core.imports import statement_lines
from apps.core.models import ImportBatch
from apps.payments.models import DirectDebitRemittance, SepaMandate
from apps.treasury.balances import balances
from apps.treasury.demo_data import iban
from apps.treasury.models import CashCount, Movement, ProviderSettlement, StatementLineState

pytestmark = pytest.mark.django_db
DEV = override_settings(SETTINGS_MODULE="config.settings.dev", DEBUG=True)


@pytest.fixture
def seeded(tmp_path):
    out = StringIO()
    with DEV:
        call_command("seed_demo_data", "--cluber-file", str(tmp_path / "c.csv"), stdout=out)
    return out.getvalue()


def test_t_m04_18_the_command_loads_the_treasury(seeded):
    assert "Tresoreria:" in seeded and "liquidacions" in seeded

    movements = Movement.objects.all()
    departments = set(movements.exclude(department=None).values_list("department__name", flat=True))
    assert {"General", "Activitats (prova)"} <= departments
    kinds = set(movements.values_list("kind", flat=True))
    assert {"income", "fee", "transfer", "cash_adjustment", "reversal"} <= kinds
    assert CashCount.objects.count() == 2

    batches = ImportBatch.objects.filter(kind=ImportBatch.Kind.BANK_STATEMENT)
    assert batches.count() == 3  # el tercer, l'abonament de la remesa dels pagaments (T-M05b-17)
    states = set(
        StatementLineState.objects.filter(statement_line__in=statement_lines()).values_list(
            "status", flat=True
        )
    )
    assert {"proposed", "reconciled", "excluded"} <= states

    assert set(ProviderSettlement.objects.values_list("status", flat=True)) == {
        "reconciled",
        "received",
        "to_review",
    }
    # La remesa avisada la liquiden les dades dels pagaments (T-M05b-17), que també bloquegen un
    # dels tres mandats amb un retorn «MD01».
    assert set(DirectDebitRemittance.objects.values_list("status", flat=True)) == {
        "settled",
        "draft",
    }
    assert SepaMandate.objects.filter(status=SepaMandate.Status.ACTIVE).count() == 2
    # Els saldos surten dels moviments i quadren: el trànsit liquidat no és negatiu, tampoc
    # «Remeses SEPA» amb els dos retorns de la remesa liquidada (P-286, opció C).
    last = movements.latest("value_date").value_date
    assert {a.name: a.balance_cents for a in balances(last) if a.balance_cents < 0} == {}


def test_invented_ibans_have_valid_check_digits():
    for n in (1, 2, 3, 999):
        value = iban(n)
        digits = "".join(str(int(c, 36)) for c in value[4:] + value[:4])
        assert int(digits) % 97 == 1 and value[4:8] == "0000"
