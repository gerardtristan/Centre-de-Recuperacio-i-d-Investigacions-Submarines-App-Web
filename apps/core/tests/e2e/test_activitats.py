"""T-DX-63: la pàgina «Activitats» del soci, en construcció (design-system §16, T-DX-63). Les
pestanyes amb les fletxes, els filtres sobre el contingut d'exemple, l'estat buit, la columna de
filtres a l'escriptori i el panell a pantalla sencera al mòbil. Res no surt del navegador."""

import re

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import CAPTURES, settle
from .test_accessibilitat_028 import axe_audit

pytestmark = pytest.mark.e2e

OVERFLOW_JS = "() => document.documentElement.scrollWidth - window.innerWidth"


@pytest.fixture
def screen(page, live_server, builder, member, settings):
    """Obre una pantalla en construcció amb la sessió d'un soci (com test_previews.py)."""
    settings.SHOW_UNDER_CONSTRUCTION = True
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    return lambda name: page.goto(f"{live_server.url}/en-construccio/{name}/")


@pytest.fixture
def activitats(page, screen):
    screen("activitats")
    expect(page.get_by_role("heading", level=1)).to_have_text("12 activitats properes, 8 per a tu")
    return page


def _tab(page, name):
    return page.get_by_role("tab", name=name)


def test_tabs_move_with_the_arrow_keys(activitats):
    page = activitats
    _tab(page, "Totes").focus()
    page.keyboard.press("ArrowRight")
    expect(_tab(page, "Sortides")).to_have_attribute("aria-selected", "true")
    expect(_tab(page, "Sortides")).to_be_focused()
    expect(_tab(page, "Totes")).to_have_attribute("aria-selected", "false")
    expect(page.locator("#panell-sortida")).to_be_visible()
    expect(page.locator("#panell-totes")).to_be_hidden()
    page.keyboard.press("End")
    expect(_tab(page, "Guardades")).to_have_attribute("aria-selected", "true")
    page.keyboard.press("ArrowRight")  # dona la volta
    expect(_tab(page, "Totes")).to_have_attribute("aria-selected", "true")
    # «Veure-les totes» d'una secció porta a la pestanya del tipus
    page.get_by_role("button", name=re.compile("Veure-les totes.*Cursos i especialitats")).click()
    expect(_tab(page, "Cursos i especialitats")).to_have_attribute("aria-selected", "true")


def test_the_can_do_switch_changes_the_count(activitats, page_checks):
    page = activitats
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    count = _tab(page, "Totes").locator("[data-n]")
    expect(count).to_have_text("12")
    switch = page.get_by_role("switch", name="Només les que puc fer")
    expect(switch).to_have_accessible_description(re.compile("Titulació B1 · llicència vigent"))
    switch.click()
    expect(switch).to_have_attribute("aria-checked", "true")
    expect(count).to_have_text("8")
    expect(page.locator("[data-recompte]")).to_have_text("8")
    # Només lectura (§16): filtrar no envia res, i guardar no es pot fer
    assert requests == []
    expect(page.locator("#panell-totes .activitats-estrella").first).to_be_disabled()


def test_an_empty_combination_says_which_filter_to_remove(activitats):
    page = activitats
    page.get_by_label("On", exact=True).select_option(label="Cadaqués")
    page.locator("label", has_text="Aquest mes").click()
    empty = page.locator("#panell-totes [data-buit]")
    expect(empty).to_be_visible()
    expect(page.locator("#panell-totes [data-targeta]:visible")).to_have_count(0)
    expect(empty.get_by_role("button", name="Treu el filtre Quan: Aquest mes")).to_be_visible()
    expect(empty.get_by_role("button", name="Treu el filtre Només les que puc fer")).to_be_hidden()
    empty.get_by_role("button", name="Treu el filtre On: Cadaqués").click()
    expect(empty).to_be_hidden()
    expect(_tab(page, "Totes").locator("[data-n]")).to_have_text("3")


def test_at_1280_the_filters_are_a_sticky_column_on_the_left(activitats):
    page = activitats
    page.set_viewport_size({"width": 1280, "height": 900})
    filters = page.locator("#activitats-filtres")
    main = page.locator(".activitats-principal")
    expect(filters).to_be_visible()
    expect(page.get_by_role("button", name="Filtres")).to_be_hidden()
    assert filters.bounding_box()["x"] + filters.bounding_box()["width"] <= main.bounding_box()["x"]
    assert filters.evaluate("el => getComputedStyle(el).position") == "sticky"
    # 3 targetes per fila a la secció de les sortides
    cards = page.locator("#panell-totes .tipus-sortida [data-targeta]:visible")
    expect(cards).to_have_count(3)
    assert len({round(cards.nth(i).bounding_box()["y"]) for i in range(3)}) == 1


def test_at_390_the_filters_open_full_screen_and_done_closes_them(activitats, request):
    page = activitats
    page.set_viewport_size({"width": 390, "height": 800})
    filters = page.locator("#activitats-filtres")
    opener = page.get_by_role("button", name="Filtres")
    expect(filters).to_be_hidden()
    opener.click()
    expect(filters).to_be_visible()
    expect(opener).to_have_attribute("aria-expanded", "true")
    box = filters.bounding_box()
    assert (box["x"], box["y"], box["width"], box["height"]) == (0, 0, 390, 800)
    page.screenshot(path=CAPTURES / request.node.name / "filtres-obert-390.png")
    page.get_by_role("switch", name="Només amb places lliures").click()
    page.get_by_role("button", name="Fet").click()
    expect(filters).to_be_hidden()
    expect(opener).to_be_focused()
    expect(page.locator("[data-recompte]")).to_have_text("11")


def test_no_sideways_scroll_at_320_and_axe_in_both_themes(activitats, request):
    page = activitats
    folder = CAPTURES / request.node.name
    for width in (1280, 1024, 800, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        assert page.evaluate(OVERFLOW_JS) <= 0, width
        for theme in ("light", "dark"):
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            settle(page)
            page.screenshot(path=folder / f"activitats-{width}-{theme}.png", full_page=True)
    page.evaluate("document.documentElement.removeAttribute('data-theme')")
    page.set_viewport_size({"width": 1280, "height": 900})
    axe = axe_audit(page)
    assert axe["light"]["violacions"] == [] and axe["dark"]["violacions"] == [], axe


def test_for_you_rail_counts_the_cards_on_mobile_without_autoplay(page, screen):
    page.set_viewport_size({"width": 390, "height": 800})
    screen("activitats-per-a-tu")
    rail = page.get_by_role("list", name="Activitats per a tu, es desplaça amb les fletxes")
    counter = page.locator("#per-a-tu-comptador")
    expect(rail.get_by_role("listitem")).to_have_count(3)
    expect(counter).to_have_text("1 / 3")
    rail.evaluate("el => el.scrollTo({left: el.scrollWidth})")
    expect(counter).to_have_text("3 / 3")
    link = page.get_by_role("link", name="Totes les activitats (12)")
    expect(link).to_have_attribute("href", "/en-construccio/activitats/")
