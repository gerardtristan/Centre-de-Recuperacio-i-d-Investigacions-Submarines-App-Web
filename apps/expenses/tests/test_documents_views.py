"""Pantalla dels documents d'una despesa (T-M09-04b, T-M09-05 i T-M09-15; RN-M09-23, 25 i 27;
CA-M09-24). Els serveis són de la T-M09-25b (`test_documents.py`). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.core.models import OutgoingEmail
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.expenses import documents, services
from apps.expenses.models import DocumentIllegibleMark, Expense, Supplier
from apps.expenses.tests.test_documents import INVOICE, PDF, PROOF, pdf
from apps.expenses.tests.test_expenses import data
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin("treasurer")
    account.notification_email = "tresoreria@example.org"
    account.save()
    return account


@pytest.fixture
def uploader(make_admin):  # noqa: F811
    """MG1 sense C5 (el President): puja la factura, però no la pot tornar a obrir."""
    account = make_admin("president")
    account.notification_email = "presidencia@example.org"
    account.save()
    return account


@pytest.fixture
def expense(treasurer):
    supplier = Supplier.objects.create(name="Nàutica Inventada SL")
    return services.record_expense(by=treasurer, **data(supplier))


def url(item):
    return reverse("administration:expense_documents", args=[item.pk])


def post(client, item, document, action, **extra):
    values = {"document": document, "action": action, **extra}
    return client.post(url(item), values, follow=True)


def test_ca_m09_01_the_uploader_attaches_the_invoice_but_cannot_open_it(expense, uploader):
    client = admin_client(uploader)
    html = main_of(client.get(url(expense)).content.decode())
    assert "Documents de la despesa" in html and "Encara no s'ha adjuntat" in html
    assert "Esborra-la de la galeria" in html  # text d'ajuda de RN-M09-25
    html = main_of(post(client, expense, INVOICE, "attach", fitxer=pdf()).content.decode())
    expense.refresh_from_db()
    assert expense.invoice_file is not None and "Document desat" in html
    assert "Obre el document" not in html  # C5: només el tresorer i la junta
    assert not services.without_invoice().exists()


def test_the_treasurer_opens_it_attaches_the_proof_and_the_masked_copy(expense, treasurer):
    client = admin_client(treasurer)
    post(client, expense, INVOICE, "attach", fitxer=pdf())
    post(client, expense, PROOF, "attach", fitxer=pdf("comprovant.pdf"))
    post(client, expense, INVOICE, "masked", fitxer=pdf("tapada.pdf"))
    expense.refresh_from_db()
    assert expense.payment_proof_file and expense.invoice_masked_file
    assert documents.masking_status(expense, INVOICE) == "masked"
    html = main_of(client.get(url(expense)).content.decode())
    assert html.count("Obre el document") == 2 and html.count("Sense còpia emmascarada") == 1
    opened = client.get(reverse("administration:private_file", args=[expense.invoice_file_id]))
    assert opened.content == PDF  # desxifrat, amb registre (T-M09-25a)


def test_t_m09_15_an_illegible_invoice_is_back_on_the_list_and_can_be_replaced(
    expense, treasurer, uploader
):
    post(admin_client(uploader), expense, INVOICE, "attach", fitxer=pdf())
    client = admin_client(treasurer)
    post(client, expense, INVOICE, "illegible", motiu="No es llegeix l'import")
    mark = DocumentIllegibleMark.objects.get()
    assert OutgoingEmail.objects.filter(to_address="presidencia@example.org").exists()
    listed = main_of(
        client.get(reverse("administration:expenses_without_invoice")).content.decode()
    )
    assert "Factura il·legible" in listed and url(expense) in listed
    html = main_of(
        post(client, expense, INVOICE, "attach", fitxer=pdf("nova.pdf")).content.decode()
    )
    mark.refresh_from_db()
    assert mark.replaced_at is not None and "Document desat" in html
    assert not services.without_invoice().exists()


def test_errors_are_shown_and_nothing_changes(expense, treasurer):
    client = admin_client(treasurer)
    html = main_of(post(client, expense, INVOICE, "attach").content.decode())
    assert "Tria un fitxer." in html
    html = main_of(post(client, expense, INVOICE, "illegible", motiu="x").content.decode())
    assert "no té aquest document" in html
    post(client, expense, INVOICE, "attach", fitxer=pdf())
    html = main_of(post(client, expense, INVOICE, "attach", fitxer=pdf("b.pdf")).content.decode())
    assert "ja té el document" in html
    html = main_of(post(client, expense, PROOF, "attach",
                        fitxer=pdf("virus.exe", b"MZ inventat")).content.decode())  # fmt: skip
    assert "no és permès" in html
    expense.refresh_from_db()
    assert expense.payment_proof_file is None
    for wrong in ({"document": "altre", "action": "attach"}, {"document": INVOICE, "action": "x"}):
        assert client.post(url(expense), wrong).status_code == 404


def test_an_annulled_expense_receives_no_document(expense, treasurer):
    services.annul(expense, reason="Duplicada", by=treasurer)
    client = admin_client(treasurer)
    assert "Desa el document" not in main_of(client.get(url(expense)).content.decode())
    html = main_of(post(client, expense, INVOICE, "attach", fitxer=pdf()).content.decode())
    assert "anul·lada" in html
    assert Expense.objects.get(pk=expense.pk).invoice_file is None


@pytest.mark.parametrize("role", ["secretary", "instructor", "courses_manager"])
def test_without_mg1_or_mg2_not_found(expense, make_admin, role):  # noqa: F811
    client = admin_client(make_admin(role))
    assert client.get(url(expense)).status_code == 404
    assert client.post(url(expense), {"document": INVOICE, "action": "attach"}).status_code == 404


def test_a_missing_expense_is_not_found(treasurer):
    missing = reverse("administration:expense_documents", args=[999999])
    assert admin_client(treasurer).get(missing).status_code == 404
