"""T-M09-08: altres ingressos (ajut, patrocini, donatiu) amb el moviment de la 04. Només dades
inventades."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core.models import AuditEntry, Department
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import income
from apps.expenses.models import OtherIncome
from apps.expenses.services import ExpenseRejected
from apps.expenses.tests.test_expenses import invoice
from apps.margins.models import Period
from apps.treasury.models import Movement, TreasuryAccount
from apps.treasury.services import PeriodClosed

pytestmark = pytest.mark.django_db
DAY = date(2026, 10, 15)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def grant(by, **extra):
    fields = {
        "kind": OtherIncome.Kind.GRANT,
        "payer": "Ajuntament Inventat",
        "amount_cents": 300000,
        "account": TreasuryAccount.objects.get(name="Banc principal"),
        "value_date": DAY,
        "department": Department.objects.get(name="General"),
        "document_file": invoice(by.person),
        "by": by,
    }
    return income.record_other_income(**{**fields, **extra})


def test_un_ajut_amb_resolucio_crea_l_ingres_i_el_moviment_de_la_04(treasurer):
    record = grant(treasurer)
    movement = Movement.objects.get(kind=Movement.Kind.OTHER_INCOME)
    assert record.movement == movement
    assert (movement.direction, movement.amount_cents, movement.value_date) == ("in", 300000, DAY)
    assert movement.department == record.department
    assert movement.concept == "Ajut (General)"  # sense el pagador
    entry = AuditEntry.objects.get(action=income.OTHER_INCOME_RECORDED)
    assert entry.details == {"kind": "grant", "amount_cents": 300000, "movement": movement.pk}
    assert str(record) == "Ajut (300000 c)"


def test_un_patrocini_no_necessita_document(treasurer):
    record = grant(treasurer, kind=OtherIncome.Kind.SPONSORSHIP, document_file=None)
    assert record.document_file is None


@pytest.mark.parametrize(
    "extra",
    [
        {"document_file": None},  # un ajut sense resolució
        {"kind": "loan"},
        {"payer": "  "},
        {"payer": "x" * 141},
    ],
)
def test_dades_que_no_valen(treasurer, extra):
    with pytest.raises(ExpenseRejected):
        grant(treasurer, **extra)
    assert not Movement.objects.exists()


def test_l_import_el_comprova_la_04(treasurer):
    with pytest.raises(ValidationError):
        grant(treasurer, amount_cents=0)
    assert not OtherIncome.objects.exists()


def test_dins_un_periode_tancat_es_rebutja_i_no_desa_res(treasurer):
    Period.objects.create(starts_on=date(2026, 10, 1), ends_on=date(2026, 10, 31), status="closed")
    with pytest.raises(PeriodClosed):
        grant(treasurer)
    assert not OtherIncome.objects.exists()


@pytest.mark.parametrize("role", ["president", "secretary", "board", None])
def test_sense_mg4_no_es_registra(make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        grant(make_admin(*([role] if role else [])))


def test_l_administrador_te_mg4(make_admin):  # noqa: F811
    assert grant(make_admin("administrator")).kind == "grant"


def test_la_base_de_dades_rebutja_un_ajut_sense_document(treasurer):
    record = grant(treasurer)
    with pytest.raises(IntegrityError), transaction.atomic():
        OtherIncome.objects.filter(pk=record.pk).update(document_file=None)
