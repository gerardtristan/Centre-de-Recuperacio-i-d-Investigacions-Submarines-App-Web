"""Requisits per fer classe (T-M02-30; RN-M02-26; CA-M02-30; VC-46): soci actiu i llicència
tècnica vigent el dia de la sessió. Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.activities import sessions
from apps.activities.models import Session
from apps.core import business_settings
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences.models import Licence, LicenceType, ValidityRule

from .helpers import a_course, a_member, a_place, moment

pytestmark = pytest.mark.django_db
DAY = datetime.date(2027, 6, 14)


def mode(monkeypatch, value):
    real = business_settings.get
    monkeypatch.setattr(
        business_settings, "get",
        lambda key, at=None: value if key == sessions.INSTRUCTOR_MODE_KEY else real(key, at),
    )  # fmt: skip


def licence(person, category, *, expires_on=datetime.date(2027, 12, 31)):
    kind, _ = LicenceType.objects.get_or_create(
        name=f"Tipus inventat {category}", category=category,
        validity_rule=ValidityRule.CALENDAR_YEAR,
    )  # fmt: skip
    return Licence.objects.create(
        person=person, licence_type=kind, validity_rule=kind.validity_rule,
        status=Licence.Status.ACTIVE, origin=Licence.Origin.CLUB,
        starts_on=datetime.date(2027, 1, 1), expires_on=expires_on, price_kind="member",
        price_cents=9000,
    )  # fmt: skip


@pytest.fixture
def setup(make_admin):  # noqa: F811
    manager = make_admin(Role.Code.COURSES_MANAGER)
    member = a_member("Instructora", account=False)
    teacher = make_admin(Role.Code.INSTRUCTOR, person=member)
    return manager, teacher, a_course(manager), a_place(manager)


def add(manager, course, place, teacher, day=DAY):
    y, m, d = day.year, day.month, day.day
    return sessions.add_session(
        course, by=manager, kind=Session.Kind.POOL, starts_at=moment(y, m, d, 9),
        ends_at=moment(y, m, d, 11), place=place, instructors=[teacher.person],
    )  # fmt: skip


def test_ca_m02_30_block_rejects_an_amateur_licence_and_accepts_a_technical_one(setup, monkeypatch):
    manager, teacher, course, place = setup
    mode(monkeypatch, "block")
    licence(teacher.person, LicenceType.Category.AMATEUR)
    with pytest.raises(ValidationError, match="llicència tècnica"):
        add(manager, course, place, teacher)
    assert not Session.objects.exists()
    licence(teacher.person, LicenceType.Category.TECHNICAL)
    session = add(manager, course, place, teacher)
    assert sessions.instructor_warnings(session) == {}


def test_ca_m02_30_warn_assigns_and_marks(setup, monkeypatch):
    manager, teacher, course, place = setup
    mode(monkeypatch, "warn")
    licence(teacher.person, LicenceType.Category.AMATEUR)
    session = add(manager, course, place, teacher)
    assert list(session.instructors.all()) == [teacher.person]
    assert sessions.instructor_warnings(session) == {
        teacher.person.pk: ["no té llicència tècnica vigent"]
    }


def test_block_also_needs_an_active_member_and_applies_to_set_instructors(make_admin, setup,  # noqa: F811
                                                                          monkeypatch):  # fmt: skip
    manager, teacher, course, place = setup
    licence(teacher.person, LicenceType.Category.TECHNICAL)
    session = add(manager, course, place, teacher)
    outsider = make_admin(Role.Code.INSTRUCTOR)  # no és soci
    licence(outsider.person, LicenceType.Category.TECHNICAL)
    mode(monkeypatch, "block")
    with pytest.raises(ValidationError, match="requisits"):
        sessions.set_instructors(session, [outsider.person], by=manager)
    assert sessions.instructor_problems(outsider.person, DAY) == ["no és soci actiu"]


def test_a_session_is_marked_when_the_licence_no_longer_covers_it(setup, monkeypatch):
    manager, teacher, course, place = setup
    mode(monkeypatch, "block")
    licence(teacher.person, LicenceType.Category.TECHNICAL, expires_on=datetime.date(2027, 6, 30))
    later = datetime.date(2027, 6, 14)
    session = add(manager, course, place, teacher, later)
    Licence.objects.filter(person=teacher.person).update(expires_on=datetime.date(2027, 6, 1))
    assert teacher.person.pk in sessions.instructor_warnings(session)
