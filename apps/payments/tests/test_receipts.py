# Les fixtures es reaprofiten de `test_processing`: cada prova les torna a declarar com a paràmetre.
# ruff: noqa: F811
"""Rebut i correus en confirmar-se el pagament (T-M05b-07; RN-M05b-19; CA-M05b-03, 04 i 05; P-84,
P-85 i P-86). Proveïdor fals, sense xarxa. Només dades inventades.

Fan el camí sencer de `test_processing`: l'intent, la notificació signada a l'endpoint i la cua."""

import time

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import receipts
from apps.payments.models import PaymentAttempt as Attempt
from apps.payments.models import Receipt, ReceiptCounter, ReceiptLocked
from apps.payments.tests.test_processing import (  # noqa: F401 (fixtures)
    account,
    attempt,
    clean_orders,
    fee,
    member,
    notify,
    paying_attempt,
    run_queue,
    transit,
)

pytestmark = pytest.mark.django_db
YEAR = timezone.localdate().year
EMAIL = "anna.contacte@example.org"


@pytest.fixture(autouse=True)
def contact(member):
    member.person.contact_email = EMAIL
    member.person.save()


def emails(template):
    return OutgoingEmail.objects.filter(template=template)


def personal(account):
    """Sessió del compte personal, com si s'hagués entrat pel formulari."""
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_PERSONAL
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def receipt_page(account, attempt):
    return personal(account).get(reverse("payments:receipt", args=[attempt.pk]))


class TestIssue:
    def test_rn_m05b_19_ca_m05b_03_paying_issues_the_receipt_and_mails_the_payer(
        self, attempt, fee, transit
    ):
        notify(attempt)
        run_queue()
        receipt = Receipt.objects.get()
        assert receipt.attempt == attempt
        assert receipt.number == f"R-{YEAR}-000001"
        (email,) = emails(receipts.PAID_TEMPLATE)
        assert email.to_address == EMAIL and email.person == fee.charge.person
        assert receipt.number in email.subject and receipt.number in email.body_text
        assert "90,00 €" in email.body_text and "Quota 2026" in email.body_text
        assert f"/socis/pagaments/{attempt.pk}/rebut/" in email.body_text
        assert "Prova" not in email.body_text  # cap cognom ni cap altra dada personal

    def test_numbers_are_correlative_and_restart_each_year(self, attempt, transit):
        ReceiptCounter.objects.create(year=YEAR - 1, last_number=41)
        notify(attempt)
        second, _ = paying_attempt(
            "bruna.prova@example.org", first="Bruna", number=1300, document="87654321X"
        )
        notify(second, event_id="e-2")
        run_queue()
        assert list(Receipt.objects.order_by("pk").values_list("number", flat=True)) == [
            f"R-{YEAR}-000001",
            f"R-{YEAR}-000002",
        ]
        assert ReceiptCounter.objects.get(year=YEAR - 1).last_number == 41

    def test_ca_m05b_04_a_repeated_notification_gives_no_second_receipt_nor_email(
        self, attempt, transit
    ):
        notify(attempt, event_id="e-1")
        notify(attempt, event_id="e-1")
        notify(attempt, event_id="e-2")  # un altre esdeveniment de la mateixa ordre pagada
        run_queue()
        assert Receipt.objects.count() == 1
        assert emails(receipts.PAID_TEMPLATE).count() == 1
        assert ReceiptCounter.objects.get(year=YEAR).last_number == 1

    def test_no_gaps_when_the_payment_is_undone(self, attempt, transit, monkeypatch):
        """Si alguna cosa falla després d'emetre el rebut, es desfà tot: ni rebut, ni número
        gastat, ni correu. La xarxa de seguretat ho torna a provar."""

        def fail(_fee_id):
            raise RuntimeError("prova")

        monkeypatch.setattr("apps.members.services.on_fee_paid", fail)
        notify(attempt)
        assert run_queue() == ["error"]
        assert not Receipt.objects.exists() and not ReceiptCounter.objects.exists()
        assert not emails(receipts.PAID_TEMPLATE).exists()

    def test_without_an_address_there_is_a_receipt_but_no_email(self, attempt, member, transit):
        member.person.contact_email = ""
        member.person.save()
        notify(attempt)
        run_queue()
        assert Receipt.objects.exists() and not emails(receipts.PAID_TEMPLATE).exists()

    def test_an_attempt_that_is_not_paid_has_no_receipt(self, attempt):
        with pytest.raises(receipts.NotPaid):
            receipts.issue(attempt)
        assert not ReceiptCounter.objects.exists()

    def test_a_receipt_does_not_change_nor_disappear(self, attempt, transit):
        notify(attempt)
        run_queue()
        receipt = Receipt.objects.get()
        receipt.number = "R-2000-000001"
        with pytest.raises(ReceiptLocked):
            receipt.save()
        with pytest.raises(ReceiptLocked):
            Receipt.objects.update(number="R-2000-000001")
        with pytest.raises(Exception, match="no s'esborren"):
            receipt.delete()


class TestReceiptPage:
    def test_the_payer_sees_the_receipt_and_can_save_it_as_pdf(self, attempt, account, transit):
        notify(attempt)
        run_queue()
        response = receipt_page(account, attempt)
        assert response.status_code == 200
        assert "no-store" in response["Cache-Control"]
        html = response.content.decode()
        for text in (
            f"R-{YEAR}-000001",
            timezone.localdate().strftime("%d/%m/%Y"),
            "Quota 2026",
            "90,00",
            "General",
            "Targeta",
            attempt.provider_order_id,
            "No és una factura",
            "Desa com a PDF",
        ):
            assert text in html, text

    def test_the_payment_screen_links_to_the_receipt_once_paid(self, attempt, account, transit):
        client = personal(account)
        screen = reverse("payments:charge", args=[attempt.charge_id])
        link = reverse("payments:receipt", args=[attempt.pk])
        assert link not in client.get(screen).content.decode()
        notify(attempt)
        run_queue()
        assert link in client.get(screen).content.decode()

    def test_someone_elses_receipt_is_not_found_and_recorded(self, attempt, transit):
        notify(attempt)
        run_queue()
        other, _ = paying_attempt(
            "bruna.prova@example.org", first="Bruna", number=1300, document="87654321X"
        )
        response = receipt_page(other.started_by, attempt)
        assert response.status_code == 404
        entry = AuditEntry.objects.filter(action="members.personal_area.not_found").get()
        assert entry.details == {"object": "payments.paymentattempt", "id": attempt.pk}

    def test_an_attempt_without_receipt_is_not_found(self, attempt, account):
        assert receipt_page(account, attempt).status_code == 404

    def test_without_a_session_it_asks_to_log_in(self, attempt, transit):
        notify(attempt)
        run_queue()
        response = Client().get(reverse("payments:receipt", args=[attempt.pk]))
        assert response.status_code == 302


class TestReviewNotice:
    def test_ca_m05b_05_the_treasurer_is_told_without_personal_data(
        self,
        attempt,
        fee,
        transit,
        make_admin,  # noqa: F811
    ):
        treasurer = make_admin(Role.Code.TREASURER)
        treasurer.notification_email = "tresoreria@example.org"
        treasurer.save()
        make_admin(Role.Code.SECRETARY)  # sense T1: no rep res
        notify(attempt, amount_cents=8000)
        assert run_queue() == ["to_review"]
        assert attempt.__class__.objects.get(pk=attempt.pk).status == Attempt.Status.TO_REVIEW
        (email,) = emails("avis-pagament-revisar")
        assert email.to_address == "tresoreria@example.org"
        assert "import o la moneda" in email.body_text and str(attempt.pk) in email.body_text
        for personal in ("Anna", "Prova", EMAIL, "1287"):
            assert personal not in email.body_text + email.subject
        assert not Receipt.objects.exists() and not emails(receipts.PAID_TEMPLATE).exists()

    def test_one_email_per_address_and_none_without_an_address(
        self,
        attempt,
        transit,
        make_admin,  # noqa: F811
    ):
        for _ in range(2):
            account = make_admin(Role.Code.TREASURER)
            account.notification_email = "tresoreria@example.org"
            account.save()
        make_admin(Role.Code.ADMINISTRATOR)  # T1, però sense correu de notificació
        notify(attempt, amount_cents=8000)
        run_queue()
        assert emails("avis-pagament-revisar").count() == 1
