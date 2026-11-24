"""Paquet de justificació d'un ajut (T-M09A-10a; P-M09A-F, pas 3; RN-M09A-11; CA-M09A-08 i 15).

`build_package(application, actor, requirement=None)`: de les despeses lligades vigents, només hi
entren les que tenen factura i comprovant del banc llegibles (RN-M09-25); la resta surten a
«excloses» amb el motiu. El ZIP porta les còpies amb l'IBAN emmascarat, excepte si la convocatòria
diu que no les accepta (`accepts_masked_proofs = no`): llavors, els originals (051). Una despesa
sense la còpia emmascarada que cal també queda exclosa: cap IBAN no surt sense que la convocatòria
ho demani (P-593). El ZIP es desa xifrat (GRANT_PACKAGE) i cada document llegit queda al registre
(`files.opened`). Enviar-lo i les versions (`PackageSubmission`) són de la T-M09A-10b; l'avís al
tresorer de les excloses espera la plantilla del nucli."""

import csv
import hashlib
import io
import zipfile

from django.db import transaction
from django.utils.translation import gettext as _

from apps.core import audit, files
from apps.core.models import PrivateFile
from apps.expenses import documents
from apps.expenses.models import Expense

from .justification import JUSTIFY, _check_status
from .models import GrantApplication, GrantCall, JustificationPackage
from .services import require

PACKAGE_BUILT = "grants.package_built"
OPEN_DOCUMENTS = "grants.documents.open"  # AJ12: el paquet només l'obren el tresorer i la junta
Document = documents.Document
_NAMES = {Document.INVOICE: "factura", Document.PAYMENT_PROOF: "comprovant"}
_FORMULA = ("=", "+", "-", "@")


def _cell(value) -> str:
    """Un text de CSV que un full de càlcul no executa com a fórmula."""
    text = str(value)
    return f"'{text}" if text.startswith(_FORMULA) else text


def _exclusion(expense, masked) -> str | None:
    if expense.status == Expense.Status.ANNULLED:
        return _("Anul·lada")
    for document in (Document.INVOICE, Document.PAYMENT_PROOF):
        label = Document(document).label
        if getattr(expense, f"{document}_file_id") is None:
            return _("Sense %(document)s") % {"document": label.lower()}
        if documents.illegible(expense, document):
            return _("%(document)s il·legible") % {"document": label}
        if masked and getattr(expense, f"{document}_masked_file_id") is None:
            return _("%(document)s sense còpia emmascarada") % {"document": label}
    return None


@transaction.atomic
def build_package(application, actor, requirement=None) -> JustificationPackage:
    require(actor, JUSTIFY)
    require(actor, OPEN_DOCUMENTS)
    application = (
        GrantApplication.objects.select_for_update().select_related("call").get(pk=application.pk)
    )
    _check_status(application, requirement)
    masked = application.call.accepts_masked_proofs != GrantCall.MaskedProofs.NO
    links = (
        application.expense_links.filter(removed_at__isnull=True)
        .select_related("expense__supplier")
        .order_by("expense__invoice_date", "expense_id")
    )
    items, excluded, rows = [], [], []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for link in links:
            expense = link.expense
            reason = _exclusion(expense, masked)
            if reason:
                excluded.append({"expense": expense.pk, "amount_cents": link.amount_cents,
                                 "reason": reason})  # fmt: skip
                continue
            hashes = {}
            for document, name in _NAMES.items():
                field = f"{document}_masked_file" if masked else f"{document}_file"
                file = getattr(expense, field)
                content = files.open_decrypted(actor, file)
                hashes[document] = hashlib.sha256(content).hexdigest()
                extension = file.download_name.rsplit(".", 1)[-1]
                archive.writestr(f"despesa-{expense.pk}/{name}.{extension}", content)
            items.append({"expense": expense.pk, "amount_cents": link.amount_cents,
                          "sha256": hashes})  # fmt: skip
            rows.append([expense.pk, expense.supplier, expense.invoice_number,
                         expense.invoice_date.isoformat(), link.amount_cents])  # fmt: skip
        totals = {
            "included_cents": sum(i["amount_cents"] for i in items),
            "excluded_cents": sum(e["amount_cents"] for e in excluded),
            "included": len(items),
            "excluded": len(excluded),
        }
        listing = io.StringIO()
        writer = csv.writer(listing)
        header = [_("Despesa"), _("Proveïdor"), _("Factura"), _("Data"), _("Imputat (cèntims)")]
        writer.writerow(header)
        writer.writerows([_cell(v) for v in row] for row in rows)
        writer.writerow([])
        writer.writerow([_("Total imputat (cèntims)"), "", "", "", totals["included_cents"]])
        archive.writestr("llistat.csv", listing.getvalue())
    content = buffer.getvalue()
    file = files.store(
        content,
        owner=actor.person,
        kind=PrivateFile.Kind.GRANT_PACKAGE,
        content_type="application/zip",
        download_name=f"justificacio-ajut-{application.pk}.zip",
    )
    package = JustificationPackage.objects.create(
        application=application, generated_by=actor, file=file, masked=masked,
        sha256=hashlib.sha256(content).hexdigest(), totals=totals, excluded=excluded, items=items,
    )  # fmt: skip
    audit.record(PACKAGE_BUILT, actor=actor, target=application,
                 details={"package": package.pk, "masked": masked, **totals})  # fmt: skip
    return package
