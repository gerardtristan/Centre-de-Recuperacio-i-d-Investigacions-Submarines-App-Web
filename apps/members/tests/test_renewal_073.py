"""Avís previ de la renovació (T-M01-43a; 073, 079 i 085; RN-M01-73, RN-M01-93; CA-M01-70).
El pas a simpatitzant en renovar (CA-M01-69) és de la T-M01-43b. Només dades inventades."""

from datetime import date, datetime

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.core.models import AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import fees
from apps.members.models import AnnualFee, MemberRequest, MembershipType

from .test_downgrade_073 import downgrade_request, pay_annual_fee
from .test_member_requests import leave_request, make_member

RS = MemberRequest.Status
PAID = timezone.make_aware(datetime(2025, 3, 10, 12))  # renovació: 10/03/2026
RENEWAL = date(2026, 3, 10)


def full_member(first="Pere", **fields):
    member = make_member(first, type_code="full", **fields)
    pay_annual_fee(member, PAID)
    return member


def notices():
    return OutgoingEmail.objects.filter(template=fees.RENEWAL_NOTICE_TEMPLATE)


@pytest.mark.django_db
class TestNotice:
    def test_sent_the_same_day_of_the_previous_month_once(self):
        member = full_member()
        assert fees.send_renewal_notices(date(2026, 2, 9)) == 0
        assert fees.send_renewal_notices(date(2026, 2, 10)) == 1
        (email,) = notices()
        assert email.to_address == member.person.contact_email
        assert "10/03/2026" in email.body_text
        assert "Canvi de tipus" in email.body_text
        # La tasca torna a córrer (el mateix dia i l'endemà): cap avís més.
        assert fees.send_renewal_notices(date(2026, 2, 10)) == 0
        assert fees.send_renewal_notices(date(2026, 2, 11)) == 0
        assert notices().count() == 1

    def test_a_missed_day_is_recovered_before_the_fee_is_generated(self):
        full_member()
        assert fees.send_renewal_notices(date(2026, 2, 20)) == 1

    def test_comes_before_the_renewal_fee_and_never_after_it(self):
        member = full_member()
        assert fees.generate_due_fees(date(2026, 2, 10)) == []  # l'avís arriba abans
        fees.generate_due_fees(date(2026, 2, 23))  # quota generada sense avís
        assert AnnualFee.objects.filter(member=member).count() == 2
        assert fees.send_renewal_notices(date(2026, 2, 24)) == 0

    def test_pending_downgrade_is_mentioned_instead_of_asking_for_it(self):
        member = full_member()
        downgrade_request(member)
        fees.send_renewal_notices(date(2026, 2, 10))
        body = notices().get().body_text
        assert "pendent" in body
        assert "demana-ho" not in body

    def test_accepted_downgrade_is_mentioned(self):
        member = full_member()
        downgrade_request(member, status=RS.APPROVED)
        fees.send_renewal_notices(date(2026, 2, 10))
        assert "passaràs a simpatitzant" in notices().get().body_text

    @pytest.mark.parametrize("case", ["supporter", "unpaid", "pending_leave", "scheduled_leave"])
    def test_who_does_not_receive_it_rn_m01_93(self, case):
        member = full_member()
        if case == "supporter":
            member.type = MembershipType.objects.get(code="supporter")
            member.save(update_fields=["type"])
        elif case == "unpaid":
            member.status = "unpaid"
            member.save(update_fields=["status"])
        elif case == "pending_leave":
            leave_request(member)
        else:
            leave = leave_request(member)
            MemberRequest.objects.filter(pk=leave.pk).update(
                status=RS.APPROVED, effective_on=date(2026, 6, 1)
            )
        assert fees.send_renewal_notices(date(2026, 2, 10)) == 0

    def test_end_of_month_and_configurable_months(self):
        full_member()
        with override_settings(MEMBER_RENEWAL_NOTICE_MONTHS=2):
            assert fees.send_renewal_notices(date(2026, 1, 10)) == 1


# --- CA-M01-69: en renovar, quota i tipus de simpatitzant -----------------------------------


def test_daily_task_goes_on_after_an_error(monkeypatch):
    from apps.members import tasks

    calls = []

    def boom(*args, **kwargs):
        raise RuntimeError("error inventat")

    monkeypatch.setattr(fees, "send_renewal_notices", boom)
    monkeypatch.setattr(fees, "generate_due_fees", lambda: calls.append("quotes"))
    monkeypatch.setattr(fees, "send_due_reminders", lambda: calls.append("recordatoris"))
    with pytest.raises(RuntimeError):
        tasks.daily_fees.func(0)
    assert calls == ["quotes", "recordatoris"]


@pytest.mark.django_db
def test_member_without_an_address_is_not_counted_nor_marked():
    member = full_member()
    member.person.contact_email = ""
    member.person.save(update_fields=["contact_email"])
    assert fees.send_renewal_notices(date(2026, 2, 10)) == 0
    assert not AuditEntry.objects.filter(action=fees.RENEWAL_NOTICE_SENT).exists()


def test_months_before_with_months_after_of_payments():
    from apps.payments.expiry import months_after

    assert months_after(date(2026, 3, 31), -1) == date(2026, 2, 28)
    assert months_after(date(2026, 1, 15), -1) == date(2025, 12, 15)
    assert months_after(date(2026, 3, 10), -14) == date(2025, 1, 10)


@pytest.mark.parametrize(
    ("months", "offsets", "errors"),
    [(1, (-15, -1, 0), 0), (1, (-30, -1), 1), (2, (-45,), 0), (0, (-15,), 1)],
)
def test_notice_window_must_open_before_the_first_reminder(months, offsets, errors):
    from apps.members.checks import renewal_notice_before_fee

    with override_settings(
        MEMBER_RENEWAL_NOTICE_MONTHS=months, MEMBER_FEE_REMINDER_OFFSETS=offsets
    ):
        found = renewal_notice_before_fee(None)
    assert len(found) == errors
    assert all(error.id == "members.E002" for error in found)
