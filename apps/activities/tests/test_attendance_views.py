"""Pantalles de passar llista i incidències (T-M02-16b; P-M02-E; CA-M02-16 i 17; AC9). Només dades
inventades."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.activities import attendance, permissions
from apps.activities.models import Attendance, Incident
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import a_course
from .test_attendance import a_session, enrolled, manager, opened  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
R = Role.Code
LIST = reverse("administration:attendance_sessions")


@pytest.fixture
def today_course(manager, make_admin):  # noqa: F811
    """Un curs amb una sessió avui (de `own`) i una demà (de `other`)."""
    own, other = make_admin(R.INSTRUCTOR), make_admin(R.INSTRUCTOR)
    today = timezone.localdate()
    activity = opened(a_course(manager))
    first = a_session(manager, activity, today, own.person)
    second = a_session(manager, activity, today + datetime.timedelta(days=1), other.person)
    student = enrolled(activity)
    return type("Course", (), locals())


def roll_url(course, session):
    return reverse("administration:attendance_roll_session", args=[course.activity.pk, session.pk])


def test_the_instructor_only_lists_and_opens_their_sessions(login_as, today_course):
    client = login_as(today_course.own, AREA_ADMIN)
    html = main_of(client.get(LIST).content.decode())
    assert roll_url(today_course, today_course.first) in html
    assert roll_url(today_course, today_course.second) not in html
    page = main_of(client.get(roll_url(today_course, today_course.first)).content.decode())
    assert "Alumna Prova" in page and "Sense marcar" in page and "Hi és" in page
    # CA-M02-16: la d'un altre instructor, «no trobat» i al registre.
    assert client.get(roll_url(today_course, today_course.second)).status_code == 404
    assert AuditEntry.objects.filter(action=permissions.OUT_OF_SCOPE).count() == 1


def test_ca_m02_17_a_resent_mark_is_saved_once(login_as, today_course):
    client = login_as(today_course.own, AREA_ADMIN)
    url = roll_url(today_course, today_course.first)
    data = {"inscripcio": today_course.student.pk, "present": "1"}
    for _ in range(2):  # el mòbil la reenvia en tornar la cobertura
        response = client.post(url, data, HTTP_ACCEPT="application/json")
        assert (response.status_code, response.json()) == (200, {"present": True})
    assert Attendance.objects.get().present is True
    assert AuditEntry.objects.filter(action=attendance.MARKED).count() == 1
    # Sense JavaScript: el formulari normal torna a la llista.
    response = client.post(url, {**data, "present": "0"})
    assert response.status_code == 303 and Attendance.objects.get().present is False


def test_incidents_operational_only_and_validated(login_as, today_course):
    client = login_as(today_course.own, AREA_ADMIN)
    url = roll_url(today_course, today_course.first)
    page = main_of(client.get(url).content.decode())
    assert "Sense dades de salut" in page
    response = client.post(url, {"classe": "delay", "descripcio": ""}, follow=True)
    assert "Cal descriure la incidència." in response.content.decode()
    client.post(url, {"classe": "boat", "descripcio": "L'embarcació surt 20 minuts tard."})
    incident = Incident.objects.get()
    assert (incident.kind, incident.session) == ("boat", today_course.first)
    assert "20 minuts tard" in main_of(client.get(url).content.decode())


def test_without_ac9_not_found(login_as, today_course, make_admin):  # noqa: F811
    client = login_as(make_admin(R.SECRETARY), AREA_ADMIN)
    assert client.get(LIST).status_code == 404
    assert client.get(roll_url(today_course, today_course.first)).status_code == 404


def test_the_manager_sees_who_has_not_paid(login_as, today_course, manager):  # noqa: F811
    enrolled(today_course.activity, "Pendent", "pending_payment")
    page = main_of(
        login_as(manager, AREA_ADMIN)
        .get(roll_url(today_course, today_course.first))
        .content.decode()
    )
    assert "Pendents de pagament" in page and "Pendent Prova" in page
