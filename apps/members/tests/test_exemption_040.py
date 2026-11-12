"""Exempció puntual i anul·lació d'una quota (T-M01-40; RN-M01-72 i RN-M01-94; CA-M01-65 a 67;
072, quarta instrucció, punt 4; decisió 085, J-2 i G-2).

P22 («Eximir o anul·lar una quota», del Tresorer), motiu obligatori i reautenticació a la mateixa
petició. L'exempció anul·la el càrrec amb la categoria «exempció» i el període compta com a
resolt des del venciment de la quota fins al mateix dia de l'any següent. Només dades inventades.
"""

import datetime

import pyotp
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.urls import reverse

from apps.accounts import totp
from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL, WRONG_CODE, WRONG_PASSWORD
from apps.core import charges
from apps.core.models import AppendOnlyError, AuditEntry, Charge, Payment, RolePermission
from apps.core.permission_catalog import CATALOG
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees, roster, services, validity
from apps.members.fee_rules import local_today
from apps.members.models import (
    AnnualFee,
    FeeExemption,
    Member,
    MemberCard,
    MembershipType,
    MemberStatusChange,
)
from apps.members.tests.test_cards import add_fee, make_member, pay
from apps.members.tests.test_roster import admin_client
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

S = Member.Status
REASON = "Acord de la junta (motiu inventat)."
DETAIL = "administration:member_detail"
EXEMPT = "administration:member_fee_exempt"
CANCEL = "administration:member_fee_cancel"
P22 = "members.fees.exempt"


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin("treasurer")
    account.set_password(PASSWORD)
    account.save()
    return account


def fee_for(member, *, due_on=None, by=None):
    due_on = due_on or local_today()
    return fees.issue_annual_fee(
        member, period=due_on.year, due_on=due_on, by=by or services.audit.system("proves")
    )


def a_year_after(day):
    return validity.twelve_months_after(day)


def code_for(account):
    return pyotp.TOTP(totp.secret_of(account.totp_device)).now()


def form_data(account, **extra):
    return {"reason": REASON, "password": PASSWORD, "code": code_for(account), **extra}


CHARGE_FIELDS = ("status", "cancel_reason", "cancel_category")


def snapshot():
    return (
        list(Charge.objects.order_by("pk").values_list(*CHARGE_FIELDS)),
        list(Member.objects.order_by("pk").values_list("status", flat=True)),
        FeeExemption.objects.count(),
        MemberCard.objects.count(),
        Payment.objects.count(),
    )


# --- Permís ------------------------------------------------------------------------------------


def test_p22_is_only_of_the_treasurer_in_the_initial_matrix():
    permission = CATALOG[P22]
    assert dict(permission.initial) == {"treasurer": "all"}
    assert permission.touches_money and not permission.protected
    cells = RolePermission.objects.filter(permission_code=P22)
    assert [(c.role.code, c.scope) for c in cells] == [("treasurer", "all")]


# --- CA-M01-65 ---------------------------------------------------------------------------------


class TestExempt:
    def test_ca_m01_65_active_member_stays_active_with_a_valid_card(self, treasurer):
        member = make_member()
        due = local_today() - datetime.timedelta(days=10)  # data de renovació
        fee = fee_for(member, due_on=due)

        exemption = fees.exempt_fee(fee, by=treasurer, reason=f"  {REASON} ")

        fee.charge.refresh_from_db()
        assert fee.charge.status == Charge.Status.CANCELLED
        assert fee.charge.cancel_category == Charge.CancelCategory.EXEMPTION
        assert fee.charge.cancel_reason == REASON
        assert not Payment.objects.exists()  # mai un pagament de 0 €
        assert (exemption.starts_on, exemption.valid_until) == (due, a_year_after(due))
        assert exemption.granted_by == treasurer
        member.refresh_from_db()
        assert member.status == S.ACTIVE
        loaded = cards.load_member(member.pk)
        card = cards.active_card(loaded)
        assert cards.validity(loaded, card) == cards.CardValidity(True, a_year_after(due))
        entry = AuditEntry.objects.get(action=fees.EXEMPTED_FEE)
        assert entry.actor_account == treasurer
        assert entry.reason == REASON
        assert entry.target_id == str(fee.pk)
        assert entry.details == {
            "starts_on": due.isoformat(),
            "valid_until": a_year_after(due).isoformat(),
            "member_status": "active",
        }
        change = AuditEntry.objects.get(action="charges.status_changed", new_value="cancelled")
        assert change.details == {"category": "exemption"}

    def test_pending_member_becomes_active_with_a_card_from_the_approval_date(self, treasurer):
        member = make_member(status=S.PENDING)
        fee = fee_for(member)  # com en aprovar l'alta: venç el dia de l'aprovació

        fees.exempt_fee(fee, by=treasurer, reason=REASON)

        member.refresh_from_db()
        assert member.status == S.ACTIVE
        change = MemberStatusChange.objects.filter(member=member).latest("pk")
        assert (change.from_status, change.to_status) == (S.PENDING, S.ACTIVE)
        assert change.actor_account == treasurer
        loaded = cards.load_member(member.pk)
        validity_now = cards.validity(loaded, cards.active_card(loaded))
        assert validity_now == cards.CardValidity(True, a_year_after(local_today()))

    def test_unpaid_member_stays_unpaid(self, treasurer):
        # 040: l'impagat és una marca manual; l'exempció no la treu.
        member = make_member(status=S.UNPAID)
        fees.exempt_fee(fee_for(member), by=treasurer, reason=REASON)
        member.refresh_from_db()
        assert member.status == S.UNPAID
        assert not MemberCard.objects.exists()

    def test_fee_state_and_renewal_follow_the_exempted_period(self, treasurer):
        member = make_member()
        due = local_today()
        fees.exempt_fee(fee_for(member, due_on=due), by=treasurer, reason=REASON)
        until = a_year_after(due)
        loaded = cards.load_member(member.pk)
        assert roster.fee_state(loaded, due) == roster.FeeState(roster.WAIVED, until)
        assert roster.fee_state(loaded, until + datetime.timedelta(days=1)) is None
        # La renovació es genera per al final del període eximit, no abans.
        assert fees.generate_due_fees(until - datetime.timedelta(days=16)) == []
        (renewal,) = fees.generate_due_fees(until - datetime.timedelta(days=15))
        assert (renewal.member, renewal.due_on, renewal.period) == (member, until, until.year)

    def test_a_later_fee_of_the_same_period_undoes_the_exemption(self, treasurer):
        # RN-M01-72: es desfà creant una quota nova del mateix període (P-54, sortida E).
        member = make_member()
        due = local_today()
        fees.exempt_fee(fee_for(member, due_on=due), by=treasurer, reason=REASON)
        assert validity.valid_until(cards.load_member(member.pk)) == a_year_after(due)
        again = fee_for(member, due_on=due)
        assert again.sequence == 2
        loaded = cards.load_member(member.pk)
        assert validity.exempted_until(loaded) is None
        assert validity.valid_until(loaded) is None
        assert not cards.validity(loaded, cards.active_card(loaded)).valid

    def test_a_paid_period_is_not_shown_as_exempted(self, treasurer):
        member = make_member()
        pay(add_fee(member, period=local_today().year))  # pagada avui
        loaded = cards.load_member(member.pk)
        assert roster.fee_state(loaded).kind == roster.PAID_UNTIL


# --- CA-M01-66 i CA-M01-67 ---------------------------------------------------------------------


class TestRejected:
    @pytest.mark.parametrize("role", ["secretary", "administrator", "president", "instructor"])
    def test_ca_m01_66_without_the_permission_nothing_changes(self, make_admin, role):  # noqa: F811
        fee = fee_for(make_member())
        before = snapshot()
        with pytest.raises(Http404):
            fees.exempt_fee(fee, by=make_admin(role), reason=REASON)
        with pytest.raises(Http404):
            fees.cancel_fee(fee, by=make_admin(role), reason=REASON)
        assert snapshot() == before

    def test_ca_m01_66_a_personal_account_or_the_system_cannot(self, treasurer):
        member = make_member()
        fee = fee_for(member)
        personal = Account.objects.create_personal(member.person, "anna@example.org", PASSWORD)
        for by in (personal, services.audit.system("proves"), None):
            with pytest.raises(Http404):
                fees.exempt_fee(fee, by=by, reason=REASON)

    @pytest.mark.parametrize("reason", ["", "   ", None])
    def test_ca_m01_66_without_a_reason_nothing_changes(self, treasurer, reason):
        fee = fee_for(make_member())
        before = snapshot()
        with pytest.raises(ValidationError):
            fees.exempt_fee(fee, by=treasurer, reason=reason)
        assert snapshot() == before

    def test_ca_m01_67_a_paid_fee_is_rejected(self, treasurer):
        fee = fee_for(make_member())
        pay(fee)
        before = snapshot()
        with pytest.raises(ValidationError, match="devolució"):
            fees.exempt_fee(fee, by=treasurer, reason=REASON)
        assert snapshot() == before

    def test_a_returned_fee_waits_for_the_payments_module(self, treasurer):
        # RN-67 (spec 00): les transicions des de «retornat» són de la 05b (Q-22).
        fee = fee_for(make_member())
        Charge.objects.filter(pk=fee.charge_id).update(status=Charge.Status.RETURNED)
        before = snapshot()
        for service in (fees.exempt_fee, fees.cancel_fee):
            with pytest.raises(ValidationError, match="mòdul de cobraments"):
                service(fee, by=treasurer, reason=REASON)
        assert snapshot() == before

    def test_an_already_cancelled_fee_is_rejected(self, treasurer):
        fee = fee_for(make_member())
        fees.cancel_fee(fee, by=treasurer, reason=REASON)
        with pytest.raises(ValidationError):
            fees.exempt_fee(fee, by=treasurer, reason=REASON)
        assert not FeeExemption.objects.exists()

    def test_a_fee_cannot_be_exempted_twice(self, treasurer):
        fee = fee_for(make_member())
        fees.exempt_fee(fee, by=treasurer, reason=REASON)
        with pytest.raises(ValidationError):
            fees.exempt_fee(fee, by=treasurer, reason=REASON)
        assert FeeExemption.objects.count() == 1

    def test_a_supplement_is_not_exempted(self, treasurer):
        member = make_member()
        Member.objects.filter(pk=member.pk).update(
            type=MembershipType.objects.get(code="supporter")
        )
        member.refresh_from_db()
        supplement = fees.issue_type_change_supplement(
            member,
            MembershipType.objects.get(code="full"),
            period=local_today().year,
            due_on=local_today(),
            by=services.audit.system("proves"),
        )
        with pytest.raises(ValidationError, match="suplement"):
            fees.exempt_fee(supplement, by=treasurer, reason=REASON)

    def test_a_partly_paid_fee_is_not_exempted(self, treasurer):
        fee = fee_for(make_member())
        pay(fee, amount=3200)  # un termini: cap regla aprovada (P-61)
        with pytest.raises(ValidationError, match="a mitges"):
            fees.exempt_fee(fee, by=treasurer, reason=REASON)

    def test_a_member_who_left_is_not_exempted(self, treasurer):
        member = make_member()
        fee = fee_for(member)
        Member.objects.filter(pk=member.pk).update(status=S.LEFT, left_on=local_today())
        with pytest.raises(ValidationError, match="baixa"):
            fees.exempt_fee(fee, by=treasurer, reason=REASON)

    def test_a_period_that_is_already_over_is_not_exempted(self, treasurer):
        fee = fee_for(make_member(), due_on=local_today() - datetime.timedelta(days=400))
        before = snapshot()
        with pytest.raises(ValidationError, match="ja ha acabat"):
            fees.exempt_fee(fee, by=treasurer, reason=REASON)
        assert snapshot() == before

    def test_nobody_exempts_their_own_fee(self, treasurer):
        member = make_member()
        Member.objects.filter(pk=member.pk).update(person=treasurer.person)
        member.refresh_from_db()
        charge = charges.create_charge(
            treasurer.person,
            kind=Charge.Kind.FEE,
            amount_cents=9000,
            concept="Quota pròpia",
            origin="members",
            by=services.audit.system("proves"),
        )
        fee = AnnualFee.objects.create(
            member=member,
            period=local_today().year,
            kind="annual",
            charge=charge,
            due_on=local_today(),
        )
        with pytest.raises(services.OwnMemberChange):
            fees.exempt_fee(fee, by=treasurer, reason=REASON)
        assert AuditEntry.objects.filter(action=services.OWN_MEMBER_REJECTED).count() == 1
        assert not FeeExemption.objects.exists()


# --- Anul·lar (072, quarta instrucció, punt 4; 085, G-2) ---------------------------------------


def test_cancelling_gives_no_right(treasurer):
    member = make_member()
    fee = fee_for(member)
    fees.cancel_fee(fee, by=treasurer, reason=REASON)
    fee.charge.refresh_from_db()
    assert (fee.charge.status, fee.charge.cancel_category) == (Charge.Status.CANCELLED, "")
    assert not FeeExemption.objects.exists()
    assert validity.valid_until(cards.load_member(member.pk)) is None


# --- Estructura --------------------------------------------------------------------------------


def test_cancel_category_must_be_known(treasurer):
    fee = fee_for(make_member())
    with pytest.raises(ValidationError):
        charges.cancel(fee.charge, REASON, by=treasurer, category="regal")
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PENDING


def test_only_a_cancelled_charge_has_a_category():
    fee = fee_for(make_member())
    with pytest.raises(IntegrityError), transaction.atomic():
        Charge.objects.filter(pk=fee.charge_id).update(cancel_category="exemption")


def test_exemptions_are_append_only(treasurer):
    exemption = fees.exempt_fee(fee_for(make_member()), by=treasurer, reason=REASON)
    exemption.valid_until = exemption.valid_until + datetime.timedelta(days=365)
    with pytest.raises(AppendOnlyError):
        exemption.save()
    with pytest.raises(AppendOnlyError):
        exemption.delete()
    with pytest.raises(AppendOnlyError):
        FeeExemption.objects.all().delete()


# --- Pantalles ---------------------------------------------------------------------------------


class TestScreens:
    def test_the_member_page_lists_the_fees_and_offers_the_actions_only_with_p22(
        self,
        treasurer,
        make_admin,  # noqa: F811
    ):
        member = make_member()
        fee = fee_for(member)
        links = [reverse(name, args=[member.pk, fee.pk]) for name in (EXEMPT, CANCEL)]
        page = admin_client(treasurer).get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert 'id="quotes-titol"' in page
        assert all(link in page for link in links)
        # La secretaria veu les quotes (P10 de consulta) però cap acció.
        secretary = admin_client(make_admin("secretary"))
        page = secretary.get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert 'id="quotes-titol"' in page
        assert not any(link in page for link in links)
        for link in links:  # ni per URL directa ni amb una petició manipulada
            assert secretary.get(link).status_code == 404
            assert secretary.post(link, {"reason": REASON}).status_code == 404
        assert Charge.objects.get(pk=fee.charge_id).status == Charge.Status.PENDING

    def test_exempting_from_the_screen(self, treasurer):
        member = make_member(status=S.PENDING)
        fee = fee_for(member)
        client = admin_client(treasurer)
        url = reverse(EXEMPT, args=[member.pk, fee.pk])
        page = client.get(url).content.decode()
        assert "Eximeix la quota" in page and 'name="reason"' in page
        assert 'name="password"' in page and 'name="code"' in page

        response = client.post(url, form_data(treasurer))

        assert response.status_code == 303
        assert response["Location"] == reverse(DETAIL, args=[member.pk])
        member.refresh_from_db()
        assert member.status == S.ACTIVE
        page = client.get(response["Location"]).content.decode()
        assert "Quota eximida. El soci és actiu i té el carnet vigent." in page
        assert "Eximida fins al" in page
        assert url not in page  # ja no és pendent: cap acció

    @pytest.mark.parametrize(
        ("extra", "field", "message"),
        [
            ({"reason": ""}, "reason", "Cal el motiu."),
            ({"reason": "   "}, "reason", "Cal el motiu."),
            ({"password": ""}, "password", WRONG_PASSWORD),
            ({"code": "000000"}, "code", WRONG_CODE),
            ({"code": ""}, "code", WRONG_CODE),
        ],
    )
    def test_ca_m01_66_reason_password_and_code_are_all_required(
        self, treasurer, extra, field, message
    ):
        fee = fee_for(make_member())
        before = snapshot()
        for name in (EXEMPT, CANCEL):
            response = admin_client(treasurer).post(
                reverse(name, args=[fee.member_id, fee.pk]), form_data(treasurer, **extra)
            )
            assert response.status_code == 200
            assert response.context["form"].errors[field] == [str(message)]
        assert snapshot() == before

    def test_cancelling_from_the_screen(self, treasurer):
        member = make_member()
        fee = fee_for(member)
        client = admin_client(treasurer)
        response = client.post(reverse(CANCEL, args=[member.pk, fee.pk]), form_data(treasurer))
        assert response.status_code == 303
        fee.charge.refresh_from_db()
        assert (fee.charge.status, fee.charge.cancel_category) == ("cancelled", "")
        page = client.get(response["Location"]).content.decode()
        assert "Quota anul·lada." in page and "Anul·lada" in page

    def test_ca_m01_67_a_paid_fee_shows_no_form_and_a_post_changes_nothing(self, treasurer):
        fee = fee_for(make_member())
        pay(fee)
        client = admin_client(treasurer)
        url = reverse(EXEMPT, args=[fee.member_id, fee.pk])
        page = client.get(url).content.decode()
        assert '<form class="formulari"' not in page
        before = snapshot()
        response = client.post(url, form_data(treasurer))
        assert response.status_code == 200
        assert "devolució" in response.content.decode()
        assert snapshot() == before

    def test_the_fee_of_another_member_is_not_found(self, treasurer):
        fee = fee_for(make_member())
        other = make_member("Berta", number=1288, document="87654321X")
        for name in (EXEMPT, CANCEL):
            url = reverse(name, args=[other.pk, fee.pk])
            assert admin_client(treasurer).get(url).status_code == 404
            assert admin_client(treasurer).post(url, form_data(treasurer)).status_code == 404
        assert Charge.objects.get(pk=fee.charge_id).status == Charge.Status.PENDING

    def test_the_member_sees_the_fee_as_exempted(self, treasurer, login_as):
        member = make_member()
        fee = fee_for(member)
        fees.exempt_fee(fee, by=treasurer, reason=REASON)
        personal = Account.objects.create_personal(member.person, "anna@example.org", PASSWORD)
        personal.status = Account.Status.ACTIVE
        personal.save()
        page = login_as(personal, AREA_PERSONAL).get(reverse("members:fees")).content.decode()
        assert "Eximida fins al" in page  # l'estat general
        assert "Eximida</span>" in page  # la fila de la quota
        assert REASON not in page  # el motiu és intern
