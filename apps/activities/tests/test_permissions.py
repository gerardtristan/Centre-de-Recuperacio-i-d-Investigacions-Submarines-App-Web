"""Permisos del 02 per cel·la (T-M02-33; CA-RP-13; CA-M02-24 i CA-M02-35; decisió 059).

- **Declaració:** el catàleg té els permisos AC5 a AC20 i C3, i cap altre del 02. AC1 a AC4 són
  accions pròpies o públiques, i CF1 i CF2 són del mòdul 11.
- **Matriu:** cada cel·la (permís × rol) coincideix amb la taula «02 Activitats» de la configuració
  inicial del pla (`docs/planning.md#rols-i-permisos-059-matriu`). La taula `PLAN` d'aquest fitxer
  n'és una transcripció feta a mà, a propòsit: no surt del catàleg ni de la migració.
- **Serveis:** cada servei del 02 que canvia dades rebutja amb «no trobat» un compte sense el
  permís amb edició, també cridat fora d'una vista, i no canvia res.
- **Rutes:** el 02 encara no té cap vista; una ruta nova sense declarar fa fallar la prova.

L'abast per objecte «les seves sessions» (T-M02-04) és a `test_object_permissions.py`. Fora
d'aquestes proves, perquè encara no existeixen: les vistes (T-M02-05, T-M02-06 i T-M02-16). Només
dades inventades.
"""

import inspect
import re
from types import SimpleNamespace

import pytest
from django.http import Http404

from apps.accounts.models import Account
from apps.activities import catalogue, permissions, services, sessions, states
from apps.activities.models import (
    Activity,
    EnvironmentalProject,
    EnvironmentalSubtype,
    OutingType,
    ProgrammeBlock,
    Session,
    TrainingCatalogueEntry,
    TrainingCataloguePrice,
)
from apps.core import audit
from apps.core.models import AuditEntry, PermissionMatrixVersion, Role, RolePermission
from apps.core.permission_catalog import CATALOG, PERMISSIONS
from apps.core.permissions import has_perm, scope_for
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_access import _routes
from conftest import PASSWORD

from .helpers import (
    BEFORE_DEADLINE,
    REASON,
    TODAY,
    a_course,
    a_person,
    an_entry,
    an_outing,
    at,
    general,
)

ROLES = [code for code in Role.Code.values if code not in ("member", "visitor", "guest")]
PERSONAL = "personal"  # el compte personal, que no hereta cap rol (059, punt 4.2)
ACCOUNTS = [*ROLES, PERSONAL]

ALL, READ, OWN = "all", "read", "own_sessions"
INSTR, RCS, RM = "instructor", "courses_manager", "equipment_manager"
TRES, ADMIN, PRES, BOARD = "treasurer", "administrator", "president", "board"
FOUR = dict.fromkeys((RCS, TRES, ADMIN, PRES), ALL)  # qui gestiona activitats completes
THREE = dict.fromkeys((RCS, ADMIN, PRES), ALL)  # els mateixos sense el tresorer

# Transcripció de la taula «02 Activitats» de la configuració inicial (pla, 059). Un rol que no
# hi surt és «—». Secretaria, Departament d'Història, comunicació i botiga no hi tenen res.
PLAN = {
    "AC5": ("activities.enrol_in_person", FOUR),
    "AC6": ("activities.catalogue.manage", FOUR),
    "AC7": ("activities.manage", FOUR),
    "AC8": ("activities.participants.view", {INSTR: OWN, RM: READ, **FOUR}),
    "AC9": ("activities.attendance.record", {INSTR: OWN, **THREE}),
    "AC10a": ("activities.assessment.record", {INSTR: OWN}),
    "AC10b": ("activities.reinforcement.propose", {INSTR: OWN}),
    "AC11": ("activities.reinforcement.decide", THREE),
    "AC12": ("activities.outcome.record", {INSTR: OWN}),
    "AC13": ("activities.certificate.issue", THREE),
    "AC14": ("activities.environment.manage", {BOARD: READ, **THREE}),
    "AC15": ("activities.message.send", FOUR),
    "AC16": ("activities.waitlist.manage", FOUR),
    "AC17": ("activities.refund.propose", FOUR),
    "AC18": ("activities.refund.execute", {TRES: ALL}),
    "AC19": ("activities.income.view", {RCS: READ, TRES: ALL, ADMIN: ALL}),
    "AC20": ("activities.reports.view", {INSTR: OWN, RM: READ, BOARD: READ, **FOUR}),
    "C3": ("activities.field.student_for_instructor", {INSTR: OWN}),
}
PROTECTED = {"C3"}
OWN_SESSIONS_ONLY = {"AC10a", "AC10b", "AC12", "C3"}  # RN-RP-04
MODULE = [p for p in PERMISSIONS if p.module == "activities"]


# --- Declaració al catàleg ------------------------------------------------------------------------


def test_the_catalog_declares_ac5_to_ac20_and_c3_and_nothing_else():
    assert {p.ref: p.code for p in MODULE} == {ref: code for ref, (code, _cells) in PLAN.items()}


def test_own_and_public_actions_and_conferences_are_not_role_permissions():
    refs = {p.ref for p in PERMISSIONS}
    # AC1 a AC4 es fan amb el compte personal o sense compte; CF1 i CF2 són del mòdul 11.
    assert not refs & {"AC1", "AC2", "AC3", "AC4", "AC10", "CF1", "CF2"}


def test_the_module_constants_are_the_catalog_codes():
    constants = {
        value for name, value in vars(permissions).items() if re.fullmatch(r"AC\d+[AB]?|C3", name)
    }
    assert constants == {p.code for p in MODULE}
    assert permissions.AC6 == permissions.CATALOGUE == "activities.catalogue.manage"
    assert permissions.AC7 == permissions.MANAGE == "activities.manage"


@pytest.mark.parametrize("ref", sorted(OWN_SESSIONS_ONLY))
def test_rn_rp_04_only_who_teaches_the_session(ref):
    # Avaluar, proposar reforç, posar apte i els camps de l'alumne: només «les seves sessions».
    assert CATALOG[PLAN[ref][0]].allowed_scopes == (OWN,)


def test_c3_is_a_protected_field_without_rows():
    perm = CATALOG[PLAN["C3"][0]]
    assert perm.kind == "field"
    assert perm.protected
    assert perm.protected_by
    assert perm.touches_personal_data


@pytest.mark.parametrize("ref", sorted(PLAN))
def test_permissions_over_people_or_money_are_marked(ref):
    # RN-RP-07 i RN-RP-11: l'editor avisa quan s'amplia un accés a dades personals o a diners.
    perm = CATALOG[PLAN[ref][0]]
    assert perm.touches_personal_data or perm.touches_money or ref == "AC14"


# --- Matriu inicial: cada cel·la del pla ----------------------------------------------------------

CELLS = [(ref, role) for ref in PLAN for role in ROLES]


@pytest.mark.parametrize(("ref", "role"), CELLS, ids=[f"{ref}-{role}" for ref, role in CELLS])
def test_ca_rp_13_initial_cell_matches_the_plan(make_admin, ref, role):  # noqa: F811
    """CA-RP-13 i CA-M02-24: el «sí» (amb el seu abast) o el «no» de cada cel·la del 02."""
    code, cells = PLAN[ref]
    account = make_admin(role)
    expected = cells.get(role)
    assert scope_for(account, code) == expected
    assert has_perm(account, code) == (expected is not None)
    # «Cons.» no deixa canviar res.
    assert has_perm(account, code, write=True) == (expected in (ALL, OWN))


@pytest.mark.django_db
def test_the_database_has_exactly_the_editable_cells_of_the_plan():
    stored = set(
        RolePermission.objects.filter(permission_code__startswith="activities.").values_list(
            "role__code", "permission_code", "scope"
        )
    )
    expected = {
        (role, code, scope)
        for ref, (code, cells) in PLAN.items()
        if ref not in PROTECTED
        for role, scope in cells.items()
    }
    assert stored == expected


@pytest.mark.django_db
def test_the_cells_arrive_with_a_new_version_of_the_matrix():
    """060: la matriu inicial no s'edita; el 02 hi afegeix les seves cel·les amb una versió nova
    que diu què ha canviat."""
    versions = [
        v
        for v in PermissionMatrixVersion.objects.order_by("number")
        if any(row["permission"].startswith("activities.") for row in v.diff)
    ]
    assert len(versions) == 1
    (version,) = versions
    assert version.number > 1
    assert "02" in version.note
    stored = RolePermission.objects.filter(permission_code__startswith="activities.")
    assert {(r["role"], r["permission"], r["before"], r["after"]) for r in version.diff} == {
        (role, code, None, scope)
        for role, code, scope in stored.values_list("role__code", "permission_code", "scope")
    }
    assert len(version.diff) == stored.count()


@pytest.mark.django_db
def test_roles_outside_the_table_have_nothing_of_the_module(make_admin):  # noqa: F811
    for role in ("secretary", "history_department", "communications_manager", "shop_manager"):
        account = make_admin(role)
        assert not [p.code for p in MODULE if has_perm(account, p.code)], role


# --- Serveis: el permís també fora de la vista ----------------------------------------------------

AC6, AC7 = permissions.CATALOGUE, permissions.MANAGE


@pytest.fixture
def world(make_admin):  # noqa: F811
    """Una fitxa, un curs en esborrany amb una sessió, una sortida oberta i una de tancada a
    inscripcions, fetes per un administrador; un instructor i un compte personal."""
    issuer = make_admin(ADMIN)
    entry = an_entry(issuer)
    course = a_course(issuer, entry)
    session = sessions.add_session(
        course,
        by=issuer,
        kind=Session.Kind.POOL,
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
    )
    open_outing = an_outing(issuer, title="Sortida oberta inventada")
    states.publish(open_outing, by=issuer, now=BEFORE_DEADLINE)
    closed_outing = an_outing(issuer, title="Sortida tancada inventada")
    states.publish(closed_outing, by=issuer, now=BEFORE_DEADLINE)
    states.close_registration(closed_outing, by=issuer, now=BEFORE_DEADLINE)
    own = a_person("Propia")
    personal = Account.objects.create_personal(own, "propia@example.org", PASSWORD)
    personal.status = Account.Status.ACTIVE
    personal.save()
    return SimpleNamespace(
        entry=entry,
        course=course,
        session=session,
        open_outing=open_outing,
        closed_outing=closed_outing,
        teacher=make_admin(INSTR).person,
        personal=personal,
    )


SERVICES = {
    # nom: (permís que cal, amb edició; crida vàlida)
    "catalogue.create_entry": (AC6, lambda w, by: an_entry(by, name="Una altra fitxa inventada")),
    "catalogue.update_entry": (
        AC6,
        lambda w, by: catalogue.update_entry(w.entry, by=by, description="Descripció inventada."),
    ),
    "catalogue.set_active": (AC6, lambda w, by: catalogue.set_active(w.entry, False, by=by)),
    "catalogue.change_prices": (
        AC6,
        lambda w, by: catalogue.change_prices(
            w.entry,
            by=by,
            price_member_cents=5000,
            price_non_member_cents=6000,
            valid_from=TODAY,
            note=REASON,
            today=TODAY,
        ),
    ),
    "catalogue.create_outing_type": (
        AC6,
        lambda w, by: catalogue.create_outing_type(
            by=by, name="Tipus inventat", default_department=general()
        ),
    ),
    "catalogue.create_subtype": (
        AC6,
        lambda w, by: catalogue.create_subtype(by=by, name="Subtipus inventat"),
    ),
    "catalogue.create_project": (
        AC6,
        lambda w, by: catalogue.create_project(
            by=by, name="Projecte inventat", objective="Objectiu inventat.", department=general()
        ),
    ),
    "services.create_course": (AC7, lambda w, by: a_course(by, w.entry, title="Un altre curs")),
    "services.create_outing": (AC7, lambda w, by: an_outing(by, title="Una altra sortida")),
    "services.update_activity": (
        AC7,
        lambda w, by: services.update_activity(w.course, by=by, title="Títol nou inventat"),
    ),
    "states.publish": (AC7, lambda w, by: states.publish(w.course, by=by, now=BEFORE_DEADLINE)),
    "states.close_registration": (
        AC7,
        lambda w, by: states.close_registration(w.open_outing, by=by, now=BEFORE_DEADLINE),
    ),
    "states.reopen_registration": (
        AC7,
        lambda w, by: states.reopen_registration(w.closed_outing, by=by, now=BEFORE_DEADLINE),
    ),
    "states.mark_done": (
        AC7,
        lambda w, by: states.mark_done(w.closed_outing, by=by, now=at(2027, 6, 15, 18)),
    ),
    "states.cancel": (AC7, lambda w, by: states.cancel(w.course, by=by, reason=REASON)),
    "sessions.add_session": (
        AC7,
        lambda w, by: sessions.add_session(
            w.course,
            by=by,
            kind=Session.Kind.SEA,
            starts_at=at(2027, 6, 15, 9),
            ends_at=at(2027, 6, 15, 12),
        ),
    ),
    "sessions.update_session": (
        AC7,
        lambda w, by: sessions.update_session(w.session, by=by, location="Piscina inventada"),
    ),
    "sessions.set_instructors": (
        AC7,
        lambda w, by: sessions.set_instructors(w.session, [w.teacher], by=by),
    ),
    "sessions.cancel_session": (
        AC7,
        lambda w, by: sessions.cancel_session(w.session, by=by, reason=REASON),
    ),
    "sessions.set_programme": (
        AC7,
        lambda w, by: sessions.set_programme(
            w.open_outing,
            [{"starts_at": at(2027, 6, 14, 8).time(), "label": "Trobada"}],
            by=by,
        ),
    ),
}


def snapshot():
    return (
        list(TrainingCatalogueEntry.objects.order_by("pk").values_list("pk", "active", "name")),
        TrainingCataloguePrice.objects.count(),
        OutingType.objects.count(),
        EnvironmentalSubtype.objects.count(),
        EnvironmentalProject.objects.count(),
        list(Activity.objects.order_by("pk").values_list("pk", "status", "title")),
        list(Session.objects.order_by("pk").values_list("pk", "cancelled", "location")),
        Session.instructors.through.objects.count(),
        ProgrammeBlock.objects.count(),
        AuditEntry.objects.count(),
    )


def test_every_service_that_changes_data_is_in_the_table():
    """Tota funció pública dels serveis del 02 que rep `by` comprova un permís i té la seva fila
    a `SERVICES`: un servei nou sense permís o sense prova fa fallar això."""
    found = set()
    for module in (catalogue, services, states, sessions):
        short = module.__name__.rsplit(".", 1)[-1]
        for name, function in inspect.getmembers(module, inspect.isfunction):
            if function.__module__ != module.__name__ or name.startswith("_"):
                continue
            if "by" not in inspect.signature(function).parameters:
                continue
            source = inspect.getsource(function)
            assert "permissions.require(by, " in source or "_create_named(" in source, name
            found.add(f"{short}.{name}")
    assert found == set(SERVICES)
    assert "permissions.require(by, " in inspect.getsource(catalogue._create_named)


@pytest.mark.parametrize("who", ACCOUNTS)
@pytest.mark.parametrize("service", sorted(SERVICES))
def test_service_checks_the_permission_outside_the_view(make_admin, world, service, who):  # noqa: F811
    code, call = SERVICES[service]
    by = world.personal if who == PERSONAL else make_admin(who)
    allowed = has_perm(by, code, write=True)
    # Amb la configuració inicial, AC6 i AC7 els tenen els quatre rols que gestionen activitats.
    assert allowed == (who in FOUR)
    before = snapshot()
    if allowed:
        call(world, by)
        assert snapshot() != before
        return
    with pytest.raises(Http404):
        call(world, by)
    assert snapshot() == before


@pytest.mark.parametrize("service", sorted(SERVICES))
def test_an_actor_that_is_not_an_account_is_not_found(world, service):
    """El sistema i un actor sense identificar no tenen permisos de rol: els passos del sistema
    tenen les seves funcions (`states.advance_by_clock`)."""
    _code, call = SERVICES[service]
    before = snapshot()
    for by in (None, audit.system("activities.proves")):
        with pytest.raises(Http404):
            call(world, by)
    assert snapshot() == before


def test_the_personal_account_of_an_administrator_has_no_permission(make_admin, world):  # noqa: F811
    admin = make_admin(ADMIN)
    personal = Account.objects.create_personal(admin.person, "admin@example.org", PASSWORD)
    personal.status = Account.Status.ACTIVE
    personal.save()
    assert permissions.can(admin, AC7)
    assert not permissions.can(personal, AC7)
    with pytest.raises(Http404):
        states.cancel(world.course, by=personal, reason=REASON)


def test_a_change_in_the_matrix_applies_to_the_services_at_once(make_admin, world):  # noqa: F811
    """Els permisos són dades (059): si l'administrador treu AC7 al tresorer, el servei el rebutja
    a la crida següent, sense tocar codi."""
    treasurer = make_admin(TRES)
    states.publish(world.course, by=treasurer, now=BEFORE_DEADLINE)
    RolePermission.objects.filter(role__code=TRES, permission_code=AC7).delete()
    with pytest.raises(Http404):
        states.cancel(world.course, by=treasurer, reason=REASON)
    world.course.refresh_from_db()
    assert world.course.status == Activity.Status.OPEN


def test_a_read_only_scope_shows_but_does_not_change(make_admin):  # noqa: F811
    equipment = make_admin(RM)
    assert permissions.can(equipment, permissions.PARTICIPANTS, write=False)
    assert not permissions.can(equipment, permissions.PARTICIPANTS)
    with pytest.raises(Http404):
        permissions.require(equipment, permissions.PARTICIPANTS)
    permissions.require(equipment, permissions.PARTICIPANTS, write=False)


# --- CA-M02-35 (la part que ja existeix) ----------------------------------------------------------


def test_ca_m02_35_the_treasurer_creates_and_publishes_but_neither_calls_the_roll_nor_assesses(
    make_admin,  # noqa: F811
):
    """CA-M02-35: el tresorer crea i publica una activitat. Duplicar és de la T-M02-07. No té ni
    passar llista (AC9) ni avaluar o posar apte (AC10a, AC10b i AC12); el «no trobat» de les
    pantalles i l'excepció «tret que faci classe a la sessió» són de la T-M02-04, la T-M02-16 i la
    T-M02-17."""
    treasurer = make_admin(TRES)
    outing = an_outing(treasurer)
    states.publish(outing, by=treasurer, now=BEFORE_DEADLINE)
    assert outing.status == Activity.Status.OPEN
    for code in (
        permissions.ATTENDANCE,
        permissions.ASSESSMENT,
        permissions.REINFORCEMENT_PROPOSE,
        permissions.OUTCOME,
    ):
        assert not permissions.can(treasurer, code, write=False), code


# --- Rutes ----------------------------------------------------------------------------------------


def test_every_route_of_the_module_declares_its_permission():
    # El 02 encara no té vistes. Una ruta nova sense declaració a `ROUTES` fa fallar això.
    module_routes = {
        name for name, view, _kwargs in _routes() if view.__module__.startswith("apps.activities.")
    }
    assert module_routes == set(permissions.ROUTES)
