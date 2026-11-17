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
