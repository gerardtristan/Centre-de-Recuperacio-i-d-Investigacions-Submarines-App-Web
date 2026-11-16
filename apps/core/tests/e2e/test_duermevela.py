"""Duermevela, el motor de tema (T-DX-04): la tria passa a les altres pestanyes sense recarregar,
la barra del navegador pren el color de fons del tema i, amb moviment reduït, el canvi és
directe. Es prova a la pàgina d'entrada, que és pública i porta el selector.
"""

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

THEME = "document.documentElement.getAttribute('data-theme')"
BAR = "document.querySelector('meta[name=\"theme-color\"]')?.content"
BACKGROUND = "getComputedStyle(document.documentElement).getPropertyValue('--c-fons').trim()"


def choose(page, label):
    page.locator(".selector-tema label", has_text=label).click()


def test_the_choice_reaches_the_other_tabs_and_the_browser_bar(
    page, context, live_server, page_checks
):
    first = page
    first.goto(f"{live_server.url}/entrar/")
    second = context.new_page()
    second.goto(f"{live_server.url}/entrar/")
    light_bar = first.evaluate(BAR)
    assert light_bar == first.evaluate(BACKGROUND)

    choose(first, "Fosc")
    expect(first.locator("html")).to_have_attribute("data-theme", "dark")
    # L'altra pestanya ho rep per l'esdeveniment «storage», sense recarregar.
    expect(second.locator("html")).to_have_attribute("data-theme", "dark")
    expect(second.locator('.selector-tema input[value="dark"]')).to_be_checked()
    second.wait_for_function(f"{BAR} === {BACKGROUND}")
    assert second.evaluate(BAR) != light_bar

    choose(first, "Sistema")
    second.wait_for_function(f"{THEME} === null")
    expect(second.locator('.selector-tema input[value="sistema"]')).to_be_checked()
    assert first.evaluate("localStorage.getItem('cris-tema')") is None


def test_with_reduced_motion_the_change_is_immediate(page, live_server, page_checks):
    page.emulate_media(reduced_motion="reduce", color_scheme="light")
    page.goto(f"{live_server.url}/entrar/")
    # El clic i la lectura en un sol pas: sense cortina, el tema ja hi és en tornar del clic.
    changed = page.evaluate(
        """() => {
            document.querySelector('.selector-tema input[value="dark"]').click();
            return document.documentElement.getAttribute('data-theme');
        }"""
    )
    assert changed == "dark"
    assert page.evaluate(BAR) == page.evaluate(BACKGROUND)


def test_system_choice_without_a_visible_change_keeps_the_page_as_it_is(
    page, live_server, page_checks
):
    page.emulate_media(color_scheme="dark")
    page.goto(f"{live_server.url}/entrar/")
    choose(page, "Fosc")
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    choose(page, "Sistema")  # el sistema ja demana fosc: el color no canvia
    page.wait_for_function(f"{THEME} === null")
    assert page.evaluate(BAR) == page.evaluate(BACKGROUND)
