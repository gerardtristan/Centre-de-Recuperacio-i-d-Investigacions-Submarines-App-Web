"""Quotes després de la decisió 079 (T-M01-18; RN-M01-86, 89 i 91): un sol càlcul de «vàlid fins
al» per al llistat, la fitxa, la revisió de quotes, el carnet i la generació (CA-M01-89), avís al
tresorer per correu (CA-M01-97), data de la marca d'impagat (CA-M01-103) i generació una sola
vegada (CA-M01-10 precisat). Només dades inventades.
"""

from datetime import date, datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.core import audit
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Person, Role, RolePermission
from apps.core.permissions import accounts_with_perm
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees, roster, services, validity
from apps.members.models import AnnualFee, Member, MemberCard, MembershipType
from apps.members.tests.test_cards import add_fee, make_member, pay
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

S = Member.Status
SYSTEM = audit.system("proves")
LIST = "administration:members_list"
DETAIL = "administration:member_detail"
FEES = "administration:fees"
TODAY = date(2027, 3, 1)


def at_noon(day):
    return timezone.make_aware(datetime(day.year, day.month, day.day, 12))


def loaded(member):
    return cards.load_member(member.pk)


def state(member, today=TODAY):
    return roster.fee_state(loaded(member), today)


def paid_until(day, **kwargs):
    """Soci que va pagar un any abans de `day`: «vàlid fins al» `day`."""
    member = make_member(**kwargs)
    pay(add_fee(member, period=day.year - 1), at_noon(day.replace(year=day.year - 1)))
    return member


# --- CA-M01-89: un sol càlcul -----------------------------------------------------------------


class TestCaM0189SingleCalculation:
    def test_ca_m01_89_renewal_issued_before_the_due_date_is_still_paid_until(self):
        member = paid_until(date(2027, 3, 10))
        (renewal,) = fees.generate_due_fees(date(2027, 2, 23))
        assert renewal.charge.status == Charge.Status.PENDING
        card = MemberCard.objects.create(member=member, token_hash="a" * 64)

        assert state(member) == roster.FeeState(roster.PAID_UNTIL, date(2027, 3, 10))
        assert cards.validity(loaded(member), card, TODAY).valid
        assert cards.valid_until(loaded(member)) == date(2027, 3, 10)
        assert services.get_member_summary(member.person).valid_until == date(2027, 3, 10)

    def test_ca_m01_89_after_the_due_date_without_paying_it_is_pending_and_the_card_is_not_valid(
        self,
    ):
        member = paid_until(date(2027, 3, 10))
        fees.generate_due_fees(date(2027, 2, 23))
        card = MemberCard.objects.create(member=member, token_hash="a" * 64)
        last_day, next_day = date(2027, 3, 10), date(2027, 3, 11)
        assert state(member, last_day).kind == roster.PAID_UNTIL  # el mateix dia encara val
        assert cards.validity(loaded(member), card, last_day).valid
        assert state(member, next_day) == roster.FeeState(roster.PENDING)
        assert not cards.validity(loaded(member), card, next_day).valid

    def test_ca_m01_89_imported_member_with_cluber_renewal_is_paid_until(self):
        member = make_member(cluber_id="C-1", cluber_renewed_on=date(2026, 5, 2))
        assert state(member) == roster.FeeState(roster.PAID_UNTIL, date(2027, 5, 2))
        assert state(member, date(2027, 5, 3)) is None  # vençut i sense cap quota emesa

    def test_ca_m01_89_returned_fee_is_pending(self):
        member = make_member()
        fee = add_fee(member, period=2027)
        Charge.objects.filter(pk=fee.charge_id).update(status=Charge.Status.RETURNED)
        assert state(member) == roster.FeeState(roster.PENDING)
        rows = fees.rows_for_review({"quota": roster.PENDING}, TODAY)
        assert [m.pk for m, _fee in rows] == [member.pk]

    def test_returned_renewal_does_not_hide_a_period_that_is_still_valid(self):
        member = paid_until(date(2027, 3, 10))
        (renewal,) = fees.generate_due_fees(date(2027, 2, 23))
        Charge.objects.filter(pk=renewal.charge_id).update(status=Charge.Status.RETURNED)
        assert state(member).kind == roster.PAID_UNTIL
        assert state(member, date(2027, 3, 11)) == roster.FeeState(roster.PENDING)

    def test_pending_fee_that_is_not_due_yet_shows_nothing(self):
        member = make_member(status=S.PENDING)
        fee = add_fee(member, period=2027)
        assert fee.due_on == date(2027, 1, 1)
        assert state(member, date(2026, 12, 31)) is None
        assert state(member, date(2027, 1, 1)) is None  # el dia del venciment encara no
        assert state(member, date(2027, 1, 2)) == roster.FeeState(roster.PENDING)

    def test_exempt_minor_uses_the_birth_date_of_the_person(self):
        member = make_member()
        Person.objects.filter(pk=member.person_id).update(birth_date=date(2015, 5, 5))
        assert state(member) == roster.FeeState(roster.EXEMPT)
        assert cards.valid_until(loaded(member)) == date(2029, 12, 31)
        assert state(member, date(2030, 1, 1)) is None  # l'1 de gener ja ha de pagar

    def test_partial_payments_show_nothing_and_the_card_has_no_date(self):
        member = make_member()
        pay(add_fee(member, period=2026), at_noon(date(2026, 6, 1)), amount=3200)
        assert state(member) is None
        assert cards.valid_until(loaded(member)) is None

    def test_cards_roster_and_fees_share_the_same_functions(self):
        assert cards.valid_until is validity.valid_until
        assert roster.twelve_months_after is validity.twelve_months_after
        member = paid_until(date(2027, 3, 10))
        assert fees.next_fee_due(loaded(member)) == validity.valid_until(loaded(member))

    def test_ca_m01_89_list_detail_and_review_show_the_same(self, make_admin):  # noqa: F811
        today = timezone.localdate()
        until = today + timedelta(days=5)
        member = paid_until(until)
        fees.generate_due_fees(today)  # la renovació ja és emesa i pendent
        assert AnnualFee.objects.filter(member=member).count() == 2
        client = admin_client(make_admin("treasurer"))
        text = f"Pagada fins al {until:%d/%m/%Y}"
        assert text in client.get(reverse(LIST)).content.decode()
        assert text in client.get(reverse(DETAIL, args=[member.pk])).content.decode()
        review = client.get(reverse(FEES))
        assert text in review.content.decode()
        assert client.get(reverse(FEES), {"quota": "pending"}).context["page"].paginator.count == 0


# --- CA-M01-97: avís al tresorer per correu ---------------------------------------------------


def notices():
    return list(OutgoingEmail.objects.filter(template=fees.NOTICE_TEMPLATE).order_by("pk"))


def with_address(account, address):
    account.notification_email = address
    account.save()
    return account


class TestCaM0197TreasurerNotice:
    def test_ca_m01_97_paid_while_unpaid_notifies_who_can_edit_the_fees(self, make_admin):  # noqa: F811
        treasurer = with_address(make_admin("treasurer"), "tresoreria@example.org")
        admin = with_address(make_admin("administrator"), "admin@example.org")
        with_address(make_admin("secretary"), "secretaria@example.org")  # P10 de consulta: no
        member = make_member(first="Sentinella", status=S.UNPAID, number=4321)
        fee = add_fee(member, period=2027)
        pay(fee)

        services.on_fee_paid(fee.pk)

        assert Member.objects.get(pk=member.pk).status == S.UNPAID  # no es desmarca sol (040)
        sent = notices()
        assert {e.to_address for e in sent} == {"tresoreria@example.org", "admin@example.org"}
        assert {e.person_id for e in sent} == {treasurer.person_id, admin.person_id}
        for email in sent:
            assert "4321" in email.body_text and "2027" in email.body_text
            assert "4321" in email.subject
            for text in ("Sentinella", "Prova", "12345678Z", "90"):
                assert text not in email.body_text
                assert text not in email.subject
        entry = AuditEntry.objects.get(action=fees.NOTICE_SENT)
        assert entry.details == {"event": fees.NOTICE_PAID_WHILE_UNPAID, "recipients": 2}
        assert (entry.target_type, entry.target_id) == ("members.annualfee", str(fee.pk))

    def test_ca_m01_97_returned_fee_sends_the_same_notice(self, make_admin):  # noqa: F811
        with_address(make_admin("treasurer"), "tresoreria@example.org")
        member = make_member(number=4321)
        fee = add_fee(member, period=2027)
        services.on_fee_returned(fee.pk)
        (email,) = notices()
        assert "retornat" in email.subject.lower()
        assert "4321" in email.body_text
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE

    def test_recipients_follow_the_matrix_not_a_role_name(self, make_admin):  # noqa: F811
        board = with_address(make_admin("board"), "junta@example.org")
        with_address(make_admin("treasurer"), "tresoreria@example.org")
        RolePermission.objects.filter(permission_code=fees.EDIT_PERMISSION).delete()
        RolePermission.objects.create(
            role=Role.objects.get(code="board"), permission_code=fees.EDIT_PERMISSION, scope="all"
        )
        assert accounts_with_perm(fees.EDIT_PERMISSION, write=True) == [board]
        fee = add_fee(make_member(status=S.UNPAID), period=2027)
        assert fees.notify_fee_editors(fee, fees.NOTICE_RETURNED) == 1
        assert [e.to_address for e in notices()] == ["junta@example.org"]

    def test_one_email_per_address_and_none_without_address_or_inactive(self, make_admin):  # noqa: F811
        with_address(make_admin("treasurer"), "compartida@example.org")
        with_address(make_admin("administrator"), "compartida@example.org")
        make_admin("administrator")  # sense correu de notificació
        disabled = with_address(make_admin("treasurer"), "fora@example.org")
        type(disabled).objects.filter(pk=disabled.pk).update(status="disabled")
        fee = add_fee(make_member(status=S.UNPAID), period=2027)
        assert fees.notify_fee_editors(fee, fees.NOTICE_RETURNED) == 1
        assert [e.to_address for e in notices()] == ["compartida@example.org"]

    def test_active_member_renewal_sends_no_notice(self, make_admin):  # noqa: F811
        with_address(make_admin("treasurer"), "tresoreria@example.org")
        member = make_member()
        fee = add_fee(member, period=2027)
        pay(fee)
        services.on_fee_paid(fee.pk)
        assert notices() == []


# --- CA-M01-103: data de la marca d'impagat ---------------------------------------------------


class TestCaM01103UnpaidDate:
    @pytest.fixture
    def treasurer(self, make_admin):  # noqa: F811
        return make_admin("treasurer")

    def test_ca_m01_103_future_date_is_rejected(self, treasurer):
        member = make_member()
        tomorrow = timezone.localdate() + timedelta(days=1)
        with pytest.raises(ValidationError):
            services.mark_unpaid(member, by=treasurer, effective_on=tomorrow, reason="Prova")
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE

    @pytest.mark.parametrize("days", [0, 1, 40])
    def test_ca_m01_103_today_or_a_past_date_is_accepted(self, treasurer, days):
        member = make_member()
        day = timezone.localdate() - timedelta(days=days)
        services.mark_unpaid(member, by=treasurer, effective_on=day, reason="Prova")
        assert Member.objects.get(pk=member.pk).status == S.UNPAID
        assert member.status_changes.get().effective_on == day

    def test_ca_m01_103_screen_rejects_a_future_date(self, treasurer):
        member = make_member()
        tomorrow = (timezone.localdate() + timedelta(days=1)).isoformat()
        admin_client(treasurer).post(
            reverse("administration:fee_mark_unpaid", args=[member.pk]),
            {"data": tomorrow, "motiu": "Prova"},
        )
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE


# --- CA-M01-10 (precisat per la 079): una quota de renovació per soci, una sola vegada --------


class TestCaM0110GenerateOnce:
    def test_ca_m01_10_150_members_get_exactly_one_renewal_each(self):
        full = MembershipType.objects.get(code="full")
        paid_day = date(2026, 3, 10)
        members = []
        for n in range(150):
            person = Person.objects.create(
                first_name=f"Soci{n}", last_name="Prova", origin=Person.Origin.WEB
            )
            member = Member.objects.create(
                person=person,
                member_number=2000 + n,
                type=full,
                status=S.ACTIVE,
                joined_on=date(2019, 3, 12),
            )
            pay(add_fee(member, period=2026), at_noon(paid_day))
            members.append(member)

        first_reminder_day = date(2027, 2, 23)  # 15 dies abans del venciment (Q-061)
        assert fees.generate_due_fees(first_reminder_day - timedelta(days=1)) == []
        created = fees.generate_due_fees(first_reminder_day)
        again = fees.generate_due_fees(first_reminder_day)

        assert len(created) == 150 and again == []
        renewals = AnnualFee.objects.filter(period=2027, kind=AnnualFee.Kind.ANNUAL)
        assert renewals.count() == 150
        assert renewals.values("member").distinct().count() == 150
        assert set(renewals.values_list("due_on", flat=True)) == {date(2027, 3, 10)}
        departments = set(renewals.values_list("charge__department__name", flat=True))
        assert len(departments) == 1  # «General» (la 00 ho imposa per a les quotes)

    def test_ca_m01_11_a_new_price_only_affects_fees_generated_afterwards(self):
        first = paid_until(date(2027, 3, 10))
        second = paid_until(date(2027, 6, 10), first="Berta", number=1288, document="87654321X")
        (old,) = fees.generate_due_fees(date(2027, 2, 23))
        MembershipType.objects.filter(code="full").update(annual_fee_cents=9500)
        (new,) = fees.generate_due_fees(date(2027, 5, 26))
        assert (old.member, old.charge.amount_cents) == (first, 9000)
        assert (new.member, new.charge.amount_cents) == (second, 9500)
        old.charge.refresh_from_db()
        assert old.charge.amount_cents == 9000
