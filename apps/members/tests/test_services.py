"""Serveis d'estat i transicions del M01 (T-M01-12; RN-M01-07 a RN-M01-09, 067).

Decisions de l'aprovació del pla de la T-M01-12 (planning.md, lectura de les tasques
substituïdes). La part del carnet de CA-M01-09 («no vàlid») no es comprova aquí: és de la
T-M01-19 i la T-M01-20. Només dades inventades.
"""

import datetime
import hashlib
import itertools

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import AccountRole, AuditEntry, Person, Role
from apps.members import services
from apps.members.models import (
    Member,
    MemberCard,
    MemberRequest,
    MembershipNumberCounter,
    MembershipType,
    MemberStatusChange,
)
from apps.members.services import InactiveAccount, InvalidTransition, OwnMemberChange
from conftest import CommittedDataTestCase, run_together

S = Member.Status
JOINED = datetime.date(2020, 1, 15)
LEFT_ON = datetime.date(2024, 6, 30)
REASON = "Motiu inventat de proves"
SYSTEM = audit.system("proves-t-m01-12")

# RN-M01-07: les úniques transicions que `_change_status` fa. Actiu ↔ impagat són de
# `mark_unpaid`/`unmark_unpaid` (P9) i baixa → pendent, de `_readmit` (067).
CHANGE_STATUS_ALLOWED = {
    (S.PENDING, S.ACTIVE),
    (S.PENDING, S.LEFT),
    (S.ACTIVE, S.LEFT),
    (S.UNPAID, S.LEFT),
}
ALL_PAIRS = list(itertools.product(S.values, repeat=2))


def today():
    return timezone.localdate()


def history(member):
    return list(MemberStatusChange.objects.filter(member=member).order_by("created_at", "id"))


def audit_entries(member, action=None):
    entries = AuditEntry.objects.filter(
        target_type="members.member", target_id=str(member.pk)
    ).order_by("id")
    return list(entries.filter(action=action) if action else entries)


def snapshot(member):
    member = Member.objects.get(pk=member.pk)
    return (member.status, member.type_id, member.left_on, member.avatar_seed, member.member_number)


def make_admin(*roles, person=None):
    person = person or Person.objects.create(first_name="Gestor", origin="in_person")
    account = Account.objects.create_admin(person, f"gestor{person.pk}")
    for code in roles:
        AccountRole.objects.create(admin_account=account, role=Role.objects.get(code=code))
    return account


@pytest.fixture
def supporter(db):
    return MembershipType.objects.get(code="supporter")


@pytest.fixture
def full(db):
    return MembershipType.objects.get(code="full")


@pytest.fixture
def make_member(make_person, supporter):
    def make(status=S.ACTIVE, person=None, **fields):
        fields.setdefault("type", supporter)
        fields.setdefault("joined_on", JOINED)
        if status == S.LEFT:
            fields.setdefault("left_on", LEFT_ON)
        fields.setdefault("member_number", 87)
        return Member.objects.create(person=person or make_person(), status=status, **fields)

    return make


@pytest.fixture
def actor(db):
    return make_admin(Role.Code.SECRETARY)


@pytest.fixture
def treasurer(db):
    return make_admin(Role.Code.TREASURER)


def change(member, to_status, by, **kwargs):
    kwargs.setdefault("effective_on", today())
    kwargs.setdefault("reason", REASON)
    return services._change_status(member, to_status, by=by, **kwargs)


# --- CA-M01-07: transicions permeses i rebutjades ---------------------------------------


class TestTransitionMatrix:
    @pytest.mark.parametrize(("from_status", "to_status"), ALL_PAIRS)
    def test_change_status_only_allows_rn_m01_07(self, make_member, actor, from_status, to_status):
        member = make_member(status=from_status)
        before = snapshot(member)
        if (from_status, to_status) in CHANGE_STATUS_ALLOWED:
            change(member, to_status, actor)
            assert Member.objects.get(pk=member.pk).status == to_status
            assert len(history(member)) == 1
        else:
            with pytest.raises(InvalidTransition):
                change(member, to_status, actor)
            assert snapshot(member) == before
            assert history(member) == []
            assert audit_entries(member) == []

    @pytest.mark.parametrize("to_status", ["baixa", None])
    def test_unknown_status_is_an_invalid_transition(self, make_member, actor, to_status):
        # Regressió de la revisió de codi: abans sortia un ValueError en compondre el missatge.
        member = make_member(status=S.ACTIVE)
        with pytest.raises(InvalidTransition):
            change(member, to_status, actor)
        assert history(member) == []

    @pytest.mark.parametrize("from_status", [S.PENDING, S.UNPAID, S.LEFT])
    def test_mark_unpaid_only_from_active(self, make_member, treasurer, from_status):
        member = make_member(status=from_status)
        with pytest.raises(InvalidTransition):
            services.mark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
        assert Member.objects.get(pk=member.pk).status == from_status
        assert history(member) == []

    @pytest.mark.parametrize("from_status", [S.PENDING, S.ACTIVE, S.LEFT])
    def test_unmark_unpaid_only_from_unpaid(self, make_member, treasurer, from_status):
        member = make_member(status=from_status)
        with pytest.raises(InvalidTransition):
            services.unmark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
        assert Member.objects.get(pk=member.pk).status == from_status
        assert history(member) == []

    def test_public_api_is_only_the_authorised_services(self):
        assert set(services.__all__) == {
            "InactiveAccount",
            "InvalidTransition",
            "OwnMemberChange",
            "ensure_not_own_member",
            "mark_unpaid",
            "unmark_unpaid",
            # Serveis de M01-8 (T-M01-26); les primitives `_…` continuen fora.
            "MemberStats",
            "MemberSummary",
            "NotAMember",
            "active_members_for_mandates",
            "get_member_summary",
            "is_member",
            "on_fee_paid",
            "on_fee_returned",
            "stats",
            "verify_card",
            # Lectura de la llicència (T-M01-30), afegida en integrar la T-M01-26.
            "LicenceInfo",
            "licence_record",
            "licence_records",
        }


# --- CA-M01-08: historial i registre d'activitat --------------------------------------


class TestHistoryAndAudit:
    def test_status_change_writes_history_and_audit_with_old_value(self, make_member, actor):
        member = make_member(status=S.ACTIVE)
        change(member, S.LEFT, actor, effective_on=LEFT_ON)

        (entry,) = history(member)
        assert (entry.from_status, entry.to_status) == (S.ACTIVE, S.LEFT)
        assert entry.from_type_id == entry.to_type_id == member.type_id
        assert entry.effective_on == LEFT_ON
        assert entry.reason == REASON
        assert entry.actor_account == actor

        entries = {e.field: e for e in audit_entries(member, services.STATUS_CHANGED)}
        assert set(entries) == {"status", "left_on"}
        assert (entries["status"].old_value, entries["status"].new_value) == ("active", "left")
        assert (entries["left_on"].old_value, entries["left_on"].new_value) == (
            None,
            LEFT_ON.isoformat(),
        )
        assert entries["status"].reason == REASON
        assert entries["status"].actor_account == actor

    def test_leaving_sets_left_on_to_the_effective_date(self, make_member, actor):
        member = make_member(status=S.PENDING)
        change(member, S.LEFT, actor, effective_on=LEFT_ON)
        assert Member.objects.get(pk=member.pk).left_on == LEFT_ON

    def test_type_change_writes_history_and_audit(self, make_member, actor, supporter, full):
        member = make_member(status=S.ACTIVE)
        services._change_type(member, full, by=actor, effective_on=today())

        assert Member.objects.get(pk=member.pk).type == full
        (entry,) = history(member)
        assert (entry.from_status, entry.to_status) == (S.ACTIVE, S.ACTIVE)
        assert (entry.from_type, entry.to_type) == (supporter, full)
        (audited,) = audit_entries(member, services.TYPE_CHANGED)
        assert (audited.field, audited.old_value, audited.new_value) == (
            "type",
            "supporter",
            "full",
        )

    def test_type_change_to_the_same_type_is_rejected(self, make_member, actor, supporter):
        member = make_member(status=S.ACTIVE)
        with pytest.raises(InvalidTransition):
            services._change_type(member, supporter, by=actor, effective_on=today())
        assert history(member) == []

    def test_type_change_of_unpaid_member_needs_reason(self, make_member, actor, full):
        # Limitació actual del model (restricció de la T-M01-11), no regla nova.
        member = make_member(status=S.UNPAID)
        with pytest.raises(ValidationError):
            services._change_type(member, full, by=actor, effective_on=today())
        assert history(member) == []
        services._change_type(member, full, by=actor, effective_on=today(), reason=REASON)
        assert Member.objects.get(pk=member.pk).type == full

    def test_system_actor_leaves_history_actor_empty(self, make_member):
        member = make_member(status=S.PENDING)
        change(member, S.ACTIVE, SYSTEM, reason="")
        (entry,) = history(member)
        assert entry.actor_account is None
        (audited,) = audit_entries(member, services.STATUS_CHANGED)
        assert audited.actor_kind == AuditEntry.ActorKind.SYSTEM
        assert audited.actor_origin == "proves-t-m01-12"

    @pytest.mark.parametrize("by", [None, audit.ANONYMOUS])
    def test_change_without_author_is_rejected(self, make_member, by):
        member = make_member(status=S.PENDING)
        with pytest.raises(ValidationError):
            change(member, S.ACTIVE, by)
        assert history(member) == []

    def test_reason_required_to_leave(self, make_member, actor):
        member = make_member(status=S.ACTIVE)
        with pytest.raises(ValidationError):
            change(member, S.LEFT, actor, reason="   ")
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE
        assert history(member) == []

    def test_transitions_never_touch_the_avatar_seed(self, make_member, treasurer, actor):
        member = make_member(status=S.ACTIVE)
        seed = member.avatar_seed
        services.mark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
        services.unmark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
        change(member, S.LEFT, actor)
        assert Member.objects.get(pk=member.pk).avatar_seed == seed

    def test_failure_half_way_leaves_nothing_written(self, make_member, actor, monkeypatch):
        member = make_member(status=S.ACTIVE)
        before = snapshot(member)

        def broken(*args, **kwargs):
            raise RuntimeError("registre d'activitat no disponible (simulat)")

        monkeypatch.setattr(services.audit, "record_changes", broken)
        with pytest.raises(RuntimeError):
            change(member, S.LEFT, actor)
        assert snapshot(member) == before
        assert history(member) == []


# --- Dates efectives i `left_on` (D2, D3) ---------------------------------------------


class TestDates:
    def test_future_effective_date_is_rejected(self, make_member, actor):
        member = make_member(status=S.ACTIVE)
        with pytest.raises(ValidationError):
            change(member, S.LEFT, actor, effective_on=today() + datetime.timedelta(days=1))
        assert snapshot(member)[0] == S.ACTIVE
        assert history(member) == []

    def test_today_is_accepted(self, make_member, actor):
        member = make_member(status=S.ACTIVE)
        change(member, S.LEFT, actor, effective_on=today())
        assert Member.objects.get(pk=member.pk).left_on == today()

    def test_leaving_before_joining_is_rejected(self, make_member, actor):
        member = make_member(status=S.ACTIVE)
        with pytest.raises(ValidationError):
            change(member, S.LEFT, actor, effective_on=JOINED - datetime.timedelta(days=1))
        assert history(member) == []

    def test_leaving_on_the_joining_day_is_accepted(self, make_member, actor):
        member = make_member(status=S.ACTIVE)
        change(member, S.LEFT, actor, effective_on=JOINED)
        assert Member.objects.get(pk=member.pk).left_on == JOINED

    @pytest.mark.parametrize(
        "value", [None, "2026-01-01", datetime.datetime(2025, 1, 1, tzinfo=datetime.UTC)]
    )
    def test_effective_date_must_be_a_date(self, make_member, actor, value):
        member = make_member(status=S.PENDING)
        with pytest.raises(ValidationError):
            change(member, S.ACTIVE, actor, effective_on=value)

    def test_left_on_on_a_member_that_has_not_left_is_rejected(self, make_member, treasurer):
        member = make_member(status=S.ACTIVE, left_on=LEFT_ON)
        with pytest.raises(InvalidTransition):
            services.mark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
        assert snapshot(member)[0] == S.ACTIVE
        assert history(member) == []


# --- CA-M01-09: impagat manual amb P9 i motiu ------------------------------------------


class TestUnpaid:
    @pytest.mark.parametrize("reason", ["", "   "])
    def test_mark_without_reason_is_rejected(self, make_member, treasurer, reason):
        member = make_member(status=S.ACTIVE)
        with pytest.raises(ValidationError):
            services.mark_unpaid(member, by=treasurer, effective_on=today(), reason=reason)
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE
        assert history(member) == []

    def test_mark_and_unmark_with_reason(self, make_member, treasurer):
        member = make_member(status=S.ACTIVE)
        services.mark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
        assert Member.objects.get(pk=member.pk).status == S.UNPAID

        with pytest.raises(ValidationError):
            services.unmark_unpaid(member, by=treasurer, effective_on=today(), reason="")
        services.unmark_unpaid(member, by=treasurer, effective_on=today(), reason="Ja ha pagat")
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE

        marked, unmarked = history(member)
        assert (marked.to_status, marked.reason, marked.actor_account) == (
            S.UNPAID,
            REASON,
            treasurer,
        )
        assert (unmarked.from_status, unmarked.to_status, unmarked.reason) == (
            S.UNPAID,
            S.ACTIVE,
            "Ja ha pagat",
        )
        reasons = [e.reason for e in audit_entries(member, services.STATUS_CHANGED)]
        assert reasons == [REASON, "Ja ha pagat"]

    @pytest.mark.parametrize(
        "roles", [(Role.Code.SECRETARY,), (Role.Code.ADMINISTRATOR,), (Role.Code.PRESIDENT,), ()]
    )
    def test_without_p9_is_not_found(self, make_member, roles):
        member = make_member(status=S.ACTIVE)
        with pytest.raises(Http404):
            services.mark_unpaid(member, by=make_admin(*roles), effective_on=today(), reason=REASON)
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE
        assert history(member) == []

    def test_system_cannot_mark_unpaid(self, make_member):
        # RN-M01-09 i 040: l'impagat no és automàtic.
        member = make_member(status=S.ACTIVE)
        with pytest.raises(Http404):
            services.mark_unpaid(member, by=SYSTEM, effective_on=today(), reason=REASON)
        assert history(member) == []

    @pytest.mark.parametrize("to_status", [S.UNPAID, S.ACTIVE])
    def test_change_status_cannot_bypass_p9(self, make_member, treasurer, to_status):
        member = make_member(status=S.ACTIVE if to_status == S.UNPAID else S.UNPAID)
        with pytest.raises(InvalidTransition):
            change(member, to_status, treasurer)
        assert history(member) == []

    def test_marking_unpaid_does_not_touch_the_card(self, make_member, treasurer):
        # D1: estat i validesa van separats; la resposta «No vàlid» és de la T-M01-19/20.
        member = make_member(status=S.ACTIVE)
        card = MemberCard.objects.create(
            member=member, token_hash=hashlib.sha256(b"testimoni-inventat").hexdigest()
        )
        before = MemberCard.objects.filter(pk=card.pk).values().get()
        services.mark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
        assert MemberCard.objects.filter(pk=card.pk).values().get() == before
        services.unmark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
        assert MemberCard.objects.filter(pk=card.pk).values().get() == before
        assert MemberCard.objects.filter(member=member).count() == 1


# --- Conflicte d'interès (S-M01-22) -----------------------------------------------------


class TestOwnMember:
    def test_treasurer_cannot_mark_own_member_and_attempt_is_kept(self, make_member):
        member = make_member(status=S.ACTIVE)
        own = make_admin(Role.Code.TREASURER, person=member.person)
        with pytest.raises(OwnMemberChange):
            services.mark_unpaid(member, by=own, effective_on=today(), reason=REASON)
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE
        assert history(member) == []
        (attempt,) = audit_entries(member, services.OWN_MEMBER_REJECTED)
        assert attempt.actor_account == own

    def test_primitives_reject_own_member(self, make_member, full):
        member = make_member(status=S.ACTIVE)
        own = make_admin(Role.Code.SECRETARY, person=member.person)
        with pytest.raises(OwnMemberChange):
            change(member, S.LEFT, own)
        with pytest.raises(OwnMemberChange):
            services._change_type(member, full, by=own, effective_on=today())
        assert history(member) == []
        assert len(audit_entries(member, services.OWN_MEMBER_REJECTED)) == 2


# --- Readmissió (067, D5) ---------------------------------------------------------------


@pytest.fixture
def left_member(make_member, actor):
    """Soci de baixa per la plataforma: l'historial té la baixa amb la data de `left_on`."""
    member = make_member(status=S.ACTIVE)
    change(member, S.LEFT, actor, effective_on=LEFT_ON)
    return Member.objects.get(pk=member.pk)


@pytest.fixture
def join_request(left_member, supporter):
    return MemberRequest.objects.create(
        kind=MemberRequest.Kind.JOIN,
        person=left_member.person,
        requested_type=supporter,
        channel=MemberRequest.Channel.WEB,
    )


def readmit(member, request, by, **kwargs):
    kwargs.setdefault("effective_on", today())
    return services._readmit(member, request, by=by, **kwargs)


class TestReadmission:
    def test_keeps_the_same_record_and_number_and_clears_left_on(
        self, left_member, join_request, actor
    ):
        counter = MembershipNumberCounter.objects.get().last_number
        before = Member.objects.get(pk=left_member.pk)

        readmit(left_member, join_request, actor)

        after = Member.objects.get(pk=left_member.pk)
        assert after.status == S.PENDING
        assert after.left_on is None
        assert (after.pk, after.member_number, after.joined_on, after.avatar_seed) == (
            before.pk,
            before.member_number,
            before.joined_on,
            before.avatar_seed,
        )
        assert MembershipNumberCounter.objects.get().last_number == counter
        assert Member.objects.filter(person=left_member.person).count() == 1

        leave, back = history(left_member)
        assert (leave.to_status, leave.effective_on) == (S.LEFT, LEFT_ON)
        assert (back.from_status, back.to_status, back.effective_on) == (S.LEFT, S.PENDING, today())
        assert back.actor_account == actor

        entries = {
            e.field: e
            for e in audit_entries(left_member, services.STATUS_CHANGED)
            if e.new_value in ("pending", None)
        }
        assert (entries["status"].old_value, entries["status"].new_value) == ("left", "pending")
        assert (entries["left_on"].old_value, entries["left_on"].new_value) == (
            LEFT_ON.isoformat(),
            None,
        )
        # L'aprovació de la sol·licitud és de la T-M01-14.
        assert MemberRequest.objects.get(pk=join_request.pk).status == MemberRequest.Status.PENDING

    def test_outer_rollback_undoes_the_readmission(self, left_member, join_request, actor):
        before = snapshot(left_member)
        entries = len(audit_entries(left_member))
        with pytest.raises(RuntimeError), transaction.atomic():
            readmit(left_member, join_request, actor)
            raise RuntimeError("la resta de l'aprovació falla (simulat)")
        assert snapshot(left_member) == before
        assert len(history(left_member)) == 1
        assert len(audit_entries(left_member)) == entries

    @pytest.mark.parametrize("status", [S.PENDING, S.ACTIVE, S.UNPAID])
    def test_member_must_have_left(self, make_member, actor, supporter, status):
        member = make_member(status=status)
        request = MemberRequest.objects.create(
            kind="join", person=member.person, requested_type=supporter, channel="web"
        )
        with pytest.raises(InvalidTransition):
            readmit(member, request, actor)
        assert history(member) == []

    def test_request_must_be_a_join(self, left_member, actor, full):
        request = MemberRequest.objects.create(
            kind="change_type",
            person=left_member.person,
            member=left_member,
            requested_type=full,
            channel="web",
        )
        with pytest.raises(InvalidTransition):
            readmit(left_member, request, actor)
        assert len(history(left_member)) == 1

    def test_request_must_be_of_the_same_person(self, left_member, actor, supporter, make_person):
        request = MemberRequest.objects.create(
            kind="join", person=make_person("Pere", "Roca"), requested_type=supporter, channel="web"
        )
        with pytest.raises(InvalidTransition):
            readmit(left_member, request, actor)
        assert snapshot(left_member)[0] == S.LEFT

    @pytest.mark.parametrize(
        ("status", "resolution_reason"),
        [("approved", ""), ("rejected", "Motiu inventat"), ("cancelled", "")],
    )
    def test_request_must_be_pending(
        self, left_member, join_request, actor, status, resolution_reason
    ):
        MemberRequest.objects.filter(pk=join_request.pk).update(
            status=status, resolution_reason=resolution_reason
        )
        with pytest.raises(InvalidTransition):
            readmit(left_member, join_request, actor)
        assert snapshot(left_member)[0] == S.LEFT

    def test_leave_must_be_in_the_history(self, make_member, actor, supporter):
        member = make_member(status=S.LEFT)  # baixa sense entrada d'historial
        request = MemberRequest.objects.create(
            kind="join", person=member.person, requested_type=supporter, channel="web"
        )
        with pytest.raises(InvalidTransition):
            readmit(member, request, actor)
        assert Member.objects.get(pk=member.pk).left_on == LEFT_ON

    def test_leave_in_the_history_must_match_the_current_left_on(
        self, left_member, join_request, actor
    ):
        # Una baixa antiga no val: la data de l'última baixa ha de ser l'actual `left_on`.
        later = LEFT_ON + datetime.timedelta(days=1)
        Member.objects.filter(pk=left_member.pk).update(left_on=later)
        with pytest.raises(InvalidTransition):
            readmit(left_member, join_request, actor)
        assert snapshot(left_member)[2] == later

    def test_last_status_change_must_be_the_leave(self, left_member, join_request, actor):
        # Historial: la baixa i després una readmissió; el soci consta de baixa amb la mateixa
        # data, però l'últim canvi d'estat no és la baixa.
        MemberStatusChange.objects.create(
            member=left_member,
            from_status=S.LEFT,
            to_status=S.PENDING,
            from_type=left_member.type,
            to_type=left_member.type,
            effective_on=today(),
        )
        with pytest.raises(InvalidTransition):
            readmit(left_member, join_request, actor)
        assert snapshot(left_member)[0] == S.LEFT

    def test_only_through_readmit(self, left_member, actor):
        with pytest.raises(InvalidTransition):
            change(left_member, S.PENDING, actor)

    def test_system_cannot_readmit(self, left_member, join_request):
        with pytest.raises(ValidationError):
            readmit(left_member, join_request, SYSTEM)
        assert snapshot(left_member)[0] == S.LEFT

    def test_own_readmission_is_rejected_and_recorded(self, left_member, join_request):
        own = make_admin(Role.Code.SECRETARY, person=left_member.person)
        with pytest.raises(OwnMemberChange):
            readmit(left_member, join_request, own)
        assert snapshot(left_member)[0] == S.LEFT
        assert len(audit_entries(left_member, services.OWN_MEMBER_REJECTED)) == 1

    def test_readmission_before_the_leave_is_rejected(self, left_member, join_request, actor):
        with pytest.raises(ValidationError, match="anterior a la data de la baixa"):
            readmit(
                left_member, join_request, actor, effective_on=LEFT_ON - datetime.timedelta(days=1)
            )
        assert snapshot(left_member)[:3] == (S.LEFT, left_member.type_id, LEFT_ON)
        assert len(history(left_member)) == 1

    @pytest.mark.parametrize("days_after_leave", [0, 1])
    def test_readmission_on_or_after_the_leave_is_accepted(
        self, left_member, join_request, actor, days_after_leave
    ):
        effective_on = LEFT_ON + datetime.timedelta(days=days_after_leave)
        readmit(left_member, join_request, actor, effective_on=effective_on)
        assert snapshot(left_member)[0] == S.PENDING
        assert history(left_member)[-1].effective_on == effective_on

    def test_future_readmission_date_is_rejected(self, left_member, join_request, actor):
        tomorrow = today() + datetime.timedelta(days=1)
        with pytest.raises(ValidationError):
            readmit(left_member, join_request, actor, effective_on=tomorrow)
        assert snapshot(left_member)[0] == S.LEFT


# --- Compte no actiu ---------------------------------------------------------------------


def _deactivate(account):
    Account.objects.filter(pk=account.pk).update(status=Account.Status.DISABLED)


class TestInactiveAccount:
    @pytest.mark.parametrize("status", [Account.Status.DISABLED, Account.Status.PENDING])
    def test_inactive_account_cannot_use_the_primitives(
        self, left_member, join_request, make_member, full, status
    ):
        member = make_member(status=S.PENDING, member_number=88)
        account = make_admin(Role.Code.SECRETARY)
        Account.objects.filter(pk=account.pk).update(status=status)
        account.refresh_from_db()
        before, before_left = snapshot(member), snapshot(left_member)

        with pytest.raises(InactiveAccount):
            change(member, S.ACTIVE, account)
        with pytest.raises(InactiveAccount):
            services._change_type(member, full, by=account, effective_on=today())
        with pytest.raises(InactiveAccount):
            readmit(left_member, join_request, account)

        assert (snapshot(member), snapshot(left_member)) == (before, before_left)
        assert history(member) == []
        assert len(history(left_member)) == 1

    def test_stale_account_object_is_checked_against_the_database(self, make_member):
        # L'objecte encara diu «actiu», però a la base de dades ja està desactivat.
        member = make_member(status=S.PENDING)
        account = make_admin(Role.Code.SECRETARY)
        _deactivate(account)
        assert account.is_active
        with pytest.raises(InactiveAccount):
            change(member, S.ACTIVE, account)
        assert snapshot(member)[0] == S.PENDING
        assert history(member) == []

    def test_deactivated_treasurer_cannot_mark_unpaid(self, make_member, treasurer):
        member = make_member(status=S.ACTIVE)
        _deactivate(treasurer)
        # La mateixa resposta amb l'objecte desfasat i amb l'objecte al dia, abans del permís.
        for _attempt in ("desfasat", "al dia"):
            with pytest.raises(InactiveAccount):
                services.mark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)
            treasurer.refresh_from_db()
        assert snapshot(member)[0] == S.ACTIVE
        assert history(member) == []

    def test_deactivation_after_the_first_check_is_caught_inside_the_transaction(
        self, make_member, actor, monkeypatch
    ):
        # Es desactiva just després de la comprovació d'abans de la transacció: la de dins,
        # amb la fila del compte bloquejada, ho rebutja.
        member = make_member(status=S.PENDING)
        original = services.ensure_not_own_member

        def check_then_deactivate(*args, **kwargs):
            original(*args, **kwargs)
            _deactivate(actor)

        monkeypatch.setattr(services, "ensure_not_own_member", check_then_deactivate)
        with pytest.raises(InactiveAccount):
            change(member, S.ACTIVE, actor)
        assert snapshot(member)[0] == S.PENDING
        assert history(member) == []

    def test_inactive_account_on_its_own_member_leaves_no_attempt(self, make_member):
        # El compte no actiu es rebutja abans del conflicte d'interès: no hi ha intent nou.
        member = make_member(status=S.ACTIVE)
        own = make_admin(Role.Code.SECRETARY, person=member.person)
        _deactivate(own)
        with pytest.raises(InactiveAccount):
            change(member, S.LEFT, own)
        assert audit_entries(member) == []
        assert history(member) == []

    def test_system_actor_is_not_affected(self, make_member):
        member = make_member(status=S.PENDING)
        change(member, S.ACTIVE, SYSTEM, reason="")
        assert snapshot(member)[0] == S.ACTIVE


# --- Concurrència i registre de l'intent fora de transacció ----------------------------


def _committed_member(status, **fields):
    person = Person.objects.create(first_name="Anna", last_name="Puig", origin=Person.Origin.WEB)
    return Member.objects.create(
        person=person,
        type=MembershipType.objects.get(code="supporter"),
        joined_on=JOINED,
        status=status,
        **fields,
    )


def _outcome(function):
    def run():
        try:
            function()
            return "fet"
        except InvalidTransition:
            return "rebutjat"

    return run


class TestConcurrency(CommittedDataTestCase):
    def test_two_simultaneous_unpaid_marks_apply_once(self):
        member = _committed_member(S.ACTIVE)
        treasurer = make_admin(Role.Code.TREASURER)

        def mark():
            services.mark_unpaid(member, by=treasurer, effective_on=today(), reason=REASON)

        assert sorted(run_together([_outcome(mark), _outcome(mark)])) == ["fet", "rebutjat"]
        assert Member.objects.get(pk=member.pk).status == S.UNPAID
        assert len(history(member)) == 1

    def test_two_simultaneous_readmissions_apply_once(self):
        member = _committed_member(S.ACTIVE)
        secretary = make_admin(Role.Code.SECRETARY)
        change(member, S.LEFT, secretary, effective_on=LEFT_ON)
        request = MemberRequest.objects.create(
            kind="join",
            person=member.person,
            requested_type=MembershipType.objects.get(code="supporter"),
            channel="web",
        )

        def back():
            readmit(member, request, secretary)

        assert sorted(run_together([_outcome(back), _outcome(back)])) == ["fet", "rebutjat"]
        assert Member.objects.get(pk=member.pk).status == S.PENDING
        assert [e.to_status for e in history(member)] == [S.LEFT, S.PENDING]

    def test_locks_the_member_row_but_not_its_type(self):
        # Prova executada, a més de la inspecció de la SQL. Mentre la transacció del canvi és
        # oberta, una altra connexió no pot bloquejar el compte que actua ni el soci (aquest
        # també el bloqueja l'UPDATE: el bloqueig explícit el fixa la comprovació de la SQL), però
        # sí el tipus que el soci comparteix amb altres. Les claus foranes de Django es
        # comproven en confirmar (DEFERRABLE): aleshores PostgreSQL pren un moment un bloqueig
        # de clau compartida (FOR KEY SHARE) sobre el tipus, propi de la clau forana i no
        # d'aquest servei, que no impedeix editar-ne la quota.
        member = _committed_member(S.ACTIVE)
        secretary = make_admin(Role.Code.SECRETARY)

        def try_lock(model, pk):
            def run():
                try:
                    with transaction.atomic():
                        model.objects.select_for_update(nowait=True).get(pk=pk)
                    return "lliure"
                except DatabaseError:
                    return "bloquejada"

            return run

        with CaptureQueriesContext(connection) as queries, transaction.atomic():
            change(member, S.LEFT, secretary)
            (member_lock,) = run_together([try_lock(Member, member.pk)])
            (type_lock,) = run_together([try_lock(MembershipType, member.type_id)])
            (account_lock,) = run_together([try_lock(Account, secretary.pk)])

        assert (member_lock, type_lock, account_lock) == ("bloquejada", "lliure", "bloquejada")
        (lock_sql,) = [q["sql"] for q in queries if 'FOR UPDATE OF "members_member"' in q["sql"]]
        assert "membershiptype" not in lock_sql.split("FOR UPDATE", 1)[1]
        assert any(
            "FOR NO KEY UPDATE" in q["sql"] and "accounts_account" in q["sql"] for q in queries
        )

    def test_own_member_attempt_is_committed_without_any_change(self):
        # Recorregut correcte: el punt d'entrada comprova el conflicte abans d'obrir la
        # transacció. Fora d'una transacció exterior, l'intent queda confirmat.
        member = _committed_member(S.ACTIVE)
        own = make_admin(Role.Code.TREASURER, person=member.person)
        with pytest.raises(OwnMemberChange):
            services.mark_unpaid(member, by=own, effective_on=today(), reason=REASON)
        assert Member.objects.get(pk=member.pk).status == S.ACTIVE
        assert history(member) == []
        assert len(audit_entries(member, services.OWN_MEMBER_REJECTED)) == 1
