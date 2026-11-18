"""Tipus de soci com a dada (T-M01-52; 091, RN-M01-107): les regles llegeixen els atributs del
tipus (`full_rights`, `min_age`) i no el codi. CA-M01-125, part de l'alta i dels canvis de
tipus. Només dades inventades."""

import pytest

from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import member_requests as mr
from apps.members.models import MemberRequest, MembershipType
from apps.members.tests.test_join import submit, texts  # noqa: F401 (fixture)
from apps.members.tests.test_join_minors import GUARDIAN, nothing_created, today  # noqa: F401
from apps.members.tests.test_member_requests import account_for, make_member

pytestmark = pytest.mark.usefixtures("texts")


def new_type(code, **attributes):
    return MembershipType.objects.create(
        code=code, name=code.capitalize(), annual_fee_cents=9000, **attributes
    )


def test_current_types_keep_their_rules():
    rules = MembershipType.objects.values_list("code", "full_rights", "min_age")
    assert set(rules) == {("full", True, 14), ("supporter", False, 0)}


@pytest.mark.usefixtures("today")  # 06/11/2026
class TestJoin:
    def test_new_type_like_full_has_the_same_age_rule(self):
        copy = new_type("ple-dret-2", full_rights=True, min_age=14)
        response = submit(birth_date="2016-04-01", membership_type=copy.pk, **GUARDIAN)
        assert "Amb menys de 14 anys només es pot ser simpatitzant." in response.content.decode()
        assert nothing_created()
        response = submit(birth_date="2010-06-01", membership_type=copy.pk, **GUARDIAN)
        assert response.status_code == 303
        assert MemberRequest.objects.get().requested_type == copy

    def test_new_type_like_supporter_admits_under_14(self):
        copy = new_type("infantil", min_age=0)
        response = submit(birth_date="2016-04-01", membership_type=copy.pk, **GUARDIAN)
        assert response.status_code == 303

    def test_a_higher_min_age_changes_the_rule(self):
        senior = new_type("senior", min_age=16)  # 15 anys el dia de la sol·licitud
        response = submit(birth_date="2011-06-01", membership_type=senior.pk, **GUARDIAN)
        assert response.status_code == 200
        assert nothing_created()


class TestTypeChange:
    def test_member_of_a_new_full_rights_type_may_only_downgrade(self):
        member = make_member(type_code=new_type("ple-dret-2", full_rights=True).code)
        assert mr.downgrade_problem(member) == ""
        assert mr.type_change_problem(member)
        request = mr.request_downgrade(member, by=account_for(member))
        assert request.requested_type.code == "supporter" and mr.is_downgrade(request)

    def test_member_of_a_new_type_without_full_rights_may_upgrade(self):
        member = make_member(type_code=new_type("juvenil").code)
        assert mr.type_change_problem(member) == ""
        assert mr.downgrade_problem(member)
        request = mr.request_type_change(member, by=account_for(member))
        assert request.requested_type.code == "full" and not mr.is_downgrade(request)

    def test_without_an_active_full_rights_type_no_upgrade(self):
        MembershipType.objects.filter(full_rights=True).update(active=False)
        member = make_member()
        with pytest.raises(mr.RequestNotAllowed):
            mr.request_type_change(member, by=account_for(member))
