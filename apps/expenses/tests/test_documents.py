"""T-M09-25b: documents de justificació d'una despesa (051; RN-M09-23, 25 i 27; CA-M09-23, 24,
28, 30 a 34). Només dades inventades."""

from datetime import date

import pytest
from django.core.files.storage import storages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.forms.models import model_to_dict
from django.http import Http404
from django.urls import reverse

from apps.core.models import AuditEntry, OutgoingEmail, PrivateFile
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import documents, services
from apps.expenses.models import DocumentIllegibleMark, Expense, Supplier
from apps.expenses.tests.test_expenses import data
from apps.members.tests.test_roster import admin_client
from apps.treasury.models import TreasuryAccount

pytestmark = pytest.mark.django_db
INVOICE, PROOF = documents.Document.INVOICE, documents.Document.PAYMENT_PROOF
PDF = b"%PDF-1.7\n%factura inventada\n"
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


def pdf(name="factura.pdf", content=PDF):
    return SimpleUploadedFile(name, content)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin("treasurer")
    account.notification_email = "tresoreria@example.org"
    account.save()
    return account


@pytest.fixture
def uploader(make_admin):  # noqa: F811
    """Qui registra la despesa i puja la factura (MG1) sense poder-la tornar a obrir (C5)."""
    account = make_admin("president")
    account.notification_email = "presidencia@example.org"
    account.save()
    return account


@pytest.fixture
def expense(treasurer):
    supplier = Supplier.objects.create(name="Nàutica Inventada SL")
    return services.record_expense(by=treasurer, **data(supplier))


@pytest.fixture
def with_invoice(expense, uploader):
    documents.attach(expense, INVOICE, pdf(), by=uploader)
    return Expense.objects.get(pk=expense.pk)


def paid(expense, treasurer):
    bank = TreasuryAccount.objects.get(name="Banc principal")
    return services.pay(expense, account=bank, value_date=date(2026, 10, 15), by=treasurer)


def expense_entries(expense):
    return AuditEntry.objects.filter(target_type="expenses.expense", target_id=str(expense.pk))


def mark_entries(mark):
    return AuditEntry.objects.filter(
        target_type="expenses.documentillegiblemark", target_id=str(mark.pk)
    )


# --- Desar xifrat i qui l'obre (CA-M09-23, 24; RN-M09-23) -------------------------------------


def test_ca_m09_23_la_factura_es_desa_xifrada_i_nomes_lobren_el_tresorer_i_la_junta(
    with_invoice,
    treasurer,
    uploader,
    make_admin,  # noqa: F811
):
    file = with_invoice.invoice_file
    assert (file.kind, file.owner) == ("expense_invoice", uploader.person)
    with storages["private"].open(file.storage_key, "rb") as handle:
        assert b"factura inventada" not in handle.read()

    url = reverse("administration:private_file", args=[file.pk])
    for account in (treasurer, make_admin("board")):
        response = admin_client(account).get(url)
        assert (response.status_code, response.content) == (200, PDF)
    # L'administrador, el responsable de cursos i qui l'ha pujada: «no trobat».
    for account in (make_admin("administrator"), make_admin("courses_manager"), uploader):
        assert admin_client(account).get(url).status_code == 404


def test_ca_m09_24_sense_deteccio_queda_not_detected_fins_a_la_copia_a_ma(
    expense,
    uploader,
    treasurer,
    make_admin,  # noqa: F811
):
    documents.attach(expense, INVOICE, SimpleUploadedFile("foto.jpg", JPEG), by=uploader)
    expense.refresh_from_db()
    assert documents.masking_status(expense, INVOICE) == "not_detected"
    assert documents.pending_masking() == [(expense, INVOICE)]

    for role in ("administrator", "board"):  # sense C5 o sense MG2
        with pytest.raises(Http404):
            documents.attach_masked_copy(expense, INVOICE, pdf(), by=make_admin(role))
    copy = documents.attach_masked_copy(expense, INVOICE, pdf("copia.pdf"), by=treasurer)
    expense.refresh_from_db()
    assert copy.kind == PrivateFile.Kind.EXPENSE_MASKED_COPY
    assert documents.masking_status(expense, INVOICE) == "masked"
    assert documents.pending_masking() == []


def test_el_comprovant_del_banc_demana_mg2(expense, uploader, treasurer):
    with pytest.raises(Http404):
        documents.attach(expense, PROOF, pdf(), by=uploader)
    file = documents.attach(expense, PROOF, pdf(), by=treasurer)
    assert file.kind == PrivateFile.Kind.EXPENSE_BANK_PROOF


def test_un_document_llegible_no_se_substitueix_i_una_anullada_no_en_rep(
    with_invoice, uploader, treasurer
):
    with pytest.raises(services.ExpenseRejected):
        documents.attach(with_invoice, INVOICE, pdf(), by=uploader)
    services.annul(with_invoice, reason="Duplicada (inventat)", by=treasurer)
    with pytest.raises(services.ExpenseLocked):
        documents.attach(with_invoice, PROOF, pdf(), by=treasurer)


# --- Il·legible (CA-M09-28, 30, 31, 33, 34) -----------------------------------------------------


def test_ca_m09_28_marcar_avisa_sense_enllac_i_la_despesa_surt_sense_factura(
    with_invoice, treasurer, uploader
):
    assert with_invoice not in services.without_invoice()
    received = []

    def listener(**kw):
        received.append((kw["expense"].pk, kw["document"]))

    documents.document_marked_illegible.connect(listener)
    try:
        mark = documents.mark_illegible(with_invoice, INVOICE, reason="Borrosa", by=treasurer)
    finally:
        # Només el d'aquesta prova: el de la 09A (grants.apps) s'ha de quedar connectat.
        documents.document_marked_illegible.disconnect(listener)

    assert received == [(with_invoice.pk, INVOICE)]
    assert (mark.notified_person, mark.file) == (uploader.person, with_invoice.invoice_file)
    email = OutgoingEmail.objects.get(template="avis-document-illegible")
    assert email.to_address == "presidencia@example.org"
    assert "Borrosa" in email.body_text and "http" not in email.body_text
    assert documents.illegible(with_invoice, INVOICE)
    assert with_invoice in services.without_invoice()

    old_file = with_invoice.invoice_file
    new_file = documents.attach(with_invoice, INVOICE, pdf("nova.pdf"), by=uploader)
    mark.refresh_from_db()
    assert mark.replaced_at is not None
    assert with_invoice not in services.without_invoice()
    assert Expense.objects.get(pk=with_invoice.pk).invoice_file == new_file
    # L'il·legible es conserva xifrat i el tresorer el pot obrir.
    assert PrivateFile.objects.get(pk=old_file.pk).deleted_at is None


def test_ca_m09_30_marcar_una_pagada_no_toca_la_despesa(with_invoice, treasurer):
    expense = paid(with_invoice, treasurer)
    before, entries = (
        model_to_dict(Expense.objects.get(pk=expense.pk)),
        expense_entries(expense).count(),
    )
    updated_at = Expense.objects.get(pk=expense.pk).updated_at

    documents.mark_illegible(expense, INVOICE, reason="Il·legible", by=treasurer)

    after = Expense.objects.get(pk=expense.pk)
    assert model_to_dict(after) == before and after.updated_at == updated_at
    assert expense_entries(expense).count() == entries
    assert AuditEntry.objects.filter(action=documents.MARKED_ILLEGIBLE).count() == 1


def test_ca_m09_31_marca_i_substitucio_queden_al_registre_de_la_marca(
    with_invoice, treasurer, uploader
):
    entries = expense_entries(with_invoice).count()
    mark = documents.mark_illegible(with_invoice, INVOICE, reason="Tallada", by=treasurer)
    new_file = documents.attach(with_invoice, INVOICE, pdf(), by=uploader)

    marked, replaced = mark_entries(mark).order_by("pk")
    assert (marked.action, marked.actor_account, marked.reason) == (
        documents.MARKED_ILLEGIBLE,
        treasurer,
        "Tallada",
    )
    assert marked.details == {
        "expense": with_invoice.pk,
        "document": INVOICE,
        "file": str(with_invoice.invoice_file_id),
    }
    assert (replaced.action, replaced.actor_account) == (documents.DOCUMENT_REPLACED, uploader)
    assert replaced.details["new_file"] == str(new_file.pk)
    assert expense_entries(with_invoice).count() == entries


def test_ca_m09_33_nomes_una_marca_oberta_per_document(with_invoice, treasurer, uploader):
    mark = documents.mark_illegible(with_invoice, INVOICE, reason="Borrosa", by=treasurer)
    with pytest.raises(services.ExpenseRejected):
        documents.mark_illegible(with_invoice, INVOICE, reason="Una altra", by=treasurer)
    with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO expenses_documentillegiblemark (expense_id, document, file_id, reason,"
            " marked_by_id, marked_at, notified_person_id) SELECT expense_id, document, file_id,"
            " 'SQL', marked_by_id, now(), notified_person_id FROM expenses_documentillegiblemark"
            " WHERE id = %s",
            [mark.pk],
        )
    documents.attach(with_invoice, INVOICE, pdf(), by=uploader)
    documents.mark_illegible(with_invoice, INVOICE, reason="També borrosa", by=treasurer)
    assert DocumentIllegibleMark.objects.filter(expense=with_invoice).count() == 2


def test_marcar_demana_el_tresorer_i_un_motiu(with_invoice, treasurer, make_admin):  # noqa: F811
    for role in ("administrator", "board"):  # MG2 sense C5, i C5 sense MG2
        with pytest.raises(Http404):
            documents.mark_illegible(with_invoice, INVOICE, reason="x", by=make_admin(role))
    with pytest.raises(services.ExpenseRejected):
        documents.mark_illegible(with_invoice, INVOICE, reason="  ", by=treasurer)
    with pytest.raises(services.ExpenseRejected):
        documents.mark_illegible(with_invoice, PROOF, reason="Sense comprovant", by=treasurer)
    assert not DocumentIllegibleMark.objects.exists()


def test_ca_m09_34_comprovant_illegible_deixa_la_pagada_sense_comprovant(with_invoice, treasurer):
    expense = paid(with_invoice, treasurer)
    assert expense in documents.without_payment_proof()
    documents.attach(expense, PROOF, pdf("rebut.pdf"), by=treasurer)
    assert expense not in documents.without_payment_proof()

    before = model_to_dict(Expense.objects.get(pk=expense.pk))
    documents.mark_illegible(expense, PROOF, reason="Il·legible", by=treasurer)
    assert expense in documents.without_payment_proof()
    assert model_to_dict(Expense.objects.get(pk=expense.pk)) == before

    documents.attach(expense, PROOF, pdf("rebut-nou.pdf"), by=treasurer)
    assert expense not in documents.without_payment_proof()


# --- Activador de PostgreSQL (CA-M09-32) ----------------------------------------------------------


def _sql(statement, params):
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(statement, params)


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE expenses_documentillegiblemark SET replaced_at = now() - interval '1 day'"
        " WHERE id = %s",
        "UPDATE expenses_documentillegiblemark SET replaced_at = NULL WHERE id = %s",
        "UPDATE expenses_documentillegiblemark SET reason = 'canviat' WHERE id = %s",
        "DELETE FROM expenses_documentillegiblemark WHERE id = %s",
    ],
    ids=["canviar", "buidar", "un-altre-camp", "esborrar"],
)
def test_ca_m09_32_amb_replaced_at_ple_postgresql_ho_rebutja(
    with_invoice, treasurer, uploader, statement
):
    mark = documents.mark_illegible(with_invoice, INVOICE, reason="Borrosa", by=treasurer)
    documents.attach(with_invoice, INVOICE, pdf(), by=uploader)
    with pytest.raises(DatabaseError, match="replaced_at una vegada"):
        _sql(statement, [mark.pk])


def test_ca_m09_32_amb_replaced_at_buit_nomes_sacepta_omplir_lo_una_vegada(with_invoice, treasurer):
    mark = documents.mark_illegible(with_invoice, INVOICE, reason="Borrosa", by=treasurer)
    for statement in (
        "UPDATE expenses_documentillegiblemark SET reason = 'canviat' WHERE id = %s",
        "UPDATE expenses_documentillegiblemark SET replaced_at = now(), reason = 'x' WHERE id = %s",
        "DELETE FROM expenses_documentillegiblemark WHERE id = %s",
    ):
        with pytest.raises(DatabaseError, match="replaced_at una vegada"):
            _sql(statement, [mark.pk])
    _sql("UPDATE expenses_documentillegiblemark SET replaced_at = now() WHERE id = %s", [mark.pk])
    mark.refresh_from_db()
    assert mark.replaced_at is not None and mark.reason == "Borrosa"


def test_t_m09_33_no_copy_needed_without_a_persons_bank_details(
    with_invoice,
    uploader,
    treasurer,
    make_admin,  # noqa: F811
):
    """P-550 (108): el compte del club o d'una empresa no s'emmascara; el tresorer ho marca i el
    document surt de «per emmascarar». Un document nou ho torna a demanar."""
    with pytest.raises(Http404):
        documents.set_masking_not_needed(with_invoice, INVOICE, by=uploader)
    documents.set_masking_not_needed(with_invoice, INVOICE, by=treasurer)
    expense = Expense.objects.get(pk=with_invoice.pk)
    assert documents.masking_status(expense, INVOICE) == "not_needed"
    assert documents.pending_masking() == []
    assert documents.shareable_file(expense, INVOICE) == expense.invoice_file
    entry = AuditEntry.objects.get(action=documents.MASKING_NOT_NEEDED)
    assert (entry.old_value, entry.new_value) == (False, True)
    documents.set_masking_not_needed(expense, INVOICE, value=False, by=treasurer)  # desfer
    expense.refresh_from_db()
    assert documents.masking_status(expense, INVOICE) == "not_detected"
    assert documents.shareable_file(expense, INVOICE) is None
    with pytest.raises(services.ExpenseRejected):
        documents.set_masking_not_needed(expense, PROOF, by=treasurer)  # sense original


def test_t_m09_33_a_new_document_asks_again(with_invoice, uploader, treasurer):
    documents.set_masking_not_needed(with_invoice, INVOICE, by=treasurer)
    documents.mark_illegible(with_invoice, INVOICE, reason="Borrosa", by=treasurer)
    documents.attach(with_invoice, INVOICE, pdf("nova.pdf"), by=uploader)
    expense = Expense.objects.get(pk=with_invoice.pk)
    assert documents.masking_status(expense, INVOICE) == "not_detected"
