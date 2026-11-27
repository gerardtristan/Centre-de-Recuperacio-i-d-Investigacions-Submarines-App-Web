"""Pantalla del menú, la capçalera i el peu (T-M07-21 b; WP9; addenda 106). Només dades
inventades."""

import pytest
from django.urls import reverse

from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.core.tests.test_guest_links import admin_client
from apps.website import menus
from apps.website.models import MenuItem, SiteChrome

pytestmark = pytest.mark.django_db
R = Role.Code
LIST = reverse("administration:website_menu")
ADD = reverse("administration:website_menu_item_add")


def _main(label):
    return MenuItem.objects.get(menu__code=menus.MAIN, label=label)


def test_wp9_adds_a_submenu_and_an_external_link_and_removes_one(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.PRESIDENT))
    assert client.get(LIST).status_code == 200
    group = {"label": "El club", "url": "", "order": 7}
    assert client.post(ADD, group)["Location"] == LIST
    parent = _main("El club").pk
    sub = {"label": "Federació", "url": "https://federacio.exemple.cat/", "parent": parent}
    sub["order"] = 1
    assert client.post(ADD, sub)["Location"] == LIST
    assert _main("Federació").parent == _main("El club")
    html = client.get(LIST).content.decode()
    assert "https://federacio.exemple.cat/" in html and "Treu «Federació»" in html
    remove = reverse("administration:website_menu_item_remove", args=[_main("Federació").pk])
    client.post(remove)
    assert not MenuItem.objects.filter(label="Federació").exists()


@pytest.mark.parametrize("url", ["http://exemple.cat/", "javascript:alert(1)", "//exemple.cat/"])
def test_an_address_that_is_not_https_or_a_route_shows_the_error(make_admin, url):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    response = client.post(ADD, {"label": "Fora", "url": url, "order": 1})
    assert response.status_code == 200
    assert "Només una adreça de la plataforma que existeixi" in response.content.decode()
    assert not MenuItem.objects.filter(label="Fora").exists()


def test_editing_an_item_and_saving_the_header_and_footer(make_admin):  # noqa: F811
    client = admin_client(make_admin(R.ADMINISTRATOR))
    edit = reverse("administration:website_menu_item_edit", args=[_main("Ajuda").pk])
    client.post(edit, {"label": "Preguntes", "url": "/ajuda/", "order": 3})
    assert _main("Preguntes").url == "/ajuda/"
    data = {"header_text": "Club de busseig", "footer_text": "<script>x</script>", "note": "Prova"}
    assert client.post(LIST, data)["Location"] == LIST
    assert menus.current_chrome().footer_text == "<script>x</script>"
    html = client.get(LIST).content.decode()
    assert "Versió 1" in html and "<script>x</script>" not in html  # escapat


def test_an_item_with_a_submenu_is_not_removed_and_the_error_is_shown(make_admin):  # noqa: F811
    editor = make_admin(R.ADMINISTRATOR)
    top = menus.save_item(None, actor=editor, menu=_main("Inici").menu, label="Grup", order=9)
    menus.save_item(None, actor=editor, menu=top.menu, parent=top, label="A", url="/ajuda/")
    client = admin_client(editor)
    response = client.post(reverse("administration:website_menu_item_remove", args=[top.pk]))
    assert "treu primer els enllaços de dins" in client.get(response["Location"]).content.decode()
    assert MenuItem.objects.filter(pk=top.pk).exists()


@pytest.mark.parametrize("role", [R.SECRETARY, R.BOARD, R.COMMUNICATIONS_MANAGER])
def test_without_wp9_every_screen_is_not_found_and_nothing_is_saved(make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    item = _main("Inici")
    edit = reverse("administration:website_menu_item_edit", args=[item.pk])
    remove = reverse("administration:website_menu_item_remove", args=[item.pk])
    assert client.get(LIST).status_code == 404
    assert client.post(LIST, {"header_text": "X"}).status_code == 404
    assert client.post(ADD, {"label": "X", "url": "/", "order": 1}).status_code == 404
    assert client.post(edit, {"label": "X", "url": "/", "order": 1}).status_code == 404
    assert client.post(remove).status_code == 404
    assert _main("Inici") and not SiteChrome.objects.exists()
    assert MenuItem.objects.filter(menu__code=menus.MAIN).count() == 3
