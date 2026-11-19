"""Pagament a terminis de la quota de ple dret (T-M01-49; 097, P-61 punts 1 a 4; 085, J-9; 072,
quarta instrucció, punt 2). Apagat per defecte: res no canvia; encès, el soci tria els tres
terminis a l'alta o a la renovació. Només dades inventades."""

from datetime import date, datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone

from apps.core import audit
from apps.core.models import AuditEntry, Charge, Setting
from apps.members import cards, fees, instalments, roster, services
from apps.members import settings as values
from apps.members.models import AnnualFee, Member, MembershipType
from apps.members.tests.test_cards import account_for, make_member, pay

pytestmark = pytest.mark.django_db

S = Member.Status
K = AnnualFee.Kind
SYSTEM = audit.system("proves")


def set_value(key, value):
    Setting.objects.filter(key=key).update(initial_value=value)


@pytest.fixture
def on():
    set_value(values.INSTALMENTS_ENABLED, True)


def at_noon(day):
    return timezone.make_aware(datetime(day.year, day.month, day.day, 12))


def annual(member, due_on=date(2027, 1, 31)):
    return fees.issue_annual_fee(member, period=due_on.year, due_on=due_on, by=SYSTEM)


def plan_of(member):
    return list(
        AnnualFee.objects.filter(member=member, kind=K.INSTALMENT)
        .select_related("charge")
        .order_by("instalment")
    )


def choose(member, due_on=date(2027, 1, 31)):
    fee = annual(member, due_on)
    return fee, instalments.choose(fee, by=account_for(member))


def loaded(member):
    return cards.load_member(member.pk)


# --- Ajustos i import -------------------------------------------------------------------------


def test_off_by_default_with_the_provisional_amounts():
    assert values.instalments_enabled() is False
    assert values.instalments_total_cents() == 9600
    assert values.instalments_unpaid_days() == 30


@pytest.mark.parametrize(
    ("total", "surcharge", "expected"),
    [
        (9600, 0, [3200, 3200, 3200]),
        (9000, 1000, [3334, 3333, 3333]),
        (9600, 2, [3202, 3200, 3200]),
    ],
)
def test_the_plan_adds_the_surcharge_and_gives_the_spare_cents_to_the_first(
    total, surcharge, expected
):
    set_value(values.INSTALMENTS_TOTAL, total)
    set_value(values.INSTALMENTS_SURCHARGE, surcharge)
    amounts = instalments.plan(values.instalments_total_cents())
    assert amounts == expected and sum(amounts) == total + surcharge


# --- Apagat: res no canvia --------------------------------------------------------------------


def test_off_nobody_can_choose_and_nothing_is_created():
    member = make_member(status=S.PENDING)
    fee = annual(member)
    assert not instalments.can_choose(fee)
    with pytest.raises(ValidationError):
        instalments.choose(fee, by=account_for(member))
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PENDING and not plan_of(member)


# --- Encès: triar els terminis ----------------------------------------------------------------


def test_on_choosing_cancels_the_annual_fee_and_creates_three_monthly_instalments(on):
    member = make_member(status=S.PENDING)
    fee, created = choose(member)
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.CANCELLED and fee.charge.cancel_reason
    assert [f.instalment for f in created] == [1, 2, 3]
    assert [f.charge.amount_cents for f in created] == [3200, 3200, 3200]
    # J-9: mensuals; el 31 de gener passa a l'últim dia de febrer i de març.
    assert [f.due_on for f in created] == [date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31)]
    assert all(f.period == 2027 and f.charge.kind == Charge.Kind.FEE for f in created)
    assert created[1].charge.concept == "Quota de soci 2027, termini 2 de 3"
    assert AuditEntry.objects.filter(action=instalments.CHOSEN, target_id=str(fee.pk)).exists()


@pytest.mark.parametrize(
    "case", ["supporter", "paid", "partial", "unpaid", "left", "supplement", "chosen"]
)
def test_on_only_a_pending_annual_fee_without_payments_of_a_full_member(on, case):
    member = make_member(status=S.UNPAID if case == "unpaid" else S.ACTIVE)
    if case == "left":
        Member.objects.filter(pk=member.pk).update(status=S.LEFT)
    if case == "supporter":
        Member.objects.filter(pk=member.pk).update(
            type=MembershipType.objects.get(code="supporter")
        )
    fee, by = annual(member), account_for(member)
    if case == "paid":
        pay(fee)
    if case == "partial":
        pay(fee, amount=1000)
    if case == "supplement":
        fee = fees._issue_fee(
            member, kind=K.TYPE_CHANGE_SUPPLEMENT, amount_cents=5500, concept="Suplement",
            period=2027, due_on=date(2027, 1, 31), by=SYSTEM,
        )  # fmt: skip
    if case == "chosen":
        instalments.choose(fee, by=by)
    fee = AnnualFee.objects.select_related("charge", "member__type").get(pk=fee.pk)
    assert not instalments.can_choose(fee)
    with pytest.raises(ValidationError):
        instalments.choose(fee, by=by)


def test_on_another_persons_fee_is_not_found(on):
    member, other = make_member(), make_member("Berta", 1288, document="00000001R")
    fee = annual(member)
    with pytest.raises(Http404):
        instalments.choose(fee, by=account_for(other, "berta@example.org"))
    assert not plan_of(member)


def test_on_a_payment_in_progress_blocks_the_choice(on):
    from apps.payments import attempts
    from apps.payments.models import PaymentAttempt

    member = make_member(status=S.PENDING)
    fee = annual(member)
    attempt = attempts.create_attempt(fee.charge, PaymentAttempt.Method.CARD)
    attempts.transition(attempt, PaymentAttempt.Status.IN_PROGRESS, by=SYSTEM)
    with pytest.raises(ValidationError):
        instalments.choose(fee, by=account_for(member))
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PENDING and not plan_of(member)


# --- Actiu amb el primer termini i carnet mentre estan al dia (punt 1) ------------------------


def test_the_member_becomes_active_only_with_the_first_instalment(on):
    member = make_member(status=S.PENDING)
    _fee, (first, second, third) = choose(member)
    pay(second, at_noon(date(2027, 1, 20)))
    assert services.on_fee_paid(second.pk).status == S.PENDING
    pay(first, at_noon(date(2027, 1, 25)))
    assert services.on_fee_paid(first.pk).status == S.ACTIVE
    assert cards.active_card(loaded(member)) is not None
    # El tercer, pendent: val fins al seu venciment.
    assert cards.valid_until(loaded(member)) == date(2027, 3, 31)
    pay(third, at_noon(date(2027, 3, 2)))
    services.on_fee_paid(third.pk)
    # Tots pagats: la renovació, 12 mesos després del primer pagament (070).
    assert cards.valid_until(loaded(member)) == date(2028, 1, 25)
    assert fees.next_fee_due(loaded(member)) == date(2028, 1, 25)


def test_an_overdue_instalment_makes_the_fee_pending_and_the_card_not_valid(on):
    member = make_member(status=S.PENDING)
    _fee, (first, second, _third) = choose(member)
    pay(first, at_noon(date(2027, 1, 25)))
    services.on_fee_paid(first.pk)
    card = cards.active_card(loaded(member))
    assert cards.validity(loaded(member), card, date(2027, 2, 28)).valid
    assert roster.fee_state(loaded(member), date(2027, 2, 28)).kind == roster.PAID_UNTIL
    assert not cards.validity(loaded(member), card, date(2027, 3, 1)).valid
    assert roster.fee_state(loaded(member), date(2027, 3, 1)) == roster.FeeState(roster.PENDING)
    assert fees.next_fee_due(loaded(member)) is None  # cap renovació amb terminis sense pagar


def test_a_returned_first_instalment_gives_no_validity(on):
    member = make_member(status=S.PENDING)
    _fee, (first, _second, _third) = choose(member)
    pay(first, at_noon(date(2027, 1, 25)))
    Charge.objects.filter(pk=first.charge_id).update(status=Charge.Status.RETURNED)
    assert cards.valid_until(loaded(member)) is None


# --- Candidat a impagat (punt 2) --------------------------------------------------------------


def test_an_unpaid_instalment_is_proposed_after_the_days_and_never_marked_alone(on):
    member = make_member(status=S.PENDING)
    _fee, (first, _second, _third) = choose(member)
    pay(first, at_noon(date(2027, 1, 25)))
    services.on_fee_paid(first.pk)
    assert member.pk not in instalments.unpaid_candidates(date(2027, 3, 29))  # 29 dies
    assert member.pk in instalments.unpaid_candidates(date(2027, 3, 30))  # 30 dies
    set_value(values.INSTALMENTS_UNPAID_DAYS, 10)
    assert member.pk in instalments.unpaid_candidates(date(2027, 3, 10))
    member.refresh_from_db()
    assert member.status == S.ACTIVE  # 040: la marca és del tresorer
