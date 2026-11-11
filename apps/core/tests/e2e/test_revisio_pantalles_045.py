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


def test_point_2_theme_selector_shows_its_labels_at_320(page, live_server, review):
    page.set_viewport_size(NARROW)
    page.goto(f"{live_server.url}/entrar/")
    selector = page.locator(".selector-tema")
    expect(selector).to_be_visible()
    for label in ("Sistema", "Clar", "Fosc"):
        text = selector.locator(".text-opcio", has_text=label)
        expect(text).to_be_visible()
        assert text.bounding_box()["width"] > 10, label  # no és el text amagat d'1 px
    review("entrada-selector-tema")


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
    leave = page.get_by_role("link", name="Crea una baixa")
    expect(edit).to_be_visible()
    expect(leave).to_have_class("boto boto-petit boto-text")
    review("fitxa-accions")
