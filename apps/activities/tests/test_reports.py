"""Informes operatius (T-M02-24; AC20, AC19 i C3). Proves de permisos i de contingut. Només dades
inventades."""

import codecs
import datetime

import pytest
from django.http import Http404

from apps.activities import enrolment, reports, sessions
from apps.activities.models import Enrolment, Session
from apps.core.models import Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, a_member, a_place, an_open_course, an_open_outing, moment

pytestmark = pytest.mark.django_db


def enrol(activity, first):
    account = a_member(first)
    return enrolment.enrol(activity, account.person, channel="account", actor=account,
                           now=BEFORE_DEADLINE)  # fmt: skip


@pytest.fixture
def world(make_admin):  # noqa: F811
    manager = make_admin(Role.Code.COURSES_MANAGER)
    teacher, stranger = make_admin("instructor"), make_admin("instructor")
    course = an_open_course(manager, max_places=1)
    sessions.add_session(
        course, by=manager, kind=Session.Kind.POOL, starts_at=moment(2027, 6, 14, 9),
        ends_at=moment(2027, 6, 14, 11), place=a_place(manager), instructors=[teacher.person],
    )  # fmt: skip
    paid = enrol(course, "Alumna")
    Enrolment.objects.filter(pk=paid.pk).update(status=Enrolment.Status.CONFIRMED)
    Person.objects.filter(pk=paid.person_id).update(
        contact_email="alumna@example.org", phone="600000000"
    )
    waiting = enrol(course, "Espera")
    return type("World", (), dict(manager=manager, teacher=teacher, stranger=stranger,
                                  course=course, paid=paid, waiting=waiting))  # fmt: skip


def test_the_instructor_sees_only_confirmed_names_certifications_and_licence(world):
    headers, rows = reports.participants_report(world.course, viewer=world.teacher)
    assert headers == ["Nom", "Titulacions", "Llicència vigent"]
    assert rows == [["Alumna Prova", "", "No"]]


def test_other_roles_see_status_and_waiting_list_and_the_price_only_with_ac19(world, make_admin):  # noqa: F811
    board = make_admin(Role.Code.BOARD)  # AC20 de consulta, sense AC19
    headers, rows = reports.participants_report(world.course, viewer=board)
    assert "Preu (cèntims)" not in headers
    assert [r[:3] for r in rows] == [
        ["Alumna Prova", "Confirmada", ""],
        ["Espera Prova", "En llista d'espera", 1],
    ]
    for viewer in (world.manager, make_admin(Role.Code.TREASURER)):  # AC19 (S-M02-18)
        headers, rows = reports.participants_report(world.course, viewer=viewer)
        assert headers[-2:] == ["Preu (cèntims)", "Tipus de preu"] and rows[0][-2] == 4500


def test_no_contact_data_in_any_csv(world):
    content = reports.participants_csv(world.course, viewer=world.manager)
    assert content.startswith(codecs.BOM_UTF8)
    for private in (b"alumna@example.org", b"600000000"):
        assert private not in content


def test_ac20_and_the_scope_are_checked(world, make_admin):  # noqa: F811
    for viewer in (world.stranger, make_admin("secretary")):
        with pytest.raises(Http404):
            reports.participants_report(world.course, viewer=viewer)
    with pytest.raises(Http404):
        reports.schedule(world.course, viewer=world.stranger)
    with pytest.raises(Http404):
        reports.occupancy(viewer=make_admin("secretary"))


def test_occupancy_counts_and_scope(world):
    outing = an_open_outing(world.manager, max_places=4)
    rows = {r.activity: r for r in reports.occupancy(viewer=world.manager)}
    assert (rows[world.course].occupied, rows[world.course].free, rows[world.course].waiting,
            rows[world.course].percent) == (1, 0, 1, 100)  # fmt: skip
    assert rows[outing].free == 4
    assert [r.activity for r in reports.occupancy(viewer=world.teacher)] == [world.course]
    csv = reports.occupancy_csv(viewer=world.manager).decode("utf-8-sig")
    assert csv.splitlines()[0].startswith("Activitat;Data d'inici")


def test_the_schedule_has_times_and_places_but_no_names(world):
    data = reports.schedule(world.course, viewer=world.teacher)
    (session,) = data["sessions"]
    assert session["place"] and session["starts_at"].date() == datetime.date(2027, 6, 14)
    assert "Prova" not in str(data) and data["blocks"] == []
