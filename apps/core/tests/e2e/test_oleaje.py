"""Oleaje a la portada de l'àrea del soci (T-DX-17 i T-DX-60): la capçalera amb la vora en ona, la
quota i el carnet en petit; la franja de pendents només si n'hi ha."""

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import CAPTURES, settle

pytestmark = pytest.mark.e2e


def all_widths(page, request, name):
    """T-DX-60: l'inici a totes les amplades del programa de l'escriptori, en clar i en fosc."""
    for width in (1280, 1024, 800, 390, 320):
        page.set_viewport_size({"width": width, "height": 900})
        for theme in ("light", "dark"):
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            page.wait_for_timeout(300)
            settle(page)
            suffix = "-fosc" if theme == "dark" else ""
            path = CAPTURES / request.node.name / f"{name}-{width}{suffix}.png"
            page.screenshot(path=path, full_page=True)
    page.evaluate("document.documentElement.removeAttribute('data-theme')")
    page.set_viewport_size({"width": 1280, "height": 900})


def test_member_home_has_the_wave_header_and_the_fee_block(
    page, live_server, builder, member, review, page_checks, request
):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/")
    portada = page.locator(".oleaje-portada")
    expect(portada.locator("svg.oleaje-vora")).to_be_attached()
    quota = portada.locator(".oleaje-quota")
    expect(quota.get_by_role("heading", name="La teva quota")).to_be_visible()
    expect(quota.get_by_text("Al dia")).to_be_visible()
    expect(quota.get_by_role("link", name="El meu carnet")).to_be_visible()
    expect(portada.get_by_role("heading", name="El teu carnet")).to_be_visible()
    expect(page.locator(".franja-estat")).to_have_count(0)
    # Sense animació d'entrada (D20, B10): la quota ja és al seu lloc.
    assert quota.evaluate("e => e.getAnimations().length") == 0
    review("portada-oleaje")
    all_widths(page, request, "inici-al-dia")


def test_a_pending_fee_shows_the_flat_strip_with_pay_now(
    page, live_server, builder, review, page_checks, request
):
    member = builder.approve(
        builder.submit(
            "Marta",
            "Pendent Inventada",
            "marta.pendent@example.org",
            builder.born(40),
            builder.full,
            privacy=True,
            membership_terms=True,
        )
    )
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/")
    strip = page.locator(".franja-estat")
    expect(strip).to_have_attribute("role", "status")
    expect(strip).to_contain_text("1 pagament pendent")
    pay = strip.get_by_role("link", name="Paga ara")
    assert pay.bounding_box()["height"] >= 56  # §6.5: «Paga ara» de 56 px
    assert page.locator(".boto-principal").count() == 1  # D19
    review("portada-pendent")
    all_widths(page, request, "inici-pendent")
