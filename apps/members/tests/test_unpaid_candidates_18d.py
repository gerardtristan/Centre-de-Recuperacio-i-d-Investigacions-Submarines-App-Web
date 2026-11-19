"""Candidats a «impagat» per la quota anual (T-M01-18d; 085, J-4 i J-5; P-71; P-400): la
plataforma els proposa a «Quotes i impagats» i el tresorer els marca a mà, amb motiu (040). Només
dades inventades."""

from datetime import date, timedelta

import pytest
from django.urls import reverse

from apps.core import audit
from apps.core.models import Charge
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import fees
from apps.members import settings as values
from apps.members.fee_rules import local_today
from apps.members.models import AnnualFee, Member
from apps.members.tests.test_cards import make_member
from apps.members.tests.test_instalments_049 import annual, set_value
from apps.members.tests.test_roster import admin_client

pytestmark = pytest.mark.django_db

S = Member.Status
DUE = date(2027, 1, 31)
BADGE = "!</span> Candidat a impagat</span>"


def returned(fee):
    Charge.objects.filter(pk=fee.charge_id).update(status=Charge.Status.RETURNED)


def test_an_annual_fee_unpaid_for_the_days_is_proposed_and_never_marked_alone():
    member = make_member()
    annual(member, DUE)
    assert member.pk not in fees.unpaid_candidates(DUE + timedelta(days=29))
    assert member.pk in fees.unpaid_candidates(DUE + timedelta(days=30))
    set_value(values.INSTALMENTS_UNPAID_DAYS, 10)  # P-400: el mateix ajust que els terminis
    assert member.pk in fees.unpaid_candidates(DUE + timedelta(days=10))
    member.refresh_from_db()
    assert member.status == S.ACTIVE  # 040: la marca és del tresorer


def test_a_returned_receipt_is_proposed_without_waiting_for_the_days():
    member = make_member()
    returned(annual(member, DUE))
    assert member.pk in fees.unpaid_candidates(DUE + timedelta(days=1))


def test_a_fee_that_may_still_be_collected_is_not_proposed():
    from apps.payments import attempts
    from apps.payments.models import PaymentAttempt

    member = make_member()
    fee = annual(member, DUE)  # un rebut retornat es reobre abans de tornar-lo a cobrar
    attempt = attempts.create_attempt(fee.charge, PaymentAttempt.Method.CARD)
    attempts.transition(attempt, PaymentAttempt.Status.IN_PROGRESS, by=audit.system("proves"))
    assert member.pk not in fees.unpaid_candidates(DUE + timedelta(days=40))


@pytest.mark.parametrize("status", [S.PENDING, S.UNPAID])
def test_only_active_members_are_proposed(status):
    member = make_member(status=status)
    annual(member, DUE)
    assert member.pk not in fees.unpaid_candidates(DUE + timedelta(days=40))


def test_a_paid_or_cancelled_fee_or_a_supplement_is_not_proposed():
    members = [make_member(first, 1300 + i, document=doc) for i, (first, doc) in enumerate(
        [("Berta", "00000001R"), ("Carla", "00000002W"), ("Dani", "00000003A")]
    )]  # fmt: skip
    paid, cancelled = annual(members[0], DUE), annual(members[1], DUE)
    Charge.objects.filter(pk=paid.charge_id).update(status=Charge.Status.PAID)
    Charge.objects.filter(pk=cancelled.charge_id).update(
        status=Charge.Status.CANCELLED, cancel_reason="Prova"
    )
    fees._issue_fee(
        members[2], kind=AnnualFee.Kind.TYPE_CHANGE_SUPPLEMENT, amount_cents=9000,
        concept="Suplement", period=2027, due_on=DUE, by=audit.system("proves"),
    )  # fmt: skip
    assert not fees.unpaid_candidates(DUE + timedelta(days=40)) & {m.pk for m in members}


def test_the_screen_marks_the_candidate_and_filters_only_the_candidates(make_admin):  # noqa: F811
    candidate = make_member()
    annual(candidate, local_today() - timedelta(days=31))
    other = make_member("Berta", 1288, document="00000001R")
    annual(other, local_today())
    client = admin_client(make_admin("treasurer"))
    url = reverse("administration:fees")
    page = client.get(url).text
    assert page.count(BADGE) == 1 and "«Candidat a impagat»" in page
    filtered = client.get(url, {"quota": fees.CANDIDATE})
    assert [m.pk for m, _fee in filtered.context["page"]] == [candidate.pk]
    candidate.refresh_from_db()
    assert candidate.status == S.ACTIVE
