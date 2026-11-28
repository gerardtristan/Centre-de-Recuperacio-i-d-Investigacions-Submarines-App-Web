"""Menú de la web pública al navegador (T-DX-170): un visitant obre una pàgina pública amb un menú
de vuit enllaços desat i obre «Més». Captures a 1280, 1024, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.website import menus
from apps.website.models import Menu, MenuItem

from .conftest import make_admin

pytestmark = pytest.mark.e2e

ETIQUETES = (
    "Inici",
    "Qui som",
    "Cursos",
    "Sortides",
    "Projectes",
    "Notícies",
    "Galeria",
    "Contacte",
)


def test_the_visitor_opens_more_in_the_public_menu(page, live_server, transactional_db, review):
    editor = make_admin("presidencia.prova", "president")
    MenuItem.objects.all().delete()  # la migració en sembra uns quants
    menu, _ = Menu.objects.get_or_create(code=menus.MAIN, defaults={"name": "Menú principal"})
    for n, label in enumerate(ETIQUETES, start=1):
        url = "/noticies/" if label == "Notícies" else "/ajuda/"
        menus.save_item(None, actor=editor, menu=menu, label=label, url=url, order=n)
    page.goto(f"{live_server.url}{reverse('website:news_list')}")
    nav = page.get_by_role("navigation", name="Navegació principal")
    expect(nav.get_by_role("link", name="Inici")).to_be_visible()
    review("menu-public")
    nav.locator("summary", has_text="Més").click()
    expect(nav.get_by_role("link", name="Contacte")).to_be_visible()
    review("menu-public-mes")
