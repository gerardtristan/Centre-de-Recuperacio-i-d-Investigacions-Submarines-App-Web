"""T-M07-11 (P-M07-D; CA-M07-11): un visitant escriu al club des de «Contacte». Dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.core.models import Setting
from apps.website import contact
from apps.website.models import ContactMessage

pytestmark = pytest.mark.e2e


def test_visitor_writes_to_the_club(page, live_server, texts, review, monkeypatch):
    Setting.objects.filter(key=contact.ENABLED).update(initial_value=True)
    monkeypatch.setattr(contact, "MIN_SECONDS", 0)  # el temps mínim té la seva prova unitària
    page.goto(f"{live_server.url}/contacte/")
    expect(page.get_by_role("heading", name="Escriu al club")).to_be_visible()
    review("contacte-formulari")
    page.get_by_label("Motiu").select_option(label="Quotes")
    page.get_by_label("Nom", exact=True).fill("Mar Visitant Prova")
    page.get_by_label("Correu electrònic").fill("mar.visitant@example.org")
    page.get_by_label("Missatge").fill("Quan es paga la quota de l'any vinent?")
    page.locator("input[name='accept_privacy']").check()
    page.get_by_role("button", name="Envia el missatge").click()
    expect(page.get_by_text("Missatge enviat")).to_be_visible()
    review("contacte-enviat")
    message = ContactMessage.objects.get()
    assert (message.reason.name, message.status) == ("Quotes", "new")
