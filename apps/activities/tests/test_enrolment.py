"""Inscriure's: preu, requisits i càrrec (T-M02-11; RN-M02-04, 07, 10, 11 i 30; CA-M02-06, 12, 13,
28 i 29; L-M02-02 i L-M02-06; decisió 103). Portat de la branca aparcada. Només dades inventades.
"""

import datetime

import pytest
from django.http import Http404

from apps.activities import catalogue, enrolment, extensions, states
from apps.activities.models import Activity, DiverCertification, Enrolment
from apps.core import events
from apps.core.models import AuditEntry, Charge, Event, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences.models import Licence, LicenceType, ValidityRule
from apps.members.models import Member
from apps.payments import checkout
from apps.payments.models import PaymentAttempt
from apps.payments.providers import fake
from apps.payments.tests.test_processing import notify, run_queue

from .helpers import (
    AFTER_DEADLINE,
    BEFORE_DEADLINE,
    a_member,
    a_person,
    a_personal_account,
    an_open_course,
    an_open_outing,
    an_outing,
)

pytestmark = pytest.mark.django_db

S = Enrolment.Status
ACCOUNT, DESK = Enrolment.Channel.ACCOUNT, Enrolment.Channel.DESK
NOW = BEFORE_DEADLINE


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def enrol_member(activity, account=None, *, now=NOW):
    account = account or a_member()
    return enrolment.enrol(activity, account.person, channel=ACCOUNT, actor=account, now=now)


# --- CA-M02-06: soci, activitat oberta amb places ------------------------------------------------


def test_ca_m02_06_a_member_gets_a_pending_enrolment_and_an_enrolment_charge(manager):
    outing = an_open_outing(manager, max_places=12)
    account = a_member()

    row = enrol_member(outing, account)

    assert (row.status, row.channel, row.created_by) == (S.PENDING_PAYMENT, ACCOUNT, None)
    assert (row.price_kind, row.price_cents) == (Enrolment.PriceKind.MEMBER, 4500)
    assert row.payment_due_at == NOW + datetime.timedelta(hours=outing.payment_window_hours)
    charge = row.charge
    assert (charge.kind, charge.amount_cents, charge.status, charge.origin) == (
        Charge.Kind.ENROLMENT,
        4500,
        Charge.Status.PENDING,
        "activities",
    )
    assert charge.person == account.person
    assert (charge.department, charge.cost_centre) == (outing.department, outing.cost_centre)
    assert outing.title in charge.concept
    entry = AuditEntry.objects.get(action=enrolment.CREATED)
    assert entry.actor_account == account and entry.target_id == str(row.pk)
    assert entry.details["status"] == S.PENDING_PAYMENT and entry.details["price_cents"] == 4500
    assert enrolment.occupied(outing) == 1


def test_ca_m02_06_the_charge_takes_the_cost_centre_of_the_activity(manager):
    from apps.treasury.models import CostCentre

    outing = an_open_outing(manager)
    centre = CostCentre.objects.filter(department=outing.department).first()
    assert centre is not None
    Activity.objects.filter(pk=outing.pk).update(cost_centre=centre)

    assert enrol_member(outing).charge.cost_centre == centre


def test_ca_m02_06_paying_through_the_05b_confirms_the_enrolment(manager, settings):
    """El camí sencer: el càrrec es paga a la pantalla del 05b (proveïdor fictici), la notificació
    verificada el marca pagat i l'esdeveniment `charge.paid` confirma la inscripció (T-M02-10)."""
    fake.reset()
    outing = an_open_outing(manager)
    account = a_member()
    row = enrol_member(outing, account)

    start = checkout.start_payment(row.charge, PaymentAttempt.Method.CARD, account)
    attempt = PaymentAttempt.objects.get(pk=start.attempt_id)
    notify(attempt, event_id=f"ev-{attempt.pk}")
    run_queue()
    for event in Event.objects.filter(name=events.CHARGE_PAID, payload__charge=row.charge_id):
        events.deliver(event.pk)

    row.refresh_from_db()
    assert row.charge.status == Charge.Status.PAID
    assert (row.status, row.payment_due_at) == (S.CONFIRMED, None)
    fake.reset()


def test_rn_m02_04_the_price_is_copied_and_does_not_follow_the_activity_or_the_member(manager):
    """L-M02-02: una baixa posterior no canvia el preu de soci."""
    outing = an_open_outing(manager)
    account = a_member()
    row = enrol_member(outing, account)

    Activity.objects.filter(pk=outing.pk).update(price_member_cents=9900)
    Member.objects.filter(person=account.person).update(status=Member.Status.LEFT)
    row.refresh_from_db()

    assert (row.price_kind, row.price_cents, row.charge.amount_cents) == ("member", 4500, 4500)


def test_l_m02_06_a_free_activity_confirms_without_a_charge(manager):
    outing = an_open_outing(
        manager, price_member_cents=0, price_non_member_cents=0, price_override_note="Gratuïta."
    )
    heard = []
    extensions.enrolment_confirmed.connect(
        lambda sender, enrolment, **kw: heard.append(enrolment.pk), weak=False, dispatch_uid="t"
    )
    try:
        row = enrol_member(outing)
    finally:
        extensions.enrolment_confirmed.disconnect(dispatch_uid="t")

    assert (row.status, row.charge, row.payment_due_at) == (S.CONFIRMED, None, None)
    assert heard == [row.pk]
    assert not Charge.objects.filter(origin="activities").exists()


def test_a_course_takes_enrolments_like_an_outing(manager):
    course = an_open_course(manager)
    row = enrol_member(course)
    assert row.status == S.PENDING_PAYMENT and row.charge.amount_cents == course.price_member_cents


# --- Oberta (decisió 103) ------------------------------------------------------------------------


@pytest.mark.parametrize("status", ["draft", "registration_closed", "in_progress", "done"])
def test_only_an_open_activity_takes_enrolments(manager, status):
    outing = an_outing(manager)
    Activity.objects.filter(pk=outing.pk).update(status=status)

    with pytest.raises(enrolment.ActivityNotOpen):
        enrol_member(outing)
    assert not Enrolment.objects.exists()


def test_after_the_deadline_nobody_enrols_even_if_the_clock_task_has_not_run(manager):
    outing = an_open_outing(manager)
    with pytest.raises(enrolment.ActivityNotOpen):
        enrol_member(outing, now=AFTER_DEADLINE)


def test_after_closing_by_hand_nobody_enrols(manager):
    outing = an_open_outing(manager)
    states.close_registration(outing, by=manager, now=NOW)
    with pytest.raises(enrolment.ActivityNotOpen):
        enrol_member(outing)


def test_without_free_places_the_enrolment_is_rejected_until_the_waiting_list(manager):
    outing = an_open_outing(manager, max_places=1)
    enrol_member(outing)
    with pytest.raises(enrolment.ActivityFull):
        enrol_member(outing)
    assert enrolment.occupied(outing) == 1


# --- CA-M02-13 i qui s'hi pot inscriure ----------------------------------------------------------


def test_ca_m02_13_enrolling_twice_is_rejected_but_again_after_cancelling_is_fine(manager):
    outing = an_open_outing(manager)
    account = a_member()
    first = enrol_member(outing, account)

    with pytest.raises(enrolment.AlreadyEnrolled):
        enrol_member(outing, account)

    Enrolment.objects.filter(pk=first.pk).update(status=S.CANCELLED, cancelled_reason="Inventat")
    again = enrol_member(outing, account)
    assert again.pk != first.pk and again.status == S.PENDING_PAYMENT


def test_a_non_member_is_rejected_when_the_activity_is_for_members(manager):
    outing = an_open_outing(manager, open_to_non_members=False)
    with pytest.raises(enrolment.NonMembersNotAllowed, match="fer soci"):
        enrol_member(outing, a_personal_account())
    assert not Enrolment.objects.exists()


def test_a_non_member_pays_the_non_member_price_when_the_activity_allows_it(manager):
    outing = an_open_outing(manager, open_to_non_members=True)
    row = enrol_member(outing, a_personal_account())
    assert (row.price_kind, row.price_cents, row.charge.amount_cents) == ("non_member", 6000, 6000)


@pytest.mark.parametrize("status", ["pending", "left"])
def test_a_pending_or_former_member_does_not_get_the_member_price(manager, status):
    outing = an_open_outing(manager, open_to_non_members=True)
    assert enrol_member(outing, a_member(status=status)).price_kind == "non_member"


def test_an_anonymised_person_cannot_enrol(make_admin, manager):  # noqa: F811
    outing = an_open_outing(manager, open_to_non_members=True)
    person = a_person()
    Person.objects.filter(pk=person.pk).update(status="anonymised", anonymous_ref="A-9001")
    person.refresh_from_db()
    with pytest.raises(enrolment.EnrolmentError):
        enrolment.enrol(outing, person, channel=DESK, actor=make_admin("treasurer"), now=NOW)


def test_the_account_channel_is_only_for_the_own_personal_account(manager):
    outing = an_open_outing(manager)
    mine, other = a_member(), a_member()
    for person, actor in ((other.person, mine), (manager.person, manager), (mine.person, None)):
        with pytest.raises(Http404):
            enrolment.enrol(outing, person, channel=ACCOUNT, actor=actor, now=NOW)
    assert not Enrolment.objects.exists()


@pytest.mark.parametrize(
    ("role", "allowed"),
    [
        ("courses_manager", True),
        ("treasurer", True),
        ("president", True),
        ("administrator", True),
        ("secretary", False),
        ("instructor", False),
        ("board", False),
    ],
)
def test_ac5_only_some_roles_enrol_someone_in_person(make_admin, manager, role, allowed):  # noqa: F811
    outing = an_open_outing(manager)
    member = a_member(account=False)
    by = make_admin(role)
    if allowed:
        row = enrolment.enrol(outing, member, channel=DESK, actor=by, now=NOW)
        assert (row.channel, row.created_by, row.price_kind) == (DESK, by, "member")
    else:
        with pytest.raises(Http404):
            enrolment.enrol(outing, member, channel=DESK, actor=by, now=NOW)
        assert not Enrolment.objects.exists()


def test_a_personal_account_cannot_use_the_desk_or_an_unknown_channel(manager):
    outing = an_open_outing(manager)
    account = a_member()
    with pytest.raises(Http404):
        enrolment.enrol(outing, account.person, channel=DESK, actor=account, now=NOW)
    with pytest.raises(enrolment.ValidationError):
        enrolment.enrol(outing, account.person, channel="guest", actor=account, now=NOW)


# --- Requisits: CA-M02-12, 28 i 29 ---------------------------------------------------------------


def licence(person, status):
    kind = LicenceType.objects.create(
        name="Aficionat (inventat)",
        category=LicenceType.Category.AMATEUR,
        validity_rule=ValidityRule.CALENDAR_YEAR,
    )
    Licence.objects.create(
        person=person, licence_type=kind, validity_rule=kind.validity_rule, status=status,
        origin=Licence.Origin.CLUB, starts_on=datetime.date(2027, 1, 1),
        expires_on=datetime.date(2027, 12, 31), price_kind="member", price_cents=9000,
    )  # fmt: skip


def test_ca_m02_12_without_a_valid_licence_warn_enrols_flagged_and_block_rejects(manager):
    warn = an_open_outing(manager, licence_required=True, requirements_mode="warn")
    block = an_open_outing(manager, licence_required=True, requirements_mode="block")
    account = a_member()

    row = enrol_member(warn, account)
    assert row.status == S.PENDING_PAYMENT and "Llicència vigent" in row.requirements_warning
    assert AuditEntry.objects.get(action=enrolment.CREATED).details["requirements_warning"]

    with pytest.raises(enrolment.RequirementsNotMet) as error:
        enrol_member(block, account)
    assert [check.key for check in error.value.checks] == ["licence"]
    assert not Enrolment.objects.filter(activity=block).exists()


def test_ca_m02_28_a_licence_in_progress_is_flagged_in_warn_and_rejected_in_block(manager):
    warn = an_open_outing(manager, licence_required=True, requirements_mode="warn")
    block = an_open_outing(manager, licence_required=True, requirements_mode="block")
    account = a_member()
    licence(account.person, Licence.Status.REQUESTED)

    row = enrol_member(warn, account)
    assert "En tràmit" in row.requirements_warning
    for private in ("2027-12-31", "Aficionat"):  # mai la categoria ni la caducitat
        assert private not in row.requirements_warning
    with pytest.raises(enrolment.RequirementsNotMet):
        enrol_member(block, account)


def test_with_a_valid_licence_nothing_is_flagged(manager):
    outing = an_open_outing(manager, licence_required=True, requirements_mode="block")
    account = a_member()
    licence(account.person, Licence.Status.ACTIVE)
    assert enrol_member(outing, account).requirements_warning == ""


@pytest.mark.parametrize(
    ("source", "verified", "origin"),
    [
        (DiverCertification.Source.CLUB_COURSE, False, "d'un curs del club"),
        (DiverCertification.Source.DECLARED, True, "verificada"),
    ],
)
def test_ca_m02_29_the_level_counts_and_the_origin_is_shown(manager, source, verified, origin):
    """Llegit amb RN-M02-30 (addenda de la 058, P-456): la titulació d'un curs del club compleix i
    el responsable en veu l'origen; la verificada compleix sense marca."""
    level = catalogue.create_level(by=manager, name="Nivell inventat B1", rank=10)
    outing = an_open_outing(manager, min_level=level, requirements_mode="block")
    account = a_member()
    DiverCertification.objects.create(
        person=account.person, level=level, source=source,
        verified_by=manager if verified else None, verified_at=NOW if verified else None,
    )  # fmt: skip

    row = enrol_member(outing, account)

    assert row.status == S.PENDING_PAYMENT and row.requirements_warning == ""
    (check,) = enrolment.requirements.check(outing, account.person).checks
    assert check.met and origin in check.detail


def test_an_unverified_declared_level_is_flagged_in_warn(manager):
    level = catalogue.create_level(by=manager, name="Nivell inventat B1", rank=10)
    outing = an_open_outing(manager, min_level=level, requirements_mode="warn")
    account = a_member()
    DiverCertification.objects.create(person=account.person, level=level, source="declared")

    assert "sense verificar" in enrol_member(outing, account).requirements_warning
