"""Pantalles «En construcció» al navegador (design-system §16): cada pantalla, amb l'etiqueta
visible i captures a 1280, 390 i 320 px, en clar i en fosc. Es troben soles."""

import pytest
from playwright.sync_api import expect

from apps.core.models import Role, RolePermission
from apps.core.under_construction import PERMISSION
from apps.previews.screens import discover
from conftest import PASSWORD

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("name", [name for name, _ in discover()])
def test_under_construction_screen(
    name, page, live_server, builder, member, settings, review, page_checks
):
    settings.SHOW_UNDER_CONSTRUCTION = True
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/en-construccio/{name.replace('_', '-')}/")
    expect(page.locator(".en-construccio").first).to_be_visible()
    expect(page.get_by_role("heading", level=1)).to_be_visible()
    review(f"en-construccio-{name}")


def test_admin_with_dx1_reaches_the_screens_from_the_menu(page, live_server, settings, review):
    """Com a producció (sense SHOW_UNDER_CONSTRUCTION): un compte d'administrador amb DX1 (P-90)
    hi arriba pel menú i les pantalles s'obren dins l'administració (T-DX-50)."""
    settings.SHOW_UNDER_CONSTRUCTION = False
    RolePermission.objects.create(
        role=Role.objects.get(code=Role.Code.TREASURER), permission_code=PERMISSION, scope="all"
    )
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    sidebar = page.locator("#barra-lateral")
    menu_entry(page, "Pantalles en construcció").click()
    expect(page.get_by_role("heading", level=1)).to_have_text("Pantalles en construcció")
    page.get_by_role("main").get_by_role("link").first.click()
    expect(page.locator(".en-construccio").first).to_be_visible()
    expect(sidebar.get_by_role("link", name="Pantalles en construcció")).to_have_attribute(
        "aria-current", "page"
    )
    review("en-construccio-des-del-menu")
