"""Traspassos i arqueig (T-M04-09; HU-T07, HU-T08; P-M04-D; CA-T07.1, CA-T08.1; RN-T12, RN-T13;
VT-06; P-222, P-224, P-225). Només dades inventades."""

from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.http import Http404
from django.utils import timezone

from apps.core.models import AppendOnlyError, AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import services
from apps.treasury.balances import balance
from apps.treasury.models import CashCount, Movement, TreasuryAccount
from apps.treasury.tests.test_movements import adjustments, cash, fields  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
K = Movement.Kind
IN, OUT = Movement.Direction.IN, Movement.Direction.OUT
DAY = date(2026, 11, 13)
REASON = "Recompte de la caixa després de la sortida (prova)"


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


@pytest.fixture
def bank():
    return TreasuryAccount.objects.get(name="Banc principal")


def deposit(cash, bank, by, amount=12_000, **kwargs):  # noqa: F811
    kwargs = {"value_date": DAY, "concept": "Ingrés de l'efectiu de la caixa", **kwargs}
    return services.record_transfer(cash, bank, amount, by=by, **kwargs)


class TestTransfer:
    def test_ca_t07_1_two_linked_legs_same_amount_no_department(self, treasurer, cash, bank):  # noqa: F811
        out, entry = deposit(cash, bank, treasurer, concept="  Ingrés de l'efectiu  ")
        assert (out.account, out.direction, entry.account, entry.direction) == (
            cash,
            OUT,
            bank,
            IN,
        )
        for leg in (out, entry):
            assert (leg.kind, leg.amount_cents, leg.value_date) == (K.TRANSFER, 12_000, DAY)
            assert (leg.department, leg.cost_centre, leg.concept) == (
                None,
                None,
                "Ingrés de l'efectiu",
            )
            assert leg.recorded_by == treasurer
        assert entry.linked_movement == out and list(out.linked_from.all()) == [entry]
        # RN-T12: ni ingrés ni despesa; només mou el saldo d'un compte a l'altre.
        assert (balance(cash, DAY), balance(bank, DAY)) == (-12_000, 12_000)
        entry_log = AuditEntry.objects.get(action=services.TRANSFER_RECORDED)
        assert entry_log.actor_account == treasurer
        assert entry_log.details == {
            "from": "Caixa",
            "to": "Banc principal",
            "amount_cents": 12_000,
            "value_date": "2026-11-13",
            "legs": [out.pk, entry.pk],
        }

    def test_ca_t07_2_partial_the_bank_leg_is_the_one_to_match(self, treasurer, cash, bank):  # noqa: F811
        # La línia de l'extracte es casarà amb l'entrada al banc (casar a mà: T-M04-11/12).
        deposit(cash, bank, treasurer)
        legs = Movement.objects.filter(account=bank, kind=K.TRANSFER, direction=IN)
        assert legs.get().linked_movement.account == cash

    def test_p_114_corrected_with_a_transfer_the_other_way(self, treasurer, cash, bank):  # noqa: F811
        deposit(cash, bank, treasurer)
        deposit(bank, cash, treasurer, concept="Correcció del traspàs")
        assert (balance(cash, DAY), balance(bank, DAY)) == (0, 0)

    def test_t6_treasurer_and_administrator_only(self, make_admin, cash, bank):  # noqa: F811
        assert deposit(cash, bank, make_admin("administrator"))
        for role in ("secretary", "board"):
            with pytest.raises(Http404):
                deposit(cash, bank, make_admin(role))
        assert Movement.objects.count() == 2

    @pytest.mark.parametrize("amount", [0, -1, 1.5, True, "100"])
    def test_amount_is_positive_cents(self, treasurer, cash, bank, amount):  # noqa: F811
        with pytest.raises(services.InvalidAmount):
            deposit(cash, bank, treasurer, amount=amount)
        assert not Movement.objects.exists()

    @pytest.mark.parametrize("concept", ["", "   ", None, "x" * 141])
    def test_concept_is_required_and_short(self, treasurer, cash, bank, concept):  # noqa: F811
        with pytest.raises(services.TransferRejected):
            deposit(cash, bank, treasurer, concept=concept)
        assert not Movement.objects.exists()

    def test_p_224_no_future_value_date(self, treasurer, cash, bank):  # noqa: F811
        tomorrow = timezone.localdate() + timedelta(days=1)
        with pytest.raises(services.TransferRejected):
            deposit(cash, bank, treasurer, value_date=tomorrow)
        assert deposit(cash, bank, treasurer, value_date=timezone.localdate())

    def test_same_account_is_rejected(self, treasurer, cash):  # noqa: F811
        with pytest.raises(services.TransferRejected):
            deposit(cash, cash, treasurer)
        assert not Movement.objects.exists()

    def test_p_222_a_transit_account_is_not_a_manual_transfer(self, treasurer, cash, bank):  # noqa: F811
        transit = services.create_transit_account("fake", "Trànsit de proves")
        for source, destination in ((transit, bank), (bank, transit), (cash, transit)):
            with pytest.raises(services.TransferRejected):
                deposit(source, destination, treasurer)
        assert not Movement.objects.exists()

    def test_all_or_nothing_with_an_inactive_destination(self, treasurer, cash, bank):  # noqa: F811
        TreasuryAccount.objects.filter(pk=bank.pk).update(active=False)
        with pytest.raises(ValidationError):
            deposit(cash, bank, treasurer)
        assert not Movement.objects.exists()
        assert not AuditEntry.objects.filter(action=services.TRANSFER_RECORDED).exists()


def count(by, counted, **kwargs):
    kwargs = {"counted_on": DAY, **kwargs}
    return services.record_cash_count(
        TreasuryAccount.objects.get(name="Caixa"), counted, by=by, **kwargs
    )


class TestCashCount:
    @pytest.fixture(autouse=True)
    def cash_in_box(self, treasurer, cash, bank):  # noqa: F811
        """Saldo de la caixa el dia 13: 20.000 cèntims entrats (del banc) i 5.000 sortits."""
        deposit(bank, cash, treasurer, amount=20_000, value_date=DAY - timedelta(days=3))
        deposit(cash, bank, treasurer, amount=5_000)
        deposit(cash, bank, treasurer, amount=700, value_date=DAY + timedelta(days=1))  # després

    def test_ca_t08_1_the_difference_is_shown_and_nothing_is_booked(self, treasurer):
        movements = Movement.objects.count()
        result = count(treasurer, 14_650)
        assert (result.computed_cents, result.counted_cents, result.difference_cents) == (
            15_000,
            14_650,
            -350,
        )
        assert result.adjustment is None and result.recorded_by == treasurer
        assert Movement.objects.count() == movements  # cap moviment automàtic
        log = AuditEntry.objects.get(action=services.CASH_COUNTED)
        assert (log.actor_account, log.reason) == (treasurer, "")
        assert log.details == {
            "account": "Caixa",
            "counted_on": "2026-11-13",
            "counted_cents": 14_650,
            "computed_cents": 15_000,
            "difference_cents": -350,
            "adjustment": None,
        }

    @pytest.mark.parametrize(("counted", "direction"), [(14_650, OUT), (15_120, IN)])
    def test_ca_t08_1_optional_adjustment_with_reason(
        self,
        treasurer,
        cash,  # noqa: F811
        adjustments,  # noqa: F811
        counted,
        direction,
    ):
        result = count(treasurer, counted, adjustment_reason=f"  {REASON} ")
        adjustment = result.adjustment
        assert (adjustment.kind, adjustment.direction, adjustment.amount_cents) == (
            K.CASH_ADJUSTMENT,
            direction,
            abs(counted - 15_000),
        )
        assert (adjustment.account, adjustment.value_date, adjustment.reason) == (cash, DAY, REASON)
        assert (adjustment.department, adjustment.cost_centre) == (
            adjustments.department,
            adjustments,
        )  # VT-06: «General / Ajustos de caixa»
        assert adjustment.recorded_by == treasurer
        assert balance(cash, DAY) == counted  # l'ajust deixa el saldo igual al comptat
        log = AuditEntry.objects.get(action=services.CASH_COUNTED)
        assert (log.reason, log.details["adjustment"]) == (REASON, adjustment.pk)

    def test_no_difference_nothing_to_adjust(self, treasurer):
        assert count(treasurer, 15_000).difference_cents == 0
        with pytest.raises(services.CashCountRejected):
            count(treasurer, 15_000, adjustment_reason=REASON)
        assert not Movement.objects.filter(kind=K.CASH_ADJUSTMENT).exists()
        assert CashCount.objects.count() == 1

    def test_a_negative_computed_balance_and_a_zero_count(self, treasurer):
        # El dia 9 la caixa encara no tenia l'entrada del dia 10: no hi ha res a calcular.
        assert count(treasurer, 0, counted_on=DAY - timedelta(days=4)).difference_cents == 0
        deposit(
            TreasuryAccount.objects.get(name="Caixa"),
            TreasuryAccount.objects.get(name="Banc principal"),
            treasurer,
            amount=20_000,
        )
        result = count(treasurer, 0)
        assert (result.computed_cents, result.difference_cents) == (-5_000, 5_000)

    def test_t7_treasurer_and_administrator_only(self, make_admin):  # noqa: F811
        assert count(make_admin("administrator"), 15_000)
        for role in ("secretary", "board"):
            with pytest.raises(Http404):
                count(make_admin(role), 14_000, adjustment_reason=REASON)
        assert CashCount.objects.count() == 1
        assert not Movement.objects.filter(kind=K.CASH_ADJUSTMENT).exists()

    @pytest.mark.parametrize("counted", [-1, 1.5, True, "100", None])
    def test_counted_is_cents_zero_or_more(self, treasurer, counted):
        with pytest.raises(services.InvalidAmount):
            count(treasurer, counted)
        assert not CashCount.objects.exists()

    def test_p_224_no_future_date(self, treasurer):
        with pytest.raises(services.CashCountRejected):
            count(treasurer, 100, counted_on=timezone.localdate() + timedelta(days=1))
        assert not CashCount.objects.exists()

    def test_only_a_cash_account(self, treasurer, bank):
        with pytest.raises(services.CashCountRejected):
            services.record_cash_count(bank, 100, counted_on=DAY, by=treasurer)
        assert not CashCount.objects.exists()

    def test_all_or_nothing_when_the_adjustment_fails(self, treasurer, cash):  # noqa: F811
        TreasuryAccount.objects.filter(pk=cash.pk).update(active=False)
        with pytest.raises(ValidationError):
            count(treasurer, 100, adjustment_reason=REASON)
        assert not CashCount.objects.exists()
        assert not Movement.objects.filter(kind=K.CASH_ADJUSTMENT).exists()


class TestCashCountIsAppendOnly:
    @pytest.fixture
    def counted(self, treasurer):
        return count(treasurer, 0)

    def test_orm_refuses_changes(self, counted):
        with pytest.raises(AppendOnlyError):
            counted.save()
        with pytest.raises(AppendOnlyError):
            counted.delete()

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE treasury_cashcount SET counted_cents = 1",
            "DELETE FROM treasury_cashcount",
            "TRUNCATE treasury_cashcount CASCADE",
        ],
    )
    def test_database_refuses_direct_sql(self, counted, sql):
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(sql)
        assert CashCount.objects.get().counted_cents == 0

    def test_database_checks_the_difference(self, treasurer, cash):  # noqa: F811
        with pytest.raises(IntegrityError), transaction.atomic():
            CashCount.objects.create(
                account=cash,
                counted_on=DAY,
                counted_cents=100,
                computed_cents=0,
                difference_cents=50,
                recorded_by=treasurer,
            )
