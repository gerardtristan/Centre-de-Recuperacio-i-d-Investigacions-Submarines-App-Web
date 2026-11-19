"""Correccions de la revisió de pantalles al navegador (T-M01-45). Una prova per incidència, amb
el número del punt de la fila del pla. Les pantalles es desen a 1280, 390 i 320 px (clar i
fosc) i es comprova que a 320 px no es desplaça de costat.
"""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import login_admin

pytestmark = pytest.mark.e2e

NARROW = {"width": 320, "height": 800}


@pytest.fixture(autouse=True)
def _no_motion(page):
    """Sense transicions: la captura en fosc es fa just després de canviar el tema."""
    page.emulate_media(reduced_motion="reduce")


def test_point_2_theme_selector_shows_its_labels_at_320(page, live_server, builder, member, review):
    # Amb sessió, a la configuració del compte (T-DX-05 i T-DX-05b).
    login_personal(page, live_server, builder, member)
    page.goto(f"{live_server.url}/compte/seguretat/")
    page.set_viewport_size(NARROW)
    selector = page.locator(".selector-tema")
    expect(selector).to_be_visible()
    for label in ("Sistema", "Clar", "Fosc"):
        text = selector.locator(".text-opcio", has_text=label)
        expect(text).to_be_visible()
        assert text.bounding_box()["width"] > 10, label  # no és el text amagat d'1 px
    review("seguretat-selector-tema")


def login_personal(page, live_server, builder, member):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("button", name="Surt")).to_be_visible()


def test_point_5_type_change_title_for_a_full_member(page, live_server, builder, member, review):
    login_personal(page, live_server, builder, member)  # soci de ple dret
    page.goto(f"{live_server.url}{reverse('members:change_type')}")
    expect(page.get_by_role("heading", level=1, name="Canvi de tipus")).to_be_visible()
    expect(page.get_by_role("link", name="Canvi de tipus")).to_have_attribute(
        "aria-current", "page"
    )
    review("canvi-de-tipus-ple-dret")


def test_point_5_create_a_leave_is_a_text_button(page, live_server, secretary, member, review):
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}{reverse('administration:member_detail', args=[member.pk])}")
    edit = page.get_by_role("link", name="Edita les dades")
    page.locator("summary", has_text="Més").click()  # T-DX-67: «Crea una baixa», dins de «Més»
    leave = page.get_by_role("link", name="Crea una baixa")
    expect(edit).to_be_visible()
    expect(leave).to_have_class("boto boto-petit boto-text")
    review("fitxa-accions")


def test_point_6_tab_goes_from_the_logo_to_the_personal_menu(
    page, live_server, builder, member, review
):
    """Des de la T-DX-05b el tema és a la configuració: després del logotip, el Tab va al menú.
    A l'escriptori el logotip i el menú són al panell de Ramillete (T-DX-59); al mòbil, el menú és
    la barra de baix (T-DX-08)."""
    login_personal(page, live_server, builder, member)
    panel = page.get_by_role("navigation", name="Àrea de socis")
    panel.get_by_role("link", name="Àrea de socis").focus()
    page.keyboard.press("Tab")
    expect(panel.locator(":focus")).to_have_count(1)
    review("inici-ordre-del-tabulador")


def test_point_6_fields_have_the_same_focus_ring_as_buttons(page, live_server, review):
    """Vora de focus de 3 px (`--v-focus`) als camps, com als botons i als enllaços (§9)."""
    page.goto(f"{live_server.url}/entrar/")
    field = page.get_by_label("Correu electrònic")
    field.focus()
    page.keyboard.press("Tab")
    page.keyboard.press("Shift+Tab")  # hi torna amb el teclat: :focus-visible
    expect(field).to_be_focused()
    width = field.evaluate("e => getComputedStyle(e).outlineWidth")
    page.get_by_role("button", name="Entrar").focus()
    button = page.evaluate("getComputedStyle(document.activeElement).outlineWidth")
    assert width == button == "3px"
    field.focus()
    review("entrada-focus-camp")


def test_iphone_install_help_from_the_login(page, live_server, review):
    """079, A-28 (RN-M01-96): ajuda per instal·lar-la a l'iPhone, pública i només de text."""
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_role("link", name="He oblidat la contrasenya").focus()
    page.keyboard.press("Tab")
    link = page.get_by_role("link", name="Com instal·lar la plataforma a l'iPhone")
    expect(link).to_be_focused()
    page.keyboard.press("Enter")
    expect(
        page.get_by_role("heading", level=1, name="Instal·lar la plataforma a l'iPhone")
    ).to_be_visible()
    expect(page.locator("ol.passos > li")).to_have_count(5)
    review("ajuda-iphone")
