"""Ajustos del 08 (T-M08-10; M08-6; RN-M08-07; CA-M08-07). Només dades inventades."""

import datetime
import importlib

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.activities.models import Activity, Enrolment
from apps.activities.tests.helpers import a_person, a_place, outing_data
from apps.core import business_settings
from apps.core.models import AuditEntry, Role, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.dashboard import panels

pytestmark = pytest.mark.django_db
LOW = "dashboard.low_occupancy_pct"
NOW = timezone.make_aware(datetime.datetime(2027, 6, 1, 12))
JUNE = (datetime.date(2027, 6, 1), datetime.date(2027, 6, 30))


def test_m08_6_the_settings_with_their_ranges():
    low = Setting.objects.get(key=LOW)
    assert (low.module, low.value_type, low.initial_value, low.min_value, low.max_value) == (
        "dashboard", "integer", 50, 0, 100,
    )  # fmt: skip
    period = Setting.objects.get(key="dashboard.default_period")
    assert (period.module, period.value_type, period.initial_value) == (
        "dashboard", "choice", "year",
    )  # fmt: skip
    assert period.choices == ["month", "quarter", "year", "last_12_months"]


def test_ca_m08_07_low_occupancy_follows_the_setting(make_admin):  # noqa: F811
    admin = make_admin(Role.Code.ADMINISTRATOR)
    place = a_place(make_admin(Role.Code.COURSES_MANAGER), prices=None)
    day = datetime.date(2027, 6, 14)
    open_one = Activity.objects.create(
        **outing_data(place, starts_on=day, ends_on=day, max_places=20, status=Activity.Status.OPEN)
    )
    for n in range(11):  # 11 de 20: el 55 %
        Enrolment.objects.create(
            activity=open_one, person=a_person(f"Inscrita{n}"), status=Enrolment.Status.CONFIRMED,
            channel="account", price_kind="member", price_cents=4500, created_at=NOW,
        )  # fmt: skip
    assert panels.panel("general", *JUNE, now=NOW)["low_occupancy"].value.value == 0
    business_settings.change(LOW, 60, admin, note="Prova inventada")
    assert panels.panel("general", *JUNE, now=NOW)["low_occupancy"].value.value == 1
    with pytest.raises(ValidationError):
        business_settings.change(LOW, 101, admin, note="Fora de rang")
    entry = AuditEntry.objects.get(action=business_settings.ACTION_CHANGED, field=LOW)
    assert (entry.old_value, entry.new_value) == (50, 60)


def test_the_help_text_migrations_create_exactly_the_catalog_codes():
    codes = []
    for name in ("0001_help_texts", "0003_settings"):
        codes += importlib.import_module(f"apps.dashboard.migrations.{name}").CODES
    assert sorted(codes) == sorted(panels.CATALOG)
