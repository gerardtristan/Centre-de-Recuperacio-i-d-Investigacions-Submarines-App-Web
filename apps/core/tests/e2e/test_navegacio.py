"""Navegació comuna al navegador (T-M01-46): la barra lateral de l'administració amb el botó
«Menú» en pantalles estretes, i «Surt» a l'administració i a l'àrea personal. Cada pantalla es
desa a 1280, 390 i 320 px (clar i fosc) i es comprova que a 320 px no es desplaça de costat.
El menú s'obre i s'arriba a «Surt» només amb el teclat.
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH
MOBILE = {"width": 390, "height": 900}


@pytest.fixture(autouse=True)
def _no_motion(page):
    """Sense transicions: la captura en fosc es fa just després de canviar el tema i, amb
    moviment, els botons hi sortirien a mig canvi de color."""
    page.emulate_media(reduced_motion="reduce")


def tab_until(page, locator, limit=40):
    """Prem Tab fins que el focus arriba a `locator`; torna el text de cada parada."""
    stops = []
    for _ in range(limit):
        page.keyboard.press("Tab")
        stops.append(
            page.evaluate(
                "(e => (e.innerText || e.value || e.getAttribute('aria-label') || '').trim())"
                "(document.activeElement)"
            )
        )
        if locator.evaluate("e => e === document.activeElement"):
            return stops
    raise AssertionError(f"El focus no hi arriba amb Tab: {stops}")


def test_admin_menu_follows_the_permissions_and_logs_out_with_the_keyboard(
    page, live_server, secretary, review
):
    login_admin(page, live_server.url, secretary.login)
    sidebar = page.locator("#barra-lateral")
    menu = page.get_by_role("button", name="Menú")
    logout = sidebar.get_by_role("button", name="Surt")

    # Escriptori: la barra es veu sempre, sense botó, amb el compte, el TOTP i «Surt».
    expect(sidebar).to_be_visible()
    expect(menu).to_be_hidden()
    expect(sidebar.get_by_text(secretary.login)).to_be_visible()
    expect(sidebar.get_by_text("TOTP actiu")).to_be_visible()
    expect(sidebar.get_by_role("link", name="Inici")).to_have_attribute("aria-current", "page")
    # La secretaria no té el registre d'activitat ni els comptes: no són a la pàgina.
    expect(page.get_by_role("link", name="Registre d'activitat")).to_have_count(0)
    expect(page.get_by_role("link", name="Comptes d'administrador")).to_have_count(0)
    # P-193 (095, B): la Secretaria té A4 «Cons.» (només «té mètode: sí/no»), i per tant l'entrada.
    expect(page.get_by_role("link", name="Pagaments: mètodes i mandats").first).to_be_visible()
    expect(page.get_by_role("link", name="Tresoreria: conciliació")).to_have_count(0)  # T1
    # A4 «Cons.»
    expect(page.get_by_role("link", name="Pagaments: campanya de mandats").first).to_be_visible()
    expect(page.get_by_role("link", name="Pagaments: llistat")).to_have_count(0)  # B6
    expect(page.get_by_role("link", name="Pagaments: remeses")).to_have_count(0)  # B3
    expect(page.get_by_role("link", name="Pantalles en construcció")).to_have_count(0)  # DX1
    sidebar.get_by_role("link", name="Llistat de socis").click()
    expect(page.get_by_role("heading", name="Llistat de socis")).to_be_visible()
    expect(sidebar.get_by_role("link", name="Llistat de socis")).to_have_attribute(
        "aria-current", "page"
    )
    review("llistat-amb-barra")

    # Mòbil: plegada darrere de «Menú».
    page.goto(f"{live_server.url}/{ADMIN}/")
    page.set_viewport_size(MOBILE)
    expect(menu).to_be_visible()
    expect(menu).to_have_attribute("aria-expanded", "false")
    expect(sidebar).to_be_hidden()
    review("inici-menu-plegat")

    # Només amb el teclat: obrir, tancar amb Esc (el focus torna al botó) i tornar a obrir.
    page.set_viewport_size(MOBILE)
    menu.focus()
    page.keyboard.press("Enter")
    expect(menu).to_have_attribute("aria-expanded", "true")
    expect(sidebar).to_be_visible()
    page.keyboard.press("Escape")
    expect(sidebar).to_be_hidden()
    expect(menu).to_be_focused()
    page.keyboard.press("Space")
    expect(sidebar).to_be_visible()
    review("inici-menu-obert")

    # Del botó a «Surt» amb Tab: el tema, les entrades i «Surt», en l'ordre de la pantalla.
    page.set_viewport_size(MOBILE)
    menu.focus()
    stops = tab_until(page, logout)
    assert stops[-1] == "Surt"
    assert stops.index("Inici") < stops.index("Llistat de socis") < len(stops) - 1
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Entrada d'administració")).to_be_visible()
    # La sessió és tancada: l'inici torna a demanar l'entrada.
    page.goto(f"{live_server.url}/{ADMIN}/")
    expect(page.get_by_role("heading", name="Entrada d'administració")).to_be_visible()
    expect(page.locator("#barra-lateral")).to_have_count(0)


def test_personal_menu_logs_out_with_the_keyboard(page, live_server, builder, member, review):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("heading", name="Plataforma del C.R.I.S.")).to_be_visible()
    logout = page.get_by_role("button", name="Surt")
    expect(logout).to_have_count(1)
    review("inici-area-personal")

    page.goto(f"{live_server.url}/socis/perfil/")
    expect(logout).to_be_visible()
    review("perfil-amb-surt")
    page.set_viewport_size(MOBILE)
    # Al mòbil, la capçalera només deixa «Surt»; la resta és a la barra de baix (T-DX-08).
    page.locator(".capcalera-compte .marca").focus()
    page.keyboard.press("Tab")
    expect(logout).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Entrar a l'àrea de socis")).to_be_visible()
    page.goto(f"{live_server.url}/socis/perfil/")
    expect(page.get_by_role("heading", name="Entrar a l'àrea de socis")).to_be_visible()
