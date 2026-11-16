"""Pagar per transferència (T-M05b-06; P-M05b-C; CA-M05b-10 i 11; RN-M05b-05 i 09; P-136 i
P-137, opcions per defecte). Només dades inventades: l'IBAN del club és de proves."""

import pytest
from django.db import DatabaseError, connection, transaction
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.core import audit, charges
from apps.core.models import AppendOnlyError, AuditEntry, Charge, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import attempts, checkout, transfers
from apps.payments.models import InvalidTransition, Receipt, ReceiptCancellation
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.providers import base, fake
from apps.payments.tests.test_checkout import SITE, new_charge
from apps.treasury import reconciliation
from apps.treasury.tests.test_reconciliation import lines, ref, treasurer  # noqa: F401

pytestmark = pytest.mark.django_db
S = Attempt.Status
TRANSFER = Attempt.Method.TRANSFER
IBAN = "ES00 0000 0000 0000 0000 0000"  # inventat: cap compte real


@pytest.fixture(autouse=True)
def configured(settings):
    settings.PUBLIC_SITE_URL = SITE
    settings.CLUB_IBAN_TRANSFERENCIES = IBAN
    settings.TRANSFER_REFERENCE_PREFIX = "CRIS"
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def charge(personal_account):
    return new_charge(personal_account.person)


@pytest.fixture
def member(login_as, personal_account):
    return login_as(personal_account, AREA_PERSONAL)


def screen(client, charge):
    return client.get(reverse("payments:charge", args=[charge.pk])).content.decode()


def pay_by_transfer(client, charge):
    return client.post(reverse("payments:pay_transfer", args=[charge.pk]))


def confirm(charge, by):
    (line,) = lines(by, (charge.amount_cents, f"TRANSF {ref(charge)} QUOTA"))
    reconciliation.refresh()
    return reconciliation.confirm(line, by=by)


class TestStart:
    def test_ca_m05b_10_the_transfer_waits_with_the_reference_of_the_charge(
        self, charge, personal_account
    ):
        start = checkout.start_payment(charge, TRANSFER, personal_account)
        attempt = Attempt.objects.get()
        assert (attempt.method, attempt.status) == (TRANSFER, S.IN_PROGRESS)
        assert attempt.amount_cents == 9000
        assert (start.kind, start.amount_cents) == (checkout.TRANSFER_DETAILS, 9000)
        assert start.club_iban == "ES0000000000000000000000"
        assert start.reference == ref(charge)  # la del càrrec, que no canvia (RN-T20)
        assert not fake._orders  # cap ordre al proveïdor
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PENDING  # mai pagat pel navegador (RN-M05b-05)

    def test_without_the_club_iban_it_is_not_offered_nor_started(
        self, settings, charge, personal_account, member
    ):
        settings.CLUB_IBAN_TRANSFERENCIES = ""
        with pytest.raises(attempts.MethodNotAllowed):
            checkout.start_payment(charge, TRANSFER, personal_account)
        assert "Paga per transferència" not in screen(member, charge)
        assert not Attempt.objects.exists()

    def test_level_1_refuses_the_transfer_too(self, settings, charge, personal_account):
        settings.PAYMENTS_ENVIRONMENT = base.LIVE
        settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False
        with pytest.raises(base.LiveChargesNotAllowed):
            checkout.start_payment(charge, TRANSFER, personal_account)
        assert not Attempt.objects.exists()

    def test_someone_elses_charge_is_not_started(self, personal_account, make_person):
        other = new_charge(make_person("Pere", "Inventat"))
        with pytest.raises(checkout.NotOwnCharge):
            checkout.start_payment(other, TRANSFER, personal_account)
        assert not Attempt.objects.exists()

    def test_rn_m05b_04_not_while_a_card_payment_is_open(self, charge, personal_account, member):
        checkout.start_payment(charge, Attempt.Method.CARD, personal_account)
        response = pay_by_transfer(member, charge)
        assert response.status_code == 302
        assert Attempt.objects.filter(method=TRANSFER).count() == 0
        assert "El pagament anterior encara no" in screen(member, charge)  # «'» s'escapa


class TestScreen:
    def test_ca_m05b_10_iban_amount_and_reference_each_copiable(self, charge, member):
        assert "Paga per transferència" in screen(member, charge)
        response = pay_by_transfer(member, charge)
        assert response.url == reverse("payments:charge", args=[charge.pk])
        page = screen(member, charge)
        assert "Esperant la transferència" in page
        assert "ES00 0000 0000 0000 0000 0000" in page
        assert "90,00" in page and ref(charge) in page
        for value in ("ES0000000000000000000000", "90,00", ref(charge)):
            assert f'data-copia="{value}"' in page
        assert "hx-get" not in page  # la prova és l'extracte: la pantalla no pregunta
        assert "Paga per transferència" not in page
        assert "js/copia.js" in page

    def test_p_136_paying_by_card_abandons_the_waiting_transfer(
        self, charge, member, personal_account
    ):
        pay_by_transfer(member, charge)
        assert "Paga amb targeta" in screen(member, charge)
        start = checkout.start_payment(charge, Attempt.Method.CARD, personal_account)
        transfer = Attempt.objects.get(method=TRANSFER)
        assert transfer.status == S.ABANDONED
        assert Attempt.objects.get(pk=start.attempt_id).status == S.IN_PROGRESS
        entry = AuditEntry.objects.get(reason="P-136: un altre mètode")
        assert entry.action == "payments.attempt_status_changed"
        assert entry.target_id == str(transfer.pk)


class TestReconciled:
    def test_ca_m05b_11_the_member_sees_paid_and_the_receipt(
        self,
        charge,
        member,
        treasurer,  # noqa: F811
    ):
        pay_by_transfer(member, charge)
        confirm(charge, treasurer)
        attempt = Attempt.objects.get()
        assert attempt.status == S.PAID
        receipt = Receipt.objects.get(attempt=attempt)
        payment = Payment.objects.get()
        assert (payment.method, payment.transfer_reference) == ("transfer", ref(charge))
        page = screen(member, charge)
        assert "Pagat" in page and "Esperant la transferència" not in page
        assert reverse("payments:receipt", args=[attempt.pk]) in page
        receipt_page = member.get(reverse("payments:receipt", args=[attempt.pk])).content.decode()
        assert receipt.number in receipt_page and "Transferència" in receipt_page

    def test_paid_without_the_screen_still_gets_an_attempt_and_a_receipt(
        self,
        charge,
        treasurer,  # noqa: F811
    ):
        confirm(charge, treasurer)
        attempt = Attempt.objects.get()
        assert (attempt.method, attempt.status, attempt.started_by) == (TRANSFER, S.PAID, None)
        assert Receipt.objects.filter(attempt=attempt).exists()

    def test_p_137_with_a_card_payment_open_the_charge_is_paid_without_receipt(
        self,
        charge,
        personal_account,
        treasurer,  # noqa: F811
    ):
        checkout.start_payment(charge, Attempt.Method.CARD, personal_account)
        confirm(charge, treasurer)
        charge.refresh_from_db()
        assert charge.status == Charge.Status.PAID
        assert not Attempt.objects.filter(method=TRANSFER).exists()
        assert not Receipt.objects.exists()
        entry = AuditEntry.objects.get(action=transfers.RECEIPT_PENDING)
        assert entry.reason.startswith("P-137")

    def test_other_payments_are_left_alone(self, charge):
        attempt = attempts.create_attempt(charge, Attempt.Method.CARD)
        attempts.transition(attempt, S.IN_PROGRESS, by=audit.system("proves"))
        charges.record_payment(charge, method="card", origin="provider", by=audit.system("proves"))
        assert Attempt.objects.get().status == S.IN_PROGRESS  # ho fa el processament, no aquí
        assert not Receipt.objects.exists()


class TestReverted:
    """045 (T-M05b-29; P-122, opció per defecte): el tresorer torna a pendent un càrrec que una
    transferència conciliada va pagar per error. L'intent pagat queda cancel·lat i el rebut,
    anul·lat amb una nota; res s'esborra, i el càrrec es torna a pagar amb un intent i un rebut
    nous."""

    REASON = "Càrrec equivocat (prova)"

    def revert(self, charge, by):
        return charges.revert_paid_transfer(charge, self.REASON, by=by)

    def test_revert_then_transfer_again_gives_a_new_attempt_and_receipt(
        self,
        charge,
        treasurer,  # noqa: F811
    ):
        confirm(charge, treasurer)
        old = Receipt.objects.get()
        self.revert(charge, treasurer)

        old.refresh_from_db()
        assert old.attempt.status == S.CANCELLED
        assert old.cancellation.note == f"045: {self.REASON}"
        entry = AuditEntry.objects.get(action=transfers.RECEIPT_CANCELLED)
        assert (entry.actor_account, entry.reason) == (treasurer, self.REASON)

        charges.record_payment(charge, method="transfer", origin="reconciliation", by=treasurer)

        new = Receipt.objects.exclude(pk=old.pk).get()
        assert new.attempt.status == S.PAID and new.number != old.number
        assert not hasattr(new, "cancellation")
        assert sorted(Attempt.objects.values_list("status", flat=True)) == ["cancelled", "paid"]

    def test_the_receipt_cancellation_is_never_changed(
        self,
        charge,
        treasurer,  # noqa: F811
    ):
        confirm(charge, treasurer)
        self.revert(charge, treasurer)
        cancellation = ReceiptCancellation.objects.get()
        with pytest.raises(AppendOnlyError):
            cancellation.save()
        with pytest.raises(AppendOnlyError):
            cancellation.delete()
        for sql in ("UPDATE {} SET note = 'x'", "DELETE FROM {}"):
            with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
                cur.execute(sql.format(ReceiptCancellation._meta.db_table))

    def test_p_137_a_transfer_without_attempt_reverts_without_touching_the_card(
        self,
        charge,
        personal_account,
        treasurer,  # noqa: F811
    ):
        checkout.start_payment(charge, Attempt.Method.CARD, personal_account)
        confirm(charge, treasurer)
        self.revert(charge, treasurer)
        assert Attempt.objects.get().status == S.IN_PROGRESS
        assert not ReceiptCancellation.objects.exists()

    def test_only_a_transfer_attempt_can_leave_paid(self, charge):
        by = audit.system("proves")
        attempt = attempts.create_attempt(charge, Attempt.Method.CARD)
        attempt = attempts.transition(attempt, S.IN_PROGRESS, by=by)
        attempt = attempts.transition(attempt, S.PAID, by=by)
        with pytest.raises(InvalidTransition):
            attempts.transition(attempt, S.CANCELLED, by=by)
