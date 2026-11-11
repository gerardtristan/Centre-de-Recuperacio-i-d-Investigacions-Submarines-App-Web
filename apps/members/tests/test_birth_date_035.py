"""Data de naixement que falta (T-M01-35; RN-M01-55, RN-M01-97; CA-M01-41 i CA-M01-43; decisió
079, A-10 i A-29). Només dades inventades.
"""

import datetime
import time

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import persons
from apps.core.models import AuditEntry, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import admissions, birth_date, join, member_edit
from apps.members.models import Member, MembershipType
from apps.members.tests.test_admissions import a_request
from apps.members.tests.test_member_edit import EDIT, a_member, data
from apps.members.tests.test_roster import admin_client
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
BIRTH = datetime.date(1985, 4, 12)
PROFILE = "members:profile"
SAVE = "members:birth_date"


def imported_member():
    person = Person.objects.create(
        first_name="Importada",
        last_name="Sense Data",
        origin=Person.Origin.CLUBER_IMPORT,
        contact_email="importada@example.org",
    )
    return Member.objects.create(
        person=person,
        member_number=7001,
        type=MembershipType.objects.get(code="full"),
        status=Member.Status.ACTIVE,
        joined_on=datetime.date(2010, 1, 1),
    )


def personal_client(person):
    account = Account.objects.create_personal(person, person.contact_email, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_PERSONAL
    session[AUTH_AT_SESSION_KEY] = time.time()
    session["imported_policies_ok"] = True  # les polítiques són una altra prova (CA-M01-109)
    session.save()
    return client, account


class TestCaM0143:
    def test_ca_m01_43_member_without_date_sees_the_notice_and_the_field(self):
        member = imported_member()
        client, _account = personal_client(member.person)
        home = client.get(reverse("core:home")).content.decode()
        assert "Falta la teva data de naixement" in home
        profile = client.get(reverse(PROFILE)).content.decode()
        assert "Falta la teva data de naixement" in profile
        assert 'name="birth_date"' in profile

    def test_ca_m01_43_completing_it_saves_it_without_the_date_in_the_audit_log(self):
        member = imported_member()
        client, account = personal_client(member.person)
        response = client.post(reverse(SAVE), {"birth_date": BIRTH.isoformat()})
        assert response.status_code == 302
        member.person.refresh_from_db()
        assert member.person.birth_date == BIRTH
        entry = AuditEntry.objects.get(action=persons.BIRTH_DATE_SET)
        assert entry.actor_account == account
        assert entry.details == {"had_value": False, "has_value": True, "source": "profile"}
        assert "1985" not in str(AuditEntry.objects.values().get(pk=entry.pk))
        profile = client.get(reverse(PROFILE)).content.decode()
        assert 'name="birth_date"' not in profile  # un cop desada, ja no s'ofereix
        assert "Falta la teva data" not in client.get(reverse("core:home")).content.decode()

    def test_ca_m01_43_the_member_cannot_change_a_date_already_saved(self):
        member = imported_member()
        Person.objects.filter(pk=member.person_id).update(birth_date=BIRTH)
        client, _account = personal_client(Person.objects.get(pk=member.person_id))
        client.post(reverse(SAVE), {"birth_date": "1990-01-01"})
        assert Person.objects.get(pk=member.person_id).birth_date == BIRTH
        assert not AuditEntry.objects.filter(action=persons.BIRTH_DATE_SET).exists()

    def test_ca_m01_43_future_date_is_rejected(self):
        member = imported_member()
        client, _account = personal_client(member.person)
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        response = client.post(reverse(SAVE), {"birth_date": tomorrow.isoformat()})
        assert response.status_code == 200
        assert "no pot ser posterior a avui" in response.content.decode()
        assert Person.objects.get(pk=member.person_id).birth_date is None

    def test_ca_m01_43_nothing_the_member_already_did_is_blocked(self):
        member = imported_member()
        client, _account = personal_client(member.person)
        for name in ("members:fees", "members:card", "members:profile"):
            assert client.get(reverse(name)).status_code == 200

    def test_ca_m01_43_appears_in_the_secretary_list(self, make_admin):  # noqa: F811
        member = imported_member()
        client = admin_client(make_admin("secretary"))
        page = client.get(reverse("administration:members_list"), {"sense_data": "on"})
        assert [m.pk for m, _fee in page.context["rows"]] == [member.pk]

    def test_no_notice_for_someone_who_is_not_a_member_or_has_left(self):
        person = Person.objects.create(
            first_name="No", last_name="Soci", origin=Person.Origin.WEB, contact_email="no@ex.org"
        )
        assert birth_date.missing_for(person) is False
        member = imported_member()
        Member.objects.filter(pk=member.pk).update(
            status=Member.Status.LEFT, left_on=datetime.date(2026, 1, 1)
        )
        assert birth_date.missing_for(member.person) is False


class TestSecretaryCompletesIt:
    def test_rn_m01_55_secretary_with_c1_completes_and_corrects_it(self, make_admin):  # noqa: F811
        secretary = make_admin("secretary")
        member = a_member(document=("dni", "12345678Z"))
        client = admin_client(secretary)
        response = client.post(
            reverse(EDIT, args=[member.pk]), data(member, birth_date="1980-02-03")
        )
        assert response.status_code == 303
        assert Person.objects.get(pk=member.person_id).birth_date == datetime.date(1980, 2, 3)
        entry = AuditEntry.objects.get(action=persons.BIRTH_DATE_SET)
        assert (entry.actor_account, entry.details["source"]) == (secretary, "member_edit")
        assert "1980" not in str(AuditEntry.objects.values().get(pk=entry.pk))

    def test_the_date_cannot_be_removed_or_be_in_the_future(self, make_admin):  # noqa: F811
        secretary = make_admin("secretary")
        member = a_member(document=("dni", "12345678Z"), birth_date=BIRTH)
        client = admin_client(secretary)
        tomorrow = (timezone.localdate() + datetime.timedelta(days=1)).isoformat()
        for value in ("", tomorrow):
            response = client.post(reverse(EDIT, args=[member.pk]), data(member, birth_date=value))
            assert response.status_code == 200
        assert Person.objects.get(pk=member.person_id).birth_date == BIRTH
        with pytest.raises(ValidationError):
            member_edit.edit_member_data(member, by=secretary, fields={"birth_date": None})

    def test_without_c1_the_date_is_not_editable(self, make_admin):  # noqa: F811
        # C1 és protegit (058): ve del catàleg, no de la matriu editable.
        assert "birth_date" in member_edit.editable_fields(make_admin("administrator"))
        for role in ("treasurer", "president", "board"):
            assert "birth_date" not in member_edit.editable_fields(make_admin(role))


class TestCaM0141AndFutureDates:
    def test_ca_m01_41_a_pending_join_without_date_cannot_be_approved(self, make_admin):  # noqa: F811
        with pytest.raises(ValidationError):
            admissions.approve_join(a_request(birth=None), by=make_admin("secretary"))
        assert not Member.objects.exists()

    def test_a10_the_join_service_rejects_a_future_date(self):
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        with pytest.raises(ValidationError):
            join.submit({"birth_date": tomorrow}, channel="web")
        assert not Person.objects.exists()
