# ruff: noqa: F811
"""Devolucions que fa el club (T-M05b-13; P-M05b-G; RN-M05b-17; RN-T11; CA-M05b-21 i CA-M05b-22;
P-118, P-119, P-228). Proveïdor fals, sense xarxa. Només dades inventades."""

from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.core.models import AuditEntry, Charge, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import refunds
from apps.payments.models import Receipt, RefundRequest
from apps.payments.providers import base, fake
from apps.payments.tests.test_processing import (  # noqa: F401 (fixtures)
    account,
    attempt,
    clean_orders,
    fee,
    member,
    notify,
    run_queue,
    transit,
)
from apps.treasury.models import Movement
from apps.treasury.tests.test_record_income import paid, record

pytestmark = pytest.mark.django_db
M = Payment.Method
REASON = "Activitat anul·lada pel club (prova)"


@pytest.fixture
def treasurer(make_admin):
    return make_admin("treasurer")


@pytest.fixture
def card(make_person, transit):
    """Inscripció de 12.000 pagada amb targeta, amb l'ingrés al trànsit (exemple de M05b-7)."""
    payment = paid(make_person("Pau", "Serra"), amount=12_000)
    record(payment)
    return payment


def refunded(payment):
    return list(
        Movement.objects.filter(payment=payment, kind=Movement.Kind.REFUND).values_list(
            "amount_cents", flat=True
        )
    )


def status(payment):
    return Charge.objects.get(pk=payment.charge_id).status


def do(payment, amount, by, key=None, reason=REASON):
    return refunds.refund(payment, amount, reason=reason, key=key or uuid4(), by=by)


class TestRefund:
    def test_ca_m05b_21_partial_then_total_then_rejected(self, card, treasurer):
        first = do(card, 4000, treasurer)
        assert (first.status, first.channel) == (RefundRequest.Status.DONE, "provider")
        assert first.provider_refund_id and first.done_at
        assert status(card) == Charge.Status.PAID  # parcial: continua «pagat»
        do(card, 8000, treasurer)
        assert status(card) == Charge.Status.CANCELLED  # suma 12.000: «anul·lat»
        with pytest.raises(refunds.RefundRejected):
            do(card, 1, treasurer)
        assert refunded(card) == [4000, 8000]
        entry = AuditEntry.objects.filter(action=refunds.REFUNDED).latest("pk")
        assert (entry.actor_account, entry.reason) == (treasurer, REASON)
        assert entry.details == {
            "payment": card.pk,
            "amount_cents": 8000,
            "channel": "provider",
            "total": True,
        }

    def test_rn_t11_more_than_paid_is_rejected(self, card, treasurer):
        with pytest.raises(refunds.RefundRejected):
            do(card, 12_001, treasurer)
        assert not RefundRequest.objects.exists() and refunded(card) == []

    def test_ca_m05b_22_same_key_one_refund(self, card, treasurer, monkeypatch):
        calls = []
        original = fake.FakeProvider.refund
        monkeypatch.setattr(
            fake.FakeProvider,
            "refund",
            lambda self, *args: calls.append(args) or original(self, *args),
        )
        key = uuid4()
        first = do(card, 4000, treasurer, key=key)
        assert do(card, 4000, treasurer, key=key) == first
        assert len(calls) == 1 and refunded(card) == [4000]

    def test_p_119_a_retry_after_a_provider_error_books_once(self, card, treasurer, monkeypatch):
        key = uuid4()
        original = fake.FakeProvider.refund

        def down(self, *args):
            raise base.ProviderError("caigut")

        monkeypatch.setattr(fake.FakeProvider, "refund", down)
        with pytest.raises(base.ProviderError):
            do(card, 4000, treasurer, key=key)
        # Pendent, sense cap apunt: l'apunt s'ha desfet amb l'error del proveïdor.
        assert RefundRequest.objects.get().status == RefundRequest.Status.PENDING
        assert refunded(card) == []
        # La pendent compta: una altra no pot passar de l'import (RN-T11).
        with pytest.raises(refunds.RefundRejected):
            do(card, 8001, treasurer)
        monkeypatch.setattr(fake.FakeProvider, "refund", original)
        done = do(card, 4000, treasurer, key=key)
        assert done.status == RefundRequest.Status.DONE
        assert done.provider_refund_id == f"fake-refund-{key.hex}"
        assert refunded(card) == [4000]

    def test_a_key_of_another_refund_is_rejected(self, card, treasurer):
        key = uuid4()
        do(card, 4000, treasurer, key=key)
        with pytest.raises(refunds.RefundRejected):
            do(card, 5000, treasurer, key=key)
        assert refunded(card) == [4000]

    def test_p_228_a_transfer_is_refunded_from_the_bank(self, make_person, treasurer, monkeypatch):
        payment = paid(make_person("Laia", "Pons"), amount=3000, method=M.TRANSFER)
        record(payment, origin="reconciliation")
        monkeypatch.setattr(fake.FakeProvider, "refund", lambda *a: pytest.fail("proveïdor"))
        request = do(payment, 3000, treasurer)
        assert (request.channel, request.provider_refund_id) == ("bank", "")
        assert refunded(payment) == [3000] and status(payment) == Charge.Status.CANCELLED

    def test_a_bizum_goes_through_the_provider_only_if_it_refunds_bizum(
        self, make_person, transit, treasurer, monkeypatch
    ):
        payment = paid(make_person("Joan", "Vila"), amount=2000, method=M.BIZUM)
        record(payment)
        assert do(payment, 500, treasurer).channel == "provider"
        caps = fake.FakeProvider().capabilities()
        monkeypatch.setattr(
            fake.FakeProvider,
            "capabilities",
            lambda self: base.Capabilities(**{**caps.__dict__, "refund_bizum": False}),
        )
        assert do(payment, 500, treasurer).channel == "bank"

    def test_rn_m05b_17_a_total_refund_cancels_the_receipt(self, attempt, transit, treasurer):
        notify(attempt)
        run_queue()
        payment = Payment.objects.get(charge=attempt.charge)
        do(payment, payment.amount_cents, treasurer)
        receipt = Receipt.objects.get()
        assert receipt.cancellation.note == f"Devolució: {REASON}"

    def test_b5_treasurer_only(self, card, make_admin):
        for role in ("administrator", "secretary", "board"):
            with pytest.raises(Http404):
                do(card, 100, make_admin(role))
        assert not RefundRequest.objects.exists()

    @pytest.mark.parametrize("amount", [0, -1, 1.5, True])
    def test_amount_is_positive_cents(self, card, treasurer, amount):
        with pytest.raises(refunds.RefundRejected):
            do(card, amount, treasurer)

    @pytest.mark.parametrize("reason", ["", "   ", None])
    def test_a_reason_is_required(self, card, treasurer, reason):
        with pytest.raises(refunds.RefundRejected):
            do(card, 100, treasurer, reason=reason)
        assert not RefundRequest.objects.exists()

    def test_only_a_paid_charge(self, make_person, transit, treasurer):
        payment = paid(make_person("Marc", "Roca"), amount=1000)
        record(payment)
        Charge.objects.filter(pk=payment.charge_id).update(status=Charge.Status.RETURNED)
        with pytest.raises(refunds.RefundRejected):
            do(payment, 100, treasurer)

    def test_all_or_nothing_when_treasury_refuses(self, make_person, transit, treasurer):
        payment = paid(make_person("Eva", "Mas"), amount=1000)  # sense ingrés a la 04
        with pytest.raises(ValidationError):
            do(payment, 100, treasurer)
        assert RefundRequest.objects.get().status == RefundRequest.Status.PENDING
        assert status(payment) == Charge.Status.PAID
