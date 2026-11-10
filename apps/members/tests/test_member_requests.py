"""Canvi de tipus i baixa: sol·licitud del soci i resolució de l'administració (T-M01-17;
P-M01-B i P-M01-C; P3a, P7 i P14; 064; CA-M01-05, CA-M01-08, CA-M01-24 per a P3a i P7,
CA-M01-47; conflicte d'interès als punts d'entrada). Només dades inventades.

072: suplement del canvi a ple dret i quotes de la RN-M01-20. 074 (tanda del 10/11/2026): baixa
programada i tasca diària (CA-M01-72), canvi pendent cancel·lat (CA-M01-73), quota sense pagar
(CA-M01-74), venciment i anul·lació del suplement (CA-M01-75) i correccions de la revisió de
pantalles (C1 a C7).
"""

import time
from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Person, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees
from apps.members import member_requests as mr
from apps.members.fee_rules import local_today
from apps.members.models import (
    AnnualFee,
    Member,
    MemberCard,
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


def test_leave_confirmation_is_a_checkbox_inside_its_label(marta):
    # Patró `casella`: quadrat al costat del text i tota l'etiqueta clicable (revisió 09/11/2026).
    html = personal_client(marta[1]).get(reverse(LEAVE)).content.decode()
    assert '<label class="casella" for="id_confirm"><input type="checkbox" name="confirm"' in html


def test_admin_home_links_to_the_requests_only_with_p3a(make_admin, db):  # noqa: F811
    home = reverse("administration:home")
    assert reverse(LIST) in admin_client(make_admin("secretary")).get(home).content.decode()
    assert reverse(LIST) not in admin_client(make_admin("board")).get(home).content.decode()


def test_member_detail_links_to_create_a_leave_only_with_p7(make_admin, marta):  # noqa: F811
    member = marta[0]
    detail = reverse("administration:member_detail", args=[member.pk])
    create = reverse(CREATE, args=[member.pk])
    client = admin_client(make_admin("secretary"))
    assert create in client.get(detail).content.decode()
    leave_request(member)  # amb una baixa pendent, ja no s'ofereix
    assert create not in client.get(detail).content.decode()
    left = make_member("Pere", status="left")
    left_detail = reverse("administration:member_detail", args=[left.pk])
    assert reverse(CREATE, args=[left.pk]) not in client.get(left_detail).content.decode()
    RolePermission.objects.filter(
        role__code="secretary", permission_code=mr.RESOLVE_PERMISSION
    ).delete()
    other = make_member("Anna")
    other_detail = reverse("administration:member_detail", args=[other.pk])
    assert reverse(CREATE, args=[other.pk]) not in client.get(other_detail).content.decode()


# --- Canvi a ple dret (P-M01-B, pas 1) ------------------------------------------------------


def test_full_member_sees_the_downgrade_rule_without_a_promised_notice(db):
    # 073: el text explica la regla i no promet cap avís ni cap sol·licitud que encara no existeix.
    member = make_member(type_code="full")
    page = personal_client(account_for(member)).get(reverse(CHANGE)).content.decode()
    assert "efectiu en la pròxima renovació de la quota anual" in page
    assert "encara no està disponible" in page
    assert "avisarem" not in page.lower()
    assert 'method="post"' not in page


def test_active_supporter_requests_the_change_without_any_charge(marta):
    member, account = marta
    client = personal_client(account)
    page = client.get(reverse(CHANGE)).content.decode()
    assert "55,00 €" in page  # C2: el mateix càlcul que el càrrec (Q-049)
    assert "Pendent de determinar" not in page
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


def test_ca_m01_72_validating_without_date_is_a_field_error(make_admin, marta):  # noqa: F811
    """Prova b: sense data, error al camp i res no canvia."""
    member = marta[0]
    request = leave_request(member)
    client = admin_client(make_admin("secretary"))
    response = client.post(
        reverse(DETAIL, args=[request.pk]), {"action": "approve", "effective_on": ""}
    )
    assert response.status_code == 200
    assert response.context["form"].errors["effective_on"] == ["Escriu la data efectiva."]
    request.refresh_from_db()
    member.refresh_from_db()
    assert request.status == RS.PENDING and member.status == "active"


def test_effective_date_before_joining_is_rejected(make_admin, marta):  # noqa: F811
    with pytest.raises(ValidationError):
        mr.approve_leave(
            leave_request(marta[0]), by=make_admin("secretary"), effective_on=date(2018, 1, 1)
        )
    assert not MemberStatusChange.objects.exists()


def test_leave_cancels_later_unpaid_fees_and_keeps_earlier_ones(make_admin, marta):  # noqa: F811
    """Prova f: RN-M01-20 tal com és (Q-056 de la 072), carnet revocat amb registre (C4) i
    correu."""
    member = marta[0]
    MemberCard.objects.create(member=member, token_hash="c" * 64)
    add_unpaid_fee(member)  # venç l'1/1/2026: anterior a la baixa, es continua devent
    later = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=3500,
        concept="Quota posterior de prova",
        origin="members",
        by=audit.system("proves"),
    )
    AnnualFee.objects.create(
        member=member,
        period=2099,
        kind=AnnualFee.Kind.ANNUAL,
        charge=later,
        due_on=date(2099, 1, 1),
    )
    request = leave_request(member)
    secretary = make_admin("secretary")
    mr.approve_leave(request, by=secretary, effective_on=local_today())
    member.refresh_from_db()
    assert member.status == "left"
    statuses = dict(AnnualFee.objects.values_list("period", "charge__status"))
    assert statuses == {2026: Charge.Status.PENDING, 2099: Charge.Status.CANCELLED}
    later.refresh_from_db()
    assert "RN-M01-20" in later.cancel_reason
    card = MemberCard.objects.get(member=member)
    assert card.revoked_at is not None and "Baixa" in card.revoked_reason
    revoked = entries(cards.CARD_REVOKED).get()
    assert revoked.actor_account == secretary and revoked.old_value in (None, "")
    assert OutgoingEmail.objects.filter(template=mr.LEAVE_EMAIL).count() == 1


def test_ca_m01_75_approving_a_type_change_creates_the_supplement_and_applies_on_payment(
    make_admin,  # noqa: F811
    marta,  # noqa: F811
):
    """Prova e: Q-049 (55 €) i Q-050 (efectiu en pagar-lo) de la 072; venç d'aquí a una setmana
    (RN-M01-76)."""
    from apps.core.models import Payment
    from apps.members import services

    member = marta[0]
    request = change_request(member)
    client = admin_client(make_admin("secretary"))
    page = client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    assert 'value="approve"' in page
    assert "55,00 €" in page  # C2
    assert "es farà efectiu quan es confirmi el pagament del suplement" in page  # C7
    assert "Per aprovar el canvi, opcional." in page  # C7
    client.post(reverse(DETAIL, args=[request.pk]), {"action": "approve", "reason": "Acta 4"})
    request.refresh_from_db()
    member.refresh_from_db()
    assert request.status == RS.APPROVED and request.effective_on is None
    fee = request.supplement_fee
    assert fee.kind == AnnualFee.Kind.TYPE_CHANGE_SUPPLEMENT
    assert fee.charge.amount_cents == 9000 - 3500
    assert fee.due_on == local_today() + timedelta(days=7)
    assert request.resolution_reason == "Acta 4"
    assert member.type.code == "supporter"  # encara no: falta pagar-lo

    payment = Payment.objects.create(
        charge=fee.charge, method=Payment.Method.CARD, amount_cents=5500, paid_at=timezone.now()
    )
    charges.mark_paid(fee.charge, payment, origin="provider", by=audit.system("proves"))
    services.on_fee_paid(fee.pk)
    member.refresh_from_db()
    request.refresh_from_db()
    assert member.type.code == "full"
    assert request.effective_on == local_today()
    services.on_fee_paid(fee.pk)  # una segona notificació no fa res més
    assert member.status_changes.filter(to_type__code="full").count() == 1


def test_a_left_member_does_not_change_type(make_admin, marta):  # noqa: F811
    # Q-053 de la 072.
    member = marta[0]
    request = change_request(member)
    Member.objects.filter(pk=member.pk).update(status="left", left_on=local_today())
    with pytest.raises(ValidationError):
        mr.approve_type_change(request, by=make_admin("secretary"))
    assert not AnnualFee.objects.exists()


def test_cancelling_a_fee_needs_edit_permission(make_admin, marta):  # noqa: F811
    # Q-057 de la 072: amb permís d'edició de quotes (P8), amb motiu; amb només lectura, no.
    from apps.members import fees

    member = marta[0]
    add_unpaid_fee(member)
    fee = AnnualFee.objects.get()
    with pytest.raises(Http404):
        fees.cancel_fee(fee, by=make_admin("secretary"), reason="Prova")
    treasurer = make_admin("treasurer")
    with pytest.raises(ValidationError):
        fees.cancel_fee(fee, by=treasurer, reason="")
    fees.cancel_fee(fee, by=treasurer, reason="Perdonada per la junta (prova)")
    assert AnnualFee.objects.get().charge.status == Charge.Status.CANCELLED


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


# --- Tanda del 10/11/2026 (074): baixa programada i tasca diària (RN-M01-74) ----------------


def add_future_fee(member, due_on):
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=3500,
        concept="Quota futura de prova",
        origin="members",
        by=audit.system("proves"),
    )
    return AnnualFee.objects.create(
        member=member, period=due_on.year, kind=AnnualFee.Kind.ANNUAL, charge=charge, due_on=due_on
    )


def travel_to(monkeypatch, day):
    """Dates controlades: «avui» passa a ser `day` per a `local_today` i `_check_effective_on`."""
    monkeypatch.setattr(timezone, "localdate", lambda value=None, timezone=None: day)


def test_ca_m01_72_future_leave_is_scheduled_and_the_daily_task_applies_it_once(
    make_admin,  # noqa: F811
    marta,
    monkeypatch,
):
    """Proves b i c: data futura → programada; la tasca diària l'aplica aquell dia, una vegada."""
    member = marta[0]
    MemberCard.objects.create(member=member, token_hash="c" * 64)
    today = local_today()
    effective = today + timedelta(days=10)
    fee = add_future_fee(member, today + timedelta(days=40))
    request = leave_request(member)
    response = admin_client(make_admin("secretary")).post(
        reverse(DETAIL, args=[request.pk]),
        {"action": "approve", "effective_on": effective.isoformat()},
        follow=True,
    )
    page = response.content.decode()
    date = effective.strftime("%d/%m/%Y")
    assert f"Queda programada per al {date}" in page
    assert f"Programada per al {date}" in page
    request.refresh_from_db()
    member.refresh_from_db()
    assert (request.status, request.effective_on, request.applied_at) == (
        RS.APPROVED,
        effective,
        None,
    )
    assert mr.is_scheduled(request)
    assert member.status == "active" and member.left_on is None
    assert MemberCard.objects.get(member=member).revoked_at is None
    assert AnnualFee.objects.get(pk=fee.pk).charge.status == Charge.Status.PENDING
    assert not OutgoingEmail.objects.exists()

    assert mr.apply_due_leaves(effective - timedelta(days=1)) == []  # encara no
    travel_to(monkeypatch, effective)
    assert [r.pk for r in mr.apply_due_leaves()] == [request.pk]
    member.refresh_from_db()
    request.refresh_from_db()
    assert (member.status, member.left_on) == ("left", effective)
    assert request.applied_at is not None and not mr.is_scheduled(request)
    assert MemberCard.objects.get(member=member).revoked_at is not None
    assert AnnualFee.objects.get(pk=fee.pk).charge.status == Charge.Status.CANCELLED
    change = MemberStatusChange.objects.get(member=member)
    assert change.actor_account is None and change.effective_on == effective
    assert OutgoingEmail.objects.filter(template=mr.LEAVE_EMAIL).count() == 1

    # Idempotent: ni efectes ni correus nous.
    assert mr.apply_due_leaves() == []
    assert mr.apply_due_leaves(effective + timedelta(days=5)) == []
    assert OutgoingEmail.objects.count() == 1
    assert MemberStatusChange.objects.filter(member=member).count() == 1
    assert entries(cards.CARD_REVOKED).count() == 1


def test_ca_m01_72_the_daily_task_is_registered_on_the_queue():
    from apps.members import tasks

    assert tasks.daily_leaves.name == "members.daily_leaves"
    assert tasks.daily_leaves.queue == tasks.daily_fees.queue


def test_ca_m01_72_scheduled_leave_blocks_another_leave(make_admin, marta):  # noqa: F811
    """Prova d (en part): una baixa programada impedeix demanar-ne o crear-ne una altra."""
    member, account = marta
    mr.approve_leave(
        leave_request(member),
        by=make_admin("secretary"),
        effective_on=local_today() + timedelta(days=3),
    )
    client = personal_client(account)
    assert "Ja tens una baixa programada" in client.get(reverse(LEAVE)).content.decode()
    with pytest.raises(ValidationError):
        mr.request_leave(member, by=account, reason="Una altra")
    secretary = admin_client(make_admin("secretary"))
    detail = reverse("administration:member_detail", args=[member.pk])
    assert reverse(CREATE, args=[member.pk]) not in secretary.get(detail).content.decode()
    response = secretary.post(reverse(CREATE, args=[member.pk]), {"reason": "Acta 9"})
    assert "ja té una baixa programada" in response.content.decode()
    assert MemberRequest.objects.count() == 1


@pytest.mark.parametrize("case", ["read_only_p7", "own", "left", "pending"])
def test_create_leave_errors(make_admin, marta, case):  # noqa: F811
    """Prova d: errors de «Crea una baixa» (P7 sense edició, propi soci, soci de baixa i baixa
    pendent). No es crea res més."""
    from apps.core.permission_catalog import SCOPE_READ

    member = marta[0]
    if case == "own":
        account = make_admin("secretary", person=member.person)
    else:
        account = make_admin("secretary")
    if case == "read_only_p7":
        RolePermission.objects.filter(
            role__code="secretary", permission_code=mr.RESOLVE_PERMISSION
        ).update(scope=SCOPE_READ)
    if case == "left":
        Member.objects.filter(pk=member.pk).update(status="left", left_on=local_today())
    if case == "pending":
        leave_request(member)
    before = MemberRequest.objects.count()
    response = admin_client(account).post(reverse(CREATE, args=[member.pk]), {"reason": "Acta"})
    expected = {"read_only_p7": 404, "own": 403, "left": 200, "pending": 200}[case]
    assert response.status_code == expected
    assert MemberRequest.objects.count() == before
    if case == "own":
        assert entries(OWN_MEMBER_REJECTED).exists()


def test_ca_m01_73_validating_a_leave_cancels_the_pending_type_change(
    make_admin,  # noqa: F811
    marta,
):
    member = marta[0]
    change = change_request(member)
    leave = leave_request(member)
    secretary = make_admin("secretary")
    page = admin_client(secretary).get(reverse(DETAIL, args=[leave.pk])).content.decode()
    assert "es cancel·la amb el motiu «baixa»" in page
    mr.approve_leave(leave, by=secretary, effective_on=local_today() + timedelta(days=5))
    change.refresh_from_db()
    assert (change.status, change.resolution_reason, change.resolved_by) == (
        RS.CANCELLED,
        "Baixa",
        secretary,
    )
    assert (
        entries(mr.REQUEST_RESOLVED)
        .filter(target_id=str(change.pk), field="status", new_value="cancelled")
        .exists()
    )
    assert not AnnualFee.objects.exists()


def test_ca_m01_74_unpaid_fee_blocks_the_change_on_request_and_on_approval(
    make_admin,  # noqa: F811
    marta,
):
    member, account = marta
    add_unpaid_fee(member)
    client = personal_client(account)
    page = client.get(reverse(CHANGE)).content.decode()
    assert "Tens una quota sense pagar" in page and 'method="post"' not in page
    response = client.post(reverse(CHANGE))
    assert "Tens una quota sense pagar" in response.content.decode()
    assert not MemberRequest.objects.exists()

    request = change_request(member)  # demanada abans que es generés la quota
    response = admin_client(make_admin("secretary")).post(
        reverse(DETAIL, args=[request.pk]), {"action": "approve"}
    )
    assert response.status_code == 200
    assert "alguna quota sense pagar" in response.content.decode()
    request.refresh_from_db()
    assert request.status == RS.PENDING
    assert not AnnualFee.objects.filter(kind=AnnualFee.Kind.TYPE_CHANGE_SUPPLEMENT).exists()
    assert Charge.objects.count() == 1


def _approved_change(member, by):
    request = change_request(member)
    mr.approve_type_change(request, by=by)
    request.refresh_from_db()
    return request


def test_ca_m01_75_overdue_supplement_stays_alive_and_only_p7a_or_p8_edit_cancels_it(
    make_admin,  # noqa: F811
    marta,
    monkeypatch,
):
    member = marta[0]
    request = _approved_change(member, make_admin("secretary"))
    fee = request.supplement_fee
    treasurer = admin_client(make_admin("treasurer"))  # P3a i P8 amb edició
    url = reverse(DETAIL, args=[request.pk])
    data = {"action": "cancel_supplement", "reason": "No l'ha pagat (prova)"}

    # Abans del venciment: no s'ofereix i el servidor ho rebutja.
    page = treasurer.get(url).content.decode()
    assert "Pendent" in page and 'value="cancel_supplement"' not in page
    assert treasurer.post(url, data).status_code == 200
    assert AnnualFee.objects.get(pk=fee.pk).charge.status == Charge.Status.PENDING

    # Vençut: continua viu; les tasques diàries no l'anul·len.
    travel_to(monkeypatch, fee.due_on + timedelta(days=1))
    mr.apply_due_leaves()
    fees.generate_due_fees()
    assert AnnualFee.objects.get(pk=fee.pk).charge.status == Charge.Status.PENDING
    page = treasurer.get(url).content.decode()
    assert "Vençut" in page and 'value="cancel_supplement"' in page

    # Sense P7a ni P8 amb edició (el President de la configuració inicial; la secretaria té P7a
    # des de la 075, CA-M01-83): ni botó ni acció.
    president = admin_client(make_admin("president"))
    assert 'value="cancel_supplement"' not in president.get(url).content.decode()
    assert president.post(url, data).status_code == 404

    # Sense motiu: error.
    assert treasurer.post(url, {"action": "cancel_supplement", "reason": " "}).status_code == 200
    assert AnnualFee.objects.get(pk=fee.pk).charge.status == Charge.Status.PENDING

    response = treasurer.post(url, data, follow=True)
    assert "Suplement anul·lat." in response.content.decode()
    charge = AnnualFee.objects.get(pk=fee.pk).charge
    assert (charge.status, charge.cancel_reason) == (Charge.Status.CANCELLED, data["reason"])
    assert entries(fees.CANCELLED_FEE).get().reason == data["reason"]
    assert "Anul·lat" in treasurer.get(url).content.decode()


def test_ca_m01_75_own_overdue_supplement_cannot_be_cancelled(
    make_admin,  # noqa: F811
    marta,
    monkeypatch,
):
    member = marta[0]
    request = _approved_change(member, make_admin("secretary"))
    travel_to(monkeypatch, request.supplement_fee.due_on + timedelta(days=1))
    own = admin_client(make_admin("treasurer", person=member.person))
    response = own.post(
        reverse(DETAIL, args=[request.pk]), {"action": "cancel_supplement", "reason": "Prova"}
    )
    assert response.status_code == 403
    assert AnnualFee.objects.get(pk=request.supplement_fee_id).charge.status == "pending"
    assert entries(OWN_MEMBER_REJECTED).exists()


# --- Correccions de la revisió de pantalles (C1, C3, C5, C7) --------------------------------


def test_c1_initial_effective_date_is_iso(make_admin, marta):  # noqa: F811
    request = leave_request(marta[0])
    page = admin_client(make_admin("secretary")).get(reverse(DETAIL, args=[request.pk]))
    assert f'value="{local_today().isoformat()}"' in page.content.decode()


def test_c3_leave_detail_summarises_the_consequences(make_admin, marta):  # noqa: F811
    member = marta[0]
    add_unpaid_fee(member)
    request = leave_request(member)
    page = admin_client(make_admin("secretary")).get(reverse(DETAIL, args=[request.pk]))
    html = page.content.decode()
    assert "vencen després de la data efectiva s&#x27;anul·len" in html or (
        "vencen després de la data efectiva s'anul·len" in html
    )
    assert "el carnet es revoca" in html and "correu de confirmació" in html
    assert "01/01/2026" in html and "35,00 €" in html


def test_c3_personal_leave_page_explains_what_will_happen(marta):
    html = personal_client(marta[1]).get(reverse(LEAVE)).content.decode()
    for text in (
        "fixarà la data efectiva",
        "les continuaràs devent",
        "anul·laran",
        "deixarà de ser vàlid",
        "Mantindràs el compte personal",
    ):
        assert text in html


def test_c5_c7_requests_table_has_labels_and_a_neutral_link(make_admin, marta):  # noqa: F811
    leave_request(make_member("Arnau"))
    html = admin_client(make_admin("secretary")).get(reverse(LIST)).content.decode()
    for label in ("Soci", "Número", "Tipus", "Canal", "Enviada"):
        assert f'data-etiqueta="{label}"' in html
    assert "Obre la sol·licitud: Arnau Prova" in html
    assert "de Arnau" not in html
