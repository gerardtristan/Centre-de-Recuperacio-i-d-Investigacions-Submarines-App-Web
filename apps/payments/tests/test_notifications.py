"""Notificacions del proveïdor (T-M05a-04; CA-M05a-10 i CA-M05a-11; arquitectura §4.2)."""

import hashlib
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.db import IntegrityError, transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.core.models import UndeletableError
from apps.payments import webhooks
from apps.payments.models import ProviderEvent, ProviderEventLocked
from apps.payments.providers import base, fake

pytestmark = pytest.mark.django_db
R = ProviderEvent.Result
URL = reverse("payments:provider_notification", args=["fake"])
URLS = base.OrderUrls("https://example.org/n", "https://example.org/ok", "https://example.org/ko")


@pytest.fixture(autouse=True)
def clean_orders():
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def provider():
    return fake.FakeProvider()


@pytest.fixture
def order(provider):
    charge = SimpleNamespace(pk=1, amount_cents=9000, currency="EUR", concept="Quota anual")
    return provider.create_order(charge, base.CARD, URLS, uuid4())


@pytest.fixture
def visitor():
    """Sense sessió i amb la comprovació de CSRF activada, com un servidor de fora."""
    return Client(enforce_csrf_checks=True)


def send(client, body: bytes, headers: dict, **extra):
    return client.post(URL, data=body, content_type="application/json", headers=headers, **extra)


def events(result=None):
    rows = ProviderEvent.objects.order_by("pk")
    return list(rows.filter(result=result) if result else rows)


class TestAccepted:
    def test_valid_notification_is_stored_and_answered_at_once(self, visitor, provider, order):
        body, headers = provider.notification(order.external_id, base.PAID, event_id="e-1")
        assert send(visitor, body, headers).status_code == 200
        (event,) = events()
        assert (event.provider_code, event.external_id, event.result) == ("fake", "e-1", R.RECEIVED)
        assert (event.order_id, event.event_type) == (order.external_id, base.PAID)
        assert (event.amount_cents, event.currency) == (9000, "EUR")
        assert event.payload_hash == hashlib.sha256(body).hexdigest()
        assert event.processed_at is None  # el processament és del 05b (T-M05b-05)

    def test_ca_m05a_11_a_repeated_notification_is_answered_and_not_accepted_again(
        self, visitor, provider, order
    ):
        body, headers = provider.notification(order.external_id, base.PAID, event_id="e-1")
        assert send(visitor, body, headers).status_code == 200
        assert send(visitor, body, headers).status_code == 200
        assert send(visitor, body, headers).status_code == 200
        assert len(events(R.RECEIVED)) == 1
        assert len(events(R.IGNORED_DUPLICATE)) == 2

    def test_two_events_of_the_same_order_are_two_rows(self, visitor, provider, order):
        send(visitor, *provider.notification(order.external_id, base.DENIED))
        send(visitor, *provider.notification(order.external_id, base.PAID))
        assert [e.event_type for e in events(R.RECEIVED)] == [base.DENIED, base.PAID]

    def test_signed_notification_that_cannot_be_understood_goes_to_review(self, visitor):
        body = json.dumps({"event_id": "e-1"}).encode()
        response = send(visitor, body, {fake.SIGNATURE_HEADER: fake.sign(body)})
        assert response.status_code == 200  # el proveïdor no l'ha de tornar a enviar
        (event,) = events()
        assert (event.result, event.external_id, event.amount_cents) == (R.TO_REVIEW, "", None)

    @pytest.mark.parametrize(
        "changes", [{"event_id": "e" * 101}, {"order_id": "o" * 101}, {"amount_cents": 10**30}]
    )
    def test_signed_notification_with_a_value_that_does_not_fit_goes_to_review(
        self, visitor, changes
    ):
        payload = {
            "event_id": "e-1",
            "order_id": "fake-1",
            "status": base.PAID,
            "amount_cents": 9000,
            "currency": "EUR",
        }
        body = json.dumps(payload | changes).encode()
        assert send(visitor, body, {fake.SIGNATURE_HEADER: fake.sign(body)}).status_code == 200
        (event,) = events()
        assert (event.result, event.external_id, event.amount_cents) == (R.TO_REVIEW, "", None)


class TestRejected:
    def test_ca_m05a_10_invalid_signature_is_an_error_and_is_recorded_as_rejected(
        self, visitor, provider, order
    ):
        body, headers = provider.notification(order.external_id, base.PAID, key="una-altra-clau")
        assert send(visitor, body, headers).status_code == 400
        (event,) = events()
        assert event.result == R.REJECTED_SIGNATURE
        # No se'n llegeix res: ni l'esdeveniment, ni l'ordre, ni l'import.
        assert (event.external_id, event.order_id, event.amount_cents) == ("", "", None)
        assert event.payload_hash == hashlib.sha256(body).hexdigest()

    def test_altered_or_unsigned_notification_is_rejected(self, visitor, provider, order):
        body, headers = provider.notification(order.external_id, base.PAID)
        assert send(visitor, body.replace(b"9000", b"1"), headers).status_code == 400
        assert send(visitor, body, {}).status_code == 400
        assert [e.result for e in events()] == [R.REJECTED_SIGNATURE] * 2

    def test_a_rejected_notification_does_not_block_the_real_one(self, visitor, provider, order):
        body, headers = provider.notification(order.external_id, base.PAID, event_id="e-1")
        assert send(visitor, body, {fake.SIGNATURE_HEADER: "0" * 64}).status_code == 400
        assert send(visitor, body, headers).status_code == 200
        assert len(events(R.RECEIVED)) == 1

    def test_ca_m05a_10_origin_outside_the_list_is_rejected(
        self, visitor, provider, order, monkeypatch
    ):
        monkeypatch.setattr(fake.FakeProvider, "allowed_ips", ("203.0.113.7",))
        body, headers = provider.notification(order.external_id, base.PAID)
        assert send(visitor, body, headers, REMOTE_ADDR="198.51.100.9").status_code == 400
        assert [e.result for e in events()] == [R.REJECTED_SIGNATURE]
        assert send(visitor, body, headers, REMOTE_ADDR="203.0.113.7").status_code == 200
        assert len(events(R.RECEIVED)) == 1

    def test_rejections_cannot_fill_the_table(self, visitor, monkeypatch):
        monkeypatch.setattr(webhooks, "REJECTED_MAX", 3)
        for _ in range(5):
            assert send(visitor, b"{}", {}).status_code == 400
        assert len(events(R.REJECTED_SIGNATURE)) == 3


class TestRoute:
    def test_only_post(self, visitor):
        assert visitor.get(URL).status_code == 405

    def test_another_provider_code_does_not_exist(self, visitor):
        url = reverse("payments:provider_notification", args=["un-altre"])
        assert visitor.post(url, data=b"{}", content_type="application/json").status_code == 404

    def test_without_a_configured_provider_the_route_does_not_exist(self, visitor, settings):
        settings.PAYMENTS_PROVIDER = ""
        assert send(visitor, b"{}", {}).status_code == 404
        assert events() == []

    def test_path_is_the_one_in_the_specification(self):
        assert URL == "/pagaments/notificacions/fake"


class TestStoredEvents:
    @pytest.fixture
    def event(self):
        return ProviderEvent.objects.create(
            provider_code="fake", external_id="e-1", payload_hash="0" * 64
        )

    def test_an_event_is_accepted_only_once(self, event):
        with pytest.raises(IntegrityError), transaction.atomic():
            ProviderEvent.objects.create(
                provider_code="fake", external_id="e-1", payload_hash="1" * 64
            )
        # El mateix identificador en un altre proveïdor és un altre esdeveniment.
        ProviderEvent.objects.create(
            provider_code="altre", external_id="e-1", payload_hash="2" * 64
        )

    def test_a_stored_event_cannot_be_changed_or_deleted(self, event):
        event.amount_cents = 1
        with pytest.raises(ProviderEventLocked):
            event.save()
        with pytest.raises(ProviderEventLocked):
            event.save(update_fields=["amount_cents"])
        with pytest.raises(ProviderEventLocked):
            event.save(update_fields=["result", "order_id"])
        with pytest.raises(UndeletableError):
            event.delete()
        with pytest.raises(ProviderEventLocked):
            ProviderEvent.objects.filter(pk=event.pk).update(amount_cents=1)
        event.refresh_from_db()
        assert event.amount_cents is None

    def test_its_result_is_closed_once(self, event):
        event.result, event.processed_at = R.PROCESSED, timezone.now()
        event.save(update_fields=["result", "processed_at"])
        event.result = R.ERROR
        with pytest.raises(ProviderEventLocked):
            event.save(update_fields=["result"])
        event.refresh_from_db()
        assert event.result == R.PROCESSED

    def test_unknown_result_is_refused_by_the_database(self):
        with pytest.raises(IntegrityError), transaction.atomic():
            ProviderEvent.objects.create(provider_code="fake", payload_hash="0" * 64, result="x")

    def test_no_field_can_hold_the_body_card_data_or_an_iban(self):
        names = {field.name for field in ProviderEvent._meta.get_fields()}
        assert not names & {"body", "payload", "raw", "iban", "pan", "cvv", "card_number", "ip"}
        assert str(ProviderEvent(provider_code="fake", result=R.TO_REVIEW)) == "fake — (A revisar)"
