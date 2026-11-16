"""Conciliació, primera part: estats de les línies i propostes (T-M04-11; RN-T15, RN-T17b,
RN-T18; CA-T09.1 a CA-T09.3; LT2 a LT6). Només dades inventades."""

import datetime

import pytest

from apps.core import audit, charges, imports
from apps.core.imports import bank_statement as bs
from apps.core.models import AuditEntry, Charge, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import reconciliation, references
from apps.treasury.models import Movement, StatementLineState

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
