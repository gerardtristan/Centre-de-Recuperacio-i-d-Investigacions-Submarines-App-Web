"""Cancel·lacions com a esdeveniments de la 049 (T-M02-35; RN-M02-36; CA-M02-38). Només dades
inventades."""

import pytest

from apps.activities import cancellation, enrolment
from apps.core import events
from apps.core.models import Event, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, a_member, an_open_outing

pytestmark = pytest.mark.django_db
NOW = BEFORE_DEADLINE
REASON = "Motiu inventat de proves"


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def enrol(activity):
    account = a_member()
    row = enrolment.enrol(activity, account.person, channel="account", actor=account, now=NOW)
    return row, account


def payloads(name):
    return [event.payload for event in Event.objects.filter(name=name).order_by("pk")]


def test_cancelling_an_enrolment_emits_enrolment_cancelled_without_personal_data(manager):
    outing = an_open_outing(manager)
    row, account = enrol(outing)

    cancellation.cancel_enrolment(row, by=account, reason=REASON, now=NOW)

    (payload,) = payloads(events.ENROLMENT_CANCELLED)
    assert payload == {
        "enrolment": row.pk, "activity": outing.pk, "previous_status": "pending_payment",
        "by": "participant",
    }  # fmt: skip
    assert not payloads(events.ACTIVITY_CANCELLED)


def test_cancelling_the_activity_emits_activity_cancelled_and_one_per_enrolment(manager):
    outing = an_open_outing(manager, max_places=1)
    first, _ = enrol(outing)
    waiting, _ = enrol(outing)

    cancellation.cancel_activity(outing, by=manager, reason=REASON, now=NOW)

    assert payloads(events.ACTIVITY_CANCELLED) == [{"activity": outing.pk}]
    sent = payloads(events.ENROLMENT_CANCELLED)
    assert {(p["enrolment"], p["previous_status"], p["by"]) for p in sent} == {
        (first.pk, "pending_payment", "club"),
        (waiting.pk, "waitlisted", "club"),
    }


def test_ca_m02_38_delivered_twice_each_subscriber_applies_it_once(manager, monkeypatch):
    seen = []
    monkeypatch.setattr(events, "_subscribers", {})
    events.subscribe(events.ACTIVITY_CANCELLED, lambda event: seen.append(event.pk))
    outing = an_open_outing(manager)

    cancellation.cancel_activity(outing, by=manager, reason=REASON, now=NOW)
    event = Event.objects.get(name=events.ACTIVITY_CANCELLED)
    events.deliver(event.pk)
    events.deliver(event.pk)

    assert seen == [event.pk]
