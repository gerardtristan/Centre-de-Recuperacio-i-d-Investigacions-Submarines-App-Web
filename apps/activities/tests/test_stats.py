"""Recomptes d'activitat per al dashboard (T-M08-04; RP-M08-01; RN-M08-10; RN-M02-07): prova de
contracte. Només dades inventades."""

import dataclasses
import datetime

import pytest
from django.utils import timezone

from apps.activities import stats
from apps.activities.models import Activity, Attendance, Enrolment, Session
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_person, a_place, outing_data

pytestmark = pytest.mark.django_db
A, E = Activity.Status, Enrolment.Status
JUNE, JUNE_END = datetime.date(2027, 6, 1), datetime.date(2027, 6, 30)
NOW = timezone.make_aware(datetime.datetime(2027, 6, 20, 12))


def moment(day, hour=10):
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time(hour)))


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.fixture
def place(manager):
    return a_place(manager, prices=None)


def activity(place, day, places=10, status=A.OPEN, kind=Activity.Kind.OUTING):
    data = outing_data(place, starts_on=day, ends_on=day, max_places=places, status=status)
    if kind == Activity.Kind.COURSE:
        data.update(kind=kind, outing_type=None)
    return Activity.objects.create(**data)


def enrol(target, status=E.CONFIRMED, made=None, first="Inscrita"):
    return Enrolment.objects.create(
        activity=target, person=a_person(first), status=status, channel="account",
        price_kind="member", price_cents=4500, created_at=made or moment(JUNE),
    )  # fmt: skip


def present(manager, enrolment, session=None, yes=True):
    Attendance.objects.create(
        enrolment=enrolment, session=session, present=yes, recorded_by=manager, recorded_at=NOW
    )


def test_occupancy_counts_confirmed_over_the_places_of_the_period(place):
    june = activity(place, datetime.date(2027, 6, 14), places=10)
    other = activity(place, datetime.date(2027, 6, 21), places=6, status=A.REGISTRATION_CLOSED)
    for status in (E.CONFIRMED, E.CONFIRMED, E.PENDING_PAYMENT, E.WAITLISTED, E.CANCELLED):
        enrol(june, status)
    enrol(other)
    activity(place, datetime.date(2027, 6, 15), places=50, status=A.DRAFT)
    activity(place, datetime.date(2027, 6, 16), places=50, status=A.CANCELLED)
    enrol(activity(place, datetime.date(2027, 7, 1), places=50))  # fora del període
    result = stats.stats(JUNE, JUNE_END, now=NOW)
    assert (result.places, result.confirmed, result.occupancy_percent) == (16, 3, 19)


def test_free_places_are_of_open_upcoming_activities_minus_occupying(place):
    soon = activity(place, datetime.date(2027, 6, 25), places=5)
    for status in (E.CONFIRMED, E.PENDING_PAYMENT, E.OFFERED, E.WAITLISTED, E.EXPIRED):
        enrol(soon, status)
    full = activity(place, datetime.date(2027, 6, 26), places=1)
    enrol(full)
    enrol(full)  # més ocupades que places: compta 0, no -1
    activity(place, datetime.date(2027, 6, 27), places=9, status=A.REGISTRATION_CLOSED)
    activity(place, datetime.date(2027, 6, 20), places=9)  # comença avui
    assert stats.stats(JUNE, JUNE_END, now=NOW).free_places == 2


def test_attendance_of_done_course_sessions_and_finished_outings(manager, place):
    course = activity(place, datetime.date(2027, 6, 14), kind=Activity.Kind.COURSE)
    done = Session.objects.create(
        activity=course, kind="pool", starts_at=moment(datetime.date(2027, 6, 14)),
        ends_at=moment(datetime.date(2027, 6, 14), 12), place=place,
    )  # fmt: skip
    later = Session.objects.create(
        activity=course, kind="pool", starts_at=moment(datetime.date(2027, 6, 28)),
        ends_at=moment(datetime.date(2027, 6, 28), 12), place=place,
    )  # fmt: skip
    a, b = enrol(course), enrol(course)
    enrol(course, E.PENDING_PAYMENT)
    present(manager, a, done)
    present(manager, b, done, yes=False)
    present(manager, a, later)  # la sessió encara no s'ha fet
    outing = activity(place, datetime.date(2027, 6, 10))
    c, _ = enrol(outing), enrol(outing)
    present(manager, c)
    activity(place, datetime.date(2027, 6, 22))  # sortida que encara no s'ha fet
    result = stats.stats(JUNE, JUNE_END, now=NOW)
    assert (result.attended, result.expected, result.attendance_percent) == (2, 4, 50)


def test_weekly_enrolments_cover_every_week_of_the_period(place):
    target = activity(place, datetime.date(2027, 7, 5))
    enrol(target, made=moment(datetime.date(2027, 6, 2)))  # dimecres de la setmana del 31/5
    enrol(target, made=moment(datetime.date(2027, 6, 9)))
    enrol(target, made=moment(datetime.date(2027, 6, 10)))
    enrol(target, E.CANCELLED, made=moment(datetime.date(2027, 6, 10)))
    enrol(target, made=moment(datetime.date(2027, 5, 31)))  # fora del període
    weekly = stats.stats(JUNE, JUNE_END, now=NOW).weekly
    assert weekly == {
        datetime.date(2027, 5, 31): 1, datetime.date(2027, 6, 7): 2,
        datetime.date(2027, 6, 14): 0, datetime.date(2027, 6, 21): 0,
        datetime.date(2027, 6, 28): 0,
    }  # fmt: skip


def test_empty_period_has_no_percentages():
    result = stats.stats(JUNE, JUNE_END, now=NOW)
    assert (result.occupancy_percent, result.attendance_percent, result.free_places) == (
        None, None, 0,
    )  # fmt: skip


def test_contract_only_counts_no_personal_data(place):
    """RP-M08-01 i RN-M08-01: la sortida només té recomptes, cap nom ni identificador."""
    enrol(activity(place, datetime.date(2027, 6, 14)), first="Nom-Que-No-Surt")
    result = stats.stats(JUNE, JUNE_END, now=NOW)
    values = [getattr(result, f.name) for f in dataclasses.fields(result)]
    assert all(isinstance(v, int) for v in values if not isinstance(v, dict))
    assert all(isinstance(k, datetime.date) and isinstance(v, int)
               for k, v in result.weekly.items())  # fmt: skip
    assert "Nom-Que-No-Surt" not in repr(result) and "Prova" not in repr(result)
