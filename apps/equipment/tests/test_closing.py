"""T-M03-15 (comprovació de tancament) i T-M03-16 (cancel·lacions): «material pendent» i peces
alliberades (RN-M03-13 i 20; L-M03-05; CA-M03-09 i 14). Només dades inventades."""

import pytest

from apps.activities import cancellation, states
from apps.activities import closing as activities_closing
from apps.activities.models import Activity, Enrolment
from apps.activities.tests.test_attendance import enrolled, opened
from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, closing, handover, rentals
from apps.equipment.models import DiveCentre, EquipmentAssignment, EquipmentNeed

from .test_assignments import jacket, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
A = EquipmentAssignment.Status


def test_ca_m03_09_a_delivered_piece_is_pending_material(manager, keeper):  # noqa: F811
    activity = outing(manager)
    row = handover.deliver(
        assignments.assign_club(enrolled(activity), jacket(keeper), by=keeper), by=keeper
    )
    reasons = activities_closing.closing_blockers(activity)
    assert "Hi ha 1 peça de material prevista o lliurada sense tancar." in reasons
    handover.give_back(row, by=keeper)
    assert activities_closing.closing_blockers(activity) == []


def test_unassigned_needs_and_unsent_rental_lists_are_pending(manager, keeper):  # noqa: F811
    activity = outing(manager)
    row = enrolled(activity)
    EquipmentNeed.objects.create(
        enrolment=row, equipment_type=kind("Jaquet"), brings_own=False, size="M"
    )
    EquipmentNeed.objects.create(enrolment=row, equipment_type=kind("Aletes"), brings_own=True)
    rentals.generate(activity, DiveCentre.objects.create(name="Centre A"), by=keeper)
    assert closing.pending_reasons(activity) == [
        "Hi ha 1 necessitat de material sense assignar.",
        "Hi ha 1 llista de lloguer sense enviar.",
    ]
    handover.mark_not_used(assignments.assign_club(row, jacket(keeper), by=keeper), by=keeper)
    assert closing.pending_reasons(activity) == ["Hi ha 1 llista de lloguer sense enviar."]


def test_ca_m03_14_a_cancelled_enrolment_frees_its_planned_pieces(manager, keeper):  # noqa: F811
    activity = opened(outing(manager), Activity.Status.OPEN)
    item = jacket(keeper)
    row = enrolled(activity)
    planned = assignments.assign_club(row, item, by=keeper)
    cancellation.cancel_enrolment(row, by=manager, reason="No pot venir (inventat).")
    planned.refresh_from_db()
    assert planned.status == A.CANCELLED
    assert item in assignments.available_items(activity, kind("Jaquet"), size="M")
    entry = AuditEntry.objects.get(action=closing.RELEASED)
    assert entry.actor_kind == "system"


def test_l_m03_05_a_cancelled_activity_frees_planned_but_not_delivered(manager, keeper):  # noqa: F811
    activity = opened(outing(manager), Activity.Status.OPEN)
    planned = assignments.assign_club(enrolled(activity), jacket(keeper), by=keeper)
    delivered = handover.deliver(
        assignments.assign_club(enrolled(activity, "B"), jacket(keeper), by=keeper), by=keeper
    )
    states.cancel(activity, by=manager, reason="Mal temps (inventat).")
    planned.refresh_from_db()
    delivered.refresh_from_db()
    assert (planned.status, delivered.status) == (A.CANCELLED, A.DELIVERED)
    assert Enrolment.objects.filter(activity=activity).exists()
