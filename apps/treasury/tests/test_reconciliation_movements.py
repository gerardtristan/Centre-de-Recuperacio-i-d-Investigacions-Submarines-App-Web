"""Casar a mà una línia de l'extracte amb moviments que ja hi són o amb una liquidació (T-M04-12f;
CA-T07.2; RN-T16, RN-T17; P-394, P-395). Només dades inventades."""

from datetime import date

import pytest
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.core.models import AuditEntry, Department, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import reconciliation, services, settlements
from apps.treasury.models import Movement, ProviderSettlement, Reconciliation, StatementLineState
from apps.treasury.settlements import SettlementLine
from apps.treasury.tests import test_settlements as base
from apps.treasury.tests.test_movements import cash  # noqa: F401 (fixture)
from apps.treasury.tests.test_reconciliation import charge, lines, ref  # noqa: F401 (fixture)
from apps.treasury.tests.test_settlement_reconciliation import NET, bank_line, received
from apps.treasury.tests.test_transfers_and_cash_counts import bank, deposit  # noqa: F401
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
State = StatementLineState.Status
Rejected = reconciliation.ReconciliationRejected
REASON = "Casada amb el moviment equivocat (prova)"
person, transit, two, collected = base.person, base.transit, base.two, base.collected


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


def status(line):
    return StatementLineState.objects.get(statement_line=line).status


def opened(*rows, by):
    found = lines(by, *rows)
    reconciliation.refresh()
    return found


def other_income(bank, by, amount=3000, value_date=date(2026, 11, 3)):  # noqa: F811
    general = Department.objects.get(name="General")
    return services.record_other_income(
        bank, amount, value_date=value_date, department=general, concept="Donatiu", by=by
    )


class TestMatchMovements:
    def test_ca_t07_2_the_cash_deposit_line_is_matched_with_the_bank_leg(
        self,
        treasurer,
        cash,  # noqa: F811
        bank,  # noqa: F811
    ):
        out, entry = deposit(cash, bank, treasurer)
        (line,) = opened((12_000, "INGRES EFECTIU"), by=treasurer)
        assert entry in reconciliation.matchable_movements(line)
        assert out not in reconciliation.matchable_movements(line)  # la de la caixa, no
        before = Movement.objects.count()
        done = reconciliation.match_movements(line, [entry.pk], by=treasurer)
        assert list(done.matched_movements.all()) == [entry]
        assert not done.matched_charges.exists() and done.confirmed_by == treasurer
        assert Movement.objects.count() == before  # cap diner no es mou
        assert status(line) == State.RECONCILED
        audit = AuditEntry.objects.get(action=reconciliation.CONFIRMED)
        assert audit.details == {
            "line": line.pk,
            "movements": [entry.pk],
            "amount_cents": 12_000,
            "manual": True,
        }

    def test_an_outgoing_line_is_matched_with_two_bank_movements_summing_it(
        self,
        treasurer,
        cash,  # noqa: F811
        bank,  # noqa: F811
    ):
        first = deposit(bank, cash, treasurer, amount=2000)[0]
        second = deposit(bank, cash, treasurer, amount=500)[0]
        (line,) = opened((-2500, "RETIRADA"), by=treasurer)
        with pytest.raises(Rejected):  # 20 € de 25 €: la suma ha de ser exacta (RN-T17)
            reconciliation.match_movements(line, [first.pk], by=treasurer)
        assert not Reconciliation.objects.exists()
        reconciliation.match_movements(line, [first.pk, second.pk], by=treasurer)
        assert status(line) == State.RECONCILED

    def test_what_cannot_be_matched(self, treasurer, cash, bank, charge):  # noqa: F811
        entry = deposit(cash, bank, treasurer, amount=9000)[1]
        quota = charge(9000)
        paid, other, outgoing = opened(
            (9000, f"TRANSF {ref(quota)}"), (9000, "ALTRA"), (-9000, "SORTIDA"), by=treasurer
        )
        reconciliation.confirm(paid, by=treasurer)
        income = Movement.objects.get(kind=Movement.Kind.INCOME)
        # L'ingrés d'un càrrec ja conciliat i un moviment d'un altre sentit no surten.
        assert income not in reconciliation.matchable_movements(other)
        assert entry not in reconciliation.matchable_movements(outgoing)
        for line, ids in ((other, [income.pk]), (outgoing, [entry.pk]), (other, [])):
            with pytest.raises(Rejected):
                reconciliation.match_movements(line, ids, by=treasurer)
        reconciliation.match_movements(other, [entry.pk], by=treasurer)
        (again,) = opened((9000, "UNA ALTRA"), by=treasurer)
        with pytest.raises(Rejected):  # un moviment només es casa una vegada
            reconciliation.match_movements(again, [entry.pk], by=treasurer)
        with pytest.raises(Rejected):  # una línia conciliada no torna a casar-se
            reconciliation.match_movements(other, [entry.pk], by=treasurer)

    def test_review_1_the_refund_of_a_reconciled_charge_is_matchable(self, treasurer, charge):  # noqa: F811
        quota = charge(9000)
        paid, outgoing, other = opened(
            (9000, f"TRANSF {ref(quota)}"), (-4000, "DEVOLUCIO"), (9000, "ALTRA"), by=treasurer
        )
        reconciliation.confirm(paid, by=treasurer)
        payment = quota.payments.get()
        refund = services.record_refund(payment, 4000, reason=REASON, by=treasurer)
        assert refund.account.kind == "bank" and refund in reconciliation.matchable_movements(
            outgoing
        )
        income = Movement.objects.get(kind=Movement.Kind.INCOME)
        assert income not in reconciliation.matchable_movements(other)  # l'ingrés, no
        reconciliation.match_movements(outgoing, [refund.pk], by=treasurer)
        assert status(outgoing) == State.RECONCILED

    def test_review_6_messages_for_a_line_that_cannot_be_matched(self, treasurer, cash, bank):  # noqa: F811
        entry = deposit(cash, bank, treasurer)[1]
        done, zero = opened((12_000, "INGRES"), (0, "ZERO"), by=treasurer)
        reconciliation.match_movements(done, [entry.pk], by=treasurer)
        assert reconciliation.match_problem(done, incoming=False) == (
            "Aquesta línia no està pendent: no es pot casar."
        )
        assert reconciliation.match_problem(zero, incoming=False) == (
            "Aquesta línia no té cap import: no es pot casar."
        )

    def test_a_proposed_line_and_an_account_without_t4_are_rejected(
        self,
        treasurer,
        make_admin,  # noqa: F811
        cash,  # noqa: F811
        bank,  # noqa: F811
        charge,  # noqa: F811
    ):
        entry = deposit(cash, bank, treasurer, amount=9000)[1]
        quota = charge(9000)
        proposed, line = opened((9000, ref(quota)), (9000, "INGRES"), by=treasurer)
        with pytest.raises(Rejected):
            reconciliation.match_movements(proposed, [entry.pk], by=treasurer)
        for role in (Role.Code.PRESIDENT, Role.Code.SECRETARY):
            with pytest.raises(Http404):
                reconciliation.match_movements(line, [entry.pk], by=make_admin(role))
        assert not Reconciliation.objects.exists()

    def test_append_only_also_in_sql(self, treasurer, cash, bank):  # noqa: F811
        entry = deposit(cash, bank, treasurer)[1]
        (line,) = opened((12_000, "INGRES"), by=treasurer)
        reconciliation.match_movements(line, [entry.pk], by=treasurer)
        for sql in (
            "DELETE FROM treasury_reconciliation_matched_movements",
            "UPDATE treasury_reconciliation_matched_movements SET movement_id = movement_id",
            "TRUNCATE treasury_reconciliation_matched_movements",
        ):
            with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
                cur.execute(sql)


class TestUndo:
    def test_p394_undo_leaves_the_movements_and_the_line_can_be_matched_again(
        self,
        treasurer,
        bank,  # noqa: F811
    ):
        donation = other_income(bank, treasurer)
        (line,) = opened((3000, "DONATIU"), by=treasurer)
        done = reconciliation.match_movements(line, [donation.pk], by=treasurer)
        # Mentre és casat, el moviment no s'anul·la: la línia quedaria amb un moviment anul·lat.
        with pytest.raises(services.NotReversible):
            services.reverse(donation, reason=REASON, by=treasurer)
        with pytest.raises(Rejected):
            reconciliation.undo(done, reason=" ", by=treasurer)
        before = Movement.objects.count()
        undone = reconciliation.undo(done, reason=REASON, by=treasurer)
        assert (undone.reason, undone.undone_by) == (REASON, treasurer)
        assert (
            Movement.objects.count() == before
            and not Movement.objects.get(pk=donation.pk).is_reversed
        )
        assert status(line) == State.PENDING
        entry = AuditEntry.objects.get(action=reconciliation.UNDONE)
        assert entry.details["movements"] == [donation.pk] and entry.details["charges"] == []
        assert Reconciliation.objects.filter(pk=done.pk).exists()  # no s'esborra res
        reconciliation.match_movements(line, [donation.pk], by=treasurer)
        assert status(line) == State.RECONCILED

    def test_review_2_reverse_locks_the_movement_before_the_check(self, treasurer, bank):  # noqa: F811
        donation = other_income(bank, treasurer)
        with CaptureQueriesContext(connection) as queries:
            services.reverse(donation, reason=REASON, by=treasurer)
        sql = [q["sql"] for q in queries]
        locked = next(
            n for n, q in enumerate(sql) if "FOR UPDATE" in q and '"treasury_movement"' in q
        )
        guard = next(
            n for n, q in enumerate(sql) if "treasury_reconciliation_matched_movements" in q
        )
        assert locked < guard

    def test_after_undo_the_movement_can_be_reversed(self, treasurer, bank):  # noqa: F811
        donation = other_income(bank, treasurer)
        (line,) = opened((3000, "DONATIU"), by=treasurer)
        done = reconciliation.match_movements(line, [donation.pk], by=treasurer)
        reconciliation.undo(done, reason=REASON, by=treasurer)
        services.reverse(donation, reason=REASON, by=treasurer)
        assert Movement.objects.get(pk=donation.pk).is_reversed
        assert donation not in reconciliation.matchable_movements(line)


class TestManualSettlement:
    def test_p395_a_settlement_out_of_the_window_is_a_manual_choice(self, two, treasurer):
        late = received(settled_on=date(2026, 10, 1))  # fora de la finestra (P-364)
        line = bank_line(treasurer)
        assert StatementLineState.objects.get(statement_line=line).proposed_settlement is None
        assert reconciliation.settlement_choices(line) == [late]
        settlements.confirm_line(line, late.pk, by=treasurer)
        assert ProviderSettlement.objects.get().status == ProviderSettlement.Status.RECONCILED
        assert status(line) == State.RECONCILED

    def test_review_5_a_settlement_beyond_the_shown_list_can_be_confirmed(
        self,
        two,
        treasurer,
        person,  # noqa: F811
        monkeypatch,
    ):
        monkeypatch.setattr(reconciliation, "SEARCH_LIMIT", 1)
        older = received(settled_on=date(2026, 10, 1))
        collected(person, 12500, "REF-C")
        newer = received(
            SettlementLine("REF-C", 12500), external_id="LIQ-002", settled_on=date(2026, 10, 2)
        )
        line = bank_line(treasurer)
        assert reconciliation.settlement_choices(line, limit=reconciliation.SEARCH_LIMIT) == [newer]
        settlements.confirm_line(line, older.pk, by=treasurer)
        assert ProviderSettlement.objects.get(pk=older.pk).status == "reconciled"

    def test_a_settlement_proposed_to_another_line_is_not_offered(self, two, treasurer):
        received()
        proposed, other = lines(treasurer, (NET, "ABONAMENT LIQ-001"), (NET, "ABONAMENT"))
        reconciliation.refresh()
        assert status(proposed) == State.PROPOSED
        assert reconciliation.settlement_choices(other) == []

    def test_an_outgoing_line_gets_no_settlement(self, two, treasurer):
        received(settled_on=date(2026, 10, 1))
        (line,) = opened((-NET, "SORTIDA"), by=treasurer)
        assert reconciliation.settlement_choices(line) == []

    def test_p366_the_bank_leg_of_one_confirmed_without_a_line_is_not_matchable(
        self,
        two,
        treasurer,
        person,  # noqa: F811
    ):
        collected(person, 12500, "REF-C")
        settlement = received(
            SettlementLine("REF-C", 12500), external_id="LIQ-9", settled_on=date(2026, 9, 1)
        )
        settlements.confirm(settlement, by=treasurer)
        leg = settlement.movements.get(account__kind="bank")
        line = bank_line(treasurer, amount=leg.amount_cents)
        assert leg not in reconciliation.matchable_movements(line)  # opció A: s'exclou la línia


class TestViews:
    def test_review_and_confirm_by_post(self, treasurer, cash, bank):  # noqa: F811
        entry = deposit(cash, bank, treasurer)[1]
        (line,) = opened((12_000, "INGRES EFECTIU"), by=treasurer)
        client = client_for(treasurer)
        url = reverse("administration:treasury_match_movements", args=[line.pk])
        page = client.get(url).content.decode()
        assert f'value="{entry.pk}"' in page and "Ingrés de l&#x27;efectiu" in page
        listing = client.get(reverse("administration:treasury_reconciliation")).content.decode()
        assert url in listing
        review = client.post(url, {"moviment": [entry.pk]}).content.decode()
        assert "Confirma el casament" in review and not Reconciliation.objects.exists()
        response = client.post(url, {"moviment": [entry.pk], "confirma": "1"})
        assert response.status_code == 302 and status(line) == State.RECONCILED
        listing = client.get(reverse("administration:treasury_reconciliation")).content.decode()
        assert "Traspàs · Ingrés de l&#x27;efectiu de la caixa" in listing
        assert "els moviments casats no es toquen" in listing

    def test_a_wrong_sum_goes_back_with_an_error(self, treasurer, cash, bank):  # noqa: F811
        entry = deposit(cash, bank, treasurer, amount=1000)[1]
        (line,) = opened((12_000, "INGRES"), by=treasurer)
        client = client_for(treasurer)
        url = reverse("administration:treasury_match_movements", args=[line.pk])
        response = client.post(url, {"moviment": [entry.pk]}, follow=True)
        assert "han de coincidir" in response.content.decode()
        assert not Reconciliation.objects.exists()

    def test_undo_message_says_the_movements_stay(self, treasurer, cash, bank):  # noqa: F811
        entry = deposit(cash, bank, treasurer)[1]
        (line,) = opened((12_000, "INGRES"), by=treasurer)
        done = reconciliation.match_movements(line, [entry.pk], by=treasurer)
        response = client_for(treasurer).post(
            reverse("administration:treasury_undo_reconciliation", args=[done.pk]),
            {"motiu": REASON},
            follow=True,
        )
        assert "Els moviments no es toquen" in response.content.decode()
        assert status(line) == State.PENDING

    def test_a_proposed_line_shows_why_and_no_form(self, treasurer, charge):  # noqa: F811
        (line,) = opened((9000, ref(charge(9000))), by=treasurer)
        url = reverse("administration:treasury_match_movements", args=[line.pk])
        page = client_for(treasurer).get(url).content.decode()
        assert "ja té una proposta" in page and 'name="moviment"' not in page

    def test_review_4_the_closest_movements_to_the_line_date_come_first(
        self,
        treasurer,
        bank,  # noqa: F811
        monkeypatch,
    ):
        monkeypatch.setattr(reconciliation, "SEARCH_LIMIT", 1)
        near = other_income(bank, treasurer, value_date=date(2026, 11, 3))
        other_income(bank, treasurer, value_date=date(2026, 1, 5))  # més recent per pk, però lluny
        (line,) = opened((3000, "DONATIU"), by=treasurer)  # data de valor: 02/11/2026
        url = reverse("administration:treasury_match_movements", args=[line.pk])
        response = client_for(treasurer).get(url)
        assert [item["movement"] for item in response.context["found"]] == [near]
        assert response.context["more"]

    def test_review_8_a_bad_id_empties_the_choice(self, treasurer, bank):  # noqa: F811
        donation = other_income(bank, treasurer)
        (line,) = opened((3000, "DONATIU"), by=treasurer)
        url = reverse("administration:treasury_match_movements", args=[line.pk])
        response = client_for(treasurer).post(
            url, {"moviment": [donation.pk, "x"], "confirma": "1"}, follow=True
        )
        assert "Tria un o més moviments" in response.content.decode()
        assert not Reconciliation.objects.exists()
