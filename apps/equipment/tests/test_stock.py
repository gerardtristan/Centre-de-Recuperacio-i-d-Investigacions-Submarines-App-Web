"""T-M03-04: stock en una data (RN-M03-16; CA-M03-15; MT4). Només dades inventades."""

import datetime

import pytest
from django.http import Http404

from apps.activities.tests.test_attendance import enrolled
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, handover, inventory, stock
from apps.equipment.models import EquipmentItem

from .test_assignments import JUNE, jacket, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db


def test_ca_m03_15_every_piece_in_exactly_one_state(manager, keeper):  # noqa: F811
    pieces = [jacket(keeper) for _ in range(5)] + [jacket(keeper, "L")]
    inventory.change_status(pieces[0], EquipmentItem.Status.IN_REVIEW, by=keeper)
    gone = jacket(keeper)
    inventory.change_status(gone, EquipmentItem.Status.RETIRED, by=keeper, reason="Perduda.")
    activity = outing(manager)  # 14 i 15 de juny
    handover.deliver(
        assignments.assign_club(enrolled(activity, "A"), pieces[1], by=keeper), by=keeper
    )
    assignments.assign_club(enrolled(activity, "B"), pieces[2], by=keeper)
    lines = {line.measure: line for line in stock.stock(JUNE, viewer=keeper)}
    medium = lines["M"]
    assert (medium.available, medium.assigned, medium.in_use, medium.in_review) == (2, 1, 1, 1)
    assert lines["L"].available == 1
    assert (
        sum(line.total for line in lines.values())
        == EquipmentItem.objects.exclude(status=EquipmentItem.Status.RETIRED).count()
    )
    before = {
        line.measure: line for line in stock.stock(JUNE - datetime.timedelta(days=1), viewer=keeper)
    }
    assert (before["M"].available, before["M"].assigned) == (4, 0)  # encara no ha començat


def test_tanks_by_litres_and_filter_by_type(keeper):  # noqa: F811
    inventory.create_item(equipment_type=kind("Ampolla"), by=keeper, litres=12, next_review_on=JUNE)
    jacket(keeper)
    lines = stock.stock(JUNE, viewer=keeper, equipment_type=kind("Ampolla"))
    assert [(line.equipment_type, line.measure, line.available) for line in lines] == [
        ("Ampolla", "12.0 l", 1)
    ]


def test_mt4_consultation_is_enough_and_without_it_not_found(make_admin):  # noqa: F811
    stock.stock(JUNE, viewer=make_admin(Role.Code.BOARD))  # consulta
    with pytest.raises(Http404):
        stock.stock(JUNE, viewer=make_admin(Role.Code.SECRETARY))
