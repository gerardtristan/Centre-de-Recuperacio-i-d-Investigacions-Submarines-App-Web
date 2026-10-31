"""Sessió obligatòria per defecte (RN-40)."""

import uuid

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse

from apps.core.models import Person

# Rutes públiques declarades. Afegir-ne una obliga a canviar aquesta llista a propòsit.
PUBLIC_ROUTES = {"core:health", "core:login"}

SAMPLE_VALUES = {"int": 1, "str": "x", "slug": "x", "path": "x", "uuid": uuid.UUID(int=0)}


def _routes(patterns=None, namespace=""):
    """Totes les rutes amb nom, amb el nom complet i valors d'exemple per als paràmetres."""
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
    assert response["Location"] == f"{reverse('core:login')}?next={url}"


def test_htmx_request_without_session_gets_hx_redirect(client):
    response = client.get(reverse("core:home"), headers={"HX-Request": "true"})
    assert response.status_code == 401
    assert response["HX-Redirect"] == reverse("core:login")


def test_health_is_public(client):
    response = client.get(reverse("core:health"))
    assert response.status_code == 200
    assert response.content == b"ok"


def test_login_page_is_public(client):
    response = client.get(reverse("core:login"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_home_with_session(client, django_user_model):
    person = Person.objects.create(first_name="Anna", origin=Person.Origin.WEB)
    account = django_user_model.objects.create_personal(person, "anna@example.org")
    account.status = account.Status.ACTIVE
    account.save()
    client.force_login(account)
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert "Plataforma del C.R.I.S." in response.content.decode()
