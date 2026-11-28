"""T-DX-170 (design-system §6.29): el menú desat de la web pública surt a la capçalera de qui no ha
entrat, amb 6 enllaços i «Més» a l'escriptori i 3 al mòbil (cada enllaç visible una sola vegada a
cada mida), i no surt amb sessió (el compte personal té la seva navegació). Dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.core.models import Role
from apps.website import menus
from apps.website.models import Menu, MenuItem

pytestmark = pytest.mark.django_db


@pytest.fixture
def menu_de_vuit(make_admin):
    editor = make_admin(Role.Code.PRESIDENT)
    menu, _ = Menu.objects.get_or_create(code=menus.MAIN, defaults={"name": "Menú principal"})
    for n in range(1, 9):
        menus.save_item(
            None, actor=editor, menu=menu, label=f"Enllaç {n}", url="/noticies/", order=n
        )


def test_the_visitor_sees_the_saved_menu_split_by_width(client, menu_de_vuit):
    html = client.get(reverse("website:news_list")).content.decode()
    assert '<nav class="menu-public"' in html
    assert html.count('class="nav-escriptori"') == 3  # el 4t, el 5è i el 6è, només a l'escriptori
    assert html.count('class="nav-no-escriptori"') == 3  # les seves còpies a «Més», només al mòbil
    assert html.count(">Enllaç 7<") == 1 and html.count(">Enllaç 1<") == 1
    assert 'aria-current="page"' in html  # /noticies/ és la pàgina actual


def test_with_a_session_the_public_menu_is_not_shown(
    client, login_as, personal_account, menu_de_vuit
):
    login_as(personal_account, AREA_PERSONAL)
    assert (
        '<nav class="menu-public"' not in client.get(reverse("website:news_list")).content.decode()
    )


def test_an_empty_menu_paints_nothing(client):
    MenuItem.objects.all().delete()  # la migració en sembra uns quants
    assert (
        '<nav class="menu-public"' not in client.get(reverse("website:news_list")).content.decode()
    )
