"""Permisos per objecte del 02 (T-M02-04a; RN-43 de la 00; RN-RP-04; CA-M02-16): «les seves
sessions» i «les seves activitats», registrades al motor comú i fetes servir també pel 06 (LC10) i
el 09 (MG1, MG5 i MG6). Només dades inventades.
"""

import datetime
from types import SimpleNamespace

import pytest
from django.http import Http404
from django.utils import timezone

from apps.activities import permissions
from apps.activities.models import Session
from apps.core.models import AuditEntry, Role
from apps.core.permission_catalog import CATALOG, SCOPE_OWN_ACTIVITIES, SCOPE_OWN_SESSIONS
from apps.core.permissions import _SCOPE_CHECKS, has_perm
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_person, a_place, an_outing

pytestmark = pytest.mark.django_db
R = Role.Code


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


def a_session(manager, activity, *teachers, cancelled=False):
    start = timezone.make_aware(datetime.datetime(2027, 6, 14, 9))
    session = Session.objects.create(
        activity=activity,
        kind="sea",
        starts_at=start,
        ends_at=start + datetime.timedelta(hours=2),
        place=a_place(manager, prices=None),
        cancelled=cancelled,
        cancellation_reason="Motiu inventat" if cancelled else "",
    )
    session.instructors.set(teachers)
    return session


def test_the_02_registers_both_scope_checks():
    assert _SCOPE_CHECKS[SCOPE_OWN_SESSIONS] is permissions.teaches
    assert _SCOPE_CHECKS[SCOPE_OWN_ACTIVITIES] is permissions.responsible_for


def test_rn_43_an_instructor_acts_only_on_the_sessions_they_teach(manager, make_admin):  # noqa: F811
    teacher = make_admin(R.INSTRUCTOR)
    mine_activity, other_activity = an_outing(manager), an_outing(manager)
    mine = a_session(manager, mine_activity, teacher.person)
    other = a_session(manager, other_activity)
    gone = a_session(manager, an_outing(manager), teacher.person, cancelled=True)
    code = permissions.ATTENDANCE  # AC9: «les seves» per a l'instructor
    assert has_perm(teacher, code, mine, write=True)
    assert has_perm(teacher, code, mine_activity, write=True)
    assert not has_perm(teacher, code, other, write=True)
    assert not has_perm(teacher, code, other_activity, write=True)
    assert not has_perm(
        teacher, code, gone.activity, write=True
    )  # una sessió cancel·lada no compta
    assert has_perm(
        teacher, code, SimpleNamespace(session=mine), write=True
    )  # un objecte d'un altre mòdul
    assert list(permissions.sessions_for(teacher, code)) == [mine, gone]
    assert set(permissions.sessions_for(manager, code)) == {mine, other, gone}
    assert not permissions.sessions_for(make_admin(R.SECRETARY), code).exists()


def responsible_and_activities(make_admin):  # noqa: F811
    person = a_person("Responsable inventada")
    responsible = make_admin(R.COURSES_MANAGER, person=person)
    return responsible, an_outing(responsible, responsible=person), an_outing(responsible)


def test_the_responsible_acts_only_on_their_activities(make_admin):  # noqa: F811
    responsible, own, other = responsible_and_activities(make_admin)
    for code in (permissions.MATERIAL_COST, permissions.MATERIAL_COST_FIELD):  # AC23 i C7
        assert has_perm(responsible, code, own, write=True), code
        assert not has_perm(responsible, code, other, write=True), code
    assert has_perm(responsible, permissions.MATERIAL_COST, a_session(responsible, own), write=True)
    assert has_perm(
        responsible, permissions.MATERIAL_COST, SimpleNamespace(activity=own), write=True
    )


@pytest.mark.skipif(
    "expenses.margin.view" not in CATALOG, reason="els permisos del 09 arriben amb core/0062"
)
def test_the_09_uses_the_same_check_for_mg1_mg5_and_mg6(make_admin):  # noqa: F811
    responsible, own, other = responsible_and_activities(make_admin)
    for code in ("expenses.record", "expenses.planned_costs", "expenses.margin.view"):
        assert has_perm(responsible, code, own, write=True), code
        assert not has_perm(responsible, code, other, write=True), code
    assert has_perm(make_admin(R.TREASURER), "expenses.margin.view", other)  # «Sí»: totes


def test_ca_m02_16_out_of_scope_is_not_found_and_recorded(manager, make_admin):  # noqa: F811
    teacher = make_admin(R.INSTRUCTOR)
    other = a_session(manager, an_outing(manager))
    with pytest.raises(Http404):
        permissions.require(teacher, permissions.ATTENDANCE, other)
    entry = AuditEntry.objects.get(action=permissions.OUT_OF_SCOPE)
    assert (entry.actor_account, entry.target_id) == (teacher, str(other.pk))
    assert entry.details == {"permission": permissions.ATTENDANCE}
    with pytest.raises(Http404):  # sense el permís, «no trobat» i sense entrada nova
        permissions.require(make_admin(R.SECRETARY), permissions.ATTENDANCE, other)
    assert AuditEntry.objects.filter(action=permissions.OUT_OF_SCOPE).count() == 1
    permissions.require(manager, permissions.ATTENDANCE, other)  # «Sí»: totes


def test_nothing_else_is_ever_inside_a_scope(manager, make_admin):  # noqa: F811
    teacher = make_admin(R.INSTRUCTOR)
    for obj in (None, "meva", SimpleNamespace()):
        assert not permissions.teaches(teacher, obj)
        assert not permissions.responsible_for(teacher, obj)
