"""Un instructor deixa de ser-ho: surt de les sessions futures (T-M02-04b; L-M02-05; decisió 101;
RN-RP-12). Portat de la branca aparcada. Només dades inventades."""

from types import SimpleNamespace

import pytest

from apps.accounts.models import Account
from apps.activities import permissions, sessions, states, tasks
from apps.activities.models import Session
from apps.core import roles
from apps.core.models import AccountRole, AuditEntry, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import REASON, a_course, a_place, moment

pytestmark = pytest.mark.django_db
NOW = moment(2027, 6, 1, 9)


def a_session(course, by, day, *instructors, place, year=2027, month=6):
    return sessions.add_session(
        course,
        by=by,
        kind=Session.Kind.SEA,
        starts_at=moment(year, month, day, 9),
        ends_at=moment(year, month, day, 11),
        place=place,
        instructors=[account.person for account in instructors],
    )


@pytest.fixture
def world(make_admin):  # noqa: F811
    """Dos instructors, cadascun amb la seva sessió del mateix curs, i un altre curs on només fa
    classe el segon."""
    admin = make_admin("administrator")
    i1, i2 = make_admin("instructor"), make_admin("instructor")
    place = a_place(admin)
    course = a_course(admin)
    other = a_course(admin, title="Un altre curs inventat")
    return SimpleNamespace(
        admin=admin, i1=i1, i2=i2, course=course, other=other, place=place,
        s1=a_session(course, admin, 14, i1, place=place),
        s2=a_session(course, admin, 15, i2, place=place),
        s3=a_session(other, admin, 14, i2, place=place),
    )  # fmt: skip


def released():
    return AuditEntry.objects.filter(action=sessions.INSTRUCTOR_RELEASED).order_by("pk")


def instructors_of(session):
    return set(Session.objects.get(pk=session.pk).instructors.values_list("pk", flat=True))


def test_l_m02_05_removing_the_role_frees_their_future_sessions(world):
    shared = a_session(world.course, world.admin, 16, world.i1, world.i2, place=world.place)
    assert not sessions.sessions_without_instructor(NOW).exists()

    roles.remove_role(world.i2, "instructor", by=world.admin, note="Plega (inventat).")

    assert instructors_of(world.s2) == instructors_of(world.s3) == set()
    assert instructors_of(shared) == {world.i1.person.pk}  # l'altre instructor s'hi queda
    assert instructors_of(world.s1) == {world.i1.person.pk}
    assert set(sessions.sessions_without_instructor(NOW)) == {world.s2, world.s3}
    entries = list(released())
    assert {e.target_id for e in entries} == {str(world.s2.pk), str(world.s3.pk), str(shared.pk)}
    assert all(e.actor_account == world.admin and e.reason for e in entries)
    by_session = {e.target_id: (e.old_value, e.new_value) for e in entries}
    assert by_session[str(world.s2.pk)] == ([world.i2.person.pk], [])
    assert not permissions.can(world.i2, permissions.ATTENDANCE, world.s2)


def test_l_m02_05_removing_another_role_changes_nothing(world, make_admin):  # noqa: F811
    both = make_admin("secretary", "instructor")
    session = a_session(world.course, world.admin, 16, both, place=world.place)
    roles.remove_role(both, "secretary", by=world.admin, note="Canvi (inventat).")
    assert instructors_of(session) == {both.person.pk}
    assert not released().exists()


def test_l_m02_05_nobody_comes_back_alone(world):
    roles.remove_role(world.i2, "instructor", by=world.admin, note="Plega (inventat).")
    roles.assign_role(world.i2, "instructor", by=world.admin, note="Torna (inventat).")
    assert instructors_of(world.s2) == set()
    sessions.set_instructors(world.s2, [world.i2.person], by=world.admin)
    assert instructors_of(world.s2) == {world.i2.person.pk}


def test_l_m02_05_the_queue_covers_disabled_accounts_and_anonymised_people(world):
    Account.objects.filter(pk=world.i1.pk).update(status=Account.Status.DISABLED)
    Person.objects.filter(pk=world.i2.person.pk).update(
        status=Person.Status.ANONYMISED, anonymous_ref="A-9002"
    )
    changed = sessions.release_former_instructors(now=NOW)
    assert changed == sorted([world.s1.pk, world.s2.pk, world.s3.pk])
    assert all(instructors_of(s) == set() for s in (world.s1, world.s2, world.s3))
    assert {(e.actor_kind, e.actor_origin) for e in released()} == {
        ("system", sessions.RELEASE_ORIGIN)
    }
    assert sessions.release_former_instructors(now=NOW) == []  # idempotent
    assert released().count() == 3


def test_l_m02_05_cancelled_finished_and_past_sessions_are_left_alone(world):
    sessions.cancel_session(world.s2, by=world.admin, reason=REASON)
    states.cancel(world.other, by=world.admin, reason=REASON)
    AccountRole.objects.filter(admin_account=world.i2).update(removed_at=NOW)
    assert sessions.release_former_instructors(now=NOW) == []
    assert instructors_of(world.s2) == instructors_of(world.s3) == {world.i2.person.pk}
    assert sessions.release_former_instructors(now=moment(2027, 6, 15, 10)) == []  # ja començada


def test_the_queue_task_calls_the_service(monkeypatch):
    seen = []
    monkeypatch.setattr(sessions, "release_former_instructors", lambda: seen.append(1) or [])
    tasks.release_former_instructors(timestamp=0)
    assert seen == [1]
