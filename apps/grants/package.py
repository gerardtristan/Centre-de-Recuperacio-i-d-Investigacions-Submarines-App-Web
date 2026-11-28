"""Paquet de justificació d'un ajut (T-M09A-10a; P-M09A-F, pas 3; RN-M09A-11; CA-M09A-08 i 15).

`build_package(application, actor, requirement=None)`: de les despeses lligades vigents, només hi
entren les que tenen factura i comprovant del banc llegibles (RN-M09-25); la resta surten a
«excloses» amb el motiu. El ZIP porta les còpies amb l'IBAN emmascarat, excepte si la convocatòria
diu que no les accepta (`accepts_masked_proofs = no`): llavors, els originals (051). Un document
que el tresorer ha marcat que no porta dades bancàries de cap persona física (el compte del club o
d'una empresa) hi va en original (RN-M09-23 precisada per la 108, P-550; T-M09-33). Una despesa
sense la còpia emmascarada que cal també queda exclosa: cap IBAN d'una persona no surt sense que la
convocatòria ho demani (P-593). El ZIP es desa xifrat (GRANT_PACKAGE) i cada document llegit queda
al registre (`files.opened`); si n'hi ha d'excloses, el responsable i el tresorer en reben l'avís.

`submit_package_version` (T-M09A-10b; RN-M09A-18 i 21; CA-M09A-16 i 20): la versió 1 passa la
sol·licitud a «justificada» i en queda el paquet congelat (`submitted_package`); les següents,
només amb un requeriment obert, que en queda respost. Si s'anul·la una despesa d'una versió
enviada o se'n marca il·legible un document, el responsable i el tresorer en reben l'avís i cap
paquet no canvia (CA-M09A-16 i 24)."""

import csv
import hashlib
import io
import zipfile

from django.db import transaction
from django.db.models import Max
from django.utils.translation import gettext as _

from apps.core import audit, files, mail
from apps.core.models import PrivateFile
from apps.expenses import documents
from apps.expenses.models import Expense

from . import reminders
from .justification import JUSTIFY, _check_status
from .models import GrantApplication, GrantCall, JustificationPackage, PackageSubmission
from .requirements import RequirementNotOpen, answer_requirement, is_open
from .services import GrantError, S, _move, require

PACKAGE_BUILT = "grants.package_built"
PACKAGE_SENT = "grants.package_sent"
NOTICE_TEMPLATE = "avis-ajut-paquet"
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
        if masked and documents.shareable_file(expense, document) is None:
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
                file = (
                    documents.shareable_file(expense, document)
                    if masked
                    else getattr(expense, f"{document}_file")
                )
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
    if excluded:
        _notify(application, "excluded", count=len(excluded))
    return package


class PackageAlreadySent(GrantError):
    """Aquest paquet ja és una versió enviada (`PackageSubmission.package` és únic)."""


def _notify(application, kind, **context) -> None:
    """Avís al responsable i al tresorer (RN-M09A-11 i 18): només la sol·licitud, la convocatòria i
    els números; cap document ni dada personal. `kind`: excluded, annulled o illegible."""
    context = {"kind": kind, "application_id": application.pk, "call": application.call.name,
               "body": application.call.body, **context}  # fmt: skip
    for address, person in reminders.addresses(application.responsible).items():
        mail.queue_email(NOTICE_TEMPLATE, to=address, person=person, context=context)


@transaction.atomic
def submit_package_version(application, package, *, sent_on, by, requirement=None):
    require(by, JUSTIFY)
    application = (
        GrantApplication.objects.select_for_update().select_related("call").get(pk=application.pk)
    )
    if package.application_id != application.pk:
        raise GrantError(_("Aquest paquet no és d'aquesta sol·licitud."))
    if PackageSubmission.objects.filter(package=package).exists():
        raise PackageAlreadySent(_("Aquest paquet ja s'ha enviat: genera'n un de nou."))
    if application.status == S.GRANTED and requirement is None:
        version = 1
    elif application.status == S.JUSTIFIED and is_open(requirement, application):
        latest = application.submissions.aggregate(v=Max("version"))["v"]
        version = latest + 1
    elif application.status == S.JUSTIFIED:
        raise RequirementNotOpen(_("Una versió nova demana un requeriment obert."))
    else:
        raise GrantError(_("Només es justifica un ajut concedit."))
    submission = PackageSubmission.objects.create(
        application=application, package=package, version=version, requirement=requirement,
        sent_on=sent_on, sent_by=by,
    )  # fmt: skip
    if version == 1:
        application.submitted_package, application.justified_on = package, sent_on
        _move(application, S.JUSTIFIED, reason="", by=by)
    else:
        answer_requirement(requirement, answered_on=sent_on, by=by)
    audit.record(PACKAGE_SENT, actor=by, target=application,
                 details={"package": package.pk, "version": version})  # fmt: skip
    return submission


def _sent_versions_with(expense_id):
    """Les versions enviades que porten la despesa (JSON `items` del paquet)."""
    return PackageSubmission.objects.filter(
        package__items__contains=[{"expense": expense_id}]
    ).select_related("application__call", "application__responsible")


def on_expense_annulled(sender, expense, **kwargs) -> None:
    """Subscriptor del senyal del 09 (RN-M09A-18; CA-M09A-16): avís; cap paquet no canvia."""
    for submission in _sent_versions_with(expense.pk):
        _notify(submission.application, "annulled", version=submission.version,
                expense_id=expense.pk)  # fmt: skip


def on_document_marked_illegible(sender, expense, document, **kwargs) -> None:
    """Subscriptor de `documents.document_marked_illegible` (RN-M09A-18; CA-M09A-24)."""
    for submission in _sent_versions_with(expense.pk):
        _notify(submission.application, "illegible", version=submission.version,
                expense_id=expense.pk, document=str(Document(document).label))  # fmt: skip
