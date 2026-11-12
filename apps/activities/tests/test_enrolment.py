"""Inscripcions, places i llista d'espera (T-M02-10, T-M02-11 i T-M02-12; RN-M02-03, 04, 07, 10 i
11; CA-M02-06, 07, 08, 10, 12, 13 i 40; L-M02-02 i L-M02-06; decisió 088).

Només dades inventades. El pagament es confirma amb el servei real de la 00 (`charges.mark_paid`);
el que encara no existeix és qui avisa el 02 (l'esdeveniment `charge.paid`, T-M05b-21): aquí es
crida `on_charge_paid` directament, que és el contracte, no la integració.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.accounts.models import Account, TotpDevice
from apps.activities import charges as activity_charges
from apps.activities import enrolment, extensions, states
from apps.activities.models import Activity, Enrolment
from apps.core import charges
from apps.core.crypto import encrypt
from apps.core.models import AccountRole, AuditEntry, Charge, Department, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.models import LicenceRecord, Member
from conftest import CommittedDataTestCase, run_together

from .helpers import (
    AFTER_DEADLINE,
    BEFORE_DEADLINE,
    PUBLISHED,
    a_member,
    a_person,
    a_personal_account,
    an_open_course,
    an_open_outing,
    an_outing,
    pay,
)

pytestmark = pytest.mark.django_db

S = Enrolment.Status
ACCOUNT, DESK = Enrolment.Channel.ACCOUNT, Enrolment.Channel.DESK
NOW = BEFORE_DEADLINE
OTHERS = [S.CONFIRMED, S.OFFERED, S.WAITLISTED, S.CANCELLED, S.EXPIRED]


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


def enrol_member(activity, account=None, *, now=NOW):
    account = account or a_member()
    return enrolment.enrol(activity, account.person, channel=ACCOUNT, actor=account, now=now)


def fill(activity, n, *, now=NOW):
    return [enrol_member(activity, now=now) for _ in range(n)]


# --- CA-M02-06: soci, activitat oberta amb places ------------------------------------------------


def test_ca_m02_06_a_member_gets_a_pending_enrolment_and_an_enrolment_charge(manager):
    outing = an_open_outing(manager, max_places=12)
    account = a_member()

    row = enrol_member(outing, account)

    assert row.status == S.PENDING_PAYMENT
    assert (row.price_kind, row.price_cents) == (Enrolment.PriceKind.MEMBER, 4500)
    assert row.channel == ACCOUNT and row.created_by is None
    assert row.payment_due_at == NOW + datetime.timedelta(hours=outing.payment_window_hours)
    charge = row.charge
    assert (charge.kind, charge.amount_cents, charge.status) == (
        Charge.Kind.ENROLMENT,
        4500,
        Charge.Status.PENDING,
    )
    assert charge.person == account.person
    assert charge.activity == outing
    assert charge.department == outing.department
    assert charge.origin == "activities"
    assert outing.title in charge.concept
    entry = AuditEntry.objects.get(action=enrolment.CREATED)
    assert entry.actor_account == account and entry.target_id == str(row.pk)
    assert entry.details["status"] == S.PENDING_PAYMENT and entry.details["price_cents"] == 4500
    assert enrolment.occupied(outing) == 1 and enrolment.free_places(outing) == 11


def test_the_price_is_copied_and_does_not_follow_the_catalogue_or_the_member(manager):
    """RN-M02-04 i L-M02-02: el preu queda a la inscripció; una baixa posterior no el canvia."""
    outing = an_open_outing(manager)
    account = a_member()
    row = enrol_member(outing, account)

    Activity.objects.filter(pk=outing.pk).update(price_member_cents=9900)
    Member.objects.filter(person=account.person).update(status=Member.Status.LEFT)
    row.refresh_from_db()

    assert (row.price_kind, row.price_cents) == (Enrolment.PriceKind.MEMBER, 4500)
    assert row.charge.amount_cents == 4500


def test_a_fee_charge_cannot_belong_to_an_activity(manager):
    outing = an_open_outing(manager)
    with pytest.raises(ValidationError, match="quota"):
        charges.create_charge(
            a_person(),
            kind=Charge.Kind.FEE,
            amount_cents=1000,
            concept="Quota inventada",
            origin="members",
            by=manager,
            activity=outing,
        )


# --- CA-M02-07: el càrrec es paga ----------------------------------------------------------------


def test_ca_m02_07_a_paid_charge_confirms_the_enrolment_once(manager):
    outing = an_open_outing(manager)
    row = enrol_member(outing)
    heard = []
    receiver = lambda sender, enrolment, **kw: heard.append(enrolment.pk)  # noqa: E731
    extensions.enrolment_confirmed.connect(receiver)
    try:
        pay(row.charge)
        event = {"charge_id": row.charge_id, "origin": "activities", "kind": "enrolment"}
        first = activity_charges.on_charge_paid(event)
        again = activity_charges.on_charge_paid(event)  # el mateix esdeveniment, repetit
    finally:
        extensions.enrolment_confirmed.disconnect(receiver)

    row.refresh_from_db()
    assert first == row and again is None
    assert row.status == S.CONFIRMED and row.payment_due_at is None
    assert heard == [row.pk]
    change = AuditEntry.objects.get(action=enrolment.STATUS_CHANGED, target_id=str(row.pk))
    assert "pending_payment" in change.old_value and "confirmed" in change.new_value
    assert change.actor_kind == "system"


def test_the_subscriber_does_not_trust_the_event(manager):
    """Si el càrrec no és pagat de debò, no confirma. I els càrrecs d'altres mòduls no són seus."""
    outing = an_open_outing(manager)
    row = enrol_member(outing)

    assert activity_charges.on_charge_paid({"charge_id": row.charge_id}) is None
    assert (
        activity_charges.on_charge_paid({"charge_id": row.charge_id, "origin": "members"}) is None
    )
    assert activity_charges.on_charge_paid({"charge_id": 987654, "origin": "activities"}) is None

    row.refresh_from_db()
    assert row.status == S.PENDING_PAYMENT


def test_l_m02_01_a_payment_after_expiry_does_not_confirm_and_is_logged_once(manager):
    outing = an_open_outing(manager)
    row = enrol_member(outing)
    Enrolment.objects.filter(pk=row.pk).update(status=S.EXPIRED)
    pay(row.charge)

    for _ in range(2):
        assert activity_charges.on_charge_paid({"charge_id": row.charge_id}) is None

    row.refresh_from_db()
    assert row.status == S.EXPIRED
    assert AuditEntry.objects.filter(action=activity_charges.PAID_NOT_CONFIRMED).count() == 1


# --- Places i llista d'espera (RN-M02-07; CA-M02-40; decisió 088) --------------------------------


def test_ca_m02_40_a_full_activity_stays_open_and_the_next_one_waits(manager):
    outing = an_open_outing(manager, max_places=2)
    fill(outing, 2)

    third, fourth = fill(outing, 2)

    outing.refresh_from_db()
    assert outing.status == Activity.Status.OPEN  # omplir les places no tanca res (088)
    assert enrolment.is_open(outing, NOW)
    assert enrolment.free_places(outing) == 0
    assert (third.status, third.waitlist_position) == (S.WAITLISTED, 1)
    assert (fourth.status, fourth.waitlist_position) == (S.WAITLISTED, 2)
    assert third.charge is None and third.payment_due_at is None
    assert list(enrolment.waitlist(outing)) == [third, fourth]


def test_ca_m02_40_after_the_deadline_nobody_enrols_not_even_to_wait(manager):
    """El sistema tanca per la data límit: es mira l'hora, encara que la cua no hagi passat."""
    outing = an_open_outing(manager, max_places=1)
    fill(outing, 1)

    with pytest.raises(enrolment.ActivityNotOpen):
        enrol_member(outing, now=AFTER_DEADLINE)

    assert Enrolment.objects.filter(activity=outing).count() == 1


def test_ca_m02_40_after_closing_by_hand_nobody_enrols(manager):
    outing = an_open_outing(manager, max_places=5)
    states.close_registration(outing, by=manager, now=NOW)

    with pytest.raises(enrolment.ActivityNotOpen):
        enrol_member(outing)


@pytest.mark.parametrize("status", ["draft", "in_progress", "done", "cancelled"])
def test_only_an_open_activity_takes_enrolments(manager, status):
    outing = an_outing(manager)
    extra = {"cancellation_reason": "Motiu inventat"} if status == "cancelled" else {}
    Activity.objects.filter(pk=outing.pk).update(status=status, **extra)

    with pytest.raises(enrolment.ActivityNotOpen):
        enrol_member(outing)


def test_rn_m02_07_occupied_places_are_pending_confirmed_and_offered(manager):
    outing = an_open_outing(manager, max_places=10)
    rows = fill(outing, 6)
    for row, status in zip(rows[1:], OTHERS, strict=True):
        extra = {"cancelled_reason": "Motiu inventat"} if status == S.CANCELLED else {}
        position = {"waitlist_position": 1} if status == S.WAITLISTED else {}
        Enrolment.objects.filter(pk=row.pk).update(status=status, **extra, **position)

    assert enrolment.occupied(outing) == 3
    assert enrolment.free_places(outing) == 7


def test_whoever_arrives_queues_behind_the_waiting_list_even_with_a_free_place(manager):
    """La plaça que s'allibera és per al primer de la llista (RN-M02-09), no per a qui arriba."""
    outing = an_open_outing(manager, max_places=1)
    first, waiting = fill(outing, 2)
    Enrolment.objects.filter(pk=first.pk).update(status=S.EXPIRED)
    assert enrolment.free_places(outing) == 1

    late = enrol_member(outing)

    assert (late.status, late.waitlist_position) == (S.WAITLISTED, 2)
    waiting.refresh_from_db()
    assert waiting.waitlist_position == 1


def test_l_m02_06_a_free_activity_confirms_without_a_charge(manager):
    outing = an_open_outing(manager, max_places=1, price_member_cents=0, price_non_member_cents=0)
    heard = []
    receiver = lambda sender, enrolment, **kw: heard.append(enrolment.pk)  # noqa: E731
    extensions.enrolment_confirmed.connect(receiver)
    try:
        row = enrol_member(outing)
        second = enrol_member(outing)
    finally:
        extensions.enrolment_confirmed.disconnect(receiver)

    assert row.status == S.CONFIRMED and row.charge is None and row.payment_due_at is None
    assert heard == [row.pk]
    assert not Charge.objects.filter(origin="activities").exists()
    # La llista d'espera funciona igual.
    assert (second.status, second.waitlist_position) == (S.WAITLISTED, 1)


# --- Qui s'hi pot inscriure ----------------------------------------------------------------------


def test_ca_m02_13_enrolling_twice_is_rejected_but_a_new_one_after_cancelling_is_fine(manager):
    outing = an_open_outing(manager)
    account = a_member()
    first = enrol_member(outing, account)

    with pytest.raises(enrolment.AlreadyEnrolled):
        enrol_member(outing, account)

    Enrolment.objects.filter(pk=first.pk).update(
        status=S.CANCELLED, cancelled_reason="Motiu inventat"
    )
    again = enrol_member(outing, account)
    assert again.pk != first.pk and again.status == S.PENDING_PAYMENT


def test_ca_m02_10_a_non_member_is_rejected_when_the_activity_is_for_members(manager):
    outing = an_open_outing(manager, open_to_non_members=False)
    account = a_personal_account()

    with pytest.raises(enrolment.NonMembersNotAllowed, match="fer soci"):
        enrol_member(outing, account)
    with pytest.raises(enrolment.NonMembersNotAllowed):
        enrolment.quote(outing, account.person)

    assert not Enrolment.objects.exists()


def test_a_non_member_pays_the_non_member_price_when_the_activity_allows_it(manager):
    outing = an_open_outing(manager, open_to_non_members=True)
    account = a_personal_account()

    row = enrol_member(outing, account)

    assert (row.price_kind, row.price_cents) == (Enrolment.PriceKind.NON_MEMBER, 6000)
    assert row.charge.amount_cents == 6000
    assert enrolment.quote(outing, account.person).price_cents == 6000


@pytest.mark.parametrize("status", ["pending", "left"])
def test_a_pending_or_former_member_is_not_a_member_for_the_price(manager, status):
    outing = an_open_outing(manager, open_to_non_members=True)
    account = a_member(status=status)

    assert enrol_member(outing, account).price_kind == Enrolment.PriceKind.NON_MEMBER


def test_ca_m02_12_without_a_valid_licence_warn_enrols_with_a_note_and_block_rejects(manager):
    warn = an_open_outing(manager, licence_required=True, requirements_mode="warn")
    block = an_open_outing(manager, licence_required=True, requirements_mode="block")
    account = a_member()

    row = enrol_member(warn, account)
    assert row.status == S.PENDING_PAYMENT
    assert "licència" in row.requirements_warning.lower()

    with pytest.raises(enrolment.RequirementsNotMet) as error:
        enrol_member(block, account)
    assert [check.key for check in error.value.checks] == ["licence"]
    assert not Enrolment.objects.filter(activity=block).exists()


def test_with_a_valid_licence_nothing_is_flagged(manager):
    outing = an_open_outing(manager, licence_required=True, requirements_mode="block")
    account = a_member()
    member = Member.objects.get(person=account.person)
    LicenceRecord.objects.create(
        member=member,
        licence_type="Federativa inventada",
        issued_on=datetime.date(2027, 1, 1),
        expires_on=datetime.date(2027, 12, 31),
        source=LicenceRecord.Source.values[0],
    )

    row = enrol_member(outing, account)

    assert row.status == S.PENDING_PAYMENT and row.requirements_warning == ""


def test_an_anonymised_person_cannot_enrol(manager):
    outing = an_open_outing(manager, open_to_non_members=True)
    person = a_person()
    Person.objects.filter(pk=person.pk).update(status="anonymised", anonymous_ref="anon-prova-1")
    person.refresh_from_db()

    with pytest.raises(enrolment.EnrolmentError):
        enrolment.enrol(outing, person, channel=DESK, actor=manager, now=NOW)


# --- Qui pot fer la inscripció (AC2 propi, AC5 presencial) ---------------------------------------


def test_the_account_channel_is_only_for_the_own_personal_account(manager):
    outing = an_open_outing(manager)
    mine, other = a_member(), a_member()

    with pytest.raises(Http404):
        enrolment.enrol(outing, other.person, channel=ACCOUNT, actor=mine, now=NOW)
    with pytest.raises(Http404):  # un compte d'administrador no s'inscriu pel canal del soci
        enrolment.enrol(outing, manager.person, channel=ACCOUNT, actor=manager, now=NOW)
    with pytest.raises(Http404):
        enrolment.enrol(outing, mine.person, channel=ACCOUNT, actor=None, now=NOW)

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
        ("equipment_manager", False),
    ],
)
def test_ac5_only_some_roles_enrol_someone_else_in_person(make_admin, manager, role, allowed):  # noqa: F811
    outing = an_open_outing(manager)
    member = a_member(account=False)
    by = make_admin(role)

    if allowed:
        row = enrolment.enrol(outing, member, channel=DESK, actor=by, now=NOW)
        assert row.channel == DESK and row.created_by == by
        assert row.price_kind == Enrolment.PriceKind.MEMBER
    else:
        with pytest.raises(Http404):
            enrolment.enrol(outing, member, channel=DESK, actor=by, now=NOW)
        assert not Enrolment.objects.exists()


def test_a_personal_account_cannot_use_the_desk_channel(manager):
    outing = an_open_outing(manager)
    account = a_member()
    with pytest.raises(Http404):
        enrolment.enrol(outing, account.person, channel=DESK, actor=account, now=NOW)


# --- Restriccions de la base de dades i transicions ----------------------------------------------


def test_the_database_keeps_one_live_enrolment_per_person(manager):
    outing = an_open_outing(manager)
    row = enrol_member(outing)
    with pytest.raises(IntegrityError), transaction.atomic():
        Enrolment.objects.create(
            activity=outing,
            person=row.person,
            status=S.WAITLISTED,
            waitlist_position=1,
            channel=ACCOUNT,
            price_kind="member",
            price_cents=4500,
            created_at=NOW,
        )
    with pytest.raises(IntegrityError), transaction.atomic():
        Enrolment.objects.filter(pk=row.pk).update(waitlist_position=3)  # només si espera
    with pytest.raises(IntegrityError), transaction.atomic():
        Enrolment.objects.filter(pk=row.pk).update(status=S.CANCELLED)  # sense motiu


def test_rn_m02_03_only_the_listed_transitions_exist(manager):
    allowed = {
        ("pending_payment", "confirmed"),
        ("pending_payment", "expired"),
        ("pending_payment", "cancelled"),
        ("waitlisted", "offered"),
        ("waitlisted", "cancelled"),
        ("waitlisted", "expired"),
        ("offered", "pending_payment"),
        ("offered", "confirmed"),  # només una activitat gratuïta (L-M02-06)
        ("offered", "expired"),
        ("confirmed", "cancelled"),
    }
    assert {(str(a), str(b)) for a, b in enrolment.TRANSITIONS} == allowed

    row = enrol_member(an_open_outing(manager))
    Enrolment.objects.filter(pk=row.pk).update(status=S.CONFIRMED)
    row.refresh_from_db()
    with pytest.raises(ValidationError):  # una confirmada no torna a pendent de pagament
        enrolment.change_status(row, S.PENDING_PAYMENT, actor=manager)


def test_a_course_takes_enrolments_like_an_outing(manager):
    course = an_open_course(manager)
    row = enrol_member(course)
    assert row.status == S.PENDING_PAYMENT and row.charge.activity == course


# --- CA-M02-08: concurrència ---------------------------------------------------------------------


def _committed_manager():
    person = Person.objects.create(first_name="Responsable", last_name="Prova", origin="in_person")
    account = Account.objects.create_admin(person, f"resp-concurrencia-{person.pk}")
    TotpDevice.objects.create(
        account=account,
        secret_encrypted=encrypt(
            "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"
        ),  # gitleaks:allow (TOTP inventat)
        confirmed_at=PUBLISHED,
    )
    AccountRole.objects.create(admin_account=account, role=Role.objects.get(code="courses_manager"))
    return account


class TestConcurrentEnrolments(CommittedDataTestCase):
    def test_ca_m02_08_two_people_and_one_place_left(self):
        assert Department.objects.filter(name=Department.GENERAL).exists()
        manager = _committed_manager()
        outing = an_open_outing(manager, max_places=1)
        first, second = a_member("Primera"), a_member("Segona")

        rows = run_together(
            [
                lambda: (
                    enrolment.enrol(
                        outing, first.person, channel=ACCOUNT, actor=first, now=NOW
                    ).status
                ),
                lambda: (
                    enrolment.enrol(
                        outing, second.person, channel=ACCOUNT, actor=second, now=NOW
                    ).status
                ),
            ]
        )

        assert sorted(rows) == [S.PENDING_PAYMENT, S.WAITLISTED]
        assert enrolment.occupied(outing) == 1
        assert Charge.objects.filter(activity=outing).count() == 1
        assert enrolment.waitlist(outing).get().waitlist_position == 1

    def test_ten_people_and_three_places(self):
        manager = _committed_manager()
        outing = an_open_outing(manager, max_places=3)
        people = [a_member(f"Persona{n}") for n in range(10)]

        def job(account):
            return lambda: (
                enrolment.enrol(
                    outing, account.person, channel=ACCOUNT, actor=account, now=NOW
                ).status
            )

        rows = run_together([job(account) for account in people])

        assert rows.count(S.PENDING_PAYMENT) == 3 and rows.count(S.WAITLISTED) == 7
        positions = list(enrolment.waitlist(outing).values_list("waitlist_position", flat=True))
        assert positions == [1, 2, 3, 4, 5, 6, 7]
