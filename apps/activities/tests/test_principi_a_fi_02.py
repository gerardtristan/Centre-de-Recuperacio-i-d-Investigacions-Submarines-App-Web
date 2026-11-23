"""Prova de flux sencer de la llesca F2-2 (T-M02-26; decisió 092: proveïdor fictici). El
responsable crea una sortida en un lloc amb preu estàndard i la publica; com que demana llicència,
un soci en treu una d'un dia (opció encesa a la prova), la paga, la secretaria la deixa vigent i
el soci s'inscriu sense cap avís; un convidat s'hi inscriu amb «Soc major d'edat» i rep l'avís
de requisits. Tots dos paguen pel 05b amb el proveïdor fictici, `charge.paid` confirma les
inscripcions i el dia de la sortida es passa llista. Només dades inventades."""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.activities import attendance, catalogue, enrolment, guests, services, states
from apps.activities.models import Attendance, Enrolment, OutingType
from apps.core import business_settings, events
from apps.core.models import Charge, Event, GuestLink, LegalText, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences import filing, prices
from apps.licences import services as licences
from apps.licences.models import LicenceType, ValidityRule
from apps.payments.providers import fake
from apps.payments.tests.test_principi_a_fi import pay_by_provider

from .helpers import a_member, general

R = Role.Code
S = Enrolment.Status


@pytest.fixture(autouse=True)
def fake_provider(settings):
    settings.PUBLIC_SITE_URL = "https://socis.example.org"
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def day_enabled(monkeypatch):
    real = business_settings.get
    monkeypatch.setattr(
        business_settings, "get",
        lambda key, at=None: True if key == licences.DAY_ENABLED else real(key, at),
    )  # fmt: skip


def deliver_all():
    for event in Event.objects.order_by("pk"):
        events.deliver(event.pk)


def at(day, hour):
    return timezone.make_aware(datetime.datetime.combine(day, datetime.time(hour)))


@pytest.mark.django_db
def test_f2_2_outing_enrol_member_and_guest_pay_confirm_and_roll(make_admin, day_enabled):  # noqa: F811
    today = timezone.localdate()
    day = today + datetime.timedelta(days=30)
    manager, secretary = make_admin(R.COURSES_MANAGER), make_admin(R.SECRETARY)
    for kind, content in (
        ("privacy", "Política inventada."),
        (guests.ADULT, guests.ADULT_PROPOSAL),
    ):
        LegalText.objects.get_or_create(kind=kind, version=1, defaults={"content": content})

    # 1. Un lloc amb preu estàndard i una sortida que en pren el preu, publicada.
    cove = catalogue.create_place(by=manager, name="Cala inventada")
    catalogue.change_place_price(
        cove, by=manager, price_member_cents=4500, price_non_member_cents=6000,
        valid_from=today, note="Preu inventat.", today=today,
    )  # fmt: skip
    outing = services.create_outing(
        by=manager, outing_type=OutingType.objects.get(name="Immersió"), today=today,
        title="Sortida inventada", starts_on=day, ends_on=day,
        registration_closes_at=at(day - datetime.timedelta(days=3), 20), place=cove,
        max_places=10, open_to_non_members=True, licence_required=True,
        requirements_mode="warn", responsible=manager.person,
    )  # fmt: skip
    assert (outing.price_member_cents, outing.price_non_member_cents) == (4500, 6000)
    states.publish(outing, by=manager)
    outing.refresh_from_db()

    # 2. La sortida demana llicència: el soci en treu una d'un dia, la paga i queda vigent.
    member = a_member("Marta")
    day_type = LicenceType.objects.create(
        name="Un dia (inventat)", category=LicenceType.Category.AMATEUR,
        validity_rule=ValidityRule.SINGLE_DAY,
    )  # fmt: skip
    prices.add_price(
        day_type, federation_cost_cents=1500, non_member_surcharge_cents=500,
        valid_from=today, note="Tarifa inventada", actor=make_admin(R.TREASURER),  # LC8 (T-M06-25)
    )  # fmt: skip
    licence = licences.request(member.person, day_type, day, actor=member)
    assert pay_by_provider(licence.charge, "card", member).status == "paid"
    deliver_all()
    licence.refresh_from_db()
    filing.mark_active(licence, "F-0001", actor=secretary)

    # 3. El soci s'inscriu (sense avís) i el convidat, amb «Soc major d'edat» (amb avís).
    own = enrolment.enrol(outing, member.person, channel="account", actor=member)
    guest = guests.enrol_guest(
        outing, {"first_name": "Mar", "last_name": "Convidada",
                 "contact_email": "mar@example.org", "accept_privacy": True,
                 "adult_declared": True},
    )  # fmt: skip
    assert (own.status, own.price_cents, own.requirements_warning) == (S.PENDING_PAYMENT, 4500, "")
    assert (guest.status, guest.price_cents) == (S.PENDING_PAYMENT, 6000)
    assert guest.requirements_warning  # sense llicència: avís, el mode és «avís»
    assert Person.objects.get(pk=guest.person_id).origin == Person.Origin.GUEST

    # 4. Cobrament pel 05b amb el proveïdor fictici: el soci amb el seu compte i el convidat amb
    # el seu enllaç. `charge.paid` confirma les dues inscripcions.
    assert pay_by_provider(own.charge, "card", member).status == "paid"
    link = GuestLink.objects.get(charge=guest.charge)
    assert pay_by_provider(guest.charge, "card", link).status == "paid"
    deliver_all()
    for row in (own, guest):
        row.refresh_from_db()
        assert (row.status, row.charge.status) == (S.CONFIRMED, Charge.Status.PAID)

    # 5. El dia de la sortida, la llista porta els dos confirmats i es passa.
    roll = attendance.roll(outing, viewer=manager, today=day)
    assert {row.enrolment_id for row in roll.rows} == {own.pk, guest.pk}
    assert {row.enrolment_id: row.licence_valid for row in roll.rows} == {
        own.pk: True, guest.pk: False,
    }  # fmt: skip
    attendance.mark(own, None, present=True, by=manager, today=day)
    attendance.mark(guest, None, present=False, by=manager, today=day)
    marks = Attendance.objects.filter(enrolment__activity=outing)
    assert dict(marks.values_list("enrolment", "present")) == {
        own.pk: True, guest.pk: False,
    }  # fmt: skip


def a_course(manager, instructor, today, day, places):
    from apps.activities import sessions
    from apps.activities.models import Session

    entry = catalogue.create_entry(
        by=manager, kind="course", name="Curs inventat", level="Nivell inventat",
        default_places=places, price_member_cents=12000, price_non_member_cents=15000,
        department=general(), today=today,
    )  # fmt: skip
    pool = catalogue.create_place(by=manager, name="Piscina inventada")
    course = services.create_course(
        by=manager, catalogue_entry=entry, today=today, title="Curs inventat",
        starts_on=day, ends_on=day, registration_closes_at=at(day - datetime.timedelta(days=3), 20),
        place=pool, responsible=manager.person,
    )  # fmt: skip
    practice = sessions.add_session(
        course, by=manager, kind=Session.Kind.POOL, starts_at=at(day, 9), ends_at=at(day, 11),
        place=pool, is_practice=True, instructors=[instructor.person],
    )  # fmt: skip
    states.publish(course, by=manager)
    course.refresh_from_db()
    return course, practice


def enrol_and_pay(activity, account):
    row = enrolment.enrol(activity, account.person, channel="account", actor=account)
    if row.status == S.PENDING_PAYMENT:
        assert pay_by_provider(row.charge, "card", account).status == "paid"
        deliver_all()
        row.refresh_from_db()
    return row


@pytest.mark.django_db
def test_f2_2_course_sessions_assessment_outcome_certificate_and_club_title(make_admin):  # noqa: F811
    from apps.activities import assessment, certificates, certifications
    from apps.activities.models import CertificationLevel, DiverCertification

    today = timezone.localdate()
    day = today + datetime.timedelta(days=30)
    manager, instructor = make_admin(R.COURSES_MANAGER), make_admin(R.INSTRUCTOR)
    CertificationLevel.objects.create(name="Nivell inventat", rank=10)
    course, practice = a_course(manager, instructor, today, day, places=4)

    # 1. Dos alumnes s'inscriuen i paguen pel proveïdor fictici: confirmats per `charge.paid`.
    good, other = enrol_and_pay(course, a_member("Pau")), enrol_and_pay(course, a_member("Laia"))
    assert (good.status, other.status) == (S.CONFIRMED, S.CONFIRMED)

    # 2. El dia del curs: llista i avaluació per pràctica (només qui hi fa classe).
    states.advance_by_clock(now=at(day, 8))
    practice.refresh_from_db()  # l'activitat de la sessió, amb l'estat d'ara
    for row in (good, other):
        attendance.mark(row, practice, present=True, by=instructor, today=day)
    assessment.assess(
        practice, good, result="achieved", notes="Inventat.", by=instructor, today=day
    )
    assessment.assess(
        practice, other, result="needs_reinforcement", notes="Inventat.", by=instructor, today=day
    )

    # 3. Resultat: apte i no apte (amb motiu). Només l'apte té certificat.
    certificates.record_outcome(good, result="pass", by=instructor)
    certificates.record_outcome(other, result="fail", by=instructor, reason="Motiu inventat.")
    with pytest.raises(ValidationError):
        certificates.issue(other, by=manager, today=day)
    outcome = certificates.issue(good, by=manager, today=day)
    assert outcome.certificate_number.startswith(f"C-{day.year}-")

    # 4. La titulació del club queda lligada al resultat i surt a les titulacions de l'alumne.
    title = DiverCertification.objects.get(course_outcome=outcome)
    assert (title.person_id, title.source, title.level.name) == (
        good.person_id, DiverCertification.Source.CLUB_COURSE, "Nivell inventat",
    )  # fmt: skip
    assert title in list(certifications.of(good.person))
    assert not DiverCertification.objects.filter(person=other.person).exists()


@pytest.mark.django_db
def test_f2_2_full_waitlist_cancel_refund_offer_accept_and_pay(make_admin):  # noqa: F811
    from apps.activities import cancellation, deadlines
    from apps.activities.models import RefundProposal

    today = timezone.localdate()
    day = today + datetime.timedelta(days=30)
    manager, treasurer = make_admin(R.COURSES_MANAGER), make_admin(R.TREASURER)
    course, _practice = a_course(manager, make_admin(R.INSTRUCTOR), today, day, places=1)

    # 1. Plaça plena: el primer paga i queda confirmat; el segon va a la llista d'espera.
    first, second = a_member("Primer"), a_member("Segon")
    paid = enrol_and_pay(course, first)
    waiting = enrolment.enrol(course, second.person, channel="account", actor=second)
    assert (paid.status, waiting.status, waiting.waitlist_position) == (
        S.CONFIRMED, S.WAITLISTED, 1,
    )  # fmt: skip

    # 2. El confirmat cancel·la: proposta de devolució de l'import pagat, i la plaça s'ofereix.
    proposal = cancellation.cancel_enrolment(paid, by=first, reason="No hi puc anar (inventat).")
    assert (proposal.amount_cents, proposal.status) == (12000, RefundProposal.Status.PROPOSED)
    waiting.refresh_from_db()
    assert (waiting.status, waiting.waitlist_position) == (S.OFFERED, None)

    # 3. El tresorer fa la devolució pel 05b amb el proveïdor fictici.
    done = cancellation.decide_refund(proposal, approve=True, note="Devolució inventada.",
                                      by=treasurer)  # fmt: skip
    assert done.status == RefundProposal.Status.DONE and done.refund is not None

    # 4. El següent accepta la plaça, la paga pel proveïdor fictici i queda confirmat.
    accepted = deadlines.accept_offer(waiting, actor=second)
    assert accepted.status == S.PENDING_PAYMENT
    assert pay_by_provider(accepted.charge, "card", second).status == "paid"
    deliver_all()
    accepted.refresh_from_db()
    assert (accepted.status, accepted.charge.status) == (S.CONFIRMED, Charge.Status.PAID)
    assert enrolment.occupied(course) == 1
