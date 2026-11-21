"""T-M03-19: informes del 03 (part de servei) i els seus permisos. Només dades inventades."""

import datetime

import pytest
from django.http import Http404

from apps.activities.tests.helpers import a_person
from apps.activities.tests.test_attendance import enrolled
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, handover, inventory, reports

from .test_assignments import JUNE, jacket, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
R = Role.Code


def test_most_used_counts_only_used_pieces_in_the_period(manager, keeper):  # noqa: F811
    activity = outing(manager)
    for first in ("A", "B"):
        row = assignments.assign_club(enrolled(activity, first), jacket(keeper), by=keeper)
        handover.deliver(row, by=keeper)
    handover.mark_not_used(
        assignments.assign_own(enrolled(activity, "C"), kind("Aletes"), by=keeper), by=keeper
    )
    june = (datetime.date(2027, 6, 1), datetime.date(2027, 6, 30))
    assert reports.most_used(*june, viewer=keeper) == [
        {"type": "Jaquet", "origin": "club", "uses": 2}
    ]
    july = (datetime.date(2027, 7, 1), datetime.date(2027, 7, 31))
    assert reports.most_used(*july, viewer=keeper) == []


def test_costs_by_object_for_the_courses_manager(make_admin, keeper):  # noqa: F811
    person = a_person("Responsable inventada")
    responsible = make_admin(R.COURSES_MANAGER, person=person)
    own = outing(responsible)
    own.responsible = person
    own.save(update_fields=["responsible"])
    other = outing(responsible)
    assert reports.activity_costs(own, viewer=responsible).club_use_cents == 0
    with pytest.raises(Http404):
        reports.activity_costs(other, viewer=responsible)
    reports.activity_costs(other, viewer=make_admin(R.BOARD))  # consulta
    with pytest.raises(Http404):
        reports.activity_costs(other, viewer=make_admin(R.SECRETARY))


def test_upcoming_reviews_need_mt11(make_admin, keeper):  # noqa: F811
    tank = inventory.create_item(
        equipment_type=kind("Ampolla"), by=keeper, litres=12, next_review_on=JUNE
    )
    assert list(reports.upcoming_reviews(JUNE - datetime.timedelta(days=10), viewer=keeper)) == [
        tank
    ]
    with pytest.raises(Http404):
        reports.upcoming_reviews(JUNE, viewer=make_admin(R.SECRETARY))
