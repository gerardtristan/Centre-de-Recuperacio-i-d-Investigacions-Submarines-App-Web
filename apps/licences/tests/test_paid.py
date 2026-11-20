"""Llicència pagada amb `charge.paid` (T-M06-05; CA-M06-07; RN-M06-09; 049)."""

import pytest

from apps.core import audit, charges, events
from apps.core.models import AuditEntry, Event, Payment
from apps.licences import services
from apps.licences.models import Licence
from apps.licences.tests.test_request import ask, options, priced, soci  # noqa: F401 (fixtures)

SYSTEM = audit.system("proves-t-m06-05")


def paid_event(licence):
    charges.record_payment(licence.charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
    return Event.objects.get(name=events.CHARGE_PAID, payload__charge=licence.charge_id)


def test_the_app_subscribes_to_charge_paid():
    assert any(
        key.endswith("services.on_charge_paid") for key in events._subscribers[events.CHARGE_PAID]
    )


def test_ca_m06_07_paid_once_even_if_the_event_arrives_twice(options, soci, annual, priced):  # noqa: F811
    licence = ask(soci, annual)
    event = paid_event(licence)
    events.deliver(event.pk)
    events.deliver(event.pk)  # la cua el lliura dues vegades
    services.on_charge_paid(event)  # i encara que el subscriptor es cridi de nou
    licence.refresh_from_db()
    assert licence.status == Licence.Status.PAID
    entry = AuditEntry.objects.get(action=services.ACTION_PAID)
    assert (entry.old_value, entry.new_value) == ("requested", "paid")


def test_events_of_other_modules_are_ignored(options, soci, annual, priced):  # noqa: F811
    licence = ask(soci, annual)
    event = Event.objects.create(
        name=events.CHARGE_PAID, payload={"charge": licence.charge_id, "origin": "members"}
    )
    services.on_charge_paid(event)
    licence.refresh_from_db()
    assert licence.status == Licence.Status.REQUESTED


def test_a_cancelled_licence_is_not_revived(options, soci, annual, priced):  # noqa: F811
    licence = ask(soci, annual)
    Licence.objects.filter(pk=licence.pk).update(status="cancelled", cancellation_reason="Prova")
    services.on_charge_paid(paid_event(licence))
    licence.refresh_from_db()
    assert licence.status == Licence.Status.CANCELLED
    assert not AuditEntry.objects.filter(action=services.ACTION_PAID).exists()


@pytest.mark.django_db
def test_an_unknown_charge_does_nothing():
    event = Event.objects.create(
        name=events.CHARGE_PAID, payload={"charge": 0, "origin": "licences"}
    )
    services.on_charge_paid(event)
    assert not AuditEntry.objects.filter(action=services.ACTION_PAID).exists()
