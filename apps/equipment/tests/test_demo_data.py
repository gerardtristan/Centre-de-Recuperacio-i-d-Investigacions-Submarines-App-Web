"""Dades inventades del 03 (part de la T-M03-20): es creen pels serveis, amb el registre, i sense
cap dada personal."""

import datetime

import pytest

from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import demo_data, reports, stock
from apps.equipment.models import CentreRate, DiveCentre, EquipmentItem, TypicalEquipmentTemplate

pytestmark = pytest.mark.django_db
TODAY = datetime.date(2027, 3, 1)


def test_the_03_demo_data(make_admin):  # noqa: F811
    admin = make_admin(Role.Code.ADMINISTRATOR)
    summary = demo_data.create(admin=admin, today=TODAY)
    assert summary == {"centres": 2, "items": 19, "typical": 5, "reviews": 1}
    assert DiveCentre.objects.count() == 2 and CentreRate.objects.count() == 2
    assert TypicalEquipmentTemplate.objects.count() == 5
    assert EquipmentItem.objects.count() == 19
    assert AuditEntry.objects.filter(action__startswith="equipment.").count() >= 19
    lines = stock.stock(TODAY, viewer=admin)
    assert sum(line.total for line in lines) == 19
    due = reports.upcoming_reviews(TODAY, viewer=admin)
    assert [item.type.name for item in due] == ["Regulador"]
