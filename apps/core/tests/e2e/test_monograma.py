"""Monograma (T-DX-18): l'avatar per defecte del soci, de la llavor, a la portada i al perfil."""

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

pytestmark = pytest.mark.e2e


def test_member_sees_the_default_avatar_on_home_and_profile(
    page, live_server, builder, member, review, page_checks
):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/")
    avatar = page.locator(".oleaje-portada svg.monograma")
    expect(avatar).to_be_visible()
    expect(avatar).to_have_attribute("aria-hidden", "true")
    drawn = avatar.evaluate("e => e.outerHTML")
    review("portada-monograma")
    page.goto(f"{live_server.url}/socis/perfil/")
    profile = page.locator(".monograma-titol svg.monograma")
    expect(profile).to_be_visible()
    # El mateix dibuix a les dues pantalles: surt de la llavor, no de la pàgina.
    assert profile.evaluate("e => e.outerHTML") == drawn
    review("perfil-monograma")
