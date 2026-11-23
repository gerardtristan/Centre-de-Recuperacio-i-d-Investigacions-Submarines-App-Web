"""Avisos per correu a l'alumne (T-M02-21; RN-M02-19; VC-23; P-M02-F passos 4 a 6). Només dades
inventades."""

import datetime

import pytest
from django.utils import timezone

from apps.activities import certificates, notifications, reinforcement, tasks
from apps.activities.models import (
    Activity,
    CertificationLevel,
    ReinforcementRequest,
    TrainingCatalogueEntry,
)
from apps.core import business_settings
from apps.core.models import OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_place, an_outing
from .test_attendance import DAY, course, enrolled, manager, opened  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
TWO_DAYS_BEFORE = DAY - datetime.timedelta(days=2)


def with_email(enrolment, address):
    Person.objects.filter(pk=enrolment.person_id).update(contact_email=address)
    enrolment.person.refresh_from_db()
    return enrolment


def sent(template):
    return sorted(
        OutgoingEmail.objects.filter(template=template).values_list("to_address", flat=True)
    )


def test_rn_m02_19_reminder_to_confirmed_students_two_days_before(course, manager):  # noqa: F811
    with_email(course.student, "alumna@example.org")
    with_email(course.unpaid, "pendent@example.org")  # pendent de pagament: no en rep
    outing = opened(an_outing(manager, starts_on=DAY, ends_on=DAY), Activity.Status.OPEN)
    with_email(enrolled(outing, "Sortida"), "sortida@example.org")
    assert notifications.send_reminders(TWO_DAYS_BEFORE) == 2
    assert sent(notifications.REMINDER) == ["alumna@example.org", "sortida@example.org"]
    email = OutgoingEmail.objects.filter(to_address="alumna@example.org").get()
    assert course.activity.title in email.body_text and "14/06/2027" in email.body_text
    # L'endemà, la segona sessió del curs; el mateix dia de la sessió, res.
    assert notifications.send_reminders(TWO_DAYS_BEFORE + datetime.timedelta(days=1)) == 1
    assert notifications.send_reminders(DAY) == 0


def test_vc_23_the_days_come_from_the_setting(course, monkeypatch):  # noqa: F811
    with_email(course.student, "alumna@example.org")
    real = business_settings.get
    monkeypatch.setattr(
        business_settings, "get",
        lambda key, at=None: 0 if key == notifications.REMINDER_DAYS else real(key, at),
    )  # fmt: skip
    assert notifications.send_reminders(DAY) == 1


def test_without_an_address_nothing_is_sent(course):  # noqa: F811
    assert notifications.send_reminders(TWO_DAYS_BEFORE) == 0
    assert not OutgoingEmail.objects.exists()


def test_outcome_and_certificate_emails(course, manager):  # noqa: F811
    with_email(course.student, "alumna@example.org")
    certificates.record_outcome(course.student, result="pass", by=course.own)
    email = OutgoingEmail.objects.get(template=notifications.OUTCOME)
    assert "Has superat" in email.body_text
    level = CertificationLevel.objects.create(name="Nivell inventat", rank=99)
    outcome = certificates.issue(course.student, by=manager, level=level)
    email = OutgoingEmail.objects.get(template=notifications.CERTIFICATE)
    assert outcome.certificate_number in email.body_text


def test_a_fail_does_not_send_the_reason(course):  # noqa: F811
    with_email(course.student, "alumna@example.org")
    certificates.record_outcome(
        course.student, result="fail", by=course.own, reason="Motiu pedagògic (inventat)."
    )
    email = OutgoingEmail.objects.get(template=notifications.OUTCOME)
    assert "no apte" in email.body_text and "Motiu pedagògic" not in email.body_text


def test_confirmed_reinforcement_sends_dates_and_price(course, manager):  # noqa: F811
    with_email(course.student, "alumna@example.org")
    TrainingCatalogueEntry.objects.filter(pk=course.activity.catalogue_entry_id).update(
        reinforcement_price_cents=3000
    )
    proposal = ReinforcementRequest.objects.create(
        enrolment=course.student, proposed_by=course.own, classes=1,
        reason="Motiu (inventat).", status="proposed",
    )  # fmt: skip
    start = timezone.make_aware(datetime.datetime.combine(DAY, datetime.time(10)))
    reinforcement.confirm(proposal, by=manager, sessions_data=[{
        "kind": "pool", "starts_at": start, "ends_at": start + datetime.timedelta(hours=1),
        "place": a_place(manager, prices=None), "instructors": [course.own.person],
    }])  # fmt: skip
    email = OutgoingEmail.objects.get(template=notifications.REINFORCEMENT)
    assert "14/06/2027 10:00" in email.body_text and "30,00" in email.body_text
    assert "Motiu (inventat)." not in email.body_text
    # El recordatori d'aquell dia també li arriba per la sessió de reforç.
    OutgoingEmail.objects.all().delete()
    notifications.send_reminders(TWO_DAYS_BEFORE)
    assert sent(notifications.REMINDER) == ["alumna@example.org", "alumna@example.org"]


def test_the_daily_task_calls_the_reminders(monkeypatch):
    periodic = tasks.app.periodic_registry.periodic_tasks[("activities.send_reminders", "")]
    assert periodic.cron == "0 8 * * *"
    calls = []
    monkeypatch.setattr(notifications, "send_reminders", lambda: calls.append(1))
    tasks.send_reminders.func(timestamp=0)
    assert calls == [1]
