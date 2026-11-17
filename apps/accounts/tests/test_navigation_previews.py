"""Menú de l'administració (T-DX-50): l'índex de les pantalles «En construcció» només surt amb el
permís DX1 (core.under_construction.view), encara que SHOW_UNDER_CONSTRUCTION ensenyi les pantalles
a tothom, i queda marcat com a actual també a cada pantalla."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import Role, RolePermission
from apps.core.permissions import has_perm
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.under_construction import PERMISSION
from apps.previews.screens import discover

pytestmark = pytest.mark.django_db

INDEX = reverse("administration:previews:index")


@pytest.fixture(autouse=True)
def secretary_has_dx1(db):
    """Cap rol no comença amb DX1 (P-90): a la prova el té la secretaria."""
    role = Role.objects.get(code=Role.Code.SECRETARY)
    RolePermission.objects.create(role=role, permission_code=PERMISSION, scope="all")


def link(url):
    return f'<a href="{url}"'


@pytest.mark.parametrize("show", [False, True])
def test_entry_only_with_the_permission(login_as, make_admin, settings, show):  # noqa: F811
    settings.SHOW_UNDER_CONSTRUCTION = show
    with_perm, without = make_admin("secretary"), make_admin("treasurer")
    assert has_perm(with_perm, PERMISSION) and not has_perm(without, PERMISSION)
    home = reverse("administration:home")
    assert link(INDEX) in login_as(with_perm, AREA_ADMIN).get(home).content.decode()
    assert link(INDEX) not in login_as(without, AREA_ADMIN).get(home).content.decode()


def test_index_entry_is_current_on_every_screen(login_as, make_admin):  # noqa: F811
    client = login_as(make_admin("secretary"), AREA_ADMIN)
    for name, _module in discover():
        response = client.get(reverse(f"administration:previews:{name}"))
        assert response.status_code == 200, name
        assert f'<a href="{INDEX}" aria-current="page">' in response.content.decode(), name


def test_index_links_stay_in_the_administration(login_as, make_admin):  # noqa: F811
    """Des de l'administració, l'índex enllaça les pantalles de l'administració: a /en-construccio/
    un compte d'administrador seria a la zona de socis i rebria un 401."""
    html = login_as(make_admin("secretary"), AREA_ADMIN).get(INDEX).content.decode()
    for name, _module in discover():
        assert link(reverse(f"administration:previews:{name}")) in html, name
    assert reverse("previews:index") != INDEX
