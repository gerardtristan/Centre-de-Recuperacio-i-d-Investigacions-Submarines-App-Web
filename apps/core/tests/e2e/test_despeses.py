"""Despeses al navegador (T-M09-06, part sense fitxer, i T-M09-15; MG1 i MG2): el tresorer registra
una despesa des del mòbil i la veu a «Despeses sense factura». Pantalles a 1280, 390 i 320 px.
Només dades inventades."""

import re
import struct
import zlib

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.expenses.models import Expense, Supplier

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def _png(width, height):
    """Un PNG inventat (blanc amb una franja verda), sense Pillow, que no és dependència."""

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))

    green, white = bytes((11, 93, 75)), bytes((255, 255, 255))
    rows = b"".join(bytes(1) + (green if 24 <= y < 80 else white) * width for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    signature = bytes((137, 80, 78, 71, 13, 10, 26, 10))
    idat = chunk(b"IDAT", zlib.compress(rows))
    return signature + chunk(b"IHDR", header) + idat + chunk(b"IEND", b"")


def test_the_treasurer_records_an_expense(page, live_server, transactional_db, review):
    Supplier.objects.create(name="Nàutica Inventada SL")
    treasurer = make_admin("tresorer.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)

    page.goto(f"{live_server.url}{reverse('administration:expense_new')}")
    expect(page.get_by_role("heading", name="Registra una despesa")).to_be_visible()
    page.get_by_role("button", name="Registra la despesa").click()
    expect(page.get_by_text("Aquest camp és obligatori.").first).to_be_visible()
    review("despesa-nova-errors")

    # Formulari net: la captura «despesa-nova» no ha de dur els errors del primer intent.
    page.goto(f"{live_server.url}{reverse('administration:expense_new')}")
    page.get_by_label("Proveïdor").select_option(label="Nàutica Inventada SL")
    page.get_by_label("Número de factura").fill("F-2027-1")
    page.get_by_label("Data de la factura").fill("2027-06-10")
    page.get_by_label("Categoria").select_option(label="Embarcació")
    page.get_by_label("Descripció").fill("Sortida a les Medes")
    page.get_by_label("Import (€)").fill("250,50")
    page.get_by_label("Departament").select_option(label="General")
    review("despesa-nova")
    page.get_by_role("button", name="Registra la despesa").click()

    expect(page.get_by_role("heading", name="Despeses sense factura")).to_be_visible()
    expect(page.get_by_text("Despesa registrada")).to_be_visible()
    expect(
        page.get_by_role("table", name="1 despesa sense factura, la més antiga primer")
    ).to_contain_text("Sortida a les Medes")
    review("despeses-sense-factura")
    assert Expense.objects.get().amount_cents == 25050


def test_the_treasurer_attaches_and_marks_the_invoice(
    page, live_server, transactional_db, review, tmp_path
):
    """T-M09-04b i T-M09-15: adjuntar la factura i marcar-la il·legible (fitxer inventat)."""
    from apps.expenses import services
    from apps.expenses.tests.test_expenses import data

    treasurer = make_admin("tresorer.prova", "treasurer")
    expense = services.record_expense(
        by=treasurer, **data(Supplier.objects.create(name="Nàutica Inventada SL"))
    )
    invoice = tmp_path / "factura.pdf"
    invoice.write_bytes(b"%PDF-1.7\n%factura inventada\n")
    login_admin(page, live_server.url, treasurer.login)

    page.goto(f"{live_server.url}{reverse('administration:expense_documents', args=[expense.pk])}")
    expect(page.get_by_role("heading", name="Documents de la despesa")).to_be_visible()
    review("despesa-documents")
    # T-DX-116 (RN-M09-25): la vista prèvia és només al navegador, amb un URL blob: en memòria.
    photo = tmp_path / "factura.png"
    photo.write_bytes(_png(480, 300))
    field = page.get_by_label("Fitxer (PDF, JPG o PNG)").first
    field.set_input_files(photo)
    preview = page.get_by_role("img", name="Vista prèvia del fitxer triat")
    expect(preview).to_be_visible()
    assert preview.get_attribute("src").startswith("blob:")
    review("despesa-documents-vista-previa")
    field.set_input_files(invoice)
    expect(preview).to_have_count(0)
    expect(page.locator("iframe.zm-vista").first).to_have_attribute("src", re.compile("^blob:"))
    page.get_by_role("button", name="Desa el document").first.click()
    expect(page.get_by_text("Document desat")).to_be_visible()
    review("despesa-documents-factura")

    page.get_by_label("Motiu, si no es llegeix").first.fill("No es llegeix l'import")
    page.get_by_role("button", name="Marca'l com a il·legible").first.click()
    expect(page.get_by_text("Il·legible: cal pujar-lo de nou")).to_be_visible()
    page.goto(f"{live_server.url}{reverse('administration:expenses_without_invoice')}")
    expect(page.get_by_text("Factura il·legible")).to_be_visible()
    review("despeses-sense-factura-illegible")
