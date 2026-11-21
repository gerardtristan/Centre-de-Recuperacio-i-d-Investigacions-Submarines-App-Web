"""Passar llista i incidències (T-M02-16, part de servei; P-M02-E; RN-M02-17; CA-M02-16 i
CA-M02-17; AC9; C3). Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404
from django.utils import timezone

from apps.activities import attendance, permissions
from apps.activities.models import Activity, Attendance, Enrolment, Incident, Session
from apps.core.models import AppendOnlyError, AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_course, a_person, a_place, an_outing

pytestmark = pytest.mark.django_db
S = Enrolment.Status
R = Role.Code
DAY = datetime.date(2027, 6, 14)  # el dia de la primera sessió i de la sortida
BEFORE = datetime.date(2027, 6, 13)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


def opened(activity, status=Activity.Status.IN_PROGRESS):
    Activity.objects.filter(pk=activity.pk).update(status=status, cancellation_reason="Vent")
    activity.refresh_from_db()
    return activity


def enrolled(activity, first="Alumna", status=S.CONFIRMED):
    return Enrolment.objects.create(
        activity=activity, person=a_person(first), status=status, channel="account",
        price_kind="member", price_cents=4500, created_at=timezone.now(),
    )  # fmt: skip


def a_session(manager, activity, day, *teachers):
    start = timezone.make_aware(datetime.datetime.combine(day, datetime.time(9)))
    session = Session.objects.create(
        activity=activity, kind="pool", starts_at=start,
        ends_at=start + datetime.timedelta(hours=2), place=a_place(manager, prices=None),
    )  # fmt: skip
    session.instructors.set(teachers)
    return session


@pytest.fixture
def course(manager, make_admin):  # noqa: F811
    """Un curs amb dues sessions: la primera la fa `own`; la segona, `other`."""
    own, other = make_admin(R.INSTRUCTOR), make_admin(R.INSTRUCTOR)
    activity = opened(a_course(manager))
    first = a_session(manager, activity, DAY, own.person)
    second = a_session(manager, activity, DAY + datetime.timedelta(days=1), other.person)
    student = enrolled(activity)
    unpaid = enrolled(activity, "Pendent", S.PENDING_PAYMENT)
    return type("Course", (), locals())


def test_the_instructor_sees_only_confirmed_students_with_the_c3_fields(course):
    roll = attendance.roll(course.activity, course.first, viewer=course.own, today=DAY)
    assert roll.can_record and [row.name for row in roll.rows] == ["Alumna Prova"]
    row = roll.rows[0]
    assert (row.present, row.licence_valid, row.certifications) == (None, False, ())
    assert roll.unpaid == ()  # l'instructor no veu qui no ha pagat
    assert set(row.__dataclass_fields__) == {
        "enrolment_id", "name", "certifications", "licence_valid", "present",
    }  # fmt: skip


def test_p_m02_e_4_the_manager_also_sees_who_has_not_paid(course, manager):
    roll = attendance.roll(course.activity, course.first, viewer=manager, today=DAY)
    assert [row.name for row in roll.rows] == ["Alumna Prova"]
    assert [row.name for row in roll.unpaid] == ["Pendent Prova"]
    assert (roll.present, roll.unmarked) == (0, 1)


def test_ca_m02_16_another_instructors_session_is_not_found_and_logged(course):
    for call in (
        lambda: attendance.roll(course.activity, course.second, viewer=course.own, today=DAY),
        lambda: attendance.mark(course.student, course.second, present=True, by=course.own),
        lambda: attendance.add_incident(
            course.activity, session=course.second, by=course.own, kind="delay", description="x"
        ),
    ):
        with pytest.raises(Http404):
            call()
    entries = AuditEntry.objects.filter(action=permissions.OUT_OF_SCOPE)
    assert entries.count() == 3
    assert not Attendance.objects.exists() and not Incident.objects.exists()


def test_without_ac9_not_found(course, make_admin):  # noqa: F811
    with pytest.raises(Http404):
        attendance.roll(course.activity, course.first, viewer=make_admin(R.SECRETARY), today=DAY)


def test_ca_m02_17_the_same_mark_resent_does_not_duplicate(course):
    first = attendance.mark(course.student, course.first, present=True, by=course.own, today=DAY)
    again = attendance.mark(course.student, course.first, present=True, by=course.own, today=DAY)
    assert first.pk == again.pk and Attendance.objects.count() == 1
    assert AuditEntry.objects.filter(action=attendance.MARKED).count() == 1


def test_a_correction_is_logged_with_the_previous_value(course):
    attendance.mark(course.student, course.first, present=True, by=course.own, today=DAY)
    attendance.mark(course.student, course.first, present=False, by=course.own, today=DAY)
    entries = AuditEntry.objects.filter(action=attendance.MARKED).order_by("id")
    assert [(e.old_value, e.new_value) for e in entries] == [(None, True), (True, False)]
    roll = attendance.roll(course.activity, course.first, viewer=course.own, today=DAY)
    assert roll.rows[0].present is False


def test_only_confirmed_enrolments_on_the_day_and_with_a_yes_or_no(course, manager):
    with pytest.raises(ValidationError):  # abans del dia
        attendance.mark(course.student, course.first, present=True, by=course.own, today=BEFORE)
    with pytest.raises(ValidationError):  # pendent de pagament
        attendance.mark(course.unpaid, course.first, present=True, by=manager, today=DAY)
    with pytest.raises(ValidationError):  # cal un sí o un no
        attendance.mark(course.student, course.first, present="sí", by=course.own, today=DAY)
    with pytest.raises(Http404):  # un curs sempre per sessió
        attendance.mark(course.student, None, present=True, by=manager, today=DAY)
    assert not Attendance.objects.exists()


def test_a_cancelled_session_or_activity_has_no_roll(course, manager):
    Session.objects.filter(pk=course.first.pk).update(cancelled=True, cancellation_reason="Vent")
    course.first.refresh_from_db()
    with pytest.raises(ValidationError):
        attendance.mark(course.student, course.first, present=True, by=manager, today=DAY)
    opened(course.activity, Activity.Status.CANCELLED)
    roll = attendance.roll(course.activity, course.second, viewer=manager, today=DAY)
    assert not roll.can_record


def test_an_outing_has_one_mark_for_the_day(manager):
    outing = opened(an_outing(manager), Activity.Status.OPEN)
    row = enrolled(outing)
    attendance.mark(row, present=True, by=manager, today=DAY)
    attendance.mark(row, present=True, by=manager, today=DAY)
    assert Attendance.objects.get().session is None
    with transaction.atomic(), pytest.raises(IntegrityError):  # una sola marca, també a la base
        Attendance.objects.create(
            enrolment=row, present=False, recorded_by=manager, recorded_at=timezone.now()
        )


def test_incidents_are_operational_and_append_only(course):
    incident = attendance.add_incident(
        course.activity, session=course.first, by=course.own, kind="weather",
        description="  Mar arrissada: es fa a la piscina.  ",
    )  # fmt: skip
    assert incident.description == "Mar arrissada: es fa a la piscina."
    entry = AuditEntry.objects.get(action=attendance.INCIDENT_ADDED)
    assert "Mar" not in str(entry.details)  # el registre no repeteix el text
    listed = attendance.incidents(course.activity, course.first, viewer=course.own)
    assert list(listed) == [incident]
    with pytest.raises(AppendOnlyError):
        incident.save()
    with pytest.raises(AppendOnlyError):
        incident.delete()
    for kind, text in (("salut", "x"), ("delay", "  "), ("delay", "x" * 1001)):
        with pytest.raises(ValidationError):
            attendance.add_incident(course.activity, by=course.own, kind=kind, description=text)
    assert "salut" in str(attendance.INCIDENT_HELP)
