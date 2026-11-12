"""Permisos per objecte: «les seves sessions» (T-M02-04; RN-43 de la 00; RN-RP-04; CA-M02-16 i la
part de CA-M02-35 de «tret que faci classe a la sessió») i el cas L-M02-05 (decisió 086).

Les pantalles que faran servir aquestes comprovacions (passar llista, avaluar) són de la T-M02-16
i la T-M02-17. Només dades inventades.
"""

from types import SimpleNamespace

import pytest
from django.http import Http404

from apps.accounts.models import Account
from apps.activities import permissions, sessions, states, tasks
from apps.activities.models import Activity, Session
from apps.core import audit, roles
from apps.core.models import AccountRole, AuditEntry, Person
from apps.core.permissions import has_perm
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from conftest import PASSWORD

from .helpers import REASON, a_course, a_person, at

pytestmark = pytest.mark.django_db

OWN_SESSIONS = [  # tots els permisos que l'instructor té amb l'abast «les seves sessions»
    permissions.PARTICIPANTS,
    permissions.ATTENDANCE,
    permissions.ASSESSMENT,
    permissions.REINFORCEMENT_PROPOSE,
    permissions.OUTCOME,
    permissions.REPORTS,
    permissions.STUDENT_FIELDS,
]
ONLY_WHO_TEACHES = [  # RN-RP-04: cap rol els té amb un abast més ampli
    permissions.ASSESSMENT,
    permissions.REINFORCEMENT_PROPOSE,
    permissions.OUTCOME,
]
NOW = at(2027, 6, 1, 9)


def a_session(course, by, day, *instructors, hour=9):
    return sessions.add_session(
        course,
        by=by,
        kind=Session.Kind.SEA,
        starts_at=at(2027, 6, day, hour),
        ends_at=at(2027, 6, day, hour + 2),
        instructors=[account.person for account in instructors],
    )


@pytest.fixture
def world(make_admin):  # noqa: F811
    """Dos instructors, I1 i I2, cadascun amb la seva sessió del mateix curs, i un altre curs
    on només fa classe I2."""
    admin = make_admin("administrator")
    i1, i2 = make_admin("instructor"), make_admin("instructor")
    course = a_course(admin)
    other_course = a_course(admin, title="Un altre curs inventat")
    return SimpleNamespace(
        admin=admin,
        i1=i1,
        i2=i2,
        course=course,
        other_course=other_course,
        s1=a_session(course, admin, 14, i1),
        s2=a_session(course, admin, 15, i2),
        s3=a_session(other_course, admin, 14, i2),
    )


def attempts():
    return AuditEntry.objects.filter(action=permissions.OUT_OF_SCOPE)


# --- CA-M02-16 ------------------------------------------------------------------------------------


def test_ca_m02_16_the_session_of_another_instructor_is_not_found_and_recorded(world):
    """CA-M02-16: I1 fa classe a S1. Amb S2, d'un altre instructor, «no trobat» i l'intent queda
    al registre."""
    permissions.require(world.i1, permissions.ATTENDANCE, world.s1)
    assert not attempts().exists()
    with pytest.raises(Http404):
        permissions.require(world.i1, permissions.ATTENDANCE, world.s2)
    (attempt,) = attempts()
    assert attempt.actor_account == world.i1
    assert (attempt.target_type, attempt.target_id) == ("activities.session", str(world.s2.pk))
    assert attempt.details == {"permission": permissions.ATTENDANCE}


@pytest.mark.parametrize("code", OWN_SESSIONS)
def test_every_own_sessions_permission_reaches_only_their_sessions(world, code):
    assert has_perm(world.i1, code)  # el permís hi és
    assert has_perm(world.i1, code, world.s1)
    assert not has_perm(world.i1, code, world.s2)
    assert not has_perm(world.i1, code, world.s3)
    assert has_perm(world.i2, code, world.s2)
    assert not has_perm(world.i2, code, world.s1)


def test_an_activity_is_theirs_if_they_teach_one_of_its_live_sessions(world):
    code = permissions.PARTICIPANTS
    assert permissions.can(world.i1, code, world.course, write=False)
    assert not permissions.can(world.i1, code, world.other_course, write=False)
    assert permissions.can(world.i2, code, world.other_course, write=False)
    # Una sessió cancel·lada ja no fa que l'activitat sigui seva.
    sessions.cancel_session(world.s1, by=world.admin, reason=REASON)
    assert not permissions.can(world.i1, code, world.course, write=False)


def test_any_other_object_is_out_of_scope(world):
    assert not permissions.can(world.i1, permissions.ATTENDANCE, world.i1.person)
    assert not permissions.teaches(world.i1, object())
    assert not permissions.teaches(None, world.s1)


def test_without_the_permission_it_is_not_found_and_nothing_is_recorded(world, make_admin):  # noqa: F811
    """Qui no té el permís rep «no trobat» igual; l'intent que es registra és el de qui el té i
    prova un objecte que no és seu."""
    secretary = make_admin("secretary")
    with pytest.raises(Http404):
        permissions.require(secretary, permissions.ATTENDANCE, world.s1)
    for by in (None, audit.system("activities.proves")):
        with pytest.raises(Http404):
            permissions.require(by, permissions.ATTENDANCE, world.s1)
    assert not attempts().exists()


def test_the_personal_account_of_the_instructor_reaches_nothing(world):
    personal = Account.objects.create_personal(world.i1.person, "i1@example.org", PASSWORD)
    personal.status = Account.Status.ACTIVE
    personal.save()
    assert not permissions.can(personal, permissions.ATTENDANCE, world.s1)
    with pytest.raises(Http404):
        permissions.require(personal, permissions.ATTENDANCE, world.s1)


# --- Qui té l'abast «tot» o «consulta» ------------------------------------------------------------


def test_whoever_manages_activities_reaches_every_session(world, make_admin):  # noqa: F811
    manager = make_admin("courses_manager")
    for session in (world.s1, world.s2, world.s3):
        permissions.require(manager, permissions.ATTENDANCE, session)
        permissions.require(manager, permissions.PARTICIPANTS, session)
    assert not attempts().exists()


def test_a_read_only_scope_sees_every_session_but_changes_none(world, make_admin):  # noqa: F811
    equipment = make_admin("equipment_manager")  # AC8 «Cons.», per assignar material
    assert permissions.can(equipment, permissions.PARTICIPANTS, world.s1, write=False)
    assert not permissions.can(equipment, permissions.PARTICIPANTS, world.s1)
    assert not permissions.can(equipment, permissions.ATTENDANCE, world.s1, write=False)


# --- RN-RP-04 i CA-M02-35: avaluar, només qui fa classe a la sessió -------------------------------


@pytest.mark.parametrize("code", ONLY_WHO_TEACHES)
@pytest.mark.parametrize("role", ["courses_manager", "treasurer", "administrator", "president"])
def test_rn_rp_04_no_managing_role_assesses_by_itself(world, make_admin, role, code):  # noqa: F811
    account = make_admin(role)
    assert not permissions.can(account, code, world.s1, write=False)
    with pytest.raises(Http404):
        permissions.require(account, code, world.s1)


def test_ca_m02_35_the_treasurer_calls_the_roll_only_where_they_teach(world, make_admin):  # noqa: F811
    """CA-M02-35: el tresorer no passa llista ni avalua, «tret que faci classe a la sessió». Fa
    classe qui també té el rol d'instructor i surt a la sessió."""
    both = make_admin("treasurer", "instructor")
    own = a_session(world.course, world.admin, 16, both)
    for code in (permissions.ATTENDANCE, *ONLY_WHO_TEACHES):
        permissions.require(both, code, own)
        with pytest.raises(Http404):
            permissions.require(both, code, world.s1)
    assert attempts().count() == 1 + len(ONLY_WHO_TEACHES)


def test_the_widest_scope_wins_when_someone_has_two_roles(world, make_admin):  # noqa: F811
    # RN-RP-02: responsable de cursos (tot) i instructor (les seves) → passa llista a totes.
    both = make_admin("courses_manager", "instructor")
    permissions.require(both, permissions.ATTENDANCE, world.s1)
    # Però avaluar continua sent només on fa classe.
    with pytest.raises(Http404):
        permissions.require(both, permissions.ASSESSMENT, world.s1)


# --- Llistes --------------------------------------------------------------------------------------


def test_sessions_for_lists_only_what_the_account_reaches(world, make_admin):  # noqa: F811
    code = permissions.ATTENDANCE
    assert set(permissions.sessions_for(world.i1, code)) == {world.s1}
    assert set(permissions.sessions_for(world.i2, code)) == {world.s2, world.s3}
    assert set(permissions.sessions_for(make_admin("courses_manager"), code)) == {
        world.s1,
        world.s2,
        world.s3,
    }
    assert not permissions.sessions_for(make_admin("treasurer"), code).exists()
    assert not permissions.sessions_for(None, code).exists()
    equipment = make_admin("equipment_manager")
    assert not permissions.sessions_for(equipment, permissions.PARTICIPANTS).exists()
    assert permissions.sessions_for(equipment, permissions.PARTICIPANTS, write=False).count() == 3


# --- L-M02-05 (decisió 086): un instructor deixa de tenir el rol ----------------------------------


def released():
    return AuditEntry.objects.filter(action=sessions.INSTRUCTOR_RELEASED).order_by("pk")


def instructors_of(session):
    return set(Session.objects.get(pk=session.pk).instructors.values_list("pk", flat=True))


def test_l_m02_05_removing_the_role_frees_their_future_sessions(world):
    """L-M02-05: les sessions futures de qui perd el rol queden sense instructor i es poden
    llistar. Les passades conserven qui hi va fer classe. Al registre hi surt qui ha retirat el
    rol."""
    past = sessions.add_session(
        world.course,
        by=world.admin,
        kind=Session.Kind.THEORY,
        starts_at=at(2020, 1, 10, 9),
        ends_at=at(2020, 1, 10, 11),
        instructors=[world.i2.person],
    )
    shared = a_session(world.course, world.admin, 16, world.i1, world.i2)
    assert not sessions.sessions_without_instructor(NOW).exists()

    roles.remove_role(world.i2, "instructor", by=world.admin)

    assert instructors_of(world.s2) == set()
    assert instructors_of(world.s3) == set()
    assert instructors_of(shared) == {world.i1.person.pk}  # l'altre instructor s'hi queda
    assert instructors_of(world.s1) == {world.i1.person.pk}
    assert instructors_of(past) == {world.i2.person.pk}  # el passat no es toca
    assert set(sessions.sessions_without_instructor(NOW)) == {world.s2, world.s3}
    entries = list(released())
    assert {e.target_id for e in entries} == {str(world.s2.pk), str(world.s3.pk), str(shared.pk)}
    assert all(e.actor_account == world.admin and e.reason for e in entries)
    by_session = {e.target_id: (e.old_value, e.new_value) for e in entries}
    assert by_session[str(world.s2.pk)] == ([world.i2.person.pk], [])
    # I ja no hi arriba amb cap permís.
    assert not permissions.can(world.i2, permissions.ATTENDANCE, world.s2)


def test_l_m02_05_removing_another_role_changes_nothing(world, make_admin):  # noqa: F811
    both = make_admin("secretary", "instructor")
    session = a_session(world.course, world.admin, 16, both)
    roles.remove_role(both, "secretary", by=world.admin)
    assert instructors_of(session) == {both.person.pk}
    assert not released().exists()


def test_l_m02_05_nobody_comes_back_alone(world):
    roles.remove_role(world.i2, "instructor", by=world.admin)
    roles.assign_role(world.i2, "instructor", by=world.admin)
    assert instructors_of(world.s2) == set()
    sessions.set_instructors(world.s2, [world.i2.person], by=world.admin)
    assert instructors_of(world.s2) == {world.i2.person.pk}


def test_l_m02_05_the_queue_covers_disabled_accounts_and_anonymised_people(world):
    Account.objects.filter(pk=world.i1.pk).update(status=Account.Status.DISABLED)
    Person.objects.filter(pk=world.i2.person.pk).update(
        status=Person.Status.ANONYMISED, anonymous_ref="anonima-de-proves-2"
    )
    changed = sessions.release_former_instructors(now=NOW)
    assert changed == sorted([world.s1.pk, world.s2.pk, world.s3.pk])
    assert all(instructors_of(s) == set() for s in (world.s1, world.s2, world.s3))
    assert {(e.actor_kind, e.actor_origin) for e in released()} == {
        ("system", sessions.RELEASE_ORIGIN)
    }
    # Es pot cridar tantes vegades com calgui.
    assert sessions.release_former_instructors(now=NOW) == []
    assert released().count() == 3


def test_l_m02_05_finished_cancelled_and_past_sessions_are_left_alone(world):
    sessions.cancel_session(world.s2, by=world.admin, reason=REASON)
    states.cancel(world.other_course, by=world.admin, reason=REASON)
    AccountRole.objects.filter(admin_account=world.i2).update(removed_at=NOW)
    assert sessions.release_former_instructors(now=NOW) == []
    assert instructors_of(world.s2) == instructors_of(world.s3) == {world.i2.person.pk}
    # Una sessió que ja ha començat tampoc.
    assert sessions.release_former_instructors(now=at(2027, 6, 15, 10)) == []
    assert not sessions.sessions_without_instructor(NOW).filter(pk=world.s2.pk).exists()


def test_l_m02_05_a_session_that_never_had_an_instructor_is_listed_too(world):
    bare = a_session(world.course, world.admin, 17)
    assert list(sessions.sessions_without_instructor(NOW)) == [bare]
    assert not sessions.sessions_without_instructor(at(2027, 7, 1)).exists()
    Activity.objects.filter(pk=world.course.pk).update(status="done")
    assert not sessions.sessions_without_instructor(NOW).exists()


def test_l_m02_05_the_queue_runs_it_every_ten_minutes(world):
    name = "activities.release_former_instructors"
    periodic = tasks.app.periodic_registry.periodic_tasks[(name, "")]
    assert periodic.cron == "5-59/10 * * * *"
    Account.objects.filter(pk=world.i1.pk).update(status=Account.Status.DISABLED)
    tasks.release_former_instructors(timestamp=0)
    assert instructors_of(world.s1) == set()


def test_someone_without_a_person_teaches_nothing(world):
    assert a_person("Sense compte").taught_sessions.count() == 0
    assert not permissions.teaches(object(), world.s1)
