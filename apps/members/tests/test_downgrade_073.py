"""Pas de ple dret a simpatitzant: sol·licitud, retirada i resolució (T-M01-42; 073 i 079;
RN-M01-73 i RN-M01-93; CA-M01-68, CA-M01-71 i CA-M01-106). El canvi de tipus en renovar i l'avís
previ són de la T-M01-43 i no es proven aquí. Només dades inventades.
"""

from datetime import date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.core import audit, charges
from apps.core.models import Charge, OutgoingEmail, Payment, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import fees
from apps.members import member_requests as mr
from apps.members.fee_rules import local_today
from apps.members.models import AnnualFee, MemberCard, MemberRequest, MembershipType
from apps.members.services import OWN_MEMBER_REJECTED

from .test_member_requests import (
    account_for,
    add_unpaid_fee,
    admin_client,
    change_request,
    entries,
    leave_request,
    make_member,
    personal_client,
)

CHANGE = "members:change_type"
WITHDRAW = "members:change_type_withdraw"
LIST = "administration:member_requests"
DETAIL = "administration:member_request_detail"
SEND = {"direction": "downgrade"}
CONFIRM = {"confirm": "on"}
K, RS = MemberRequest.Kind, MemberRequest.Status


@pytest.fixture
def pere(db):
    """Soci de ple dret actiu amb el seu compte personal."""
    member = make_member("Pere", type_code="full")
    return member, account_for(member)


def downgrade_request(member, status=RS.PENDING):
    return MemberRequest.objects.create(
        kind=K.CHANGE_TYPE,
        person=member.person,
        member=member,
        requested_type=MembershipType.objects.get(code="supporter"),
        channel=MemberRequest.Channel.WEB,
        status=status,
    )


def pay_annual_fee(member, paid_at):
    """Quota anual pagada: el «vàlid fins al» és el mateix dia de l'any següent (070)."""
    system = audit.system("proves")
    fee = fees.issue_annual_fee(member, period=paid_at.year, due_on=paid_at.date(), by=system)
    payment = Payment.objects.create(
        charge=fee.charge,
        method=Payment.Method.CARD,
        amount_cents=fee.charge.amount_cents,
        paid_at=paid_at,
    )
    charges.mark_paid(fee.charge, payment, origin="provider", by=system)
    return fee


def untouched(member):
    """Res no ha canviat al soci: tipus, estat, historial i carnet."""
    member.refresh_from_db()
    return (
        member.type.code == "full"
        and member.status == "active"
        and not member.status_changes.exists()
        and not MemberCard.objects.filter(member=member).exists()
    )


# --- CA-M01-68: el soci de ple dret veu la regla i envia la sol·licitud ---------------------


def test_ca_m01_68_active_full_member_sees_the_rule_and_can_send_the_request(pere):
    page = personal_client(pere[1]).get(reverse(CHANGE)).content.decode()
    assert "Actualment ets soci de ple dret" in page
    assert "en la pròxima renovació de la quota anual" in page
    assert "renovaràs com a simpatitzant, amb la quota d'aquest tipus" in page
    assert "cap devolució de la quota del període actual" in page
    assert 'name="direction" value="downgrade"' in page
    assert "Envia la sol·licitud" in page
    # La frase de l'avís previ surt des que l'avís existeix (T-M01-43).
    assert "T'avisarem abans de la renovació" in page
    assert "suplement" not in page.lower()


def test_ca_m01_68_sending_it_creates_no_charge_and_does_not_change_the_type(pere):
    member, account = pere
    client = personal_client(account)
    response = client.post(reverse(CHANGE), SEND)
    assert response.status_code == 302 and response["Location"] == reverse(CHANGE)
    created = MemberRequest.objects.get()
    assert (created.kind, created.status, created.channel) == (K.CHANGE_TYPE, RS.PENDING, "web")
    assert created.member == member and created.requested_type.code == "supporter"
    assert created.supplement_fee is None and created.effective_on is None
    entry = entries(mr.REQUEST_CREATED).get()
    assert entry.actor_account == account
    assert not Charge.objects.exists() and not AnnualFee.objects.exists()
    assert not OutgoingEmail.objects.exists()
    assert untouched(member)
    page = client.get(reverse(CHANGE)).content.decode()
    assert "Sol·licitud de pas a simpatitzant enviada." in page
    assert "Tens una sol·licitud pendent" in page
    assert reverse(WITHDRAW) in page
    assert 'name="direction"' not in page  # mentre és pendent, no se n'ofereix cap altra


def test_ca_m01_68_it_can_be_requested_at_any_moment_of_the_period(pere):
    # RN-M01-93, punt 3: també amb la renovació lluny o acabada de pagar.
    member, account = pere
    pay_annual_fee(member, timezone.now() - timedelta(days=3))
    assert mr.downgrade_problem(member) == ""
    mr.request_downgrade(member, by=account)
    assert MemberRequest.objects.filter(status=RS.PENDING).count() == 1


# --- CA-M01-71: qui no la pot enviar --------------------------------------------------------


@pytest.mark.parametrize(
    "type_code,status",
    [("supporter", "active"), ("full", "left"), ("full", "unpaid"), ("full", "pending")],
)
def test_ca_m01_71_only_an_active_full_member_can_send_it(db, type_code, status):
    extra = {"left_on": date(2025, 1, 1)} if status == "left" else {}
    member = make_member(type_code=type_code, status=status, **extra)
    account = account_for(member)
    client = personal_client(account)
    page = client.get(reverse(CHANGE)).content.decode()
    assert 'name="direction"' not in page
    response = client.post(reverse(CHANGE), SEND)  # petició manipulada: el formulari no hi és
    assert response.status_code == 200
    with pytest.raises(mr.RequestNotAllowed):
        mr.request_downgrade(member, by=account)
    assert not MemberRequest.objects.exists()
    assert not entries(mr.REQUEST_CREATED).exists()
    assert not Charge.objects.exists()
    member.refresh_from_db()
    assert (member.type.code, member.status) == (type_code, status)


def test_ca_m01_71_with_one_pending_another_cannot_be_sent(pere):
    client = personal_client(pere[1])
    client.post(reverse(CHANGE), SEND)
    response = client.post(reverse(CHANGE), SEND)
    assert response.status_code == 200
    assert "Ja hi ha una sol·licitud pendent" in response.content.decode()
    assert MemberRequest.objects.count() == 1
    assert entries(mr.REQUEST_CREATED).count() == 1


def test_ca_m01_71_with_one_accepted_another_cannot_be_sent(pere):
    member, account = pere
    downgrade_request(member, RS.APPROVED)
    response = personal_client(account).post(reverse(CHANGE), SEND)
    assert response.status_code == 200
    assert "Ja tens el pas a simpatitzant acceptat" in response.content.decode()
    assert MemberRequest.objects.count() == 1


def test_ca_m01_71_inactive_supporter_type_cannot_be_requested(pere):
    MembershipType.objects.filter(code="supporter").update(active=False)
    personal_client(pere[1]).post(reverse(CHANGE), SEND)
    assert not MemberRequest.objects.exists()


def test_ca_m01_71_the_service_rejects_someone_elses_or_an_admin_account(
    pere,
    make_admin,  # noqa: F811
):
    member = pere[0]
    other = account_for(make_member("Anna", type_code="full"))
    for account in (other, make_admin("secretary"), make_admin("secretary", person=member.person)):
        with pytest.raises(Http404):
            mr.request_downgrade(member, by=account)
        with pytest.raises(Http404):
            mr.withdraw_downgrade(member, by=account)
    assert not MemberRequest.objects.exists()


def test_ca_m01_71_a_full_member_still_cannot_ask_for_the_full_type(pere):
    # Sense `direction`, el formulari és el del canvi a ple dret: el servei el rebutja.
    response = personal_client(pere[1]).post(reverse(CHANGE))
    assert response.status_code == 200
    assert not MemberRequest.objects.exists()


# --- CA-M01-106: retirar-la mentre és pendent -----------------------------------------------


def test_ca_m01_106_withdrawing_needs_the_confirmation(pere):
    member, account = pere
    request = downgrade_request(member)
    response = personal_client(account).post(reverse(WITHDRAW))
    assert response.status_code == 200
    assert "Cal que marquis la confirmació." in response.content.decode()
    request.refresh_from_db()
    assert request.status == RS.PENDING
    assert not entries(mr.REQUEST_RESOLVED).exists()


def test_ca_m01_106_pending_request_is_withdrawn_with_audit_and_another_can_be_sent(pere):
    member, account = pere
    client = personal_client(account)
    client.post(reverse(CHANGE), SEND)
    first = MemberRequest.objects.get()
    response = client.post(reverse(WITHDRAW), CONFIRM)
    assert response.status_code == 302 and response["Location"] == reverse(CHANGE)
    first.refresh_from_db()
    assert (first.status, first.resolution_reason, first.resolved_by) == (
        RS.CANCELLED,
        "Retirada pel soci",
        account,
    )
    assert first.resolved_at is not None and first.effective_on is None
    entry = entries(mr.REQUEST_RESOLVED).get()
    assert (entry.field, entry.old_value, entry.new_value) == ("status", "pending", "cancelled")
    assert entry.actor_account == account and entry.target_id == str(first.pk)
    assert entry.reason == "Retirada pel soci"
    page = client.get(reverse(CHANGE)).content.decode()
    assert "Sol·licitud retirada." in page
    assert 'name="direction" value="downgrade"' in page  # en pot fer una altra
    assert client.post(reverse(CHANGE), SEND).status_code == 302
    assert MemberRequest.objects.filter(status=RS.PENDING).count() == 1
    assert MemberRequest.objects.count() == 2
    assert not Charge.objects.exists() and untouched(member)
    profile = client.get(reverse("members:profile")).content.decode()
    assert "Cancel·lada" in profile and "Pendent" in profile


def test_ca_m01_106_once_accepted_it_cannot_be_withdrawn(pere, make_admin):  # noqa: F811
    member, account = pere
    request = downgrade_request(member)
    mr.approve_type_change(request, by=make_admin("secretary"))
    client = personal_client(account)
    page = client.get(reverse(CHANGE)).content.decode()
    assert "Sol·licitud acceptada" in page
    assert "S'aplicarà en la pròxima renovació de la quota anual" in page
    assert "ja no es pot retirar" in page
    assert reverse(WITHDRAW) not in page and 'name="direction"' not in page
    response = client.post(reverse(WITHDRAW), CONFIRM)  # petició manipulada
    assert response.status_code == 200
    assert "Un cop acceptat, ja no es pot retirar." in response.content.decode()
    with pytest.raises(mr.RequestNotAllowed):
        mr.withdraw_downgrade(member, by=account)
    request.refresh_from_db()
    assert request.status == RS.APPROVED
    assert not entries(mr.REQUEST_RESOLVED).filter(new_value="cancelled").exists()


def test_ca_m01_106_a_rejected_one_cannot_be_withdrawn_and_another_can_be_sent(
    pere,
    make_admin,  # noqa: F811
):
    member, account = pere
    request = downgrade_request(member)
    mr.reject(request, by=make_admin("secretary"), reason="Prova inventada")
    client = personal_client(account)
    assert client.post(reverse(WITHDRAW), CONFIRM).status_code == 200
    request.refresh_from_db()
    assert request.status == RS.REJECTED
    assert client.post(reverse(CHANGE), SEND).status_code == 302
    assert MemberRequest.objects.filter(status=RS.PENDING).count() == 1


def test_ca_m01_106_it_is_the_only_request_the_member_can_withdraw(db):
    # El canvi a ple dret i la baixa no els retira el soci (RN-M01-93, punt 4; P-72 tancada).
    supporter = make_member("Marta")
    change = change_request(supporter)
    full = make_member("Pere", type_code="full")
    leave = leave_request(full)
    for member in (supporter, full):
        response = personal_client(account_for(member)).post(reverse(WITHDRAW), CONFIRM)
        assert response.status_code == 200
    change.refresh_from_db()
    leave.refresh_from_db()
    assert (change.status, leave.status) == (RS.PENDING, RS.PENDING)
    assert not entries(mr.REQUEST_RESOLVED).exists()


def test_withdraw_route_is_post_only_and_needs_the_personal_session_and_a_member(
    client, pere, personal_account
):
    assert personal_client(pere[1]).get(reverse(WITHDRAW)).status_code == 405
    response = client.post(reverse(WITHDRAW), CONFIRM)
    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))
    assert personal_client(personal_account).post(reverse(WITHDRAW), CONFIRM).status_code == 404


# --- Administració: «Sol·licituds» (P3a i P7; RN-M01-93, punt 2) ----------------------------


def test_list_and_detail_show_the_requested_type_and_the_renewal_date(
    pere,
    make_admin,  # noqa: F811
):
    member = pere[0]
    paid_at = timezone.make_aware(datetime(2026, 3, 10, 12, 0))
    pay_annual_fee(member, paid_at)
    request = downgrade_request(member)
    client = admin_client(make_admin("secretary"))
    listing = client.get(reverse(LIST)).content.decode()
    assert "Ple dret → Simpatitzant" in listing
    page = client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    assert "Tipus demanat" in page and "Simpatitzant" in page
    assert "Renovació en què s'aplicarà" in page
    assert "10/03/2027" in page  # el «vàlid fins al»: 12 mesos després del pagament (070)
    assert "no es crea cap càrrec ni cap suplement" in page
    assert "Accepta el pas a simpatitzant" in page
    assert "Import del suplement" not in page


def test_detail_without_valid_until_says_so_and_invents_no_date(
    pere,
    make_admin,  # noqa: F811
):
    request = downgrade_request(pere[0])
    page = admin_client(make_admin("secretary")).get(reverse(DETAIL, args=[request.pk]))
    assert "Sense data: el soci no té cap «vàlid fins al»." in page.content.decode()


def test_detail_with_a_passed_valid_until_says_so(pere, make_admin):  # noqa: F811
    member = pere[0]
    pay_annual_fee(member, timezone.make_aware(datetime(2024, 3, 10, 12, 0)))
    request = downgrade_request(member)
    page = admin_client(make_admin("secretary")).get(reverse(DETAIL, args=[request.pk]))
    assert "10/03/2025 (el «vàlid fins al» del soci ja ha passat)" in page.content.decode()


def test_renewal_date_is_only_shown_with_p10(pere, make_admin):  # noqa: F811
    # El «vàlid fins al» és l'estat de la quota (P10): el President resol amb P3a i P7, sense.
    member = pere[0]
    pay_annual_fee(member, timezone.make_aware(datetime(2026, 3, 10, 12, 0)))
    request = downgrade_request(member)
    page = admin_client(make_admin("president")).get(reverse(DETAIL, args=[request.pk]))
    html = page.content.decode()
    assert "10/03/2027" not in html
    assert "La data només la veu qui té permís per consultar les quotes." in html
    assert "Accepta el pas a simpatitzant" in html


def test_ca_m01_68_accepting_does_not_change_the_type_and_keeps_the_contract_for_t_m01_43(
    pere,
    make_admin,  # noqa: F811
):
    """RN-M01-93, punt 2: l'accepta la secretaria amb P7, sense càrrec ni suplement. El tipus
    no canvia: la T-M01-43 la trobarà amb `accepted_downgrade` (aprovada, cap a simpatitzant,
    amb `effective_on` buit) i hi escriurà la data en aplicar-la."""
    member = pere[0]
    fee = pay_annual_fee(member, timezone.now() - timedelta(days=30))
    request = downgrade_request(member)
    assert mr.accepted_downgrade(member) is None
    secretary = make_admin("secretary")
    client = admin_client(secretary)
    response = client.post(reverse(DETAIL, args=[request.pk]), {"action": "approve"})
    assert response.status_code == 302
    request.refresh_from_db()
    assert (request.status, request.resolved_by) == (RS.APPROVED, secretary)
    assert request.effective_on is None and request.supplement_fee is None
    assert request.applied_at is None
    assert mr.accepted_downgrade(member) == request
    # Cap càrrec nou, cap correu, i el soci igual: tipus, estat, historial i carnet.
    assert Charge.objects.count() == 1 and AnnualFee.objects.get() == fee
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PAID
    assert not OutgoingEmail.objects.exists()
    assert untouched(member)
    entry = entries(mr.REQUEST_RESOLVED).get()
    assert (entry.old_value, entry.new_value) == ("pending", "approved")
    assert entry.actor_account == secretary
    page = client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    assert "Pas a simpatitzant acceptat." in page
    assert 'value="approve"' not in page
    assert reverse(DETAIL, args=[request.pk]) not in client.get(reverse(LIST)).content.decode()
    # Quan la T-M01-43 l'apliqui hi escriurà la data efectiva, i deixarà de sortir.
    MemberRequest.objects.filter(pk=request.pk).update(effective_on=local_today())
    assert mr.accepted_downgrade(member) is None


def test_accepted_change_to_full_is_not_an_accepted_downgrade(db, make_admin):  # noqa: F811
    # El contracte no confon el canvi a ple dret aprovat i pendent de pagar amb el pas contrari.
    member = make_member("Marta")
    mr.approve_type_change(change_request(member), by=make_admin("secretary"))
    assert mr.accepted_downgrade(member) is None


def test_rejecting_needs_a_reason_and_changes_nothing(pere, make_admin):  # noqa: F811
    member = pere[0]
    request = downgrade_request(member)
    client = admin_client(make_admin("secretary"))
    response = client.post(reverse(DETAIL, args=[request.pk]), {"action": "reject"})
    assert "Escriu el motiu del rebuig." in response.content.decode()
    client.post(reverse(DETAIL, args=[request.pk]), {"action": "reject", "reason": "No escau"})
    request.refresh_from_db()
    assert (request.status, request.resolution_reason) == (RS.REJECTED, "No escau")
    assert mr.accepted_downgrade(member) is None
    assert untouched(member) and not Charge.objects.exists()


def test_unpaid_fee_does_not_create_any_supplement_when_accepting(
    pere,
    make_admin,  # noqa: F811
):
    # RN-M01-75 és del canvi a ple dret; acceptar el pas a simpatitzant no crea mai cap càrrec.
    member = pere[0]
    add_unpaid_fee(member)
    request = downgrade_request(member)
    assert mr.approve_type_change(request, by=make_admin("secretary")) is None
    assert Charge.objects.count() == 1
    assert not AnnualFee.objects.filter(kind=AnnualFee.Kind.TYPE_CHANGE_SUPPLEMENT).exists()


@pytest.mark.parametrize("status", ["unpaid", "left"])
def test_accepting_needs_an_active_member(db, make_admin, status):  # noqa: F811
    extra = {"left_on": date(2025, 1, 1)} if status == "left" else {}
    member = make_member("Pere", type_code="full", status=status, **extra)
    request = downgrade_request(member)
    with pytest.raises(ValidationError):
        mr.approve_type_change(request, by=make_admin("secretary"))
    request.refresh_from_db()
    assert request.status == RS.PENDING


def test_resolving_needs_p7_with_edit(pere, make_admin):  # noqa: F811
    request = downgrade_request(pere[0])
    for role in ("board", "instructor"):
        client = admin_client(make_admin(role))
        assert client.get(reverse(DETAIL, args=[request.pk])).status_code == 404
        assert (
            client.post(reverse(DETAIL, args=[request.pk]), {"action": "approve"}).status_code
            == 404
        )
    secretary = make_admin("secretary")
    RolePermission.objects.filter(
        role__code="secretary", permission_code=mr.RESOLVE_PERMISSION
    ).delete()
    client = admin_client(secretary)
    assert 'value="approve"' not in client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    assert client.post(reverse(DETAIL, args=[request.pk]), {"action": "approve"}).status_code == 404
    with pytest.raises(Http404):
        mr.approve_type_change(request, by=secretary)
    request.refresh_from_db()
    assert request.status == RS.PENDING


@pytest.mark.parametrize("data", [{"action": "approve"}, {"action": "reject", "reason": "No"}])
def test_own_downgrade_cannot_be_resolved_and_the_attempt_is_recorded(
    pere,
    make_admin,  # noqa: F811
    data,
):
    # S-M01-22: conflicte d'interès, com la resta de sol·licituds.
    member = pere[0]
    request = downgrade_request(member)
    own_admin = make_admin("secretary", person=member.person)
    client = admin_client(own_admin)
    page = client.get(reverse(DETAIL, args=[request.pk])).content.decode()
    assert "És la teva sol·licitud" in page and 'value="approve"' not in page
    assert client.post(reverse(DETAIL, args=[request.pk]), data).status_code == 403
    request.refresh_from_db()
    assert request.status == RS.PENDING
    attempt = entries(OWN_MEMBER_REJECTED).get()
    assert attempt.actor_account == own_admin and attempt.target_id == str(member.pk)


# --- Baixa i pas a simpatitzant (RN-M01-74) -------------------------------------------------


def test_ca_m01_73_validating_a_leave_cancels_the_pending_downgrade(
    pere,
    make_admin,  # noqa: F811
):
    # RN-M01-74: «el canvi de tipus pendent de la mateixa persona es cancel·la amb el motiu
    # "baixa"»; el pas a simpatitzant pendent és un canvi de tipus pendent.
    member, account = pere
    downgrade = downgrade_request(member)
    leave = leave_request(member)
    secretary = make_admin("secretary")
    page = admin_client(secretary).get(reverse(DETAIL, args=[leave.pk])).content.decode()
    assert "es cancel·la amb el motiu «baixa»" in page
    mr.approve_leave(leave, by=secretary, effective_on=local_today() + timedelta(days=5))
    downgrade.refresh_from_db()
    assert (downgrade.status, downgrade.resolution_reason) == (RS.CANCELLED, "Baixa")
    with pytest.raises(mr.RequestNotAllowed):
        mr.withdraw_downgrade(member, by=account)


def test_081_validating_a_leave_cancels_the_accepted_downgrade_keeping_its_history(
    pere,
    make_admin,  # noqa: F811
):
    """Decisió 081, punt 17 (opció A): en validar la baixa, el pas a simpatitzant ja acceptat es
    cancel·la amb el motiu «baixa». L'acceptació anterior queda al registre (qui i quan) i la
    renovació (`accepted_downgrade`, contracte de la T-M01-43) ja no el troba."""
    member, account = pere
    secretary = make_admin("secretary")
    downgrade = downgrade_request(member)
    mr.approve_type_change(downgrade, by=secretary)
    downgrade.refresh_from_db()
    accepted_at = downgrade.resolved_at
    assert mr.accepted_downgrade(member) == downgrade
    leave = leave_request(member)
    page = admin_client(secretary).get(reverse(DETAIL, args=[leave.pk])).content.decode()
    assert "El pas a simpatitzant acceptat d'aquest soci es cancel·la amb el motiu «baixa»." in page
    other = make_admin("secretary", username="secretaria.dos")
    mr.approve_leave(leave, by=other, effective_on=local_today() + timedelta(days=5))

    downgrade.refresh_from_db()
    assert (downgrade.status, downgrade.resolution_reason) == (RS.CANCELLED, "Baixa")
    assert downgrade.effective_on is None and downgrade.applied_at is None
    assert mr.accepted_downgrade(member) is None
    # Historial: l'acceptació i la cancel·lació, cadascuna amb el seu compte i el valor anterior.
    resolved = entries(mr.REQUEST_RESOLVED).filter(target_id=str(downgrade.pk)).order_by("pk")
    states = [(e.old_value, e.new_value, e.actor_account) for e in resolved if e.field == "status"]
    assert states == [("pending", "approved", secretary), ("approved", "cancelled", other)]
    fields = {
        e.field: (e.old_value, e.new_value, e.reason) for e in resolved if e.actor_account == other
    }
    assert fields["status"] == ("approved", "cancelled", "Baixa")
    assert fields["resolved_by"][:2] == (secretary.pk, other.pk)
    assert fields["resolved_at"][0] == accepted_at.isoformat()
    # El soci no el pot tornar a retirar ni demanar-ne un altre (ja és de baixa programada).
    with pytest.raises(mr.RequestNotAllowed):
        mr.withdraw_downgrade(member, by=account)


def test_081_a_downgrade_already_applied_is_not_touched_by_the_leave(
    pere,
    make_admin,  # noqa: F811
):
    # Un pas que la renovació ja ha aplicat (amb `effective_on`) és història: la baixa no el toca.
    member = pere[0]
    secretary = make_admin("secretary")
    downgrade = downgrade_request(member)
    mr.approve_type_change(downgrade, by=secretary)
    MemberRequest.objects.filter(pk=downgrade.pk).update(effective_on=local_today())
    mr.approve_leave(leave_request(member), by=secretary, effective_on=local_today())
    downgrade.refresh_from_db()
    assert downgrade.status == RS.APPROVED and downgrade.effective_on == local_today()
