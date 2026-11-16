# ruff: noqa: F811
"""Rebut anul·lat (T-DX-11b; 045, M05b-6): un rebut amb una anul·lació diu «Anul·lat» i la nota, i
no porta mai el segell de pagat. Un rebut sense anul·lació no canvia."""

import pytest

from apps.payments.models import Receipt, ReceiptCancellation
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
from apps.payments.tests.test_receipts import contact, receipt_page  # noqa: F401

pytestmark = pytest.mark.django_db
NOTE = "Pagament duplicat; es retorna l'import."


def seal(html):
    return html.split('class="rebut-segell', 1)[1].split("</p>", 1)[0]


def test_a_cancelled_receipt_shows_cancelled_and_the_note(account, attempt, transit):
    notify(attempt)
    run_queue()
    ReceiptCancellation.objects.create(receipt=Receipt.objects.get(), note=NOTE)
    html = receipt_page(account, attempt).content.decode()
    assert "es-anullat" in seal(html) and "Anul·lat" in seal(html)
    assert "Pagat" not in seal(html)
    assert "Pagament duplicat; es retorna l&#x27;import." in html or NOTE in html


def test_a_receipt_without_cancellation_keeps_the_paid_seal(account, attempt, transit):
    notify(attempt)
    run_queue()
    html = receipt_page(account, attempt).content.decode()
    assert "Pagat" in seal(html) and "es-anullat" not in html and "Anul·lat" not in html
