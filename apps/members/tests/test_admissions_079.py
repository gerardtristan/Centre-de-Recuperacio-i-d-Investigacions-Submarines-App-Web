"""Altes pendents després de la decisió 079 (T-M01-14; RN-M01-87 i RN-M01-88; CA-M01-90 a
CA-M01-95): invitació del compte personal, identitat, correu del rebuig, menors sense document,
readmissió amb un altre tipus, data d'alta i còpia de la data de naixement. Només dades
inventades.
"""

import datetime
import re

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts import invitations
from apps.accounts.models import Account, AccountInvitation
from apps.core import persons
from apps.core.models import AuditEntry, OutgoingEmail, Person, Role
from apps.core.tests import conftest as core_conftest
from apps.members import admissions
from apps.members.models import AnnualFee, Member, MemberRequest, MemberStatusChange
from apps.members.tests.test_admissions import (
    ADULT,
    REASON,
    a_person,
    a_request,
    a_type,
    admin_client,
    entries,
    left_member,
)
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
make_admin = core_conftest.make_admin  # fixture de la 00

S = Member.Status
APPROVE = "administration:join_approve"
LIST = "administration:join_requests"
INVITE = "administration:member_invite"
GUARDIAN = {
    "guardian_first_name": "Marta",
    "guardian_last_name": "Petit",
    "guardian_id_document_type": "dni",
    "guardian_id_document_number": "55555555K",
    "guardian_email": "marta@example.org",
    "guardian_phone": "600000001",
}


def years_ago(years):
    today = timezone.localdate()
    return today.replace(year=today.year - years, day=min(today.day, 28))


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin(Role.Code.SECRETARY)


def minor_request(person, birth, **extra):
    return a_request(person, birth=birth, **GUARDIAN, **extra)


def emails(template):
    return list(OutgoingEmail.objects.filter(template=template).order_by("pk"))


# --- CA-M01-90 i 91: invitació en aprovar ---------------------------------------------------


class TestInvitationOnApproval:
    def test_ca_m01_90_adult_without_account_gets_the_invitation(self, secretary):
        person = a_person(email="pol@example.org")
        member = admissions.approve_join(a_request(person), by=secretary)
        assert member.access_mail_sent is True
        (email,) = emails(invitations.INVITATION_TEMPLATE)
        assert email.to_address == "pol@example.org"
        assert email.person == person
        invitation = AccountInvitation.objects.get()
        assert (invitation.person, invitation.created_by) == (person, secretary)
        assert not Account.objects.filter(kind=Account.Kind.PERSONAL).exists()

    def test_ca_m01_91_person_with_account_gets_a_notice_and_no_invitation(self, secretary):
        person = a_person(email="pol@example.org")
        Account.objects.create_personal(person, "pol@example.org", PASSWORD)
        member = admissions.approve_join(a_request(person), by=secretary)
        assert member.access_mail_sent is True
        assert not AccountInvitation.objects.exists()
        (email,) = emails(invitations.NOTICE_TEMPLATE)
        assert "/compte/invitacio/" not in email.body_text
        assert not emails(invitations.INVITATION_TEMPLATE)

    def test_ca_m01_91_under_14_gets_nothing(self, secretary):
        person = a_person("Nil", "Petit", email="nil@example.org")
        member = admissions.approve_join(
            minor_request(person, years_ago(10)), by=secretary, guardian_checked=True
        )
        assert member.access_mail_sent is False
        assert not AccountInvitation.objects.exists()
        assert not OutgoingEmail.objects.exists()

    def test_ca_m01_91_from_14_to_17_without_own_email_gets_nothing(self, secretary):
        person = a_person("Aina", "Roig", email="")
        member = admissions.approve_join(
            minor_request(person, years_ago(16)), by=secretary, guardian_checked=True
        )
        assert member.access_mail_sent is False
        assert not AccountInvitation.objects.exists()
        assert not OutgoingEmail.objects.exists()  # tampoc al representant

    def test_ca_m01_91_from_14_to_17_with_own_email_gets_the_invitation(self, secretary):
        person = a_person("Aina", "Roig", email="aina@example.org")
        admissions.approve_join(
            minor_request(person, years_ago(16)), by=secretary, guardian_checked=True
        )
        (email,) = emails(invitations.INVITATION_TEMPLATE)
        assert email.to_address == "aina@example.org"  # mai el representant

    def test_readmission_also_sends_it(self, secretary):
        member = left_member(by=secretary)
        join_request = a_request(
            member.person, warning=[{"match": "document", "person_id": member.person_id}]
        )
        admissions.approve_join(join_request, by=secretary, identity_checked=True)
        assert len(emails(invitations.INVITATION_TEMPLATE)) == 1

    def test_failed_approval_sends_nothing(self, secretary, monkeypatch):
        def broken(*args, **kwargs):
            raise RuntimeError("fallada inventada")

        monkeypatch.setattr(admissions.cards, "replace_card", broken)
        person = a_person("Aina", "Roig", email="aina@example.org")
        with pytest.raises(RuntimeError):  # exempt per edat: el carnet falla després de tot
            admissions.approve_join(
                minor_request(person, years_ago(14)), by=secretary, guardian_checked=True
            )
        assert not AccountInvitation.objects.exists()
        assert not OutgoingEmail.objects.exists()

    def test_screen_does_not_say_which_email_was_sent(self, secretary):
        with_account = a_person("Laia", "Bru", email="laia@example.org")
        Account.objects.create_personal(with_account, "laia@example.org", PASSWORD)
        without_account = a_person("Pol", "Rius", email="pol@example.org")
        client = admin_client(secretary)
        texts = []
        for person in (with_account, without_account):
            response = client.post(reverse(APPROVE, args=[a_request(person).pk]), follow=True)
            (message,) = [str(m) for m in response.context["messages"]]
            texts.append(message.split("pendent fins que pagui la quota.")[1])
        assert texts[0] == texts[1]
        assert "correu d'accés" in texts[0]


# --- CA-M01-92: identitat i correu del rebuig -----------------------------------------------


class TestIdentityAndRejection:
    def test_ca_m01_92_identity_confirmation_records_who_and_when(self, secretary):
        existing = a_person()
        join_request = a_request(
            existing, warning=[{"match": "document", "person_id": existing.pk}]
        )
        before = timezone.now()
        admissions.approve_join(join_request, by=secretary, identity_checked=True)
        (approved,) = entries(admissions.APPROVED, join_request)
        assert approved.details["identity_checked"] is True
        assert approved.actor_account == secretary
        assert approved.created_at >= before

    def test_ca_m01_92_rejection_goes_to_the_address_written_in_the_request(self, secretary):
        existing = a_person(email="existent@example.org")
        join_request = a_request(
            existing,
            warning=[{"match": "document", "person_id": existing.pk}],
            new_contact_email="escrita@example.org",
        )
        admissions.reject_join(join_request, by=secretary, reason=REASON)
        (email,) = emails(admissions.REJECTION_TEMPLATE)
        assert email.to_address == "escrita@example.org"
        assert email.person is None  # no es lliga a la persona existent
        assert REASON not in email.body_text

    def test_ca_m01_92_same_text_whether_the_person_existed_or_not(self, secretary):
        existing = a_person(email="existent@example.org")
        admissions.reject_join(
            a_request(existing, warning=[{"match": "document", "person_id": existing.pk}]),
            by=secretary,
            reason=REASON,
        )
        admissions.reject_join(
            a_request(a_person("Nova", "Persona", email="nova@example.org")),
            by=secretary,
            reason="Un altre motiu inventat",
        )
        first, second = emails(admissions.REJECTION_TEMPLATE)
        assert (first.subject, first.body_text) == (second.subject, second.body_text)
        assert first.to_address == "existent@example.org"  # la mateixa que es va escriure

    def test_rejection_of_a_minor_goes_to_the_guardian(self, secretary):
        person = a_person("Nil", "Petit", email="nil@example.org")
        admissions.reject_join(minor_request(person, years_ago(10)), by=secretary, reason=REASON)
        (email,) = emails(admissions.REJECTION_TEMPLATE)
        assert email.to_address == "marta@example.org"


# --- CA-M01-93: menors sense document --------------------------------------------------------


class TestMinorsWithoutDocument:
    BIRTH = datetime.date(2015, 5, 5)

    def request_for_minor(self):
        return minor_request(a_person("Nil", "Petit", document=False, email=""), self.BIRTH)

    def test_ca_m01_93_no_similar_person_no_confirmation(self, secretary):
        join_request = self.request_for_minor()
        assert admissions.similar_minors(join_request) == []
        member = admissions.approve_join(join_request, by=secretary, guardian_checked=True)
        assert member.status == S.ACTIVE
        (approved,) = entries(admissions.APPROVED, join_request)
        assert approved.details["similar_minors_reviewed"] == 0

    @pytest.mark.parametrize("where", ["person", "join_request"])
    def test_ca_m01_93_similar_person_needs_the_review(self, secretary, where):
        other = a_person("nil", "PETIT", document=False, email="")
        if where == "person":
            Person.objects.filter(pk=other.pk).update(birth_date=self.BIRTH)
        else:
            minor_request(
                other, self.BIRTH, status=MemberRequest.Status.REJECTED, resolution_reason=REASON
            )
        join_request = self.request_for_minor()
        assert admissions.similar_minors(join_request) == [other]
        with pytest.raises(ValidationError):
            admissions.approve_join(join_request, by=secretary, guardian_checked=True)
        assert not Member.objects.exists()
        member = admissions.approve_join(
            join_request, by=secretary, guardian_checked=True, duplicates_reviewed=True
        )
        assert member.person == join_request.person  # mai es fusionen
        (approved,) = entries(admissions.APPROVED, join_request)
        assert approved.details["similar_minors_reviewed"] == 1
        assert approved.actor_account == secretary

    def test_other_name_or_birth_date_is_not_similar(self, secretary):
        other = a_person("Nil", "Gran", document=False, email="")
        Person.objects.filter(pk=other.pk).update(birth_date=self.BIRTH)
        same_name = a_person("Nil", "Petit", document=False, email="")
        Person.objects.filter(pk=same_name.pk).update(birth_date=datetime.date(2014, 1, 1))
        assert admissions.similar_minors(self.request_for_minor()) == []

    def test_minor_with_document_or_adult_is_never_compared(self, secretary):
        other = a_person("Nil", "Petit", document=False, email="")
        Person.objects.filter(pk=other.pk).update(birth_date=self.BIRTH)
        with_document = minor_request(a_person("Nil", "Petit", email=""), self.BIRTH)
        assert admissions.similar_minors(with_document) == []
        assert admissions.similar_minors(a_request(a_person("Nil", "Petit"))) == []

    def test_ca_m01_93_screen_shows_the_warning_and_the_checkbox(self, secretary):
        other = a_person("Nil", "Petit", document=False, email="")
        Person.objects.filter(pk=other.pk).update(birth_date=self.BIRTH)
        Member.objects.create(
            person=other,
            member_number=77,
            type=a_type(),
            status=S.ACTIVE,
            joined_on=datetime.date(2024, 1, 1),
        )
        join_request = self.request_for_minor()
        client = admin_client(secretary)
        page = client.get(reverse(LIST)).content.decode()
        assert "Possible duplicat d'un menor sense document" in page
        assert "soci número 77" in page
        assert 'name="duplicats_revisats"' in page

        data = {"representant_comprovat": "1"}
        client.post(reverse(APPROVE, args=[join_request.pk]), data)
        assert Member.objects.count() == 1  # sense la casella, el servidor ho rebutja
        client.post(reverse(APPROVE, args=[join_request.pk]), data | {"duplicats_revisats": "1"})
        assert Member.objects.count() == 2


# --- CA-M01-94: readmissió amb un altre tipus ------------------------------------------------


class TestReadmissionWithAnotherType:
    def test_ca_m01_94_same_number_new_type_and_fee_of_the_new_type(self, secretary):
        member = left_member(number=41, type_code="supporter", by=secretary)
        join_request = a_request(
            member.person,
            type_code="full",
            warning=[{"match": "document", "person_id": member.person_id}],
        )
        readmitted = admissions.approve_join(join_request, by=secretary, identity_checked=True)

        assert readmitted.pk == member.pk
        assert readmitted.member_number == 41
        assert (readmitted.status, readmitted.type) == (S.PENDING, a_type("full"))
        history = list(MemberStatusChange.objects.filter(member=member).order_by("id"))
        assert [(h.to_status, h.to_type.code) for h in history] == [
            (S.LEFT, "supporter"),
            (S.PENDING, "supporter"),
            (S.PENDING, "full"),
        ]
        assert history[-1].from_type.code == "supporter"
        fee = AnnualFee.objects.get(member=member)
        assert fee.charge.amount_cents == a_type("full").annual_fee_cents

    def test_failure_after_the_type_change_undoes_everything(self, secretary, monkeypatch):
        member = left_member(type_code="supporter", by=secretary)
        join_request = a_request(
            member.person,
            type_code="full",
            warning=[{"match": "document", "person_id": member.person_id}],
        )

        def broken(*args, **kwargs):
            raise RuntimeError("fallada inventada")

        monkeypatch.setattr(admissions.fees, "issue_annual_fee", broken)
        with pytest.raises(RuntimeError):
            admissions.approve_join(join_request, by=secretary, identity_checked=True)
        member.refresh_from_db()
        assert (member.status, member.type) == (S.LEFT, a_type("supporter"))


# --- CA-M01-95: data d'alta i data de naixement ----------------------------------------------


class TestJoinDateAndBirthDate:
    def test_ca_m01_95_join_date_is_the_approval_day(self, secretary):
        join_request = a_request()
        MemberRequest.objects.filter(pk=join_request.pk).update(
            created_at=timezone.now() - datetime.timedelta(days=20)
        )
        member = admissions.approve_join(join_request, by=secretary)
        assert member.joined_on == timezone.localdate()

    def test_ca_m01_95_birth_date_is_copied_when_the_person_has_none(self, secretary):
        join_request = a_request(birth=ADULT)
        assert join_request.person.birth_date is None
        member = admissions.approve_join(join_request, by=secretary)
        assert member.person.birth_date == ADULT
        entry = AuditEntry.objects.get(action=persons.BIRTH_DATE_SET)
        # RN-M01-48: el registre diu que ha canviat, mai la data.
        assert (entry.old_value, entry.new_value) == (None, None)
        assert entry.details == {
            "had_value": False,
            "has_value": True,
            "source": "join_request",
            "check_reset": False,
        }
        assert str(ADULT) not in str(AuditEntry.objects.values().get(pk=entry.pk))
        (approved,) = entries(admissions.APPROVED, join_request)
        assert approved.details["birth_date_copied"] is True

    def test_ca_m01_95_a_different_birth_date_is_not_touched(self, secretary):
        existing = a_person()
        known = datetime.date(1985, 1, 1)
        Person.objects.filter(pk=existing.pk).update(birth_date=known)
        join_request = a_request(
            Person.objects.get(pk=existing.pk),
            birth=ADULT,
            warning=[{"match": "document", "person_id": existing.pk}],
        )
        assert admissions.birth_date_conflict(join_request) is True
        member = admissions.approve_join(join_request, by=secretary, identity_checked=True)
        assert member.person.birth_date == known
        assert not AuditEntry.objects.filter(action=persons.BIRTH_DATE_SET).exists()
        page = admin_client(secretary).get(reverse(LIST))
        assert page.status_code == 200

    def test_screen_warns_about_a_different_birth_date_without_showing_it(self, make_admin):  # noqa: F811
        existing = a_person()
        Person.objects.filter(pk=existing.pk).update(birth_date=datetime.date(1985, 1, 1))
        join_request = a_request(Person.objects.get(pk=existing.pk), birth=ADULT)
        # L'hora de la sol·licitud surt amb microsegons; el 20/11 al CI, «.511985» (P-315b).
        moment = timezone.now().replace(microsecond=511985)
        MemberRequest.objects.filter(pk=join_request.pk).update(created_at=moment)
        page = admin_client(make_admin(Role.Code.TREASURER)).get(reverse(LIST)).content.decode()
        assert "Data de naixement diferent" in page
        # L'any com a número sencer, no dins dels microsegons (el tresorer no té C1).
        assert not re.search(r"\b1985\b", page) and "01/01/1985" not in page

    def test_ca_m01_102_future_birth_date_is_rejected_by_the_service(self, secretary):
        person = a_person()
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        with pytest.raises(ValidationError):
            persons.set_birth_date(person, tomorrow, by=secretary)
        person.refresh_from_db()
        assert person.birth_date is None


# --- Tornar a enviar la invitació (especificació, punt 7) -----------------------------------


class TestResendInvitation:
    def member(self, secretary, email="pol@example.org"):
        return admissions.approve_join(a_request(a_person(email=email)), by=secretary)

    def test_secretary_resends_and_the_old_link_stops_working(self, secretary):
        member = self.member(secretary)
        old = AccountInvitation.objects.get()
        client = admin_client(secretary)
        response = client.post(reverse(INVITE, args=[member.pk]))
        assert response.status_code == 303
        old.refresh_from_db()
        assert old.invalidated_at is not None
        assert AccountInvitation.objects.filter(invalidated_at__isnull=True).count() == 1
        assert len(emails(invitations.INVITATION_TEMPLATE)) == 2

    def test_needs_m2_and_p4(self, make_admin, secretary):  # noqa: F811
        member = self.member(secretary)
        for role in (Role.Code.TREASURER, Role.Code.PRESIDENT, Role.Code.BOARD):
            account = make_admin(role)
            assert admin_client(account).post(reverse(INVITE, args=[member.pk])).status_code == 404
            with pytest.raises(Http404):
                admissions.resend_invitation(member, by=account)
        assert len(emails(invitations.INVITATION_TEMPLATE)) == 1

    def test_nothing_is_sent_when_the_person_already_has_an_account(self, secretary):
        member = self.member(secretary)
        Account.objects.create_personal(member.person, "pol@example.org", PASSWORD)
        assert admissions.resend_invitation(member, by=secretary) is False
        assert len(emails(invitations.INVITATION_TEMPLATE)) == 1

    def test_button_only_when_it_can_be_sent(self, make_admin, secretary):  # noqa: F811
        member = self.member(secretary)
        detail = reverse("administration:member_detail", args=[member.pk])
        assert (
            "Envia la invitació del compte" in admin_client(secretary).get(detail).content.decode()
        )
        treasurer = admin_client(make_admin(Role.Code.TREASURER))
        assert "Envia la invitació del compte" not in treasurer.get(detail).content.decode()
        Account.objects.create_personal(member.person, "pol@example.org", PASSWORD)
        assert (
            "Envia la invitació del compte"
            not in admin_client(secretary).get(detail).content.decode()
        )

    def test_get_is_not_allowed(self, secretary):
        member = self.member(secretary)
        assert admin_client(secretary).get(reverse(INVITE, args=[member.pk])).status_code == 405
