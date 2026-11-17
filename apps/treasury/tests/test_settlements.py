"""Liquidacions del proveïdor (T-M04-13, primer tall; HU-T11; P-M04-F; RN-T21; VT-05; LT8 i LT9;
CA-T02.2, CA-T04.4, CA-T11.1 i CA-T11.2). Només dades inventades."""

from dataclasses import replace
from datetime import date

import pytest
from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.http import Http404

from apps.core.models import AuditEntry, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import services, settlements
from apps.treasury.balances import balances
from apps.treasury.models import Movement, ProviderSettlement, SettlementItem, TreasuryAccount
from apps.treasury.settlements import SettlementData, SettlementLine
from apps.treasury.tests.test_record_income import SYSTEM, new_transit, paid, record

pytestmark = pytest.mark.django_db
K = Movement.Kind
Status = ProviderSettlement.Status
ON = date(2026, 11, 20)


@pytest.fixture
def transit():
    return new_transit()


@pytest.fixture
def person(make_person):
    return make_person("Núria", "Coll")


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def collected(person, amount, ref, method=Payment.Method.CARD):
    """Un cobrament amb targeta pagat, amb la referència del proveïdor i l'ingrés al trànsit."""
    payment = paid(person, amount=amount, method=method)
    Payment.objects.filter(pk=payment.pk).update(provider_reference=ref)
    record(payment)
    return payment


def data(*lines, gross=None, fees=120, external_id="LIQ-001"):
    """Exemple de M04-7: brut 12.500, comissions 120, net 12.380."""
    lines = lines or (SettlementLine("REF-A", 9000), SettlementLine("REF-B", 3500))
    gross = sum(line.amount_cents for line in lines) if gross is None else gross
    return SettlementData(external_id, ON, gross, fees, gross - fees, tuple(lines))


@pytest.fixture
def two(person, transit):
    return collected(person, 9000, "REF-A"), collected(person, 3500, "REF-B")


def record_it(payload=None, provider=None):
    return settlements.record_settlement(
        provider or settings.PAYMENTS_PROVIDER, payload or data(), by=SYSTEM
    )


def transit_balance(transit):
    return balances(ON).get(pk=transit.pk).balance_cents


class TestSplit:
    def test_lt9_the_spare_cent_goes_to_the_largest(self):
        # 120 × 9000 / 12.500 = 86,4 → 86; 120 × 3500 / 12.500 = 33,6 → 33; sobra 1 → 87 i 33.
        assert settlements.split(120, [9000, 3500]) == [87, 33]

    @pytest.mark.parametrize(
        ("total", "amounts", "shares"),
        [
            (100, [5000, 5000], [50, 50]),
            (0, [9000, 3500], [0, 0]),
            (2, [1000, 1000, 1000], [1, 1, 0]),  # a igual import, a la primera
            (5, [3500, 9000, 3500], [1, 3, 1]),
            (7, [100], [7]),
        ],
    )
    def test_shares_add_up_to_the_total(self, total, amounts, shares):
        assert settlements.split(total, amounts) == shares
        assert sum(shares) == total


class TestRecord:
    def test_a_settlement_with_known_collections_is_received(self, two):
        settlement = record_it()
        assert (settlement.status, settlement.review_notes) == (Status.RECEIVED, [])
        assert settlement.net_cents == settlement.gross_cents - settlement.fees_cents == 12380
        items = list(settlement.items.order_by("pk"))
        assert [(i.payment, i.amount_cents, i.fee_cents) for i in items] == [
            (two[0], 9000, None),
            (two[1], 3500, None),
        ]
        # CA-T04.4: el repartiment proporcional, visible abans de confirmar.
        assert list(settlements.fee_split(settlement).values()) == [87, 33]
        assert not Movement.objects.filter(kind__in=[K.FEE, K.TRANSFER]).exists()
        entry = AuditEntry.objects.get(action=settlements.RECORDED)
        assert entry.details["status"] == Status.RECEIVED

    def test_detailed_fees_are_kept(self, two):
        payload = data(SettlementLine("REF-A", 9000, 100), SettlementLine("REF-B", 3500, 20))
        settlement = record_it(payload)
        assert list(settlements.fee_split(settlement).values()) == [100, 20]

    def test_ca_t11_2_an_unknown_collection_goes_to_review(self, two):
        payload = data(SettlementLine("REF-A", 9000), SettlementLine("REF-X", 3500))
        settlement = record_it(payload)
        assert settlement.status == Status.TO_REVIEW
        assert settlement.review_notes == [{"reference": "REF-X", "problem": "unknown_payment"}]
        assert not settlement.items.exists()

    def test_each_problem_has_its_reason(self, person, transit, two):
        no_income = paid(person, amount=1000)
        Payment.objects.filter(pk=no_income.pk).update(provider_reference="REF-N")
        collected(person, 2000, "REF-T", method=Payment.Method.TRANSFER)  # ingrés al banc
        refunded = collected(person, 3000, "REF-R")
        services.record_refund(refunded, 100, reason="Prova", by=SYSTEM)
        record_it(data(SettlementLine("REF-A", 9000), fees=0, external_id="LIQ-000"))
        payload = data(
            SettlementLine("REF-B", 3500),
            SettlementLine("REF-B", 3500),
            SettlementLine("REF-N", 1000),
            SettlementLine("REF-T", 2000),
            SettlementLine("REF-R", 3000),
            SettlementLine("REF-A", 9000),
            SettlementLine("REF-A", 1),
        )
        problems = [n["problem"] for n in record_it(payload).review_notes]
        assert problems == [
            "repeated_line",
            "no_income",
            "no_income",
            "refunded",
            "already_settled",
            "repeated_line",
        ]

    def test_a_reversed_income_and_a_different_amount_go_to_review(self, two, treasurer):
        services.reverse(
            Movement.objects.get(payment=two[1], kind=K.INCOME),
            reason="Prova",
            by=treasurer,
            origin=services.RECONCILIATION,
        )
        payload = data(SettlementLine("REF-A", 8999), SettlementLine("REF-B", 3500))
        assert [n["problem"] for n in record_it(payload).review_notes] == [
            "amount_mismatch",
            "no_income",
        ]

    @pytest.mark.parametrize(
        "payload",
        [
            replace(data(), net_cents=12381),  # net ≠ brut − comissions
            data(gross=12501),  # les línies no sumen el brut
            data(SettlementLine("REF-A", 9000, 100), SettlementLine("REF-B", 3500)),  # barreja
            data(SettlementLine("REF-A", 9000, 100), SettlementLine("REF-B", 3500, 10)),
            data(SettlementLine("REF-A", 9000, -1), SettlementLine("REF-B", 3500, 121)),
            data(fees=1.5),
            data(fees=True),
            data(SettlementLine("REF-A", 0)),
            replace(data(), lines=(), gross_cents=1, net_cents=1, fees_cents=0),
            data(fees=12500),  # net zero
        ],
    )
    def test_figures_that_do_not_add_up_are_rejected(self, two, payload):
        with pytest.raises(settlements.SettlementRejected):
            record_it(payload)
        assert not ProviderSettlement.objects.exists()

    def test_a_repeated_settlement_is_rejected(self, two):
        record_it()
        with pytest.raises(settlements.DuplicateSettlement):
            record_it()
        assert ProviderSettlement.objects.count() == 1

    def test_nobody_else_records_it(self, two):
        with pytest.raises(services.BrowserOriginRejected):
            settlements.record_settlement("x", data(), by=None)

    def test_items_are_append_only_also_in_sql(self, two):
        item = record_it().items.first()
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                "UPDATE treasury_settlementitem SET amount_cents = 1 WHERE id = %s", [item.pk]
            )
        assert SettlementItem.objects.get(pk=item.pk).amount_cents == 9000


class TestConfirm:
    def test_ca_t11_1_fees_by_department_and_the_net_to_the_bank(self, two, transit, treasurer):
        settlement = settlements.confirm(record_it(), by=treasurer)
        assert settlement.status == Status.RECONCILED
        fees = {m.payment: m for m in Movement.objects.filter(kind=K.FEE)}
        assert (fees[two[0]].amount_cents, fees[two[1]].amount_cents) == (87, 33)
        assert fees[two[0]].cost_centre.full_name == "General / Quotes de socis"
        out, entry = Movement.objects.filter(kind=K.TRANSFER).order_by("pk")
        bank = TreasuryAccount.objects.get(kind="bank")
        assert (out.account, out.direction, out.amount_cents) == (transit, "out", 12380)
        assert out.settlement == entry.settlement == settlement
        assert (entry.account, entry.direction, entry.linked_movement) == (bank, "in", out)
        assert (out.value_date, out.department, out.recorded_by) == (ON, None, treasurer)
        # 12.500 − 12.380 − 120 = 0 (exemple de M04-7).
        assert transit_balance(transit) == 0
        assert AuditEntry.objects.filter(action=settlements.CONFIRMED).count() == 1

    def test_ca_t02_2_the_transit_keeps_what_is_not_settled(self, two, person, transit, treasurer):
        collected(person, 4500, "REF-C")
        settlements.confirm(record_it(), by=treasurer)
        assert transit_balance(transit) == 4500

    def test_without_fees_only_the_transfer(self, two, treasurer):
        settlements.confirm(record_it(data(fees=0)), by=treasurer)
        assert not Movement.objects.filter(kind=K.FEE).exists()
        assert Movement.objects.filter(kind=K.TRANSFER).count() == 2

    def test_only_with_t4(self, two, make_admin):  # noqa: F811
        settlement = record_it()
        for role in ("administrator", "secretary"):
            with pytest.raises(Http404):
                settlements.confirm(settlement, by=make_admin(role))
        assert ProviderSettlement.objects.get().status == Status.RECEIVED

    def test_only_a_received_settlement(self, two, treasurer):
        settlement = settlements.confirm(record_it(), by=treasurer)
        with pytest.raises(settlements.SettlementRejected):
            settlements.confirm(settlement, by=treasurer)
        review = record_it(data(SettlementLine("REF-X", 100), fees=0, external_id="LIQ-002"))
        with pytest.raises(settlements.SettlementRejected):
            settlements.confirm(review, by=treasurer)

    def test_p_116_a_different_fee_already_there_rolls_everything_back(self, two, treasurer):
        services.record_fee(two[0], 90, by=SYSTEM)
        with pytest.raises(services.FeeAlreadyRecorded):
            settlements.confirm(record_it(), by=treasurer)
        assert ProviderSettlement.objects.get().status == Status.RECEIVED
        assert not Movement.objects.filter(kind=K.TRANSFER).exists()
        assert Movement.objects.filter(kind=K.FEE).count() == 1

    def test_without_a_single_bank_account_nothing_is_booked(self, two, treasurer):
        TreasuryAccount.objects.filter(kind="bank").update(active=False)
        with pytest.raises(settlements.SettlementRejected):
            settlements.confirm(record_it(), by=treasurer)
        assert not Movement.objects.filter(kind__in=[K.FEE, K.TRANSFER]).exists()
