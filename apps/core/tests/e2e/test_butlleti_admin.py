"""Butlletí a l'administració (WP6; T-M07-14c) al navegador: el President redacta un esborrany, en
veu la vista prèvia i el nombre de destinataris, l'envia amb la confirmació i en veu els
recomptes. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core.models import LegalText, Setting
from apps.website import newsletter

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_president_writes_and_sends_a_newsletter(page, live_server, transactional_db, review):
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)
    text = LegalText.objects.create(kind="newsletter", version=1, content="Butlletí inventat")
    subscription, _ = newsletter.subscribe("subscriptora.inventada@example.org", legal_text=text)
    newsletter.confirm(subscription.token)
    president = make_admin("presidencia.prova", "president")
    login_admin(page, live_server.url, president.login)
    page.goto(f"{live_server.url}{reverse('administration:website_newsletters')}")
    expect(page.get_by_role("heading", name="Butlletí", exact=True)).to_be_visible()
    page.locator("main").get_by_role("link", name="Butlletí nou").click()
    page.get_by_label("Assumpte").fill("Sortides de gener")
    page.get_by_label("Text", exact=True).fill(
        "Primera sortida a les Medes.\n\nInscripcions obertes."
    )
    page.get_by_role("button", name="Desa l'esborrany").click()
    expect(page.get_by_text("Esborrany desat.")).to_be_visible()
    expect(page.get_by_text("Ara l'han de rebre 1 subscripció confirmada.")).to_be_visible()
    page.get_by_role("button", name="Envia el butlletí").click()
    expect(page.get_by_role("heading", name="Hi ha 1 error")).to_be_visible()  # Errata
    review("butlleti-esborrany")
    page.get_by_label("Confirmo que l'envio ara").check()
    page.get_by_role("button", name="Envia el butlletí").click()
    expect(page.get_by_text("Butlletí a la cua per a 1 destinataris.")).to_be_visible()
    review("butlleti-llista")
    page.locator("main").get_by_role("link", name="Sortides de gener").click()
    expect(page.get_by_text("Destinataris")).to_be_visible()
    expect(page.locator("main")).not_to_contain_text("@example.org")
    review("butlleti-recomptes")
