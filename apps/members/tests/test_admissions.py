"""Altes pendents: aprovar i rebutjar (T-M01-14; CA-M01-03 a 05; RN-M01-05, RN-M01-06; 039,
059 i 067).

Retoc del 09/11/2026 (072): quota anual íntegra amb número d'ordre (P-54 E), exempts actius amb
carnet (P-57), acceptacions del sol·licitant a `core.Consent` (Q-044), comprovació del
representant (Q-043) i contacte nou a la sol·licitud (Q-042). Fora d'aquestes proves: la invitació
per activar el compte (cap mecanisme especificat; cap per als menors de 14 anys, Q-012), i les
proves comproven que no es crea cap compte personal. Només dades inventades.
"""

import datetime
import time

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit, charges
from apps.core.models import (
    AccountRole,
    AuditEntry,
    Charge,
    Consent,
    OutgoingEmail,
    Person,
    Role,
    RolePermission,
)
from apps.core.tests import conftest as core_conftest
from apps.members import admissions, services
from apps.members.models import (
    AnnualFee,
    Member,
    MemberRequest,
    MembershipNumberCounter,
    MembershipType,
    MemberStatusChange,
)
from apps.members.services import InactiveAccount, OwnMemberChange
from conftest import CommittedDataTestCase, run_together

S = Member.Status
R = MemberRequest.Status
ADULT = datetime.date(1990, 2, 14)
MINOR = datetime.date(2015, 5, 5)
LEFT_ON = datetime.date(2024, 6, 30)
REASON = "Motiu inventat de proves"
LIST = "administration:join_requests"
APPROVE = "administration:join_approve"
REJECT = "administration:join_reject"
P3A_ROLES = ["secretary", "treasurer", "administrator", "president"]
NO_ROLES = ["board", "instructor", "courses_manager", "equipment_manager", "history_department"]
_docs = iter(range(10_000_000, 99_999_999))
make_admin = core_conftest.make_admin  # fixture de la 00


def counter():
    return MembershipNumberCounter.objects.get(pk=1).last_number


def set_counter(value):
    MembershipNumberCounter.objects.filter(pk=1).update(last_number=value)


def a_type(code="supporter"):
    return MembershipType.objects.get(code=code)


def a_person(first="Pol", last="Rius", *, document=True, email="pol@example.org"):
    fields = {"contact_email": email}
    if document:
        fields.update(id_document_type="dni", id_document_number=f"{next(_docs)}X")
    return Person.objects.create(first_name=first, last_name=last, origin="web", **fields)


def a_request(person=None, *, type_code="supporter", birth=ADULT, warning=None, **fields):
    return MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=person or a_person(),
        requested_type=a_type(type_code),
        channel=MemberRequest.Channel.WEB,
        birth_date=birth,
        duplicate_warning=warning or [],
        **fields,
    )


def minor_request(*, document):
    return a_request(
        a_person("Nil", "Petit", document=document),
        birth=MINOR,
        guardian_first_name="Marta",
        guardian_last_name="Petit",
        guardian_id_document_type="dni",
        guardian_id_document_number="55555555K",
    )


def left_member(number=41, type_code="supporter", person=None, by=None):
    member = Member.objects.create(
        person=person or a_person("Núria", "Font"),
        member_number=number,
        type=a_type(type_code),
        status=S.ACTIVE,
        joined_on=datetime.date(2020, 1, 15),
    )
    services._change_status(member, S.LEFT, by=by, effective_on=LEFT_ON, reason=REASON)
    return Member.objects.get(pk=member.pk)


def readmission_request(member):
    return a_request(
        member.person,
        type_code=member.type.code,
        warning=[{"match": "document", "person_id": member.person_id}],
    )


def entries(action, target):
    return list(
        AuditEntry.objects.filter(
            action=action,
            target_type=target._meta.label_lower,
            target_id=str(target.pk),
        ).order_by("id")
    )


def side_effects():
    return (
        AnnualFee.objects.count(),
        Charge.objects.count(),
        Account.objects.filter(kind=Account.Kind.PERSONAL).count(),
        Consent.objects.count(),
    )


def admin_client(account, *, csrf=False):
    client = Client(enforce_csrf_checks=csrf)
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_ADMIN
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


@pytest.fixture
def secretary(make_admin):
    return make_admin(Role.Code.SECRETARY)


# --- CA-M01-03: aprovar crea el soci pendent amb el número següent ---------------------------


@pytest.mark.django_db
class TestApprove:
    def test_creates_pending_member_with_next_number(self, secretary):
        set_counter(355)
        join_request = a_request()
        before = side_effects()

        member = admissions.approve_join(join_request, by=secretary)

        assert member.status == S.PENDING
        assert member.member_number == 356
        assert counter() == 356
        assert member.person_id == join_request.person_id
        assert member.type == a_type("supporter")
        assert member.joined_on == timezone.localdate()
        assert len(member.avatar_seed) == 64
        join_request.refresh_from_db()
        assert join_request.status == R.APPROVED
        assert join_request.member == member
        assert join_request.resolved_by == secretary
        assert join_request.resolved_at is not None
        assert join_request.effective_on == timezone.localdate()
        # 072: la quota anual íntegra (un càrrec); cap compte personal (invitació oberta) ni
        # consentiment (aquesta sol·licitud no té acceptacions).
        fees, charges_, accounts, consents_ = before
        assert side_effects() == (fees + 1, charges_ + 1, accounts, consents_)

    def test_writes_initial_history_entry(self, secretary):
        member = admissions.approve_join(a_request(), by=secretary)
        (entry,) = MemberStatusChange.objects.filter(member=member)
        assert (entry.from_status, entry.to_status) == ("", S.PENDING)
        assert entry.from_type is None
        assert entry.to_type == member.type
        assert entry.actor_account == secretary
        assert entry.effective_on == timezone.localdate()

    def test_audit_has_previous_values(self, secretary):
        set_counter(9)
        join_request = a_request()
        member = admissions.approve_join(join_request, by=secretary)
        created = {
            e.field: (e.old_value, e.new_value) for e in entries(admissions.MEMBER_CREATED, member)
        }
        assert created["member_number"] == (None, 10)
        assert created["status"] == ("", S.PENDING)
        assert created["type"] == (None, "supporter")
        (approved,) = entries(admissions.APPROVED, join_request)
        assert (approved.old_value, approved.new_value) == (R.PENDING, R.APPROVED)
        assert approved.actor_account == secretary
        assert approved.details["member_id"] == member.pk
        assert approved.details["readmission"] is False

    def test_consecutive_approvals_get_consecutive_numbers(self, secretary):
        set_counter(100)
        first = admissions.approve_join(a_request(), by=secretary)
        second = admissions.approve_join(a_request(a_person("Clara", "Bosch")), by=secretary)
        assert (first.member_number, second.member_number) == (101, 102)

    def test_avatar_seed_is_new_for_each_member(self, secretary):
        first = admissions.approve_join(a_request(), by=secretary)
        second = admissions.approve_join(a_request(a_person("Clara", "Bosch")), by=secretary)
        assert first.avatar_seed != second.avatar_seed

    def test_already_resolved_request_is_rejected(self, secretary):
        join_request = a_request()
        admissions.approve_join(join_request, by=secretary)
        with pytest.raises(ValidationError):
            admissions.approve_join(join_request, by=secretary)
        assert Member.objects.count() == 1

    def test_without_p3_is_not_found(self, make_admin):
        join_request = a_request()
        with pytest.raises(Http404):
            admissions.approve_join(join_request, by=make_admin(Role.Code.BOARD))
        assert not Member.objects.exists()

    def test_inactive_account_cannot_approve(self, secretary):
        Account.objects.filter(pk=secretary.pk).update(status=Account.Status.DISABLED)
        with pytest.raises(InactiveAccount):
            admissions.approve_join(a_request(), by=secretary)
        assert not Member.objects.exists()

    def test_failure_half_way_leaves_nothing_written(self, secretary, monkeypatch):
        set_counter(7)
        join_request = a_request()
        original = audit.record

        def broken(action, **kwargs):
            if action == admissions.APPROVED:
                raise RuntimeError("fallada inventada")
            return original(action, **kwargs)

        monkeypatch.setattr(admissions.audit, "record", broken)
        with pytest.raises(RuntimeError):
            admissions.approve_join(join_request, by=secretary)
        assert counter() == 7
        assert not Member.objects.exists()
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING


# --- Casos que no s'aproven (decisions obertes o dades que falten) ---------------------------


@pytest.mark.django_db
class TestBlocked:
    def assert_not_approved(self, join_request, by, **kwargs):
        before = (counter(), Member.objects.count())
        with pytest.raises(ValidationError):
            admissions.approve_join(join_request, by=by, **kwargs)
        assert (counter(), Member.objects.count()) == before
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING

    def test_without_birth_date(self, secretary):
        self.assert_not_approved(a_request(birth=None), secretary)

    def test_minor_without_document_is_approved_without_similar_people(self, secretary):
        # 079 (A-15, RN-M01-88): ja no espera cap decisió; sense coincidències, s'aprova.
        join_request = minor_request(document=False)
        assert admissions.approval_blocker(join_request) is None
        member = admissions.approve_join(join_request, by=secretary, guardian_checked=True)
        assert member.status == S.ACTIVE

    def test_minor_with_document_is_approved(self, secretary):
        member = admissions.approve_join(
            minor_request(document=True), by=secretary, guardian_checked=True
        )
        # P-57, opció 1 (072): l'exempt per edat passa a actiu, sense quota.
        assert member.status == S.ACTIVE
        assert not AnnualFee.objects.exists()

    def test_person_who_is_already_a_member(self, secretary):
        person = a_person()
        Member.objects.create(
            person=person, member_number=5, type=a_type(), joined_on=datetime.date(2020, 1, 1)
        )
        self.assert_not_approved(a_request(person), secretary)

    def test_document_match_needs_identity_confirmation(self, secretary):
        existing = a_person()
        join_request = a_request(
            existing, warning=[{"match": "document", "person_id": existing.pk}]
        )
        self.assert_not_approved(join_request, secretary)
        member = admissions.approve_join(join_request, by=secretary, identity_checked=True)
        assert member.person == existing
        (approved,) = entries(admissions.APPROVED, join_request)
        assert approved.details["identity_checked"] is True

    def test_email_match_alone_does_not_need_identity_confirmation(self, secretary):
        join_request = a_request(warning=[{"match": "email", "person_id": 1}])
        assert admissions.approve_join(join_request, by=secretary).status == S.PENDING

    def test_readmission_with_another_type_needs_only_the_identity_check(self, secretary):
        # 079 (A-05, P-68): ja no espera cap decisió; el detall és a `test_admissions_079.py`.
        member = left_member(by=secretary)
        join_request = a_request(
            member.person,
            type_code="full",
            warning=[{"match": "document", "person_id": member.person_id}],
        )
        self.assert_not_approved(join_request, secretary)
        assert Member.objects.get(pk=member.pk).status == S.LEFT
        admissions.approve_join(join_request, by=secretary, identity_checked=True)
        assert Member.objects.get(pk=member.pk).status == S.PENDING


# --- Readmissió (067): mateix número, el comptador no avança -------------------------------


@pytest.mark.django_db
class TestReadmission:
    def test_keeps_the_number_and_does_not_move_the_counter(self, secretary):
        member = left_member(number=41, by=secretary)
        set_counter(500)
        join_request = readmission_request(member)

        readmitted = admissions.approve_join(join_request, by=secretary, identity_checked=True)

        assert readmitted.pk == member.pk
        assert readmitted.member_number == 41
        assert readmitted.status == S.PENDING
        assert readmitted.left_on is None
        assert counter() == 500
        assert Member.objects.count() == 1
        join_request.refresh_from_db()
        assert (join_request.status, join_request.member_id) == (R.APPROVED, member.pk)
        assert [
            e.to_status for e in MemberStatusChange.objects.filter(member=member).order_by("id")
        ] == [
            S.LEFT,
            S.PENDING,
        ]
        (approved,) = entries(admissions.APPROVED, join_request)
        assert approved.details["readmission"] is True

    @pytest.mark.parametrize("other_status", [S.ACTIVE, S.LEFT])
    def test_number_of_another_member_is_rejected(self, secretary, other_status):
        # Prova separada de l'anterior (fila de la 067): el comptador donaria el número 42, que
        # ja és d'un altre soci, actiu o de baixa.
        Member.objects.create(
            person=a_person("Altre", "Soci"),
            member_number=42,
            type=a_type(),
            status=other_status,
            joined_on=datetime.date(2019, 1, 1),
            left_on=LEFT_ON if other_status == S.LEFT else None,
        )
        set_counter(41)
        join_request = a_request()
        with pytest.raises(ValidationError):
            admissions.approve_join(join_request, by=secretary)
        assert counter() == 41
        assert Member.objects.count() == 1
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING

    def test_failure_after_readmit_undoes_the_readmission(self, secretary, monkeypatch):
        member = left_member(by=secretary)
        join_request = readmission_request(member)
        original = audit.record

        def broken(action, **kwargs):
            if action == admissions.APPROVED:
                raise RuntimeError("fallada inventada")
            return original(action, **kwargs)

        monkeypatch.setattr(admissions.audit, "record", broken)
        with pytest.raises(RuntimeError):
            admissions.approve_join(join_request, by=secretary, identity_checked=True)
        member.refresh_from_db()
        assert (member.status, member.left_on) == (S.LEFT, LEFT_ON)
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING


# --- CA-M01-05: rebutjar amb motiu ---------------------------------------------------------


@pytest.mark.django_db
class TestReject:
    def test_rejects_with_reason_without_member_or_number(self, secretary):
        set_counter(30)
        join_request = a_request()

        admissions.reject_join(join_request, by=secretary, reason=f"  {REASON}  ")

        join_request.refresh_from_db()
        assert join_request.status == R.REJECTED
        assert join_request.resolution_reason == REASON
        assert join_request.resolved_by == secretary
        assert join_request.resolved_at is not None
        assert not Member.objects.exists()
        assert counter() == 30
        (entry,) = entries(admissions.REJECTED, join_request)
        assert (entry.old_value, entry.new_value, entry.reason) == (R.PENDING, R.REJECTED, REASON)

    @pytest.mark.parametrize("reason", ["", "   ", None])
    def test_reason_is_required(self, secretary, reason):
        join_request = a_request()
        with pytest.raises(ValidationError):
            admissions.reject_join(join_request, by=secretary, reason=reason)
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING
        assert not OutgoingEmail.objects.exists()

    def test_person_is_told_by_email_without_reason_or_personal_data(self, secretary):
        person = a_person("Sentinella", "Cognom", email="sentinella@example.org")
        admissions.reject_join(a_request(person), by=secretary, reason=REASON)
        email = OutgoingEmail.objects.get()
        assert email.template == admissions.REJECTION_TEMPLATE
        assert email.to_address == "sentinella@example.org"
        for text in (REASON, "Sentinella", person.id_document_number):
            assert text not in email.body_text
            assert text not in email.subject

    def test_no_email_without_address(self, secretary):
        admissions.reject_join(a_request(a_person(email="")), by=secretary, reason=REASON)
        assert not OutgoingEmail.objects.exists()

    def test_minor_without_document_can_be_rejected(self, secretary):
        join_request = minor_request(document=False)
        admissions.reject_join(join_request, by=secretary, reason=REASON)
        join_request.refresh_from_db()
        assert join_request.status == R.REJECTED

    def test_already_resolved_request_cannot_be_rejected(self, secretary):
        join_request = a_request()
        admissions.approve_join(join_request, by=secretary)
        with pytest.raises(ValidationError):
            admissions.reject_join(join_request, by=secretary, reason=REASON)
        join_request.refresh_from_db()
        assert join_request.status == R.APPROVED

    def test_without_p3_is_not_found(self, make_admin):
        with pytest.raises(Http404):
            admissions.reject_join(a_request(), by=make_admin(Role.Code.BOARD), reason=REASON)


# --- Conflicte d'interès als punts d'entrada (fila de la revisió de la T-M01-12) -----------


@pytest.mark.django_db
class TestOwnRequestAtTheEntryPoint:
    def test_own_new_join_is_rejected_and_recorded(self, make_admin):
        join_request = a_request()
        own = make_admin(Role.Code.SECRETARY, person=join_request.person)
        response = admin_client(own).post(reverse(APPROVE, args=[join_request.pk]))
        assert response.status_code == 303
        assert not Member.objects.exists()
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING
        (attempt,) = entries(services.OWN_MEMBER_REJECTED, join_request)
        assert attempt.actor_account == own
        assert attempt.details == {"operation": "approve_join"}

    def test_own_readmission_is_rejected_and_recorded(self, make_admin, secretary):
        member = left_member(by=secretary)
        join_request = readmission_request(member)
        own = make_admin(Role.Code.SECRETARY, person=member.person)
        response = admin_client(own).post(
            reverse(APPROVE, args=[join_request.pk]), {"identitat_comprovada": "1"}
        )
        assert response.status_code == 303
        member.refresh_from_db()
        assert member.status == S.LEFT
        assert MemberStatusChange.objects.filter(member=member).count() == 1
        assert len(entries(services.OWN_MEMBER_REJECTED, join_request)) == 1

    def test_own_rejection_is_rejected_and_recorded(self, make_admin):
        join_request = a_request()
        own = make_admin(Role.Code.SECRETARY, person=join_request.person)
        admin_client(own).post(reverse(REJECT, args=[join_request.pk]), {"motiu": REASON})
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING
        (attempt,) = entries(services.OWN_MEMBER_REJECTED, join_request)
        assert attempt.details == {"operation": "reject_join"}

    def test_service_rejects_own_request(self, make_admin):
        join_request = a_request()
        own = make_admin(Role.Code.ADMINISTRATOR, person=join_request.person)
        with pytest.raises(OwnMemberChange):
            admissions.approve_join(join_request, by=own)


# --- Pantalla: permisos per rol (059) i per camp (C1, C2) ----------------------------------


@pytest.mark.django_db
class TestScreen:
    @pytest.mark.parametrize("role", P3A_ROLES)
    def test_roles_with_p3a_see_the_list(self, make_admin, role):
        a_request(a_person("Visible", "Persona"))
        response = admin_client(make_admin(role)).get(reverse(LIST))
        assert response.status_code == 200
        assert "Visible Persona" in response.content.decode()

    @pytest.mark.parametrize("role", NO_ROLES)
    def test_other_roles_get_not_found(self, make_admin, role):
        join_request = a_request()
        client = admin_client(make_admin(role))
        assert client.get(reverse(LIST)).status_code == 404
        assert client.post(reverse(APPROVE, args=[join_request.pk])).status_code == 404
        assert (
            client.post(reverse(REJECT, args=[join_request.pk]), {"motiu": REASON}).status_code
            == 404
        )
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING

    def test_personal_session_gets_no_access(self, personal_account, client):
        client.force_login(personal_account)
        assert client.get(reverse(LIST)).status_code in (302, 404)

    def test_p3a_without_p3_sees_the_list_but_cannot_resolve(self, make_admin):
        RolePermission.objects.filter(
            role__code="treasurer", permission_code=admissions.APPROVE_PERMISSION
        ).delete()
        join_request = a_request()
        client = admin_client(make_admin(Role.Code.TREASURER))
        page = client.get(reverse(LIST)).content.decode()
        assert "Aprova l'alta" not in page and "Rebutja" not in page
        assert client.post(reverse(APPROVE, args=[join_request.pk])).status_code == 404
        assert not Member.objects.exists()

    def test_birth_date_and_documents_only_with_c1_and_c2(self, make_admin):
        person = a_person("Doc", "Sentinella")
        a_request(
            person,
            birth=datetime.date(2010, 7, 7),
            guardian_first_name="Tutor",
            guardian_last_name="Sentinella",
            guardian_id_document_type="dni",
            guardian_id_document_number="GUARDDOC1",
        )
        secretary_page = admin_client(make_admin("secretary")).get(reverse(LIST)).content.decode()
        assert "07/07/2010" in secretary_page
        assert person.id_document_number in secretary_page
        assert "GUARDDOC1" in secretary_page
        for role in ("treasurer", "president"):
            page = admin_client(make_admin(role)).get(reverse(LIST)).content.decode()
            assert "07/07/2010" not in page and "2010-07-07" not in page
            assert person.id_document_number not in page
            assert "GUARDDOC1" not in page
            assert "Tutor Sentinella" in page

    def test_own_request_shows_no_buttons(self, make_admin):
        join_request = a_request()
        own = make_admin(Role.Code.SECRETARY, person=join_request.person)
        page = admin_client(own).get(reverse(LIST)).content.decode()
        assert "És la teva sol·licitud" in page
        assert reverse(APPROVE, args=[join_request.pk]) not in page

    def test_only_pending_joins_are_listed(self, secretary):
        a_request(a_person("Pendent", "Llistada"))
        a_request(a_person("Rebutjada", "Amagada"), status=R.REJECTED, resolution_reason=REASON)
        page = admin_client(secretary).get(reverse(LIST)).content.decode()
        assert "Pendent Llistada" in page
        assert "Rebutjada Amagada" not in page

    def test_approve_through_the_screen(self, secretary):
        set_counter(12)
        join_request = a_request()
        client = admin_client(secretary)
        response = client.post(reverse(APPROVE, args=[join_request.pk]))
        assert response.status_code == 303
        assert Member.objects.get().member_number == 13
        assert "número 13" in client.get(reverse(LIST)).content.decode()

    def test_identity_checkbox_is_needed_through_the_screen(self, secretary):
        existing = a_person()
        join_request = a_request(
            existing, warning=[{"match": "document", "person_id": existing.pk}]
        )
        client = admin_client(secretary)
        assert "identitat_comprovada" in client.get(reverse(LIST)).content.decode()
        client.post(reverse(APPROVE, args=[join_request.pk]))
        assert not Member.objects.exists()
        client.post(reverse(APPROVE, args=[join_request.pk]), {"identitat_comprovada": "1"})
        assert Member.objects.get().person == existing

    def test_reject_through_the_screen_needs_a_reason(self, secretary):
        join_request = a_request()
        client = admin_client(secretary)
        client.post(reverse(REJECT, args=[join_request.pk]), {"motiu": " "})
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING
        client.post(reverse(REJECT, args=[join_request.pk]), {"motiu": REASON})
        join_request.refresh_from_db()
        assert join_request.status == R.REJECTED

    def test_resolving_needs_post_and_csrf(self, secretary):
        join_request = a_request()
        assert (
            admin_client(secretary).get(reverse(APPROVE, args=[join_request.pk])).status_code == 405
        )
        response = admin_client(secretary, csrf=True).post(reverse(APPROVE, args=[join_request.pk]))
        assert response.status_code == 403
        assert not Member.objects.exists()

    def test_change_type_request_is_not_found_on_the_join_routes(self, secretary):
        member = Member.objects.create(
            person=a_person(), member_number=3, type=a_type(), joined_on=datetime.date(2020, 1, 1)
        )
        change = MemberRequest.objects.create(
            kind=MemberRequest.Kind.CHANGE_TYPE,
            person=member.person,
            member=member,
            requested_type=a_type("full"),
            channel=MemberRequest.Channel.WEB,
        )
        assert admin_client(secretary).post(reverse(APPROVE, args=[change.pk])).status_code == 404

    def test_admin_home_links_to_the_list_only_with_p3a(self, make_admin):
        link = reverse(LIST)
        home = reverse("administration:home")
        assert link in admin_client(make_admin("secretary")).get(home).content.decode()
        assert link not in admin_client(make_admin("instructor")).get(home).content.decode()


# --- CA-M01-45: el tresorer (059) ------------------------------------------------------------


@pytest.mark.django_db
class TestCaM0145Treasurer:
    """CA-M01-45: el tresorer aprova o rebutja una alta; hi veu «major d'edat» o «menor d'edat»
    en lloc de la data de naixement, sense el document; la seva, rebutjada i registrada."""

    def test_ca_m01_45_age_band_instead_of_birth_date_and_no_document(self, make_admin):
        adult = a_request(a_person("Adulta", "Franja"))
        minor = minor_request(document=True)
        page = admin_client(make_admin("treasurer")).get(reverse(LIST)).content.decode()
        assert page.count("Major d&#x27;edat") == 1
        assert page.count("Menor d&#x27;edat") == 1
        for day in (ADULT, MINOR):
            assert day.strftime("%d/%m/%Y") not in page and day.isoformat() not in page
        for document in (adult.person.id_document_number, minor.person.id_document_number):
            assert document not in page
        assert minor.guardian_id_document_number not in page
        # Amb C1, la data i no la franja.
        secretary_page = admin_client(make_admin("secretary")).get(reverse(LIST)).content.decode()
        assert ADULT.strftime("%d/%m/%Y") in secretary_page
        assert "Major d&#x27;edat" not in secretary_page

    def test_ca_m01_45_treasurer_approves(self, make_admin):
        join_request = a_request()
        client = admin_client(make_admin("treasurer"))
        response = client.post(reverse(APPROVE, args=[join_request.pk]))
        assert response.status_code == 303
        assert Member.objects.get().person == join_request.person

    def test_ca_m01_45_treasurer_rejects(self, make_admin):
        join_request = a_request()
        client = admin_client(make_admin("treasurer"))
        client.post(reverse(REJECT, args=[join_request.pk]), {"motiu": REASON})
        join_request.refresh_from_db()
        assert join_request.status == R.REJECTED
        assert not Member.objects.exists()

    @pytest.mark.parametrize(("route", "data"), [(APPROVE, {}), (REJECT, {"motiu": REASON})])
    def test_ca_m01_45_own_request_is_rejected_and_recorded(self, make_admin, route, data):
        join_request = a_request()
        own = make_admin("treasurer", person=join_request.person)
        response = admin_client(own).post(reverse(route, args=[join_request.pk]), data)
        assert response.status_code == 303
        join_request.refresh_from_db()
        assert join_request.status == R.PENDING
        assert not Member.objects.exists()
        (attempt,) = entries(services.OWN_MEMBER_REJECTED, join_request)
        assert attempt.actor_account == own


# --- Quota: el càrrec ha de ser de la persona del soci i de tipus «quota» (M01-6) -----------


@pytest.mark.django_db
class TestAnnualFeeCharge:
    def member(self):
        return Member.objects.create(
            person=a_person(), member_number=8, type=a_type(), joined_on=datetime.date(2020, 1, 1)
        )

    def charge(self, person, kind=Charge.Kind.FEE):
        return charges.create_charge(
            person,
            kind=kind,
            amount_cents=3500,
            concept="Càrrec de proves",
            origin="members",
            by=audit.system("proves-t-m01-14"),
            department=None if kind == Charge.Kind.FEE else _general(),
        )

    def fee(self, member, charge):
        return AnnualFee.objects.create(
            member=member,
            period=2027,
            kind="annual",
            charge=charge,
            due_on=datetime.date(2027, 1, 31),
        )

    def test_charge_of_another_person_is_rejected(self):
        member = self.member()
        with pytest.raises(ValidationError):
            self.fee(member, self.charge(a_person("Altra", "Persona")))
        assert not AnnualFee.objects.exists()

    def test_charge_that_is_not_a_fee_is_rejected(self):
        member = self.member()
        with pytest.raises(ValidationError):
            self.fee(member, self.charge(member.person, kind=Charge.Kind.ENROLMENT))
        assert not AnnualFee.objects.exists()

    def test_own_fee_charge_is_accepted(self):
        member = self.member()
        assert self.fee(member, self.charge(member.person)).pk

    def test_bulk_create_and_update_are_refused(self):
        member = self.member()
        fee = self.fee(member, self.charge(member.person))
        with pytest.raises(ValidationError):
            AnnualFee.objects.bulk_create([AnnualFee(member=member, period=2028, kind="annual")])
        with pytest.raises(ValidationError):
            AnnualFee.objects.filter(pk=fee.pk).update(charge=self.charge(a_person("Altra", "P")))


def _general():
    from apps.core.models import Department

    return Department.objects.get(name=Department.GENERAL)


# --- CA-M01-04: aprovacions simultànies ----------------------------------------------------


def _committed_admin(role):
    person = Person.objects.create(first_name="Gestor", origin="in_person")
    account = Account.objects.create_admin(person, f"gestor{person.pk}")
    AccountRole.objects.create(admin_account=account, role=Role.objects.get(code=role))
    return account


class TestConcurrentApprovals(CommittedDataTestCase):
    def setUp(self):
        self._counter = counter()

    def tearDown(self):
        set_counter(self._counter)  # fila de la migració: es deixa com estava (conftest.py)

    def test_two_simultaneous_approvals_get_different_consecutive_numbers(self):
        set_counter(200)
        secretary = _committed_admin(Role.Code.SECRETARY)
        first, second = a_request(), a_request(a_person("Clara", "Bosch"))

        numbers = run_together(
            [
                lambda: admissions.approve_join(first, by=secretary).member_number,
                lambda: admissions.approve_join(second, by=secretary).member_number,
            ]
        )

        assert sorted(numbers) == [201, 202]
        assert counter() == 202

    def test_the_same_request_approved_twice_at_once_creates_one_member(self):
        set_counter(300)
        secretary = _committed_admin(Role.Code.SECRETARY)
        join_request = a_request()

        def approve():
            try:
                admissions.approve_join(join_request, by=secretary)
                return "fet"
            except ValidationError:
                return "rebutjat"

        assert sorted(run_together([approve, approve])) == ["fet", "rebutjat"]
        assert Member.objects.filter(person=join_request.person).count() == 1
        assert counter() == 301
