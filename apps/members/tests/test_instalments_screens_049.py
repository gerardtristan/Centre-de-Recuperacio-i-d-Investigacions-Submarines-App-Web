"""Pantalles del pagament a terminis (T-M01-49; 097, P-61): l'opció a la quota del soci, només
amb l'ajust encès i sobre una quota pròpia, i el candidat a «impagat» a «Quotes i impagats».
Només dades inventades."""

from datetime import date

import pytest
from django.urls import reverse

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import services
from apps.members.models import Member
from apps.members.tests.test_cards import make_member, pay, personal  # noqa: F401, F811
from apps.members.tests.test_instalments_049 import (  # noqa: F401 (fixture «on»)
    annual,
    at_noon,
    choose,
    on,
    plan_of,
)
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

S = Member.Status


def test_off_the_fee_page_shows_nothing_and_the_post_changes_nothing(personal):  # noqa: F811
    member = make_member(status=S.PENDING)
    fee = annual(member)
    client = personal(member)
    assert "terminis" not in client.get(reverse("members:fee_detail", args=[fee.pk])).text
    client.post(reverse("members:fee_instalments", args=[fee.pk]))
    assert not plan_of(member)


def test_the_fees_screen_shows_the_candidate(on, make_admin):  # noqa: F811
    member = make_member(status=S.PENDING)
    _fee, (first, _second, _third) = choose(member, date(2026, 1, 31))
    pay(first, at_noon(date(2026, 1, 25)))
    services.on_fee_paid(first.pk)
    response = admin_client(make_admin("treasurer")).get(reverse("administration:fees"))
    assert "Candidat a impagat" in response.text


def test_on_the_member_sees_the_plan_and_chooses_it(on, personal):  # noqa: F811
    member = make_member(status=S.PENDING)
    fee = annual(member)
    client = personal(member)
    page = client.get(reverse("members:fee_detail", args=[fee.pk])).text
    assert "Paga en tres terminis" in page and "32,00" in page and "28/02/2027" in page
    response = client.post(reverse("members:fee_instalments", args=[fee.pk]))
    first = plan_of(member)[0]
    assert response.status_code == 302
    assert response["Location"] == reverse("members:fee_detail", args=[first.pk])
    again = client.post(reverse("members:fee_instalments", args=[fee.pk]), follow=True)
    assert "ja no es pot pagar a terminis" in again.text and len(plan_of(member)) == 3


def test_on_another_members_fee_is_not_found_on_screen(on, personal):  # noqa: F811
    member, other = make_member(), make_member("Berta", 1288, document="00000001R")
    fee = annual(other)
    client = personal(member)
    assert client.post(reverse("members:fee_instalments", args=[fee.pk])).status_code == 404
    assert not plan_of(other)
