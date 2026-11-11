"""T-M01-47: pàgines 404 i 500 pròpies, coherents amb la 403.

- La 404 és també la resposta «no trobat» sense permís (`apps/core/permissions.py`): la mateixa
  pàgina per a una adreça que no existeix, per a un objecte que no existeix i per a un objecte
  que existeix però que el compte no pot veure. No diu l'adreça demanada, ni el permís que
  falta, ni el missatge intern de l'excepció.
- La 500 no depèn de la base de dades ni de la petició: és la mateixa per a tothom i no mostra
  cap detall de l'error.

Només dades inventades.
"""

import re

import pytest
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.urls_errors import INTERNAL_DETAIL
from apps.members.tests.test_route_permissions import a_member

ADMIN = settings.ADMIN_URL_PATH
URLS = "apps.core.tests.urls_errors"
NOT_FOUND_TITLE = "No s'ha trobat la pàgina"
ERROR_TITLE = "Hi ha hagut un error"


@pytest.fixture(autouse=True)
def _production_like(settings):
    settings.DEBUG = False  # amb DEBUG, Django mostra les seves pàgines tècniques


def body(response):
    """El cos sense el testimoni CSRF, que canvia a cada resposta."""
    html = response.content.decode()
    return re.sub(r'(X-CSRFToken": "|name="csrfmiddlewaretoken" value=")[^"]*', r"\1", html)


def template_names(response):
    return [template.name for template in response.templates]


# --- 404 ----------------------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize("path", ["/no-existeix/", f"/{ADMIN}/no-existeix/"])
def test_404_without_session_uses_the_own_template_and_reveals_nothing(client, path):
    response = client.get(path)
    assert response.status_code == 404
    assert "404.html" in template_names(response)
    html = response.content.decode()
    assert NOT_FOUND_TITLE in html
    assert "no-existeix" not in html  # l'adreça demanada no es repeteix
    # Sense sessió d'administració no es diu que l'adreça sigui de l'administració.
    assert 'class="zona-soci"' in html and "Administració" not in html
    assert f'href="{reverse("core:home")}"' in html


@pytest.mark.django_db
def test_404_is_the_same_without_session_whatever_the_address(client):
    assert body(client.get("/no-existeix/")) == body(client.get(f"/{ADMIN}/una-altra/"))


def test_404_in_the_personal_area_is_the_same_for_a_missing_address_and_a_foreign_object(
    login_as, personal_account
):
    """Àrea de socis amb sessió: l'objecte d'un altre soci (CA-M01-25) respon com una adreça
    que no existeix."""
    client = login_as(personal_account, AREA_PERSONAL)
    foreign = client.get(reverse("members:fee_detail", kwargs={"fee_id": 987654}))
    unknown = client.get("/no-existeix/")
    assert foreign.status_code == unknown.status_code == 404
    assert "404.html" in template_names(foreign)
    html = foreign.content.decode()
    assert NOT_FOUND_TITLE in html and 'class="zona-soci"' in html
    assert "987654" not in html
    main = re.compile(r"<main.*</main>", re.S)
    assert main.search(body(foreign)).group(0) == main.search(body(unknown)).group(0)


def test_404_in_the_administration_does_not_tell_whether_the_object_exists(login_as, make_admin):  # noqa: F811
    """Administració amb sessió: sense permís, un soci que existeix i un que no existeix donen
    exactament la mateixa pàgina, que no diu quin permís falta."""
    member = a_member("Existeix")
    client = login_as(make_admin(), AREA_ADMIN)  # compte operatiu sense cap rol
    existing = client.get(reverse("administration:member_detail", kwargs={"pk": member.pk}))
    unknown = client.get(reverse("administration:member_detail", kwargs={"pk": 987654}))
    assert existing.status_code == unknown.status_code == 404
    assert "404.html" in template_names(existing)
    assert body(existing) == body(unknown)
    html = existing.content.decode()
    assert NOT_FOUND_TITLE in html
    assert 'class="zona-admin"' in html
    assert f'href="{reverse("administration:home")}"' in html
    assert "Existeix" not in html and "members." not in html and "permís" not in html


def test_404_with_permission_and_a_missing_object(login_as, make_admin):  # noqa: F811
    client = login_as(make_admin("secretary"), AREA_ADMIN)
    response = client.get(reverse("administration:member_detail", kwargs={"pk": 987654}))
    assert response.status_code == 404
    assert "404.html" in template_names(response)
    assert "987654" not in response.content.decode()


@pytest.mark.django_db
@pytest.mark.urls(URLS)
def test_404_never_shows_the_message_of_the_exception(client):
    response = client.get("/prova-no-trobat/")
    assert response.status_code == 404
    html = response.content.decode()
    assert NOT_FOUND_TITLE in html
    assert INTERNAL_DETAIL not in html and "prova-no-trobat" not in html


# --- 500 ----------------------------------------------------------------------------------------


def error_page(client):
    client.raise_request_exception = False
    return client.get("/prova-error-500/")


def assert_error_page(response):
    assert response.status_code == 500
    assert template_names(response) == ["500.html"]
    html = response.content.decode()
    assert ERROR_TITLE in html and '<html lang="ca">' in html
    for leak in (INTERNAL_DETAIL, "RuntimeError", "Traceback", "prova-error-500", "broken"):
        assert leak not in html
    assert f"/{ADMIN}/" not in html  # la ruta de l'administració tampoc
    return html


@pytest.mark.urls(URLS)
def test_500_works_without_the_database(client):
    """Sense la marca `django_db`, qualsevol consulta faria fallar la prova: la 500 no en fa."""
    assert_error_page(error_page(client))


@pytest.mark.urls(URLS)
def test_500_is_the_same_with_and_without_session_in_both_areas(
    client,
    login_as,
    personal_account,
    make_admin,  # noqa: F811
):
    anonymous = assert_error_page(error_page(client))
    personal = assert_error_page(error_page(login_as(personal_account, AREA_PERSONAL)))
    client.logout()
    admin = assert_error_page(error_page(login_as(make_admin("administrator"), AREA_ADMIN)))
    assert anonymous == personal == admin
    assert personal_account.login not in anonymous


def test_500_template_stands_alone():
    """Es dibuixa sense context i sense cap altra plantilla: si la base falla, la 500 no."""
    source = (settings.BASE_DIR / "templates" / "500.html").read_text(encoding="utf-8")
    assert "{% extends" not in source and "{% include" not in source
    assert "csrf_token" not in source and "request" not in source and "user" not in source
    assert ERROR_TITLE in render_to_string("500.html")
