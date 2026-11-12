"""Ajuda per instal·lar la web a l'iPhone (decisió 041; 079, A-28 i RN-M01-96; T-M01-45).

Pàgina pública i només de text: els passos de Safari i què cal saber (sense botiga, sense
notificacions, carnet sense connexió que s'esborra en sortir). No mostra cap dada.

Només dades inventades.
"""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.core.tests.conftest import main_of
from apps.core.tests.test_access import PUBLIC_ROUTES

URL_NAME = "core:install_help_iphone"


def test_route_is_declared_public():
    assert URL_NAME in PUBLIC_ROUTES


@pytest.mark.django_db
def test_without_session_it_shows_the_safari_steps(client):
    response = client.get(reverse(URL_NAME))
    assert response.status_code == 200
    html = main_of(response.content.decode())
    assert "<ol" in html and "Safari" in html
    assert "Afegeix a la pantalla d" in html
    assert "notificacions" in html  # decisió 041: cap notificació al mòbil
    assert "s&#x27;esborra" in html or "s'esborra" in html  # RN-M01-96: en sortir
    assert "<form" not in html and "<script" not in html


@pytest.mark.django_db
def test_only_get(client):
    assert client.post(reverse(URL_NAME)).status_code == 405


def test_with_a_personal_session_it_shows_nothing_of_the_account(login_as, personal_account):
    html = main_of(
        login_as(personal_account, AREA_PERSONAL).get(reverse(URL_NAME)).content.decode()
    )
    assert personal_account.login not in html
    assert personal_account.person.first_name not in html


@pytest.mark.django_db
def test_personal_login_links_to_it_and_admin_login_does_not(client):
    link = f'href="{reverse(URL_NAME)}"'
    assert link in client.get(reverse("accounts:login")).content.decode()
    assert link not in client.get(reverse("administration:login")).content.decode()
