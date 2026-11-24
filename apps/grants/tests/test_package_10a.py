"""T-M09A-10a: paquet de justificació (RN-M09A-11; CA-M09A-08 i 15; 051; P-593). Només dades i
fitxers inventats."""

import io
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404

from apps.core import files
from apps.core.models import AppendOnlyError, AuditEntry, PrivateFile
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses import documents
from apps.expenses.models import Supplier
from apps.grants import justification as j
from apps.grants import package as p
from apps.grants.models import GrantApplication, GrantCall
from apps.grants.tests.test_justification import expense
from apps.grants.tests.test_resolution import grant, submitted  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
INVOICE, PROOF = documents.Document.INVOICE, documents.Document.PAYMENT_PROOF


@pytest.fixture
def granted(submitted, treasurer):  # noqa: F811
    return grant(submitted, treasurer)


def pdf(text):
    return SimpleUploadedFile("document.pdf", f"%PDF-1.7\n%{text}\n".encode())


def linked(application, by, amount, number, *, docs=(INVOICE, PROOF), masked=True,
           requirement=None, **extra):  # fmt: skip
    item = expense(by, amount=amount, number=number, **extra)
    for document in docs:
        documents.attach(item, document, pdf(f"{document} {number}"), by=by)
        if masked:
            documents.attach_masked_copy(item, document, pdf(f"tapada {document} {number}"), by=by)
    j.link_expense(application, item, amount, by=by, requirement=requirement)
    return item


def unzip(package, by):
    content = files.open_decrypted(by, package.file)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_ca_m09a_08_the_package_has_the_complete_expenses_and_excludes_the_rest(granted, treasurer):
    first = linked(granted, treasurer, 50000, "F-1")
    second = linked(granted, treasurer, 24000, "F-2")
    missing = linked(granted, treasurer, 6500, "F-3", docs=(PROOF,))
    package = p.build_package(granted, treasurer)
    assert package.totals == {
        "included_cents": 74000, "excluded_cents": 6500, "included": 2, "excluded": 1,
    }  # fmt: skip
    assert package.excluded == [
        {"expense": missing.pk, "amount_cents": 6500, "reason": "Sense factura"}
    ]
    assert [i["expense"] for i in package.items] == [first.pk, second.pk]
    assert (package.file.kind, package.masked) == (PrivateFile.Kind.GRANT_PACKAGE, True)
    content = unzip(package, treasurer)
    assert sorted(content) == [
        f"despesa-{first.pk}/comprovant.pdf", f"despesa-{first.pk}/factura.pdf",
        f"despesa-{second.pk}/comprovant.pdf", f"despesa-{second.pk}/factura.pdf", "llistat.csv",
    ]  # fmt: skip
    assert b"74000" in content["llistat.csv"]
    assert AuditEntry.objects.get(action=p.PACKAGE_BUILT).details["included_cents"] == 74000


def test_ca_m09a_15_masked_copies_unless_the_call_refuses_them(granted, treasurer):
    item = linked(granted, treasurer, 50000, "F-1")
    masked = p.build_package(granted, treasurer)
    assert b"tapada" in unzip(masked, treasurer)[f"despesa-{item.pk}/factura.pdf"]
    GrantCall.objects.filter(pk=granted.call_id).update(accepts_masked_proofs="no")
    originals = p.build_package(granted, treasurer)
    invoice = unzip(originals, treasurer)[f"despesa-{item.pk}/factura.pdf"]
    assert not originals.masked and b"tapada" not in invoice
    assert originals.items[0]["sha256"][INVOICE] != masked.items[0]["sha256"][INVOICE]


def test_p_593_without_the_masked_copy_it_is_excluded(granted, treasurer):
    linked(granted, treasurer, 50000, "F-1", masked=False)
    package = p.build_package(granted, treasurer)
    assert package.excluded[0]["reason"] == "Factura sense còpia emmascarada"


def test_an_illegible_proof_or_an_annulled_expense_is_excluded(granted, treasurer):
    item = linked(granted, treasurer, 50000, "F-1")
    documents.mark_illegible(item, PROOF, reason="No es llegeix", by=treasurer)
    other = linked(granted, treasurer, 1000, "F-2")
    type(other).objects.filter(pk=other.pk).update(status="annulled")
    package = p.build_package(granted, treasurer)
    assert [e["reason"] for e in package.excluded] == [
        "Comprovant del banc il·legible",
        "Anul·lada",
    ]
    assert package.items == []


def test_the_listing_does_not_run_formulas(granted, treasurer):
    supplier = Supplier.objects.create(name='=HYPERLINK("inventat")')
    linked(granted, treasurer, 1000, "F-1", supplier=supplier)
    listing = unzip(p.build_package(granted, treasurer), treasurer)["llistat.csv"].decode()
    assert "'=HYPERLINK" in listing


def test_a_package_never_changes(granted, treasurer):
    package = p.build_package(granted, treasurer)
    package.masked = False
    with pytest.raises(AppendOnlyError):
        package.save()


def test_only_a_granted_application_without_a_sent_justification(granted, treasurer):
    applications = GrantApplication.objects.filter(pk=granted.pk)
    applications.update(status="submitted")
    with pytest.raises(j.GrantError):
        p.build_package(granted, treasurer)
    applications.update(status="justified", justified_on="2027-06-01")
    with pytest.raises(j.AlreadyJustified):
        p.build_package(granted, treasurer)


@pytest.mark.parametrize("role", ["board", "secretary", "administrator"])
def test_without_aj7_and_aj12_not_found(granted, make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        p.build_package(granted, make_admin(role))
