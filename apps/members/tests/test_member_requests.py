"""Canvi de tipus i baixa: sol·licitud del soci i resolució de l'administració (T-M01-17;
P-M01-B i P-M01-C; P3a, P7 i P14; 064; CA-M01-05, CA-M01-08, CA-M01-24 per a P3a i P7,
CA-M01-47; conflicte d'interès als punts d'entrada). Només dades inventades.

No es prova cap creació de quotes: aquesta tasca no en crea (l'aprovació del canvi de tipus, amb
el suplement, està desconnectada; P-54 i RN-M01-15).
"""

import time
from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Person, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import member_requests as mr
from apps.members.fee_rules import local_today
from apps.members.models import (
    AnnualFee,
    Member,
    MemberRequest,
    MembershipType,
    MemberStatusChange,
)
from apps.members.services import OWN_MEMBER_REJECTED, STATUS_CHANGED
from conftest import PASSWORD

CHANGE = "members:change_type"
LEAVE = "members:leave"
LIST = "administration:member_requests"
DETAIL = "administration:member_request_detail"
CREATE = "administration:member_leave_create"
RESOLVERS = ["secretary", "treasurer", "administrator", "president"]  # P3a i P7 (059)
NO_ACCESS = ["board", "instructor", "courses_manager", "equipment_manager", "history_department"]
K, RS = MemberRequest.Kind, MemberRequest.Status


def admin_client(account):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_ADMIN
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def personal_client(account):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_PERSONAL
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


_numbers = iter(range(500, 10_000))


def make_member(first="Marta", *, type_code="supporter", status="active", **fields):
    person = Person.objects.create(
        first_name=first,
        last_name="Prova",
        origin=Person.Origin.WEB,
        contact_email=f"{first.lower()}@example.org",
    )
    return Member.objects.create(
        person=person,
        member_number=next(_numbers),
        type=MembershipType.objects.get(code=type_code),
        status=status,
        joined_on=date(2019, 3, 12),
        **fields,
    )


def account_for(member):
    account = Account.objects.create_personal(member.person, member.person.contact_email, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


def add_unpaid_fee(member):
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=3500,
        concept="Quota de prova",
        origin="members",
        by=audit.system("proves"),
    )
    AnnualFee.objects.create(
        member=member,
        period=2026,
        kind=AnnualFee.Kind.ANNUAL,
        charge=charge,
        due_on=date(2026, 1, 1),
    )


def leave_request(member, reason="Em trasllado a una altra ciutat"):
    return MemberRequest.objects.create(
        kind=K.LEAVE,
        person=member.person,
        member=member,
        request_reason=reason,
        channel=MemberRequest.Channel.WEB,
    )


def change_request(member):
    return MemberRequest.objects.create(
        kind=K.CHANGE_TYPE,
        person=member.person,
        member=member,
        requested_type=MembershipType.objects.get(code="full"),
        channel=MemberRequest.Channel.WEB,
    )


def entries(action):
    return AuditEntry.objects.filter(action=action)


@pytest.fixture
def marta(db):
    member = make_member()
    return member, account_for(member)


# --- Àrea del soci: accés -------------------------------------------------------------------


@pytest.mark.parametrize("name", [CHANGE, LEAVE])
def test_without_session_goes_to_the_personal_login(client, db, name):
    response = client.get(reverse(name))
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))


@pytest.mark.parametrize("name", [CHANGE, LEAVE])
def test_without_member_is_not_found(personal_account, name):
    client = personal_client(personal_account)
    assert client.get(reverse(name)).status_code == 404
    assert client.post(reverse(name), {"reason": "x", "confirm": "on"}).status_code == 404
    assert not MemberRequest.objects.exists()


def test_navigation_links_to_both_pages_for_a_member(marta):
    html = personal_client(marta[1]).get(reverse("members:profile")).content.decode()
    assert reverse(CHANGE) in html
    assert reverse(LEAVE) in html


# --- Canvi a ple dret (P-M01-B, pas 1) ------------------------------------------------------


def test_active_supporter_requests_the_change_without_any_charge(marta):
    member, account = marta
    client = personal_client(account)
    page = client.get(reverse(CHANGE)).content.decode()
    assert "Pendent de determinar per la secretaria" in page
    response = client.post(reverse(CHANGE))
    assert response.status_code == 302
    created = MemberRequest.objects.get()
    assert (created.kind, created.status, created.channel) == (K.CHANGE_TYPE, RS.PENDING, "web")
    assert created.member == member and created.requested_type.code == "full"
    entry = entries(mr.REQUEST_CREATED).get()
    assert entry.actor_account == account
    assert entry.details == {"kind": "change_type", "channel": "web"}
    # Cap càrrec ni quota: l'import l'escriu qui aprova (RN-M01-15) i l'aprovació no hi és.
    assert not Charge.objects.exists() and not AnnualFee.objects.exists()
    member.refresh_from_db()
    assert member.type.code == "supporter"


@pytest.mark.parametrize(
    "type_code,status",
    [("full", "active"), ("supporter", "unpaid"), ("supporter", "pending"), ("supporter", "left")],
)
def test_only_an_active_supporter_can_request_the_change(db, type_code, status):
    extra = {"left_on": date(2025, 1, 1)} if status == "left" else {}
    member = make_member(type_code=type_code, status=status, **extra)
    client = personal_client(account_for(member))
    response = client.post(reverse(CHANGE))
    assert response.status_code == 200
    assert not MemberRequest.objects.exists()
    assert not entries(mr.REQUEST_CREATED).exists()


def test_inactive_full_type_cannot_be_requested(marta):
    MembershipType.objects.filter(code="full").update(active=False)
    personal_client(marta[1]).post(reverse(CHANGE))
    assert not MemberRequest.objects.exists()


def test_only_one_pending_change_per_person(marta):
    client = personal_client(marta[1])
    client.post(reverse(CHANGE))
    response = client.post(reverse(CHANGE))
    assert "Ja hi ha una sol·licitud pendent" in response.content.decode()
    assert MemberRequest.objects.count() == 1


def test_service_rejects_someone_elses_or_an_admin_account(marta, make_admin):  # noqa: F811
    member, _account = marta
    other = account_for(make_member("Pere"))
    with pytest.raises(Http404):
        mr.request_type_change(member, by=other)
    with pytest.raises(Http404):
        mr.request_type_change(member, by=make_admin("secretary"))
    with pytest.raises(Http404):
        mr.request_leave(member, by=other, reason="Motiu")
    assert not MemberRequest.objects.exists()


# --- Baixa demanada pel soci (P-M01-C, pas 1) -----------------------------------------------


@pytest.mark.parametrize(
    "data",
    [{"confirm": "on"}, {"reason": "   ", "confirm": "on"}, {"reason": "Em trasllado"}],
    ids=["sense-motiu", "motiu-buit", "sense-confirmacio"],
)
def test_leave_needs_reason_and_confirmation(marta, data):
    response = personal_client(marta[1]).post(reverse(LEAVE), data)
    assert response.status_code == 200
    assert not MemberRequest.objects.exists()


def test_member_requests_the_leave_with_reason(marta):
    member, account = marta
    response = personal_client(account).post(
        reverse(LEAVE), {"reason": " Em trasllado ", "confirm": "on"}
    )
    assert response.status_code == 302
    created = MemberRequest.objects.get()
    assert (created.kind, created.status, created.channel) == (K.LEAVE, RS.PENDING, "web")
    assert created.request_reason == "Em trasllado"
    assert entries(mr.REQUEST_CREATED).get().details == {"kind": "leave", "channel": "web"}
    member.refresh_from_db()
    assert member.status == "active"  # demanar-la no la fa efectiva


def test_left_member_cannot_request_another_leave(db):
    member = make_member(status="left", left_on=date(2025, 1, 1))
    client = personal_client(account_for(member))
    assert "Ja ets de baixa" in client.get(reverse(LEAVE)).content.decode()
    client.post(reverse(LEAVE), {"reason": "Motiu", "confirm": "on"})
    assert not MemberRequest.objects.exists()


def test_only_one_pending_leave_per_person(marta):
    leave_request(marta[0])
    client = personal_client(marta[1])
    assert "Ja tens una sol·licitud de baixa pendent" in client.get(reverse(LEAVE)).content.decode()
    client.post(reverse(LEAVE), {"reason": "Motiu", "confirm": "on"})
    assert MemberRequest.objects.count() == 1


# --- Administració: permisos (059; CA-M01-24 per a P3a i P7) -------------------------------


@pytest.mark.parametrize("role", RESOLVERS)
def test_p3a_and_p7_roles_see_and_resolve(make_admin, marta, role):  # noqa: F811
    request = change_request(marta[0])
    client = admin_client(make_admin(role))
    assert client.get(reverse(LIST)).status_code == 200
    page = client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    assert 'value="reject"' in page
    response = client.post(reverse(DETAIL, args=[request.pk]), {"action": "reject", "reason": "No"})
    assert response.status_code == 302
    request.refresh_from_db()
    assert request.status == RS.REJECTED


@pytest.mark.parametrize("role", [*NO_ACCESS, None])
def test_other_roles_get_not_found(make_admin, marta, role):  # noqa: F811
    request = leave_request(marta[0])
    client = admin_client(make_admin(role) if role else make_admin())
    assert client.get(reverse(LIST)).status_code == 404
    assert client.get(reverse(DETAIL, args=[request.pk])).status_code == 404
    data = {"action": "approve", "effective_on": local_today().isoformat()}
    assert client.post(reverse(DETAIL, args=[request.pk]), data).status_code == 404
    assert client.get(reverse(CREATE, args=[marta[0].pk])).status_code == 404
    request.refresh_from_db()
    assert request.status == RS.PENDING


def test_permissions_are_data_without_p7_only_reading(make_admin, marta):  # noqa: F811
    RolePermission.objects.filter(
        role__code="secretary", permission_code=mr.RESOLVE_PERMISSION
    ).delete()
    request = leave_request(marta[0])
    client = admin_client(make_admin("secretary"))
    page = client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    assert 'value="approve"' not in page and 'value="reject"' not in page
    response = client.post(reverse(DETAIL, args=[request.pk]), {"action": "reject", "reason": "No"})
    assert response.status_code == 404
    assert client.get(reverse(CREATE, args=[marta[0].pk])).status_code == 404
    request.refresh_from_db()
    assert request.status == RS.PENDING


def test_personal_session_does_not_reach_the_admin_screens(marta):
    client = personal_client(marta[1])
    response = client.get(reverse(LIST))
    assert response.status_code in (302, 404)
    assert "Sol·licituds" not in response.content.decode()


def test_join_requests_are_not_here(make_admin, marta):  # noqa: F811
    join = MemberRequest.objects.create(
        kind=K.JOIN,
        person=marta[0].person,
        member=marta[0],
        requested_type=marta[0].type,
        channel=MemberRequest.Channel.WEB,
        status=RS.APPROVED,
    )
    client = admin_client(make_admin("secretary"))
    assert client.get(reverse(DETAIL, args=[join.pk])).status_code == 404
    with pytest.raises(Http404):
        mr.reject(join, by=make_admin("secretary"), reason="No")


def test_list_shows_pending_without_identity_data(make_admin, marta):  # noqa: F811
    member = marta[0]
    Person.objects.filter(pk=member.person_id).update(
        id_document_type=Person.DocumentType.DNI,
        id_document_number="SENTINELLADOC",
        address="Carrer Sentinella 9",
    )
    change_request(member)
    leave_request(make_member("Pere"))
    page = admin_client(make_admin("treasurer")).get(reverse(LIST)).content.decode()
    assert "Canvis de tipus (1)" in page and "Baixes (1)" in page
    assert "SENTINELLADOC" not in page and "Carrer Sentinella" not in page


# --- Rebutjar (064; CA-M01-05, CA-M01-47) ---------------------------------------------------


def test_reject_needs_reason(make_admin, marta):  # noqa: F811
    request = leave_request(marta[0])
    client = admin_client(make_admin("secretary"))
    response = client.post(reverse(DETAIL, args=[request.pk]), {"action": "reject", "reason": " "})
    assert response.status_code == 200
    request.refresh_from_db()
    assert request.status == RS.PENDING
    with pytest.raises(ValidationError):
        mr.reject(request, by=make_admin("secretary"), reason="  ")


def test_rejected_leave_keeps_both_reasons_and_the_member(make_admin, marta):  # noqa: F811
    member = marta[0]
    request = leave_request(member, reason="Motiu del soci")
    secretary = make_admin("secretary")
    mr.reject(request, by=secretary, reason="Motiu de la junta")
    request.refresh_from_db()
    assert request.request_reason == "Motiu del soci"
    assert request.resolution_reason == "Motiu de la junta"
    assert (request.status, request.resolved_by) == (RS.REJECTED, secretary)
    assert request.resolved_at is not None and request.effective_on is None
    entry = entries(mr.REQUEST_RESOLVED).get()
    assert (entry.field, entry.old_value, entry.new_value) == ("status", "pending", "rejected")
    assert entry.reason == "Motiu de la junta" and entry.actor_account == secretary
    member.refresh_from_db()
    assert member.status == "active" and not member.status_changes.exists()


def test_rejected_change_does_not_touch_the_member(make_admin, marta):  # noqa: F811
    member = marta[0]
    mr.reject(change_request(member), by=make_admin("president"), reason="No")
    member.refresh_from_db()
    assert member.type.code == "supporter" and not member.status_changes.exists()


def test_a_resolved_request_cannot_be_resolved_again(make_admin, marta):  # noqa: F811
    request = leave_request(marta[0])
    secretary = make_admin("secretary")
    mr.reject(request, by=secretary, reason="No")
    with pytest.raises(ValidationError):
        mr.reject(request, by=secretary, reason="Altra vegada")
    with pytest.raises(ValidationError):
        mr.approve_leave(request, by=secretary, effective_on=local_today())
    assert entries(mr.REQUEST_RESOLVED).count() == 1


# --- Validar una baixa (P-M01-C, passos 2 i 3; CA-M01-08) -----------------------------------


def test_approve_leave_changes_status_with_history_audit_and_email(make_admin, marta):  # noqa: F811
    member = marta[0]
    request = leave_request(member, reason="Em trasllado")
    secretary = make_admin("secretary")
    day = local_today() - timedelta(days=3)
    response = admin_client(secretary).post(
        reverse(DETAIL, args=[request.pk]),
        {"action": "approve", "effective_on": day.isoformat(), "reason": "Acta 12"},
    )
    assert response.status_code == 302
    member.refresh_from_db()
    assert (member.status, member.left_on) == ("left", day)
    change = MemberStatusChange.objects.get(member=member)
    assert (change.from_status, change.to_status, change.effective_on) == ("active", "left", day)
    assert change.reason == "Em trasllado" and change.actor_account == secretary
    status_entry = entries(STATUS_CHANGED).get(field="status")
    assert (status_entry.old_value, status_entry.new_value) == ("active", "left")
    request.refresh_from_db()
    assert (request.status, request.effective_on, request.resolved_by) == (
        RS.APPROVED,
        day,
        secretary,
    )
    assert request.resolution_reason == "Acta 12"
    assert entries(mr.REQUEST_RESOLVED).filter(field="status", new_value="approved").exists()
    email = OutgoingEmail.objects.get()
    assert (email.template, email.to_address) == (mr.LEAVE_EMAIL, "marta@example.org")
    assert day.strftime("%d/%m/%Y") in email.body_text


@pytest.mark.parametrize("status", ["pending", "unpaid"])
def test_pending_or_unpaid_member_can_also_leave(make_admin, db, status):  # noqa: F811
    member = make_member(status=status)
    mr.approve_leave(leave_request(member), by=make_admin("secretary"), effective_on=local_today())
    member.refresh_from_db()
    assert member.status == "left"


def test_future_effective_date_is_rejected_and_nothing_changes(make_admin, marta):  # noqa: F811
    member = marta[0]
    request = leave_request(member)
    client = admin_client(make_admin("secretary"))
    tomorrow = (local_today() + timedelta(days=1)).isoformat()
    response = client.post(
        reverse(DETAIL, args=[request.pk]), {"action": "approve", "effective_on": tomorrow}
    )
    assert response.status_code == 200
    request.refresh_from_db()
    member.refresh_from_db()
    assert request.status == RS.PENDING and member.status == "active"
    assert not MemberStatusChange.objects.exists() and not OutgoingEmail.objects.exists()


def test_effective_date_before_joining_is_rejected(make_admin, marta):  # noqa: F811
    with pytest.raises(ValidationError):
        mr.approve_leave(
            leave_request(marta[0]), by=make_admin("secretary"), effective_on=date(2018, 1, 1)
        )
    assert not MemberStatusChange.objects.exists()


def test_leave_with_unpaid_fees_is_blocked_pending_decision(make_admin, marta):  # noqa: F811
    member = marta[0]
    add_unpaid_fee(member)
    request = leave_request(member)
    with pytest.raises(ValidationError, match="quotes pendents"):
        mr.approve_leave(request, by=make_admin("secretary"), effective_on=local_today())
    member.refresh_from_db()
    request.refresh_from_db()
    assert member.status == "active" and request.status == RS.PENDING
    assert AnnualFee.objects.get().charge.status == Charge.Status.PENDING  # cap anul·lació


def test_approving_a_type_change_is_disconnected(make_admin, marta):  # noqa: F811
    member = marta[0]
    request = change_request(member)
    client = admin_client(make_admin("secretary"))
    page = client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    assert 'value="approve"' not in page
    response = client.post(
        reverse(DETAIL, args=[request.pk]),
        {"action": "approve", "effective_on": local_today().isoformat()},
    )
    assert response.status_code == 200
    request.refresh_from_db()
    member.refresh_from_db()
    assert request.status == RS.PENDING and member.type.code == "supporter"
    assert not AnnualFee.objects.exists() and not Charge.objects.exists()


# --- Conflicte d'interès als punts d'entrada (S-M01-22) -------------------------------------


@pytest.mark.parametrize(
    "kind,data",
    [
        ("leave", {"action": "approve", "effective_on": "TODAY"}),
        ("leave", {"action": "reject", "reason": "No"}),
        ("change", {"action": "reject", "reason": "No"}),
    ],
)
def test_own_request_cannot_be_resolved_and_the_attempt_is_recorded(
    make_admin,  # noqa: F811
    marta,
    kind,
    data,
):
    member = marta[0]
    request = leave_request(member) if kind == "leave" else change_request(member)
    own_admin = make_admin("secretary", person=member.person)
    client = admin_client(own_admin)
    assert (
        "És la teva sol·licitud" in client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    )
    data = {k: local_today().isoformat() if v == "TODAY" else v for k, v in data.items()}
    response = client.post(reverse(DETAIL, args=[request.pk]), data)
    assert response.status_code == 403
    request.refresh_from_db()
    member.refresh_from_db()
    assert request.status == RS.PENDING
    assert (member.status, member.type.code) == ("active", "supporter")
    assert not member.status_changes.exists()
    attempt = entries(OWN_MEMBER_REJECTED).get()
    assert attempt.actor_account == own_admin and attempt.target_id == str(member.pk)


# --- Baixa creada per la secretaria per decisió de la junta (P-M01-C, pas 1) ----------------


def test_secretary_creates_a_leave_by_board_decision(make_admin, marta):  # noqa: F811
    member = marta[0]
    client = admin_client(make_admin("secretary"))
    assert client.get(reverse(CREATE, args=[member.pk])).status_code == 200
    assert client.post(reverse(CREATE, args=[member.pk]), {"reason": " "}).status_code == 200
    assert not MemberRequest.objects.exists()
    response = client.post(reverse(CREATE, args=[member.pk]), {"reason": "Acta de la junta 3"})
    created = MemberRequest.objects.get()
    assert response["Location"] == reverse(DETAIL, args=[created.pk])
    assert (created.kind, created.channel, created.status) == (K.LEAVE, "in_person", RS.PENDING)
    assert created.request_reason == "Acta de la junta 3"
    member.refresh_from_db()
    assert member.status == "active"


def test_unknown_member_or_request_is_not_found(make_admin, marta):  # noqa: F811
    client = admin_client(make_admin("secretary"))
    assert client.get(reverse(CREATE, args=[marta[0].pk + 999])).status_code == 404
    assert client.get(reverse(DETAIL, args=[999_999])).status_code == 404
