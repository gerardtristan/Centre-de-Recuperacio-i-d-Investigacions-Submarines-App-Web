"""Primera llicència d'un alumne nou (T-M06-26 i T-M06-27; RN-M06-28; CA-M06-34 i 35). Només
dades inventades."""

import datetime

import pytest
from django.http import Http404
from django.utils import timezone

from apps.activities.models import CertificationFiling
from apps.core.models import AuditEntry, Charge, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import first
from apps.licences.filing import mark_active, mark_filed
from apps.licences.models import Licence

from .test_request import TODAY, options, priced  # noqa: F401 (fixtures)

R = Role.Code


@pytest.fixture
def secretary(make_admin):  # noqa: F811
    return make_admin(R.SECRETARY)


@pytest.fixture
def entry(make_person, secretary):
    """Una entrada de la llista «Titulacions i llicències per tramitar» (primera estrella)."""
    return CertificationFiling.objects.create(
        kind=CertificationFiling.Kind.COURSE, person=make_person("Nou", "Alumne"),
        status=CertificationFiling.Status.REQUESTED, requested_by=secretary,
        requested_at=timezone.now(),
    )  # fmt: skip


def test_ca_m06_34_request_the_first_licence_then_cal_llicencia_goes(
    entry,
    annual,
    priced,  # noqa: F811
    options,  # noqa: F811
    secretary,
):
    status = first.entry_status(entry, TODAY)
    assert (status.needs_licence, status.licence, status.can_request) == (True, None, True)
    licence = first.request_first(entry, annual, actor=secretary, today=TODAY)
    assert (licence.status, licence.renewal_of, licence.federation_number) == (
        "requested",
        None,
        "",
    )
    assert licence.list_entry == entry and licence.charge.status == Charge.Status.PENDING
    assert AuditEntry.objects.filter(action=first.ACTION_REQUESTED_FIRST).exists()
    # Demanada però no vigent: encara «Cal llicència», però ja sense el botó.
    status = first.entry_status(entry, TODAY)
    assert (status.needs_licence, status.licence, status.can_request) == (True, licence, False)
    with pytest.raises(first.EntryHasLicence):  # una per entrada
        first.request_first(entry, annual, actor=secretary, today=TODAY)
    # T-M06-27: marcada vigent amb el número, desapareix.
    Licence.objects.filter(pk=licence.pk).update(status=Licence.Status.PAID)
    licence.refresh_from_db()
    mark_active(
        mark_filed(licence, actor=secretary, today=TODAY), "FED-1", actor=secretary, today=TODAY
    )
    status = first.entry_status(entry, TODAY)
    assert (status.needs_licence, status.can_request) == (False, False)


def test_a_licensed_person_has_no_button(entry, annual, make_licence, secretary):
    make_licence(
        person=entry.person, status="active", expires_on=TODAY + datetime.timedelta(days=90)
    )
    status = first.entry_status(entry, TODAY)
    assert (status.needs_licence, status.can_request) == (False, False)
    with pytest.raises(first.AlreadyLicensed):
        first.request_first(entry, annual, actor=secretary, today=TODAY)
    with pytest.raises(first.AlreadyLicensed):
        first.grant_included(entry, annual, actor=secretary, today=TODAY)


def test_only_lc5_requests_it(entry, annual, priced, options, make_admin):  # noqa: F811
    with pytest.raises(Http404):
        first.request_first(entry, annual, actor=make_admin(R.INSTRUCTOR), today=TODAY)
    assert not Licence.objects.exists()


def test_ca_m06_35_included_is_paid_free_and_only_once(entry, annual, secretary):
    licence = first.grant_included(entry, annual, actor=secretary, today=TODAY)
    assert (licence.status, licence.price_kind, licence.price_cents, licence.charge) == (
        "paid", "included", 0, None,
    )  # fmt: skip
    assert (licence.origin, licence.renewal_of, licence.list_entry) == ("club", None, entry)
    assert first.grant_included(entry, annual, actor=secretary, today=TODAY) == licence
    assert Licence.objects.count() == 1 and not Charge.objects.exists()
    assert first.entry_status(entry, TODAY).can_request is False
