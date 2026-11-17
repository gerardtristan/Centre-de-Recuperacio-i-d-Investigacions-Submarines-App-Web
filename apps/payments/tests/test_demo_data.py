"""Dades inventades dels pagaments (T-M05b-17: «es carreguen amb una ordre»). `seed_demo_data`
en una base buida deixa intents en cada estat que pot quedar desat, notificacions de cada mena,
una remesa liquidada amb dos rebuts retornats i la proposta pendent, una devolució, pagaments de
convidats i mandats actius, revocats, caducats i bloquejats. Només dades inventades."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.payments.models import (
    DirectDebitItem,
    DirectDebitRemittance,
    PaymentAttempt,
    ProviderEvent,
    Receipt,
    RefundRequest,
    SepaMandate,
)
from apps.treasury.balances import balances
from apps.treasury.models import Movement

pytestmark = pytest.mark.django_db
DEV = override_settings(SETTINGS_MODULE="config.settings.dev", DEBUG=True)


@pytest.fixture
def seeded(tmp_path):
    out = StringIO()
    with DEV:
        call_command("seed_demo_data", "--cluber-file", str(tmp_path / "c.csv"), stdout=out)
    return out.getvalue()


def test_t_m05b_17_the_command_loads_the_payments(seeded):
    assert "Pagaments:" in seeded

    states = set(PaymentAttempt.objects.values_list("status", flat=True))
    # Totes menys «creat», que només és un pas dins de `start_payment`.
    assert states == set(PaymentAttempt.Status.values) - {"created"}
    to_review = PaymentAttempt.objects.get(status="to_review")
    assert to_review.review_reason and to_review.guest_link_id

    results = set(ProviderEvent.objects.values_list("result", flat=True))
    assert {"processed", "ignored_duplicate", "rejected_signature", "to_review"} <= results

    remittance = DirectDebitRemittance.objects.get(status="settled")
    assert set(remittance.items.values_list("status", flat=True)) == {"returned"}
    assert set(remittance.items.values_list("return_reason_code", flat=True)) == {"AM04", "MD01"}
    # AM04: el reintent espera la decisió del tresorer (càrrec «retornat»). MD01 bloqueja el
    # mandat, no hi ha reintent possible i l'alternativa surt sola (T-M05b-27): torna a pendent.
    by_code = {
        item.return_reason_code: item.attempt.charge.status
        for item in remittance.items.select_related("attempt__charge")
    }
    assert by_code == {"AM04": "returned", "MD01": "pending"}
    assert DirectDebitItem.objects.filter(status="included").exists()  # la remesa en esborrany

    refund = RefundRequest.objects.get()
    assert refund.status == "done" and refund.payment.charge.status == "paid"

    guest_paid = PaymentAttempt.objects.filter(status="paid", guest_link__isnull=False)
    assert Receipt.objects.filter(attempt__in=guest_paid).exists()

    mandates = set(SepaMandate.objects.values_list("status", flat=True))
    assert mandates == set(SepaMandate.Status.values)


def test_returns_after_a_settled_remittance_leave_the_transit_at_zero(seeded):
    """P-286 (opció C): un rebut retornat d'una remesa ja liquidada surt del banc, que és qui el
    carrega, i el trànsit «Remeses SEPA», ja traspassat, queda a zero."""
    last = Movement.objects.latest("value_date").value_date
    sepa = {a.name: a.balance_cents for a in balances(last)}["Remeses SEPA"]
    assert sepa == 0
