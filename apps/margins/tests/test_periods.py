"""T-M09-02: la guarda de període tancat del 09 registrada a la 04 (CA-T19, CA-T22, CA-M09-22 i
CA-M09-25). Només dades inventades."""

from datetime import date, timedelta

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.models import Department, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.margins import periods
from apps.margins.models import Period
from apps.treasury import services
from apps.treasury.models import Movement, TreasuryAccount
from apps.treasury.tests.test_record_income import SYSTEM, paid, record

pytestmark = pytest.mark.django_db
OCTOBER = (date(2026, 10, 1), date(2026, 10, 31))
NOVEMBER = (date(2026, 11, 1), date(2026, 11, 30))
MID_OCTOBER, END_OCTOBER, FIRST_NOVEMBER = date(2026, 10, 15), date(2026, 10, 31), date(2026, 11, 1)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def period(span, status="open"):
    return Period.objects.create(starts_on=span[0], ends_on=span[1], status=status)


def close(p):
    Period.objects.filter(pk=p.pk).update(status=Period.Status.CLOSED)


def expense(by, day, concept="Factura de l'embarcació"):
    return services.record_expense(
        TreasuryAccount.objects.get(name="Banc principal"),
        25000,
        value_date=day,
        department=Department.objects.get(name="General"),
        concept=concept,
        by=by,
    )


def test_la_guarda_del_09_es_registrada_a_la_04():
    assert periods.closed_until in services._GUARDS


def test_sense_cap_periode_tancat_no_hi_ha_bloqueig():
    period(OCTOBER)
    assert periods.closed_until() is None
    assert services.closed_until() is None
    assert periods.is_period_closed(MID_OCTOBER) is False


def test_tancat_fins_a_l_ultim_dia_del_darrer_periode_tancat():
    assert str(period(OCTOBER, "closed")) == "2026-10-01 – 2026-10-31"
    period(NOVEMBER)
    assert services.closed_until() == END_OCTOBER
    assert periods.is_period_closed(END_OCTOBER) is True
    assert periods.is_period_closed(FIRST_NOVEMBER) is False


def test_p_471_un_periode_anterior_reobert_continua_bloquejat_si_n_hi_ha_un_de_posterior_tancat():
    period(OCTOBER)
    period(NOVEMBER, "closed")
    assert periods.is_period_closed(MID_OCTOBER) is True


def test_ca_t19_i_ca_m09_22_l_anullacio_i_la_despesa_nova_van_al_periode_obert(treasurer):
    october = period(OCTOBER)
    original = expense(treasurer, MID_OCTOBER)
    close(october)
    period(NOVEMBER)

    with pytest.raises(services.PeriodClosed):
        services.reverse(original, reason="Import equivocat", by=treasurer, value_date=END_OCTOBER)
    with pytest.raises(services.PeriodClosed):
        expense(treasurer, END_OCTOBER, concept="Factura corregida")

    reversal = services.reverse(
        original, reason="Import equivocat", by=treasurer, value_date=FIRST_NOVEMBER
    )
    corrected = expense(treasurer, FIRST_NOVEMBER, concept="Factura corregida")

    assert (reversal.value_date, corrected.value_date) == (FIRST_NOVEMBER, FIRST_NOVEMBER)
    unchanged = Movement.objects.get(pk=original.pk)
    assert (unchanged.value_date, unchanged.amount_cents, unchanged.is_reversed) == (
        MID_OCTOBER,
        25000,
        True,
    )


def test_ca_t22_un_pagament_confirmat_dins_el_tancat_entra_al_periode_obert():
    # `paid` el marca pagat el 13/11/2026 (dades de la 04).
    period((date(2026, 11, 1), date(2026, 11, 14)), "closed")
    income = record(paid(Person.objects.create(first_name="Pere", origin="web")))
    assert (income.value_date, income.original_value_date) == (
        date(2026, 11, 15),
        date(2026, 11, 13),
    )


def test_ca_m09_25_una_comissio_del_banc_dins_el_tancat_no_es_rebutja():
    card = record(paid(Person.objects.create(first_name="Pere", origin="web")))
    today = timezone.localdate()
    period((date(2026, 11, 1), today), "closed")
    fee = services.record_fee(card.payment, 120, by=SYSTEM)
    assert fee.value_date == today + timedelta(days=1)
    assert fee.original_value_date is not None


def test_cap_dia_dins_de_dos_periodes():
    period(OCTOBER)
    with pytest.raises(IntegrityError), transaction.atomic():
        period((END_OCTOBER, date(2026, 11, 30)))
    period(NOVEMBER)  # l'endemà, sense forat ni solapament


@pytest.mark.parametrize(
    "fields",
    [
        {"starts_on": date(2026, 10, 31), "ends_on": date(2026, 10, 1)},
        {"starts_on": date(2026, 10, 1), "ends_on": date(2026, 10, 31), "status": "frozen"},
    ],
)
def test_dates_en_ordre_i_estat_valid(fields):
    with pytest.raises(IntegrityError), transaction.atomic():
        Period.objects.create(**fields)
