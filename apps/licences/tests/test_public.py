"""Pàgina pública de llicències per a no socis (T-M06-07; P-M06-C, passos 1 i 2; RN-M06-01, 03 i
07; CA-M06-06). Només dades inventades."""

import datetime

import pytest
from django.urls import reverse

from apps.core import business_settings
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import prices
from apps.licences.models import LicencePrice, LicenceType, ValidityRule
from apps.members.models import MembershipType
from apps.members.services import membership_fees

D = datetime.date
URL = reverse("licences:public")


@pytest.fixture
def options(monkeypatch):
    values = {"licences.non_members_enabled": True, "licences.day_enabled": False}
    real_get = business_settings.get
    monkeypatch.setattr(
        business_settings, "get", lambda key, at=None: values.get(key, real_get(key, at))
    )
    return values


@pytest.fixture
def priced(annual, make_admin):  # noqa: F811
    author = make_admin()
    day = LicenceType.objects.create(name="Un dia (inventat)", category="other",
                                     validity_rule=ValidityRule.SINGLE_DAY)  # fmt: skip
    without_price = LicenceType.objects.create(
        name="Sense preu (inventat)", category="other", validity_rule=ValidityRule.CALENDAR_YEAR
    )
    for licence_type, cost in ((annual, 9000), (day, 1500)):
        LicencePrice.objects.create(
            licence_type=licence_type, federation_cost_cents=cost,
            non_member_surcharge_cents=2000, valid_from=D(2020, 1, 1), note="Preu inventat",
            created_by=author,
        )  # fmt: skip
    return annual, day, without_price


def test_ca_m06_06_disabled_it_is_not_found(client, db):
    assert business_settings.get("licences.non_members_enabled") is False  # desactivada d'entrada
    assert client.get(URL).status_code == 404


def test_ca_m06_06_enabled_a_visitor_sees_the_price_comparison(client, options, priced):
    html = client.get(URL).content.decode()
    assert "Aficionat anual (inventat)" in html
    assert "110,00 €" in html and "90,00 €" in html and "20,00 €" in html  # RN-M06-07
    assert "Un dia (inventat)" not in html and "Sense preu (inventat)" not in html
    assert reverse("members:join") in html


def test_the_comparison_shows_day_licences_only_when_enabled(options, priced):
    assert [row.name for row in prices.comparison(D(2027, 3, 15))] == ["Aficionat anual (inventat)"]
    options["licences.day_enabled"] = True
    rows = prices.comparison(D(2027, 3, 15))
    assert [(r.name, r.member_cents, r.non_member_cents, r.saving_cents) for r in rows] == [
        ("Aficionat anual (inventat)", 9000, 11000, 2000),
        ("Un dia (inventat)", 1500, 3500, 2000),
    ]


def test_inactive_types_and_types_without_a_price_today_are_left_out(options, priced):
    annual, _, _ = priced
    LicenceType.objects.filter(pk=annual.pk).update(active=False)
    assert prices.comparison(D(2027, 3, 15)) == []
    assert prices.comparison(D(2019, 12, 31)) == []


def test_membership_fees_only_active_types_cheapest_first(db):
    MembershipType.objects.create(code="old", name="Antic (inventat)", annual_fee_cents=100,
                                  active=False)  # fmt: skip
    fees = membership_fees(D(2027, 3, 15))
    assert fees == sorted(fees, key=lambda fee: fee[1])
    assert "Antic (inventat)" not in dict(fees)
    assert all(cents > 0 for _, cents in fees)


def test_logged_in_accounts_also_see_it(client, options, priced, personal_account, login_as):
    assert login_as(personal_account, "personal").get(URL).status_code == 200
