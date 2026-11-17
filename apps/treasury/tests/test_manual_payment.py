"""Registre manual d'un pagament (P-12; RN-72 de la 00; 072, Q-037 i Q-038; RN-T08, RN-T10).

M14 (inicialment, el Tresorer), motiu obligatori, només un càrrec pendent i mai un de propi. Tot
o res: el càrrec pagat amb el pagament «manual», l'ingrés al compte triat (caixa o banc), el
rebut, el soci actiu amb carnet i el registre d'activitat. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse

from apps.accounts.models import Account
from apps.core import audit, charges
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees
from apps.members import services as members
from apps.members.fee_rules import local_today
from apps.members.models import Member
from apps.members.tests.test_roster import admin_client, make_member
from apps.payments.models import PaymentAttempt, Receipt
from apps.treasury import services
from apps.treasury.models import Movement, TreasuryAccount
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

REASON = "Paga en efectiu a la secretaria (motiu inventat)"
URL = "administration:treasury_manual_payment"
EMAIL = "anna.mero@example.org"
ROLES_WITHOUT = [
    "secretary",
    "administrator",
    "president",
    "board",
    "instructor",
    "courses_manager",
    "history_department",
]


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin("treasurer")


@pytest.fixture
def cash():
    return TreasuryAccount.objects.get(name="Caixa")


@pytest.fixture
def bank():
    return TreasuryAccount.objects.get(name="Banc principal")


@pytest.fixture
def fee():
    member = make_member(1954, status=Member.Status.PENDING, contact_email=EMAIL)
    today = local_today()
    return fees.issue_annual_fee(member, period=today.year, due_on=today, by=audit.system("proves"))


def snapshot():
    return (
        list(Charge.objects.values_list("pk", "status")),
        Payment.objects.count(),
        Movement.objects.count(),
        Receipt.objects.count(),
        list(Member.objects.values_list("pk", "status")),
    )


def record(fee, by, account, reason=REASON):
    return services.record_manual_payment(fee.charge, account=account, reason=reason, by=by)


class TestService:
    def test_p_12_everything_at_once_with_the_charge_amount_in_cents(self, fee, treasurer, cash):
        movement = record(fee, treasurer, cash)
        charge = Charge.objects.get(pk=fee.charge_id)
        payment = Payment.objects.get(charge=charge)
        assert charge.status == Charge.Status.PAID
        assert (payment.method, payment.amount_cents) == ("manual", charge.amount_cents)
        assert (payment.recorded_by, payment.reason) == (treasurer, REASON)
        # RN-T08 i RN-T10: el compte triat, el mateix import i el centre de cost de les quotes.
        assert (movement.kind, movement.direction) == (Movement.Kind.INCOME, "in")
        assert (movement.account, movement.amount_cents, movement.payment) == (
            cash,
            charge.amount_cents,
            payment,
        )
        assert (movement.department.name, movement.cost_centre.name) == (
            "General",
            "Quotes de socis",
        )
        assert movement.recorded_by == treasurer
        # El rebut, com qualsevol pagament confirmat (RN-M05b-19), i el correu al pagador.
        receipt = Receipt.objects.get(attempt__charge=charge)
        assert receipt.attempt.method == PaymentAttempt.Method.MANUAL
        assert receipt.attempt.status == PaymentAttempt.Status.PAID
        assert OutgoingEmail.objects.filter(template="pagament-confirmat", to_address=EMAIL)
        # La quota pagada: el soci pendent passa a actiu i té carnet (on_fee_paid).
        member = Member.objects.get(pk=fee.member_id)
        assert member.status == Member.Status.ACTIVE
        assert cards.active_card(member) is not None

    def test_p_12_the_audit_log_says_who_why_and_from_where(self, fee, treasurer, cash):
        movement = record(fee, treasurer, cash)
        paid = AuditEntry.objects.get(action="charges.status_changed", new_value="paid")
        assert (paid.actor_account, paid.reason) == (treasurer, REASON)
        assert paid.details["origin"] == "manual"
        income = AuditEntry.objects.get(action=services.INCOME_RECORDED)
        assert (income.actor_account, income.reason) == (treasurer, REASON)
        assert income.details == {
            "payment": movement.payment_id,
            "charge": fee.charge_id,
            "amount_cents": fee.charge.amount_cents,
            "account": "Caixa",
            "origin": "manual",
        }

    def test_rn_t08_it_can_go_into_the_bank_account(self, fee, treasurer, bank):
        assert record(fee, treasurer, bank).account == bank

    @pytest.mark.parametrize("role", ROLES_WITHOUT)
    def test_q_037_without_m14_not_found_and_nothing_changes(self, fee, cash, make_admin, role):  # noqa: F811
        before = snapshot()
        with pytest.raises(Http404):
            record(fee, make_admin(role), cash)
        with pytest.raises(Http404):
            charges.record_manual_payment(fee.charge, reason=REASON, by=make_admin(role))
        assert snapshot() == before

    def test_q_037_a_personal_account_or_the_system_cannot(self, fee, cash):
        personal = Account.objects.create_personal(fee.member.person, EMAIL, PASSWORD)
        for by in (personal, audit.system("proves"), None):
            with pytest.raises(Http404):
                record(fee, by, cash)
        assert not Payment.objects.exists()

    @pytest.mark.parametrize("reason", ["", "   "])
    def test_rn_72_without_a_reason_nothing_changes(self, fee, treasurer, cash, reason):
        before = snapshot()
        with pytest.raises(ValidationError):
            record(fee, treasurer, cash, reason=reason)
        assert snapshot() == before

    def test_only_a_pending_charge(self, fee, treasurer, cash):
        record(fee, treasurer, cash)
        before = snapshot()
        with pytest.raises(ValidationError):
            record(fee, treasurer, cash)
        charges.create_charge(
            fee.member.person,
            kind=Charge.Kind.FEE,
            amount_cents=500,
            concept="Quota anul·lada",
            origin="members",
            by=audit.system("proves"),
        )
        cancelled = Charge.objects.get(concept="Quota anul·lada")
        charges.cancel(cancelled, "Error (prova)", by=audit.system("proves"))
        with pytest.raises(ValidationError):
            services.record_manual_payment(cancelled, account=cash, reason=REASON, by=treasurer)
        assert snapshot()[1:] == before[1:]

    def test_nobody_records_the_payment_of_their_own_charge(self, fee, cash, make_admin):  # noqa: F811
        own = make_admin("treasurer", person=fee.member.person)
        before = snapshot()
        with pytest.raises(ValidationError):
            record(fee, own, cash)
        assert snapshot() == before

    def test_rn_t08_never_a_transit_or_inactive_account(self, fee, treasurer, cash):
        transit = TreasuryAccount.objects.create(
            name="Trànsit (prova)", kind="transit", provider_code="prova"
        )
        before = snapshot()
        with pytest.raises(services.IncomeAccountUnavailable):
            record(fee, treasurer, transit)
        TreasuryAccount.objects.filter(pk=cash.pk).update(active=False)
        with pytest.raises(services.IncomeAccountUnavailable):
            record(fee, treasurer, cash)
        assert snapshot() == before

    def test_all_or_nothing_if_the_member_step_fails(self, fee, treasurer, cash, monkeypatch):
        def broken(annual_fee_id):
            raise members.InvalidTransition("prova")

        monkeypatch.setattr(members, "on_fee_paid", broken)
        before = snapshot()
        with pytest.raises(members.InvalidTransition):
            record(fee, treasurer, cash)
        assert snapshot() == before

    def test_the_generic_paths_still_refuse_the_manual_origin(self, fee, treasurer):
        with pytest.raises(ValidationError):
            charges.record_payment(fee.charge, method="manual", origin="manual", by=treasurer)
        assert not Payment.objects.exists()


class TestScreen:
    def test_the_member_detail_shows_the_action_only_with_m14(self, fee, treasurer, make_admin):  # noqa: F811
        detail = reverse("administration:member_detail", args=[fee.member_id])
        link = reverse(URL, args=[fee.charge_id])
        assert link in admin_client(treasurer).get(detail).content.decode()
        secretary = make_admin("secretary")
        assert link not in admin_client(secretary).get(detail).content.decode()

    @pytest.mark.parametrize("role", ROLES_WITHOUT)
    def test_q_037_without_m14_not_found(self, fee, cash, make_admin, role):  # noqa: F811
        client, url = admin_client(make_admin(role)), reverse(URL, args=[fee.charge_id])
        data = {"account": cash.pk, "reason": REASON, "confirm": "1"}
        assert client.get(url).status_code == 404
        assert client.post(url, data).status_code == 404
        assert not Payment.objects.exists()

    def test_two_steps_amount_and_member_then_back_to_the_member(self, fee, treasurer, cash):
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        page = client.get(url).content.decode()
        assert "90,00 €" in page and "Soci 1954" in page
        first = client.post(url, {"account": cash.pk, "reason": REASON})
        assert "Confirma el pagament" in first.content.decode()
        assert not Payment.objects.exists()
        done = client.post(url, {"account": cash.pk, "reason": REASON, "confirm": "1"})
        assert done.status_code == 302
        assert done.url == reverse("administration:member_detail", args=[fee.member_id])
        assert Payment.objects.get().method == "manual"

    def test_without_a_reason_the_form_says_so(self, fee, treasurer, cash):
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        response = client.post(url, {"account": cash.pk, "reason": "", "confirm": "1"})
        assert "Cal el motiu." in response.content.decode()
        assert not Payment.objects.exists()

    def test_a_paid_charge_has_no_form(self, fee, treasurer, cash):
        record(fee, treasurer, cash)
        page = admin_client(treasurer).get(reverse(URL, args=[fee.charge_id])).content.decode()
        assert "no és pendent" in page and 'name="reason"' not in page

    def test_post_without_csrf_is_refused(self, fee, treasurer, cash):
        client = admin_client(treasurer, csrf=True)
        data = {"account": cash.pk, "reason": REASON, "confirm": "1"}
        assert client.post(reverse(URL, args=[fee.charge_id]), data).status_code == 403
        assert not Payment.objects.exists()
