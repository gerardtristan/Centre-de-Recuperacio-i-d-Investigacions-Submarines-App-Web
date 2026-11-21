"""Comprovacions de tancament, `attendance_for` i participants per al 09 (T-M02-22, part de
servei; P-M02-H; RN-M02-22; CA-M02-23; M02-8). Només dades inventades.
"""

import datetime

import pytest

from apps.activities import attendance, closing, extensions, states
from apps.activities.models import Activity, Enrolment, RefundProposal
from apps.core import charges
from apps.core.models import AuditEntry, Charge, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_course, a_person, an_outing
from .test_attendance import DAY, a_session, enrolled, opened

pytestmark = pytest.mark.django_db
S = Enrolment.Status
A = Activity.Status


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.fixture
def done(manager):
    outing = opened(an_outing(manager), A.DONE)
    enrolled(outing)
    return outing


def test_ca_m02_23_a_pending_enrolment_blocks_closing(done, manager):
    enrolled(done, "Pendent", S.PENDING_PAYMENT)
    enrolled(done, "Oferta", S.OFFERED)
    reasons = closing.closing_blockers(done)
    assert reasons == [
        "Hi ha 1 inscripció pendent de pagament.",
        "Hi ha 1 plaça oferta sense resposta.",
    ]
    assert "Pendent" not in " ".join(reasons)  # cap dada personal
    with pytest.raises(closing.ClosingBlocked) as error:
        closing.mark_closed(done, actor=manager)
    assert error.value.reasons == reasons
    done.refresh_from_db()
    assert done.status == A.DONE


def test_other_modules_add_their_reasons(done):
    def check(activity):
        return ["Material pendent de tornar (mòdul fals)."]

    extensions.register_closing_check(check)
    try:
        assert closing.closing_blockers(done) == ["Material pendent de tornar (mòdul fals)."]
    finally:
        extensions._closing_checks.remove(check)


def test_only_a_done_activity_is_closed_and_it_is_logged(done, manager):
    with pytest.raises(states.InvalidTransition):
        closing.mark_closed(opened(an_outing(manager), A.OPEN), actor=manager)
    closing.mark_closed(done, actor=manager)
    assert done.status == A.CLOSED
    entry = AuditEntry.objects.get(action=states.STATUS_CHANGED, target_id=str(done.pk))
    assert (entry.old_value, entry.new_value) == (A.DONE, A.CLOSED)


def test_attendance_for_lists_only_the_days_the_person_was_there(manager):
    outing = opened(an_outing(manager), A.OPEN)
    mine, other = enrolled(outing), enrolled(outing, "Altra")
    attendance.mark(mine, present=True, by=manager, today=DAY)
    attendance.mark(other, present=False, by=manager, today=DAY)
    assert attendance.attendance_for(mine.person) == [{"activity": outing, "dates": [DAY]}]
    assert attendance.attendance_for(other.person) == []
    assert attendance.attendance_for(a_person("Ningú")) == []


def test_participants_are_attendees_or_else_confirmed(manager):
    outing = opened(an_outing(manager), A.OPEN)
    first, second = enrolled(outing), enrolled(outing, "Segona")
    enrolled(outing, "Pendent", S.PENDING_PAYMENT)
    assert attendance.participants(outing) == 2  # sense llista: les confirmades
    attendance.mark(first, present=True, by=manager, today=DAY)
    attendance.mark(second, present=False, by=manager, today=DAY)
    assert attendance.participants(outing) == 1


def test_a_course_counts_each_attendee_once(manager, make_admin):  # noqa: F811
    course = opened(a_course(manager))
    sessions = [a_session(manager, course, DAY + datetime.timedelta(days=d)) for d in (0, 1)]
    student = enrolled(course)
    later = DAY + datetime.timedelta(days=1)
    for session in sessions:
        attendance.mark(student, session, present=True, by=manager, today=later)
    assert attendance.participants(course) == 1
    assert attendance.attendance_for(student.person)[0]["dates"] == [DAY, later]


def test_rn_m02_22_an_open_refund_proposal_blocks_closing(done, manager):
    row = enrolled(done, "Cancel·lada")
    Enrolment.objects.filter(pk=row.pk).update(status=S.CANCELLED, cancelled_reason="No pot venir.")
    charge = charges.create_charge(
        row.person, kind=Charge.Kind.ENROLMENT, amount_cents=4500, concept="Sortida inventada",
        origin="activities", by=manager, department=done.department,
    )  # fmt: skip
    proposal = RefundProposal.objects.create(
        enrolment=row, charge=charge, amount_cents=4500, reason="Motiu inventat."
    )
    assert closing.closing_blockers(done) == ["Hi ha 1 proposta de devolució sense fer."]
    RefundProposal.objects.filter(pk=proposal.pk).update(
        status=RefundProposal.Status.REJECTED, decided_by=manager
    )
    assert closing.closing_blockers(done) == []
