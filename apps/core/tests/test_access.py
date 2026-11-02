"""Sessió obligatòria per defecte (RN-40)."""

import uuid

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse

# Rutes públiques declarades. Afegir-ne una obliga a canviar aquesta llista a propòsit.
PUBLIC_ROUTES = {
    "core:health",
    # Enllaç signat local (imita Scaleway fora de producció): l'enllaç és la credencial.
    "core:local_private_file",
    "accounts:login",
    "accounts:login_totp",
    "accounts:logout",
    "administration:login",
    "administration:login_totp",
    "administration:totp_enrol",
    "administration:logout",
}

SAMPLE_VALUES = {
    "int": 1,
    "str": "x",
    "string": "x",
    "slug": "x",
    "path": "x",
    "uuid": uuid.UUID(int=0),
}


def _routes(patterns=None, namespace=""):
    """Totes les rutes, amb el nom complet i valors d'exemple per als paràmetres."""
    for entry in get_resolver().url_patterns if patterns is None else patterns:
        if isinstance(entry, URLResolver):
            child_ns = f"{namespace}{entry.namespace}:" if entry.namespace else namespace
            yield from _routes(entry.url_patterns, child_ns)
        elif isinstance(entry, URLPattern):
            if not entry.name:
                yield None, entry.callback, {}
                continue
            converters = getattr(entry.pattern, "converters", {})
            kwargs = {
                name: SAMPLE_VALUES[type(conv).__name__.removesuffix("Converter").lower()]
                for name, conv in converters.items()
            }
            yield f"{namespace}{entry.name}", entry.callback, kwargs


def _login_url_for(name):
    if name.startswith("administration:"):
        return reverse("administration:login")
    return reverse("accounts:login")


def test_every_route_has_a_name():
    # Sense nom, una ruta quedaria fora de la comprovació de sota.
    assert all(name for name, _, _ in _routes())


def test_declared_public_routes_match_the_list():
    declared = {name for name, view, _ in _routes() if not getattr(view, "login_required", True)}
    assert declared == PUBLIC_ROUTES


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("name", "kwargs"),
    [(name, kwargs) for name, _, kwargs in _routes() if name and name not in PUBLIC_ROUTES],
)
def test_private_route_without_session_redirects_to_login(client, name, kwargs):
    url = reverse(name, kwargs=kwargs)
    response = client.get(url)
    assert response.status_code == 302
    assert response["Location"] == f"{_login_url_for(name)}?next={url}"


@pytest.mark.django_db
def test_htmx_request_without_session_gets_hx_redirect(client):
    response = client.get(reverse("core:home"), headers={"HX-Request": "true"})
    assert response.status_code == 401
    assert response["HX-Redirect"] == reverse("accounts:login")


def test_health_is_public(client):
    response = client.get(reverse("core:health"))
    assert response.status_code == 200
    assert response.content == b"ok"


@pytest.mark.django_db
def test_home_with_personal_session(personal_account, login_as):
    client = login_as(personal_account, "personal")
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert "Plataforma del C.R.I.S." in response.content.decode()
