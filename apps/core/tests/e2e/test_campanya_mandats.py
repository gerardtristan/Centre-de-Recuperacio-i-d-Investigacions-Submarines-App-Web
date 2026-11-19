"""Campanya de mandats al navegador (T-M05a-13, segona part; C5, A4 i A5; P-M05a-E): el tresorer
obre la campanya, veu el recompte, confirma l'enviament (que va per la cua) i la tanca.
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import pytest
from playwright.sync_api import expect
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.core.models import LegalText, Person
from apps.members.tests.test_cards import make_member
from apps.payments import campaigns

from .conftest import login_admin, make_admin, menu_entry

pytestmark = pytest.mark.e2e


def test_treasurer_opens_sends_and_closes_the_campaign(
    page, live_server, transactional_db, settings, review
):
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    LegalText.objects.create(
        kind=campaigns.INVITATION_TEXT,
        version=1,
        content="Text de prova de la invitació.\n\nSegon paràgraf inventat.",
    )
    for first, number, document in (("Marta", 427, "00000005M"), ("Jordi", 311, "00000001R")):
        member = make_member(first, number=number, document=document)
        Person.objects.filter(pk=member.person_id).update(contact_email=f"{first}@example.org")
    make_member("Laia", number=502, document="00000003A")  # sense correu
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    # Hi arriba pel menú (T-DX-46): l'entrada només surt amb A4.
    entry = menu_entry(page, "Pagaments: campanya de mandats")  # T-DX-62: dins del seu grup
    entry.click()
    expect(page.get_by_role("heading", name="Campanya de mandats")).to_be_visible()
    expect(page).to_have_url(f"{live_server.url}/gestio/pagaments/campanya/")
    expect(entry).to_have_attribute("aria-current", "page")
    expect(page.get_by_text("No hi ha cap campanya oberta.")).to_be_visible()
    page.get_by_label("Nom de la campanya").fill("Campanya de tardor")
    page.get_by_role("button", name="Obre la campanya").click()

    expect(page.get_by_role("status")).to_contain_text("Campanya oberta")
    expect(page.get_by_text("2 socis actius sense mètode")).to_be_visible()
    review("campanya-mandats")

    page.get_by_role("button", name="Envia 2 invitacions…").click()
    expect(page.get_by_role("alert")).to_contain_text("S'enviaran 2 invitacions per correu.")
    # T-M05a-13d (097, P-306 opció B): el text sencer de la invitació abans de confirmar.
    expect(page.get_by_role("heading", name="Text de la invitació (versió 1)")).to_be_visible()
    expect(page.get_by_text("Segon paràgraf inventat.")).to_be_visible()
    review("campanya-mandats-confirma")
    page.get_by_role("button", name="Sí, envia-les").click()
    expect(page.get_by_role("status")).to_contain_text("s'estan enviant")
    assert ProcrastinateJob.objects.filter(task_name="payments.send_campaign_invitations").exists()

    page.get_by_role("button", name="Tanca la campanya…").click()
    page.get_by_role("button", name="Sí, tanca-la").click()
    expect(page.get_by_text("No hi ha cap campanya oberta.")).to_be_visible()
