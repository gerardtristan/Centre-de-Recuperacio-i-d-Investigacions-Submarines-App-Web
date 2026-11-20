"""«Ja en tinc una» (T-M06-08; CA-M06-12; RN-M06-14; LC3)."""

import datetime

import pytest
from django.http import Http404

from apps.core.models import AuditEntry, Charge, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import services
from apps.licences.models import Licence, LicenceType, ValidityRule
from apps.licences.services import (
    DateInPast,
    DayLicencesDisabled,
    InvalidFederationNumber,
    NotAvailable,
    declare_existing,
)
from apps.licences.tests.test_request import TODAY, options, soci  # noqa: F401 (fixtures)

D = datetime.date
R = Role.Code
END_OF_YEAR = D(2027, 12, 31)


def declare(actor, person, licence_type, number="CAT-12345", expires_on=END_OF_YEAR, **kw):
    return declare_existing(
        person, licence_type, federation_number=number, expires_on=expires_on, actor=actor,
        today=TODAY, **kw,
    )  # fmt: skip


def test_ca_m06_12_active_external_without_charge(options, soci, annual):  # noqa: F811
    licence = declare(soci, soci.person, annual, number="  CAT-12345 ")
    assert (licence.status, licence.origin) == ("active", "external")
    assert (licence.starts_on, licence.expires_on) == (TODAY, D(2027, 12, 31))
    assert licence.federation_number == "CAT-12345"
    assert (licence.charge, licence.price_kind, licence.price_cents) == (None, None, None)
    assert not Charge.objects.exists()
    entry = AuditEntry.objects.get(action=services.ACTION_DECLARED)
    assert "federation_number" not in entry.new_value
    assert services.current(soci.person, D(2027, 12, 31)).origin == "external"


def test_a_given_start_date_is_kept(options, soci, annual):  # noqa: F811
    licence = declare(soci, soci.person, annual, starts_on=D(2027, 1, 10))
    assert licence.starts_on == D(2027, 1, 10)


@pytest.mark.parametrize("role", [R.SECRETARY, R.COURSES_MANAGER, R.TREASURER, R.PRESIDENT])
def test_lc3_roles_declare_it_for_someone_else(options, soci, annual, make_admin, role):  # noqa: F811
    assert declare(make_admin(role), soci.person, annual).origin == "external"


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.EQUIPMENT_MANAGER, R.BOARD, None])
def test_others_get_not_found(options, soci, annual, make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        declare(make_admin(*([role] if role else [])), soci.person, annual)
    with pytest.raises(Http404):
        declare(None, soci.person, annual)
    assert not Licence.objects.exists()


@pytest.mark.parametrize("number", ["", "   ", None, "X" * 31])
def test_the_number_is_required(options, soci, annual, number):  # noqa: F811
    with pytest.raises(InvalidFederationNumber):
        declare(soci, soci.person, annual, number=number)


def test_an_expired_licence_is_rejected(options, soci, annual):  # noqa: F811
    with pytest.raises(DateInPast):
        declare(soci, soci.person, annual, expires_on=D(2027, 3, 14))


def test_an_inactive_type_or_a_disabled_single_day(options, soci, annual):  # noqa: F811
    day = LicenceType.objects.create(
        name="Un dia (inventat)", category="amateur", validity_rule=ValidityRule.SINGLE_DAY
    )
    with pytest.raises(DayLicencesDisabled):
        declare(soci, soci.person, day, expires_on=TODAY)
    options[services.DAY_ENABLED] = True
    assert declare(soci, soci.person, day, expires_on=TODAY).starts_on == TODAY
    annual.active = False
    annual.save()
    with pytest.raises(NotAvailable):
        declare(soci, soci.person, annual)
