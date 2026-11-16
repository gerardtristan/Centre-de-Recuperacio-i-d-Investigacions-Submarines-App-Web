"""Anul·lació amb contramoviment (T-M04-08; P-M04-C; CA-T06.1, CA-T06.2, CA-T17.1; RN-T25,
RN-T27; P-114; P-115). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone

from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.treasury import services
from apps.treasury.models import Movement, TreasuryAccount
from apps.treasury.tests.test_movements import (  # noqa: F401 (fixtures)
    adjustments,
    cash,
    fields,
    row,
)

pytestmark = pytest.mark.django_db
K = Movement.Kind
IN, OUT = Movement.Direction.IN, Movement.Direction.OUT
REASON = "L'ajust es va apuntar dues vegades (prova)"


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def adjustment(fields, direction=OUT):  # noqa: F811
    return Movement.objects.create(**{**fields, "direction": direction})


class TestReverse:
    @pytest.mark.parametrize(("direction", "opposite"), [(OUT, IN), (IN, OUT)])
    def test_ca_t06_1_the_reversal_mirrors_the_original(
        self,
        treasurer,
        fields,  # noqa: F811
        direction,
        opposite,
    ):
        original = adjustment(fields, direction)
        before = row(original.pk)
        reversal = services.reverse(original, reason=f"  {REASON} ", by=treasurer)
        mirror = ("account", "amount_cents", "department", "cost_centre", "concept")
        assert [getattr(reversal, f) for f in mirror] == [getattr(original, f) for f in mirror]
        assert (reversal.kind, reversal.direction, reversal.reverses) == (
            K.REVERSAL,
            opposite,
            original,
        )
        assert (reversal.reason, reversal.recorded_by) == (REASON, treasurer)
        assert reversal.value_date == timezone.localdate()  # RN-T29
        # L'original no canvia, es mostra anul·lat i continua al llistat (RN-T25).
        assert row(original.pk) == before
        assert Movement.objects.get(pk=original.pk).is_reversed
        assert set(Movement.objects.all()) == {original, reversal}
        entry = AuditEntry.objects.get(action=services.MOVEMENT_REVERSED)
        assert (entry.actor_account, entry.reason) == (treasurer, REASON)
        assert entry.details == {
            "reverses": original.pk,
            "kind": K.CASH_ADJUSTMENT,
            "amount_cents": 50,
            "origin": services.MANUAL,
        }

    def test_t5_treasurer_and_administrator_only(self, make_admin, fields):  # noqa: F811
        assert services.reverse(adjustment(fields), reason=REASON, by=make_admin("administrator"))
        original = adjustment(fields)
        for role in ("secretary", "board"):
            with pytest.raises(Http404):
                services.reverse(original, reason=REASON, by=make_admin(role))
        assert not Movement.objects.get(pk=original.pk).is_reversed

    @pytest.mark.parametrize("reason", ["", "   ", None])
    def test_ca_t20_a_reason_is_required(self, treasurer, fields, reason):  # noqa: F811
        original = adjustment(fields)
        with pytest.raises(ValidationError):
            services.reverse(original, reason=reason, by=treasurer)
        assert not Movement.objects.filter(kind=K.REVERSAL).exists()

    def test_ca_t17_1_a_second_reversal_is_already_reversed(self, treasurer, fields):  # noqa: F811
        original = adjustment(fields)
        services.reverse(original, reason=REASON, by=treasurer)
        with pytest.raises(services.AlreadyReversed):
            services.reverse(original, reason=REASON, by=treasurer)
        assert Movement.objects.filter(kind=K.REVERSAL).count() == 1

    def test_a_concurrent_reversal_is_also_already_reversed(
        self,
        treasurer,
        fields,  # noqa: F811
        monkeypatch,
    ):
        # L'altra anul·lació entra entre la comprovació i la inserció: ho atura el OneToOne.
        original = adjustment(fields)
        services.reverse(original, reason=REASON, by=treasurer)
        monkeypatch.setattr(Movement, "is_reversed", property(lambda self: False))
        with pytest.raises(services.AlreadyReversed):
            services.reverse(original, reason=REASON, by=treasurer)
        assert Movement.objects.filter(kind=K.REVERSAL).count() == 1

    def test_ca_t06_2_an_income_is_not_reversed_from_treasury(self, treasurer, fields):  # noqa: F811
        income = Movement.objects.create(**{**fields, "kind": K.INCOME, "direction": IN})
        with pytest.raises(services.NotReversible):
            services.reverse(income, reason=REASON, by=treasurer)
        assert not Movement.objects.get(pk=income.pk).is_reversed

    def test_p_115_a_reversal_is_not_reversed(self, treasurer, fields):  # noqa: F811
        reversal = services.reverse(adjustment(fields), reason=REASON, by=treasurer)
        with pytest.raises(services.NotReversible):
            services.reverse(reversal, reason=REASON, by=treasurer)

    def test_p_114_a_transfer_leg_is_not_reversed_alone(self, treasurer, fields):  # noqa: F811
        leg = {**fields, "kind": K.TRANSFER, "department": None, "cost_centre": None, "reason": ""}
        out = Movement.objects.create(**leg)
        bank = TreasuryAccount.objects.get(name="Banc principal")
        Movement.objects.create(**{**leg, "account": bank, "direction": IN, "linked_movement": out})
        for movement in Movement.objects.all():
            with pytest.raises(services.NotReversible):
                services.reverse(movement, reason=REASON, by=treasurer)
        assert not Movement.objects.filter(kind=K.REVERSAL).exists()


class TestFromReconciliation:
    def test_it_reverses_an_income_without_t5(self, make_admin, fields):  # noqa: F811
        # T4 ja l'ha comprovat `reconciliation.undo`; aquí no cal T5.
        income = Movement.objects.create(**{**fields, "kind": K.INCOME, "direction": IN})
        by = make_admin("secretary")
        reversal = services.reverse(income, reason=REASON, by=by, origin=services.RECONCILIATION)
        assert (reversal.reverses, reversal.direction) == (income, OUT)
        entry = AuditEntry.objects.get(action=services.MOVEMENT_REVERSED)
        assert entry.details["origin"] == services.RECONCILIATION

    def test_it_only_reverses_incomes(self, treasurer, fields):  # noqa: F811
        with pytest.raises(services.NotReversible):
            services.reverse(
                adjustment(fields), reason=REASON, by=treasurer, origin=services.RECONCILIATION
            )

    def test_an_unknown_origin_is_a_programming_error(self, treasurer, fields):  # noqa: F811
        with pytest.raises(ValueError):
            services.reverse(adjustment(fields), reason=REASON, by=treasurer, origin="browser")
