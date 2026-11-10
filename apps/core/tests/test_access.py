"""Sessió obligatòria per defecte (RN-40)."""

import uuid

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse

# Rutes públiques declarades. Afegir-ne una obliga a canviar aquesta llista a propòsit.
PUBLIC_ROUTES = {
    "core:health",
    # Service worker de la web instal·lable (T-M01-21): la pàgina d'entrada també el registra
    # i el fitxer no porta cap dada.
    "core:service_worker",
    # Enllaç signat local (imita Scaleway fora de producció): l'enllaç és la credencial.
    "core:local_private_file",
    "accounts:login",
    "accounts:login_totp",
    "accounts:logout",
    # Enllaços del correu del compte personal: el testimoni és la credencial (RN-18).
    "accounts:verify_email",
    "accounts:verify_email_link",
    "accounts:password_reset",
    "accounts:password_reset_link",
    "accounts:password_reset_request",
    "accounts:resend_verification",
    # Confirmació del correu d'entrada nou (RN-M01-79): el testimoni lliga el compte i l'adreça.
    "accounts:change_email",
    "accounts:change_email_link",
    "administration:login",
    "administration:login_totp",
    "administration:totp_enrol",
    # Canvi de la credencial temporal (CA-08.1): dins l'entrada, abans de tenir sessió.
    "administration:change_temporary_credential",
    "administration:logout",
    # Formulari «Fer-se soci» (RN-40, M01-8): P1 és del visitant.
    "members:join",
    # Verificació del carnet (P15, M01-8): qualsevol persona; el testimoni no dona cap dada.
    "members:card_verify",
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


@pytest.mark.django_db
def test_each_account_greets_only_its_own_person(make_person, login_as):
    """Cada compte veu el nom de la seva persona i mai el d'una altra (revisió de la
    T-M01-38). Una persona sense compte creada primer fa que els ids de compte i de persona
    no coincideixin: triar la persona per l'id del compte fallaria."""
    from apps.accounts.models import Account

    make_person(first_name="Sense", last_name="Compte")
    accounts = {}
    for first, last, login in [("Biel", "Mero", "biel@example.org"), ("Núria", "Pop", "n@x.org")]:
        account = Account.objects.create_personal(
            make_person(first, last), login, "contrasenya-de-proves-1954"
        )
        account.status = Account.Status.ACTIVE
        account.save()
        accounts[first] = account
    assert all(a.pk != a.person_id for a in accounts.values())
    for own, other in [("Biel", "Núria"), ("Núria", "Biel")]:
        text = login_as(accounts[own], "personal").get(reverse("core:home")).content.decode()
        assert f"Hola, {own}." in text
        assert other not in text
