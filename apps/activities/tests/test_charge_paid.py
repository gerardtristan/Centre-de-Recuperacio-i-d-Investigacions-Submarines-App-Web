"""Inscripció confirmada quan es paga el seu càrrec (T-M02-10; CA-M02-07, la part del 02; 049;
L-M02-01). Prova d'esdeveniment repetit. Només dades inventades.
"""

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.activities import charges as activity_charges
from apps.activities import extensions
from apps.activities.models import Enrolment
from apps.core import audit, charges, events
from apps.core.models import AuditEntry, Charge, Event, Payment, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_person, an_outing

pytestmark = pytest.mark.django_db
S = Enrolment.Status
SYSTEM = audit.system("proves-t-m02-10")


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def enrolment(manager, status=S.PENDING_PAYMENT, origin="activities", **fields):
    activity, person = an_outing(manager), a_person("Participant")
    charge = charges.create_charge(
        person, kind=Charge.Kind.ENROLMENT, amount_cents=4500, concept="Sortida inventada",
        origin=origin, by=SYSTEM, department=activity.department,
    )  # fmt: skip
    return Enrolment.objects.create(
        activity=activity, person=person, status=status, channel="account", price_kind="member",
        price_cents=4500, charge=charge, created_at=timezone.now(), **fields,
    )  # fmt: skip


def pay(enrolment):
    charges.record_payment(
        enrolment.charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM
    )
    return Event.objects.get(name=events.CHARGE_PAID, payload__charge=enrolment.charge_id)


def test_the_app_subscribes_to_charge_paid():
    assert any(
        k.endswith("charges.on_charge_paid") for k in events._subscribers[events.CHARGE_PAID]
    )


def test_ca_m02_07_confirmed_once_even_if_the_event_arrives_twice(manager):
    pending = enrolment(manager, payment_due_at=timezone.now())
    heard = []
    extensions.enrolment_confirmed.connect(
        lambda sender, enrolment, **kw: heard.append(enrolment.pk), weak=False, dispatch_uid="t"
    )
    try:
        event = pay(pending)
        events.deliver(event.pk)
        events.deliver(event.pk)  # la cua el lliura dues vegades
        activity_charges.on_charge_paid(event)  # i encara que es cridi de nou
    finally:
        extensions.enrolment_confirmed.disconnect(dispatch_uid="t")
    pending.refresh_from_db()
    assert (pending.status, pending.payment_due_at) == (S.CONFIRMED, None)
    assert heard == [pending.pk]
    entry = AuditEntry.objects.get(action=activity_charges.CONFIRMED)
    assert (entry.old_value, entry.new_value, entry.actor_kind) == (
        "pending_payment",
        "confirmed",
        "system",
    )


def test_events_of_other_modules_and_unpaid_charges_are_ignored(manager):
    other = enrolment(manager, origin="licences")
    pay(other)
    assert (
        activity_charges.on_charge_paid(
            Event(payload={"charge": other.charge_id, "origin": "licences"})
        )
        is None
    )
    unpaid = enrolment(manager)
    fake = Event(
        payload={"charge": unpaid.charge_id, "origin": "activities"}
    )  # no es fia del missatge
    assert activity_charges.on_charge_paid(fake) is None
    for row in (other, unpaid):
        row.refresh_from_db()
        assert row.status == S.PENDING_PAYMENT


@pytest.mark.parametrize("status", [S.EXPIRED, S.CANCELLED])
def test_l_m02_01_a_late_payment_does_not_confirm_and_is_flagged_once(manager, status):
    late = enrolment(manager, status=status, cancelled_reason="Motiu inventat")
    event = pay(late)
    activity_charges.on_charge_paid(event)
    activity_charges.on_charge_paid(event)
    late.refresh_from_db()
    assert late.status == status
    flagged = AuditEntry.objects.get(action=activity_charges.PAID_NOT_CONFIRMED)
    assert flagged.details == {"status": status, "charge": late.charge_id}


def test_one_live_enrolment_per_person_and_activity(manager):
    first = enrolment(manager)
    with pytest.raises(IntegrityError), transaction.atomic():
        Enrolment.objects.create(
            activity=first.activity, person=first.person, status=S.WAITLISTED, channel="account",
            price_kind="member", price_cents=0, waitlist_position=1, created_at=timezone.now(),
        )  # fmt: skip
