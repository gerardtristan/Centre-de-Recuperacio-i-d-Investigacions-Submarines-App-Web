"""Pas de ple dret a simpatitzant al navegador (T-M01-42; 073 i 079, RN-M01-93; CA-M01-68 i
CA-M01-106): el soci el demana, el veu pendent, el retira només amb el teclat i en fa un altre;
la secretaria l'accepta i el soci veu que ja no el pot retirar. Les pantalles es desen a 1280,
390 i 320 px (clar i fosc).
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.members import member_requests
from apps.members.models import Member, MemberRequest
from conftest import PASSWORD

from .conftest import login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH


def login_personal(page, base_url, account):
    page.goto(f"{base_url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page).to_have_url(f"{base_url}/")


def test_full_member_requests_withdraws_and_the_secretary_accepts_another(
    page, live_server, builder, secretary, member, review
):
    account = builder.personal(member.person)
    login_personal(page, live_server.url, account)
    # T-DX-59: a l'escriptori, «Canvi de tipus» és dins de «Més» del panell de Ramillete.
    panel = page.get_by_role("navigation", name="Àrea de socis")
    panel.get_by_role("button", name="Més", exact=True).click()
    panel.get_by_role("link", name="Canvi de tipus").click()
    expect(
        page.get_by_role("heading", level=1, name="Canvi de tipus")
    ).to_be_visible()  # T-M01-45, punt 5
    expect(page.get_by_text("Actualment ets soci de ple dret.")).to_be_visible()
    expect(page.get_by_text("cap devolució de la quota del període actual")).to_be_visible()
    # T-M01-43: la frase de l'avís previ.
    expect(page.get_by_text("T'avisarem abans de la renovació", exact=False)).to_be_visible()
    review("explicacio")
    page.get_by_role("button", name="Envia la sol·licitud").click()
    expect(page.get_by_role("heading", name="Tens una sol·licitud pendent")).to_be_visible()
    review("pendent")

    # Retirar-la sense marcar la confirmació: el servidor ho diu i no canvia res.
    page.get_by_role("button", name="Retira la sol·licitud").click()
    expect(page.get_by_text("Cal que marquis la confirmació.")).to_be_visible()
    review("retirar-sense-confirmar")
    # Només amb el teclat: la casella i el botó.
    page.get_by_label("Confirmo que vull retirar la sol·licitud.").focus()
    page.keyboard.press("Space")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Retira la sol·licitud")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("Sol·licitud retirada.")).to_be_visible()
    review("retirada")
    change = MemberRequest.objects.get(kind=MemberRequest.Kind.CHANGE_TYPE)
    assert change.status == MemberRequest.Status.CANCELLED

    # En fa una altra, i la secretaria l'accepta.
    page.get_by_role("button", name="Envia la sol·licitud").click()
    expect(page.get_by_role("heading", name="Tens una sol·licitud pendent")).to_be_visible()
    page.context.clear_cookies()
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{ADMIN}/socis/sollicituds/")
    expect(page.get_by_text("Ple dret → Simpatitzant")).to_be_visible()
    review("sollicituds")
    page.get_by_role("link", name="Obre la sol·licitud: Pere Prova Inventat").click()
    expect(page.get_by_text("Renovació en què s'aplicarà")).to_be_visible()
    expect(page.get_by_text("no es crea cap càrrec ni cap suplement")).to_be_visible()
    review("detall")
    page.get_by_role("button", name="Accepta el pas a simpatitzant").click()
    expect(
        page.get_by_text("Pas a simpatitzant acceptat. S'aplicarà quan el soci renovi.")
    ).to_be_visible()
    review("acceptat")
    current = Member.objects.select_related("type").get(pk=member.pk)
    assert current.type.code == "full"  # el tipus no canvia fins a la renovació (T-M01-43)
    assert member_requests.accepted_downgrade(current) is not None

    # El soci veu que està acceptada i ja no la pot retirar.
    page.context.clear_cookies()
    login_personal(page, live_server.url, account)
    page.goto(f"{live_server.url}/socis/canvi-tipus/")
    expect(page.get_by_role("heading", name="Sol·licitud acceptada")).to_be_visible()
    expect(page.get_by_role("button", name="Retira la sol·licitud")).to_have_count(0)
    review("acceptada-soci")
