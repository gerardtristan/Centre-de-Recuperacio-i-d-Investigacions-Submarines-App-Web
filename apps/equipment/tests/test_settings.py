"""T-M03-22, part sense nucli: l'ajust `equipment.unreturned_after_days` (VC-29; RN-M03-14) i la
seva lectura des dels serveis. Només dades inventades."""

import datetime

import pytest

from apps.activities.tests.test_attendance import enrolled
from apps.core.models import Setting, SettingVersion
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, handover

from .test_assignments import jacket, keeper, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
LAST_DAY = datetime.date(2027, 6, 15)


def test_the_setting_exists_with_its_range():
    setting = Setting.objects.get(key=handover.UNRETURNED_DAYS)
    assert (setting.module, setting.initial_value, setting.min_value, setting.max_value) == (
        "equipment", 7, 1, 90,
    )  # fmt: skip


def test_rn_m03_14_unreturned_after_the_days_of_the_setting(manager, keeper):  # noqa: F811
    row = assignments.assign_club(enrolled(outing(manager)), jacket(keeper), by=keeper)
    handover.deliver(row, by=keeper)
    assert list(handover.unreturned(LAST_DAY + datetime.timedelta(days=7))) == []
    assert list(handover.unreturned(LAST_DAY + datetime.timedelta(days=8))) == [row]
    # Un valor nou de l'ajust (amb historial) es llegeix des del servei.
    setting = Setting.objects.get(key=handover.UNRETURNED_DAYS)
    SettingVersion.objects.create(
        setting=setting, value=3, effective_from=datetime.date(2027, 1, 1),
        changed_by=keeper, note="Prova inventada.",
    )  # fmt: skip
    assert list(handover.unreturned(LAST_DAY + datetime.timedelta(days=4))) == [row]
    handover.give_back(row, by=keeper)
    assert list(handover.unreturned(LAST_DAY + datetime.timedelta(days=30))) == []
