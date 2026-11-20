"""Editar els terminis d'una quota (T-M01-49c; 072, tercera instrucció, punt 2): la secretaria,
amb permís propi (P23, P-413) i motiu, edita l'import i el venciment de cada termini mentre no
té cap pagament; la suma no canvia i l'historial guarda el valor anterior. Només dades
inventades."""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.core import charges
from apps.core.models import AuditEntry, Charge, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import instalments, services
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member, pay
from apps.members.tests.test_exemption_040 import form_data
from apps.members.tests.test_instalments_049 import SYSTEM, choose, on, plan_of  # noqa: F401
from apps.members.tests.test_roster import admin_client
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

REASON = "El soci cobra a final de mes (motiu inventat)."
DETAIL = "administration:member_detail"
EDIT = "administration:member_fee_instalments"


@pytest.fixture
def clerk(make_admin):  # noqa: F811
    """Un compte de la Secretaria (P23)."""
    account = make_admin("secretary")
    account.set_password(PASSWORD)
    account.save()
    return account


@pytest.fixture
def plan(on):  # noqa: F811
    member = make_member(status=Member.Status.PENDING)
    choose(member)
    return member, plan_of(member)


def state(member):
    return [(f.charge.amount_cents, f.due_on) for f in plan_of(member)]


def test_p23_is_only_of_the_secretary_in_the_initial_matrix():
    cells = RolePermission.objects.filter(permission_code=instalments.EDIT_PERMISSION)
    assert [(c.role.code, c.scope) for c in cells] == [("secretary", "all")]


class TestService:
    def test_moving_amounts_and_dates_keeps_the_sum_and_records_the_previous_values(
        self, plan, clerk
    ):
        member, (first, second, third) = plan
        assert [f.charge.amount_cents for f in (first, second, third)] == [3200, 3200, 3200]
        changes = {
            first.pk: (2000, first.due_on),
            second.pk: (3800, date(2027, 3, 15)),
            third.pk: (3800, third.due_on),
        }
        instalments.edit(first, changes, by=clerk, reason=REASON)
        assert state(member) == [
            (2000, first.due_on),
            (3800, date(2027, 3, 15)),
            (3800, third.due_on),
        ]
        entries = AuditEntry.objects.filter(action=instalments.EDITED, reason=REASON)
        assert {(e.field, e.old_value, e.new_value) for e in entries} == {
            ("amount_cents", 3200, 2000),
            ("amount_cents", 3200, 3800),
            ("due_on", str(second.due_on), "2027-03-15"),
        }
        assert all(e.actor_account_id == clerk.pk for e in entries)

    @pytest.mark.parametrize("amounts", [(3200, 3200, 3300), (3200, 3200, 3100)])
    def test_changing_the_total_is_rejected_and_nothing_changes(self, plan, clerk, amounts):
        member, fees = plan
        before = state(member)
        changes = {f.pk: (cents, f.due_on) for f, cents in zip(fees, amounts, strict=True)}
        with pytest.raises(ValidationError, match="continuar sumant 96,00"):
            instalments.edit(fees[0], changes, by=clerk, reason=REASON)
        assert state(member) == before
        assert not AuditEntry.objects.filter(action=instalments.EDITED).exists()

    def test_a_paid_instalment_cannot_be_edited_but_the_others_can(self, plan, clerk):
        member, (first, second, third) = plan
        pay(first)
        first.charge.refresh_from_db()
        assert not instalments.is_editable(first)
        with pytest.raises(ValidationError, match="només anul·lar"):
            instalments.edit(
                first,
                {first.pk: (3000, first.due_on), second.pk: (3400, second.due_on)},
                by=clerk,
                reason=REASON,
            )
        # Els altres dos sí, i la suma compta també el pagat.
        instalments.edit(
            second,
            {second.pk: (3000, second.due_on), third.pk: (3400, third.due_on)},
            by=clerk,
            reason=REASON,
        )
        assert [c for c, _d in state(member)] == [3200, 3000, 3400]

    def test_an_instalment_being_charged_cannot_be_edited(self, plan, clerk):
        from apps.payments import attempts
        from apps.payments.models import PaymentAttempt

        member, (first, second, third) = plan
        attempt = attempts.create_attempt(second.charge, PaymentAttempt.Method.CARD)
        attempts.transition(attempt, PaymentAttempt.Status.IN_PROGRESS, by=SYSTEM)
        assert not instalments.is_editable(second)
        before = state(member)
        with pytest.raises(ValidationError):
            instalments.edit(
                first,
                {first.pk: (3000, first.due_on), second.pk: (3400, second.due_on)},
                by=clerk,
                reason=REASON,
            )
        assert state(member) == before

    def test_zero_is_not_an_amount(self, plan, clerk):
        member, (first, second, third) = plan
        with pytest.raises(ValidationError, match="més gran que zero"):
            instalments.edit(
                first,
                {first.pk: (0, first.due_on), second.pk: (6400, second.due_on)},
                by=clerk,
                reason=REASON,
            )

    @pytest.mark.parametrize("role", ["treasurer", "administrator", "president"])
    def test_without_p23_not_found_and_nothing_changes(self, plan, make_admin, role):  # noqa: F811
        member, (first, *_rest) = plan
        with pytest.raises(Http404):
            instalments.edit(
                first, {first.pk: (3200, date(2027, 2, 1))}, by=make_admin(role), reason=REASON
            )
        assert plan_of(member)[0].due_on == first.due_on

    @pytest.mark.parametrize("reason", ["", "   "])
    def test_the_reason_is_required(self, plan, clerk, reason):
        member, (first, *_rest) = plan
        with pytest.raises(ValidationError, match="motiu"):
            instalments.edit(first, {first.pk: (3200, date(2027, 2, 1))}, by=clerk, reason=reason)

    def test_nobody_edits_their_own_instalments(self, plan, make_admin):  # noqa: F811
        member, (first, *_rest) = plan
        own = make_admin("secretary", person=member.person)
        with pytest.raises(services.OwnMemberChange):
            instalments.edit(first, {first.pk: (3200, date(2027, 2, 1))}, by=own, reason=REASON)
        assert plan_of(member)[0].due_on == first.due_on

    def test_an_instalment_of_another_member_is_rejected(self, plan, clerk):
        member, (first, *_rest) = plan
        other = make_member("Berta", number=1300, document="00000000T")
        with pytest.raises(ValidationError):
            instalments.edit(
                add_fee(other), {first.pk: (3200, date(2027, 2, 1))}, by=clerk, reason=REASON
            )
        assert plan_of(member)[0].due_on == first.due_on


def test_the_core_does_not_change_the_amount_of_a_charge_that_is_not_pending(clerk):
    fee = add_fee(make_member())
    charges.cancel(fee.charge, "Motiu inventat", by=SYSTEM)
    with pytest.raises(ValidationError):
        charges.change_amount(fee.charge, 100, by=clerk, reason=REASON)
    assert Charge.objects.get(pk=fee.charge_id).amount_cents == 9000


class TestScreen:
    def test_v25_the_member_page_lists_the_instalments_in_order_with_one_edit_link(
        self, plan, clerk
    ):
        """T-F1-01 (V25): a la fitxa, els terminis en ordre (1, 2, 3) i un sol «Edita els
        terminis…», fora de les files."""
        member, _plan = plan
        page = admin_client(clerk).get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert (
            page.index("termini 1 de 3")
            < page.index("termini 2 de 3")
            < page.index("termini 3 de 3")
        )
        assert page.count("Edita els terminis…") == 1

    def test_the_secretary_edits_from_the_member_page(self, plan, clerk):
        member, (first, second, third) = plan
        client = admin_client(clerk)
        url = reverse(EDIT, args=[member.pk, first.pk])
        assert url in client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        page = client.get(url).content.decode()
        assert "Edita els terminis" in page and "sumen 96,00" in page
        assert f'name="amount_{third.pk}"' in page and 'name="password"' in page
        assert 'value="32,00"' in page  # amb els cèntims, com es mostra l'import

        data = form_data(clerk)
        for f, euros, day in (
            (first, "30,00", "2027-01-31"),
            (second, "33,00", "2027-02-28"),
            (third, "33,00", "2027-04-30"),
        ):
            data.update({f"amount_{f.pk}": euros, f"due_{f.pk}": day})
        response = client.post(url, data)

        assert response.status_code == 303
        assert [c for c, _d in state(member)] == [3000, 3300, 3300]
        assert plan_of(member)[2].due_on == date(2027, 4, 30)
        assert "Terminis desats" in client.get(response["Location"]).content.decode()

    def test_a_wrong_sum_shows_the_error_and_saves_nothing(self, plan, clerk):
        member, fees = plan
        url = reverse(EDIT, args=[member.pk, fees[0].pk])
        data = form_data(clerk)
        for f in fees:
            data.update({f"amount_{f.pk}": "40,00", f"due_{f.pk}": f.due_on.isoformat()})
        response = admin_client(clerk).post(url, data)
        assert response.status_code == 200
        assert "continuar sumant" in response.content.decode()
        assert [c for c, _d in state(member)] == [3200, 3200, 3200]

    def test_without_p23_not_found(self, plan, make_admin):  # noqa: F811
        member, (first, *_rest) = plan
        client = admin_client(make_admin("treasurer"))
        url = reverse(EDIT, args=[member.pk, first.pk])
        assert url not in client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        assert client.get(url).status_code == 404
        assert client.post(url, {"reason": REASON}).status_code == 404

    def test_an_annual_fee_has_nothing_to_edit(self, clerk):
        member = make_member()
        fee = add_fee(member)
        url = reverse(EDIT, args=[member.pk, fee.pk])
        page = admin_client(clerk).get(url).content.decode()
        assert "No hi ha cap termini per editar" in page and 'name="reason"' not in page
