"""Contracte de `members.on_fee_paid` després de la decisió 079 (T-M01-26; RN-M01-89;
CA-M01-96 a CA-M01-98): un actiu sense carnet que renova en rep un, un impagat que paga fa
sortir l'avís (CA-M01-97, a test_fees_079.py) i un soci de baixa que paga no fa fallar el servei
i surt a «Pagaments per revisar». Només dades inventades.
"""

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.core.models import AuditEntry, Charge, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees, services
from apps.members.models import Member, MemberCard, MemberStatusChange
from apps.members.services import InvalidTransition, OwnMemberChange
from apps.members.tests.test_cards import SYSTEM, add_fee, make_member, pay
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

S = Member.Status
FEES = "administration:fees"
REVIEWED = "administration:fee_payment_reviewed"
NOTE = "Retornat per transferència (nota inventada)"


def paid_fee(member, period=2027):
    fee = add_fee(member, period=period)
    pay(fee)
    return fee


def left_member(**kwargs):
    return make_member(status=S.LEFT, left_on=date(2026, 6, 1), **kwargs)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


# --- CA-M01-96: un actiu sense carnet que renova en rep un ------------------------------------


class TestCaM0196ActiveWithoutCard:
    def test_ca_m01_96_active_member_without_card_gets_one_when_the_renewal_is_paid(self):
        member = make_member()
        fee = paid_fee(member)
        assert not MemberCard.objects.exists()
        result = services.on_fee_paid(fee.pk)
        assert result.status == S.ACTIVE
        card = MemberCard.objects.get(member=member)
        assert cards.validity(cards.load_member(member.pk), card).valid
        assert not MemberStatusChange.objects.filter(member=member).exists()
        issued = AuditEntry.objects.get(action=cards.CARD_ISSUED)
        assert issued.actor_origin == services.FEE_PAID_ORIGIN

    def test_ca_m01_96_a_revoked_card_does_not_count_as_having_one(self):
        member = make_member()
        pay(add_fee(member, period=2026))
        cards.issue_card(member, by=SYSTEM)
        cards.revoke_card(member, by=SYSTEM, reason="Perdut (prova)")
        services.on_fee_paid(paid_fee(member).pk)
        assert MemberCard.objects.filter(member=member, revoked_at__isnull=True).count() == 1
        assert MemberCard.objects.filter(member=member).count() == 2

    def test_active_member_with_a_card_keeps_it(self):
        member = make_member()
        pay(add_fee(member, period=2026))
        token = cards.issue_card(member, by=SYSTEM)
        services.on_fee_paid(paid_fee(member).pk)
        assert MemberCard.objects.filter(member=member).count() == 1
        assert cards.valid_card_for_token(token) is not None

    def test_it_is_idempotent(self):
        member = make_member()
        fee = paid_fee(member)
        services.on_fee_paid(fee.pk)
        services.on_fee_paid(fee.pk)
        assert MemberCard.objects.filter(member=member).count() == 1

    def test_partial_payments_give_no_card_and_no_error_for_an_active_member(self):
        member = make_member()
        fee = add_fee(member, period=2027)
        first = pay(fee, amount=3000)
        pay(fee, amount=6000)
        Charge.objects.filter(pk=fee.charge_id).update(status=Charge.Status.PAID)
        assert first.amount_cents == 3000
        services.on_fee_paid(fee.pk)
        assert not MemberCard.objects.exists()

    def test_pending_member_with_partial_payments_is_still_the_only_invalid_transition(self):
        member = make_member(status=S.PENDING)
        fee = add_fee(member, period=2027)
        pay(fee, amount=3000)
        pay(fee, amount=6000)
        Charge.objects.filter(pk=fee.charge_id).update(status=Charge.Status.PAID)
        with pytest.raises(InvalidTransition):
            services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.PENDING


# --- CA-M01-98: soci de baixa amb una quota pagada --------------------------------------------


class TestCaM0198LeftMember:
    def test_ca_m01_98_service_does_not_fail_and_changes_nothing(self):
        member = left_member()
        fee = paid_fee(member)
        result = services.on_fee_paid(fee.pk)
        assert result.status == S.LEFT
        assert Member.objects.get(pk=member.pk).left_on == date(2026, 6, 1)
        assert not MemberStatusChange.objects.filter(member=member).exists()
        assert not MemberCard.objects.exists()
        assert not OutgoingEmail.objects.exists()
        entry = AuditEntry.objects.get(action=services.FEE_PAID_AFTER_LEAVING)
        assert (entry.target_type, entry.target_id) == ("members.annualfee", str(fee.pk))
        assert entry.actor_origin == services.FEE_PAID_ORIGIN
        assert services.FEE_PAID_AFTER_LEAVING == fees.PAID_AFTER_LEAVING

    def test_ca_m01_98_it_is_listed_until_it_is_marked_as_reviewed(self, treasurer):
        member = left_member(first="Sentinella")
        fee = paid_fee(member)
        services.on_fee_paid(fee.pk)
        services.on_fee_paid(fee.pk)  # idempotent: una sola entrada, una sola fila
        assert AuditEntry.objects.filter(action=services.FEE_PAID_AFTER_LEAVING).count() == 1
        assert fees.payments_to_review() == [fee]

        client = admin_client(treasurer)
        page = client.get(reverse(FEES)).content.decode()
        assert "Pagaments per revisar" in page and "Sentinella" in page

        response = client.post(reverse(REVIEWED, args=[fee.pk]), {"nota": f"  {NOTE}  "})
        assert response.status_code == 303
        assert fees.payments_to_review() == []
        entry = AuditEntry.objects.get(action=fees.PAYMENT_REVIEWED)
        assert (entry.actor_account, entry.reason) == (treasurer, NOTE)
        assert "Pagaments per revisar" not in client.get(reverse(FEES)).content.decode()
        fee.charge.refresh_from_db()
        assert fee.charge.status == Charge.Status.PAID  # el càrrec i el pagament no es toquen

    def test_ca_m01_98_note_is_required(self, treasurer):
        fee = paid_fee(left_member())
        services.on_fee_paid(fee.pk)
        admin_client(treasurer).post(reverse(REVIEWED, args=[fee.pk]), {"nota": "  "})
        assert fees.payments_to_review() == [fee]
        with pytest.raises(ValidationError):
            fees.mark_payment_reviewed(fee, by=treasurer, note="")

    def test_ca_m01_98_without_p10_the_list_is_not_visible(self, make_admin):  # noqa: F811
        fee = paid_fee(left_member())
        services.on_fee_paid(fee.pk)
        for role in ("president", "board", "instructor"):
            assert admin_client(make_admin(role)).get(reverse(FEES)).status_code == 404

    def test_secretary_sees_the_list_but_cannot_mark_it(self, make_admin):  # noqa: F811
        fee = paid_fee(left_member())
        services.on_fee_paid(fee.pk)
        secretary = make_admin(Role.Code.SECRETARY)
        client = admin_client(secretary)
        page = client.get(reverse(FEES)).content.decode()
        assert "Pagaments per revisar" in page and "Marca com a revisat" not in page
        assert client.post(reverse(REVIEWED, args=[fee.pk]), {"nota": NOTE}).status_code == 404
        with pytest.raises(Http404):
            fees.mark_payment_reviewed(fee, by=secretary, note=NOTE)
        assert fees.payments_to_review() == [fee]

    def test_own_payment_cannot_be_reviewed(self, make_admin):  # noqa: F811
        member = left_member()
        fee = paid_fee(member)
        services.on_fee_paid(fee.pk)
        own = make_admin(Role.Code.TREASURER, person=member.person)
        with pytest.raises(OwnMemberChange):
            fees.mark_payment_reviewed(fee, by=own, note=NOTE)
        assert fees.payments_to_review() == [fee]

    def test_a_fee_that_is_not_in_the_list_cannot_be_marked(self, treasurer):
        fee = paid_fee(make_member())
        with pytest.raises(ValidationError):
            fees.mark_payment_reviewed(fee, by=treasurer, note=NOTE)
        assert not AuditEntry.objects.filter(action=fees.PAYMENT_REVIEWED).exists()

    def test_marking_needs_post_and_csrf(self, treasurer):
        fee = paid_fee(left_member())
        services.on_fee_paid(fee.pk)
        url = reverse(REVIEWED, args=[fee.pk])
        assert admin_client(treasurer).get(url).status_code == 405
        assert admin_client(treasurer, csrf=True).post(url, {"nota": NOTE}).status_code == 403
        assert fees.payments_to_review() == [fee]
