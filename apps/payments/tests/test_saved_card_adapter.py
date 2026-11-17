"""Targeta guardada, primera part (T-M05a-12a; RN-M05a-10; CA-M05a-15; P-297): l'adaptador, el
proveïdor fals i els models. Sense xarxa; només dades inventades."""

from dataclasses import replace
from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from django.test import RequestFactory

from apps.accounts.models import Account
from apps.members.tests.test_cards import make_member
from apps.payments.models import CardSetup, SavedCard
from apps.payments.providers import base, fake
from apps.payments.tests.provider_contract import URLS, a_charge
from conftest import PASSWORD

CARD = base.ProviderCard("fake-card-referencia-opaca", "4821", 8, 2029)


@pytest.fixture(autouse=True)
def clean_orders():
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def provider(monkeypatch):
    original = fake.FakeProvider.capabilities
    monkeypatch.setattr(
        fake.FakeProvider, "capabilities", lambda self: replace(original(self), tokenization=True)
    )
    return fake.FakeProvider()


def verify(provider, body, headers):
    request = RequestFactory().post(
        "/pagaments/notificacions/fake", data=body, content_type="application/json", headers=headers
    )
    return provider.verify_notification(request)


def test_without_tokenization_there_is_no_card_setup(monkeypatch):
    original = fake.FakeProvider.capabilities
    monkeypatch.setattr(
        fake.FakeProvider, "capabilities", lambda self: replace(original(self), tokenization=False)
    )
    with pytest.raises(base.NotSupported):
        fake.FakeProvider().start_card_setup(None, URLS)


def test_a_card_setup_is_a_zero_euro_order_with_its_page(provider):
    order = provider.start_card_setup(None, URLS)

    assert order.external_id.startswith(fake.SETUP_PREFIX) and order.pay_url
    assert provider.get_order(order.external_id).amount_cents == 0


def test_an_accepted_setup_keeps_the_card_and_only_its_reference_and_display_data(provider):
    order = provider.start_card_setup(None, URLS)
    with pytest.raises(base.ProviderError):
        provider.get_card_setup(order.external_id)  # encara no

    body, headers = provider.notification(order.external_id, base.PAID, card=CARD)
    assert verify(provider, body, headers).amount_cents == 0
    assert provider.get_card_setup(order.external_id) == CARD


def test_zero_euros_only_for_a_card_setup(provider):
    order = provider.create_order(a_charge(), base.CARD, URLS, uuid4())
    body, headers = provider.notification(order.external_id, base.PAID)
    body = body.replace(b'"amount_cents": 9000', b'"amount_cents": 0')
    with pytest.raises(base.MalformedNotification):
        verify(provider, body, {fake.SIGNATURE_HEADER: fake.sign(body)})


def test_charging_a_saved_card_is_not_there_yet(provider):
    # El cobrament amb la targeta guardada arriba amb la T-M05b-15.
    with pytest.raises(base.NotSupported):
        provider.charge_saved_card(a_charge(), None, uuid4())


@pytest.mark.django_db
def test_p_297_one_active_card_per_person_in_the_database():
    person = make_member().person
    SavedCard.objects.create(
        person=person, provider_code="fake", provider_card_id="a", last4="1111"
    )
    SavedCard.objects.create(
        person=person, provider_code="fake", provider_card_id="b", last4="2222", status="removed"
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        SavedCard.objects.create(
            person=person, provider_code="fake", provider_card_id="c", last4="3333"
        )


@pytest.mark.django_db
def test_a_saved_setup_has_its_card():
    person = make_member().person
    account = Account.objects.create_personal(person, "anna.prova@example.org", PASSWORD)
    with pytest.raises(IntegrityError), transaction.atomic():
        CardSetup.objects.create(
            person=person,
            started_by=account,
            provider_code="fake",
            provider_order_id="fake-setup-1",
            status="saved",
        )
