"""«Inclou la primera llicència» (T-M02-50; addenda de la 104; RN-M02-57; CA-M02-59) i els
ajustos VC-60 i VC-61. Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import catalogue, services
from apps.activities.models import TrainingCataloguePrice
from apps.core import business_settings
from apps.core.models import AuditEntry, Department, Role, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.expenses.models import ExpenseCategory

from .helpers import an_entry, common_data

pytestmark = pytest.mark.django_db

TODAY = datetime.date(2027, 3, 1)
TOMORROW = TODAY + datetime.timedelta(days=1)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def change(entry, manager, *, includes, on=TODAY, note="Canvi inventat.", member=4500):
    return catalogue.change_prices(
        entry, by=manager, price_member_cents=member, price_non_member_cents=6000,
        valid_from=on, note=note, includes_first_licence=includes, today=TODAY,
    )  # fmt: skip


def test_ca_m02_59_the_activity_copies_the_version_of_its_day(manager):
    entry = an_entry(manager)
    change(entry, manager, includes=True, member=4600)
    change(entry, manager, includes=False, on=TOMORROW, member=4600)
    for day, expected in ((TODAY, True), (TOMORROW, False)):
        course = services.create_course(
            by=manager, catalogue_entry=entry, today=day, **common_data()
        )
        assert course.includes_first_licence is expected
    entry_change = AuditEntry.objects.filter(
        action=catalogue.PRICE_CHANGED, field="includes_first_licence"
    ).order_by("pk")
    assert [(e.old_value, e.new_value) for e in entry_change] == [(False, True), (True, False)]


def test_ca_m02_59_without_note_or_without_ac28_it_is_rejected(manager, make_admin):  # noqa: F811
    entry = an_entry(manager)
    with pytest.raises(ValidationError):
        change(entry, manager, includes=True, note="")
    RolePermission.objects.filter(
        role__code=Role.Code.COURSES_MANAGER, permission_code="activities.first_licence.manage"
    ).delete()
    other = make_admin(Role.Code.COURSES_MANAGER)
    with pytest.raises(Http404):
        change(entry, other, includes=True, member=4700)
    change(entry, other, includes=None, member=4700)  # sense tocar-lo, n'hi ha prou amb AC6
    assert TrainingCataloguePrice.objects.filter(includes_first_licence=True).count() == 0


@pytest.mark.parametrize(
    ("key", "good", "bad"),
    [
        (catalogue.LICENCE_CATEGORY_KEY, "Categoria inventada", "No existeix"),
        (catalogue.HOMOLOGATION_DEPARTMENT_KEY, "General", "No existeix"),
    ],
)
def test_vc_60_and_61_start_empty_and_take_only_active_values(key, good, bad):
    ExpenseCategory.objects.create(name="Categoria inventada")
    assert Department.objects.filter(name="General", active=True).exists()
    assert business_settings.get(key) == ""
    check = business_settings.EXTRA_CHECKS[key]
    check("")
    check(good)
    with pytest.raises(ValidationError):
        check(bad)
