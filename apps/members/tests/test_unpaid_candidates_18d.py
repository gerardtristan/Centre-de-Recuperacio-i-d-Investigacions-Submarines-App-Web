"""Candidats a «impagat» per la quota anual (T-M01-18d; 085, J-4 i J-5; P-71; P-400): la
plataforma els proposa a «Quotes i impagats» i el tresorer els marca a mà, amb motiu (040). Els
rebuts retornats es fan amb els serveis reals del 05b. Només dades inventades."""

from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit
from apps.core.models import Charge, LegalText
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import fees
from apps.members import settings as values
from apps.members.fee_rules import local_today
from apps.members.models import AnnualFee, Member
from apps.members.tests.test_cards import make_member, pay
from apps.members.tests.test_instalments_049 import annual, at_noon, set_value
from apps.members.tests.test_roster import admin_client
from apps.payments import remittances, returns, sepa_xml
from apps.payments.tests.test_remittance_settlement import club  # noqa: F401 (autouse)
from apps.payments.tests.test_remittances import collection_date, new_member
from apps.payments.tests.test_returns import settle
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

S = Member.Status
DUE = date(2027, 1, 31)
# La marca de la fila: el nom també surt al filtre, i per això es busca la peça sencera.
BADGE = "!</span> Candidat a impagat</span>"


def collected_receipt(treasurer, *, n=1, due_days_ago=5):
    """Quota domiciliada vençuda fa `due_days_ago` dies, en una remesa enviada i liquidada."""
    text = LegalText.objects.filter(kind="sepa_mandate").first() or LegalText.objects.create(
        kind="sepa_mandate", version=1, content="Text de prova."
    )
    holder = make_member(first="Signant", number=9000 + n, document=f"9{n:07d}R")
    signer = Account.objects.create_personal(holder.person, f"signant{n}@example.org", PASSWORD)
    fee = new_member(n, signer=signer, text=text)
    fee.due_on = timezone.localdate() - timedelta(days=due_days_ago)
    fee.save()
    remittance = remittances.build_remittance(f"R{n}", collection_date(), treasurer)
    sepa_xml.remittance_file(remittance, treasurer)
    remittances.mark_remittance_sent(remittance, file_deleted=True, by=treasurer)
    settle(remittance, treasurer, n=n)
    return remittance.items.get(), fee.member


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


def test_an_annual_fee_unpaid_for_the_days_is_proposed_and_never_marked_alone():
    member = make_member()
    annual(member, DUE)
    assert member.pk not in fees.unpaid_candidates(DUE + timedelta(days=29))
    assert member.pk in fees.unpaid_candidates(DUE + timedelta(days=30))
    set_value(values.INSTALMENTS_UNPAID_DAYS, 10)  # P-400: el mateix ajust que els terminis
    assert member.pk in fees.unpaid_candidates(DUE + timedelta(days=10))
    member.refresh_from_db()
    assert member.status == S.ACTIVE  # 040: la marca és del tresorer


def test_a_returned_receipt_without_retry_is_proposed_the_same_day(treasurer):
    """AC04 bloqueja el mandat: sense reintent, l'alternativa ja s'aplica i el càrrec torna a
    «pendent» (`register_return` → `confirm`). El retorn el proposa igualment el mateix dia."""
    item, member = collected_receipt(treasurer)
    assert returns.register_return(item, "AC04", by=treasurer) == returns.SENT
    assert Charge.objects.get(pk=item.attempt.charge_id).status == Charge.Status.PENDING
    assert member.pk in fees.unpaid_candidates(timezone.localdate())


def test_a_confirmed_retry_is_not_proposed_until_it_resolves(treasurer):
    item, member = collected_receipt(treasurer)
    today = timezone.localdate()
    assert returns.register_return(item, "AM04", by=treasurer) == returns.RETRY
    assert member.pk in fees.unpaid_candidates(today)  # retornat, sense decidir encara
    returns.confirm(item, returns.RETRY, by=treasurer)
    assert member.pk not in fees.unpaid_candidates(today)
    assert member.pk not in fees.unpaid_candidates(today + timedelta(days=40))
    second = remittances.build_remittance("R2", collection_date(), treasurer)
    assert member.pk not in fees.unpaid_candidates(today)  # el rebut nou, al banc
    sepa_xml.remittance_file(second, treasurer)
    remittances.mark_remittance_sent(second, file_deleted=True, by=treasurer)
    settle(second, treasurer, n=2)
    assert returns.register_return(second.items.get(), "AM04", by=treasurer) == returns.SENT
    assert member.pk in fees.unpaid_candidates(today)  # el reintent també s'ha retornat


def test_a_fee_that_may_still_be_collected_is_not_proposed():
    from apps.payments import attempts
    from apps.payments.models import PaymentAttempt

    member = make_member()
    fee = annual(member, DUE)
    attempt = attempts.create_attempt(fee.charge, PaymentAttempt.Method.CARD)
    attempts.transition(attempt, PaymentAttempt.Status.IN_PROGRESS, by=audit.system("proves"))
    assert member.pk not in fees.unpaid_candidates(DUE + timedelta(days=40))


def test_only_the_current_period_counts_and_never_within_a_paid_period():
    """Mateixa definició que `roster.fee_state`: amb «Pagada fins al» no és candidat, i una quota
    antiga retornada (d'un període ja superat) no el fa candidat per sempre."""
    member = make_member()
    old = annual(member, date(2025, 1, 31))
    Charge.objects.filter(pk=old.charge_id).update(status=Charge.Status.RETURNED)
    pay(annual(member, date(2026, 1, 31)), at_noon(date(2026, 2, 1)))  # fins al 01/02/2027
    assert member.pk not in fees.unpaid_candidates(date(2026, 12, 1))
    annual(member, date(2027, 2, 1))  # la renovació
    assert member.pk not in fees.unpaid_candidates(date(2027, 2, 10))
    assert member.pk in fees.unpaid_candidates(date(2027, 3, 3))  # 30 dies


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
