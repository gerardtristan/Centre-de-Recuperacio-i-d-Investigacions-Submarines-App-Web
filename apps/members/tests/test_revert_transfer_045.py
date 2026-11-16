"""Una quota pagada per una transferència conciliada per error i tornada a pendent (045,
T-M04-12c): el pagament anul·lat ja no compta enlloc del 01. Només dades inventades."""

from datetime import UTC, datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.core import audit, charges
from apps.core.models import Charge, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import fees, roster, validity
from apps.members.models import Member
from apps.members.tests.test_cards import add_fee, make_member
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
TRANSFER = Payment.Method.TRANSFER
SYSTEM = audit.system("proves-045")


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def pay_by_transfer(fee, by):
    return charges.record_payment(fee.charge, method=TRANSFER, origin="reconciliation", by=by)


def revert(fee, by):
    charges.revert_paid_transfer(fee.charge, "Càrrec equivocat (prova)", by=by)


def reverted_and_paid_again(fee, by):
    first = pay_by_transfer(fee, by)
    Payment.objects.filter(pk=first.pk).update(paid_at=datetime(2026, 1, 10, 10, tzinfo=UTC))
    revert(fee, by)
    # Per targeta: tornar a pagar per transferència xoca amb l'intent «pagat» del 05b, que la 045
    # encara no desfà (xfail a `apps/core/tests/test_revert_transfer.py`).
    return charges.record_payment(
        fee.charge, method=Payment.Method.CARD, origin="provider", by=SYSTEM
    )


def loaded(member):
    return roster.with_fee_data(Member.objects.filter(pk=member.pk)).get()


def test_paid_until_counts_only_the_valid_payment(treasurer, django_assert_num_queries):
    member = make_member()
    again = reverted_and_paid_again(add_fee(member), treasurer)
    member = loaded(member)
    with django_assert_num_queries(0):  # la precàrrega porta les anul·lacions
        assert validity.paid_until(member) == validity.twelve_months_after(
            timezone.localdate(again.paid_at)
        )
        assert validity.has_partial_payments(member) is False


def test_a_reverted_fee_can_be_exempted(treasurer):
    member = make_member()
    fee = add_fee(member)
    pay_by_transfer(fee, treasurer)
    revert(fee, treasurer)
    fees.exempt_fee(fee, by=treasurer, reason="Acord de la junta (motiu inventat).")
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.CANCELLED


def test_the_personal_fee_pages_show_the_valid_payment(treasurer, login_as):
    member = make_member()
    fee = add_fee(member)
    again = reverted_and_paid_again(fee, treasurer)
    account = Account.objects.create_personal(member.person, "anna.045@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    client = login_as(account, AREA_PERSONAL)
    paid_on = f"Pagada el {timezone.localdate(again.paid_at):%d/%m/%Y}"
    assert paid_on in client.get(reverse("members:fees")).content.decode()
    detail = client.get(reverse("members:fee_detail", args=[fee.pk])).content.decode()
    assert paid_on in detail and "Targeta" in detail
