"""Registre manual d'un pagament (P-12; RN-72 de la 00; 072, Q-037 i Q-038; RN-T08, RN-T10).

M14 (inicialment, el Tresorer), motiu obligatori, només un càrrec pendent i mai un de propi. Tot
o res: el càrrec pagat amb el pagament «manual», l'ingrés al compte triat (caixa o banc), el
rebut, el soci actiu amb carnet i el registre d'activitat. Només dades inventades."""

import re
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit, charges, permissions
from apps.core.models import (
    AuditEntry,
    Charge,
    Department,
    OutgoingEmail,
    Payment,
    RolePermission,
)
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, fees
from apps.members import services as members
from apps.members.fee_rules import local_today
from apps.members.models import Member
from apps.members.tests.test_roster import admin_client, make_member
from apps.payments import attempts
from apps.payments.models import PaymentAttempt, Receipt, ReceiptCancellation
from apps.payments.transfers import on_payment_saved
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


def review(client, url, account, reason=REASON, paid_on=None):
    """El primer pas: torna la resposta i el testimoni signat del que s'ha mostrat."""
    paid_on = paid_on or timezone.localdate()
    data = {"account": account.pk, "reason": reason, "paid_on": paid_on.isoformat()}
    response = client.post(url, data)
    token = re.search(r'name="token" value="([^"]+)"', response.content.decode())
    return response, token.group(1) if token else None


def record(fee, by, account, reason=REASON, **kwargs):
    return services.record_manual_payment(
        fee.charge, account=account, reason=reason, by=by, **kwargs
    )


def in_flight(fee, method, status):
    """Un intent del càrrec en aquest estat (una domiciliació l'obre el sistema a la remesa)."""
    attempt = PaymentAttempt.objects.create(
        charge=fee.charge, method=method, amount_cents=fee.charge.amount_cents
    )
    system = audit.system("proves")
    if status == "to_review":
        attempts.transition(attempt, "in_progress", by=system)
        attempts.transition(attempt, status, by=system, reason="Resposta dubtosa (prova)")
    else:
        attempts.transition(attempt, status, by=system)
    return attempt


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

    @pytest.mark.parametrize(
        ("method", "status"),
        [
            ("card", "in_progress"),
            ("bizum", "in_progress"),
            ("transfer", "in_progress"),
            ("direct_debit", "sent_to_bank"),
            ("card", "to_review"),  # potser cobrat: el proveïdor no ha donat una resposta clara
            ("bizum", "to_review"),
        ],
    )
    def test_no_double_charge_with_an_attempt_in_progress(
        self, fee, treasurer, cash, method, status
    ):
        in_flight(fee, method, status)
        before = snapshot()
        with pytest.raises(ValidationError, match="pagament en curs"):
            record(fee, treasurer, cash)
        assert snapshot() == before

    def test_the_core_service_itself_refuses_without_the_receipt_hook(self, fee, treasurer):
        in_flight(fee, "card", "in_progress")
        post_save.disconnect(sender=Payment, dispatch_uid="payments.transfer_paid")
        try:
            with pytest.raises(ValidationError, match="pagament en curs"):
                charges.record_manual_payment(fee.charge, reason=REASON, by=treasurer)
        finally:
            post_save.connect(
                on_payment_saved, sender=Payment, dispatch_uid="payments.transfer_paid"
            )
        assert not Payment.objects.exists()

    def test_an_attempt_already_paid_is_a_message_not_an_error(self, fee, treasurer, cash):
        # Un intent pagat d'un càrrec que torna a ser pendent (p. ex., retornat i reobert).
        in_flight(fee, "card", "in_progress")
        attempts.transition(PaymentAttempt.objects.get(), "paid", by=audit.system("proves"))
        before = snapshot()
        with pytest.raises(ValidationError, match="ja té un pagament confirmat"):
            record(fee, treasurer, cash)
        assert snapshot() == before

    def test_the_date_of_receipt_sets_the_payment_and_the_value_date(self, fee, treasurer, cash):
        yesterday = timezone.localdate() - timedelta(days=1)
        movement = record(fee, treasurer, cash, paid_on=yesterday)
        assert timezone.localdate(movement.payment.paid_at) == yesterday
        assert movement.value_date == yesterday

    def test_the_date_of_receipt_is_never_in_the_future(self, fee, treasurer, cash):
        before = snapshot()
        with pytest.raises(ValidationError, match="futur"):
            record(fee, treasurer, cash, paid_on=timezone.localdate() + timedelta(days=1))
        assert snapshot() == before

    def test_the_date_of_receipt_is_never_in_a_closed_period(
        self, fee, treasurer, cash, monkeypatch
    ):
        last_week = timezone.localdate() - timedelta(days=7)
        monkeypatch.setattr(services, "_GUARDS", [])
        services.register_movement_guard(lambda: last_week)
        before = snapshot()
        with pytest.raises(services.PeriodClosed):
            record(fee, treasurer, cash, paid_on=last_week)
        assert snapshot() == before

    def test_if_the_receipt_cannot_be_issued_nothing_is_saved(
        self, fee, treasurer, cash, monkeypatch
    ):
        def busy(*args, **kwargs):
            raise attempts.AttemptInProgress

        monkeypatch.setattr(attempts, "create_attempt", busy)
        before = snapshot()
        with pytest.raises(ValidationError):
            record(fee, treasurer, cash)
        assert snapshot() == before

    def test_cancelling_a_manual_payment_cancels_its_receipt(self, fee, treasurer, cash):
        payment = record(fee, treasurer, cash).payment
        charges._cancel_payment(payment, "Registrat per error (prova)", by=treasurer, origin="P-12")
        receipt = Receipt.objects.get(attempt__charge=fee.charge)
        assert receipt.attempt.status == PaymentAttempt.Status.CANCELLED
        assert ReceiptCancellation.objects.filter(receipt=receipt).exists()

    def test_the_permission_is_checked_once_with_the_charge(
        self, fee, treasurer, cash, monkeypatch
    ):
        seen = []
        real = permissions.has_perm

        def spy(account, code, obj=None, **kwargs):
            seen.append((code, obj))
            return real(account, code, obj, **kwargs)

        monkeypatch.setattr(charges, "has_perm", spy)
        monkeypatch.setattr(services, "has_perm", spy)
        record(fee, treasurer, cash)
        manual = [obj for code, obj in seen if code == charges.MANUAL_PAYMENT]
        assert len(manual) == 1 and manual[0].pk == fee.charge_id

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
        data = {"account": cash.pk, "reason": REASON}
        assert client.get(url).status_code == 404
        assert client.post(url, data).status_code == 404
        assert not Payment.objects.exists()

    def test_two_steps_amount_and_member_then_back_to_the_member(self, fee, treasurer, cash):
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        page = client.get(url).content.decode()
        assert "90,00 €" in page and "Soci 1954" in page
        first, token = review(client, url, cash)
        assert "Confirma el pagament" in first.content.decode() and token
        assert not Payment.objects.exists()
        done = client.post(url, {"token": token})
        assert done.status_code == 302
        assert done.url == reverse("administration:member_detail", args=[fee.member_id])
        assert Payment.objects.get().method == "manual"

    def test_the_second_step_saves_exactly_what_was_confirmed(self, fee, treasurer, cash, bank):
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        first, token = review(client, url, cash)
        # Al segon pas, el compte i el motiu ja no són camps del formulari.
        assert 'name="reason"' not in first.content.decode()
        changed = {"token": token, "account": bank.pk, "reason": "Un altre motiu"}
        assert client.post(url, changed).status_code == 302
        payment = Payment.objects.get()
        assert (payment.reason, Movement.objects.get(payment=payment).account) == (REASON, cash)

    def test_a_tampered_or_foreign_token_saves_nothing(self, fee, treasurer, cash, make_admin):  # noqa: F811
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        _, token = review(client, url, cash)
        other = admin_client(make_admin("treasurer"))
        for c, t in ((client, token + "x"), (other, token)):
            assert "Torna a revisar" in c.post(url, {"token": t}).content.decode()
        assert not Payment.objects.exists()

    def test_without_fee_visibility_not_found(self, fee, treasurer, cash):
        RolePermission.objects.filter(
            role__code="treasurer", permission_code="members.fees.view"
        ).delete()
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        assert client.get(url).status_code == 404
        assert client.post(url, {"account": cash.pk, "reason": REASON}).status_code == 404

    def test_without_an_active_cash_or_bank_account_it_says_so(self, fee, treasurer):
        TreasuryAccount.objects.filter(kind__in=["cash", "bank"]).update(active=False)
        page = admin_client(treasurer).get(reverse(URL, args=[fee.charge_id])).content.decode()
        assert "No hi ha cap caixa ni compte bancari actiu" in page
        assert 'name="reason"' not in page

    def test_an_attempt_in_progress_is_refused_on_the_screen(self, fee, treasurer, cash):
        attempt = attempts.create_attempt(fee.charge, PaymentAttempt.Method.CARD)
        attempts.transition(attempt, PaymentAttempt.Status.IN_PROGRESS, by=audit.system("p"))
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        _, token = review(client, url, cash)
        assert "pagament en curs" in client.post(url, {"token": token}).content.decode()
        assert not Payment.objects.exists()

    def test_the_second_step_keeps_the_date_that_was_shown(self, fee, treasurer, cash):
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        two_days = timezone.localdate() - timedelta(days=2)
        _, token = review(client, url, cash, paid_on=two_days)
        client.post(url, {"token": token, "paid_on": timezone.localdate().isoformat()})
        assert timezone.localdate(Payment.objects.get().paid_at) == two_days

    def test_the_form_refuses_a_future_date(self, fee, treasurer, cash):
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        response, token = review(client, url, cash, paid_on=timezone.localdate() + timedelta(1))
        assert token is None and "futur" in response.content.decode()

    def test_an_attempt_already_paid_shows_a_message(self, fee, treasurer, cash):
        in_flight(fee, "card", "in_progress")
        attempts.transition(PaymentAttempt.objects.get(), "paid", by=audit.system("proves"))
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        _, token = review(client, url, cash)
        response = client.post(url, {"token": token})
        assert response.status_code == 200
        assert "ja té un pagament confirmat" in response.content.decode()

    def test_p10_only_for_a_fee(self, fee, treasurer, cash):
        RolePermission.objects.filter(
            role__code="treasurer", permission_code="members.fees.view"
        ).delete()
        courses = Department.objects.create(name="Cursos (prova)")
        other = charges.create_charge(
            fee.member.person,
            kind=Charge.Kind.ENROLMENT,
            amount_cents=4500,
            concept="Inscripció (prova)",
            origin="activities",
            by=audit.system("proves"),
            department=courses,
        )
        assert admin_client(treasurer).get(reverse(URL, args=[other.pk])).status_code == 200

    def test_the_member_detail_checks_m14_with_each_charge(self, fee, treasurer, monkeypatch):
        from apps.members.views import admin as member_views

        seen = []
        real = member_views.has_perm

        def spy(account, code, obj=None, **kwargs):
            seen.append((code, obj))
            return real(account, code, obj, **kwargs)

        monkeypatch.setattr(member_views, "has_perm", spy)
        admin_client(treasurer).get(reverse("administration:member_detail", args=[fee.member_id]))
        assert (charges.MANUAL_PAYMENT, fee.charge) in seen

    def test_without_a_reason_the_form_says_so(self, fee, treasurer, cash):
        client, url = admin_client(treasurer), reverse(URL, args=[fee.charge_id])
        response = client.post(url, {"account": cash.pk, "reason": ""})
        assert "Cal el motiu." in response.content.decode()
        assert not Payment.objects.exists()

    def test_a_paid_charge_has_no_form(self, fee, treasurer, cash):
        record(fee, treasurer, cash)
        page = admin_client(treasurer).get(reverse(URL, args=[fee.charge_id])).content.decode()
        assert "no és pendent" in page and 'name="reason"' not in page

    def test_post_without_csrf_is_refused(self, fee, treasurer, cash):
        client = admin_client(treasurer, csrf=True)
        data = {"account": cash.pk, "reason": REASON}
        assert client.post(reverse(URL, args=[fee.charge_id]), data).status_code == 403
        assert not Payment.objects.exists()
