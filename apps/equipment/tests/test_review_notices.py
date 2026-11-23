"""T-M03-14: avís diari de les revisions que vencen (CA-M03-11; RN-M03-15; VC-29). Només dades
inventades."""

import datetime

import pytest

from apps.core.models import OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.equipment import inventory, reviews, tasks
from apps.equipment.models import EquipmentType

pytestmark = pytest.mark.django_db
TODAY = datetime.date(2027, 3, 1)


@pytest.fixture
def keeper(make_admin):  # noqa: F811
    account = make_admin(Role.Code.EQUIPMENT_MANAGER)
    account.notification_email = "material@example.org"
    account.save()
    return account


def regulator(keeper, due_on):
    regulator_type = EquipmentType.objects.get(name="Regulador")
    return inventory.create_item(equipment_type=regulator_type, by=keeper, next_review_on=due_on)


def test_ca_m03_11_the_keeper_gets_one_daily_email_with_the_pieces(keeper, make_admin):  # noqa: F811
    make_admin(Role.Code.EQUIPMENT_MANAGER)  # sense correu de notificació: no en rep
    board = make_admin(Role.Code.BOARD)  # sense MT11: no en rep
    board.notification_email = "junta@example.org"
    board.save()
    soon = regulator(keeper, TODAY + datetime.timedelta(days=30))
    late = regulator(keeper, TODAY - datetime.timedelta(days=1))
    regulator(keeper, TODAY + datetime.timedelta(days=31))  # fora del termini (VC-29: 30)
    assert reviews.send_due_notices(TODAY) == 1
    (email,) = OutgoingEmail.objects.filter(template=reviews.NOTICE_TEMPLATE)
    assert email.to_address == "material@example.org"
    assert soon.code in email.body_text and late.code in email.body_text
    lines = {line.split(" ")[1]: line for line in email.body_text.splitlines() if "MAT-" in line}
    assert set(lines) == {soon.code, late.code}
    assert "vençuda" in lines[late.code] and "vençuda" not in lines[soon.code]


def test_without_pieces_to_review_no_email(keeper):
    regulator(keeper, TODAY + datetime.timedelta(days=90))
    assert reviews.send_due_notices(TODAY) == 0
    assert not OutgoingEmail.objects.exists()


def test_the_daily_task_calls_the_notice(monkeypatch):
    periodic = tasks.app.periodic_registry.periodic_tasks[("equipment.review_notices", "")]
    assert periodic.cron == "0 7 * * *"
    calls = []
    monkeypatch.setattr(reviews, "send_due_notices", lambda: calls.append(1))
    tasks.review_notices.func(timestamp=0)
    assert calls == [1]
