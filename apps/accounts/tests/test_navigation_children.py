"""Menú de l'administració (T-DX-49): les pantalles de tresoreria que s'obren des d'una entrada
(traspàs, arqueig, liquidacions; «a revisar») la deixen marcada com a actual."""

import pytest
from django.urls import reverse

from apps.accounts.navigation import ENTRIES
from apps.accounts.security import AREA_ADMIN
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db

PAGES = [
    ("administration:treasury_transfer", "administration:treasury_accounts"),
    ("administration:treasury_cash_count", "administration:treasury_accounts"),
    ("administration:treasury_settlements", "administration:treasury_accounts"),
    ("administration:treasury_review", "administration:treasury_reconciliation"),
]


def test_every_child_route_exists_and_belongs_to_one_entry():
    children = [child for _name, _label, kids in ENTRIES for child in kids]
    assert len(children) == len(set(children))
    for page, parent in PAGES:
        assert page in dict((name, kids) for name, _l, kids in ENTRIES)[parent]


@pytest.mark.parametrize(("page", "parent"), PAGES)
def test_the_parent_entry_is_current_on_its_child_pages(login_as, make_admin, page, parent):  # noqa: F811
    client = login_as(make_admin("treasurer"), AREA_ADMIN)
    response = client.get(reverse(page))
    assert response.status_code == 200
    html = response.content.decode()
    assert f'<a href="{reverse(parent)}" aria-current="page">' in html


def test_accounts_entry_is_current_on_the_roles_screen(login_as, make_admin):  # noqa: F811
    """T-DX-55: la pantalla de rols d'un compte (T-RP-02) porta paràmetre i no té entrada pròpia;
    «Comptes d'administrador», d'on s'obre, queda marcada."""
    admin = make_admin("administrator")
    other = make_admin("treasurer")
    response = login_as(admin, AREA_ADMIN).get(
        reverse("administration:account_roles", args=[other.pk])
    )
    assert response.status_code == 200
    accounts = reverse("administration:accounts")
    assert f'<a href="{accounts}" aria-current="page">' in response.content.decode()


def test_accounts_entry_is_current_on_the_deactivate_screen(login_as, make_admin):  # noqa: F811
    """T-RP-02d: la pantalla de desactivar un compte s'obre des dels rols del compte; «Comptes
    d'administrador» queda marcada."""
    admin = make_admin("administrator")
    other = make_admin("administrator")
    response = login_as(admin, AREA_ADMIN).get(
        reverse("administration:account_deactivate", args=[other.pk])
    )
    assert response.status_code == 200
    accounts = reverse("administration:accounts")
    assert f'<a href="{accounts}" aria-current="page">' in response.content.decode()


def test_types_entry_is_current_when_editing_a_type(login_as, make_admin):  # noqa: F811
    """T-DX-56: «Tipus de soci» (T-M01-52) queda marcada també en editar-ne un."""
    from apps.members.models import MembershipType

    membership_type = MembershipType.objects.first()
    assert membership_type, "la migració de dades crea els tipus inicials"
    client = login_as(make_admin("administrator"), AREA_ADMIN)
    url = reverse("administration:membership_type_edit", args=[membership_type.pk])
    response = client.get(url)
    assert response.status_code == 200
    entry = reverse("administration:membership_types")
    assert f'<a href="{entry}" aria-current="page">' in response.content.decode()
