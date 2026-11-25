"""Inscripció de convidats i presencial de qui no és soci, i «Soc major d'edat» (T-M02-14 i
T-M02-34; RN-M02-11 i 35; CA-M02-10, 11 i 37; decisió 021). Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import enrolment, guests
from apps.activities.models import Enrolment
from apps.core import audit, events
from apps.core.models import (
    AuditEntry,
    Charge,
    Consent,
    Event,
    GuestLink,
    LegalText,
    OutgoingEmail,
    Person,
    Role,
)
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import checkout
from apps.payments.models import PaymentAttempt
from apps.payments.providers import fake
from apps.payments.tests.test_processing import notify, run_queue

from .helpers import AFTER_DEADLINE, BEFORE_DEADLINE, a_member, an_open_outing

pytestmark = pytest.mark.django_db

S = Enrolment.Status
NOW = BEFORE_DEADLINE
EMAIL = "convidada@example.org"


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


@pytest.fixture(autouse=True)
def texts():
    """Els textos vigents que demana el formulari (els publica l'administrador amb M12)."""
    for kind, content in (
        ("privacy", "Política inventada."),
        (guests.ADULT, guests.ADULT_PROPOSAL),
    ):
        if not LegalText.objects.filter(kind=kind).exists():
            LegalText.objects.create(kind=kind, version=1, content=content)


def data(**fields):
    return {
        "first_name": "Mar",
        "last_name": "Convidada",
        "contact_email": EMAIL,
        "accept_privacy": True,
        "adult_declared": True,
        **fields,
    }


def test_ca_m02_11_a_guest_pays_the_non_member_price_with_a_guest_link(manager):
    outing = an_open_outing(manager, open_to_non_members=True)

    row = guests.enrol_guest(outing, data(), now=NOW)

    assert (row.status, row.channel, row.created_by) == (S.PENDING_PAYMENT, "guest", None)
    assert (row.price_kind, row.charge.amount_cents) == ("non_member", 6000)
    person = row.person
    assert (person.origin, person.contact_email) == (Person.Origin.GUEST, EMAIL)
    link = GuestLink.objects.get(charge=row.charge)
    assert link.person == person and link.is_live()
    mail = OutgoingEmail.objects.filter(template="enllac-convidat").get()
    assert mail.to_address == EMAIL and outing.title not in mail.body_text  # sense l'activitat
    consent = Consent.objects.get(person=person, legal_text__kind="privacy")
    assert consent.channel == Consent.Channel.WEB
    entry = AuditEntry.objects.get(action=enrolment.CREATED)
    assert entry.actor_kind == AuditEntry.ActorKind.ANONYMOUS


def test_ca_m02_11_the_guest_link_pays_only_its_charge_and_confirms_the_enrolment(manager):
    fake.reset()
    outing = an_open_outing(manager, open_to_non_members=True)
    row = guests.enrol_guest(outing, data(), now=NOW)
    other = guests.enrol_guest(outing, data(contact_email="altra@example.org"), now=NOW)
    link = GuestLink.objects.get(charge=row.charge)

    with pytest.raises(checkout.NotOwnCharge):  # no obre el càrrec d'una altra persona
        checkout.start_payment(other.charge, "card", link)
    start = checkout.start_payment(row.charge, "card", link)
    attempt = PaymentAttempt.objects.get(pk=start.attempt_id)
    notify(attempt, event_id=f"ev-{attempt.pk}")
    run_queue()
    for event in Event.objects.filter(name=events.CHARGE_PAID, payload__charge=row.charge_id):
        events.deliver(event.pk)

    row.refresh_from_db()
    assert row.status == S.CONFIRMED
    fake.reset()


def test_ca_m02_10_an_activity_only_for_members_rejects_a_guest_and_says_how(manager):
    outing = an_open_outing(manager, open_to_non_members=False)
    with pytest.raises(enrolment.NonMembersNotAllowed, match="fer soci"):
        guests.enrol_guest(outing, data(), now=NOW)
    assert not Person.objects.filter(contact_email=EMAIL).exists()


@pytest.mark.parametrize(
    ("fields", "message"),
    [
        ({"first_name": ""}, "nom"),
        ({"contact_email": ""}, "correu"),
        ({"accept_privacy": False}, "privacitat"),
        ({"birth_date": datetime.date(2099, 1, 1)}, ""),
    ],
)
def test_minimum_data_and_privacy_are_required(manager, fields, message):
    outing = an_open_outing(manager, open_to_non_members=True)
    with pytest.raises(ValidationError, match=message or None):
        guests.enrol_guest(outing, data(**fields), now=NOW)
    assert not Enrolment.objects.exists() and not Person.objects.filter(origin="guest").exists()


def test_with_a_minimum_age_the_birth_date_is_required(manager):
    outing = an_open_outing(manager, open_to_non_members=True, min_age=18)
    with pytest.raises(ValidationError, match="naixement"):
        guests.enrol_guest(outing, data(), now=NOW)
    row = guests.enrol_guest(outing, data(birth_date=datetime.date(1990, 5, 1)), now=NOW)
    assert row.requirements_warning == ""


def test_a_closed_activity_rejects_guests(manager):
    outing = an_open_outing(manager, open_to_non_members=True)
    with pytest.raises(enrolment.ActivityNotOpen):
        guests.enrol_guest(outing, data(), now=AFTER_DEADLINE)


def test_the_same_email_as_a_member_creates_a_new_person_and_reveals_nothing(manager):
    """Mai es fusiona amb una persona existent, ni es diu que el correu ja hi era (V-03)."""
    outing = an_open_outing(manager, open_to_non_members=True)
    member = a_member().person
    Person.objects.filter(pk=member.pk).update(contact_email=EMAIL)

    row = guests.enrol_guest(outing, data(), now=NOW)

    assert row.person_id != member.pk and row.price_kind == "non_member"


def test_a_free_or_waitlisted_guest_gets_no_link(manager):
    outing = an_open_outing(
        manager, open_to_non_members=True, max_places=1, price_member_cents=0,
        price_non_member_cents=0, price_override_note="Gratuïta.",
    )  # fmt: skip
    first = guests.enrol_guest(outing, data(), now=NOW)
    second = guests.enrol_guest(outing, data(contact_email="segona@example.org"), now=NOW)
    assert (first.status, second.status) == (S.CONFIRMED, S.WAITLISTED)
    assert not GuestLink.objects.exists()


# --- Presencial (AC5) ----------------------------------------------------------------------------


def test_in_person_the_ac5_account_enrols_and_records_the_consent(make_admin, manager):  # noqa: F811
    outing = an_open_outing(manager, open_to_non_members=True)
    desk = make_admin("treasurer")

    row = guests.enrol_guest(outing, data(), by=desk, now=NOW)

    assert (row.channel, row.created_by) == (Enrolment.Channel.DESK, desk)
    consent = Consent.objects.get(person=row.person, legal_text__kind="privacy")
    assert (consent.channel, consent.recorded_by) == (Consent.Channel.IN_PERSON, desk)
    assert GuestLink.objects.filter(charge=row.charge).exists()


@pytest.mark.parametrize("role", ["secretary", "instructor", "board"])
def test_in_person_without_ac5_is_not_found(make_admin, manager, role):  # noqa: F811
    outing = an_open_outing(manager, open_to_non_members=True)
    with pytest.raises(Http404):
        guests.enrol_guest(outing, data(), by=make_admin(role), now=NOW)
    assert not Person.objects.filter(contact_email=EMAIL).exists()


def test_without_the_published_texts_no_guest_can_enrol(manager, monkeypatch):
    outing = an_open_outing(manager, open_to_non_members=True)
    monkeypatch.setattr(guests, "ADULT", "sense_cap_text_publicat")  # els textos no s'esborren
    with pytest.raises(ValidationError, match="Torna-ho a provar"):
        guests.enrol_guest(outing, data(), now=NOW)


def test_the_guest_channel_is_only_for_the_public_form(manager):
    outing = an_open_outing(manager, open_to_non_members=True)
    account = a_member()
    for actor in (account, audit.system("una-altra-peca")):
        with pytest.raises(Http404):
            enrolment.enrol(outing, account.person, channel="guest", actor=actor, now=NOW)
    assert not Charge.objects.filter(origin="activities").exists()


def test_p_457_an_ac5_accepts_a_guest_offer_and_the_guest_gets_the_link(manager):
    from apps.activities import deadlines

    outing = an_open_outing(manager, open_to_non_members=True, max_places=1)
    first = guests.enrol_guest(outing, data(), now=NOW)
    waiting = guests.enrol_guest(outing, data(contact_email="espera@example.org"), now=NOW)
    later = NOW + datetime.timedelta(hours=73)
    deadlines.run_deadlines(now=later)
    first.refresh_from_db()
    waiting.refresh_from_db()
    assert (first.status, waiting.status) == (S.EXPIRED, S.OFFERED)

    accepted = deadlines.accept_offer(waiting, actor=manager, now=later)

    assert accepted.status == S.PENDING_PAYMENT
    assert GuestLink.objects.get(charge=accepted.charge).person == waiting.person


# --- T-M02-34: «Soc major d'edat» (RN-M02-35; CA-M02-37; P-33) -----------------------------------


def adult_consent(person):
    return Consent.objects.filter(person=person, legal_text__kind=guests.ADULT)


def test_ca_m02_37_without_the_adult_box_a_guest_is_rejected(manager):
    outing = an_open_outing(manager, open_to_non_members=True)
    with pytest.raises(ValidationError, match="menors"):
        guests.enrol_guest(outing, data(adult_declared=False), now=NOW)
    assert not Enrolment.objects.exists() and not Person.objects.filter(origin="guest").exists()


def test_ca_m02_37_with_the_box_the_declaration_keeps_the_text_version_and_no_birth_date(manager):
    outing = an_open_outing(manager, open_to_non_members=True)

    row = guests.enrol_guest(outing, data(), now=NOW)

    consent = adult_consent(row.person).get()
    assert consent.legal_text == LegalText.objects.get(kind=guests.ADULT, version=1)
    assert consent.legal_text.content == guests.ADULT_PROPOSAL
    assert (consent.channel, consent.action) == (Consent.Channel.WEB, Consent.Action.GRANTED)
    assert row.person.birth_date is None


def test_in_person_the_desk_marks_the_box_after_asking(make_admin, manager):  # noqa: F811
    outing = an_open_outing(manager, open_to_non_members=True)
    desk = make_admin("treasurer")
    with pytest.raises(ValidationError, match="menors"):
        guests.enrol_guest(outing, data(adult_declared=False), by=desk, now=NOW)
    row = guests.enrol_guest(outing, data(), by=desk, now=NOW)
    consent = adult_consent(row.person).get()
    assert (consent.channel, consent.recorded_by) == (Consent.Channel.IN_PERSON, desk)


def test_with_a_minimum_age_the_birth_date_replaces_the_box(manager):
    """RN-M01-53: amb edat mínima es demana la data de naixement i no cal la casella."""
    outing = an_open_outing(manager, open_to_non_members=True, min_age=18)
    born = datetime.date(1990, 5, 1)
    row = guests.enrol_guest(outing, data(adult_declared=False, birth_date=born), now=NOW)
    assert not adult_consent(row.person).exists()


def test_a_desk_guest_gets_the_guest_link_and_no_link_that_needs_a_session(manager):
    """Revisió de la #596: inscrit al taulell (canal DESK) i sense compte, només l'enllaç segur,
    també en acceptar una plaça oferta."""
    from apps.activities import deadlines, notifications
    from apps.core.models import OutgoingEmail

    outing = an_open_outing(manager, open_to_non_members=True, max_places=1)
    first = guests.enrol_guest(outing, data(), by=manager, now=NOW)
    assert first.channel == "desk"
    assert not OutgoingEmail.objects.filter(template=notifications.PAYMENT).exists()
    waiting = guests.enrol_guest(
        outing, data(contact_email="taulell@example.org"), by=manager, now=NOW
    )
    later = NOW + datetime.timedelta(hours=73)
    deadlines.run_deadlines(now=later)
    waiting.refresh_from_db()
    accepted = deadlines.accept_offer(waiting, actor=manager, now=later)
    assert GuestLink.objects.get(charge=accepted.charge).person == waiting.person
    assert not OutgoingEmail.objects.filter(template=notifications.PAYMENT).exists()
