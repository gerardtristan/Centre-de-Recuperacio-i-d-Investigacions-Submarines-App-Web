"""Primera llicència d'un alumne nou, part del 02 (T-M02-51a; RN-M02-58; RN-M06-28; CA-M02-58;
P-530). Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.activities import filings
from apps.activities.models import Activity
from apps.core import business_settings
from apps.core.models import Charge, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences.first import EntryHasLicence
from apps.licences.models import Licence, LicencePrice, LicenceType, ValidityRule

from .test_certificates import course  # noqa: F401 (fixture)
from .test_first_star import pass_and_issue, with_official_level

pytestmark = pytest.mark.django_db


@pytest.fixture
def licence_type(make_admin):  # noqa: F811
    kind = LicenceType.objects.create(
        name="Aficionat (inventat)", category=LicenceType.Category.AMATEUR,
        validity_rule=ValidityRule.CALENDAR_YEAR,
    )  # fmt: skip
    LicencePrice.objects.create(
        licence_type=kind, federation_cost_cents=4000, non_member_surcharge_cents=1000,
        valid_from=datetime.date(2026, 1, 1), note="Preu inventat.",
        created_by=make_admin(Role.Code.TREASURER),
    )  # fmt: skip
    return kind


def includes(course, value=True):  # noqa: F811
    Activity.objects.filter(pk=course.activity.pk).update(includes_first_licence=value)


def choose(licence_type, make_admin):  # noqa: F811
    business_settings.change(
        filings.FIRST_LICENCE_TYPE_KEY, licence_type.name, make_admin(Role.Code.SECRETARY),
        note="Tipus inventat de proves.",
    )  # fmt: skip


def test_ca_m02_58_included_is_free(course, licence_type, make_admin):  # noqa: F811
    with_official_level(course)
    includes(course)
    choose(licence_type, make_admin)
    charges = Charge.objects.count()
    pass_and_issue(course, course.student)
    licence = Licence.objects.get(person=course.student.person)
    assert (licence.status, licence.price_cents, licence.price_kind) == ("paid", 0, "included")
    assert Charge.objects.count() == charges
    filing = licence.list_entry
    secretary = make_admin(Role.Code.SECRETARY)
    with pytest.raises(ValidationError, match="inclosa al curs"):
        filings.request_first_licence(filing, licence_type, by=secretary)
    (row,) = filings.course_pending(by=secretary)
    assert not row["can_request"] and row["licence"] == licence


def test_p_530_without_the_type_nothing_is_created_and_the_list_says_so(course, make_admin):  # noqa: F811
    with_official_level(course)
    includes(course)
    pass_and_issue(course, course.student)
    assert not Licence.objects.exists()
    (row,) = filings.course_pending(by=make_admin(Role.Code.SECRETARY))
    assert row["needs_licence"] and row["type_missing"] and not row["can_request"]


def test_ca_m02_58_not_included_one_charge(course, licence_type, make_admin):  # noqa: F811
    with_official_level(course)
    choose(licence_type, make_admin)
    pass_and_issue(course, course.student)
    assert not Licence.objects.exists()
    secretary = make_admin(Role.Code.SECRETARY)
    (row,) = filings.course_pending(by=secretary)
    assert row["can_request"]
    filings.request_first_licence(row["filing"], licence_type, by=secretary)
    with pytest.raises(EntryHasLicence):  # una segona: el 06 la rebutja
        filings.request_first_licence(row["filing"], licence_type, by=secretary)
    licence = Licence.objects.get(person=course.student.person)
    assert licence.charge_id is not None  # un sol càrrec de llicència: la segona no n'ha creat


def test_the_setting_takes_only_an_active_type(licence_type):
    filings.check_first_licence_type("")
    filings.check_first_licence_type(licence_type.name)
    with pytest.raises(ValidationError):
        filings.check_first_licence_type("No existeix")
