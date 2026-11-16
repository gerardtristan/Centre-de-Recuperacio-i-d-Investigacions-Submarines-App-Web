"""Conciliació, primera part: estats de les línies i propostes (T-M04-11; RN-T15, RN-T17b,
RN-T18; CA-T09.1 a CA-T09.3; LT2 a LT6). Només dades inventades."""

import datetime
from types import MappingProxyType

import pytest
from django.db import DatabaseError, connection, transaction
from django.http import Http404

from apps.core import audit, charges, imports, permission_catalog, permissions
from apps.core.imports import bank_statement as bs
from apps.core.models import AppendOnlyError, AuditEntry, Charge, Payment, Role, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member
from apps.treasury import reconciliation, references
from apps.treasury.models import Movement, Reconciliation, StatementLineState, TreasuryAccount

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
        StatementLineState.objects.create(statement_line=line, status=closed)
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


@pytest.fixture
def reconciler(treasurer, monkeypatch):
    """El tresorer amb T4. El permís encara no és al catàleg del nucli (T-M04-12): la prova
    l'hi posa com el posarà el nucli, amb la cel·la inicial del tresorer (M04-4)."""
    code = reconciliation.RECONCILE
    t4 = permission_catalog.Permission(code, "T4", "Conciliar i desfer una conciliació")
    catalog = MappingProxyType({**permission_catalog.CATALOG, code: t4})
    for module in (permissions, reconciliation):
        monkeypatch.setattr(module, "CATALOG", catalog)
    RolePermission.objects.create(
        role=Role.objects.get(code="treasurer"), permission_code=code, scope="all"
    )
    return treasurer


class TestConfirm:
    """T-M04-12: confirmar la proposta (CA-T10.1 a CA-T10.3; RN-T16, RN-T17, RN-T18)."""

    def test_ca_t10_1_confirming_a_transfer_pays_the_charge_and_records_the_income(
        self, reconciler, charge
    ):
        quota = charge()
        (line,) = lines(reconciler, (9000, f"TRANSF {ref(quota)} QUOTA"))
        reconciliation.refresh()
        done = reconciliation.confirm(line, by=reconciler)
        quota.refresh_from_db()
        assert quota.status == Charge.Status.PAID
        (payment,) = Payment.objects.all()
        assert (payment.charge, payment.method, payment.amount_cents) == (quota, "transfer", 9000)
        assert payment.transfer_reference == ref(quota)
        (income,) = Movement.objects.all()
        assert (income.payment, income.kind, income.amount_cents) == (payment, "income", 9000)
        assert income.account == TreasuryAccount.objects.get(kind="bank")
        assert income.recorded_by == reconciler
        assert (done.statement_line, done.confirmed_by) == (line, reconciler)
        assert list(done.matched_charges.all()) == [quota]
        assert state(line) == (State.RECONCILED, "", [quota])
        # RN-T13: qui ho confirma, al registre.
        entry = AuditEntry.objects.get(action=reconciliation.CONFIRMED)
        assert entry.actor_account == reconciler
        assert entry.details == {"line": line.pk, "charges": [quota.pk], "amount_cents": 9000}
        changed = AuditEntry.objects.filter(action=reconciliation.STATE_CHANGED).last()
        assert changed.actor_account == reconciler

    def test_ca_t10_1_a_fee_activates_the_member(self, reconciler):
        member = make_member(status=Member.Status.PENDING)
        fee = add_fee(member)
        (line,) = lines(reconciler, (9000, f"TRANSF {ref(fee.charge)}"))
        reconciliation.confirm(line, by=reconciler)
        member.refresh_from_db()
        assert member.status == Member.Status.ACTIVE  # `members.on_fee_paid`

    def test_ca_t10_2_one_line_for_several_charges_with_the_exact_sum(self, reconciler, charge):
        first, second = charge(9000), charge(3500)
        (line,) = lines(reconciler, (12500, f"QUOTES {ref(first)} {ref(second)}"))
        done = reconciliation.confirm(line, by=reconciler)
        assert set(done.matched_charges.all()) == {first, second}
        assert set(Charge.objects.values_list("status", flat=True)) == {Charge.Status.PAID}
        assert Movement.objects.filter(kind="income").count() == 2

    def test_ca_t10_2_several_charges_without_the_exact_sum_are_not_confirmed(
        self, reconciler, charge
    ):
        first, second = charge(9000), charge(3500)
        (line,) = lines(reconciler, (12000, f"QUOTES {ref(first)} {ref(second)}"))
        with pytest.raises(reconciliation.ReconciliationRejected):
            reconciliation.confirm(line, by=reconciler)
        assert not Payment.objects.exists() and not Reconciliation.objects.exists()

    def test_a_charge_cancelled_after_the_proposal_is_not_confirmed(self, reconciler, charge):
        quota = charge()
        (line,) = lines(reconciler, (9000, f"TRANSF {ref(quota)}"))
        reconciliation.refresh()
        charges.cancel(quota, "Anul·lada (prova)", by=SYSTEM)
        with pytest.raises(reconciliation.ReconciliationRejected):
            reconciliation.confirm(line, by=reconciler)
        assert not Payment.objects.exists() and not Movement.objects.exists()

    def test_ca_t10_3_a_reconciled_line_is_not_used_again(self, reconciler, charge):
        quota = charge()
        (line,) = lines(reconciler, (9000, f"TRANSF {ref(quota)}"))
        reconciliation.confirm(line, by=reconciler)
        with pytest.raises(reconciliation.ReconciliationRejected, match="ja està conciliada"):
            reconciliation.confirm(line, by=reconciler)
        reconciliation.refresh()
        assert state(line) == (State.RECONCILED, "", [quota])
        assert Reconciliation.objects.count() == Payment.objects.count() == 1
        # V-06: un extracte amb una línia conciliada no es desfà.
        with pytest.raises(bs.Rejected) as rejected:
            bs.undo(line.batch, by=reconciler, reason="Extracte equivocat (prova)")
        assert rejected.value.code == "reconciled"

    def test_a_line_without_proposal_is_not_confirmed(self, reconciler):
        (line,) = lines(reconciler, (9000, "TRANSF SENSE REFERENCIA"))
        with pytest.raises(reconciliation.ReconciliationRejected, match="cap proposta"):
            reconciliation.confirm(line, by=reconciler)

    def test_rn_t16_without_t4_nobody_confirms(self, reconciler, make_admin, charge):  # noqa: F811
        quota = charge()
        (line,) = lines(reconciler, (9000, f"TRANSF {ref(quota)}"))
        for who in (make_admin("secretary"), SYSTEM):
            with pytest.raises(Http404):
                reconciliation.confirm(line, by=who)
        assert not Payment.objects.exists()

    def test_until_the_core_catalog_has_t4_it_fails_closed(self, treasurer, charge):
        assert reconciliation.RECONCILE not in permission_catalog.CATALOG
        quota = charge()
        (line,) = lines(treasurer, (9000, f"TRANSF {ref(quota)}"))
        with pytest.raises(Http404):
            reconciliation.confirm(line, by=treasurer)

    def test_ck_c8_reconciliations_are_append_only_also_in_sql(self, reconciler, charge):
        quota = charge()
        (line,) = lines(reconciler, (9000, f"TRANSF {ref(quota)}"))
        done = reconciliation.confirm(line, by=reconciler)
        with pytest.raises(AppendOnlyError):
            done.save()
        for sql in (
            "UPDATE treasury_reconciliation SET confirmed_at = now()",
            "DELETE FROM treasury_reconciliation_matched_charges",
            "TRUNCATE treasury_reconciliation_matched_charges",
        ):
            with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
                cur.execute(sql)
