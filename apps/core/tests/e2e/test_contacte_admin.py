"""Safata del contacte i motius (WP5 i WP8; T-M07-11) al navegador: la secretaria respon un
missatge i en tanca un altre amb motiu, i l'administració reparteix un motiu. Pantalles a 1280, 390
i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core.models import LegalText
from apps.website.models import ContactMessage, ContactReason

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def _message(reason, name, body):
    privacy, _ = LegalText.objects.get_or_create(
        kind="privacy", version=1, defaults={"content": "Política inventada"}
    )
    return ContactMessage.objects.create(
        reason=ContactReason.objects.get(name=reason), name=name,
        email="visitant.inventat@example.org", body=body, privacy_text=privacy,
    )  # fmt: skip


def test_the_secretary_answers_and_closes_contact_messages(
    page, live_server, transactional_db, review
):
    _message("Quotes", "Laia Inventada", "Quan es paga la quota d'enguany?")
    _message("Cursos", "Marc Inventat", "Hi ha curs d'iniciació al gener?")
    secretary = make_admin("secretaria.prova", "secretary")
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}{reverse('administration:website_contact')}")
    expect(page.get_by_role("heading", name="Missatges de contacte")).to_be_visible()
    review("contacte-safata")

    page.get_by_role("row", name="Quotes").get_by_role("link").click()
    expect(page.get_by_role("heading", name="Missatge: Quotes")).to_be_visible()
    page.get_by_role("button", name="Envia la resposta").click()
    expect(page.get_by_role("heading", name="Hi ha 1 error")).to_be_visible()  # Errata
    review("contacte-fitxa-errata")
    page.get_by_label("Resposta", exact=True).fill("Es paga al gener (resposta inventada).")
    page.get_by_role("button", name="Envia la resposta").click()
    expect(page.get_by_text("Resposta enviada.")).to_be_visible()

    page.get_by_role("row", name="Cursos").get_by_role("link").click()
    expect(page.get_by_text("No hi escriguis dades del visitant.")).to_be_visible()
    page.get_by_label("Motiu del tancament").fill("Resolt per telèfon")
    review("contacte-fitxa")
    page.get_by_role("button", name="Tanca el missatge").click()
    expect(page.get_by_text("Missatge tancat.")).to_be_visible()
    review("contacte-safata-feta")


def test_the_administrator_assigns_a_reason(page, live_server, transactional_db, review):
    admin = make_admin("admin.prova", "administrator")
    login_admin(page, live_server.url, admin.login)
    page.goto(f"{live_server.url}{reverse('administration:website_contact_reasons')}")
    expect(page.get_by_role("heading", name="Motius de contacte")).to_be_visible()
    review("contacte-motius")
    page.locator("main").get_by_role("link", name="Llicències", exact=True).click()
    page.get_by_label("Tresorer").check()
    review("contacte-motiu")
    page.get_by_role("button", name="Desa").click()
    expect(page.get_by_text("Motiu desat.")).to_be_visible()
    expect(page.get_by_role("row", name="Llicències")).to_contain_text("Tresorer")
