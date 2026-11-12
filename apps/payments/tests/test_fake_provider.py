"""El proveïdor fals passa el contracte de l'adaptador (T-M05a-03) i té les seves regles
pròpies: no surt a la xarxa, no es pot fer servir amb l'entorn real i rebutja el que no entén."""

import json
import socket
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory

from apps.payments.providers import base, fake
from apps.payments.tests.provider_contract import (  # noqa: F401 (prova del contracte)
    URLS,
    ProviderContract,
    a_charge,
    test_no_contract_type_can_carry_card_or_bank_data,
)

PATH = "/pagaments/notificacions/fake"


def post(body: bytes, headers: dict):
    return RequestFactory().post(PATH, data=body, content_type="application/json", headers=headers)


@pytest.fixture(autouse=True)
def clean_orders():
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def provider():
    return fake.FakeProvider()


@pytest.fixture
def notify(provider):
    def build(order, status, *, event_id=None, tamper=False, signed=True):
        body, headers = provider.notification(order.external_id, status, event_id=event_id)
        if tamper:
            body = body.replace(b'"amount_cents": 9000', b'"amount_cents": 1')
        return post(body, headers if signed else {})

    return build


class TestFakeProviderContract(ProviderContract):
    pass


def signed(payload) -> tuple[bytes, dict]:
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    return body, {fake.SIGNATURE_HEADER: fake.sign(body)}


def valid_payload(**changes):
    payload = {
        "event_id": "e-1",
        "order_id": "fake-1",
        "status": base.PAID,
        "amount_cents": 9000,
        "currency": "EUR",
    }
    payload.update(changes)
    return payload


def test_never_opens_a_network_connection(provider, notify, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("El proveïdor fals ha intentat sortir a la xarxa.")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    order = provider.create_order(a_charge(), base.CARD, URLS, uuid4())
    provider.verify_notification(notify(order, base.PAID))
    provider.get_order(order.external_id)


@pytest.mark.parametrize("environment", ["live", "LIVE", "produccio", ""])
def test_can_only_be_used_with_the_test_environment(settings, environment):
    settings.PAYMENTS_ENVIRONMENT = environment
    with pytest.raises(ImproperlyConfigured):
        fake.FakeProvider()


def test_signature_with_unexpected_characters_is_rejected_not_an_error(provider):
    body, _ = signed(valid_payload())
    with pytest.raises(base.InvalidSignature):
        provider.verify_notification(post(body, {fake.SIGNATURE_HEADER: "firma-ñ-€"}))


def test_notification_signed_with_another_key_is_rejected(provider):
    order = provider.create_order(a_charge(), base.CARD, URLS, uuid4())
    body, headers = provider.notification(order.external_id, base.PAID, key="una-altra-clau")
    with pytest.raises(base.InvalidSignature):
        provider.verify_notification(post(body, headers))


def test_signature_is_checked_before_reading_the_body(provider):
    with pytest.raises(base.InvalidSignature):
        provider.verify_notification(post(b"aixo no es json", {fake.SIGNATURE_HEADER: "0" * 64}))


@pytest.mark.parametrize(
    "payload",
    [
        b"aixo no es json",
        b"[1, 2, 3]",
        {"event_id": "e-1"},
        valid_payload(status="unknown"),
        valid_payload(amount_cents=0),
        valid_payload(amount_cents=-5),
        valid_payload(amount_cents="9000"),
        valid_payload(amount_cents=90.5),
        valid_payload(amount_cents=True),
    ],
)
def test_signed_notification_that_cannot_be_understood_is_malformed(provider, payload):
    with pytest.raises(base.MalformedNotification):
        provider.verify_notification(post(*signed(payload)))


def test_order_follows_the_last_notification(provider, notify):
    order = provider.create_order(a_charge(), base.CARD, URLS, uuid4())
    assert provider.get_order(order.external_id).status == base.PENDING
    notify(order, base.PAID)
    assert provider.get_order(order.external_id).status == base.PAID


def test_unknown_order_is_an_error(provider):
    with pytest.raises(base.ProviderError):
        provider.get_order("fake-no-existeix")


def test_only_bizum_orders_expire(provider):
    assert provider.create_order(a_charge(), base.CARD, URLS, uuid4()).expires_at is None
    assert provider.create_order(a_charge(), base.BIZUM, URLS, uuid4()).expires_at is not None


@pytest.mark.parametrize("amount", [0, -1, 9001, 10.5, "4000", True])
def test_refund_outside_the_paid_amount_is_refused(provider, amount):
    with pytest.raises(ValueError):
        provider.refund(SimpleNamespace(amount_cents=9000), amount, uuid4())
