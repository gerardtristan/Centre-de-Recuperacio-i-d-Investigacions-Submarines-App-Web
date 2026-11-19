"""El carnet al navegador (T-M01-19; 079, RN-M01-85 i RN-M01-92; CA-M01-87, 104 i 105): QR
calculat, verificació pública, impressió («Desa com a PDF»), carnet nou a petició del soci i
revocació des de l'administració. Les pantalles es desen a 1280, 390 i 320 px (clar i fosc).
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.members import cards
from apps.members.models import MemberCard
from conftest import PASSWORD

from .conftest import CAPTURES, login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH


def login_personal(page, base_url, account):
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()


def verification_path(member):
    card = MemberCard.objects.get(member=member, revoked_at__isnull=True)
    return cards.verification_url(cards.qr_token(card)).split(settings.PUBLIC_SITE_URL)[1]


def test_card_with_qr_print_and_new_card(page, live_server, builder, member, review, request):
    account = builder.personal(member.person)
    login_personal(page, live_server.url, account)
    page.goto(f"{live_server.url}/socis/carnet/")
    expect(page.get_by_role("heading", name="El meu carnet")).to_be_visible()
    # T-DX-61: el QR és al darrere del carnet; «Mostra el QR» el gira.
    page.get_by_role("button", name="Mostra el QR").click()
    qr = page.get_by_role("img", name="Codi QR per verificar el carnet")
    expect(qr).to_be_visible()
    expect(page.get_by_role("button", name="Desa com a PDF")).to_be_visible()
    review("carnet")

    # Impressió: només el carnet, sense capçalera, navegació ni botons (CA-M01-104).
    page.emulate_media(media="print")
    expect(qr).to_be_visible()
    expect(page.get_by_role("button", name="Desa com a PDF")).to_be_hidden()
    expect(page.get_by_role("button", name="Demana un carnet nou")).to_be_hidden()
    expect(page.get_by_role("navigation", name="Compte personal")).to_be_hidden()
    folder = CAPTURES / request.node.name
    page.screenshot(path=folder / "carnet-impressio.png", full_page=True)
    page.pdf(path=folder / "carnet.pdf", format="A4")
    assert (folder / "carnet.pdf").stat().st_size > 5_000
    page.emulate_media(media="screen")

    # El QR porta l'adreça de verificació pública: «Vàlid», número i nom de pila.
    old_path = verification_path(member)
    page.goto(f"{live_server.url}{old_path}")
    expect(page.get_by_role("heading", name="Vàlid", exact=True)).to_be_visible()
    review("verificacio-valida")

    # Carnet nou a petició del soci, amb el teclat: l'anterior deixa de valer.
    page.goto(f"{live_server.url}/socis/carnet/")
    page.get_by_role("button", name="Demana un carnet nou").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Tens un carnet nou")).to_be_visible()
    review("carnet-nou")
    assert verification_path(member) != old_path
    page.goto(f"{live_server.url}{old_path}")
    expect(page.get_by_role("heading", name="No vàlid", exact=True)).to_be_visible()


def test_secretary_revokes_a_card_with_reason(
    page, live_server, builder, secretary, member, review
):
    account = builder.personal(member.person)
    path = verification_path(member)
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{ADMIN}/socis/{member.pk}/")
    expect(page.get_by_role("heading", name="Carnet", exact=True)).to_be_visible()
    page.get_by_text("Revoca el carnet…").click()
    review("fitxa-revoca-carnet")
    page.get_by_label("Motiu de la revocació").focus()
    page.keyboard.type("Carnet perdut (prova inventada)")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Revoca el carnet", exact=True)).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Carnet revocat")).to_be_visible()
    expect(page.get_by_text("Ara no té cap carnet vigent.")).to_be_visible()
    review("fitxa-carnet-revocat")

    page.context.clear_cookies()
    page.goto(f"{live_server.url}{path}")
    expect(page.get_by_role("heading", name="No vàlid", exact=True)).to_be_visible()

    # El soci ho veu a la seva pàgina i en pot demanar un de nou.
    login_personal(page, live_server.url, account)
    page.goto(f"{live_server.url}/socis/carnet/")
    expect(page.get_by_text("Ara no tens cap carnet.")).to_be_visible()
    review("carnet-revocat-soci")
    page.get_by_role("button", name="Demana un carnet nou").click()
    page.get_by_role("button", name="Mostra el QR").click()
    expect(page.get_by_role("img", name="Codi QR per verificar el carnet")).to_be_visible()
