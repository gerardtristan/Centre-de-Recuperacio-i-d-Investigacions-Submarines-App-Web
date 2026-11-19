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
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees, instalments, member_requests, roster, services, validity
from apps.members import settings as values
from apps.members.models import AnnualFee, FeeReminder, Member, MembershipType
from apps.members.services import InactiveAccount
from apps.members.tests.test_cards import account_for, make_member, pay

pytestmark = pytest.mark.django_db

S = Member.Status
K = AnnualFee.Kind
SYSTEM = audit.system("proves")


def set_value(key, value):
    Setting.objects.filter(key=key).update(initial_value=value)


@pytest.fixture
def on():
    """Encès, amb l'import total igual a la quota de ple dret (P-396, punt b) i 6 € de recàrrec."""
    set_value(values.INSTALMENTS_ENABLED, True)
    set_value(values.INSTALMENTS_TOTAL, 9000)
    set_value(values.INSTALMENTS_SURCHARGE, 600)


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
    assert [f.charge.amount_cents for f in created] == [3200, 3200, 3200]  # 9000 + 600
    # J-9: mensuals; el 31 de gener passa a l'últim dia de febrer i de març.
    assert [f.due_on for f in created] == [date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31)]
    assert all(f.period == 2027 and f.charge.kind == Charge.Kind.FEE for f in created)
    assert created[1].charge.concept == "Quota de soci 2027, termini 2 de 3"
    assert AuditEntry.objects.filter(action=instalments.CHOSEN, target_id=str(fee.pk)).exists()


def test_chosen_late_the_first_instalment_is_due_on_the_day_of_the_choice(on):
    """P-396 (c): una quota ja vençuda no dona terminis vençuts el mateix dia que es trien."""
    fee = annual(make_member(status=S.PENDING), date(2027, 1, 31))
    dues = [due for _cents, due in instalments.schedule(fee, today=date(2027, 2, 10))]
    assert dues == [date(2027, 2, 10), date(2027, 3, 10), date(2027, 4, 10)]


def test_on_not_offered_if_the_fee_amount_is_not_the_instalments_total(on):
    """P-396 (b): triar no pot canviar el que deu el soci."""
    member = make_member(status=S.PENDING)
    fee = annual(member)
    assert instalments.can_choose(fee)
    set_value(values.INSTALMENTS_TOTAL, 9600)
    assert not instalments.can_choose(fee)
    with pytest.raises(ValidationError):
        instalments.choose(fee, by=account_for(member))
    assert not plan_of(member)


@pytest.mark.parametrize(
    "case", ["supporter", "paid", "partial", "unpaid", "left", "supplement", "chosen", "downgrade"]
)
def test_on_only_a_pending_annual_fee_without_payments_of_a_full_member(on, case):
    member = make_member(status=S.UNPAID if case == "unpaid" else S.ACTIVE)
    if case == "left":
        Member.objects.filter(pk=member.pk).update(status=S.LEFT)
    if case == "supporter":
        Member.objects.filter(pk=member.pk).update(
            type=MembershipType.objects.get(code="supporter")
        )
    by = account_for(member)
    if case == "downgrade":  # un pas a simpatitzant pendent (P-396, e)
        member_requests.request_downgrade(member, by=by)
    fee = annual(member)
    if case == "paid":
        pay(fee)
    if case == "partial":
        pay(fee, amount=1000)
    if case == "supplement":
        fee = fees._issue_fee(
            member, kind=K.TYPE_CHANGE_SUPPLEMENT, amount_cents=9000, concept="Suplement",
            period=2027, due_on=date(2027, 1, 31), by=SYSTEM,
        )  # fmt: skip
    if case == "chosen":
        instalments.choose(fee, by=by)
    fee = AnnualFee.objects.select_related("charge", "member__type").get(pk=fee.pk)
    assert not instalments.can_choose(fee)
    with pytest.raises(ValidationError):
        instalments.choose(fee, by=by)


def test_with_unpaid_instalments_the_downgrade_cannot_be_requested(on):
    member = make_member()
    _fee, (first, second, third) = choose(member)
    assert "terminis" in member_requests.downgrade_problem(member)
    for fee in (first, second, third):
        pay(fee)
    assert member_requests.downgrade_problem(member) == ""


def test_on_another_persons_fee_is_not_found(on):
    member, other = make_member(), make_member("Berta", 1288, document="00000001R")
    fee = annual(member)
    with pytest.raises(Http404):
        instalments.choose(fee, by=account_for(other, "berta@example.org"))
    assert not plan_of(member)


def test_on_an_admin_account_or_the_system_cannot_choose(on, make_admin):  # noqa: F811
    member = make_member()
    fee = annual(member)
    for by in (make_admin("treasurer", person=member.person), audit.system("proves")):
        with pytest.raises(Http404):
            instalments.choose(fee, by=by)
    assert not plan_of(member)


def test_on_a_disabled_account_cannot_choose(on):
    member = make_member()
    fee, account = annual(member), account_for(member)
    account.status = account.Status.DISABLED
    account.save()
    with pytest.raises(InactiveAccount):
        instalments.choose(fee, by=account)
    assert not plan_of(member)


def test_on_a_payment_in_progress_blocks_the_choice_with_a_message_for_the_member(on):
    from apps.payments import attempts
    from apps.payments.models import PaymentAttempt

    member = make_member(status=S.PENDING)
    fee = annual(member)
    attempt = attempts.create_attempt(fee.charge, PaymentAttempt.Method.CARD)
    attempts.transition(attempt, PaymentAttempt.Status.IN_PROGRESS, by=SYSTEM)
    assert not instalments.can_choose(fee)
    with pytest.raises(ValidationError) as error:
        instalments.choose(fee, by=account_for(member))
    assert "pagament en curs" in error.value.messages[0]
    assert "a mà" not in error.value.messages[0]
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PENDING and not plan_of(member)


# --- Actiu amb el primer termini pagat i carnet mentre estan al dia (punt 1) ------------------


def test_the_member_becomes_active_with_the_first_paid_instalment(on):
    member = make_member(status=S.PENDING)
    _fee, (first, second, third) = choose(member)
    pay(second, at_noon(date(2027, 1, 20)))
    assert services.on_fee_paid(second.pk).status == S.ACTIVE
    assert cards.active_card(loaded(member)) is not None
    # El primer, pendent: val fins al seu venciment.
    assert cards.valid_until(loaded(member)) == date(2027, 1, 31)
    pay(first, at_noon(date(2027, 1, 25)))
    services.on_fee_paid(first.pk)
    assert cards.valid_until(loaded(member)) == date(2027, 3, 31)  # el tercer, pendent
    pay(third, at_noon(date(2027, 3, 2)))
    services.on_fee_paid(third.pk)
    # Tots pagats: la renovació, 12 mesos després del primer pagament (070).
    assert cards.valid_until(loaded(member)) == date(2028, 1, 20)
    assert fees.next_fee_due(loaded(member)) == date(2028, 1, 20)


def test_a_cancelled_first_instalment_does_not_block_the_validity(on):
    from apps.core import charges

    member = make_member(status=S.PENDING)
    _fee, (first, second, _third) = choose(member)
    charges.cancel(first.charge, "Anul·lat (motiu inventat)", by=SYSTEM)
    pay(second, at_noon(date(2027, 2, 20)))
    assert services.on_fee_paid(second.pk).status == S.ACTIVE
    assert cards.valid_until(loaded(member)) == date(2027, 3, 31)


def test_an_active_member_paying_a_renewal_instalment_keeps_a_valid_card(on):
    member = make_member()
    previous = annual(member, date(2026, 1, 31))
    pay(previous, at_noon(date(2026, 1, 31)))
    assert cards.active_card(loaded(member)) is None
    _renewal, (first, _second, _third) = choose(member, date(2027, 1, 31))
    pay(first, at_noon(date(2027, 1, 28)))
    assert services.on_fee_paid(first.pk).status == S.ACTIVE
    assert cards.active_card(loaded(member)) is not None  # A-06: en rep un
    assert cards.valid_until(loaded(member)) == date(2027, 2, 28)


def test_an_overdue_instalment_makes_the_fee_pending_and_the_card_not_valid(on):
    member = make_member(status=S.PENDING)
    _fee, (first, _second, _third) = choose(member)
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


def test_a_validity_from_instalments_is_not_shown_as_waived(monkeypatch):
    """La mateixa data d'una exempció i dels terminis compta com a pagada, no com a eximida."""
    member = make_member()
    day = date(2028, 1, 25)
    for name in ("exempted_until", "instalments_until"):
        monkeypatch.setattr(validity, name, lambda m, day=day: day)
    assert not validity.waived_now(loaded(member), date(2027, 6, 1))


def test_reminders_also_go_out_for_each_instalment(on):
    member = make_member()
    _fee, (first, second, _third) = choose(member)
    fees.send_due_reminders(date(2027, 2, 28))
    assert FeeReminder.objects.filter(fee=second, offset_days=0).exists()
    assert FeeReminder.objects.filter(fee=first).exists()


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


def test_an_instalment_that_may_still_be_collected_is_not_proposed(on):
    from apps.payments import attempts
    from apps.payments.models import PaymentAttempt

    member = make_member(status=S.PENDING)
    _fee, (first, second, _third) = choose(member)
    pay(first, at_noon(date(2027, 1, 25)))
    services.on_fee_paid(first.pk)
    attempt = attempts.create_attempt(second.charge, PaymentAttempt.Method.CARD)
    attempts.transition(attempt, PaymentAttempt.Status.IN_PROGRESS, by=SYSTEM)
    assert member.pk not in instalments.unpaid_candidates(date(2027, 4, 15))  # el 2n, en curs
