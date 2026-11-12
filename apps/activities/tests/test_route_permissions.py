"""Permisos de cada ruta del 02 per cel·la (T-M02-33, amb les pantalles de la T-M02-05 i la
T-M02-06; CA-RP-13; CA-M02-24).

- Cada ruta del 02 × cada rol de la configuració inicial (i el compte personal): el que s'espera
  surt de la matriu carregada a la base de dades (`has_perm`) i del permís que
  `apps/activities/permissions.py` declara per a la ruta; mai d'una taula escrita aquí.
- Accés directe: es demana l'adreça de cada pantalla i de cada acció, no es mira si un enllaç és
  visible. Sense permís, «no trobat» i res no canvia, també amb dades vàlides.
- Una ruta nova del 02 sense declaració fa fallar la prova.

Només dades inventades.
"""

from types import SimpleNamespace

import pytest
from django.urls import reverse

from apps.accounts.models import Account
from apps.activities import catalogue, sessions
from apps.activities.models import (
    Activity,
    CertificationLevel,
    EnvironmentalProject,
    EnvironmentalResult,
    EnvironmentalSubtype,
    OutingType,
    ProgrammeBlock,
    Session,
    TrainingCatalogueEntry,
    TrainingCataloguePrice,
)
from apps.activities.permissions import PUBLIC, ROUTES
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.permissions import has_perm
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_access import _routes
from conftest import PASSWORD

from .helpers import (
    REASON,
    a_course,
    a_done_environmental_outing,
    a_person,
    an_entry,
    an_outing,
    at,
    client_for,
    general,
    outing_type,
)

pytestmark = pytest.mark.django_db

ROLES = [code for code in Role.Code.values if code not in ("member", "visitor", "guest")]
PERSONAL = "personal"
ACCOUNTS = [*ROLES, PERSONAL]
MODULE_ROUTES = {
    name: kwargs
    for name, view, kwargs in _routes()
    if view.__module__.startswith("apps.activities.")
}
NAMES = sorted(name for name, need in ROUTES.items() if isinstance(need, dict))
PUBLIC_NAMES = {name for name, need in ROUTES.items() if need == PUBLIC}

# Quin objecte va al paràmetre `pk` de cada ruta; per defecte, l'activitat.
OBJECT_FOR_ROUTE = {
    "administration:catalogue_entry_edit": "entry",
    "administration:catalogue_entry_prices": "entry",
    "administration:catalogue_entry_active": "entry",
    "administration:outing_type_active": "outing_type",
    "administration:outing_type_mode": "outing_type",
    "administration:certification_level_active": "level",
    "administration:outing_subtype_active": "subtype",
    "administration:project_detail": "project",
    "administration:activity_results": "env_outing",
}


@pytest.fixture
def world(make_admin):  # noqa: F811
    issuer = make_admin("administrator")
    entry = an_entry(issuer)
    course = a_course(issuer, entry)
    session = sessions.add_session(
        course,
        by=issuer,
        kind=Session.Kind.POOL,
        starts_at=at(2027, 6, 14, 9),
        ends_at=at(2027, 6, 14, 11),
    )
    own = a_person("Propia")
    personal = Account.objects.create_personal(own, "propia@example.org", PASSWORD)
    personal.status = Account.Status.ACTIVE
    personal.save()
    return SimpleNamespace(
        entry=entry,
        activity=course,
        session=session,
        outing=an_outing(issuer),
        env_outing=a_done_environmental_outing(issuer),
        outing_type=outing_type("Sèniors"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"),
        project=catalogue.create_project(
            by=issuer, name="Projecte inventat", objective="Objectiu.", department=general()
        ),
        level=catalogue.create_level(by=issuer, name="Nivell inventat", rank=10),
        personal=personal,
    )


def url_for(name, world):
    kwargs = {}
    for param in MODULE_ROUTES[name]:
        target = (
            world.session
            if param == "session_pk"
            else getattr(world, OBJECT_FOR_ROUTE.get(name, "activity"))
        )
        kwargs[param] = target.pk
    return reverse(name, kwargs=kwargs)


def is_login_redirect(response):
    return response.status_code == 302 and response["Location"].startswith(
        reverse("administration:login")
    )


def snapshot():
    return (
        list(TrainingCatalogueEntry.objects.order_by("pk").values_list("pk", "active", "name")),
        TrainingCataloguePrice.objects.count(),
        list(
            OutingType.objects.order_by("pk").values_list(
                "pk", "active", "default_requirements_mode"
            )
        ),
        list(CertificationLevel.objects.order_by("pk").values_list("pk", "active")),
        list(EnvironmentalSubtype.objects.order_by("pk").values_list("pk", "active")),
        EnvironmentalProject.objects.count(),
        list(Activity.objects.order_by("pk").values_list("pk", "status", "title")),
        list(Session.objects.order_by("pk").values_list("pk", "cancelled", "location")),
        ProgrammeBlock.objects.count(),
        AuditEntry.objects.count(),
        OutgoingEmail.objects.count(),
        EnvironmentalResult.objects.count(),
    )


# --- Declaració -----------------------------------------------------------------------------------


def test_every_route_of_the_module_declares_its_permission():
    assert set(MODULE_ROUTES) == set(ROUTES)


def test_every_route_is_in_the_administration_and_declares_get_and_post():
    for name in NAMES:
        need = ROUTES[name]
        assert name.startswith("administration:"), name
        assert set(need) == {"GET", "POST"}, name
        # Cap pantalla del 02 es desa només amb un permís de consulta.
        assert all(write for _code, write in need["POST"]) or need["POST"] == need["GET"], name


def test_declared_public_routes_are_the_public_ones():
    from apps.core.tests.test_access import PUBLIC_ROUTES

    assert PUBLIC_NAMES == set(MODULE_ROUTES) & set(PUBLIC_ROUTES)
    assert PUBLIC_NAMES == {"activities:list", "activities:detail"}
    # Cap ruta de l'administració no és pública.
    assert not {name for name in PUBLIC_NAMES if name.startswith("administration:")}


# --- CA-RP-13: ruta × rol, a partir de la matriu carregada ----------------------------------------


@pytest.mark.parametrize("who", ACCOUNTS)
@pytest.mark.parametrize("name", NAMES)
def test_ca_rp_13_route_cell(make_admin, world, name, who):  # noqa: F811
    account = world.personal if who == PERSONAL else make_admin(who)
    client = client_for(account)
    url = url_for(name, world)
    for method in ("GET", "POST"):  # GET primer: el POST pot canviar l'objecte
        before = snapshot()
        response = getattr(client, method.lower())(url)
        if who == PERSONAL:
            # El compte personal no entra a l'administració: cap a l'entrada d'administració.
            assert is_login_redirect(response), (method, response.status_code)
            assert snapshot() == before
            continue
        allowed = all(has_perm(account, code, write=w) for code, w in ROUTES[name][method])
        if allowed:
            assert response.status_code != 404, method
            assert not is_login_redirect(response), method
        else:
            assert response.status_code == 404, method
            assert snapshot() == before, method


# --- Denegació amb dades vàlides: res no canvia ---------------------------------------------------

WHEN = {"starts_at": "2027-06-15T09:00", "ends_at": "2027-06-15T11:00"}
VALID_POSTS = {
    "administration:catalogue_course_add": {
        "name": "Curs nou inventat",
        "default_places": "8",
        "price_member_cents": "45",
        "price_non_member_cents": "60",
        "department": "general",
    },
    "administration:catalogue_entry_edit": {
        "name": "Nom canviat",
        "default_places": "8",
        "department": "general",
    },
    "administration:catalogue_entry_prices": {
        "price_member_cents": "50",
        "price_non_member_cents": "65",
        "valid_from": "2030-01-01",
        "note": REASON,
    },
    "administration:catalogue_entry_active": {"actiu": "0"},
    "administration:outing_types": {
        "form": "subtipus",
        "subtipus-name": "Subtipus nou inventat",
    },
    "administration:outing_type_active": {"actiu": "0"},
    "administration:outing_type_mode": {"mode": "block"},
    "administration:certification_levels": {"name": "Un altre nivell", "rank": "20"},
    "administration:certification_level_active": {"actiu": "0"},
    "administration:outing_subtype_active": {"actiu": "0"},
    "administration:projects": {
        "name": "Un altre projecte",
        "objective": "Objectiu inventat.",
        "department": "general",
    },
    "administration:activity_step": {"pas": "publica"},
    "administration:activity_cancel": {"reason": REASON},
    "administration:activity_results": {"waste_grams": "12,5"},
    "administration:activity_edit": {"title": "Títol canviat"},
    "administration:session_add": {"kind": "sea", **WHEN},
    "administration:session_edit": {"kind": "pool", "location": "Un altre lloc", **WHEN},
    "administration:session_cancel": {"reason": REASON},
    "administration:activity_programme": {"starts_at_0": "08:00", "label_0": "Trobada"},
}


@pytest.mark.parametrize("role", ["secretary", "instructor", "equipment_manager", "board"])
@pytest.mark.parametrize("name", sorted(VALID_POSTS))
def test_a_post_with_valid_data_changes_nothing_without_the_permission(
    make_admin,  # noqa: F811
    world,
    name,
    role,
):
    """Qui no té AC6 o AC7 no desa res encara que enviï el formulari sencer a l'adreça exacta."""
    data = {
        key: (general().pk if value == "general" else value)
        for key, value in VALID_POSTS[name].items()
    }
    before = snapshot()
    response = client_for(make_admin(role)).post(url_for(name, world), data)
    assert response.status_code == 404
    assert snapshot() == before


@pytest.mark.parametrize("name", sorted(VALID_POSTS))
def test_the_same_post_is_accepted_with_the_permission(make_admin, world, name):  # noqa: F811
    """Control de la prova anterior: amb el permís, la mateixa petició no dona «no trobat»."""
    data = {
        key: (general().pk if value == "general" else value)
        for key, value in VALID_POSTS[name].items()
    }
    response = client_for(make_admin("courses_manager")).post(url_for(name, world), data)
    assert response.status_code in (200, 303), response.status_code


# --- Menú: només ajuda, però coherent amb el permís -----------------------------------------------


@pytest.mark.parametrize("who", ROLES)
def test_admin_home_links_match_the_route_permissions(make_admin, world, who):  # noqa: F811
    account = make_admin(who)
    page = client_for(account).get(reverse("administration:home")).content.decode()
    for name in NAMES:
        if MODULE_ROUTES[name]:
            continue  # rutes d'un objecte: no surten al menú
        link = f'href="{reverse(name)}"'
        allowed = all(has_perm(account, c, write=w) for c, w in ROUTES[name]["GET"])
        if link in page:
            assert allowed, name
    for name in ("administration:activities", "administration:catalogue_courses"):
        allowed = all(has_perm(account, c, write=w) for c, w in ROUTES[name]["GET"])
        assert (f'href="{reverse(name)}"' in page) == allowed, name
