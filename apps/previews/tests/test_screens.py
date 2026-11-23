"""Pantalles «En construcció» (design-system §6.9 i §16): cadascuna es veu amb l'etiqueta, només
accepta GET i, sense accés, respon 404. Es troben soles (apps/previews/screens): una pantalla nova
queda coberta sense tocar aquesta prova."""

import pytest
from django.template.loader import get_template
from django.test import override_settings
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.previews.screens import discover

pytestmark = pytest.mark.django_db
SCREENS = [name for name, _ in discover()]


def test_there_is_at_least_one_screen():
    assert "novetats" in SCREENS


def test_a_screen_that_already_works_is_no_longer_under_construction():
    """§6.9: cap pantalla en construcció al costat de la real. Rols i permisos és a
    `/gestio/permisos/` (T-RP-03), i la de prova es retira (T-DX-74). Les del 02 (T-DX-95): la
    fitxa i la inscripció són a `/activitats/` (#497, #498) i «Activitats» del soci és «Les meves
    activitats» (`activities:mine`, #499)."""
    for name in (
        "rols_permisos",
        "activitats",
        "activitats_per_a_tu",
        "fitxa_activitat",
        "inscripcio",
    ):
        assert name not in SCREENS


@pytest.mark.parametrize("name", SCREENS)
def test_each_screen_declares_a_title_and_has_its_template(name):
    module = dict(discover())[name]
    assert str(module.TITLE)
    assert get_template(f"previews/{name}.html")


@override_settings(SHOW_UNDER_CONSTRUCTION=True)
@pytest.mark.parametrize("name", SCREENS)
def test_each_screen_shows_the_label_and_only_accepts_get(name, login_as, personal_account):
    client = login_as(personal_account, AREA_PERSONAL)
    response = client.get(reverse(f"previews:{name}"))
    html = response.content.decode()
    assert response.status_code == 200
    assert 'class="en-construccio"' in html and "aria-describedby=" in html
    assert "style=" not in html.split('id="contingut"', 1)[1]
    assert client.post(reverse(f"previews:{name}")).status_code == 405


@override_settings(SHOW_UNDER_CONSTRUCTION=False)
@pytest.mark.parametrize("name", [*SCREENS, None])
def test_without_access_every_screen_and_the_index_are_not_found(name, login_as, personal_account):
    client = login_as(personal_account, AREA_PERSONAL)
    url = reverse(f"previews:{name}") if name else reverse("previews:index")
    assert client.get(url).status_code == 404


@override_settings(SHOW_UNDER_CONSTRUCTION=True)
def test_the_index_links_every_screen(login_as, personal_account):
    html = login_as(personal_account, AREA_PERSONAL).get(reverse("previews:index")).content.decode()
    assert all(reverse(f"previews:{name}") in html for name in SCREENS)
