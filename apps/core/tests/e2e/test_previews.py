"""Pantalles «En construcció» al navegador (design-system §16): cada pantalla, amb l'etiqueta
visible i captures a 1280, 390 i 320 px, en clar i en fosc. Es troben soles."""

import pytest
from playwright.sync_api import expect

from apps.previews.screens import discover
from conftest import PASSWORD

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
