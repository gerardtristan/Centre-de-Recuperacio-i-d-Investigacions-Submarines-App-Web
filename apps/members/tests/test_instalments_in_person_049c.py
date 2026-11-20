"""Triar els terminis des de l'administració a la quota d'una alta presencial (T-M01-49c, part 2;
072, tercera instrucció, punt 2; P-415): P23, mai per a un mateix, i les mateixes condicions que
quan els tria el soci. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.core.models import Charge
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import fees, instalments, services
from apps.members.fee_rules import local_today
from apps.members.models import AnnualFee, Member, MemberRequest
from apps.members.tests.test_cards import make_member
from apps.members.tests.test_instalments_049 import SYSTEM, on, plan_of  # noqa: F401
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

DETAIL = "administration:member_detail"
CHOOSE = "administration:member_fee_choose_instalments"


def joined(channel=MemberRequest.Channel.IN_PERSON):
    """Un soci pendent amb la quota de l'alta, aprovada avui pel canal indicat."""
    member = make_member(status=Member.Status.PENDING)
    MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=member.person,
        member=member,
        requested_type=member.type,
        channel=channel,
        status=MemberRequest.Status.APPROVED,
        resolved_at=timezone.now(),
    )
    today = local_today()
    return member, fees.issue_annual_fee(member, period=today.year, due_on=today, by=SYSTEM)


@pytest.fixture
def clerk(make_admin):  # noqa: F811
    """Un compte de la Secretaria (P23)."""
    return make_admin("secretary")


def test_the_fee_of_an_in_person_join_is_split_in_three(on, clerk):  # noqa: F811
    member, fee = joined()
    assert instalments.can_choose_in_person(fee, clerk)
    created = instalments.choose_in_person(fee, by=clerk)
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.CANCELLED
    assert "alta presencial" in fee.charge.cancel_reason
    assert [f.charge.amount_cents for f in created] == [3200, 3200, 3200]  # 90 € + 6 € de recàrrec
    assert len(plan_of(member)) == 3


def test_not_the_fee_of_a_web_join(on, clerk):  # noqa: F811
    member, fee = joined(MemberRequest.Channel.WEB)
    assert not instalments.can_choose_in_person(fee, clerk)
    with pytest.raises(ValidationError, match="alta presencial"):
        instalments.choose_in_person(fee, by=clerk)
    assert not plan_of(member)


def test_off_it_cannot_be_chosen(clerk):
    member, fee = joined()
    with pytest.raises(ValidationError):
        instalments.choose_in_person(fee, by=clerk)
    assert not plan_of(member)


@pytest.mark.parametrize("role", ["treasurer", "administrator"])
def test_without_p23_not_found(on, make_admin, role):  # noqa: F811
    member, fee = joined()
    with pytest.raises(Http404):
        instalments.choose_in_person(fee, by=make_admin(role))
    assert not plan_of(member)


def test_nobody_chooses_for_themself(on, make_admin):  # noqa: F811
    member, fee = joined()
    own = make_admin("secretary", person=member.person)
    with pytest.raises(services.OwnMemberChange):
        instalments.choose_in_person(fee, by=own)
    assert not plan_of(member)


class TestScreen:
    def test_the_clerk_chooses_from_the_member_page(self, on, clerk):  # noqa: F811
        member, fee = joined()
        client = admin_client(clerk)
        url = reverse(CHOOSE, args=[member.pk, fee.pk])
        assert url in client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        page = client.get(url).content.decode()
        assert "Termini 3 de 3" in page and "32,00" in page
        response = client.post(url)
        assert response.status_code == 303
        assert AnnualFee.objects.filter(member=member, kind=AnnualFee.Kind.INSTALMENT).count() == 3
        assert "Terminis creats" in client.get(response["Location"]).content.decode()

    def test_a_web_join_offers_nothing(self, on, clerk):  # noqa: F811
        member, fee = joined(MemberRequest.Channel.WEB)
        client = admin_client(clerk)
        url = reverse(CHOOSE, args=[member.pk, fee.pk])
        assert url not in client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        page = client.get(url).content.decode()
        assert (
            "no es pot pagar a terminis des d'aquí" in page and "Crea els tres terminis" not in page
        )
        assert client.post(url).status_code == 200
        assert not plan_of(member)

    def test_without_p23_not_found(self, on, make_admin):  # noqa: F811
        member, fee = joined()
        client = admin_client(make_admin("treasurer"))
        url = reverse(CHOOSE, args=[member.pk, fee.pk])
        assert client.get(url).status_code == 404
        assert client.post(url).status_code == 404
        assert not plan_of(member)
