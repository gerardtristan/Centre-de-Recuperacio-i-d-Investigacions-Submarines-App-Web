"""Ramillete, la navegació de l'àrea del soci al mòbil (T-DX-08): a baix, les pàgines que més
es fan servir i el botó «Més», que s'obre en ventall amb les rares; Esc i tocar fora el tanquen,
i «Surt» es queda a la capçalera. A partir de 600 px no es veu i queda la navegació de la capçalera.
"""

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

pytestmark = pytest.mark.e2e

MOBILE = {"width": 390, "height": 844}


def login_personal(page, live_server, builder, member):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()


def bar(page):
    return page.get_by_role("navigation", name="Compte personal (mòbil)")


def test_mobile_bar_and_the_more_fan(page, live_server, builder, member, review, page_checks):
    page.set_viewport_size(MOBILE)
    login_personal(page, live_server, builder, member)
    expect(bar(page)).to_be_visible()
    # La capçalera només deixa «Surt» (un sol «Surt» per pantalla).
    header = page.get_by_role("navigation", name="Compte personal", exact=True)
    expect(header.get_by_role("link", name="Inici")).to_be_hidden()
    expect(page.get_by_role("button", name="Surt")).to_be_visible()
    expect(bar(page).get_by_role("link", name="Inici")).to_have_attribute("aria-current", "page")
    more = bar(page).get_by_role("button", name="Més opcions")
    expect(bar(page).get_by_role("link", name="Baixa")).to_be_hidden()

    more.click()
    expect(more).to_have_attribute("aria-expanded", "true")
    expect(bar(page).get_by_role("link", name="Canvi de tipus")).to_be_focused()
    review("ventall-obert")
    page.set_viewport_size(MOBILE)  # la captura acaba a 1280 px
    page.keyboard.press("Escape")
    expect(more).to_have_attribute("aria-expanded", "false")
    expect(more).to_be_focused()

    # Tocar fora tanca el ventall.
    more.click()
    page.mouse.click(10, 200)
    expect(more).to_have_attribute("aria-expanded", "false")

    bar(page).get_by_role("link", name="Quotes").click()
    expect(bar(page).get_by_role("link", name="Quotes")).to_have_attribute("aria-current", "page")
    # La barra no tapa el final de la pàgina.
    padding = page.evaluate("parseFloat(getComputedStyle(document.body).paddingBottom)")
    assert padding >= bar(page).bounding_box()["height"] - 1
    assert bar(page).get_by_role("button", name="Surt").count() == 0


def test_wide_screens_keep_the_header_navigation(page, live_server, builder, member, page_checks):
    login_personal(page, live_server, builder, member)
    expect(bar(page)).to_be_hidden()
    expect(page.get_by_role("navigation", name="Compte personal", exact=True)).to_be_visible()
