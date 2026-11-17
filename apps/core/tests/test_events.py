"""Esdeveniments entre mòduls i `charge.paid` (decisió 049; T-M05b-21). La conciliació, que també
l'emet, és a `apps/treasury/tests/test_reconciliation_events.py`. Només dades inventades."""

import pytest
from django.db import transaction
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.core import audit, charges, events
from apps.core.models import AuditEntry, Event, EventDelivery, Payment

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-t-m05b-21")
PAYLOAD = {"charge": 1, "kind": "fee", "origin": "proves", "amount_cents": 9000}


@pytest.fixture
def subscribers(monkeypatch):
    """Una llista de subscriptors buida per a cada prova."""
    monkeypatch.setattr(events, "_subscribers", {})


def received_by(calls):
    def on_charge_paid(event):
        calls.append(event.payload)

    return on_charge_paid


def jobs():
    return ProcrastinateJob.objects.filter(task_name="core.deliver_event")


def logged(action):
    return AuditEntry.objects.filter(action=action)


class TestEmit:
    def test_the_event_and_its_job_in_the_same_transaction(self, subscribers):
        event = events.emit(events.CHARGE_PAID, PAYLOAD)
        assert (event.name, event.payload) == ("charge.paid", PAYLOAD)
        (job,) = jobs()
        assert job.args == {"event_id": event.pk} and job.queue_name == "events"
        assert logged(events.EMITTED).get().target_id == str(event.pk)

    def test_if_the_change_is_undone_there_is_no_event(self, subscribers):
        with pytest.raises(RuntimeError), transaction.atomic():
            events.emit(events.CHARGE_PAID, PAYLOAD)
            raise RuntimeError("es desfà el canvi")
        assert not Event.objects.exists() and not jobs().exists()

    def test_only_approved_events(self, subscribers):
        with pytest.raises(ValueError, match="no aprovat"):
            events.emit("charge.returned", PAYLOAD)
        with pytest.raises(ValueError, match="no aprovat"):
            events.subscribe("charge.returned", received_by([]))

    def test_a_charge_that_becomes_paid_emits_charge_paid(self, subscribers, make_person):
        charge = charges.create_charge(
            make_person(), kind="fee", amount_cents=9000, concept="Quota", origin="members",
            by=SYSTEM,
        )  # fmt: skip
        charges.record_payment(charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
        (event,) = Event.objects.all()
        assert event.payload == {
            "charge": charge.pk,
            "kind": "fee",
            "origin": "members",
            "amount_cents": 9000,
        }

    def test_a_charge_that_does_not_become_paid_emits_nothing(self, subscribers, make_person):
        charge = charges.create_charge(
            make_person(), kind="fee", amount_cents=9000, concept="Quota", origin="members",
            by=SYSTEM,
        )  # fmt: skip
        charges.cancel(charge, "Prova", by=SYSTEM)
        assert not Event.objects.exists()


class TestDeliver:
    def test_each_subscriber_once(self, subscribers):
        calls = []
        events.subscribe(events.CHARGE_PAID, received_by(calls))
        event = events.emit(events.CHARGE_PAID, PAYLOAD)
        events.deliver(event.pk)
        assert calls == [PAYLOAD]
        (delivery,) = EventDelivery.objects.all()
        assert delivery.subscriber.endswith("received_by.<locals>.on_charge_paid")
        assert logged(events.DELIVERED).get().details == {"subscriber": delivery.subscriber}

    def test_a_repeated_event_does_not_run_the_subscriber_again(self, subscribers):
        calls = []
        events.subscribe(events.CHARGE_PAID, received_by(calls))
        event = events.emit(events.CHARGE_PAID, PAYLOAD)
        events.deliver(event.pk)
        events.deliver(event.pk)
        assert calls == [PAYLOAD]
        assert EventDelivery.objects.count() == 1
        assert logged(events.REPEATED).count() == 1

    def test_a_failing_subscriber_is_retried_alone_and_its_work_is_undone(self, subscribers):
        calls, attempts = [], []

        def failing(event):
            attempts.append(1)
            Event.objects.create(name="charge.paid", payload={"feina": "a mitges"})
            if len(attempts) == 1:
                raise RuntimeError("Núria Coll")  # el missatge no ha d'arribar al registre

        events.subscribe(events.CHARGE_PAID, received_by(calls))
        events.subscribe(events.CHARGE_PAID, failing)
        event = events.emit(events.CHARGE_PAID, PAYLOAD)
        with pytest.raises(events.DeliveryFailed):
            events.deliver(event.pk)
        assert calls == [PAYLOAD] and EventDelivery.objects.count() == 1
        assert Event.objects.count() == 1  # la feina del que ha fallat s'ha desfet
        failed = logged(events.FAILED).get()
        assert failed.details["error"] == "RuntimeError" and "Núria" not in str(failed.details)

        events.deliver(event.pk)  # el reintent de la cua
        assert calls == [PAYLOAD] and len(attempts) == 2
        assert EventDelivery.objects.count() == 2

    def test_without_subscribers_nothing_to_do(self, subscribers):
        event = events.emit(events.CHARGE_PAID, PAYLOAD)
        events.deliver(event.pk)
        assert not EventDelivery.objects.exists()

    def test_deliveries_are_unique_per_subscriber_in_the_database(self, subscribers):
        event = events.emit(events.CHARGE_PAID, PAYLOAD)
        EventDelivery.objects.create(event=event, subscriber="proves.un")
        with pytest.raises(Exception, match="event_delivery_once"), transaction.atomic():
            EventDelivery.objects.create(event=event, subscriber="proves.un")
