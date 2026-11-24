"""Documents de justificació d'una despesa (T-M09-25b; 051; RN-M09-23, 25 i 27; M09-6).

Factura (MG1) i comprovant del banc (MG2), desats xifrats (T-M09-25a): només els obren el
tresorer i la junta (C5). Còpia emmascarada: sense biblioteca de PDF ni d'imatge no es troba
l'IBAN; tots queden «not_detected» i el tresorer en puja la còpia a mà (D2, P-550; CA-M09-24).
«Il·legible»: una `DocumentIllegibleMark` (mai s'escriu a `Expense`), amb avís sense enllaç a qui
l'havia pujat; el document nou la tanca. Tot queda al registre de la marca (RN-M09-27)."""

from django.db import IntegrityError, transaction
from django.db.models import Exists, Q
from django.dispatch import Signal
from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core import audit, files, mail
from apps.core.models import PrivateFile
from apps.core.permissions import has_perm

from .models import DocumentIllegibleMark, Expense
from .services import PAY, RECORD, ExpenseLocked, ExpenseRejected, _require, open_marks

Document = DocumentIllegibleMark.Document
OPEN_DOCUMENTS = "expenses.documents.open"  # C5
ILLEGIBLE_TEMPLATE = "avis-document-illegible"
DOCUMENT_ATTACHED = "expenses.document_attached"
MASKED_COPY_ATTACHED = "expenses.masked_copy_attached"
MARKED_ILLEGIBLE = "expenses.document_marked_illegible"
DOCUMENT_REPLACED = "expenses.document_replaced"

# M09-6: PDF, JPG o PNG.
DOCUMENT_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png"})
_EXTENSION = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png"}
# document → (tipus de fitxer, permís per pujar-lo, nom). Els camps d'`Expense` són
# `<document>_file` i `<document>_masked_file`.
_FIELDS = {
    Document.INVOICE: (PrivateFile.Kind.EXPENSE_INVOICE, RECORD, "factura"),
    Document.PAYMENT_PROOF: (PrivateFile.Kind.EXPENSE_BANK_PROOF, PAY, "comprovant"),
}

# Senyal intern (M09-ajuts-8): l'apartat d'ajuts avisa el tresorer si el document és en una
# versió enviada d'un paquet (RN-M09A-18). Arguments: `expense`, `document`.
document_marked_illegible = Signal()


def _treasurer(by) -> None:
    """Marcar i emmascarar: qui paga despeses (MG2) i pot obrir el document (C5)."""
    _require(by, PAY)
    if not has_perm(by, OPEN_DOCUMENTS):
        raise Http404


def _store(by, expense, uploaded, kind, name) -> PrivateFile:
    content_type = files.validate_upload(uploaded, allowed=DOCUMENT_TYPES)
    uploaded.seek(0)
    return files.store(
        uploaded.read(),
        owner=by.person,
        kind=kind,
        content_type=content_type,
        download_name=f"{name}-despesa-{expense.pk}.{_EXTENSION[content_type]}",
    )


def _open_mark(expense, document):
    return DocumentIllegibleMark.objects.filter(
        expense=expense, document=document, replaced_at__isnull=True
    ).first()


@transaction.atomic
def attach(expense: Expense, document: str, uploaded, *, by, request=None) -> PrivateFile:
    """Adjunta la factura (MG1) o el comprovant del banc (MG2). Si el document tenia una marca
    d'il·legible oberta, el nou la tanca (`replaced_at`) i el registre és de la marca; si ja n'hi
    ha un de vigent i llegible, es rebutja: no se substitueix cap justificant sense la marca."""
    kind, permission, name = _FIELDS[document]
    file_field, masked_field = f"{document}_file", f"{document}_masked_file"
    _require(by, permission)
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status == Expense.Status.ANNULLED:
        raise ExpenseLocked(_("Una despesa anul·lada no rep cap document."))
    mark = _open_mark(expense, document)
    if getattr(expense, file_field) is not None and mark is None:
        raise ExpenseRejected(_("Aquesta despesa ja té el document. Si és il·legible, marca'l."))
    file = _store(by, expense, uploaded, kind, name)
    setattr(expense, file_field, file)
    setattr(expense, masked_field, None)  # el document nou necessita la seva còpia
    expense.save(update_fields=[file_field, masked_field, "updated_at"])
    details = {"document": document, "file": str(file.pk)}
    if mark is None:
        audit.record(DOCUMENT_ATTACHED, actor=by, target=expense, details=details, request=request)
    else:
        mark.replaced_at = timezone.now()
        mark.save(update_fields=["replaced_at"])
        details = {"expense": expense.pk, "document": document, "new_file": str(file.pk)}
        audit.record(DOCUMENT_REPLACED, actor=by, target=mark, details=details, request=request)
    return file


@transaction.atomic
def attach_masked_copy(expense: Expense, document: str, uploaded, *, by, request=None):
    """El tresorer puja la còpia amb l'IBAN emmascarat d'un document vigent (CA-M09-24)."""
    _treasurer(by)
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if getattr(expense, f"{document}_file") is None:
        raise ExpenseRejected(_("Primer cal el document original."))
    name = f"{_FIELDS[document][2]}-emmascarat"
    file = _store(by, expense, uploaded, PrivateFile.Kind.EXPENSE_MASKED_COPY, name)
    setattr(expense, f"{document}_masked_file", file)
    expense.save(update_fields=[f"{document}_masked_file", "updated_at"])
    details = {"document": document, "file": str(file.pk)}
    audit.record(MASKED_COPY_ATTACHED, actor=by, target=expense, details=details, request=request)
    return file


@transaction.atomic
def mark_illegible(
    expense: Expense, document: str, *, reason: str, by, request=None
) -> DocumentIllegibleMark:
    """Marca el document vigent com a il·legible (RN-M09-25). No escriu mai a la despesa."""
    _treasurer(by)
    reason = (reason or "").strip()
    if not reason:
        raise ExpenseRejected(_("Cal escriure el motiu."))
    expense = Expense.objects.get(pk=expense.pk)
    file = getattr(expense, f"{document}_file")
    if file is None:
        raise ExpenseRejected(_("Aquesta despesa no té aquest document."))
    try:
        with transaction.atomic():
            mark = DocumentIllegibleMark.objects.create(
                expense=expense,
                document=document,
                file=file,
                reason=reason,
                marked_by=by,
                notified_person=file.owner,
            )
    except IntegrityError as error:
        raise ExpenseRejected(_("Aquest document ja està marcat com a il·legible.")) from error
    audit.record(
        MARKED_ILLEGIBLE,
        actor=by,
        target=mark,
        reason=reason,
        details={"expense": expense.pk, "document": document, "file": str(file.pk)},
        request=request,
    )
    _notify_uploader(mark)
    document_marked_illegible.send(sender=DocumentIllegibleMark, expense=expense, document=document)
    return mark


def _notify_uploader(mark: DocumentIllegibleMark) -> None:
    """Avís a qui l'havia pujat, a l'adreça de notificació dels seus comptes d'administrador
    actius (qui puja documents ho fa des de l'administració). Sense el document ni cap enllaç."""
    from apps.accounts.models import Account

    addresses = (
        Account.objects.filter(
            person=mark.notified_person, kind=Account.Kind.ADMIN, status=Account.Status.ACTIVE
        )
        .exclude(notification_email="")
        .values_list("notification_email", flat=True)
    )
    context = {
        "expense_id": mark.expense_id,
        "document": str(Document(mark.document).label),
        "reason": mark.reason,
    }
    for address in sorted(set(addresses)):
        mail.queue_email(
            ILLEGIBLE_TEMPLATE, to=address, person=mark.notified_person, context=context
        )


def illegible(expense: Expense, document: str) -> bool:
    return _open_mark(expense, document) is not None


def without_payment_proof():
    """«Sense comprovant» (RN-M09-25): pagades, sense comprovant o amb el comprovant il·legible.
    «Sense factura» és `services.without_invoice`."""
    return Expense.objects.filter(status=Expense.Status.PAID).filter(
        Q(payment_proof_file__isnull=True) | Exists(open_marks(Document.PAYMENT_PROOF))
    )


def pending_masking() -> list[tuple[Expense, str]]:
    """Documents vigents sense còpia emmascarada («not_detected», CA-M09-24), per al tresorer."""
    rows = Expense.objects.exclude(status=Expense.Status.ANNULLED).filter(
        Q(invoice_file__isnull=False, invoice_masked_file__isnull=True)
        | Q(payment_proof_file__isnull=False, payment_proof_masked_file__isnull=True)
    )
    return [
        (expense, document)
        for expense in rows.order_by("pk")
        for document in _FIELDS
        if getattr(expense, f"{document}_file_id") and masking_status(expense, document) != "masked"
    ]


def masking_status(expense: Expense, document: str) -> str:
    """«masked» o «not_detected» (M09-6). «no_iban» arribarà amb la detecció (P-550)."""
    return "masked" if getattr(expense, f"{document}_masked_file_id") else "not_detected"
