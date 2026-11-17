"""Contracte de l'adaptador (M05a-8): proves que ha de passar qualsevol proveïdor.

Cada implementació hi hereta en un fitxer de proves propi i hi aporta dues peces:

- `provider`: la instància que es prova;
- `notify(order, status, **kwargs)`: una petició HTTP amb la notificació que enviaria el
  proveïdor per a aquella ordre, signada com ho fa ell. Accepta `event_id` (per repetir-la),
  `tamper=True` (cos alterat després de signar) i `signed=False` (sense firma).
"""

import dataclasses
from datetime import date
from types import SimpleNamespace
from uuid import uuid4

import pytest

from apps.payments.providers import base

URLS = base.OrderUrls(
    notification="https://example.org/pagaments/notificacions/prova",
    return_ok="https://example.org/pagaments/fet",
    return_ko="https://example.org/pagaments/error",
)
# Cap nom de camp que pugui portar dades de targeta o un IBAN (M05a-8; 044).
FORBIDDEN_FIELDS = ("pan", "card_number", "number", "cvv", "cvc", "expiry", "iban", "holder")


def a_charge(amount_cents=9000):
    """L'adaptador només llegeix del càrrec l'identificador, l'import, la moneda i el concepte."""
    return SimpleNamespace(pk=1, amount_cents=amount_cents, currency="EUR", concept="Quota anual")


class ProviderContract:
    def order(self, provider, method=base.CARD, amount_cents=9000, key=None):
        return provider.create_order(a_charge(amount_cents), method, URLS, key or uuid4())

    # --- Ordres ---

    def test_capabilities_are_declared(self, provider):
        capabilities = provider.capabilities()
        assert isinstance(capabilities, base.Capabilities)
        assert all(isinstance(value, bool) for value in dataclasses.astuple(capabilities))

    def test_order_has_an_identifier_and_a_place_to_pay(self, provider):
        order = self.order(provider)
        assert isinstance(order, base.ProviderOrder)
        assert order.external_id and order.pay_url

    def test_same_idempotency_key_gives_the_same_order(self, provider):
        key = uuid4()
        first = self.order(provider, key=key)
        assert self.order(provider, key=key).external_id == first.external_id
        assert self.order(provider).external_id != first.external_id

    @pytest.mark.parametrize("method", ["transfer", "direct_debit", "saved_card", ""])
    def test_only_card_and_bizum_go_through_the_provider(self, provider, method):
        with pytest.raises(base.NotSupported):
            self.order(provider, method=method)

    def test_a_method_the_provider_does_not_declare_is_refused(self, provider):
        for method in base.ORDER_METHODS:
            if not getattr(provider.capabilities(), method):
                with pytest.raises(base.NotSupported):
                    self.order(provider, method=method)

    def test_no_order_with_the_real_environment_unless_charges_are_allowed(
        self,
        provider,
        settings,
        db,  # la negativa queda al registre d'activitat (CA-M05a-09)
    ):
        settings.PAYMENTS_ENVIRONMENT = "live"
        settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False
        with pytest.raises(base.LiveChargesNotAllowed):
            self.order(provider)
        with pytest.raises(base.LiveChargesNotAllowed):
            provider.charge_saved_card(a_charge(), object(), uuid4())

    def test_current_state_of_an_order(self, provider):
        order = self.order(provider, amount_cents=3500)
        state = provider.get_order(order.external_id)
        assert (state.external_id, state.amount_cents, state.currency) == (
            order.external_id,
            3500,
            "EUR",
        )
        assert state.status in base.ORDER_STATUSES

    # --- Notificacions ---

    def test_paid_notification_is_read_after_checking_the_signature(self, provider, notify):
        order = self.order(provider, amount_cents=9000)
        notification = provider.verify_notification(notify(order, base.PAID))
        assert isinstance(notification, base.ProviderNotification)
        assert notification.order_id == order.external_id
        assert notification.status == base.PAID
        assert (notification.amount_cents, notification.currency) == (9000, "EUR")
        assert notification.event_id

    def test_denied_payment_is_reported_as_denied(self, provider, notify):
        order = self.order(provider)
        assert provider.verify_notification(notify(order, base.DENIED)).status == base.DENIED

    def test_repeated_notification_carries_the_same_event(self, provider, notify):
        order = self.order(provider)
        first = provider.verify_notification(notify(order, base.PAID, event_id="esdeveniment-1"))
        again = provider.verify_notification(notify(order, base.PAID, event_id="esdeveniment-1"))
        assert first == again

    def test_two_notifications_are_two_events(self, provider, notify):
        order = self.order(provider)
        first = provider.verify_notification(notify(order, base.DENIED))
        second = provider.verify_notification(notify(order, base.PAID))
        assert first.event_id != second.event_id

    def test_altered_body_is_rejected(self, provider, notify):
        order = self.order(provider)
        with pytest.raises(base.InvalidSignature):
            provider.verify_notification(notify(order, base.PAID, tamper=True))

    def test_missing_signature_is_rejected(self, provider, notify):
        order = self.order(provider)
        with pytest.raises(base.InvalidSignature):
            provider.verify_notification(notify(order, base.PAID, signed=False))

    # --- Devolucions i operacions condicionals ---

    def test_refund_within_the_paid_amount(self, provider):
        payment = SimpleNamespace(amount_cents=9000, provider_reference="ordre-1")
        refund = provider.refund(payment, 4000, uuid4())
        assert isinstance(refund, base.ProviderRefund)
        assert refund.amount_cents == 4000 and refund.external_id

    def test_refund_is_not_blocked_by_the_charges_safeguard(self, provider, settings):
        settings.PAYMENTS_ENVIRONMENT = "live"
        settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False
        payment = SimpleNamespace(amount_cents=9000, provider_reference="ordre-1")
        assert provider.refund(payment, 9000, uuid4()).amount_cents == 9000

    def test_saved_cards_only_if_the_provider_declares_them(self, provider):
        if provider.capabilities().tokenization:
            pytest.skip("El proveïdor guarda targetes: ho proven les seves proves pròpies.")
        with pytest.raises(base.NotSupported):
            provider.start_card_setup(object(), URLS)
        with pytest.raises(base.NotSupported):
            provider.charge_saved_card(a_charge(), object(), uuid4())

    # --- Liquidacions (P-M05b-H; [A verificar: P-45 punt 9]) ---

    def test_settlements_are_listed_or_not_supported(self, provider):
        try:
            reports = provider.list_settlements(date(2026, 1, 1))
        except base.NotSupported:
            return  # el tresorer casa per període (RN-T21)
        assert all(isinstance(report, base.ProviderSettlementReport) for report in reports)


def test_no_contract_type_can_carry_card_or_bank_data():
    for contract_type in (
        base.ProviderOrder,
        base.OrderState,
        base.ProviderNotification,
        base.ProviderRefund,
        base.OrderUrls,
        base.SettledOperation,
        base.ProviderSettlementReport,
        base.ProviderCard,
    ):
        names = {field.name for field in dataclasses.fields(contract_type)}
        assert not names & set(FORBIDDEN_FIELDS), contract_type.__name__
