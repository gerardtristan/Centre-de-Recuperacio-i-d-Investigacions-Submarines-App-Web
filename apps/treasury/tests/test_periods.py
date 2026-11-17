"""Despeses, altres ingressos i període tancat (T-M04-20; addendes de la 050 i la 053; CA-T18 a
CA-T25; RN-T26 a RN-T33). Només dades inventades."""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, transaction
from django.utils import timezone

from apps.core import imports
from apps.core.models import AppendOnlyError, AuditEntry, Department, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import services, settlements
from apps.treasury.models import CostCentre, Movement, StatementLineState, TreasuryAccount
from apps.treasury.tests.test_record_income import SYSTEM, new_transit, paid, record
from apps.treasury.tests.test_settlements import ON, collected, record_it

pytestmark = pytest.mark.django_db
K = Movement.Kind
MID_OCTOBER, END_OCTOBER, FIRST_NOVEMBER = date(2026, 10, 15), date(2026, 10, 31), date(2026, 11, 1)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


@pytest.fixture
def close(monkeypatch):
    """Registra un bloqueig de període tancat fins a `until`, com ho farà el 09."""

    def close(until):
        monkeypatch.setattr(services, "_GUARDS", [])
        services.register_movement_guard(lambda: until)

    return close


@pytest.fixture
def bank():
    return TreasuryAccount.objects.get(name="Banc principal")


@pytest.fixture
def general():
    return Department.objects.get(name="General")


def expense(bank, general, by, day=MID_OCTOBER, **extra):
    fields = {"value_date": day, "department": general, "concept": "Factura de prova", "by": by}
    return services.record_expense(bank, 4200, **{**fields, **extra})


def test_ca_t21_i_ca_t25_sense_bloqueig_res_no_canvia(bank, general, treasurer):
    movement = expense(bank, general, treasurer)
    assert (movement.kind, movement.direction, movement.value_date) == (
        K.EXPENSE,
        "out",
        MID_OCTOBER,
    )
    assert movement.original_value_date is None
    income = record(paid(Person.objects.create(first_name="Pere", origin="web")))
    assert income.original_value_date is None
    entry = AuditEntry.objects.get(action=services.EXPENSE_RECORDED)
    assert entry.actor_account == treasurer


def test_altres_ingressos_amb_departament_i_centre_de_cost(bank, general, treasurer):
    centre = CostCentre.selectable().filter(department=general).first()
    fields = {"department": general, "cost_centre": centre, "concept": "Ajut de prova"}
    movement = services.record_other_income(
        bank, 50000, value_date=MID_OCTOBER, by=treasurer, **fields
    )
    assert (movement.kind, movement.direction, movement.cost_centre) == (
        K.OTHER_INCOME,
        "in",
        centre,
    )


def test_un_centre_d_un_altre_departament_o_un_departament_inactiu_es_rebutgen(
    bank, general, treasurer
):
    other = CostCentre.objects.create(
        department=Department.objects.create(name="Departament de prova"), name="Centre de prova"
    )
    with pytest.raises(services.InvalidDepartment):
        expense(bank, general, treasurer, cost_centre=other)
    Department.objects.filter(pk=general.pk).update(active=False)
    general.refresh_from_db()
    with pytest.raises(services.InvalidDepartment):
        expense(bank, general, treasurer)
    assert not Movement.objects.filter(kind=K.EXPENSE).exists()


def test_ca_t18_una_despesa_no_es_modifica_ni_s_esborra(bank, general, treasurer):
    movement = expense(bank, general, treasurer)
    with pytest.raises(AppendOnlyError):
        Movement.objects.filter(pk=movement.pk).update(amount_cents=1)
    with pytest.raises(AppendOnlyError):
        movement.delete()
    with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("UPDATE treasury_movement SET amount_cents = 1 WHERE id = %s", [movement.pk])
    assert Movement.objects.get(pk=movement.pk).amount_cents == 4200


def test_ca_t19_l_anullacio_manual_dins_el_periode_tancat_es_rebutja(
    bank, general, treasurer, close
):
    movement = expense(bank, general, treasurer)
    close(END_OCTOBER)

    with pytest.raises(services.PeriodClosed):
        services.reverse(movement, reason="Factura duplicada", by=treasurer, value_date=END_OCTOBER)
    reversal = services.reverse(
        movement, reason="Factura duplicada", by=treasurer, value_date=FIRST_NOVEMBER
    )

    assert (reversal.value_date, reversal.original_value_date) == (FIRST_NOVEMBER, None)
    original = Movement.objects.get(pk=movement.pk)
    assert (original.value_date, original.is_reversed) == (MID_OCTOBER, True)


def test_ca_t20_l_anullacio_demana_motiu_i_el_registre_el_guarda(bank, general, treasurer):
    movement = expense(bank, general, treasurer)
    with pytest.raises(ValidationError):
        services.reverse(movement, reason="  ", by=treasurer)
    services.reverse(movement, reason="Factura duplicada", by=treasurer)
    entry = AuditEntry.objects.get(action=services.MOVEMENT_REVERSED)
    assert (entry.reason, entry.actor_account) == ("Factura duplicada", treasurer)


def test_ca_t22_un_pagament_confirmat_dins_el_tancat_entra_al_periode_obert(close):
    close(date(2026, 11, 14))
    payment = paid(Person.objects.create(first_name="Pere", origin="web"))  # pagat el 13/11

    income = record(payment)

    assert (income.value_date, income.original_value_date) == (
        date(2026, 11, 15),
        date(2026, 11, 13),
    )
    entry = AuditEntry.objects.get(action=services.MOVED_TO_OPEN_PERIOD)
    assert entry.details["original_value_date"] == "2026-11-13"


def test_ca_t23_comissio_retorn_i_liquidacio_no_es_rebutgen_i_la_despesa_si(
    bank, general, treasurer, close
):
    new_transit()
    person = Person.objects.create(first_name="Pere", origin="web")
    card = record(paid(person))
    collected(person, 9000, "REF-A")
    collected(person, 3500, "REF-B")
    settlement = record_it()
    until = max(ON, timezone.localdate())
    close(until)

    fee = services.record_fee(card.payment, 120, by=SYSTEM)
    returned = services.record_return(paid_and_recorded(person), by=SYSTEM)
    settlements.confirm(settlement, by=treasurer)

    legs = Movement.objects.filter(kind=K.TRANSFER, settlement=settlement)
    for movement in (fee, returned, *legs):
        assert movement.value_date == until + timedelta(days=1)
        assert movement.original_value_date is not None
    with pytest.raises(services.PeriodClosed):
        expense(bank, general, treasurer, day=until)


def paid_and_recorded(person):
    return record(paid(person, amount=3500)).payment


def test_ca_t24_la_liquidacio_entrada_al_periode_obert_es_casa_amb_la_linia_del_dia(
    treasurer, close
):
    new_transit()
    person = Person.objects.create(first_name="Pere", origin="web")
    collected(person, 9000, "REF-A")
    collected(person, 3500, "REF-B")
    settlement = record_it()  # abonament del 20/11, net 12.380
    close(ON)
    batch = imports.open_confirmed("bank_statement", file_sha256="2" * 64, by=treasurer,
                                   counts={"new_count": 1})  # fmt: skip
    imports.add_lines(batch, [{"row": 2, "result": "new", "value_date": ON, "amount_cents": 12380,
                               "concept": "ABONO LIQUIDACIO", "balance_cents": None}])  # fmt: skip
    line = imports.statement_lines(batch).get()

    settlements.confirm(settlement, by=treasurer, statement_line=line)

    legs = Movement.objects.filter(kind=K.TRANSFER, settlement=settlement)
    assert {leg.original_value_date for leg in legs} == {ON}
    assert StatementLineState.objects.get(statement_line=line).status == "reconciled"
