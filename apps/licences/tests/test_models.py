"""Model de llicència: restriccions de M06-6 i estats derivats de M06-5 (T-M06-03)."""

import datetime

import pytest
from django.db import IntegrityError, transaction

from apps.licences.models import Licence, LicencePrice, ValidityRule

D = datetime.date
S = Licence.Status
SHOWN = Licence.Display
EXTERNAL = {"origin": "external", "price_kind": None, "price_cents": None}


def rejected(make_licence, **fields):
    with pytest.raises(IntegrityError), transaction.atomic():
        make_licence(**fields)


@pytest.mark.parametrize("status", ["requested", "paid", "filed"])
def test_one_annual_licence_in_progress_per_type(make_licence, status):
    make_licence(status=status)
    rejected(make_licence, status="paid")


def test_a_finished_one_does_not_block_a_new_one(make_licence):
    make_licence(status=S.CANCELLED, cancellation_reason="Duplicada")
    make_licence(status=S.ACTIVE)
    assert make_licence(status=S.REQUESTED)


def test_single_day_licences_are_unique_per_date(make_licence):
    # RN-M06-19 (CA-M06-22, la part del model).
    day = {"validity_rule": ValidityRule.SINGLE_DAY}
    make_licence(starts_on=D(2027, 5, 10), expires_on=D(2027, 5, 10), **day)
    assert make_licence(starts_on=D(2027, 5, 17), expires_on=D(2027, 5, 17), **day)
    rejected(make_licence, starts_on=D(2027, 5, 10), expires_on=D(2027, 5, 10), **day)


@pytest.mark.parametrize(
    "fields",
    [
        {"expires_on": D(2027, 3, 14)},  # abans de l'inici
        {"status": "lapsed"},  # només les d'un dia
        {"status": "cancelled", "cancellation_reason": "  "},  # sense motiu
        {"status": "unknown"},
        {"origin": "elsewhere"},
        {"validity_rule": "two_years"},
        {"price_kind": None},  # del club sense preu
        {"price_cents": None},
        {**EXTERNAL, "price_cents": 9000},  # externa amb preu
        {"m01_record_ref": 7},  # només les importades del 01
    ],
)
def test_constraints_reject(make_licence, fields):
    rejected(make_licence, **fields)


def test_external_and_imported_have_no_price(make_licence):
    assert make_licence(status=S.ACTIVE, **EXTERNAL)
    assert make_licence(status=S.ACTIVE, **{**EXTERNAL, "origin": "imported_m01"}, m01_record_ref=7)


def test_a_lapsed_single_day_licence_is_allowed(make_licence):
    day = {"validity_rule": ValidityRule.SINGLE_DAY, "expires_on": D(2027, 3, 15)}
    assert make_licence(status=S.LAPSED, **day)


def test_str(make_licence, annual):
    assert str(annual) == "Aficionat anual (inventat)"
    assert str(make_licence()) == "Aficionat anual (inventat) (15/03/2027–31/12/2027)"


def test_licences_are_not_deleted(make_licence):
    licence = make_licence()
    with pytest.raises(Exception, match="no s'esborren"):
        licence.delete()


@pytest.mark.parametrize(
    ("today", "shown"),
    [
        (D(2027, 3, 14), SHOWN.NOT_STARTED),  # P-440
        (D(2027, 3, 15), SHOWN.VALID),
        (D(2027, 10, 31), SHOWN.VALID),  # 61 dies
        (D(2027, 11, 1), SHOWN.TO_RENEW),  # 60 dies
        (D(2027, 11, 2), SHOWN.TO_RENEW),  # l'exemple de M06-7
        (D(2027, 12, 31), SHOWN.TO_RENEW),
        (D(2028, 1, 1), SHOWN.EXPIRED),
    ],
)
def test_derived_status_of_an_active_licence(make_licence, today, shown):
    licence = make_licence(status=S.ACTIVE)
    assert licence.display_status(today, to_renew_days=60) == shown


def test_the_renewal_window_is_the_setting_passed_in(make_licence):
    licence = make_licence(status=S.ACTIVE)
    assert licence.display_status(D(2027, 11, 2), to_renew_days=58) == SHOWN.VALID  # 59 dies


def test_a_single_day_licence_is_never_to_renew(make_licence):
    licence = make_licence(
        status=S.ACTIVE, validity_rule=ValidityRule.SINGLE_DAY, expires_on=D(2027, 3, 15)
    )
    assert licence.display_status(D(2027, 3, 15), to_renew_days=60) == SHOWN.VALID
    assert licence.display_status(D(2027, 3, 16), to_renew_days=60) == SHOWN.EXPIRED


@pytest.mark.parametrize("status", ["requested", "paid", "filed", "cancelled"])
def test_other_statuses_are_shown_as_stored(make_licence, status):
    licence = make_licence(status=status, cancellation_reason="Motiu")
    assert licence.display_status(D(2028, 6, 1), to_renew_days=60) == status


def test_member_price_is_the_federation_price(annual, admin_account):
    # RN-M06-05 i RN-M06-06 (CA-M06-03, la part del model).
    price = LicencePrice.objects.create(
        licence_type=annual,
        federation_cost_cents=9000,
        non_member_surcharge_cents=2500,
        valid_from=D(2027, 1, 1),
        note="Tarifa inventada",
        created_by=admin_account,
    )
    assert price.amount_cents(LicencePrice.Kind.MEMBER) == 9000
    assert price.amount_cents(LicencePrice.Kind.NON_MEMBER) == 11500
    with pytest.raises(ValueError, match="desconegut"):
        price.amount_cents("vip")


@pytest.mark.parametrize("note", ["", "   "])
def test_a_price_without_a_note_is_rejected_by_the_database(annual, admin_account, note):
    with pytest.raises(IntegrityError), transaction.atomic():
        LicencePrice.objects.create(
            licence_type=annual,
            federation_cost_cents=9000,
            non_member_surcharge_cents=0,
            valid_from=D(2027, 1, 1),
            note=note,
            created_by=admin_account,
        )
