"""Oleaje (T-DX-17): la portada de l'àrea de socis mostra l'estat de la quota, els dies que queden i
l'accés al carnet, només del soci de la sessió i només al compte personal."""

from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core.models import Person
from apps.members.models import Member, MembershipType
from apps.members.tests.test_cards import account_for, add_fee, make_member, paid_member
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
HOME = "core:home"


def summary(html):
    return (
        html.split('class="oleaje-seccio"', 1)[1].split("</section>", 1)[0]
        if "oleaje-seccio" in html
        else None
    )


def test_a_paid_member_sees_the_fee_the_days_left_and_the_card(login_as):
    html = login_as(account_for(paid_member()), AREA_PERSONAL).get(reverse(HOME)).content.decode()
    assert "oleaje-portada" in html
    block = summary(html)
    assert "Pagada fins al" in block and "vigencia" in block
    assert reverse("members:card") in block and reverse("members:fees") in block


def test_a_pending_fee_shows_pending_and_no_countdown(login_as):
    member = make_member()
    add_fee(member)
    html = login_as(account_for(member), AREA_PERSONAL).get(reverse(HOME)).content.decode()
    block = summary(html)
    assert "Pendent" in block and "vigencia" not in block


def test_only_the_session_member_is_shown(login_as):
    paid_member("Berta", number=1300, document="00000000T")
    html = login_as(account_for(make_member()), AREA_PERSONAL).get(reverse(HOME)).content.decode()
    assert "Berta" not in html and "1300" not in html


def test_a_person_who_is_not_a_member_gets_no_summary(login_as):
    person = Person.objects.create(
        first_name="Convidat", last_name="Prova", origin=Person.Origin.WEB
    )
    account = Account.objects.create_personal(person, "convidat@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    html = login_as(account, AREA_PERSONAL).get(reverse(HOME)).content.decode()
    assert "oleaje-portada" in html and summary(html) is None


def test_the_admin_account_gets_no_member_summary(login_as, admin_account):
    Member.objects.create(
        person=admin_account.person,
        member_number=1400,
        type=MembershipType.objects.get(code="full"),
        status=Member.Status.ACTIVE,
        joined_on=date(2019, 3, 12),
    )
    html = login_as(admin_account, AREA_ADMIN).get(reverse(HOME)).content.decode()
    assert summary(html) is None
