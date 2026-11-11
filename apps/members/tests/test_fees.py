"""Quotes i impagats (T-M01-18; CA-M01-09 a l'entrada; HU-M01-12; RN-M01-09, decisió 040).

Fora d'aquestes proves, perquè depenen de decisions obertes i no s'han implementat: generar i
renovar quotes (CA-M01-10 i 11; P-54, P-61, P-29, P-57) i els recordatoris (RN-M01-14, S-M01-04).
La part del carnet de CA-M01-09 és de la T-M01-19 i la T-M01-20. Només dades inventades.
"""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core import audit, charges
from apps.core.models import Charge
from apps.members import services
from apps.members.models import AnnualFee, Member, MemberStatusChange
from apps.members.tests.test_admissions import (
    a_person,
    a_type,
    admin_client,
    entries,
    make_admin,  # noqa: F401 (fixture)
)

S = Member.Status
PAGE = "administration:fees"
MARK = "administration:fee_mark_unpaid"
UNMARK = "administration:fee_unmark_unpaid"
REASON = "Motiu inventat de proves"
P10_ROLES = ["secretary", "treasurer", "administrator"]
NO_P10_ROLES = ["president", "board", "instructor", "history_department"]
_numbers = iter(range(500, 10_000))


def a_member(status=S.ACTIVE, *, person=None, first="Laia"):
    return Member.objects.create(
        person=person or a_person(first, "Ferrer"),
        member_number=next(_numbers),
        type=a_type(),
        status=status,
        joined_on=datetime.date(2020, 1, 15),
    )


def with_pending_fee(member, due_on=datetime.date(2027, 1, 31)):
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=3500,
        concept="Quota de proves",
        origin="members",
        by=audit.system("proves-t-m01-18"),
    )
    AnnualFee.objects.create(
        member=member, period=due_on.year, kind="annual", charge=charge, due_on=due_on
    )
    return member


def today():
    return timezone.localdate().isoformat()


def post(client, name, member, **data):
    data.setdefault("data", today())
    return client.post(reverse(name, args=[member.pk]), data)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


# --- CA-M01-09 (part de l'entrada): motiu obligatori ---------------------------------------


@pytest.mark.django_db
class TestMarkUnpaid:
    def test_without_reason_is_rejected(self, treasurer):
        member = a_member()
        client = admin_client(treasurer)
        response = post(client, MARK, member, motiu="   ")
        assert response.status_code == 303
        member.refresh_from_db()
        assert member.status == S.ACTIVE
        assert not MemberStatusChange.objects.filter(member=member).exists()
        assert "Aquest canvi necessita un motiu." in client.get(reverse(PAGE)).content.decode()

    def test_with_reason_marks_unpaid_with_history_and_audit(self, treasurer):
        member = a_member()
        response = post(admin_client(treasurer), MARK, member, motiu=REASON)
        assert response.status_code == 303
        assert response["Location"] == reverse(PAGE)
        member.refresh_from_db()
        assert member.status == S.UNPAID
        change = MemberStatusChange.objects.get(member=member)
        assert (change.from_status, change.to_status) == (S.ACTIVE, S.UNPAID)
        assert change.reason == REASON
        assert change.actor_account == treasurer
        assert change.effective_on == timezone.localdate()
        (entry,) = entries(services.STATUS_CHANGED, member)
        assert entry.actor_account == treasurer

    def test_unmark_with_reason_returns_to_active(self, treasurer):
        member = a_member(S.UNPAID)
        post(admin_client(treasurer), UNMARK, member, motiu=REASON)
        member.refresh_from_db()
        assert member.status == S.ACTIVE
        assert MemberStatusChange.objects.get(member=member).reason == REASON

    def test_unmark_without_reason_is_rejected(self, treasurer):
        member = a_member(S.UNPAID)
        post(admin_client(treasurer), UNMARK, member, motiu="")
        member.refresh_from_db()
        assert member.status == S.UNPAID

    @pytest.mark.parametrize("value", ["", "no-és-una-data", "2026-02-30"])
    def test_invalid_date_is_rejected(self, treasurer, value):
        member = a_member()
        post(admin_client(treasurer), MARK, member, motiu=REASON, data=value)
        member.refresh_from_db()
        assert member.status == S.ACTIVE

    def test_future_date_is_rejected(self, treasurer):
        member = a_member()
        tomorrow = (timezone.localdate() + datetime.timedelta(days=1)).isoformat()
        post(admin_client(treasurer), MARK, member, motiu=REASON, data=tomorrow)
        member.refresh_from_db()
        assert member.status == S.ACTIVE

    def test_past_date_is_kept_in_the_history(self, treasurer):
        member = a_member()
        post(admin_client(treasurer), MARK, member, motiu=REASON, data="2026-01-10")
        change = MemberStatusChange.objects.get(member=member)
        assert change.effective_on == datetime.date(2026, 1, 10)

    @pytest.mark.parametrize(
        ("status", "name"),
        [(S.UNPAID, MARK), (S.ACTIVE, UNMARK), (S.PENDING, MARK), (S.LEFT, UNMARK)],
    )
    def test_transition_not_allowed_changes_nothing(self, treasurer, status, name):
        member = a_member(status)
        response = post(admin_client(treasurer), name, member, motiu=REASON)
        assert response.status_code == 303
        member.refresh_from_db()
        assert member.status == status
        assert not MemberStatusChange.objects.filter(member=member).exists()

    def test_unknown_member_is_not_found(self, treasurer):
        client = admin_client(treasurer)
        response = client.post(reverse(MARK, args=[999_999]), {"motiu": REASON, "data": today()})
        assert response.status_code == 404

    def test_get_is_not_allowed(self, treasurer):
        assert admin_client(treasurer).get(reverse(MARK, args=[a_member().pk])).status_code == 405

    def test_csrf_is_required(self, treasurer):
        member = a_member()
        client = admin_client(treasurer, csrf=True)
        assert post(client, MARK, member, motiu=REASON).status_code == 403
        member.refresh_from_db()
        assert member.status == S.ACTIVE


# --- Conflicte d'interès al punt d'entrada (revisió de la T-M01-12) -------------------------


@pytest.mark.django_db
class TestOwnMemberAtTheEntryPoint:
    @pytest.mark.parametrize(("status", "name"), [(S.ACTIVE, MARK), (S.UNPAID, UNMARK)])
    def test_own_member_is_rejected_and_recorded(self, make_admin, status, name):  # noqa: F811
        member = a_member(status)
        own = make_admin("treasurer", person=member.person)
        response = post(admin_client(own), name, member, motiu=REASON)
        assert response.status_code == 303
        member.refresh_from_db()
        assert member.status == status
        assert not MemberStatusChange.objects.filter(member=member).exists()
        (attempt,) = entries(services.OWN_MEMBER_REJECTED, member)
        assert attempt.actor_account == own

    def test_own_row_has_no_form(self, make_admin):  # noqa: F811
        member = a_member()
        own = make_admin("treasurer", person=member.person)
        content = admin_client(own).get(reverse(PAGE)).content.decode()
        assert reverse(MARK, args=[member.pk]) not in content
        assert "És el teu soci" in content


# --- Permisos per rol (059): P10 per veure-ho, P9 per marcar ------------------------------


@pytest.mark.django_db
class TestPermissions:
    @pytest.mark.parametrize("role", P10_ROLES)
    def test_roles_with_p10_see_the_page(self, make_admin, role):  # noqa: F811
        a_member(first="Visible")
        response = admin_client(make_admin(role)).get(reverse(PAGE))
        assert response.status_code == 200
        assert "Visible Ferrer" in response.content.decode()

    @pytest.mark.parametrize("role", NO_P10_ROLES)
    def test_roles_without_p10_get_not_found(self, make_admin, role):  # noqa: F811
        assert admin_client(make_admin(role)).get(reverse(PAGE)).status_code == 404

    @pytest.mark.parametrize("role", ["secretary", "administrator", "president", "board"])
    def test_roles_without_p9_cannot_mark_even_by_direct_post(self, make_admin, role):  # noqa: F811
        active, unpaid = a_member(), a_member(S.UNPAID, first="Pere")
        client = admin_client(make_admin(role))
        assert post(client, MARK, active, motiu=REASON).status_code == 404
        assert post(client, UNMARK, unpaid, motiu=REASON).status_code == 404
        active.refresh_from_db()
        unpaid.refresh_from_db()
        assert (active.status, unpaid.status) == (S.ACTIVE, S.UNPAID)

    def test_secretary_sees_no_actions(self, make_admin):  # noqa: F811
        member = a_member()
        content = admin_client(make_admin("secretary")).get(reverse(PAGE)).content.decode()
        assert reverse(MARK, args=[member.pk]) not in content

    def test_treasurer_sees_the_right_action_for_each_status(self, treasurer):
        active, unpaid = a_member(), a_member(S.UNPAID, first="Pere")
        content = admin_client(treasurer).get(reverse(PAGE)).content.decode()
        assert reverse(MARK, args=[active.pk]) in content
        assert reverse(UNMARK, args=[unpaid.pk]) in content
        assert reverse(UNMARK, args=[active.pk]) not in content
        assert reverse(MARK, args=[unpaid.pk]) not in content

    def test_home_links_to_the_page_only_with_p10(self, make_admin):  # noqa: F811
        url = f'href="{reverse(PAGE)}"'
        home = reverse("administration:home")
        assert url in admin_client(make_admin("treasurer")).get(home).content.decode()
        assert url not in admin_client(make_admin("president")).get(home).content.decode()


# --- Llista i filtres -------------------------------------------------------------------------


@pytest.mark.django_db
class TestList:
    def names(self, client, **params):
        response = client.get(reverse(PAGE), params)
        return [str(member.person) for member, _fee in response.context["page"]]

    def test_only_active_and_unpaid_members(self, treasurer):
        a_member(first="Activa")
        a_member(S.UNPAID, first="Impagada")
        a_member(S.PENDING, first="Pendent")
        a_member(S.LEFT, first="Baixa")
        names = self.names(admin_client(treasurer))
        assert names == ["Activa Ferrer", "Impagada Ferrer"]

    def test_filter_by_member_status(self, treasurer):
        a_member(first="Activa")
        a_member(S.UNPAID, first="Impagada")
        assert self.names(admin_client(treasurer), estat=S.UNPAID) == ["Impagada Ferrer"]

    def test_filter_by_pending_fee(self, treasurer):
        # 079 (RN-M01-86, CA-M01-89): «pendent» només amb el venciment passat; una quota
        # emesa que encara no ha vençut no hi surt.
        a_member(first="Sense")
        with_pending_fee(a_member(first="Deu"), due_on=datetime.date(2026, 1, 31))
        with_pending_fee(a_member(first="Encara"))
        client = admin_client(treasurer)
        assert self.names(client, quota="pending") == ["Deu Ferrer"]
        assert "Pendent" in client.get(reverse(PAGE), {"quota": "pending"}).content.decode()

    def test_manipulated_filter_does_not_filter(self, treasurer):
        a_member(first="Activa")
        a_member(S.LEFT, first="Baixa")
        assert self.names(admin_client(treasurer), estat=S.LEFT) == ["Activa Ferrer"]

    def test_page_creates_no_fee_or_charge(self, treasurer):
        a_member()
        admin_client(treasurer).get(reverse(PAGE))
        assert (AnnualFee.objects.count(), Charge.objects.count()) == (0, 0)
