"""T-M03-09 i T-M03-12: lliurar, retornar, pas a revisió, quantitats reals i `used_by`
(RN-M03-12; HU-M03-11; MT6 i MT10). Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities.tests.helpers import a_person
from apps.activities.tests.test_attendance import enrolled
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, handover
from apps.equipment.models import EquipmentItem

from .test_assignments import jacket, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
R = Role.Code


def test_rn_m03_12_deliver_return_and_send_to_review(manager, keeper):  # noqa: F811
    activity = outing(manager)
    item = jacket(keeper)
    row = assignments.assign_club(enrolled(activity), item, by=keeper)
    with pytest.raises(ValidationError):  # no es retorna el que no s'ha lliurat
        handover.give_back(row, by=keeper)
    row = handover.deliver(row, by=keeper)
    assert row.status == "delivered" and row.delivered_at
    row = handover.give_back(row, by=keeper, to_review=True, note="Una fuita (inventat).")
    item.refresh_from_db()
    assert (row.status, item.status) == ("returned", EquipmentItem.Status.IN_REVIEW)
    changes = AuditEntry.objects.filter(action=handover.STATUS_CHANGED).order_by("id")
    assert [(e.old_value, e.new_value) for e in changes] == [
        ("planned", "delivered"), ("delivered", "returned"),
    ]  # fmt: skip
    with pytest.raises(ValidationError):  # retornada és final
        handover.mark_not_used(row, by=keeper)


def test_a_returned_piece_without_review_stays_available(manager, keeper):  # noqa: F811
    item = jacket(keeper)
    row = handover.deliver(
        assignments.assign_club(enrolled(outing(manager)), item, by=keeper), by=keeper
    )
    handover.give_back(row, by=keeper)
    item.refresh_from_db()
    assert item.status == EquipmentItem.Status.AVAILABLE


def test_not_used_and_cancelled_free_the_piece(manager, keeper):  # noqa: F811
    activity = outing(manager)
    item = jacket(keeper)
    row = assignments.assign_club(enrolled(activity), item, by=keeper)
    with pytest.raises(ValidationError):
        handover.cancel(row, by=keeper, reason=" ")
    handover.cancel(row, by=keeper, reason="Ja no ve (inventat).")
    again = assignments.assign_club(enrolled(activity, "Una altra"), item, by=keeper)
    handover.mark_not_used(handover.deliver(again, by=keeper), by=keeper)
    assert item in assignments.available_items(activity, kind("Jaquet"), size="M")


def test_mt10_the_secretary_cannot_confirm_quantities(manager, keeper, make_admin):  # noqa: F811
    row = assignments.assign_own(enrolled(outing(manager)), kind("Aletes"), by=keeper)
    with pytest.raises(Http404):
        handover.mark_not_used(row, by=make_admin(R.SECRETARY))


def test_hu_m03_11_used_by_lists_only_what_was_used(manager, keeper):  # noqa: F811
    activity = outing(manager)
    row = enrolled(activity)
    person = row.person
    used = assignments.assign_club(row, jacket(keeper), by=keeper)
    handover.deliver(used, by=keeper)
    skipped = assignments.assign_own(row, kind("Aletes"), by=keeper)
    handover.mark_not_used(skipped, by=keeper)
    assert handover.used_by(person) == [
        {"activity": activity, "items": [
            {"type": "Jaquet", "size": "M", "litres": None, "origin": "club"},
        ]},
    ]  # fmt: skip
    assert handover.used_by(a_person("Ningú")) == []
