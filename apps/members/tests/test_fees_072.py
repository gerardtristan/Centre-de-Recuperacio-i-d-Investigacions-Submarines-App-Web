"""Retoc de la T-M01-18 segons la 072 (09/11/2026): generar i renovar quotes amb la 070 (CA-M01-10
reformulada), primer any dels exempts (Q-003), importats de Cluber (Q-076) i recordatoris (Q-061,
RN-M01-14). Els terminis (P-61) no estan implementats. Només dades inventades."""

from datetime import date, datetime

import pytest
from django.utils import timezone

from apps.core.models import Charge, OutgoingEmail, Person, Setting
from apps.members import fees
from apps.members import settings as values
from apps.members.models import AnnualFee, FeeReminder, Member
from apps.members.tests.test_cards import add_fee, exempt_member, make_member, pay

S = Member.Status


def paid_on(member, day):
    pay(add_fee(member, period=day.year), timezone.make_aware(datetime(*day.timetuple()[:3], 12)))


def reminders():
    return OutgoingEmail.objects.filter(template=fees.REMINDER_TEMPLATE).count()


@pytest.mark.django_db
class TestGenerate:
    def test_renewal_is_generated_on_the_day_of_the_first_reminder(self):
        member = make_member()
        paid_on(member, date(2026, 3, 10))
        assert fees.generate_due_fees(date(2027, 2, 22)) == []
        (fee,) = fees.generate_due_fees(date(2027, 2, 23))  # 15 dies abans
        assert (fee.member, fee.period, fee.due_on, fee.sequence) == (
            member,
            2027,
            date(2027, 3, 10),
            1,
        )
        assert fee.charge.amount_cents == member.type.annual_fee_cents
        assert fee.charge.status == Charge.Status.PENDING

    def test_generation_is_idempotent(self):
        member = make_member()
        paid_on(member, date(2026, 3, 10))
        fees.generate_due_fees(date(2027, 3, 1))
        assert fees.generate_due_fees(date(2027, 3, 2)) == []
        assert AnnualFee.objects.filter(member=member).count() == 2

    def test_exempt_first_year_fee_is_due_on_1_january(self):
        # Q-003: continua actiu i se li genera la quota de l'1 de gener del primer any.
        member = exempt_member(birth=date(2015, 5, 1))
        assert fees.generate_due_fees(date(2029, 12, 16)) == []
        (fee,) = fees.generate_due_fees(date(2029, 12, 17))
        assert (fee.period, fee.due_on) == (2030, date(2030, 1, 1))
        member.refresh_from_db()
        assert member.status == S.ACTIVE

    def test_imported_member_renews_one_year_after_cluber(self):
        member = make_member(cluber_id="CLB-9", cluber_renewed_on=date(2026, 6, 15))
        (fee,) = fees.generate_due_fees(date(2027, 5, 31))
        assert (fee.member, fee.due_on) == (member, date(2027, 6, 15))

    def test_partial_payments_generate_nothing_p61(self):
        member = make_member()
        pay(add_fee(member, period=2026), timezone.make_aware(datetime(2026, 3, 10)), amount=3200)
        assert fees.generate_due_fees(date(2027, 3, 1)) == []

    def test_left_member_gets_nothing(self):
        member = make_member()
        paid_on(member, date(2026, 3, 10))
        Member.objects.filter(pk=member.pk).update(status=S.LEFT, left_on=date(2026, 6, 1))
        assert fees.generate_due_fees(date(2027, 3, 1)) == []


@pytest.mark.django_db
class TestReminders:
    def setup_fee(self):
        member = make_member()
        Person.objects.filter(pk=member.person_id).update(contact_email="anna.prova@example.org")
        paid_on(member, date(2026, 3, 10))
        (fee,) = fees.generate_due_fees(date(2027, 2, 23))
        return fee

    def test_each_reminder_once_on_its_day(self):
        fee = self.setup_fee()
        expected = {
            date(2027, 2, 23): -15,
            date(2027, 3, 9): -1,
            date(2027, 3, 10): 0,
            date(2027, 3, 25): 15,
            date(2027, 4, 9): 30,
        }
        for day, offset in expected.items():
            assert fees.send_due_reminders(day) == 1
            assert fees.send_due_reminders(day) == 0  # mateix dia, cap duplicat
            assert FeeReminder.objects.filter(fee=fee, offset_days=offset).exists()
        assert fees.send_due_reminders(date(2027, 5, 1)) == 0
        assert reminders() == 5

    def test_a_missed_day_sends_only_the_latest_reminder(self):
        fee = self.setup_fee()
        assert fees.send_due_reminders(date(2027, 3, 12)) == 1
        assert list(FeeReminder.objects.filter(fee=fee).values_list("offset_days", flat=True)) == [
            0
        ]

    def test_paid_fee_gets_no_reminder(self):
        fee = self.setup_fee()
        pay(fee, timezone.make_aware(datetime(2027, 3, 1, 12)))
        assert fees.send_due_reminders(date(2027, 3, 25)) == 0
        assert reminders() == 0

    def test_offsets_are_configurable(self):
        Setting.objects.filter(key=values.FEE_REMINDER_OFFSETS).update(initial_value=[0, -7])
        member = make_member()
        paid_on(member, date(2026, 3, 10))
        assert fees.generate_due_fees(date(2027, 3, 2)) == []  # 8 dies abans: encara no
        (fee,) = fees.generate_due_fees(date(2027, 3, 3))
        assert fees.send_due_reminders(date(2027, 3, 3)) == 1
        assert FeeReminder.objects.get(fee=fee).offset_days == -7
