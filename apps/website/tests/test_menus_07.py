"""Menús, capçalera i peu de la web pública (T-M07-21; addenda 106, decisió 034): 6 enllaços i
«Més», submenús d'un nivell, enllaç extern només `https:`, WP9 al servidor i registre. Només
dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import Error, connection, transaction
from django.http import Http404
from django.template import Context, Template
from django.test import RequestFactory

from apps.core.models import AppendOnlyError, AuditEntry, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.website import contact, menus
from apps.website.models import Menu, MenuItem, Page, SiteChrome

pytestmark = pytest.mark.django_db
R = Role.Code


@pytest.fixture
def editor(make_admin):  # noqa: F811
    return make_admin(R.PRESIDENT)  # WP9 d'inici, com WP1


@pytest.fixture
def menu():
    return Menu.objects.create(code="prova", name="Menú de prova")


def _render(code, path="/"):
    request = RequestFactory().get(path)
    menu = menus.public_menu(code)
    return Template("{% include 'website/_menu_public.html' %}").render(
        Context({"menu": menu, "current": request.path})
    )


def test_criteri_six_links_and_more_with_a_submenu_and_an_external_link(editor, menu):
    for n in range(1, 7):
        menus.save_item(
            None, actor=editor, menu=menu, label=f"Enllaç {n}", url="/noticies/", order=n
        )
    group = menus.save_item(None, actor=editor, menu=menu, label="El club", order=7)
    menus.save_item(None, actor=editor, menu=menu, parent=group, label="Ajuda", url="/ajuda/")
    menus.save_item(
        None,
        actor=editor,
        menu=menu,
        label="Federació",
        url="https://federacio.exemple.cat/",
        order=8,
    )
    result = menus.public_menu("prova")
    assert [i.label for i in result["links"]] == [f"Enllaç {n}" for n in range(1, 7)]
    assert [i.label for i in result["more"]] == ["El club", "Federació"]
    assert [s.label for s in result["more"][0].subitems] == ["Ajuda"]
    html = _render("prova")
    assert "Més</summary>" in html and 'href="/ajuda/"' in html
    assert 'href="https://federacio.exemple.cat/" rel="noopener noreferrer"' in html


@pytest.mark.parametrize(
    "url",
    [
        "http://exemple.cat/",
        "javascript:alert(1)",
        "//exemple.cat/",
        "/\\exemple.cat/",
        "/no-existeix-aquesta-ruta/",
        "mailto:cris@cris.es",
        "https://",
    ],
)
def test_only_https_or_an_existing_route_is_accepted(editor, menu, url):
    with pytest.raises(ValidationError):
        menus.save_item(None, actor=editor, menu=menu, label="Enllaç", url=url)
    assert not MenuItem.objects.filter(menu=menu).exists()


@pytest.mark.parametrize("url", ["https://exemple.cat/cami?a=1", "/noticies/", "/"])
def test_https_and_existing_routes_are_saved(editor, menu, url):
    assert menus.save_item(None, actor=editor, menu=menu, label="Enllaç", url=url).href == url


def test_a_page_and_an_address_at_once_are_rejected(editor, menu):
    page = Page.objects.get(slug="qui-som")
    with pytest.raises(ValidationError):
        menus.save_item(None, actor=editor, menu=menu, label="Qui som", page=page, url="/ajuda/")


def test_submenus_have_a_single_level(editor, menu):
    top = menus.save_item(None, actor=editor, menu=menu, label="Grup")
    sub = menus.save_item(None, actor=editor, menu=menu, parent=top, label="A", url="/ajuda/")
    with pytest.raises(ValidationError):
        menus.save_item(None, actor=editor, menu=menu, parent=sub, label="B", url="/ajuda/")
    with pytest.raises(ValidationError):  # un enllaç amb submenú no pot anar dins d'un altre
        other = menus.save_item(None, actor=editor, menu=menu, label="Un altre")
        menus.save_item(top, actor=editor, parent=other)
    with pytest.raises(ValidationError):  # un enllaç d'un submenú porta destí
        menus.save_item(None, actor=editor, menu=menu, parent=top, label="Buit")


def test_unpublished_pages_empty_groups_and_switched_off_screens_are_not_shown(editor, menu):
    page = Page.objects.get(slug="qui-som")
    menus.save_item(None, actor=editor, menu=menu, label="Qui som", page=page, order=1)
    menus.save_item(None, actor=editor, menu=menu, label="Grup buit", order=2)
    menus.save_item(None, actor=editor, menu=menu, label="Contacte", url="/contacte/", order=3)
    assert menus.public_menu("prova")["links"] == []
    assert _render("prova").strip() == ""
    page.status = Page.Status.PUBLISHED
    page.save()
    Setting.objects.filter(key=contact.ENABLED).update(initial_value=True)
    assert [i.href for i in menus.public_menu("prova")["links"]] == ["/qui-som/", "/contacte/"]
    assert 'href="/qui-som/" aria-current="page"' in _render("prova", "/qui-som/")


def test_the_initial_main_menu_and_the_template_tag():
    labels = MenuItem.objects.filter(menu__code=menus.MAIN).values_list("label", flat=True)
    assert list(labels) == ["Inici", "Notícies", "Ajuda"]  # mínim (P-700)
    request = RequestFactory().get("/noticies/")
    html = Template("{% load website_menu %}{% menu_public %}").render(
        Context({"request": request})
    )
    assert 'href="/"' in html and 'href="/ajuda/"' in html
    assert 'href="/noticies/" aria-current="page"' in html and "Més" not in html


def test_wp9_is_checked_on_the_server_and_nothing_is_saved(make_admin, editor, menu):  # noqa: F811
    item = menus.save_item(None, actor=editor, menu=menu, label="Inici", url="/")
    other = make_admin(R.SECRETARY)
    with pytest.raises(Http404):
        menus.save_item(None, actor=other, menu=menu, label="Altre", url="/")
    with pytest.raises(Http404):
        menus.save_item(item, actor=other, label="Canviat")
    with pytest.raises(Http404):
        menus.remove_item(item, actor=other)
    with pytest.raises(Http404):
        menus.save_chrome(actor=other, header_text="Capçalera")
    assert [i.label for i in MenuItem.objects.filter(menu=menu)] == ["Inici"]
    assert not SiteChrome.objects.exists()


def test_saving_and_removing_items_are_recorded_with_the_previous_value(editor, menu):
    item = menus.save_item(None, actor=editor, menu=menu, label="Inici", url="/")
    menus.save_item(item, actor=editor, label="Portada", url="/")
    menus.remove_item(item, actor=editor)
    entries = AuditEntry.objects.filter(target_id=str(item.pk)).order_by("pk")
    assert [(e.action, e.field, e.old_value, e.new_value) for e in entries] == [
        (menus.ACTION_ITEM_SAVED, "menu", None, menu.pk),
        (menus.ACTION_ITEM_SAVED, "label", None, "Inici"),
        (menus.ACTION_ITEM_SAVED, "url", None, "/"),
        (menus.ACTION_ITEM_SAVED, "label", "Inici", "Portada"),
        (menus.ACTION_ITEM_REMOVED, "label", "Portada", None),
    ]
    assert {e.actor_account_id for e in entries} == {editor.pk}


def test_an_item_with_a_submenu_is_not_removed(editor, menu):
    top = menus.save_item(None, actor=editor, menu=menu, label="Grup")
    menus.save_item(None, actor=editor, menu=menu, parent=top, label="A", url="/ajuda/")
    with pytest.raises(ValidationError):
        menus.remove_item(top, actor=editor)
    assert MenuItem.objects.filter(menu=menu).count() == 2


def test_header_and_footer_versions_are_recorded_and_append_only(editor):
    first = menus.save_chrome(actor=editor, header_text=" Club de busseig ", note="Primera")
    second = menus.save_chrome(actor=editor, header_text="C.R.I.S.", footer_text="<b>Peu</b>")
    assert menus.current_chrome() == second and second.number == 2
    assert first.header_text == "Club de busseig" and second.footer_text == "<b>Peu</b>"
    entries = AuditEntry.objects.filter(action=menus.ACTION_CHROME_SAVED).order_by("pk")
    assert [(e.old_value, e.new_value, e.reason) for e in entries] == [
        (None, 1, "Primera"), (1, 2, ""),
    ]  # fmt: skip
    first.header_text = "canviada"
    with pytest.raises(AppendOnlyError):
        first.save()
    for sql in ("UPDATE website_sitechrome SET note = 'x'", "DELETE FROM website_sitechrome"):
        with pytest.raises(Error), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(sql)
    assert SiteChrome.objects.count() == 2


def test_an_empty_header_is_rejected(editor):
    with pytest.raises(ValidationError):
        menus.save_chrome(actor=editor, header_text="   ")
    assert not SiteChrome.objects.exists()
