"""T-M09A-08: ingrés de l'ajut des de la sol·licitud (RN-M09A-09). Només dades inventades."""

from datetime import date

import pytest
from django.http import Http404

from apps.expenses.models import OtherIncome
from apps.expenses.services import ExpenseRejected
from apps.grants import income
from apps.grants.services import GrantError
from apps.grants.tests.test_resolution import grant, submitted  # noqa: F401 (fixture)
from apps.treasury.models import Movement, TreasuryAccount

pytestmark = pytest.mark.django_db


@pytest.fixture
def bank():
    return TreasuryAccount.objects.get(name="Banc principal")


def record(application, by, bank, amount=120000):
    return income.record_income(
        application, amount_cents=amount, account=bank, value_date=date(2027, 7, 1), by=by
    )


def test_bestreta_i_saldo_lligats_a_la_sollicitud_i_al_departament(
    submitted,  # noqa: F811
    treasurer,
    bank,
):
    granted = grant(submitted, treasurer)
    advance, balance = record(granted, treasurer, bank), record(granted, treasurer, bank)
    for row in (advance, balance):
        assert (row.kind, row.grant_application, row.department) == (
            "grant",
            granted,
            granted.department,
        )
        assert (row.payer, row.document_file) == ("Diputació Inventada", granted.resolution_file)
    assert Movement.objects.filter(kind=Movement.Kind.OTHER_INCOME).count() == 2
    assert list(granted.incomes.order_by("pk")) == [advance, balance]


def test_una_sollicitud_no_concedida_no_te_ingres(submitted, treasurer, bank):  # noqa: F811
    with pytest.raises(GrantError):
        record(submitted, treasurer, bank)
    assert not OtherIncome.objects.exists()


@pytest.mark.parametrize("role", ["board", "secretary", None])
def test_sense_aj6_no_es_registra(submitted, treasurer, bank, make_admin, role):  # noqa: F811
    granted = grant(submitted, treasurer)
    with pytest.raises(Http404):
        record(granted, make_admin(*([role] if role else [])), bank)


def test_nomes_un_ajut_es_lliga_a_una_sollicitud(submitted, treasurer, bank):  # noqa: F811
    from apps.core.models import Department
    from apps.expenses import income as expenses_income

    with pytest.raises(ExpenseRejected):
        expenses_income.record_other_income(
            kind="sponsorship",
            payer="Empresa Inventada",
            amount_cents=1000,
            account=bank,
            value_date=date(2027, 7, 1),
            department=Department.objects.get(name="General"),
            grant_application=submitted,
            by=treasurer,
        )
