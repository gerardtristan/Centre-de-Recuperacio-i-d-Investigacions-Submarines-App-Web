"""Proves de contracte dels serveis que el M01 ofereix a altres mòduls (T-M01-26; M01-8,
M01-11 «Contracte»; CA-M01-06, CA-M01-13 i 14 al servei). Forma exacta de la resposta, cap
escriptura als serveis de lectura i casos límit (sense soci, pendent, impagat, de baixa,
anonimitzat). Només dades inventades."""

from dataclasses import FrozenInstanceError, asdict
from datetime import date, timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.core import charges
from apps.core.models import AuditEntry, Charge, Person
from apps.members import cards, services
from apps.members.fee_rules import local_today
from apps.members.models import (
    AnnualFee,
    Member,
    MemberCard,
    MembershipType,
    MemberStatusChange,
)
from apps.members.roster import twelve_months_after
from apps.members.services import InvalidTransition, MemberStats, MemberSummary, NotAMember
from apps.members.tests.test_cards import SYSTEM, add_fee, make_member, paid_member, pay

S = Member.Status
INVALID = {"valid": False, "partial_number": ""}
READ_PREFIXES = ("SELECT", "SAVEPOINT", "RELEASE SAVEPOINT", "ROLLBACK TO SAVEPOINT")


def read_only(fn, *args, **kwargs):
    """Executa el servei i comprova que no ha enviat cap escriptura a la base de dades."""
    with CaptureQueriesContext(connection) as ctx:
        result = fn(*args, **kwargs)
    writes = [
        q["sql"] for q in ctx.captured_queries if not q["sql"].lstrip().startswith(READ_PREFIXES)
    ]
    assert writes == []
    return result


def person(first="Pere"):
    return Person.objects.create(first_name=first, last_name="Prova", origin=Person.Origin.WEB)


def full():
    return MembershipType.objects.get(code="full")


def supporter():
    return MembershipType.objects.get(code="supporter")


def change(member, from_status, to_status, effective_on, *, from_type=None, to_type=None):
    # Historial desat directament: el que interessa aquí és la lectura per dates.
    return MemberStatusChange.objects.create(
        member=member,
        from_status=from_status,
        to_status=to_status,
        from_type=from_type or member.type,
        to_type=to_type or member.type,
        effective_on=effective_on,
        reason="Motiu de prova" if to_status in (S.LEFT, S.UNPAID) else "",
    )


def left_member(*args, left_on=date(2025, 6, 1), **kwargs):
    return make_member(*args, status=S.LEFT, left_on=left_on, **kwargs)


def history(member):
    return list(MemberStatusChange.objects.filter(member=member))


# --- is_member ------------------------------------------------------------------------------


@pytest.mark.django_db
class TestIsMember:
    def test_a_person_without_member_is_not_a_member(self):
        assert read_only(services.is_member, person()) is False

    @pytest.mark.parametrize(
        ("status", "expected"),
        [(S.ACTIVE, True), (S.UNPAID, True), (S.PENDING, False), (S.LEFT, False)],
    )
    def test_today_active_or_unpaid(self, status, expected):
        extra = {"left_on": date(2025, 6, 1)} if status == S.LEFT else {}
        member = make_member(status=status, **extra)
        assert read_only(services.is_member, member.person) is expected
        assert services.is_member(member.person, on=local_today()) is expected

    def test_a_future_date_uses_the_current_status(self):
        member = make_member(status=S.ACTIVE)
        assert services.is_member(member.person, on=local_today() + timedelta(days=60)) is True

    def test_a_past_date_reads_the_history(self):
        member = make_member(status=S.LEFT, left_on=date(2025, 6, 1), joined_on=date(2025, 1, 10))
        change(member, "", S.PENDING, date(2025, 1, 10))
        change(member, S.PENDING, S.ACTIVE, date(2025, 2, 1))
        change(member, S.ACTIVE, S.LEFT, date(2025, 6, 1))
        on = services.is_member
        assert read_only(on, member.person, on=date(2025, 1, 31)) is False  # pendent
        assert on(member.person, on=date(2025, 2, 1)) is True
        assert on(member.person, on=date(2025, 5, 31)) is True
        assert on(member.person, on=date(2025, 6, 1)) is False  # de baixa

    def test_before_the_first_change_it_is_the_previous_status(self):
        member = make_member(status=S.LEFT, left_on=date(2025, 6, 1), joined_on=date(2019, 3, 12))
        change(member, S.UNPAID, S.LEFT, date(2025, 6, 1))
        assert services.is_member(member.person, on=date(2025, 5, 1)) is True  # impagat

    def test_before_joining_without_history_it_is_not_a_member(self):
        member = make_member(status=S.ACTIVE, joined_on=date(2025, 3, 1))
        assert services.is_member(member.person, on=date(2025, 2, 28)) is False
        assert services.is_member(member.person, on=date(2025, 3, 1)) is True

    def test_a_backdated_change_counts_from_its_effective_date(self):
        member = make_member(status=S.LEFT, left_on=date(2025, 5, 1))
        change(member, S.ACTIVE, S.UNPAID, date(2025, 5, 10))
        change(member, S.UNPAID, S.LEFT, date(2025, 5, 1))  # desat després, amb data anterior
        assert services.is_member(member.person, on=date(2025, 5, 20)) is False


# --- get_member_summary ---------------------------------------------------------------------


@pytest.mark.django_db
class TestGetMemberSummary:
    def test_without_member_it_raises_not_a_member(self):
        with pytest.raises(NotAMember):
            read_only(services.get_member_summary, person())

    def test_exact_shape_of_an_active_member(self):
        member = make_member(number=1287)
        paid_at = timezone.now() - timedelta(days=10)
        pay(add_fee(member), paid_at)
        summary = read_only(services.get_member_summary, member.person)
        assert isinstance(summary, MemberSummary)
        assert asdict(summary) == {
            "person_id": member.person_id,
            "number": 1287,
            "type": "full",
            "type_name": "Ple dret",
            "status": S.ACTIVE,
            "valid_until": twelve_months_after(timezone.localdate(paid_at)),
        }

    def test_it_is_data_not_a_model(self):
        summary = services.get_member_summary(make_member().person)
        with pytest.raises(FrozenInstanceError):
            summary.status = S.LEFT

    @pytest.mark.parametrize("status", [S.PENDING, S.UNPAID, S.LEFT])
    def test_any_status_is_summarised_without_payment(self, status):
        extra = {"left_on": date(2025, 6, 1)} if status == S.LEFT else {}
        summary = services.get_member_summary(make_member(status=status, **extra).person)
        assert summary.status == status
        assert summary.valid_until is None

    def test_a_pending_member_may_have_no_number(self):
        summary = services.get_member_summary(make_member(status=S.PENDING, number=None).person)
        assert summary.number is None


# --- active_members_for_mandates ------------------------------------------------------------


@pytest.mark.django_db
class TestActiveMembersForMandates:
    def test_only_active_members_in_number_order(self):
        second = make_member("Berta", 1300, document="87654321X")
        first = make_member("Anna", 1287)
        make_member("Carla", 1301, status=S.PENDING, document="11111111H")
        make_member("Dani", 1302, status=S.UNPAID, document="22222222J")
        left_member("Eva", 1303, document="33333333P")
        result = read_only(services.active_members_for_mandates)
        assert [s.number for s in result] == [1287, 1300]
        assert [s.person_id for s in result] == [first.person_id, second.person_id]
        assert all(isinstance(s, MemberSummary) for s in result)

    def test_anonymised_persons_are_left_out(self):
        member = make_member()
        Person.objects.filter(pk=member.person_id).update(
            status=Person.Status.ANONYMISED, anonymous_ref="A-0001"
        )
        assert services.active_members_for_mandates() == []

    def test_no_members_gives_an_empty_list(self):
        assert services.active_members_for_mandates() == []


# --- verify_card ----------------------------------------------------------------------------


@pytest.mark.django_db
class TestVerifyCard:
    def test_valid_card_gives_valid_and_two_last_digits_only(self):
        token = cards.issue_card(paid_member(number=1287), by=SYSTEM)
        assert read_only(services.verify_card, token) == {"valid": True, "partial_number": "··87"}

    @pytest.mark.parametrize("token", ["inventat", "", None])
    def test_unknown_token_has_the_same_shape(self, token):
        paid_member()
        assert read_only(services.verify_card, token) == INVALID

    def test_revoked_card_has_the_same_shape(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        cards.revoke_card(member, by=SYSTEM, reason="Perdut")
        assert services.verify_card(token) == INVALID

    def test_unpaid_member_card_has_the_same_shape(self):
        member = paid_member()
        token = cards.issue_card(member, by=SYSTEM)
        Member.objects.filter(pk=member.pk).update(status=S.UNPAID)
        assert services.verify_card(token) == INVALID


# --- stats ----------------------------------------------------------------------------------


@pytest.mark.django_db
class TestStats:
    def test_counts_by_type_and_status_and_the_month(self):
        today = local_today()
        make_member("Anna", 1, joined_on=today)
        berta = make_member("Berta", 2, document="87654321X")
        Member.objects.filter(pk=berta.pk).update(type=supporter())
        make_member("Carla", 3, status=S.PENDING, document="11111111H", joined_on=today)
        gone = left_member("Dani", 4, document="22222222J", left_on=today)
        change(gone, S.ACTIVE, S.LEFT, today)
        # Un canvi de tipus d'un soci de baixa no és una altra baixa.
        change(gone, S.LEFT, S.LEFT, today, from_type=full(), to_type=supporter())
        result = read_only(services.stats)
        assert isinstance(result, MemberStats)
        assert result.by_type_and_status == {
            ("full", S.ACTIVE): 1,
            ("supporter", S.ACTIVE): 1,
            ("full", S.PENDING): 1,
            ("full", S.LEFT): 1,
        }
        assert (result.joined, result.left) == (2, 1)

    def test_a_past_date_reads_the_history_and_that_month(self):
        member = make_member(status=S.LEFT, left_on=date(2025, 6, 1), joined_on=date(2025, 1, 10))
        change(member, "", S.PENDING, date(2025, 1, 10))
        change(member, S.PENDING, S.ACTIVE, date(2025, 2, 1))
        change(member, S.ACTIVE, S.LEFT, date(2025, 6, 1))
        assert services.stats(on=date(2024, 12, 31)) == MemberStats({}, 0, 0)
        assert services.stats(on=date(2025, 1, 20)) == MemberStats({("full", S.PENDING): 1}, 1, 0)
        assert services.stats(on=date(2025, 3, 1)) == MemberStats({("full", S.ACTIVE): 1}, 0, 0)
        assert services.stats(on=date(2025, 6, 30)) == MemberStats({("full", S.LEFT): 1}, 0, 1)

    def test_only_counts_no_personal_data(self):
        make_member()
        result = services.stats()
        assert all(isinstance(v, int) for v in result.by_type_and_status.values())
        assert all(k[0] in {"full", "supporter"} for k in result.by_type_and_status)
        assert "Anna" not in repr(result) and "12345678Z" not in repr(result)


# --- on_fee_paid ----------------------------------------------------------------------------


def paid_fee(member, *, amount=None):
    fee = add_fee(member)
    pay(fee, amount=amount)
    return fee


@pytest.mark.django_db
class TestOnFeePaid:
    def test_ca_m01_06_pending_becomes_active_with_a_valid_card(self):
        member = make_member(status=S.PENDING)
        fee = paid_fee(member)
        result = services.on_fee_paid(fee.pk)
        assert result.status == S.ACTIVE
        card = MemberCard.objects.get(member=member)
        assert cards.validity(cards.load_member(member.pk), card).valid
        entry = MemberStatusChange.objects.get(member=member)
        assert (entry.from_status, entry.to_status, entry.actor_account) == (
            S.PENDING,
            S.ACTIVE,
            None,
        )
        assert entry.effective_on == local_today()
        audited = AuditEntry.objects.filter(action=services.STATUS_CHANGED)
        assert audited.exists()
        assert {(e.actor_kind, e.actor_origin) for e in audited} == {
            (AuditEntry.ActorKind.SYSTEM, services.FEE_PAID_ORIGIN)
        }
        assert AuditEntry.objects.filter(action=cards.CARD_ISSUED).count() == 1

    def test_it_is_idempotent(self):
        member = make_member(status=S.PENDING)
        fee = paid_fee(member)
        services.on_fee_paid(fee.pk)
        before = AuditEntry.objects.count()
        services.on_fee_paid(fee.pk)
        assert MemberCard.objects.filter(member=member).count() == 1
        assert len(history(member)) == 1
        assert AuditEntry.objects.count() == before

    def test_an_unpaid_charge_is_rejected_without_writing(self):
        member = make_member(status=S.PENDING)
        fee = add_fee(member)
        pay(fee, amount=4500)  # parcial: el càrrec continua pendent
        before = AuditEntry.objects.count()
        with pytest.raises(InvalidTransition):
            services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.PENDING
        assert not MemberCard.objects.exists()
        assert history(member) == []
        assert AuditEntry.objects.count() == before

    def test_a_charge_of_another_person_is_rejected(self):
        member = make_member(status=S.PENDING)
        other = person("Altra")
        charge = charges.create_charge(
            other,
            kind=Charge.Kind.FEE,
            amount_cents=9000,
            concept="Quota",
            origin="members",
            by=SYSTEM,
        )
        fee = AnnualFee.objects.create(
            member=member,
            period=2026,
            kind=AnnualFee.Kind.ANNUAL,
            charge=charge,
            due_on=date(2026, 1, 1),
        )
        pay(fee)
        with pytest.raises(InvalidTransition):
            services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.PENDING

    def test_partial_payments_are_not_decided_p_61(self):
        member = make_member(status=S.PENDING)
        fee = add_fee(member)
        first = pay(fee, amount=4500)
        pay(fee, amount=4500)
        charges.mark_paid(fee.charge, first, origin="provider", by=SYSTEM)
        with pytest.raises(InvalidTransition):
            services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.PENDING
        assert not MemberCard.objects.exists()

    def test_unpaid_member_stays_unpaid_and_is_recorded(self):
        member = make_member(status=S.UNPAID)
        fee = paid_fee(member)
        services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.UNPAID
        assert history(member) == []
        assert not MemberCard.objects.exists()
        entry = AuditEntry.objects.get(action=services.FEE_PAID_WHILE_UNPAID)
        assert (entry.target_type, entry.target_id) == ("members.annualfee", str(fee.pk))

    def test_active_member_renewal_changes_nothing(self):
        member = paid_member()
        cards.issue_card(member, by=SYSTEM)
        fee = add_fee(member, period=2027)
        pay(fee)
        before = AuditEntry.objects.count()
        services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE
        assert MemberCard.objects.filter(member=member).count() == 1
        assert AuditEntry.objects.count() == before

    def test_left_member_is_an_invalid_transition(self):
        member = left_member()
        fee = paid_fee(member)
        with pytest.raises(InvalidTransition):
            services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.LEFT
        assert history(member) == []

    def test_a_type_change_supplement_does_not_activate(self):
        member = make_member(status=S.PENDING)
        charge = charges.create_charge(
            member.person,
            kind=Charge.Kind.FEE,
            amount_cents=5500,
            concept="Suplement",
            origin="members",
            by=SYSTEM,
        )
        fee = AnnualFee.objects.create(
            member=member,
            period=2026,
            kind=AnnualFee.Kind.TYPE_CHANGE_SUPPLEMENT,
            charge=charge,
            due_on=date(2026, 1, 1),
        )
        pay(fee)
        services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.PENDING

    def test_a_leftover_card_is_revoked_before_the_new_one(self):
        member = make_member(status=S.PENDING)
        old = MemberCard.objects.create(member=member, token_hash="a" * 64)
        services.on_fee_paid(paid_fee(member).pk)
        old.refresh_from_db()
        assert old.revoked_at is not None and old.revoked_reason
        assert MemberCard.objects.filter(member=member, revoked_at__isnull=True).count() == 1

    def test_all_or_nothing_if_the_card_fails(self, monkeypatch):
        member = make_member(status=S.PENDING)
        fee = paid_fee(member)

        def broken(*args, **kwargs):
            raise RuntimeError("error de prova")

        monkeypatch.setattr(cards, "issue_card", broken)
        with pytest.raises(RuntimeError):
            services.on_fee_paid(fee.pk)
        assert Member.objects.get(pk=member.pk).status == S.PENDING
        assert history(member) == []


# --- on_fee_returned ------------------------------------------------------------------------


@pytest.mark.django_db
class TestOnFeeReturned:
    @pytest.mark.parametrize("status", [S.ACTIVE, S.UNPAID, S.PENDING])
    def test_it_never_changes_the_status_and_is_recorded(self, status):
        member = make_member(status=status)
        fee = add_fee(member)
        assert services.on_fee_returned(fee.pk) is None
        assert Member.objects.get(pk=member.pk).status == status
        assert history(member) == []
        entry = AuditEntry.objects.get(action=services.FEE_RETURNED)
        assert entry.actor_origin == services.FEE_RETURNED_ORIGIN
        assert (entry.target_type, entry.target_id) == ("members.annualfee", str(fee.pk))
