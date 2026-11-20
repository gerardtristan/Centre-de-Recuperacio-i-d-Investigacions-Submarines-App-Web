"""Menú de l'administració (T-DX-76, V5 i V19): cada pantalla de l'administració marca l'entrada
d'on s'obre. Les rutes noves han de penjar d'una entrada o ser a `STANDALONE`."""

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from apps.accounts.navigation import ENTRIES
from apps.accounts.security import AREA_ADMIN
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

# Pantalles sense menú: entrar, sortir, el doble factor de la primera entrada i els fitxers privats.
STANDALONE = {
    "administration:login",
    "administration:login_totp",
    "administration:logout",
    "administration:change_temporary_credential",
    "administration:totp_enrol",
    "administration:private_file",
}


def admin_route_names(resolver=None, namespace=""):
    for pattern in (resolver or get_resolver()).url_patterns:
        if isinstance(pattern, URLResolver):
            inner = f"{namespace}{pattern.namespace}:" if pattern.namespace else namespace
            yield from admin_route_names(pattern, inner)
        elif isinstance(pattern, URLPattern) and pattern.name:
            name = f"{namespace}{pattern.name}"
            if name.startswith("administration:"):
                yield name


def test_every_admin_route_belongs_to_an_entry_or_is_standalone():
    in_menu = {route for name, _label, kids in ENTRIES for route in (name, *kids)}
    assert sorted(set(admin_route_names()) - in_menu - STANDALONE) == []
    assert not STANDALONE & in_menu


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("page", "role", "parent"),
    [
        ("administration:payments_returns", "treasurer", "administration:payments_remittances"),
        ("administration:legal_texts", "administrator", "administration:settings"),
    ],
)
def test_the_parent_entry_is_current_on_its_sub_page(login_as, make_admin, page, role, parent):  # noqa: F811
    response = login_as(make_admin(role), AREA_ADMIN).get(reverse(page))
    assert response.status_code == 200
    assert f'<a href="{reverse(parent)}" aria-current="page">' in response.content.decode()
