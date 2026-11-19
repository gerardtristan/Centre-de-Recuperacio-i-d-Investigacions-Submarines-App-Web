"""El carnet en 3D (T-DX-61; design-system §6.21): el gir amb el botó, el teclat i el clic, la cara
amagada fora del lector de pantalla, #qr, la inclinació només amb ratolí, el moviment reduït, la
impressió amb les dues cares, la disposició a l'escriptori i al mòbil i la pista d'una sola vegada.
Desa el davant i el darrere a 1280, 1024, 800, 390 i 320 px, en clar i en fosc. Dades inventades.
"""

import pytest
from playwright.sync_api import expect

from .conftest import CAPTURES, settle
from .test_carnet_079 import login_personal

pytestmark = pytest.mark.e2e

WIDTHS = (1280, 1024, 800, 390, 320)
QR = "Codi QR per verificar el carnet"


def shots(page, folder, name):
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        for theme in ("light", "dark"):
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            page.wait_for_timeout(250)
            settle(page)
            page.screenshot(path=folder / f"{name}-{width}-{theme}.png", full_page=True)
    page.evaluate("document.documentElement.removeAttribute('data-theme')")
    page.set_viewport_size({"width": 1280, "height": 900})


def faces(page):
    return page.locator(".carnet-davant"), page.locator(".carnet-darrere")


def test_card_flips_with_keyboard_and_hides_the_other_face(
    page, live_server, builder, member, request
):
    login_personal(page, live_server.url, builder.personal(member.person))
    page.goto(f"{live_server.url}/socis/carnet/")
    front, back = faces(page)
    button = page.get_by_role("button", name="Mostra el QR")
    expect(button).to_have_attribute("aria-pressed", "false")
    expect(back).to_have_attribute("aria-hidden", "true")
    assert back.evaluate("e => e.inert") and not front.evaluate("e => e.inert")
    expect(page.get_by_role("img", name=QR)).to_have_count(0)  # fora del lector de pantalla
    expect(front.get_by_text("Vàlid", exact=True)).to_be_visible()
    expect(page.locator(".carnet-davant svg.monograma")).to_have_attribute("aria-hidden", "true")

    # La pista de Baliza: la primera vegada i prou.
    hint = page.get_by_text("Toca el carnet per veure el QR")
    expect(hint).to_be_visible()
    folder = CAPTURES / request.node.name
    shots(page, folder, "davant")

    # Amb el teclat: el botó gira el carnet i canvia de nom.
    button.focus()
    page.keyboard.press("Enter")
    back_button = page.get_by_role("button", name="Mostra el davant")
    expect(back_button).to_have_attribute("aria-pressed", "true")
    expect(back_button).to_be_focused()
    expect(front).to_have_attribute("aria-hidden", "true")
    expect(back).not_to_have_attribute("aria-hidden", "true")
    assert front.evaluate("e => e.inert") and not back.evaluate("e => e.inert")
    expect(page.get_by_role("img", name=QR)).to_be_visible()
    expect(hint).to_be_hidden()
    shots(page, folder, "darrere")
    page.keyboard.press("Space")
    expect(page.get_by_role("button", name="Mostra el QR")).to_have_attribute(
        "aria-pressed", "false"
    )

    # Un clic al carnet també el gira.
    page.locator("[data-carnet]").click()
    expect(page.get_by_role("button", name="Mostra el davant")).to_be_visible()

    # La pista ja no torna a sortir.
    page.reload()
    expect(page.get_by_role("button", name="Mostra el QR")).to_be_visible()
    expect(hint).to_be_hidden()


def test_qr_anchor_tilt_reduced_motion_and_print(page, live_server, builder, member, request):
    login_personal(page, live_server.url, builder.personal(member.person))
    # La navegació del soci enllaça a #qr: obre pel darrere.
    page.goto(f"{live_server.url}/socis/carnet/#qr")
    expect(page.get_by_role("button", name="Mostra el davant")).to_have_attribute(
        "aria-pressed", "true"
    )
    expect(page.get_by_role("img", name=QR)).to_be_visible()
    front, back = faces(page)
    expect(front).to_have_attribute("aria-hidden", "true")
    # Amb #qr no surt la pista: ja es veu el QR.
    expect(page.get_by_text("Toca el carnet per veure el QR")).to_be_hidden()

    # Inclinació amb el ratolí, fins a 6 graus, i en sortir torna al repòs.
    interior = page.locator(".carnet-interior")
    box = page.locator("[data-carnet]").bounding_box()
    page.mouse.move(box["x"] + 2, box["y"] + 2)
    page.mouse.move(box["x"] + box["width"] - 2, box["y"] + box["height"] - 2, steps=4)
    tilt = interior.evaluate(
        "e => [e.style.getPropertyValue('--rx'), e.style.getPropertyValue('--ry')]"
    )
    assert all(0 < abs(float(v.removesuffix("deg"))) <= 6 for v in tilt), tilt
    page.mouse.move(0, 0)
    assert interior.evaluate("e => e.style.getPropertyValue('--ry')") == "0deg"

    # Moviment reduït: cap transició i cap inclinació.
    page.emulate_media(reduced_motion="reduce")
    page.reload()
    assert interior.evaluate("e => getComputedStyle(e).transitionDuration") == "0s"
    page.mouse.move(box["x"] + 4, box["y"] + 4)
    page.mouse.move(box["x"] + box["width"] - 4, box["y"] + 4, steps=4)
    assert interior.evaluate("e => e.style.getPropertyValue('--ry')") in ("", "0deg")
    page.emulate_media(reduced_motion="no-preference")

    # Impressió: les dues cares, una al costat de l'altra, sense gir.
    page.emulate_media(media="print")
    expect(front).to_be_visible()
    expect(back).to_be_visible()
    a, b = front.bounding_box(), back.bounding_box()
    assert abs(a["y"] - b["y"]) < 1 and b["x"] > a["x"] + a["width"] - 1
    assert back.evaluate("e => getComputedStyle(e).transform") == "none"
    expect(page.locator(".carnet-lateral")).to_be_hidden()
    page.screenshot(path=CAPTURES / request.node.name / "impressio.png", full_page=True)
    page.emulate_media(media="screen")


def test_layout_left_on_desktop_centred_on_mobile(page, live_server, builder, member, review):
    login_personal(page, live_server.url, builder.personal(member.person))
    page.goto(f"{live_server.url}/socis/carnet/")
    card = page.locator("[data-carnet]")
    side = page.locator(".carnet-lateral")
    expect(side.locator("#carnet-nou")).to_be_visible()
    page.set_viewport_size({"width": 1280, "height": 900})
    c, s = card.bounding_box(), side.bounding_box()
    assert c["x"] + c["width"] <= s["x"] and abs(c["y"] - s["y"]) < 80
    page.set_viewport_size({"width": 390, "height": 844})
    c, s = card.bounding_box(), side.bounding_box()
    assert abs((c["x"] + c["width"] / 2) - 195) < 2 and s["y"] >= c["y"] + c["height"]
    page.set_viewport_size({"width": 1280, "height": 900})
    review("carnet-3d")  # també: cap desplaçament de costat a 320 px
