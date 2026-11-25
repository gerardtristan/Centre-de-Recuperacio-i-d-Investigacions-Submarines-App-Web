"""CA-M09-27 al navegador, a 390 px (T-M09-06; RN-M09-25; 051): el president (MG1, sense C5)
tria la foto d'una factura al mòbil i en veu la vista prèvia; si surt sense «Desa el document», el
servidor no ha rebut cap fitxer i no hi ha res desat; amb «Desa el document», el fitxer queda
xifrat a l'emmagatzematge; i si el vol tornar a obrir, «no trobat». Només dades inventades."""

import pytest
from django.core.files.storage import storages
from django.urls import reverse
from playwright.sync_api import expect

from apps.expenses import services
from apps.expenses.models import Expense, Supplier
from apps.expenses.tests.test_expenses import data

from .conftest import login_admin, make_admin
from .test_despeses import _png

pytestmark = pytest.mark.e2e
MOBILE = {"width": 390, "height": 844}


def test_ca_m09_27_the_photo_only_leaves_the_phone_with_save(
    page, live_server, transactional_db, review, tmp_path, page_checks
):
    president = make_admin("presidenta.prova", "president")
    expense = services.record_expense(
        by=president, **data(Supplier.objects.create(name="Nàutica Inventada SL"))
    )
    photo = tmp_path / "factura.png"
    content = _png(480, 300)
    photo.write_bytes(content)
    url = f"{live_server.url}{reverse('administration:expense_documents', args=[expense.pk])}"
    posts = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    page.set_viewport_size(MOBILE)
    login_admin(page, live_server.url, president.login)
    posts.clear()  # els de l'entrada no compten

    # Tria la foto i en veu la vista prèvia: només al navegador (URL blob: en memòria).
    page.goto(url)
    page.get_by_label("Fitxer (PDF, JPG o PNG)").first.set_input_files(photo)
    preview = page.get_by_role("img", name="Vista prèvia del fitxer triat")
    expect(preview).to_be_visible()
    assert preview.get_attribute("src").startswith("blob:")
    review("despesa-mobil-vista-previa")
    page.set_viewport_size(MOBILE)

    # Surt sense «Desa»: cap petició amb el fitxer, cap fitxer desat.
    # (Sense MG2 no té l'enllaç a «Despeses sense factura»: se'n va a «Registra una despesa».)
    expect(page.get_by_role("link", name="Torna a les despeses sense factura")).to_have_count(0)
    page.goto(f"{live_server.url}{reverse('administration:expense_new')}")
    expect(page.get_by_role("heading", name="Registra una despesa")).to_be_visible()
    assert posts == []
    expense.refresh_from_db()
    assert expense.invoice_file is None

    # Amb «Desa el document», el fitxer arriba i queda xifrat.
    page.goto(url)
    page.get_by_label("Fitxer (PDF, JPG o PNG)").first.set_input_files(photo)
    page.get_by_role("button", name="Desa el document").first.click()
    expect(page.get_by_text("Document desat")).to_be_visible()
    review("despesa-mobil-desada")
    page.set_viewport_size(MOBILE)
    expense = Expense.objects.select_related("invoice_file").get(pk=expense.pk)
    stored = storages["private"].open(expense.invoice_file.storage_key).read()
    assert stored != content and content not in stored and b"PNG" not in stored

    # Sense C5 no el pot tornar a obrir: ni enllaç ni l'adreça forçada.
    expect(page.get_by_role("link", name="Obre el document")).to_have_count(0)
    opened = reverse("administration:private_file", args=[expense.invoice_file.pk])
    page_checks.expect(404, opened)
    page.goto(f"{live_server.url}{opened}")
    expect(page.get_by_role("heading", name="No s'ha trobat la pàgina")).to_be_visible()
