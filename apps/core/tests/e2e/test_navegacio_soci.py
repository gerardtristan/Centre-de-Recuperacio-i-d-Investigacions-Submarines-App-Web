"""Navegació de l'àrea del soci a totes les mides (T-DX-59; design-system §6.12): la barra de
Ramillete a baix fins a 1023 px (a la tauleta, flotant, centrada i de 30rem com a màxim) i, a partir
de 1024 px, el panell lateral clar amb «Mostra el QR», les entrades i el compte, sense la capçalera.
Amb el teclat, la fletxa del QR i «Més» s'obren amb Intro i es tanquen amb Esc, i el focus torna al
botó. Desa la portada i «Les meves quotes» a 1280, 1024, 800, 390 i 320 px, en clar i en fosc."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import CAPTURES, settle

pytestmark = pytest.mark.e2e

WIDTHS = (1280, 1024, 800, 390, 320)
REM = 16


@pytest.fixture(autouse=True)
def _no_motion(page):
    page.emulate_media(reduced_motion="reduce")


def login(page, live_server, builder, member):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("heading", name="Plataforma del C.R.I.S.")).to_be_visible()


def nav(page):
    return page.get_by_role("navigation", name="Àrea de socis")


def no_horizontal_scroll(page):
    return page.evaluate(
        "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
    )


def shoot(page, request, name):
    folder = CAPTURES / request.node.name
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        for theme in ("light", "dark"):
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            settle(page)
            suffix = "-fosc" if theme == "dark" else ""
            page.screenshot(path=folder / f"{name}-{width}{suffix}.png", full_page=True)
        page.evaluate("() => document.documentElement.removeAttribute('data-theme')")


def test_side_panel_on_desktop_and_bar_below(
    page, live_server, builder, member, settings, request, page_checks
):
    settings.SHOW_UNDER_CONSTRUCTION = False  # producció: cap pantalla «En construcció»
    page.set_viewport_size({"width": 1280, "height": 900})
    login(page, live_server, builder, member)
    panel = nav(page).locator(".ramillete-lateral")
    bar = nav(page).locator(".ramillete-barra")

    # Escriptori: el panell, sense la capçalera; el contingut no hi queda a sota.
    for width in (1280, 1024):
        page.set_viewport_size({"width": width, "height": 900})
        expect(panel).to_be_visible()
        expect(bar).to_be_hidden()
        expect(page.locator(".capcalera-compte")).to_be_hidden()
        expect(page.get_by_role("navigation", name="Compte personal", exact=True)).to_be_hidden()
        box = nav(page).bounding_box()
        assert box["x"] > 0 and box["y"] > 0  # flotant: no toca les vores
        assert page.locator("main").bounding_box()["x"] >= box["x"] + box["width"]
    expect(panel.get_by_role("link", name="Inici")).to_have_attribute("aria-current", "page")
    expect(panel.get_by_role("link", name="Mostra el QR")).to_have_attribute(
        "href", "/socis/carnet/#qr"
    )
    expect(panel.get_by_text("Pere", exact=True)).to_be_visible()
    expect(panel.get_by_text(f"Soci núm. {member.member_number}")).to_be_visible()
    expect(page.get_by_role("button", name="Surt")).to_have_count(1)
    expect(panel.get_by_role("button", name="Surt")).to_be_visible()
    # «Activitats» porta a «Les meves activitats» (T-DX-95), també a producció.
    expect(panel.get_by_role("link", name="Activitats", exact=True)).to_have_attribute(
        "href", reverse("activities:mine")
    )

    # Tauleta: la barra flotant, centrada i de 30rem com a màxim; «Surt» a la capçalera.
    page.set_viewport_size({"width": 800, "height": 900})
    expect(bar).to_be_visible()
    expect(panel).to_be_hidden()
    box = nav(page).bounding_box()
    assert box["width"] <= 30 * REM + 1
    assert abs(box["x"] - (800 - box["x"] - box["width"])) <= 1
    expect(page.locator(".capcalera-compte").get_by_role("button", name="Surt")).to_be_visible()
    expect(page.get_by_role("button", name="Surt")).to_have_count(1)

    # Mòbil: la barra a baix, de vora a vora.
    page.set_viewport_size({"width": 390, "height": 844})
    expect(bar).to_be_visible()
    assert nav(page).bounding_box()["width"] == 390
    expect(bar.get_by_role("link", name="Activitats", exact=True)).to_be_visible()
    page.set_viewport_size({"width": 320, "height": 800})
    assert no_horizontal_scroll(page)

    shoot(page, request, "inici")
    page.goto(f"{live_server.url}{reverse('members:fees')}")
    page.set_viewport_size({"width": 1280, "height": 900})
    expect(
        nav(page).locator(".ramillete-lateral").get_by_role("link", name="Les meves quotes")
    ).to_have_attribute("aria-current", "page")
    page.set_viewport_size({"width": 320, "height": 800})
    assert no_horizontal_scroll(page)
    shoot(page, request, "quotes")


def test_split_button_and_more_with_the_keyboard(
    page, live_server, builder, member, request, page_checks
):
    page.set_viewport_size({"width": 1280, "height": 900})
    login(page, live_server, builder, member)
    panel = nav(page).locator(".ramillete-lateral")

    # La fletxa del QR: Intro obre el menú i hi porta el focus; Esc el tanca i torna al botó.
    arrow = panel.get_by_role("button", name="Més accions del carnet")
    arrow.focus()
    page.keyboard.press("Enter")
    expect(arrow).to_have_attribute("aria-expanded", "true")
    renew = panel.get_by_role("link", name="Demana un carnet nou")
    expect(renew).to_be_focused()
    page.screenshot(path=CAPTURES / request.node.name / "menu-qr-1280.png")
    expect(renew).to_have_attribute("href", "/socis/carnet/#carnet-nou")
    # La quota és pagada: res a pagar.
    expect(panel.get_by_role("link", name="Paga ara")).to_have_count(0)
    page.keyboard.press("Escape")
    expect(arrow).to_have_attribute("aria-expanded", "false")
    expect(renew).to_be_hidden()
    expect(arrow).to_be_focused()

    # «Més»: Intro el desplega i Esc el plega, amb el focus al botó.
    more = panel.get_by_role("button", name="Més", exact=True)
    more.focus()
    page.keyboard.press("Enter")
    expect(more).to_have_attribute("aria-expanded", "true")
    expect(panel.get_by_role("link", name="Baixa")).to_be_visible()
    page.screenshot(path=CAPTURES / request.node.name / "mes-obert-1280.png")
    page.keyboard.press("Tab")
    expect(panel.get_by_role("link", name="Canvi de tipus")).to_be_focused()
    page.keyboard.press("Escape")
    expect(more).to_have_attribute("aria-expanded", "false")
    expect(panel.get_by_role("link", name="Baixa")).to_be_hidden()
    expect(more).to_be_focused()

    # A una pàgina de dins de «Més», ja surt obert i l'entrada actual hi està marcada.
    page.goto(f"{live_server.url}{reverse('members:leave')}")
    expect(more).to_have_attribute("aria-expanded", "true")
    expect(panel.get_by_role("link", name="Baixa")).to_have_attribute("aria-current", "page")

    # Ordre del teclat: el salt, després la navegació i després el contingut.
    page.goto(f"{live_server.url}/")
    page.keyboard.press("Tab")
    expect(page.get_by_role("link", name="Vés al contingut")).to_be_focused()
    page.keyboard.press("Tab")
    expect(panel.get_by_role("link", name="Àrea de socis")).to_be_focused()
