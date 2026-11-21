"""T-M03-13: cost per participant i per activitat; servei per al 09 (RN-M03-07 a 10; CA-M03-08).
Només dades inventades."""

import pytest

from apps.activities.tests.test_attendance import enrolled
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, costs, handover, inventory
from apps.equipment.models import CentreRate, DiveCentre, UsageRate

from .test_assignments import JUNE, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db


@pytest.fixture
def centre(keeper):  # noqa: F811
    centre = DiveCentre.objects.create(name="Centre A")
    CentreRate.objects.create(
        centre=centre, label="Equip complet", equipment_type=kind("Jaquet"), cost_cents=2500,
        member_price_cents=3000, valid_from=JUNE, created_by=keeper,
    )  # fmt: skip
    return centre


def used(row, keeper):  # noqa: F811
    return handover.deliver(row, by=keeper)


def test_ca_m03_08_cost_per_participant(manager, keeper, centre):  # noqa: F811
    UsageRate.objects.create(
        equipment_type=kind("Ampolla"), cost_per_day_cents=200, valid_from=JUNE
    )
    activity = outing(manager, days=1)
    p1, p2, p3 = enrolled(activity, "P1"), enrolled(activity, "P2"), enrolled(activity, "P3")
    used(assignments.assign_own(p1, kind("Aletes"), by=keeper), keeper)
    tank = inventory.create_item(
        equipment_type=kind("Ampolla"), by=keeper, litres=12, next_review_on=JUNE
    )
    used(assignments.assign_club(p2, tank, by=keeper), keeper)
    used(assignments.assign_rented(p2, kind("Jaquet"), centre, by=keeper), keeper)
    other_tank = inventory.create_item(
        equipment_type=kind("Ampolla"), by=keeper, litres=15, next_review_on=JUNE
    )
    handover.mark_not_used(assignments.assign_club(p3, other_tank, by=keeper), by=keeper)

    cost = costs.activity_material_cost(activity)
    assert [cost.per_participant.get(p.pk, 0) for p in (p1, p2, p3)] == [0, 2700, 0]
    assert (cost.club_use_cents, cost.rental_cost_estimated_cents) == (200, 2500)


def test_ca_m03_08_four_rentals_leave_a_margin_of_2000(manager, keeper, centre):  # noqa: F811
    activity = outing(manager, days=1)
    for i in range(4):
        assignments.assign_rented(enrolled(activity, f"L{i}"), kind("Jaquet"), centre, by=keeper)
    cost = costs.activity_material_cost(activity)
    assert (cost.rental_participant_cents, cost.rental_cost_estimated_cents) == (12000, 10000)
    assert cost.rental_margin_cents == 2000
    assert cost.club_use_cents == 0 and cost.per_participant == {}  # encara no s'han lliurat
    assert len(costs.rentals_for(activity, centre)) == 4
