"""Desfer una conciliació (T-M04-12; RN-T19; decisió 045; CA-T10.4 a CA-T10.6; V-06). Només dades
inventades."""

import pytest
from django.db import DatabaseError, connection, transaction
from django.db.models import Sum
from django.http import Http404

from apps.core import audit, charges
from apps.core.imports import bank_statement as bs
from apps.core.models import AppendOnlyError, AuditEntry, Charge, PaymentCancellation
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import fees as member_fees
from apps.members.models import Member, MemberCard
from apps.members.tests.test_cards import add_fee, make_member
from apps.treasury import reconciliation
from apps.treasury.models import Movement, Reconciliation, ReconciliationUndo, StatementLineState
from apps.treasury.tests.test_reconciliation import (  # noqa: F401 (fixtures)
    charge,
    lines,
    ref,
    state,
    treasurer,
)

pytestmark = pytest.mark.django_db
State = StatementLineState.Status
REASON = "Casada amb el càrrec equivocat (prova)"


def bank_balance():
    total = {
        row["direction"]: row["total"]
        for row in Movement.objects.filter(account__kind="bank")
        .values("direction")
        .annotate(total=Sum("amount_cents"))
    }
    return total.get("in", 0) - total.get("out", 0)


def confirmed(by, *charges_, amount=None):
    concept = "TRANSF " + " ".join(ref(c) for c in charges_)
    (line,) = lines(by, (amount or sum(c.amount_cents for c in charges_), concept))
    return line, reconciliation.confirm(line, by=by)


class TestUndo:
    def test_ca_t10_5_the_wrong_charge_goes_back_to_pending(self, treasurer, charge):  # noqa: F811
        quota = charge()
        line, done = confirmed(treasurer, quota)
        income = Movement.objects.get(kind="income")
        undone = reconciliation.undo(done, reason=REASON, by=treasurer)
        assert (undone.reconciliation, undone.reason, undone.undone_by) == (done, REASON, treasurer)
        quota.refresh_from_db()
        assert quota.status == Charge.Status.PENDING
        assert PaymentCancellation.objects.get().payment == income.payment
        reversal = Movement.objects.get(kind="reversal")
        assert (reversal.reverses, reversal.direction, reversal.amount_cents) == (
            income,
            "out",
            9000,
        )
        assert (reversal.account, reversal.department, reversal.reason) == (
            income.account,
            income.department,
            REASON,
        )
        assert bank_balance() == 0
        # La línia torna a pendent i es torna a calcular: la referència la torna a proposar.
        assert state(line) == (State.PROPOSED, "", [quota])
        entry = AuditEntry.objects.get(action=reconciliation.UNDONE)
        assert (entry.actor_account, entry.reason) == (treasurer, REASON)
        # V-06: sense cap conciliació vigent, l'extracte ja es pot desfer.
        bs.undo(line.batch, by=treasurer, reason="Extracte equivocat (prova)")

    def test_p_110_a_fee_notifies_and_leaves_the_member_and_card(self, treasurer):  # noqa: F811
        member = make_member(status=Member.Status.PENDING)
        fee = add_fee(member)
        _line, done = confirmed(treasurer, fee.charge)
        member.refresh_from_db()
        assert member.status == Member.Status.ACTIVE
        cards = list(MemberCard.objects.filter(member=member, revoked_at=None))
        reconciliation.undo(done, reason=REASON, by=treasurer)
        member.refresh_from_db()
        assert member.status == Member.Status.ACTIVE
        assert list(MemberCard.objects.filter(member=member, revoked_at=None)) == cards
        notice = AuditEntry.objects.get(action=member_fees.NOTICE_SENT)
        assert notice.details["event"] == member_fees.NOTICE_TRANSFER_REVERTED

    def test_several_charges_are_all_reverted(self, treasurer, charge):  # noqa: F811
        first, second = charge(9000), charge(3500)
        _line, done = confirmed(treasurer, first, second)
        reconciliation.undo(done, reason=REASON, by=treasurer)
        assert set(Charge.objects.values_list("status", flat=True)) == {Charge.Status.PENDING}
        assert Movement.objects.filter(kind="reversal").count() == 2
        assert bank_balance() == 0

    def test_ca_t10_4_without_charges_only_the_line_goes_back(self, treasurer):  # noqa: F811
        (line,) = lines(treasurer, (4200, "TRASPAS"))
        reconciliation.refresh()
        done = Reconciliation.objects.create(statement_line=line, confirmed_by=treasurer)
        StatementLineState.objects.filter(statement_line=line).update(status=State.RECONCILED)
        reconciliation.undo(done, reason=REASON, by=treasurer)
        assert state(line) == (State.PENDING, "", [])
        assert not Movement.objects.exists()

    def test_it_is_undone_only_once_and_with_a_reason(self, treasurer, charge):  # noqa: F811
        _line, done = confirmed(treasurer, charge())
        with pytest.raises(reconciliation.ReconciliationRejected, match="motiu"):
            reconciliation.undo(done, reason="  ", by=treasurer)
        reconciliation.undo(done, reason=REASON, by=treasurer)
        with pytest.raises(reconciliation.ReconciliationRejected, match="ja està desfeta"):
            reconciliation.undo(done, reason=REASON, by=treasurer)
        assert ReconciliationUndo.objects.count() == 1

    def test_a_charge_changed_since_rolls_everything_back(self, treasurer, charge):  # noqa: F811
        first, second = charge(9000), charge(3500)
        _line, done = confirmed(treasurer, first, second)
        charges.revert_paid_transfer(second, "Corregit a part (prova)", by=treasurer)
        with pytest.raises(reconciliation.ReconciliationRejected):
            reconciliation.undo(done, reason=REASON, by=treasurer)
        first.refresh_from_db()
        assert first.status == Charge.Status.PAID
        assert not Movement.objects.filter(kind="reversal").exists()
        assert not ReconciliationUndo.objects.exists()

    def test_only_with_t4(self, treasurer, make_admin, charge):  # noqa: F811
        _line, done = confirmed(treasurer, charge())
        for who in (make_admin("administrator"), make_admin("secretary"), audit.system("proves")):
            with pytest.raises(Http404):
                reconciliation.undo(done, reason=REASON, by=who)
        assert not ReconciliationUndo.objects.exists()

    def test_undos_are_append_only_also_in_sql(self, treasurer, charge):  # noqa: F811
        _line, done = confirmed(treasurer, charge())
        undone = reconciliation.undo(done, reason=REASON, by=treasurer)
        with pytest.raises(AppendOnlyError):
            undone.save()
        for sql in (
            "UPDATE treasury_reconciliationundo SET reason = 'x'",
            "DELETE FROM treasury_reconciliationundo",
            "TRUNCATE treasury_reconciliationundo",
        ):
            with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
                cur.execute(sql)
