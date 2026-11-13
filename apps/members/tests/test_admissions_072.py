"""Retoc de la T-M01-14 segons la 072 (09/11/2026): quota íntegra amb número d'ordre (P-54, sortida
E), exempts actius amb carnet (P-57, Q-001 i Q-002), acceptacions del sol·licitant a la persona
(Q-044), comprovació del representant (Q-043), contacte nou a la sol·licitud (Q-042) i cap
invitació (Q-012; la dels adults continua oberta). Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit, charges, consents
from apps.core.models import AuditEntry, Charge, Consent, Department, Person
from apps.core.normalization import normalize_phone
from apps.core.tests import conftest as core_conftest
from apps.members import admissions, cards, fees
from apps.members.models import AnnualFee, JoinAcceptance, Member, MemberRequest
from apps.members.tests.test_admissions import (
    MINOR,
    a_person,
    a_request,
    admin_client,
    left_member,
    minor_request,
    readmission_request,
)
from apps.members.tests.test_join import form_data

S = Member.Status
SYSTEM = audit.system("proves")
make_admin = core_conftest.make_admin  # fixture de la 00


@pytest.fixture
def secretary(make_admin):
    return make_admin("secretary", username="secretaria.072")


@pytest.fixture
def publisher(make_admin):
    return make_admin("administrator", username="publicador.072")


def text(kind, publisher):
    return consents.publish_text(kind, f"Text de prova: {kind}.", by=publisher)


@pytest.mark.django_db
class TestFee:
    def test_paying_member_gets_the_full_annual_fee_of_the_type(self, secretary):
        member = admissions.approve_join(a_request(type_code="full"), by=secretary)
        today = timezone.localdate()
        (fee,) = AnnualFee.objects.filter(member=member)
        assert member.status == S.PENDING
        assert (fee.period, fee.kind, fee.sequence, fee.due_on) == (
            today.year,
            AnnualFee.Kind.ANNUAL,
            1,
            today,
        )
        assert fee.charge.amount_cents == member.type.annual_fee_cents  # 070: sense prorrata
        assert fee.charge.kind == Charge.Kind.FEE
        assert fee.charge.status == Charge.Status.PENDING
        assert fee.charge.department.name == Department.GENERAL
        assert fee.charge.cost_centre.full_name == "General / Quotes de socis"  # S-M04-06

    def test_a_live_fee_of_the_same_period_is_not_duplicated(self, secretary):
        member = admissions.approve_join(a_request(), by=secretary)
        with pytest.raises(ValidationError):
            fees.issue_annual_fee(
                member, period=timezone.localdate().year, due_on=timezone.localdate(), by=SYSTEM
            )
        assert AnnualFee.objects.filter(member=member).count() == 1

    def test_readmission_after_a_cancelled_fee_gets_the_next_sequence(self, secretary):
        # P-54, sortida E: l'anul·lada es queda a l'historial i se'n crea una de nova.
        member = left_member(by=secretary)
        year = timezone.localdate().year
        old = fees.issue_annual_fee(member, period=year, due_on=timezone.localdate(), by=SYSTEM)
        charges.cancel(old.charge, "Baixa (prova)", by=secretary)
        admissions.approve_join(readmission_request(member), by=secretary, identity_checked=True)
        rows = list(
            AnnualFee.objects.filter(member=member, period=year)
            .order_by("sequence")
            .values_list("sequence", "charge__status")
        )
        assert rows == [(1, Charge.Status.CANCELLED), (2, Charge.Status.PENDING)]


@pytest.mark.django_db
class TestExempt:
    def test_exempt_minor_is_active_without_fee_and_with_a_card(self, secretary):
        before = Charge.objects.count()
        member = admissions.approve_join(
            minor_request(document=True), by=secretary, guardian_checked=True
        )
        assert member.status == S.ACTIVE
        assert not AnnualFee.objects.filter(member=member).exists()
        assert Charge.objects.count() == before  # cap càrrec de 0 €
        last = member.status_changes.order_by("created_at", "id").last()
        assert (last.to_status, last.reason) == (S.ACTIVE, admissions.EXEMPT_REASON)
        assert cards.active_card(member) is not None
        loaded = cards.load_member(member.pk)
        assert cards.valid_until(loaded) == datetime.date(MINOR.year + 14, 12, 31)

    def test_adult_is_not_exempt(self, secretary):
        member = admissions.approve_join(a_request(), by=secretary)
        assert member.status == S.PENDING
        assert cards.active_card(member) is None


@pytest.mark.django_db
class TestGuardianCheck:
    def test_minor_needs_the_guardian_check(self, secretary):
        join_request = minor_request(document=True)
        with pytest.raises(ValidationError):
            admissions.approve_join(join_request, by=secretary)
        assert not Member.objects.filter(person=join_request.person).exists()
        join_request.refresh_from_db()
        assert join_request.status == MemberRequest.Status.PENDING

    def test_the_check_is_recorded_without_any_copy(self, secretary):
        join_request = minor_request(document=True)
        admissions.approve_join(join_request, by=secretary, guardian_checked=True)
        entry = AuditEntry.objects.get(action=admissions.APPROVED)
        assert entry.details["guardian_checked"] is True
        assert "55555555K" not in str(entry.details)


@pytest.mark.django_db
class TestAcceptances:
    def test_applicant_acceptances_become_consents_with_the_accepted_version(
        self, secretary, publisher
    ):
        accepted = text("privacy", publisher)
        text("privacy", publisher)  # una versió nova després: no és la que va acceptar
        join_request = a_request()
        JoinAcceptance.objects.create(
            request=join_request,
            legal_text=accepted,
            accepted_by=JoinAcceptance.AcceptedBy.APPLICANT,
            channel=MemberRequest.Channel.WEB,
        )
        admissions.approve_join(join_request, by=secretary)
        (consent,) = Consent.objects.filter(person=join_request.person)
        assert consent.legal_text == accepted
        assert (consent.action, consent.channel) == (Consent.Action.GRANTED, Consent.Channel.WEB)
        entry = AuditEntry.objects.get(action=consents.GRANTED, target_id=join_request.person_id)
        assert entry.details["join_request"] == join_request.pk

    def test_in_person_acceptance_keeps_who_recorded_it(self, secretary, publisher, make_admin):
        recorder = make_admin("secretary", username="registra.072")
        join_request = a_request()
        MemberRequest.objects.filter(pk=join_request.pk).update(
            channel=MemberRequest.Channel.IN_PERSON
        )
        JoinAcceptance.objects.create(
            request=join_request,
            legal_text=text("privacy", publisher),
            accepted_by=JoinAcceptance.AcceptedBy.APPLICANT,
            channel=MemberRequest.Channel.IN_PERSON,
            recorded_by=recorder,
        )
        admissions.approve_join(join_request, by=secretary)
        (consent,) = Consent.objects.filter(person=join_request.person)
        assert consent.recorded_by == recorder

    def test_guardian_acceptances_stay_on_the_request(self, secretary, publisher):
        join_request = minor_request(document=True)
        JoinAcceptance.objects.create(
            request=join_request,
            legal_text=text("privacy", publisher),
            accepted_by=JoinAcceptance.AcceptedBy.GUARDIAN,
            channel=MemberRequest.Channel.WEB,
        )
        admissions.approve_join(join_request, by=secretary, guardian_checked=True)
        assert not Consent.objects.filter(person=join_request.person).exists()


@pytest.mark.django_db
class TestNewContact:
    def test_join_stores_the_new_contact_without_changing_the_person(self, client, publisher):
        for kind in ("privacy", "membership_terms", "guardian_authorization"):
            text(kind, publisher)
        person = Person.objects.create(
            first_name="Laia",
            last_name="Dorada Rap",
            origin=Person.Origin.WEB,
            id_document_type=Person.DocumentType.DNI,
            id_document_number="12345678Z",
            contact_email="laia.antic@example.org",
            phone="600000002",
        )
        response = client.post(
            reverse("members:join"),
            form_data(contact_email="laia.nou@example.org", phone="600 000 009"),
        )
        assert response.status_code in (200, 302, 303)
        join_request = MemberRequest.objects.get(person=person)
        assert join_request.new_contact_email == "laia.nou@example.org"
        assert join_request.new_contact_phone == normalize_phone("600 000 009")
        person.refresh_from_db()
        assert person.contact_email == "laia.antic@example.org"

    def test_new_person_has_no_new_contact(self, client, publisher):
        for kind in ("privacy", "membership_terms", "guardian_authorization"):
            text(kind, publisher)
        client.post(reverse("members:join"), form_data())
        join_request = MemberRequest.objects.get()
        assert (join_request.new_contact_email, join_request.new_contact_phone) == ("", "")

    def test_approver_decides_whether_to_update_the_contact(self, secretary):
        person = a_person(email="vell@example.org")
        join_request = a_request(person, new_contact_email="nou@example.org")
        admissions.approve_join(join_request, by=secretary)
        person.refresh_from_db()
        assert person.contact_email == "vell@example.org"

        other = a_person("Ona", "Mas", email="ona.vell@example.org")
        admissions.approve_join(
            a_request(other, new_contact_email="ona.nou@example.org"),
            by=secretary,
            update_contact=True,
        )
        other.refresh_from_db()
        assert other.contact_email == "ona.nou@example.org"
        assert AuditEntry.objects.filter(target_id=other.pk, field="contact_email").exists()


@pytest.mark.django_db
class TestNoInvitation:
    @pytest.mark.parametrize("minor", [True, False])
    def test_no_personal_account_is_created(self, secretary, minor):
        before = Account.objects.filter(kind=Account.Kind.PERSONAL).count()
        if minor:
            admissions.approve_join(
                minor_request(document=True), by=secretary, guardian_checked=True
            )
        else:
            admissions.approve_join(a_request(), by=secretary)
        assert Account.objects.filter(kind=Account.Kind.PERSONAL).count() == before


@pytest.mark.django_db
class TestScreen:
    def test_minor_needs_the_guardian_checkbox_and_shows_the_new_contact(self, secretary):
        join_request = minor_request(document=True)
        MemberRequest.objects.filter(pk=join_request.pk).update(
            new_contact_email="nou.contacte@example.org"
        )
        page = admin_client(secretary).get(reverse("administration:join_requests"))
        html = page.content.decode()
        assert 'name="representant_comprovat"' in html
        assert 'name="actualitza_contacte"' in html
        assert "nou.contacte@example.org" in html

    def test_post_passes_the_checks_to_the_service(self, secretary):
        join_request = minor_request(document=True)
        url = reverse("administration:join_approve", args=[join_request.pk])
        admin_client(secretary).post(url, {"representant_comprovat": "1"})
        join_request.refresh_from_db()
        assert join_request.status == MemberRequest.Status.APPROVED
