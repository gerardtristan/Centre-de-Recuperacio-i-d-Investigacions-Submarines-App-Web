"""Excepció de client de l'art. 21.2 LSSI (T-M07-36; decisió 108, C.3; P-710): darrere d'un
interruptor apagat. Només dades inventades."""

import pytest
from django.utils import timezone

from apps.core import audit, charges, events
from apps.core.models import Charge, Department, Event, LegalText, Payment, Person, Setting
from apps.website import clients, newsletter
from apps.website.models import ClientObjection, NewsletterEvent, NewsletterSubscription

pytestmark = pytest.mark.django_db
SYSTEM = audit.system("proves-t-m07-36")
EMAIL = "client.inventada@example.org"
B = NewsletterSubscription.Basis
S = NewsletterSubscription.Status


@pytest.fixture
def on():
    Setting.objects.filter(key=clients.SWITCH).update(initial_value=True)


def paid(kind=Charge.Kind.ENROLMENT, email=EMAIL):
    person = Person.objects.create(
        first_name="Client", last_name="Inventada", origin="web", contact_email=email
    )
    general = Department.objects.get(name=Department.GENERAL)
    charge = charges.create_charge(
        person, kind=kind, amount_cents=4500, concept="Concepte inventat", origin="activities",
        by=SYSTEM, department=general,
    )  # fmt: skip
    charges.record_payment(charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM)
    return Event.objects.get(name=events.CHARGE_PAID, payload__charge=charge.pk)


def test_the_app_listens_to_charge_paid():
    assert any(
        k.endswith("clients.on_charge_paid") for k in events._subscribers[events.CHARGE_PAID]
    )


def test_switched_off_by_default_nobody_is_added_and_nothing_is_sent():
    assert Setting.objects.get(key=clients.SWITCH).initial_value is False
    assert clients.on_charge_paid(paid()) is None
    assert not NewsletterSubscription.objects.exists()


@pytest.mark.parametrize("kind", [Charge.Kind.FEE, Charge.Kind.ENROLMENT, Charge.Kind.LICENCE])
def test_switched_on_who_pays_receives_it_with_the_unsubscribe_link(on, kind):
    subscription = clients.on_charge_paid(paid(kind))
    assert (subscription.email, subscription.status, subscription.basis) == (EMAIL, S.CONFIRMED,
                                                                             B.CLIENT)  # fmt: skip
    assert subscription.legal_text is None and subscription.token
    assert NewsletterEvent.objects.filter(subscription=subscription, kind="client").exists()
    assert list(newsletter.recipients()) == [subscription]
    assert clients.on_charge_paid(paid(kind)) is None  # una sola vegada


def test_switching_off_again_stops_sending_to_them(on):
    clients.on_charge_paid(paid())
    Setting.objects.filter(key=clients.SWITCH).update(initial_value=False)
    assert not newsletter.recipients().exists()


def test_the_box_to_say_no_and_an_unsubscribe_are_never_overridden(on):
    clients.object_to(EMAIL.upper())  # la casella en donar les dades
    assert clients.on_charge_paid(paid()) is None
    other = "altra.client@example.org"
    subscription = clients.on_charge_paid(paid(email=other))
    newsletter.unsubscribe(subscription.token)  # la baixa del correu
    assert clients.on_charge_paid(paid(email=other)) is None
    assert NewsletterSubscription.objects.get().status == S.UNSUBSCRIBED
    assert ClientObjection.objects.count() == 2
    assert not ClientObjection.objects.filter(email_hash__contains="@").exists()


def test_an_existing_subscription_is_left_alone(on):
    text = LegalText.objects.create(kind="newsletter", version=1, content="Butlletí inventat")
    newsletter.subscribe(EMAIL, legal_text=text)  # pendent de confirmar
    assert clients.on_charge_paid(paid()) is None
    assert NewsletterSubscription.objects.get().basis == B.CONSENT


def test_a_client_who_subscribes_by_consent_goes_through_the_confirmation(on):
    clients.on_charge_paid(paid())
    text = LegalText.objects.create(kind="newsletter", version=1, content="Butlletí inventat")
    subscription, send = newsletter.subscribe(EMAIL, legal_text=text, now=timezone.now())
    assert send and (subscription.status, subscription.basis) == (S.PENDING, B.CONSENT)


def test_an_anonymised_person_or_one_without_email_is_never_added(on):
    event = paid(email="")
    assert clients.on_charge_paid(event) is None
    event = paid(email="persona.inventada@example.org")
    Person.objects.filter(contact_email="persona.inventada@example.org").update(
        status=Person.Status.ANONYMISED, anonymous_ref="A-9999"
    )
    assert clients.on_charge_paid(event) is None
    assert not NewsletterSubscription.objects.exists()
