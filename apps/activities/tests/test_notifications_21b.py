"""Avisos de la inscripció, del canvi de programa i del missatge de l'organitzador (T-M02-21b;
RN-M02-18 i 19; CA-M02-20; AC15). Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import cancellation, enrolment, extensions, notifications, sessions
from apps.activities.models import Enrolment, ReminderSent
from apps.core.models import OutgoingEmail, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import BEFORE_DEADLINE, a_member, an_open_course, an_open_outing
from .test_attendance import a_session

pytestmark = pytest.mark.django_db
NOW = BEFORE_DEADLINE


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def member(address):
    account = a_member()
    Person.objects.filter(pk=account.person_id).update(contact_email=address)
    account.person.refresh_from_db()
    return account


def enrol(activity, account):
    return enrolment.enrol(
        activity, account.person, channel=Enrolment.Channel.ACCOUNT, actor=account, now=NOW
    )


def bodies(template):
    return list(OutgoingEmail.objects.filter(template=template).values_list("body_text", flat=True))


def test_payment_deadline_then_confirmation_once(manager):  # noqa: F811
    outing = an_open_outing(manager, max_places=12)
    row = enrol(outing, member("soci@example.org"))
    (body,) = bodies(notifications.PAYMENT)
    assert outing.title in body and "45,00" in body and f"/{row.charge_id}/" in body
    extensions.enrolment_confirmed.send(sender=Enrolment, enrolment=row)
    extensions.enrolment_confirmed.send(sender=Enrolment, enrolment=row)  # repetit: res
    assert len(bodies(notifications.CONFIRMED)) == 1
    assert ReminderSent.objects.filter(enrolment=row).count() == 2


def test_offer_to_the_first_on_the_waitlist(manager):  # noqa: F811
    outing = an_open_outing(manager, max_places=1)
    first_account = member("primer@example.org")
    first = enrol(outing, first_account)
    waiting = enrol(outing, member("espera@example.org"))
    assert waiting.status == Enrolment.Status.WAITLISTED
    cancellation.cancel_enrolment(first, by=first_account, reason="No pot venir.", now=NOW)
    waiting.refresh_from_db()
    assert waiting.status == Enrolment.Status.OFFERED
    assert OutgoingEmail.objects.filter(template=notifications.OFFER).get().to_address == (
        "espera@example.org"
    )
    (body,) = bodies(notifications.CANCELLED)  # la del primer, sense motiu del club
    assert "No pot venir" not in body and "s'ha cancel·lat" in body


def test_a_cancelled_activity_tells_everyone_with_the_reason(manager):  # noqa: F811
    outing = an_open_outing(manager, max_places=12)
    enrol(outing, member("a@example.org"))
    enrol(outing, member("b@example.org"))
    cancellation.cancel_activity(outing, by=manager, reason="Mal temps (inventat).", now=NOW)
    sent = bodies(notifications.CANCELLED)
    assert len(sent) == 2 and all("Mal temps (inventat)." in body for body in sent)


def test_ca_m02_20_a_time_change_tells_all_live_enrolments(manager):  # noqa: F811
    course = an_open_course(manager)
    session = a_session(manager, course, course.starts_on)
    enrol(course, member("a@example.org"))
    enrol(course, member("b@example.org"))
    OutgoingEmail.objects.all().delete()
    later = session.starts_at + datetime.timedelta(hours=1)
    sessions.update_session(
        session, by=manager, starts_at=later, ends_at=session.ends_at + datetime.timedelta(hours=1)
    )
    assert len(bodies(notifications.CHANGE)) == 2
    sessions.update_session(session, by=manager, is_practice=not session.is_practice)
    assert len(bodies(notifications.CHANGE)) == 2  # no és de dia, hora ni lloc
    sessions.cancel_session(session, by=manager, reason="Piscina tancada (inventat).")
    assert sum("cancel·lat" in body for body in bodies(notifications.CHANGE)) == 2


def test_ac15_the_organiser_message(manager, make_admin):  # noqa: F811
    outing = an_open_outing(manager, max_places=12)
    enrol(outing, member("a@example.org"))
    assert (
        notifications.send_message(
            outing, by=manager, subject="Canvi de punt de trobada", body="Ens veiem al moll 3."
        )
        == 1
    )
    email = OutgoingEmail.objects.get(template=notifications.MESSAGE)
    assert email.subject == "Canvi de punt de trobada" and "Ens veiem al moll 3." in email.body_text
    with pytest.raises(ValidationError):
        notifications.send_message(outing, by=manager, subject="", body="x")
    with pytest.raises(Http404):
        notifications.send_message(
            outing, by=make_admin(Role.Code.INSTRUCTOR), subject="x", body="y"
        )


def test_a_guest_gets_no_payment_notice(manager):  # noqa: F811
    outing = an_open_outing(manager, max_places=12)
    row = enrol(outing, member("soci@example.org"))
    Enrolment.objects.filter(pk=row.pk).update(channel=Enrolment.Channel.GUEST)
    row.refresh_from_db()
    assert notifications.notify_payment(row) is False  # el convidat ja rep l'enllaç per pagar
