"""Pantalles d'administració del 02, T-M02-06a: llistat i fitxa d'una activitat (AC7; MG6 per a
l'enllaç al marge; RN-M02-41 a la fitxa). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities import states
from apps.core.models import Role, RolePermission
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import a_course, a_place, an_outing

R = Role.Code
LIST = reverse("administration:activities")


def detail(activity):
    return reverse("administration:activity_detail", args=[activity.pk])


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


@pytest.fixture
def client_of(login_as):
    return lambda account: login_as(account, AREA_ADMIN)


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.SECRETARY, R.EQUIPMENT_MANAGER, R.BOARD])
def test_without_ac7_every_screen_is_not_found(client_of, make_admin, manager, role):  # noqa: F811
    activity = an_outing(manager)
    client = client_of(make_admin(role))
    for url in (LIST, detail(activity), reverse("administration:activity_detail", args=[999999])):
        assert client.get(url).status_code == 404, url


def test_list_filters_by_state_and_kind(client_of, manager):
    an_outing(manager, title="Sortida en esborrany")
    a_course(manager, title="Curs en esborrany")
    client = client_of(manager)
    html = main_of(client.get(LIST).content.decode())
    assert "Sortida en esborrany" in html and "Curs en esborrany" in html
    html = main_of(client.get(LIST, {"classe": "course"}).content.decode())
    assert "Curs en esborrany" in html and "Sortida en esborrany" not in html
    assert "Cap activitat coincideix" in main_of(
        client.get(LIST, {"estat": "open"}).content.decode()
    )
    assert client.get(LIST, {"estat": "invent", "classe": "x"}).status_code == 200


def test_detail_shows_the_activity_and_no_participant(client_of, manager):
    activity = an_outing(manager, title="Sortida de la fitxa")
    html = main_of(client_of(manager).get(detail(activity)).content.decode())
    assert "Sortida de la fitxa" in html and activity.place.name in html and "45,00" in html
    assert "Preu diferent de l" not in html


def test_detail_shows_the_standard_and_the_note_when_the_price_differs(client_of, manager):
    activity = an_outing(
        manager, place=a_place(manager), price_member_cents=5000, price_non_member_cents=6000,
        price_override_note="Barca més cara (inventat).",
    )  # fmt: skip
    html = main_of(client_of(manager).get(detail(activity)).content.decode())
    assert "Preu diferent de l" in html and "45,00" in html and "Barca més cara" in html


def test_margin_link_only_with_mg6_for_this_activity(client_of, make_admin, manager):  # noqa: F811
    """MG6 del responsable de cursos i sortides és «les seves activitats»."""
    activity = an_outing(manager, responsible=manager.person)
    other = an_outing(manager)
    assert reverse("administration:activity_margin", args=[other.pk]) not in (
        client_of(manager).get(detail(other)).content.decode()
    )
    margin = reverse("administration:activity_margin", args=[activity.pk])
    assert margin in client_of(manager).get(detail(activity)).content.decode()
    RolePermission.objects.filter(
        role__code=R.COURSES_MANAGER, permission_code="expenses.margin.view"
    ).delete()
    assert (
        margin
        not in client_of(make_admin(R.COURSES_MANAGER)).get(detail(activity)).content.decode()
    )


def test_cancelled_activity_shows_the_reason(client_of, manager):
    activity = an_outing(manager)
    states.cancel(activity, by=manager, reason="Mal temps inventat.")
    html = main_of(client_of(manager).get(detail(activity)).content.decode())
    assert "Mal temps inventat." in html and "Cancel·lada" in html
