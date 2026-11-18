"""Tipus de soci com a dada (T-M01-52; 091, RN-M01-107): les regles llegeixen els atributs del
tipus (`full_rights`, `min_age`) i no el codi. CA-M01-125, part de l'alta i dels canvis de
tipus. Només dades inventades."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse

from apps.core.models import Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import member_requests as mr
from apps.members.fee_rules import local_today
from apps.members.models import MemberRequest, MembershipType
from apps.members.tests.test_join import PUBLIC, submit, texts  # noqa: F401 (fixture)
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
        assert "Ple-dret-2: a partir dels 14 anys complerts." in response.content.decode()
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
        member = make_member(type_code=new_type("ple-dret-2", full_rights=True, min_age=14).code)
        assert mr.downgrade_problem(member) == ""
        assert mr.type_change_problem(member)
        request = mr.request_downgrade(member, by=account_for(member))
        assert request.requested_type.code == "supporter" and mr.is_downgrade(request)

    def test_member_of_a_new_type_without_full_rights_may_upgrade(self):
        juvenile = new_type("juvenil")
        MembershipType.objects.filter(pk=juvenile.pk).update(annual_fee_cents=2000)
        member = make_member(type_code="juvenil")
        assert mr.type_change_problem(member) == ""
        assert mr.downgrade_problem(member)
        request = mr.request_type_change(member, by=account_for(member))
        assert request.requested_type.code == "full" and not mr.is_downgrade(request)

    def test_without_an_active_full_rights_type_no_upgrade(self):
        MembershipType.objects.filter(full_rights=True).update(active=False)
        member = make_member()
        with pytest.raises(mr.RequestNotAllowed):
            mr.request_type_change(member, by=account_for(member))


# --- Revisió de la #217 ---------------------------------------------------------------------


def born(years):
    """Data de naixement d'algú que avui té `years` anys (fa anys l'1 de gener)."""
    return date(local_today().year - years, 1, 1)


def test_a_full_rights_type_needs_at_least_14(db):
    young = MembershipType(code="jove", name="Jove", annual_fee_cents=1, full_rights=True)
    with pytest.raises(ValidationError):
        young.full_clean()
    with pytest.raises(IntegrityError), transaction.atomic():
        young.save()
    MembershipType.objects.create(
        code="jove", name="Jove", annual_fee_cents=1, full_rights=True, min_age=14
    )


@pytest.mark.usefixtures("today")
class TestJoinMessages:
    def test_the_help_before_the_date_names_each_type_with_a_min_age(self):
        new_type("senior", min_age=16)
        page = Client().get(reverse(PUBLIC)).content.decode().replace("&#x27;", "'")
        assert "Ple dret: a partir dels 14 anys complerts." in page
        assert "Senior: a partir dels 16 anys complerts." in page
        assert "només poden ser simpatitzants" not in page

    def test_a_type_left_out_by_age_has_its_own_message(self):
        senior = new_type("senior", min_age=16)  # 15 anys el 06/11/2026
        page = submit(birth_date="2011-06-01", membership_type=senior.pk, **GUARDIAN)
        assert "Senior: a partir dels 16 anys complerts." in page.content.decode()
        assert nothing_created()


class TestTypeChangeAge:
    def test_an_11_year_old_supporter_cannot_ask_for_full_rights(self):
        member = make_member()
        Person.objects.filter(pk=member.person_id).update(birth_date=born(11))
        member.refresh_from_db()
        assert "14 anys" in mr.type_change_problem(member)
        with pytest.raises(mr.RequestNotAllowed):
            mr.request_type_change(member, by=account_for(member))
        assert not MemberRequest.objects.exists()

    def test_the_target_skips_types_the_member_is_too_young_for(self):
        MembershipType.objects.filter(code="full").update(min_age=18)
        young_full = new_type("ple-dret-jove", full_rights=True, min_age=14)
        member = make_member()
        Person.objects.filter(pk=member.person_id).update(birth_date=born(15))
        member.refresh_from_db()
        assert mr.target_type(full_rights=True, member=member) == young_full
        assert mr.request_type_change(member, by=account_for(member)).requested_type == young_full

    def test_no_supplement_to_pay_is_refused_when_asking(self):
        MembershipType.objects.filter(code="full").update(active=False)
        same_price = new_type("ple-dret-2", full_rights=True, min_age=14)
        MembershipType.objects.filter(pk=same_price.pk).update(annual_fee_cents=3500)
        member = make_member()
        assert mr.type_change_problem(member)
        with pytest.raises(mr.RequestNotAllowed):
            mr.request_type_change(member, by=account_for(member))
        assert not MemberRequest.objects.exists()
