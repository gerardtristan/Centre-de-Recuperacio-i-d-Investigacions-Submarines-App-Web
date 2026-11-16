"""Oleaje a la portada de l'àrea del soci (T-DX-17): la capçalera amb la vora en ona i, a sota, el
bloc de la quota i del carnet, que arriba al seu lloc en desplaçar."""

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

pytestmark = pytest.mark.e2e


def test_member_home_has_the_wave_header_and_the_fee_block(
    page, live_server, builder, member, review, page_checks
):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/")
    expect(page.locator(".oleaje-portada svg.oleaje-vora")).to_be_attached()
    block = page.locator(".oleaje-seccio")
    block.scroll_into_view_if_needed()
    expect(block.get_by_role("heading", name="La teva quota")).to_be_visible()
    expect(block.get_by_role("link", name="El meu carnet")).to_be_visible()
    # Un cop a la vista, el bloc és al seu lloc (sense desplaçament ni transparència).
    page.wait_for_function(
        "() => getComputedStyle(document.querySelector('.oleaje-seccio')).opacity === '1'"
    )
    review("portada-oleaje")
