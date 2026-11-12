"""Edició del soci després de la decisió 079 (T-M01-15b; RN-M01-90; CA-M01-99 a CA-M01-101):
el número de soci no es corregeix des de l'app, el motiu de la data d'alta és obligatori i el
document d'un menor es pot buidar. Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.core import persons
from apps.core.models import AuditEntry, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import member_edit
from apps.members.models import Member, MemberJoinDateChange
from apps.members.tests.test_member_edit import (
    EDIT,
    JOIN_DATE,
    JOINED,
    REASON,
    a_member,
    data,
    entries,
    remove_permission,
)
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin("secretary")


def years_ago(years):
    today = timezone.localdate()
    return today.replace(year=today.year - years, day=min(today.day, 28))


# --- CA-M01-99: el número de soci no es corregeix des de l'app -------------------------------


class TestCaM0199MemberNumber:
    def test_ca_m01_99_form_has_no_number_field(self, secretary):
        member = a_member()
        page = admin_client(secretary).get(reverse(EDIT, args=[member.pk])).content.decode()
        assert 'name="member_number"' not in page
        assert "El número de soci no es pot corregir des de l'aplicació." in page

    def test_ca_m01_99_a_number_added_to_the_request_is_ignored(self, secretary):
        member = a_member()
        number = member.member_number
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]),
            {**data(member, first_name="Anna Maria"), "member_number": "9999"},
        )
        assert response.status_code == 303
        member.refresh_from_db()
        assert member.member_number == number
        assert member.person.first_name == "Anna Maria"

    @pytest.mark.parametrize("field", ["member_number", "status", "type", "joined_on"])
    def test_ca_m01_99_service_rejects_fields_that_are_not_editable(self, secretary, field):
        member = a_member()
        number = member.member_number
        with pytest.raises(Http404):
            member_edit.edit_member_data(member, by=secretary, fields={field: "9999"})
        member.refresh_from_db()
        assert member.member_number == number

    def test_ca_m01_99_no_editable_field_is_the_number(self, secretary):
        assert "member_number" not in member_edit.editable_fields(secretary)
        assert "member_number" not in persons.EDITABLE_FIELDS


# --- CA-M01-100: motiu obligatori per corregir la data d'alta --------------------------------


class TestCaM01100JoinDateReason:
    def test_ca_m01_100_without_reason_is_rejected_on_the_screen(self, secretary):
        member = a_member()
        client = admin_client(secretary)
        for body in ({"joined_on": "1987-05-01"}, {"joined_on": "1987-05-01", "reason": "   "}):
            response = client.post(reverse(JOIN_DATE, args=[member.pk]), body)
            assert response.status_code == 200
            assert "reason" in response.context["form"].errors
        member.refresh_from_db()
        assert member.joined_on == JOINED
        assert not MemberJoinDateChange.objects.exists()

    @pytest.mark.parametrize("reason", ["", "   ", None])
    def test_ca_m01_100_service_rejects_an_empty_reason(self, secretary, reason):
        member = a_member()
        with pytest.raises(ValidationError):
            member_edit.correct_join_date(
                member,
                by=secretary,
                joined_on=datetime.date(1987, 5, 1),
                approximate=False,
                reason=reason,
            )
        assert not MemberJoinDateChange.objects.exists()

    def test_ca_m01_100_reason_is_kept_in_the_audit_log_with_the_old_value(self, secretary):
        member = a_member()
        response = admin_client(secretary).post(
            reverse(JOIN_DATE, args=[member.pk]),
            {"joined_on": "1987-05-01", "reason": f"  {REASON}  "},
        )
        assert response.status_code == 303
        (entry,) = entries(member_edit.JOIN_DATE_CORRECTED, member)
        assert (entry.field, entry.old_value, entry.new_value) == (
            "joined_on",
            "2019-03-12",
            "1987-05-01",
        )
        assert entry.reason == REASON
        assert entry.actor_account == secretary
        # L'historial de correccions no porta text lliure: res a anonimitzar en un esborrat.
        assert not any(f.name == "reason" for f in MemberJoinDateChange._meta.get_fields())

    def test_screen_asks_for_the_reason(self, secretary):
        member = a_member()
        page = admin_client(secretary).get(reverse(JOIN_DATE, args=[member.pk])).content.decode()
        assert "Motiu de la correcció" in page


# --- CA-M01-101: buidar el document d'un menor ------------------------------------------------


class TestCaM01101MinorDocument:
    def test_ca_m01_101_minor_document_can_be_cleared_and_the_old_value_is_recorded(
        self, secretary
    ):
        member = a_member(document=("dni", "12345678Z"), birth_date=years_ago(12))
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]), data(member, id_document="")
        )
        assert response.status_code == 303
        person = Person.objects.get(pk=member.person_id)
        assert (person.id_document_type, person.id_document_number) == ("", "")
        recorded = {e.field: (e.old_value, e.new_value) for e in entries(persons.UPDATED, person)}
        assert recorded == {
            "id_document_type": ("dni", ""),
            "id_document_number": ("12345678Z", ""),
        }
        assert {e.actor_account_id for e in entries(persons.UPDATED, person)} == {secretary.pk}

    @pytest.mark.parametrize("birth", [None, "adult"])
    def test_ca_m01_101_adult_or_unknown_age_cannot_be_cleared(self, secretary, birth):
        extra = {"birth_date": years_ago(30)} if birth else {}
        member = a_member(document=("dni", "12345678Z"), **extra)
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]), data(member, id_document="")
        )
        assert response.status_code == 200
        assert "només es pot treure a una persona menor" in response.content.decode()
        assert Person.objects.get(pk=member.person_id).id_document_number == "12345678Z"

    def test_ca_m01_101_service_checks_it_too(self, secretary):
        member = a_member(document=("dni", "12345678Z"), birth_date=years_ago(30))
        with pytest.raises(ValidationError):
            member_edit.edit_member_data(
                member,
                by=secretary,
                fields={"id_document_type": "", "id_document_number": ""},
            )
        assert Person.objects.get(pk=member.person_id).id_document_number == "12345678Z"
        assert not AuditEntry.objects.filter(action=persons.UPDATED).exists()

    def test_ca_m01_101_without_c2_the_document_is_not_touched(self, secretary):
        member = a_member(document=("dni", "12345678Z"), birth_date=years_ago(12))
        remove_permission("secretary", "members.field.identity")
        response = admin_client(secretary).post(
            reverse(EDIT, args=[member.pk]), data(member, id_document="")
        )
        assert response.status_code == 303
        assert Person.objects.get(pk=member.person_id).id_document_number == "12345678Z"
        with pytest.raises(Http404):
            member_edit.edit_member_data(
                member, by=secretary, fields={"id_document_type": "", "id_document_number": ""}
            )

    def test_just_turned_eighteen_is_not_a_minor(self, secretary):
        today = timezone.localdate()
        try:
            eighteen = today.replace(year=today.year - 18)
        except ValueError:  # 29 de febrer
            eighteen = today.replace(year=today.year - 18, day=28)
        member = a_member(document=("dni", "12345678Z"), birth_date=eighteen)
        assert not member_edit.may_clear_document(member.person)
        assert Member.objects.filter(pk=member.pk).exists()
