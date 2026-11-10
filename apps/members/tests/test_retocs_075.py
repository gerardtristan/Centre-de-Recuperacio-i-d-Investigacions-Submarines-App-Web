"""Retocs de la 075 (tanda del 10/11/2026): RN-M01-81 a 84, CA-M01-81 a 86.

- T-M01-16: reautenticació per demanar el canvi del correu d'entrada (CA-M01-81) i sessions en
  confirmar-lo (CA-M01-82).
- T-M01-17: P7a, anul·lar el suplement vençut (CA-M01-83); «Crea una baixa» amb P4 (CA-M01-84);
  quotes del resum de la baixa només amb P10 (CA-M01-85).
- T-M01-27: el secret TOTP de prova no val sense DEBUG (CA-M01-86, a).
- T-M01-14: casella del document només amb C2 (CA-M01-86, b).

Només dades inventades.
"""

import time
from datetime import timedelta

import pyotp
import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from apps.accounts import totp
from apps.accounts.models import TotpDevice
from apps.accounts.security import AREA_PERSONAL, WRONG_CODE, WRONG_PASSWORD
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.accounts.tests.test_personal_totp import code_for, with_totp
from apps.core import audit
from apps.core.crypto import encrypt
from apps.core.models import AuditEntry, Charge, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import admissions, fees
from apps.members import member_requests as mr
from apps.members.models import AnnualFee, MemberRequest
from apps.members.tests.test_admissions import a_person, a_request, minor_request
from apps.members.tests.test_member_requests import (
    _approved_change,
    add_unpaid_fee,
    admin_client,
    leave_request,
    marta,  # noqa: F401 (fixture)
    travel_to,
)
from apps.members.tests.test_personal_area_074 import CHANGE_TEMPLATE, link_in, open_and_confirm
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

PROFILE = "members:profile"
CHANGE_EMAIL = "members:change_email"
NEW = "nova.adreca@example.org"
NOT_IT = "no-es-aquesta"  # una contrasenya que no és la del compte
DETAIL = "administration:member_request_detail"
CREATE = "administration:member_leave_create"
REASON = "No l'ha pagat (motiu inventat de proves)"


def personal_client(account):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_PERSONAL
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def ask(client, **data):
    return client.post(reverse(CHANGE_EMAIL), {"new_email": NEW, **data})


def failed_count(account):
    account.refresh_from_db()
    return account.failed_login_count


def session_is_valid(client):
    # Una sessió tancada va a l'entrada o a «La sessió ha caducat» (401), mai al perfil.
    return client.get(reverse(PROFILE)).status_code == 200


# --- CA-M01-81: reautenticació per demanar el canvi de correu ---------------------------------


class TestCaM0181:
    @pytest.mark.parametrize("password", ["", NOT_IT])
    def test_ca_m01_81_without_or_with_a_wrong_password_sends_nothing_and_counts(
        self, personal_account, password
    ):
        response = ask(personal_client(personal_account), password=password)
        assert response.status_code == 200
        assert response.context["email_form"].errors["password"] == [str(WRONG_PASSWORD)]
        assert escape(str(WRONG_PASSWORD)) in response.content.decode()
        assert not OutgoingEmail.objects.filter(template=CHANGE_TEMPLATE).exists()
        assert failed_count(personal_account) == 1
        assert AuditEntry.objects.filter(
            action=audit.Action.LOGIN_FAILED, target_id=str(personal_account.pk)
        ).exists()
        assert not AuditEntry.objects.filter(action=audit.Action.EMAIL_LINK_SENT).exists()

    def test_ca_m01_81_with_totp_a_wrong_code_sends_nothing_and_counts(self, personal_account):
        device = with_totp(personal_account)
        client = personal_client(personal_account)
        assert "code" in client.get(reverse(PROFILE)).context["email_form"].fields
        response = ask(client, password=PASSWORD, code="000000")
        assert response.context["email_form"].errors["code"] == [str(WRONG_CODE)]
        assert not OutgoingEmail.objects.filter(template=CHANGE_TEMPLATE).exists()
        assert failed_count(personal_account) == 1
        assert ask(client, password=PASSWORD, code=code_for(device)).status_code == 302
        assert OutgoingEmail.objects.get(template=CHANGE_TEMPLATE).to_address == NEW

    def test_ca_m01_81_right_password_sends_the_link(self, personal_account):
        client = personal_client(personal_account)
        assert "code" not in client.get(reverse(PROFILE)).context["email_form"].fields
        response = ask(client, password=PASSWORD)
        assert response.status_code == 302 and response["Location"] == reverse(PROFILE)
        assert OutgoingEmail.objects.get(template=CHANGE_TEMPLATE).to_address == NEW
        assert failed_count(personal_account) == 0


# --- CA-M01-82: sessions en confirmar el correu nou -------------------------------------------


class TestCaM0182:
    def test_ca_m01_82_confirming_from_a_session_keeps_it_and_ends_the_other(
        self, personal_account
    ):
        first, second = personal_client(personal_account), personal_client(personal_account)
        ask(first, password=PASSWORD)
        _page, done = open_and_confirm(
            link_in(OutgoingEmail.objects.get(template=CHANGE_TEMPLATE)), client=first
        )
        assert done.context["state"] == "done"
        assert session_is_valid(first)
        assert not session_is_valid(second)

    def test_ca_m01_82_confirming_without_a_session_ends_them_all(self, personal_account):
        first, second = personal_client(personal_account), personal_client(personal_account)
        ask(first, password=PASSWORD)
        _page, done = open_and_confirm(link_in(OutgoingEmail.objects.get(template=CHANGE_TEMPLATE)))
        assert done.context["state"] == "done"
        assert not session_is_valid(first)
        assert not session_is_valid(second)

    def test_ca_m01_82_a_session_of_another_account_is_not_kept_for_this_one(
        self,
        personal_account,
        make_admin,  # noqa: F811
    ):
        """La sessió que confirma és d'un altre compte: les del compte que canvia es tanquen."""
        own = personal_client(personal_account)
        ask(own, password=PASSWORD)
        other = admin_client(make_admin("secretary"))
        _page, done = open_and_confirm(
            link_in(OutgoingEmail.objects.get(template=CHANGE_TEMPLATE)), client=other
        )
        assert done.context["state"] == "done"
        assert not session_is_valid(own)


# --- CA-M01-83: P7a, anul·lar el suplement vençut ---------------------------------------------


@pytest.fixture
def overdue(make_admin, marta, monkeypatch):  # noqa: F811
    """Un canvi a ple dret aprovat amb el suplement vençut i sense pagar."""
    request = _approved_change(marta[0], make_admin("secretary"))
    travel_to(monkeypatch, request.supplement_fee.due_on + timedelta(days=1))
    return request


def charge_status(request):
    return AnnualFee.objects.get(pk=request.supplement_fee_id).charge.status


class TestCaM0183:
    def test_ca_m01_83_secretary_cancels_the_overdue_supplement_with_reason(
        self,
        make_admin,  # noqa: F811
        overdue,
    ):
        secretary = make_admin("secretary")
        client = admin_client(secretary)
        url = reverse(DETAIL, args=[overdue.pk])
        assert 'value="cancel_supplement"' in client.get(url).content.decode()
        assert client.post(url, {"action": "cancel_supplement", "reason": " "}).status_code == 200
        assert charge_status(overdue) == Charge.Status.PENDING
        response = client.post(url, {"action": "cancel_supplement", "reason": REASON})
        assert response.status_code == 302
        charge = AnnualFee.objects.get(pk=overdue.supplement_fee_id).charge
        assert (charge.status, charge.cancel_reason) == (Charge.Status.CANCELLED, REASON)
        entry = AuditEntry.objects.get(action=fees.CANCELLED_FEE)
        assert (entry.actor_account, entry.reason) == (secretary, REASON)
        assert entry.target_id == str(overdue.supplement_fee_id)

    def test_ca_m01_83_secretary_cannot_before_it_is_due(self, make_admin, marta):  # noqa: F811
        secretary = make_admin("secretary")
        request = _approved_change(marta[0], make_admin("secretary"))
        client = admin_client(secretary)
        url = reverse(DETAIL, args=[request.pk])
        assert 'value="cancel_supplement"' not in client.get(url).content.decode()
        response = client.post(url, {"action": "cancel_supplement", "reason": REASON})
        assert response.status_code == 200
        with pytest.raises(mr.RequestNotAllowed):
            mr.cancel_overdue_supplement(request, by=secretary, reason=REASON)
        assert charge_status(request) == Charge.Status.PENDING
        assert not AuditEntry.objects.filter(action=fees.CANCELLED_FEE).exists()

    def test_ca_m01_83_without_p7a_nor_p8_is_denied(self, make_admin, overdue):  # noqa: F811
        president = make_admin("president")  # P3a i P7, sense P7a ni P8
        client = admin_client(president)
        url = reverse(DETAIL, args=[overdue.pk])
        assert 'value="cancel_supplement"' not in client.get(url).content.decode()
        assert (
            client.post(url, {"action": "cancel_supplement", "reason": REASON}).status_code == 404
        )
        with pytest.raises(Http404):
            mr.cancel_overdue_supplement(overdue, by=president, reason=REASON)
        assert charge_status(overdue) == Charge.Status.PENDING

    def test_ca_m01_83_p7a_does_not_cancel_any_other_fee(self, make_admin, marta):  # noqa: F811
        """P7a no eixampla `fees.cancel_fee`: una quota anual (o el suplement per aquest camí)
        continua demanant P8; i una sol·licitud sense suplement no hi serveix."""
        member = marta[0]
        add_unpaid_fee(member)
        secretary = make_admin("secretary")
        fee = AnnualFee.objects.get(kind=AnnualFee.Kind.ANNUAL)
        with pytest.raises(Http404):
            fees.cancel_fee(fee, by=secretary, reason=REASON)
        with pytest.raises(Http404):
            mr.cancel_overdue_supplement(leave_request(member), by=secretary, reason=REASON)
        assert AnnualFee.objects.get(pk=fee.pk).charge.status == Charge.Status.PENDING

    def test_ca_m01_83_treasurer_still_can(self, make_admin, overdue):  # noqa: F811
        treasurer = make_admin("treasurer")
        mr.cancel_overdue_supplement(overdue, by=treasurer, reason=REASON)
        assert charge_status(overdue) == Charge.Status.CANCELLED
        entry = AuditEntry.objects.get(action=fees.CANCELLED_FEE)
        assert (entry.actor_account, entry.reason) == (treasurer, REASON)

    def test_ca_m01_83_p7a_is_only_the_secretarys_in_the_initial_matrix(self, make_admin):  # noqa: F811
        from apps.core.permissions import has_perm

        holders = {
            role
            for role in ("secretary", "treasurer", "administrator", "president", "board")
            if has_perm(make_admin(role), mr.CANCEL_SUPPLEMENT_PERMISSION, write=True)
        }
        assert holders == {"secretary"}


# --- CA-M01-84: «Crea una baixa» exigeix P4 ---------------------------------------------------


def test_ca_m01_84_create_leave_without_p4_is_not_found_and_hides_the_name(
    make_admin,  # noqa: F811
    marta,  # noqa: F811
):
    member = marta[0]
    president = admin_client(make_admin("president"))  # P7 amb edició, sense P4
    for response in (
        president.get(reverse(CREATE, args=[member.pk])),
        president.post(reverse(CREATE, args=[member.pk]), {"reason": "Acta de prova"}),
    ):
        assert response.status_code == 404
        assert member.person.first_name not in response.content.decode()
    assert not MemberRequest.objects.exists()
    page = admin_client(make_admin("secretary")).get(reverse(CREATE, args=[member.pk]))
    assert page.status_code == 200 and member.person.first_name in page.content.decode()


# --- CA-M01-85: quotes del resum de la baixa només amb P10 ------------------------------------


def test_ca_m01_85_unpaid_fees_of_a_leave_only_with_p10(make_admin, marta):  # noqa: F811
    member = marta[0]
    add_unpaid_fee(member)
    request = leave_request(member)
    url = reverse(DETAIL, args=[request.pk])

    without = admin_client(make_admin("president")).get(url)  # P7, sense P10
    page = without.content.decode()
    assert "unpaid_fees" not in without.context
    assert "35,00" not in page and "Quota de prova" not in page and "Quotes sense pagar" not in page
    assert "s'aplicaran les conseqüències de la baixa" in page

    with_p10 = admin_client(make_admin("secretary")).get(url)
    page = with_p10.content.decode()
    assert [amount for _fee, amount in with_p10.context["unpaid_fees"]] == ["35,00 €"]
    assert "Quota de prova" in page and "s'aplicaran les conseqüències de la baixa" not in page


# --- CA-M01-86 (a): el secret TOTP de prova no val sense DEBUG --------------------------------


def demo_device(account):
    return TotpDevice.objects.create(
        account=account,
        secret_encrypted=encrypt(totp.DEMO_TOTP_SECRET),
        confirmed_at=timezone.now(),
    )


@override_settings(DEBUG=False)
def test_ca_m01_86_without_debug_no_code_of_the_test_secret_is_valid(make_admin):  # noqa: F811
    device = demo_device(make_admin(totp=False))
    generator = pyotp.TOTP(totp.DEMO_TOTP_SECRET)
    for offset in (-30, 0, 30):
        assert not totp.verify_code(
            device, generator.at(timezone.now() + timedelta(seconds=offset))
        )
    device.refresh_from_db()
    assert device.last_used_step is None


@override_settings(DEBUG=True)
def test_ca_m01_86_with_debug_the_test_secret_works(make_admin):  # noqa: F811
    device = demo_device(make_admin(totp=False))
    assert totp.verify_code(device, pyotp.TOTP(totp.DEMO_TOTP_SECRET).now())


@override_settings(DEBUG=False)
def test_ca_m01_86_without_debug_other_secrets_are_unchanged(make_admin):  # noqa: F811
    device = TotpDevice.objects.get(account=make_admin())
    assert totp.verify_code(device, pyotp.TOTP(totp.secret_of(device)).now())


# --- CA-M01-86 (b): casella del document només amb C2 -----------------------------------------


def document_match():
    existing = a_person()
    return a_request(existing, warning=[{"match": "document", "person_id": existing.pk}])


CHECKS = {
    "guardian": (lambda: minor_request(document=True), "representant_comprovat"),
    "identity": (document_match, "identitat_comprovada"),
}


@pytest.mark.parametrize("case", sorted(CHECKS))
def test_ca_m01_86_without_c2_no_checkbox_and_cannot_approve(make_admin, case):  # noqa: F811
    build, box = CHECKS[case]
    join_request = build()
    treasurer = make_admin("treasurer")  # P3, sense C2
    client = admin_client(treasurer)
    page = client.get(reverse("administration:join_requests")).content.decode()
    assert f'name="{box}"' not in page
    assert escape("l'ha d'aprovar una persona que el pugui veure") in page
    client.post(reverse("administration:join_approve", args=[join_request.pk]), {box: "1"})
    join_request.refresh_from_db()
    assert join_request.status == MemberRequest.Status.PENDING
    with pytest.raises(ValidationError):
        admissions.approve_join(
            join_request, by=treasurer, identity_checked=True, guardian_checked=True
        )
    join_request.refresh_from_db()
    assert join_request.status == MemberRequest.Status.PENDING


@pytest.mark.parametrize("case", sorted(CHECKS))
def test_ca_m01_86_with_c2_the_checkbox_is_shown_and_approves(make_admin, case):  # noqa: F811
    build, box = CHECKS[case]
    join_request = build()
    client = admin_client(make_admin("secretary"))
    assert f'name="{box}"' in client.get(reverse("administration:join_requests")).content.decode()
    client.post(reverse("administration:join_approve", args=[join_request.pk]), {box: "1"})
    join_request.refresh_from_db()
    assert join_request.status == MemberRequest.Status.APPROVED


def test_ca_m01_86_a_join_without_the_check_is_unchanged_without_c2(make_admin):  # noqa: F811
    join_request = a_request()
    member = admissions.approve_join(join_request, by=make_admin("treasurer"))
    assert member.person == join_request.person
