"""Justificació d'un ajut al navegador (T-M09A-10c; AJ7 i AJ12): el tresorer genera el paquet, en
veu les excloses i l'envia. Pantalles a 1280, 390 i 320 px. Dades i fitxers inventats."""

import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from playwright.sync_api import expect

from apps.core.models import Department
from apps.expenses import documents
from apps.grants import justification
from apps.grants.models import GrantApplication, GrantCall
from apps.grants.tests.test_justification import expense

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def pdf(text):
    return SimpleUploadedFile("document.pdf", f"%PDF-1.7\n%{text}\n".encode())


def test_the_treasurer_generates_and_sends_the_package(page, live_server, transactional_db, review):
    treasurer = make_admin("tresorer.prova", "treasurer")
    call = GrantCall.objects.create(body="Diputació Inventada", name="Medi marí",
                                    created_by=treasurer)  # fmt: skip
    application = GrantApplication.objects.create(
        call=call, responsible=treasurer.person, department=Department.objects.get(name="General"),
        created_by=treasurer, status="granted", submitted_on=datetime.date(2027, 2, 1),
        submission_ref="RE-1", amount_requested_cents=100000,
    )  # fmt: skip
    complete = expense(treasurer, amount=50000, number="F-1")
    for document in (documents.Document.INVOICE, documents.Document.PAYMENT_PROOF):
        documents.attach(complete, document, pdf(document), by=treasurer)
        documents.attach_masked_copy(complete, document, pdf(f"tapada {document}"), by=treasurer)
    without = expense(treasurer, amount=6500, number="F-2")
    for item, amount in ((complete, 50000), (without, 6500)):
        justification.link_expense(application, item, amount, by=treasurer)
    login_admin(page, live_server.url, treasurer.login)

    url = reverse("administration:grant_justification", args=[application.pk])
    page.goto(f"{live_server.url}{url}")
    expect(page.get_by_role("heading", name="Justificació de l'ajut")).to_be_visible()
    page.get_by_role("button", name="Genera el paquet").click()
    expect(page.get_by_text("Paquet generat.")).to_be_visible()
    expect(page.get_by_text(f"Despesa núm. {without.pk}: Sense factura")).to_be_visible()
    review("justificacio-paquet")
    page.get_by_role("button", name="Envia'l i marca l'ajut com a justificat").click()
    expect(page.get_by_text("Versió 1 enviada.")).to_be_visible()
    review("justificacio-enviada")
    application.refresh_from_db()
    assert application.status == "justified"
