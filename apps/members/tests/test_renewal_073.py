"""Avís previ i pas a simpatitzant en renovar (T-M01-43; 073, 079 i 085; RN-M01-73, RN-M01-93;
CA-M01-69 i CA-M01-70). Dates passades: el canvi de tipus no admet una data efectiva futura.
Només dades inventades."""

from datetime import date, datetime

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.core import audit
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees
from apps.members import member_requests as mr
from apps.members.models import AnnualFee, MemberCard, MemberRequest, MembershipType
from apps.members.services import TYPE_CHANGED

from .test_cards import pay
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


def full_price_notices():
    return AuditEntry.objects.filter(
        action=fees.NOTICE_SENT, details__event=fees.NOTICE_DOWNGRADE_FULL_PRICE
    ).count()


def saved_card(member):
    from apps.payments.models import SavedCard

    return SavedCard.objects.create(
        person=member.person,
        provider_code="fake",
        provider_card_id="targeta-prova",
        last4="4242",
        expiry_month=12,
        expiry_year=2030,
    )


def price(code):
    return MembershipType.objects.get(code=code).annual_fee_cents


# --- CA-M01-70: avís un mes abans, una sola vegada i abans de la quota ----------------------


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


# --- T-M01-43d: llista «a revisar» dels socis sense adreça ----------------------------------


@pytest.mark.django_db
class TestWithoutAddress:
    def test_listed_while_due_and_without_address_and_never_noticed(self):
        member = full_member()
        full_member("Anna")  # amb adreça: rep l'avís i no surt a la llista
        Person.objects.filter(pk=member.person_id).update(contact_email="")
        assert fees.renewal_notices_without_address(date(2026, 2, 9)) == []  # encara no toca
        assert fees.renewal_notices_without_address(date(2026, 2, 10)) == [(member, RENEWAL)]
        assert fees.send_renewal_notices(date(2026, 2, 10)) == 1  # només l'Anna
        assert fees.renewal_notices_without_address(date(2026, 2, 11)) == [(member, RENEWAL)]
        # Amb una adreça a temps, rep l'avís i surt de la llista.
        Person.objects.filter(pk=member.person_id).update(contact_email="pere@example.org")
        assert fees.renewal_notices_without_address(date(2026, 2, 12)) == []
        assert fees.send_renewal_notices(date(2026, 2, 12)) == 1

    def test_leaves_the_list_once_the_fee_is_generated(self):
        member = full_member()
        Person.objects.filter(pk=member.person_id).update(contact_email="")
        fees.generate_due_fees(date(2026, 2, 23))
        assert fees.renewal_notices_without_address(date(2026, 2, 24)) == []

    def test_shown_on_fees_page_to_the_secretariat(self, make_admin):  # noqa: F811
        from django.urls import reverse

        from .test_roster import admin_client

        member = full_member()
        Person.objects.filter(pk=member.person_id).update(contact_email="")
        today = date(2026, 2, 10)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("apps.members.views.admin.local_today", lambda: today)
            page = admin_client(make_admin("secretary")).get(reverse("administration:fees"))
        html = page.content.decode()
        assert "Avís de renovació sense adreça" in html
        assert reverse("administration:member_detail", args=[member.pk]) in html
        assert "10/03/2026" in html


# --- CA-M01-69: en renovar, quota i tipus de simpatitzant -----------------------------------


@pytest.mark.django_db
class TestRenewal:
    def accepted(self):
        member = full_member()
        cards.issue_card(member, by=audit.system("proves"))
        change = downgrade_request(member, status=RS.APPROVED)
        return member, change

    def test_renewal_fee_is_priced_with_the_requested_type(self):
        member, change = self.accepted()
        (fee,) = fees.generate_due_fees(date(2026, 2, 23))
        assert fee.charge.amount_cents == price("supporter") != price("full")
        assert fee.due_on == RENEWAL
        change.refresh_from_db()
        assert change.renewal_fee == fee
        member.refresh_from_db()
        assert member.type.code == "full"  # fins a la renovació, res no canvia

    def test_type_changes_on_the_renewal_day_with_history_audit_and_new_card(self):
        member, change = self.accepted()
        old_card = cards.active_card(member)
        fees.generate_due_fees(date(2026, 2, 23))
        assert mr.apply_due_downgrades(date(2026, 3, 9)) == []
        assert mr.apply_due_downgrades(RENEWAL) == [change]
        member.refresh_from_db()
        assert member.type.code == "supporter"
        history = member.status_changes.get(to_type__code="supporter")
        assert (history.from_type.code, history.effective_on) == ("full", RENEWAL)
        assert AuditEntry.objects.filter(action=TYPE_CHANGED, target_id=str(member.pk)).exists()
        change.refresh_from_db()
        assert change.effective_on == RENEWAL and mr.accepted_downgrade(member) is None
        old_card.refresh_from_db()
        assert old_card.revoked_at is not None
        assert MemberCard.objects.filter(member=member, revoked_at__isnull=True).count() == 1
        # La quota del període anterior no es toca: cap devolució ni anul·lació.
        previous = AnnualFee.objects.get(member=member, period=2025)
        assert previous.charge.status == Charge.Status.PAID
        # Idempotent: tornar-la a córrer no fa res més.
        assert mr.apply_due_downgrades(date(2026, 3, 11)) == []
        assert member.status_changes.filter(to_type__code="supporter").count() == 1

    def test_without_a_downgrade_the_renewal_keeps_the_full_price(self):
        member = full_member()
        (fee,) = fees.generate_due_fees(date(2026, 2, 23))
        assert fee.charge.amount_cents == price("full")
        assert mr.apply_due_downgrades(RENEWAL) == []
        member.refresh_from_db()
        assert member.type.code == "full"

    def future(self):
        """Soci de ple dret que renova el 10/03/2027 (dates futures: la quota encara no ha
        vençut quan s'accepta el pas), amb la quota de renovació ja generada."""
        member = make_member("Pere", type_code="full")
        pay_annual_fee(member, timezone.make_aware(datetime(2026, 3, 10, 12)))
        (fee,) = fees.generate_due_fees(date(2027, 2, 23))
        return member, fee

    def test_accepted_after_the_fee_is_generated_regenerates_it_085_t5(self, make_admin):  # noqa: F811
        member, old = self.future()
        change = downgrade_request(member)
        mr.approve_type_change(change, by=make_admin("secretary"))
        old.charge.refresh_from_db()
        assert old.charge.status == Charge.Status.CANCELLED
        change.refresh_from_db()
        new = change.renewal_fee
        assert (new.charge.amount_cents, new.due_on, new.period) == (
            price("supporter"),
            old.due_on,
            old.period,
        )
        assert new.charge.status == Charge.Status.PENDING
        link = AuditEntry.objects.get(action=mr.RENEWAL_FEE_LINKED, target_id=str(change.pk))
        assert (link.old_value, link.new_value) == (None, new.pk)

    def test_reissued_fee_keeps_the_reminders_already_sent(self, make_admin):  # noqa: F811
        member, old = self.future()
        Person.objects.filter(pk=member.person_id).update(contact_email="pere@example.org")
        assert fees.send_due_reminders(date(2027, 2, 23)) == 1  # 15 dies abans
        mr.approve_type_change(downgrade_request(member), by=make_admin("secretary"))
        assert fees.send_due_reminders(date(2027, 2, 24)) == 0
        assert OutgoingEmail.objects.filter(template=fees.REMINDER_TEMPLATE).count() == 1

    @pytest.mark.parametrize("in_process", ["attempt", "saved_card_reached"])
    def test_fee_in_payment_keeps_its_price_and_is_linked_p334(
        self,
        make_admin,  # noqa: F811
        in_process,
    ):
        from apps.payments import attempts
        from apps.payments.models import SavedCardAttempt

        member, old = self.future()
        attempt = attempts.create_attempt(old.charge, "card")
        if in_process == "saved_card_reached":
            SavedCardAttempt.objects.create(
                attempt=attempt, card=saved_card(member), reached_provider=True
            )
        change = downgrade_request(member)
        mr.approve_type_change(change, by=make_admin("secretary"))
        old.charge.refresh_from_db()
        assert old.charge.status == Charge.Status.PENDING  # ni anul·lada ni tornada a generar
        change.refresh_from_db()
        assert change.renewal_fee == old  # no queda encallat: el tipus canviarà igualment
        assert AuditEntry.objects.filter(action=mr.RENEWAL_FEE_IN_PROCESS).exists()
        assert full_price_notices() == 1

    def test_payment_status_is_read_again_under_the_lock(
        self,
        make_admin,  # noqa: F811
        monkeypatch,
    ):
        # Un pagament que arriba entre la lectura de la quota i l'anul·lació: la fila del càrrec
        # es torna a llegir bloquejada i la quota no s'anul·la.
        from apps.core import charges
        from apps.core.models import Payment

        member, fee = self.future()
        stale = AnnualFee.objects.select_related("charge").get(pk=fee.pk)
        payment = Payment.objects.create(
            charge=fee.charge,
            method=Payment.Method.DIRECT_DEBIT,
            amount_cents=fee.charge.amount_cents,
            paid_at=timezone.now(),
        )
        charges.mark_paid(fee.charge, payment, origin="provider", by=audit.system("proves"))
        charges.mark_returned(fee.charge, "AM04 Fons insuficients", by=make_admin("treasurer"))
        monkeypatch.setattr(mr, "_renewal_fee", lambda member: stale)
        change = downgrade_request(member)
        mr.approve_type_change(change, by=make_admin("secretary"))
        fee.charge.refresh_from_db()
        assert fee.charge.status == Charge.Status.RETURNED
        change.refresh_from_db()
        assert change.renewal_fee == fee

    @pytest.mark.parametrize("case", ["declined_notice", "saved_card_not_reached"])
    def test_a_card_that_did_not_charge_does_not_count_as_being_paid(
        self,
        make_admin,  # noqa: F811
        case,
    ):
        from apps.payments import attempts
        from apps.payments.models import SavedCardAttempt, SavedCardNotice

        member, old = self.future()
        card = saved_card(member)
        if case == "declined_notice":
            SavedCardNotice.objects.create(charge=old.charge, card=card, case="declined")
        else:
            attempt = attempts.create_attempt(old.charge, "card")
            SavedCardAttempt.objects.create(attempt=attempt, card=card, reached_provider=False)
        change = downgrade_request(member)
        mr.approve_type_change(change, by=make_admin("secretary"))
        old.charge.refresh_from_db()
        assert old.charge.status == Charge.Status.CANCELLED
        change.refresh_from_db()
        assert change.renewal_fee.charge.amount_cents == price("supporter")

    def test_renewal_fee_paid_early_is_linked_and_the_treasurer_notified(
        self,
        make_admin,  # noqa: F811
    ):
        member, fee = self.future()
        pay(fee, timezone.make_aware(datetime(2026, 11, 17, 12)))  # abans del venciment
        change = downgrade_request(member)
        mr.approve_type_change(change, by=make_admin("secretary"))
        change.refresh_from_db()
        assert change.renewal_fee == fee
        fee.charge.refresh_from_db()
        assert fee.charge.status == Charge.Status.PAID
        assert full_price_notices() == 1

    @pytest.mark.parametrize("case", ["pending", "returned"])
    def test_overdue_fee_is_never_repriced_or_linked(
        self,
        make_admin,  # noqa: F811
        case,
    ):
        # Quota de renovació vençuda el 10/03/2026 i pas acceptat després: res de retroactiu.
        from apps.core import charges
        from apps.core.models import Payment

        member = full_member()
        (fee,) = fees.generate_due_fees(date(2026, 2, 23))
        if case == "returned":
            payment = Payment.objects.create(
                charge=fee.charge,
                method=Payment.Method.DIRECT_DEBIT,
                amount_cents=fee.charge.amount_cents,
                paid_at=timezone.make_aware(datetime(2026, 3, 10, 12)),
            )
            charges.mark_paid(fee.charge, payment, origin="provider", by=audit.system("proves"))
            charges.mark_returned(fee.charge, "AM04 Fons insuficients", by=make_admin("treasurer"))
        change = downgrade_request(member)
        mr.approve_type_change(change, by=make_admin("secretary"))
        fee.charge.refresh_from_db()
        assert fee.charge.status != Charge.Status.CANCELLED
        change.refresh_from_db()
        assert change.renewal_fee is None
        assert full_price_notices() == 0
        assert mr.apply_due_downgrades(date(2026, 4, 15)) == []
        member.refresh_from_db()
        assert member.type.code == "full"
        if case == "pending":
            # S'aplica a la renovació següent: 12 mesos després del pagament (20/04/2026).
            pay(fee, timezone.make_aware(datetime(2026, 4, 20, 12)))
            (renewal,) = fees.generate_due_fees(date(2027, 4, 5))
            assert renewal.charge.amount_cents == price("supporter")
            change.refresh_from_db()
            assert change.renewal_fee == renewal

    def test_current_period_fee_already_paid_is_not_the_renewal(
        self,
        make_admin,  # noqa: F811
    ):
        # La quota del període en curs, pagada i vençuda, no és la renovació: no es lliga.
        member = full_member()
        change = downgrade_request(member)
        mr.approve_type_change(change, by=make_admin("secretary"))
        change.refresh_from_db()
        assert change.renewal_fee is None
        assert full_price_notices() == 0

    def test_cancelled_renewal_fee_is_replaced_and_relinked(self):
        from apps.core import charges

        member, change = self.accepted()
        (fee,) = fees.generate_due_fees(date(2026, 2, 23))
        charges.cancel(fee.charge, "Correcció inventada", by=audit.system("proves"))
        (replacement,) = fees.generate_due_fees(date(2026, 2, 24))
        change.refresh_from_db()
        assert change.renewal_fee == replacement
        assert replacement.charge.amount_cents == price("supporter")
        assert mr.apply_due_downgrades(RENEWAL) == [change]

    def test_cancelled_renewal_fee_without_replacement_is_notified_once(self):
        from apps.core import charges

        member, change = self.accepted()
        (fee,) = fees.generate_due_fees(date(2026, 2, 23))
        charges.cancel(fee.charge, "Correcció inventada", by=audit.system("proves"))
        assert mr.apply_due_downgrades(RENEWAL) == []
        assert mr.apply_due_downgrades(date(2026, 3, 11)) == []
        assert (
            AuditEntry.objects.filter(
                action=fees.NOTICE_SENT, details__event=fees.NOTICE_DOWNGRADE_FEE_CANCELLED
            ).count()
            == 1
        )

    def test_a_card_error_does_not_stop_the_type_change(self, monkeypatch):
        member, change = self.accepted()
        fees.generate_due_fees(date(2026, 2, 23))

        def boom(*args, **kwargs):
            raise RuntimeError("error inventat del carnet")

        monkeypatch.setattr(mr.cards, "replace_card", boom)
        assert mr.apply_due_downgrades(RENEWAL) == [change]
        member.refresh_from_db()
        assert member.type.code == "supporter"
        change.refresh_from_db()
        assert change.effective_on == RENEWAL
        assert AuditEntry.objects.filter(action=mr.DOWNGRADE_CARD_FAILED).exists()

    def test_renewal_fee_of_an_age_exempt_member_follows_next_fee_due(
        self,
        make_admin,  # noqa: F811
    ):
        from .test_cards import exempt_member

        member = exempt_member(birth=date(2015, 5, 1), number=4321)
        (old,) = fees.generate_due_fees(date(2029, 12, 17))  # primera quota: 01/01/2030
        change = downgrade_request(member)
        mr.approve_type_change(change, by=make_admin("secretary"))
        old.charge.refresh_from_db()
        assert old.charge.status == Charge.Status.CANCELLED
        change.refresh_from_db()
        assert change.renewal_fee.charge.amount_cents == price("supporter")

    def test_member_already_supporter_is_marked_applied_without_error(self):
        member, change = self.accepted()
        fees.generate_due_fees(date(2026, 2, 23))
        member.type = MembershipType.objects.get(code="supporter")  # canviat a mà
        member.save(update_fields=["type"])
        assert mr.apply_due_downgrades(RENEWAL) == [change]
        change.refresh_from_db()
        assert change.effective_on == RENEWAL
        assert mr.apply_due_downgrades(date(2026, 3, 11)) == []

    def test_one_failing_request_does_not_stop_the_others(self, monkeypatch):
        first, change_a = self.accepted()
        second = full_member("Joan")
        change_b = downgrade_request(second, status=RS.APPROVED)
        fees.generate_due_fees(date(2026, 2, 23))
        real = mr._change_type

        def boom(member, *args, **kwargs):
            if member.pk == first.pk:
                raise RuntimeError("error inventat")
            return real(member, *args, **kwargs)

        monkeypatch.setattr(mr, "_change_type", boom)
        assert mr.apply_due_downgrades(RENEWAL) == [change_b]
        change_a.refresh_from_db()
        assert change_a.effective_on is None

    def test_a_downgrade_from_before_a_leave_does_not_count(self):
        from datetime import timedelta

        from apps.members.models import MemberStatusChange

        member = full_member()
        change = downgrade_request(member, status=RS.APPROVED)
        MemberRequest.objects.filter(pk=change.pk).update(
            resolved_at=timezone.now() - timedelta(days=30)
        )
        # Baixa i readmissió sense passar per la validació de la baixa.
        for to_status in ("left", "pending", "active"):
            MemberStatusChange.objects.create(
                member=member,
                from_status=member.status,
                to_status=to_status,
                from_type=member.type,
                to_type=member.type,
                effective_on=date(2026, 1, 1),
                reason="Motiu inventat",
            )
        assert mr.accepted_downgrade(member) is None
        (fee,) = fees.generate_due_fees(date(2026, 2, 23))
        assert fee.charge.amount_cents == price("full")


def test_daily_task_goes_on_after_an_error(monkeypatch):
    from apps.members import tasks

    calls = []

    def boom(*args, **kwargs):
        raise RuntimeError("error inventat")

    monkeypatch.setattr(mr, "apply_due_downgrades", boom)
    monkeypatch.setattr(fees, "send_renewal_notices", lambda: calls.append("avisos"))
    monkeypatch.setattr(fees, "generate_due_fees", lambda: calls.append("quotes"))
    monkeypatch.setattr(fees, "send_due_reminders", lambda: calls.append("recordatoris"))
    with pytest.raises(RuntimeError):
        tasks.daily_fees.func(0)
    assert calls == ["avisos", "quotes", "recordatoris"]


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


@pytest.mark.parametrize(("months", "errors"), [(1, 0), (2, 0), (0, 1)])
def test_notice_window_is_at_least_one_month(months, errors):
    from apps.members.checks import renewal_notice_before_fee

    with override_settings(MEMBER_RENEWAL_NOTICE_MONTHS=months):
        found = renewal_notice_before_fee(None)
    assert len(found) == errors
    assert all(error.id == "members.E002" for error in found)
