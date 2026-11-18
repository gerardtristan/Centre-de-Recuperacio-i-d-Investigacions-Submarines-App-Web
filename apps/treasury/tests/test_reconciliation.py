"""Conciliació, primera part: estats de les línies i propostes (T-M04-11; RN-T15, RN-T17b,
RN-T18; CA-T09.1 a CA-T09.3; LT2 a LT6). Només dades inventades."""

import datetime

import pytest
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.http import Http404
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit, charges, imports
from apps.core.imports import bank_statement as bs
from apps.core.models import AppendOnlyError, AuditEntry, Charge, Payment, Role, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member
from apps.treasury import reconciliation, references
from apps.treasury.models import Movement, Reconciliation, StatementLineState, TreasuryAccount
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-t-m04-11")
State = StatementLineState.Status
Reason = StatementLineState.ReviewReason


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


@pytest.fixture
def charge(make_person):
    def make(amount_cents=9000):
        return charges.create_charge(
            make_person(), kind="fee", amount_cents=amount_cents, concept="Quota", origin="proves",
            by=SYSTEM,
        )  # fmt: skip

    return make


def lines(by, *rows):
    """Lot confirmat amb aquestes línies (import, concepte), sense passar pel senyal."""
    batch = imports.open_confirmed(
        "bank_statement", file_sha256="0" * 64, by=by, counts={"new_count": len(rows)}
    )
    imports.add_lines(
        batch,
        [
            {
                "row": n,
                "result": "new",
                "value_date": datetime.date(2026, 11, n),
                "amount_cents": amount,
                "concept": concept,
                "balance_cents": None,
            }
            for n, (amount, concept) in enumerate(rows, start=2)
        ],
    )
    return list(imports.statement_lines(batch).order_by("row"))


def state(line):
    found = StatementLineState.objects.get(statement_line=line)
    return found.status, found.review_reason, list(found.proposed_charges.all())


def ref(charge):
    return references.transfer_reference(charge)


class TestStates:
    def test_ca_t09_1_every_line_of_a_confirmed_statement_has_a_state(self, treasurer, charge):
        quota = charge()
        data = (
            "Data;Concepte;Import;Saldo\n"
            f"02/11/2026;TRANSF {ref(quota)} QUOTA;90,00;1.090,00\n"
            "03/11/2026;REBUT LLUM;-12,30;1.077,70\n"
            "04/11/2026;INGRES SENSE RES;7,77;1.085,47\n"
        ).encode()
        batch = bs.confirm(bs.preview(data, by=treasurer)["token"], by=treasurer)
        found = {
            line.row: state(line)
            for line in imports.statement_lines(batch)  # una per línia
        }
        assert found == {
            2: (State.PROPOSED, "", [quota]),
            3: (State.PENDING, "", []),
            4: (State.PENDING, "", []),
        }
        assert set(State.values) == {"pending", "proposed", "reconciled", "excluded"}  # RN-T15

    def test_ca_t09_2_valid_reference_and_exact_amount_is_proposed_and_nothing_paid(
        self, treasurer, charge
    ):
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)} QUOTA"))
        reconciliation.refresh()
        assert state(line) == (State.PROPOSED, "", [quota])
        assert StatementLineState.objects.get(statement_line=line).to_review is False
        quota.refresh_from_db()
        # RN-T16, RN-M05b-05: proposar no paga res.
        assert quota.status == Charge.Status.PENDING
        assert not Payment.objects.exists() and not Movement.objects.exists()

    @pytest.mark.parametrize("amount", [9500, 8500])  # LT3, LT4 (RN-T17b)
    def test_ca_t09_3_valid_reference_and_other_amount_is_to_review(
        self, treasurer, charge, amount
    ):
        quota = charge()
        (line,) = lines(treasurer, (amount, f"TRANSF {ref(quota)}"))
        reconciliation.refresh()
        assert state(line) == (State.PENDING, Reason.AMOUNT_MISMATCH, [])
        assert StatementLineState.objects.get(statement_line=line).to_review is True

    def test_ca_t09_3_no_reference_and_one_charge_of_that_amount_is_to_review(
        self, treasurer, charge
    ):
        charge(3500)
        charge(9000)
        charge(9000)
        single, several, none = lines(
            treasurer, (3500, "TRANSF QUOTA"), (9000, "TRANSF QUOTA"), (4200, "TRANSF")
        )
        reconciliation.refresh()
        assert state(single) == (State.PENDING, Reason.AMOUNT_ONLY, [])
        assert state(several) == (State.PENDING, "", [])  # P-101
        assert state(none) == (State.PENDING, "", [])

    def test_lt5_one_line_for_two_charges_is_proposed_only_with_the_exact_sum(
        self, treasurer, charge
    ):
        a, b = charge(3500), charge(9000)
        exact, short = lines(
            treasurer,
            (12500, f"QUOTES {ref(a)} {ref(b)}"),
            (12000, f"QUOTES {ref(charge(3500))} {ref(charge(9000))}"),
        )
        reconciliation.refresh()
        assert state(exact)[:2] == (State.PROPOSED, "")
        assert set(state(exact)[2]) == {a, b}
        assert state(short) == (State.PENDING, Reason.AMOUNT_MISMATCH, [])

    def test_lt6_charge_that_is_no_longer_pending_is_to_review(self, treasurer, charge):
        quota = charge()
        charges.cancel(quota, "Prova", by=SYSTEM)
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)}"))
        reconciliation.refresh()
        assert state(line) == (State.PENDING, Reason.CHARGE_NOT_PENDING, [])

    def test_valid_reference_of_no_charge_is_to_review_and_a_bad_one_is_no_reference(
        self, treasurer, settings
    ):
        settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
        code = "AB2CD"
        good = f"CRIS-{code}-{references.check_character(code)}"
        bad = good[:-1] + ("X" if good[-1] != "X" else "Y")
        unknown, wrong = lines(treasurer, (9000, good), (9000, bad))
        reconciliation.refresh()
        assert state(unknown) == (State.PENDING, Reason.UNKNOWN_REFERENCE, [])
        assert state(wrong) == (State.PENDING, "", [])

    def test_the_same_charge_is_only_proposed_on_the_first_line(self, treasurer, charge):
        quota = charge()
        first, second = lines(treasurer, (9000, ref(quota)), (9000, ref(quota)))
        reconciliation.refresh()
        assert state(first) == (State.PROPOSED, "", [quota])
        assert state(second) == (State.PENDING, Reason.REPEATED_REFERENCE, [])

    def test_review_53_a_charge_already_proposed_does_not_count_for_amount_only(
        self, treasurer, charge
    ):
        quota = charge()
        no_reference, with_reference = lines(treasurer, (9000, "TRANSF"), (9000, ref(quota)))
        reconciliation.refresh()
        assert state(with_reference) == (State.PROPOSED, "", [quota])
        assert state(no_reference) == (State.PENDING, "", [])

    def test_outgoing_line_with_a_reference_stays_pending(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (-9000, f"DEVOLUCIO {ref(quota)}"))
        reconciliation.refresh()
        assert state(line) == (State.PENDING, "", [])


class TestRefresh:
    def test_changes_are_recomputed_logged_once_and_without_the_concept(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)} INVENTAT"))
        reconciliation.refresh()
        charges.cancel(quota, "Prova", by=SYSTEM)
        reconciliation.refresh()
        reconciliation.refresh()  # res no ha canviat: no escriu res
        assert state(line) == (State.PENDING, Reason.CHARGE_NOT_PENDING, [])
        entries = AuditEntry.objects.filter(action=reconciliation.STATE_CHANGED).order_by("pk")
        proposed = {
            "status": "proposed", "to_review": False, "review_reason": "", "charges": [quota.pk]
        }  # fmt: skip
        assert [(e.old_value, e.new_value) for e in entries] == [
            (None, proposed),
            (
                proposed,
                {
                    "status": "pending",
                    "to_review": True,
                    "review_reason": "charge_not_pending",
                    "charges": [],
                },
            ),
        ]
        assert "INVENTAT" not in str([(e.details, e.old_value, e.new_value) for e in entries])

    def test_plain_pending_lines_are_created_without_log(self, treasurer):
        lines(treasurer, (-1230, "REBUT LLUM"))
        reconciliation.refresh()
        assert StatementLineState.objects.count() == 1
        assert not AuditEntry.objects.filter(action=reconciliation.STATE_CHANGED).exists()

    @pytest.mark.parametrize("closed", [State.RECONCILED, State.EXCLUDED])
    def test_closed_lines_are_not_touched(self, treasurer, charge, closed):
        quota = charge()
        (line,) = lines(treasurer, (9000, ref(quota)))
        reason = "Prova" if closed == State.EXCLUDED else ""
        StatementLineState.objects.create(
            statement_line=line, status=closed, exclusion_reason=reason
        )
        reconciliation.refresh()
        assert state(line) == (closed, "", [])

    def test_undo_still_works_and_its_lines_are_left_out(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (9000, ref(quota)))
        reconciliation.refresh()
        assert bs._reconciled(line.batch) is False  # l'estat no és cap conciliació
        bs.undo(line.batch, by=treasurer, reason="Extracte equivocat (prova)")
        # Revisió de la #53: en desfer, la línia deixa de ser proposada (senyal `changed`).
        assert state(line) == (State.PENDING, "", [])
        (again,) = lines(treasurer, (9000, ref(quota)))
        reconciliation.refresh()
        assert state(again) == (State.PROPOSED, "", [quota])


class TestReferencesIn:
    @pytest.fixture(autouse=True)
    def prefix(self, settings):
        settings.TRANSFER_REFERENCE_PREFIX = "CRIS"

    def test_variants_the_bank_or_the_payer_may_write(self):
        code = "7K3Q9"
        reference = f"CRIS-{code}-{references.check_character(code)}"
        c = reference[-1]
        for text in [
            f"TRANSF {reference}",
            f"transf cris-{code.lower()}-{c.lower()}",
            f"TRANSF CRIS {code} {c} QUOTA",
            f"TRANSF/CRIS{code}{c}/QUOTA",
            f"TRANSF CRIS - {code} - {c}",  # revisió de la #53
            f"TRANSF CRIS.{code}.{c}",
            f"TRANSF CRIS/{code}/{c}",
            f"TRANSF CRIS_{code}_{c}",
            f"{reference} {reference}",
        ]:
            assert references.references_in(text) == [reference], text

    def test_p_100_another_prefix_or_glued_text_is_not_a_reference(self):
        code = "7K3Q9"
        c = references.check_character(code)
        for text in [f"OLD-{code}-{c}", f"XCRIS-{code}-{c}", f"CRIS-{code}-{c}9", ""]:
            assert references.references_in(text) == [], text


class TestConfirm:
    """T-M04-12: confirmar la proposta (CA-T10.1 a CA-T10.3; RN-T16, RN-T17, RN-T18)."""

    def test_ca_t10_1_confirming_a_transfer_pays_the_charge_and_records_the_income(
        self, treasurer, charge
    ):
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)} QUOTA"))
        reconciliation.refresh()
        done = reconciliation.confirm(line, by=treasurer)
        quota.refresh_from_db()
        assert quota.status == Charge.Status.PAID
        (payment,) = Payment.objects.all()
        assert (payment.charge, payment.method, payment.amount_cents) == (quota, "transfer", 9000)
        assert payment.transfer_reference == ref(quota)
        (income,) = Movement.objects.all()
        assert (income.payment, income.kind, income.amount_cents) == (payment, "income", 9000)
        assert income.account == TreasuryAccount.objects.get(kind="bank")
        assert income.recorded_by == treasurer
        assert (done.statement_line, done.confirmed_by) == (line, treasurer)
        assert list(done.matched_charges.all()) == [quota]
        assert state(line) == (State.RECONCILED, "", [quota])
        # RN-T13: qui ho confirma, al registre.
        entry = AuditEntry.objects.get(action=reconciliation.CONFIRMED)
        assert entry.actor_account == treasurer
        assert entry.details == {"line": line.pk, "charges": [quota.pk], "amount_cents": 9000}
        changed = AuditEntry.objects.filter(action=reconciliation.STATE_CHANGED).last()
        assert changed.actor_account == treasurer

    def test_p_111_the_income_takes_the_value_date_of_the_line(self, treasurer, charge):
        # Decisió 095, P-111 (A): el saldo del banc quadra amb l'extracte el dia de l'abonament.
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)} QUOTA"))
        assert line.value_date == datetime.date(2026, 11, 2)
        reconciliation.refresh()
        reconciliation.confirm(line, by=treasurer)
        (payment,) = Payment.objects.all()
        assert timezone.localdate(payment.paid_at) == line.value_date
        assert Movement.objects.get().value_date == line.value_date

    def test_ca_t10_1_a_fee_activates_the_member(self, treasurer):
        member = make_member(status=Member.Status.PENDING)
        fee = add_fee(member)
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(fee.charge)}"))
        reconciliation.confirm(line, by=treasurer)
        member.refresh_from_db()
        assert member.status == Member.Status.ACTIVE  # `members.on_fee_paid`

    def test_ca_t10_2_one_line_for_several_charges_with_the_exact_sum(self, treasurer, charge):
        first, second = charge(9000), charge(3500)
        (line,) = lines(treasurer, (12500, f"QUOTES {ref(first)} {ref(second)}"))
        done = reconciliation.confirm(line, by=treasurer)
        assert set(done.matched_charges.all()) == {first, second}
        assert set(Charge.objects.values_list("status", flat=True)) == {Charge.Status.PAID}
        assert Movement.objects.filter(kind="income").count() == 2

    def test_ca_t10_2_several_charges_without_the_exact_sum_are_not_confirmed(
        self, treasurer, charge
    ):
        first, second = charge(9000), charge(3500)
        (line,) = lines(treasurer, (12000, f"QUOTES {ref(first)} {ref(second)}"))
        with pytest.raises(reconciliation.ReconciliationRejected):
            reconciliation.confirm(line, by=treasurer)
        assert not Payment.objects.exists() and not Reconciliation.objects.exists()

    def test_a_charge_cancelled_after_the_proposal_is_not_confirmed(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)}"))
        reconciliation.refresh()
        charges.cancel(quota, "Anul·lada (prova)", by=SYSTEM)
        with pytest.raises(reconciliation.ReconciliationRejected):
            reconciliation.confirm(line, by=treasurer)
        assert not Payment.objects.exists() and not Movement.objects.exists()

    def test_ca_t10_3_a_reconciled_line_is_not_used_again(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)}"))
        reconciliation.confirm(line, by=treasurer)
        with pytest.raises(reconciliation.ReconciliationRejected, match="ja està conciliada"):
            reconciliation.confirm(line, by=treasurer)
        reconciliation.refresh()
        assert state(line) == (State.RECONCILED, "", [quota])
        assert Reconciliation.objects.count() == Payment.objects.count() == 1
        # V-06: un extracte amb una línia conciliada no es desfà.
        with pytest.raises(bs.Rejected) as rejected:
            bs.undo(line.batch, by=treasurer, reason="Extracte equivocat (prova)")
        assert rejected.value.code == "reconciled"

    def test_a_line_without_proposal_is_not_confirmed(self, treasurer):
        (line,) = lines(treasurer, (9000, "TRANSF SENSE REFERENCIA"))
        with pytest.raises(reconciliation.ReconciliationRejected, match="cap proposta"):
            reconciliation.confirm(line, by=treasurer)

    def test_rn_t16_only_the_treasurer_has_t4(self, treasurer, make_admin, make_person, charge):  # noqa: F811
        """M04-4, T4: només el tresorer (l'administrador, [A validar], comença sense: P-112).
        La resta, «no trobat»; el sistema tampoc no concilia mai sol."""
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)}"))
        member = Account.objects.create_personal(make_person(), "soci@example.org", PASSWORD)
        for who in (make_admin("administrator"), make_admin("secretary"), member, SYSTEM):
            with pytest.raises(Http404):
                reconciliation.confirm(line, by=who)
        assert not Payment.objects.exists()
        assert reconciliation.confirm(line, by=treasurer).confirmed_by == treasurer

    def test_ck_c8_reconciliations_are_append_only_also_in_sql(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)}"))
        done = reconciliation.confirm(line, by=treasurer)
        with pytest.raises(AppendOnlyError):
            done.save()
        for sql in (
            "UPDATE treasury_reconciliation SET confirmed_at = now()",
            "DELETE FROM treasury_reconciliation_matched_charges",
            "TRUNCATE treasury_reconciliation_matched_charges",
        ):
            with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
                cur.execute(sql)


class TestExclude:
    """T-M04-14: excloure una línia (RN-T15, CA-T12.1, LT11) i la llista «a revisar» (CA-T13.1)."""

    def test_ca_t12_1_excluding_needs_a_reason_and_creates_no_movement(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (9500, f"TRANSF {ref(quota)} INVENTAT"))
        for blank in ("", "   "):
            with pytest.raises(reconciliation.ReconciliationRejected, match="motiu"):
                reconciliation.exclude(line, reason=blank, by=treasurer)
        excluded = reconciliation.exclude(line, reason=" Ingrés d'una altra entitat ", by=treasurer)
        excluded.refresh_from_db()
        assert (excluded.status, excluded.exclusion_reason) == (
            State.EXCLUDED,
            "Ingrés d'una altra entitat",
        )
        assert excluded.to_review is False and not excluded.proposed_charges.exists()
        quota.refresh_from_db()
        assert quota.status == Charge.Status.PENDING
        assert not Movement.objects.exists() and not Payment.objects.exists()
        # RN-T13: al registre, amb el compte, el motiu i l'estat anterior; sense el concepte.
        entry = AuditEntry.objects.get(action=reconciliation.EXCLUDED)
        assert entry.reason == "Ingrés d'una altra entitat"
        assert entry.old_value["review_reason"] == "amount_mismatch"
        assert entry.new_value["status"] == "excluded"
        assert entry.actor_account_id == treasurer.pk
        assert "INVENTAT" not in str((entry.details, entry.old_value, entry.new_value))
        # Ja no torna enrere ni es pot excloure dues vegades.
        reconciliation.refresh()
        assert state(line)[0] == State.EXCLUDED
        with pytest.raises(reconciliation.ReconciliationRejected, match="pendent"):
            reconciliation.exclude(line, reason="Una altra vegada", by=treasurer)

    def test_lt11_an_outgoing_line_can_be_excluded(self, treasurer):
        (line,) = lines(treasurer, (-1230, "REBUT LLUM"))
        reconciliation.exclude(line, reason="Despesa amb factura, fins al 09", by=treasurer)
        assert state(line)[0] == State.EXCLUDED

    def test_rn_t15_only_an_open_line_of_a_current_statement(self, treasurer, charge):
        quota = charge()
        (done,) = lines(treasurer, (9000, ref(quota)))
        (undone,) = lines(treasurer, (500, "INGRES"))  # un altre extracte, que es desfà
        reconciliation.refresh()
        reconciliation.confirm(done, by=treasurer)
        with pytest.raises(reconciliation.ReconciliationRejected, match="pendent"):
            reconciliation.exclude(done, reason="Prova", by=treasurer)  # conciliada
        bs.undo(undone.batch, by=treasurer, reason="Extracte equivocat (prova)")
        with pytest.raises(reconciliation.ReconciliationRejected):
            reconciliation.exclude(undone, reason="Prova", by=treasurer)
        assert not StatementLineState.objects.filter(status=State.EXCLUDED).exists()

    def test_t8_only_the_treasurer(self, treasurer, make_admin, make_person):  # noqa: F811
        """M04-4, T8: només el tresorer (P-190); la resta, «no trobat»; el sistema, tampoc."""
        (line,) = lines(treasurer, (-1230, "REBUT LLUM"))
        member = Account.objects.create_personal(make_person(), "soci@example.org", PASSWORD)
        for who in (make_admin("administrator"), make_admin("secretary"), member, SYSTEM):
            with pytest.raises(Http404):
                reconciliation.exclude(line, reason="Prova", by=who)
        assert not StatementLineState.objects.filter(status=State.EXCLUDED).exists()

    def test_t8_is_its_own_cell_not_t4(self, treasurer, make_admin):  # noqa: F811
        """P-190 (095): T8 té codi propi. Sense la cel·la, el tresorer no exclou encara que tingui
        T4; un rol amb T8 i sense T4 sí que exclou."""
        first, second = lines(treasurer, (-1230, "REBUT LLUM"), (-500, "REBUT AIGUA"))
        RolePermission.objects.filter(permission_code=reconciliation.EXCLUDE).delete()
        with pytest.raises(Http404):
            reconciliation.exclude(first, reason="Prova", by=treasurer)
        RolePermission.objects.create(
            role=Role.objects.get(code="secretary"),
            permission_code=reconciliation.EXCLUDE,
            scope="all",
        )
        reconciliation.exclude(second, reason="Prova", by=make_admin("secretary"))
        assert state(second)[0] == State.EXCLUDED and state(first)[0] != State.EXCLUDED

    # --- T-M04-14d (097, P-192 opció C; RN-T15): excloure una proposada i desfer l'exclusió.

    def test_a_proposed_line_is_excluded_and_its_proposal_dropped(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)} INVENTAT"))
        reconciliation.refresh()
        assert state(line)[0] == State.PROPOSED
        reconciliation.exclude(line, reason="Ingrés repetit del banc", by=treasurer)
        assert state(line) == (State.EXCLUDED, "", [])
        quota.refresh_from_db()
        assert quota.status == Charge.Status.PENDING  # res confirmat, res pagat
        assert not Movement.objects.exists() and not Payment.objects.exists()
        entry = AuditEntry.objects.get(action=reconciliation.EXCLUDED)
        assert entry.old_value["status"] == "proposed" and entry.old_value["charges"] == [quota.pk]
        assert entry.new_value["charges"] == []
        reconciliation.refresh()  # una exclusió no torna enrere sola
        assert state(line)[0] == State.EXCLUDED

    def test_undoing_an_exclusion_needs_a_reason_and_is_logged(self, treasurer):
        (line,) = lines(treasurer, (-1230, "REBUT LLUM"))
        reconciliation.exclude(line, reason="Despesa amb factura", by=treasurer)
        for blank in ("", "   "):
            with pytest.raises(reconciliation.ReconciliationRejected, match="motiu"):
                reconciliation.undo_exclusion(line, reason=blank, by=treasurer)
        undone = reconciliation.undo_exclusion(line, reason=" Exclosa per error ", by=treasurer)
        undone.refresh_from_db()
        assert (undone.status, undone.exclusion_reason, undone.to_review) == (
            State.PENDING,
            "",
            False,
        )
        entry = AuditEntry.objects.get(action=reconciliation.EXCLUSION_UNDONE)
        assert entry.reason == "Exclosa per error" and entry.actor_account_id == treasurer.pk
        assert entry.old_value["status"] == "excluded" and entry.new_value["status"] == "pending"
        assert entry.details["exclusion_reason"] == "Despesa amb factura"
        assert "LLUM" not in str((entry.details, entry.old_value, entry.new_value))
        # Es pot tornar a excloure.
        reconciliation.exclude(line, reason="Ara sí", by=treasurer)
        assert state(line)[0] == State.EXCLUDED

    def test_after_undoing_the_line_is_proposed_again_if_it_applies(self, treasurer, charge):
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)} INVENTAT"))
        reconciliation.refresh()
        reconciliation.exclude(line, reason="Prova", by=treasurer)
        reconciliation.undo_exclusion(line, reason="Era bona", by=treasurer)
        assert state(line) == (State.PROPOSED, "", [quota])

    def test_only_an_excluded_line_of_a_current_statement_is_undone(self, treasurer):
        pending, other = lines(treasurer, (-1230, "REBUT LLUM"), (-500, "REBUT AIGUA"))
        with pytest.raises(reconciliation.ReconciliationRejected, match="exclosa"):
            reconciliation.undo_exclusion(pending, reason="Prova", by=treasurer)
        reconciliation.exclude(other, reason="Prova", by=treasurer)
        bs.undo(other.batch, by=treasurer, reason="Extracte equivocat (prova)")
        with pytest.raises(reconciliation.ReconciliationRejected, match="exclosa"):
            reconciliation.undo_exclusion(other, reason="Prova", by=treasurer)
        assert not AuditEntry.objects.filter(action=reconciliation.EXCLUSION_UNDONE).exists()

    def test_undoing_needs_t8_with_edit(self, treasurer, make_admin, make_person):  # noqa: F811
        (line,) = lines(treasurer, (-1230, "REBUT LLUM"))
        reconciliation.exclude(line, reason="Prova", by=treasurer)
        member = Account.objects.create_personal(make_person(), "soci@example.org", PASSWORD)
        for who in (make_admin("administrator"), make_admin("secretary"), member, SYSTEM):
            with pytest.raises(Http404):
                reconciliation.undo_exclusion(line, reason="Prova", by=who)
        assert state(line)[0] == State.EXCLUDED
        RolePermission.objects.filter(  # T4 sol no hi val
            role__code="treasurer", permission_code=reconciliation.EXCLUDE
        ).delete()
        with pytest.raises(Http404):
            reconciliation.undo_exclusion(line, reason="Prova", by=treasurer)

    def test_excluded_needs_a_reason_also_in_the_database(self, treasurer):
        (line,) = lines(treasurer, (-1230, "REBUT LLUM"))
        with pytest.raises(IntegrityError), transaction.atomic():
            StatementLineState.objects.create(statement_line=line, status=State.EXCLUDED)

    def test_ca_t13_1_the_list_has_the_open_lines_to_review_with_their_reason(
        self, treasurer, charge
    ):
        quota, other = charge(), charge(3500)
        # Una a revisar, una de proposada i una de pendent sense marca: només hi surt la primera.
        mismatch, _proposed, _plain = lines(
            treasurer, (9500, ref(quota)), (3500, ref(other)), (-100, "REBUT")
        )
        reconciliation.refresh()
        assert list(reconciliation.to_review()) == [
            StatementLineState.objects.get(statement_line=mismatch)
        ]
        reconciliation.exclude(mismatch, reason="Prova", by=treasurer)
        assert not reconciliation.to_review().exists()
