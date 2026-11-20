"""Recordatori d'una transferència que no arriba (T-M05b-22c; RN-M05b-09; P-M05b-C, pas 4; P-407,
opció A): passats `payments.transfer_reminder_days` dies (VC-16: 30, de 7 a 60, el Tresorer),
l'intent es tanca, el càrrec continua pendent i el pagador rep un sol recordatori. Només dades
inventades."""

import re
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.http import Http404
from django.utils import timezone

from apps.core import business_settings, charges
from apps.core.models import AuditEntry, Charge, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import attempts, transfer_reminders
from apps.payments.models import PaymentAttempt
from apps.payments.tests.test_payments_list import SYSTEM, fee
from apps.treasury import services as treasury

pytestmark = pytest.mark.django_db

S, M = PaymentAttempt.Status, PaymentAttempt.Method
TEMPLATE = "recordatori-transferencia"


@pytest.fixture
def waiting(make_person):
    """Una transferència en espera d'una persona amb correu, començada fa `days` dies."""

    def make(days):
        person = make_person("Núria", "Coll", contact_email="nuria@example.org")
        attempt = attempts.transition(
            attempts.create_attempt(fee(person), M.TRANSFER), S.IN_PROGRESS, by=SYSTEM
        )
        started(attempt, days)
        return attempt

    return make


def started(attempt, days):
    """L'intent comença fa `days` dies (el model no deixa canviar-lo amb l'ORM)."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE payments_paymentattempt SET created_at = %s WHERE id = %s",
            [timezone.now() - timedelta(days=days), attempt.pk],
        )


def emails():
    return OutgoingEmail.objects.filter(template=TEMPLATE)


def test_before_the_deadline_nothing_happens(waiting):
    attempt = waiting(29)
    assert transfer_reminders.send_due() == 0
    attempt.refresh_from_db()
    assert attempt.status == S.IN_PROGRESS and not emails().exists()


def test_after_the_deadline_the_attempt_closes_and_one_email_goes(waiting):
    attempt = waiting(30)
    assert transfer_reminders.send_due() == 1
    attempt.refresh_from_db()
    assert attempt.status == S.EXPIRED
    charge = Charge.objects.get(pk=attempt.charge_id)
    assert charge.status == Charge.Status.PENDING
    assert not charge.attempts.filter(status=S.IN_PROGRESS).exists()  # es pot tornar a pagar
    (email,) = emails()
    assert email.to_address == "nuria@example.org"
    assert treasury.transfer_reference(charge) in email.body_text
    assert charges.euros(9000) in email.body_text
    # Cap IBAN: ni el del club ni res que en tingui la forma.
    assert not re.search(r"[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,}", email.body_text)
    entry = AuditEntry.objects.get(action=transfer_reminders.SENT)
    assert entry.details == {"email_sent": True}


def test_a_second_pass_sends_nothing(waiting):
    waiting(40)
    transfer_reminders.send_due()
    assert transfer_reminders.send_due() == 0
    assert emails().count() == 1


def test_only_transfers_in_progress(waiting, make_person):
    person = make_person("Pere", "Roca", contact_email="pere@example.org")
    card = attempts.transition(
        attempts.create_attempt(fee(person), M.CARD), S.IN_PROGRESS, by=SYSTEM
    )
    started(card, 90)
    assert transfer_reminders.send_due() == 0
    card.refresh_from_db()
    assert card.status == S.IN_PROGRESS


def test_the_days_come_from_the_setting(waiting, make_admin):  # noqa: F811
    attempt = waiting(10)
    business_settings.change(transfer_reminders.DAYS, 7, make_admin("treasurer"))
    assert transfer_reminders.send_due() == 1
    attempt.refresh_from_db()
    assert attempt.status == S.EXPIRED


@pytest.mark.parametrize(("value", "ok"), [(7, True), (60, True), (6, False), (61, False)])
def test_the_treasurer_edits_from_7_to_60(make_admin, value, ok):  # noqa: F811
    treasurer = make_admin("treasurer")
    if ok:
        business_settings.change(transfer_reminders.DAYS, value, treasurer)
        assert business_settings.get(transfer_reminders.DAYS) == value
    else:
        with pytest.raises(ValidationError):
            business_settings.change(transfer_reminders.DAYS, value, treasurer)
        assert business_settings.get(transfer_reminders.DAYS) == 30


@pytest.mark.parametrize("role", ["administrator", "secretary", "president"])
def test_without_the_permission_it_cannot_be_edited(make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        business_settings.change(transfer_reminders.DAYS, 20, make_admin(role))
    assert business_settings.get(transfer_reminders.DAYS) == 30


def test_a_late_transfer_still_pays_the_expired_attempt(waiting):
    attempt = waiting(31)
    transfer_reminders.send_due()
    attempt.refresh_from_db()
    attempts.transition(attempt, S.PAID, by=SYSTEM)  # RN-M05b-03: caducat → pagat
    attempt.refresh_from_db()
    assert attempt.status == S.PAID
