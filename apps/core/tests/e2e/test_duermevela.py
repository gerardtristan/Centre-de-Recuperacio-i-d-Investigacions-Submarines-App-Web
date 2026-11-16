"""El tema a la part pública (T-DX-04 Duermevela i T-DX-05 Eclipse; decisió del propietari del
16/11/2026). En obrir la pàgina, l'interruptor de dia i nit mostra el tema del sistema; si es
canvia, la tria queda fixada, passa a les altres pestanyes sense recarregar i la barra del
navegador pren el color de fons; «Com el sistema» torna a seguir el sistema. Amb moviment
reduït, el canvi és directe. Es prova a la pàgina d'entrada, que és pública.
"""

import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e

THEME = "document.documentElement.getAttribute('data-theme')"
BAR = "document.querySelector('meta[name=\"theme-color\"]')?.content"
BACKGROUND = "getComputedStyle(document.documentElement).getPropertyValue('--c-fons').trim()"


def switch(page):
    return page.get_by_role("switch", name="Tema fosc")


@pytest.mark.parametrize(("system", "checked"), [("light", "false"), ("dark", "true")])
def test_on_opening_the_switch_shows_the_system_theme(
    page, live_server, page_checks, system, checked
):
    page.emulate_media(color_scheme=system)
    page.goto(f"{live_server.url}/entrar/")
    expect(switch(page)).to_have_attribute("aria-checked", checked)
    assert page.evaluate(THEME) is None
    expect(page.get_by_role("button", name="Com el sistema")).to_be_hidden()


def test_the_choice_reaches_the_other_tabs_and_the_browser_bar(
    page, context, live_server, page_checks
):
    page.emulate_media(color_scheme="light")
    page.goto(f"{live_server.url}/entrar/")
    second = context.new_page()
    second.emulate_media(color_scheme="light")
    second.goto(f"{live_server.url}/entrar/")
    light_bar = page.evaluate(BAR)
    assert light_bar == page.evaluate(BACKGROUND)

    switch(page).click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(switch(page)).to_have_attribute("aria-checked", "true")
    expect(page.get_by_role("button", name="Com el sistema")).to_be_visible()
    # L'altra pestanya ho rep per l'esdeveniment «storage», sense recarregar.
    expect(second.locator("html")).to_have_attribute("data-theme", "dark")
    expect(switch(second)).to_have_attribute("aria-checked", "true")
    second.wait_for_function(f"{BAR} === {BACKGROUND}")
    assert second.evaluate(BAR) != light_bar

    page.get_by_role("button", name="Com el sistema").click()
    second.wait_for_function(f"{THEME} === null")
    expect(switch(second)).to_have_attribute("aria-checked", "false")
    expect(page.get_by_role("button", name="Com el sistema")).to_be_hidden()
    assert page.evaluate("localStorage.getItem('cris-tema')") is None


def test_with_reduced_motion_the_change_is_immediate(page, live_server, page_checks, capture):
    page.emulate_media(reduced_motion="reduce", color_scheme="light")
    page.goto(f"{live_server.url}/entrar/")
    capture("entrada-dia")
    # El clic i la lectura en un sol pas: sense cortina, el tema ja hi és en tornar del clic.
    changed = page.evaluate(
        """() => {
            document.querySelector('[data-eclipse]').click();
            return document.documentElement.getAttribute('data-theme');
        }"""
    )
    assert changed == "dark"
    assert page.evaluate(BAR) == page.evaluate(BACKGROUND)
    capture("entrada-nit")


def test_switch_has_a_44px_touch_area(page, live_server, page_checks):
    page.set_viewport_size({"width": 390, "height": 800})
    page.goto(f"{live_server.url}/entrar/")
    area = page.evaluate(
        """() => {
            const boto = document.querySelector('[data-eclipse]');
            const r = boto.getBoundingClientRect();
            const a = getComputedStyle(boto, '::after');
            return { width: r.width, height: r.height - 2 * parseFloat(a.top) };
        }"""
    )
    assert area["width"] >= 44 and area["height"] >= 44, area
