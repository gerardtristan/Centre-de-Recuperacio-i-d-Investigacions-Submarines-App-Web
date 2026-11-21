"""Homologacions a la federació i llistat (T-M02-44 i T-M02-46; addenda de la 104; RN-M02-50, 51,
53 i 55; CA-M02-53 i 54). Només dades inventades."""

import csv
import datetime
import hashlib
import io

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone

from apps.activities import catalogue, filings
from apps.activities.models import CertificationAgency, CertificationFiling, DiverCertification
from apps.core.models import AuditEntry, Person, Role, Setting, SettingVersion
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member

pytestmark = pytest.mark.django_db
F = CertificationFiling
DAY = datetime.date(2027, 3, 1)


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin(Role.Code.SECRETARY)


@pytest.fixture
def levels(make_admin):  # noqa: F811
    manager = make_admin(Role.Code.COURSES_MANAGER)
    padi = CertificationAgency.objects.get(name="PADI")
    fecdas = CertificationAgency.objects.get(name="FECDAS")
    return (
        catalogue.create_level(by=manager, name="Open Water (inventat)", rank=10, agency=padi),
        catalogue.create_level(by=manager, name="B1E (inventat)", rank=11, agency=fecdas),
    )


def padi_cert(person, level, **fields):
    return DiverCertification.objects.create(
        person=person, level=level, agency=level.agency, number="PADI-0001", source="declared",
        **fields,
    )  # fmt: skip


def setting(key, value, by):
    row = Setting.objects.get(key=key)
    day = timezone.localdate() if row.effective_dated else None  # els preus porten data
    SettingVersion.objects.create(
        setting=row, value=value, changed_by=by, note="Prova.", effective_from=day
    )


# --- RN-M02-50: demanar ------------------------------------------------------------------------


def test_rn_m02_50_the_holder_requests_the_homologation_of_another_agency(levels):
    account = a_member()
    cert = padi_cert(account.person, levels[0])

    filing = filings.request_homologation(cert, by=account)

    assert (filing.kind, filing.status, filing.person_id) == (
        "homologation",
        "requested",
        cert.person_id,
    )
    assert (filing.requested_by, filing.charge) == (account, None)  # preu 0: cap càrrec
    assert AuditEntry.objects.filter(action=filings.REQUESTED, target_id=str(filing.pk)).exists()
    with pytest.raises(ValidationError, match="oberta"):
        filings.request_homologation(cert, by=account)


def test_only_the_holder_or_ac25_requests_it(levels, secretary, make_admin):  # noqa: F811
    cert = padi_cert(a_member().person, levels[0])
    for stranger in (a_member("Una altra"), make_admin(Role.Code.COURSES_MANAGER)):
        with pytest.raises(Http404):
            filings.request_homologation(cert, by=stranger)
    assert filings.request_homologation(cert, by=secretary).requested_by == secretary


def test_a_certification_of_the_target_agency_or_without_agency_is_not_homologated(levels):
    account = a_member()
    own = DiverCertification.objects.create(
        person=account.person, level=levels[1], agency=levels[1].agency, source="declared"
    )
    bare = DiverCertification.objects.create(
        person=account.person, level=levels[0], source="declared"
    )
    for cert in (own, bare):
        with pytest.raises(ValidationError, match="agència diferent"):
            filings.request_homologation(cert, by=account)


def test_with_photos_on_the_front_photo_is_needed_and_paid_filings_wait_for_p_427(
    levels,
    make_admin,  # noqa: F811
):
    admin = make_admin(Role.Code.ADMINISTRATOR)
    account = a_member()
    cert = padi_cert(account.person, levels[0])
    setting("activities.card_photos_enabled", True, admin)
    with pytest.raises(ValidationError, match="foto"):
        filings.request_homologation(cert, by=account)
    setting("activities.card_photos_enabled", False, admin)
    setting("activities.filing_fees_enabled", True, admin)
    filings.request_homologation(cert, by=account)  # preu 0: igualment sense càrrec
    F.objects.all().delete()
    setting("activities.homologation_fee_cents", 2500, admin)
    with pytest.raises(ValidationError, match="pagament"):
        filings.request_homologation(cert, by=account)


# --- RN-M02-51: tramitar (AC26) ----------------------------------------------------------------


def test_ca_m02_53_done_creates_a_verified_federation_certification_once(levels, secretary):
    cert = padi_cert(a_member().person, levels[0])
    filing = filings.request_homologation(cert, by=secretary)
    filings.mark_filed(filing, by=secretary)

    done = filings.mark_done(
        filing, by=secretary, target_level=levels[1], number="F-77", issued_on=DAY
    )
    again = filings.mark_done(
        filing, by=secretary, target_level=levels[1], number="F-77", issued_on=DAY
    )

    result = done.result_certification
    assert (done.status, again.result_certification) == ("done", result)
    assert (result.source, result.agency.name, result.level, result.number) == (
        "federation",
        "FECDAS",
        levels[1],
        "F-77",
    )
    assert result.verified_by == secretary and result.is_verified
    cert.refresh_from_db()
    assert cert.verified_by == secretary
    assert DiverCertification.objects.filter(source="federation").count() == 1


def test_done_needs_level_number_date_and_a_level_of_the_target(levels, secretary):
    filing = filings.request_homologation(padi_cert(a_member().person, levels[0]), by=secretary)
    for level, number, day in (
        (levels[1], "", DAY),
        (levels[1], "F-1", None),
        (levels[0], "F-1", DAY),
    ):
        with pytest.raises(ValidationError):
            filings.mark_done(
                filing, by=secretary, target_level=level, number=number, issued_on=day
            )
    filing.refresh_from_db()
    assert filing.status == "requested"


def test_ca_m02_54_rejecting_needs_a_reason_and_does_not_verify(levels, secretary):
    cert = padi_cert(a_member().person, levels[0])
    filing = filings.request_homologation(cert, by=secretary)
    with pytest.raises(ValidationError):
        filings.reject(filing, by=secretary, reason=" ")
    filing.refresh_from_db()
    assert filing.status == "requested"

    rejected = filings.reject(filing, by=secretary, reason="Carnet il·legible (inventat).")

    cert.refresh_from_db()
    assert (rejected.status, cert.is_verified) == ("rejected", False)
    with pytest.raises(ValidationError):
        filings.mark_filed(rejected, by=secretary)
    assert filings.request_homologation(cert, by=secretary).status == "requested"  # una de nova


@pytest.mark.parametrize("role", ["instructor", "courses_manager", "treasurer", "board"])
def test_only_ac26_processes_filings(levels, secretary, make_admin, role):  # noqa: F811
    filing = filings.request_homologation(padi_cert(a_member().person, levels[0]), by=secretary)
    by = make_admin(role)
    with pytest.raises(Http404):
        filings.mark_filed(filing, by=by)
    with pytest.raises(Http404):
        filings.pending(by=by)


def test_the_pending_list_shows_the_open_ones(levels, secretary):
    open_one = filings.request_homologation(padi_cert(a_member().person, levels[0]), by=secretary)
    closed = filings.request_homologation(padi_cert(a_member().person, levels[0]), by=secretary)
    filings.reject(closed, by=secretary, reason="Motiu inventat.")
    assert list(filings.pending(by=secretary)) == [open_one]


# --- T-M02-46: llistat per a la federació (RN-M02-53) -----------------------------------------


def test_rn_m02_53_the_csv_has_the_requested_ones_without_photos_or_documents(levels, secretary):
    person = a_member("Marina").person
    Person.objects.filter(pk=person.pk).update(
        birth_date=datetime.date(1990, 5, 4), id_document_type="dni", id_document_number="00000000T"
    )
    filings.request_homologation(padi_cert(person, levels[0]), by=secretary)
    filed = filings.request_homologation(
        padi_cert(a_member("Altra").person, levels[0]), by=secretary
    )
    filings.mark_filed(filed, by=secretary)

    content = filings.federation_csv(by=secretary)

    rows = list(csv.reader(io.StringIO(content), delimiter=";"))
    assert rows[0] == list(filings.CSV_HEADER)
    assert rows[1:] == [
        ["Prova", "Marina", "1990-05-04", "PADI", "Open Water (inventat)", "PADI-0001", ""]
    ]
    assert "00000000T" not in content and "foto" not in content.lower()
    entry = AuditEntry.objects.get(action=filings.EXPORTED)
    assert entry.details["rows"] == 1
    assert entry.details["sha256"] == hashlib.sha256(content.encode("utf-8")).hexdigest()


def test_the_csv_needs_ac26(levels, make_admin):  # noqa: F811
    with pytest.raises(Http404):
        filings.federation_csv(by=make_admin(Role.Code.COURSES_MANAGER))
