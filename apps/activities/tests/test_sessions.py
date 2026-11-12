"""Sessions d'un curs i programa del dia d'una sortida (T-M02-03; M02-6; P-M02-B, pas 2).

Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import Account
from apps.activities import sessions
from apps.activities.models import Activity, ProgrammeBlock, Session
from apps.core.models import AccountRole, AuditEntry, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import REASON, a_course, a_person, an_outing, at

pytestmark = pytest.mark.django_db

T = datetime.time
NINE, ELEVEN = at(2027, 6, 14, 9), at(2027, 6, 14, 11)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


@pytest.fixture
def teacher(make_admin):  # noqa: F811
    return make_admin("instructor").person


def add(course, manager, **fields):
    data = {"kind": Session.Kind.POOL, "starts_at": NINE, "ends_at": ELEVEN, **fields}
    return sessions.add_session(course, by=manager, **data)


def entries(action):
    return AuditEntry.objects.filter(action=action)


# --- Sessions -------------------------------------------------------------------------------------


def test_a_session_has_kind_time_place_and_instructors(manager, teacher):
    course = a_course(manager)
    session = add(
        course, manager, location="  Piscina inventada ", is_practice=True, instructors=[teacher]
    )
    session.refresh_from_db()
    assert session.activity == course
    assert (session.kind, session.starts_at, session.ends_at) == ("pool", NINE, ELEVEN)
    assert (session.location, session.is_practice, session.cancelled) == (
        "Piscina inventada",
        True,
        False,
    )
    assert list(session.instructors.all()) == [teacher]
    # «Les seves sessions» d'un instructor són aquelles on fa classe (RN-43 de la 00).
    assert list(teacher.taught_sessions.all()) == [session]
    (entry,) = entries(sessions.SESSION_ADDED)
    assert entry.actor_account == manager
    assert entry.details["activity"] == course.pk
    assert entry.details["instructors"] == [teacher.pk]


@pytest.mark.parametrize("kind", ["theory", "pool", "sea"])
def test_the_three_kinds_of_session(manager, kind):
    assert add(a_course(manager), manager, kind=kind).kind == kind


WRONG_SESSIONS = {
    "classe desconeguda": {"kind": "boat"},
    "acaba quan comença": {"ends_at": NINE},
    "acaba abans de començar": {"ends_at": at(2027, 6, 14, 8)},
    "sense fus horari": {"starts_at": datetime.datetime(2027, 6, 14, 9)},
    "sense hora": {"starts_at": datetime.date(2027, 6, 14)},
    "sense final": {"ends_at": None},
    "lloc massa llarg": {"location": "x" * 141},
}


@pytest.mark.parametrize("fields", WRONG_SESSIONS.values(), ids=WRONG_SESSIONS.keys())
def test_adding_rejects_wrong_sessions(manager, fields):
    with pytest.raises(ValidationError):
        add(a_course(manager), manager, **fields)
    assert not Session.objects.exists()


@pytest.mark.parametrize("fields", WRONG_SESSIONS.values(), ids=WRONG_SESSIONS.keys())
def test_editing_rejects_the_same_wrong_sessions(manager, fields):
    session = add(a_course(manager), manager)
    with pytest.raises(ValidationError):
        sessions.update_session(session, by=manager, **fields)
    assert Session.objects.values("kind", "starts_at", "ends_at", "location").get() == {
        "kind": "pool",
        "starts_at": NINE,
        "ends_at": ELEVEN,
        "location": "",
    }


def test_editing_a_session_records_the_previous_values(manager):
    session = add(a_course(manager), manager)
    later = at(2027, 6, 14, 10)
    changed = sessions.update_session(
        session, by=manager, starts_at=later, location="Piscina inventada", kind="pool"
    )
    assert changed == ["location", "starts_at"]
    session.refresh_from_db()
    assert (session.starts_at, session.location) == (later, "Piscina inventada")
    logged = {e.field: (e.old_value, e.new_value) for e in entries(sessions.SESSION_UPDATED)}
    assert logged["location"] == ("", "Piscina inventada")
    assert set(logged) == {"location", "starts_at"}
    assert sessions.update_session(session, by=manager, location="Piscina inventada") == []
    with pytest.raises(ValidationError):
        sessions.update_session(session, by=manager, cancelled=True)
    with pytest.raises(ValidationError):
        sessions.update_session(session, by=manager, activity=None)


def test_sessions_can_be_added_later_until_the_activity_is_done(manager):
    course = a_course(manager)
    for status in ("open", "registration_closed", "in_progress"):
        Activity.objects.filter(pk=course.pk).update(status=status)
        add(course, manager)
    for status in ("done", "closed", "cancelled"):
        Activity.objects.filter(pk=course.pk).update(status=status, cancellation_reason=REASON)
        with pytest.raises(ValidationError):
            add(course, manager)
        with pytest.raises(ValidationError):
            sessions.update_session(Session.objects.first(), by=manager, location="Un altre lloc")
    assert Session.objects.count() == 3


# --- Instructors ----------------------------------------------------------------------------------


def test_only_people_with_the_instructor_role_teach(manager, teacher, make_admin):  # noqa: F811
    course = a_course(manager)
    not_a_teacher = a_person("Sense rol")
    secretary = make_admin("secretary").person
    for person in (not_a_teacher, secretary):
        with pytest.raises(ValidationError):
            add(course, manager, instructors=[teacher, person])
    with pytest.raises(ValidationError):
        add(course, manager, instructors=["Anna"])
    assert not Session.objects.exists()
    assert set(sessions.instructor_people()) == {teacher}


def test_a_removed_role_or_a_disabled_account_no_longer_teaches(manager, make_admin):  # noqa: F811
    removed, disabled, gone = (make_admin("instructor") for _ in range(3))
    AccountRole.objects.filter(admin_account=removed).update(removed_at=at(2027, 1, 1))
    Account.objects.filter(pk=disabled.pk).update(status=Account.Status.DISABLED)
    Person.objects.filter(pk=gone.person.pk).update(
        status=Person.Status.ANONYMISED, anonymous_ref="anonima-de-proves-1"
    )
    assert not sessions.instructor_people().exists()
    course = a_course(manager)
    for account in (removed, disabled, gone):
        with pytest.raises(ValidationError):
            add(course, manager, instructors=[account.person])


def test_changing_the_instructors_is_recorded(manager, teacher, make_admin):  # noqa: F811
    other = make_admin("instructor").person
    session = add(a_course(manager), manager, instructors=[teacher])
    assert sessions.set_instructors(session, [teacher], by=manager) is False
    assert sessions.set_instructors(session, [other, teacher], by=manager) is True
    assert set(session.instructors.all()) == {teacher, other}
    assert sessions.set_instructors(session, [], by=manager) is True
    assert not session.instructors.exists()
    first, second = entries(sessions.INSTRUCTORS_CHANGED).order_by("pk")
    assert (first.old_value, first.new_value) == ([teacher.pk], sorted([teacher.pk, other.pk]))
    assert (second.old_value, second.new_value) == (sorted([teacher.pk, other.pk]), [])
    with pytest.raises(ValidationError):
        sessions.set_instructors(session, [a_person("Sense rol")], by=manager)


# --- Cancel·lar una sessió ------------------------------------------------------------------------


def test_a_session_is_cancelled_with_a_reason_and_never_deleted(manager):
    session = add(a_course(manager), manager)
    for reason in ("", "   ", None):
        with pytest.raises(ValidationError):
            sessions.cancel_session(session, by=manager, reason=reason)
    sessions.cancel_session(session, by=manager, reason=f" {REASON} ")
    session.refresh_from_db()
    assert (session.cancelled, session.cancellation_reason) == (True, REASON)
    (entry,) = entries(sessions.SESSION_CANCELLED)
    assert (entry.actor_account, entry.reason) == (manager, REASON)
    # Una sessió cancel·lada ja no es toca.
    for call in (
        lambda: sessions.update_session(session, by=manager, location="Un altre lloc"),
        lambda: sessions.set_instructors(session, [], by=manager),
        lambda: sessions.cancel_session(session, by=manager, reason=REASON),
    ):
        with pytest.raises(ValidationError):
            call()
    assert Session.objects.count() == 1


BROKEN_SESSIONS = {
    "classe desconeguda": {"kind": "boat"},
    "acaba quan comença": {"ends_at": NINE},
    "cancel·lada sense motiu": {"cancelled": True},
}


@pytest.mark.parametrize("fields", BROKEN_SESSIONS.values(), ids=BROKEN_SESSIONS.keys())
def test_session_constraints_are_also_in_the_database(manager, fields):
    data = {"kind": "pool", "starts_at": NINE, "ends_at": ELEVEN, **fields}
    course = a_course(manager)
    with pytest.raises(IntegrityError), transaction.atomic():
        Session.objects.create(activity=course, **data)


# --- Programa del dia -----------------------------------------------------------------------------

PROGRAMME = [
    {"starts_at": T(8, 0), "label": "Trobada", "location": "Port inventat"},
    {"starts_at": T(8, 30), "ends_at": T(9, 0), "label": "Briefing"},
    {"starts_at": T(9, 30), "label": " Immersió ", "responsible_label": "Cap d'immersió"},
]


def test_the_programme_is_saved_whole_and_in_order(manager):
    outing = an_outing(manager)
    blocks = sessions.set_programme(outing, PROGRAMME, by=manager)
    assert [(b.order, b.label) for b in blocks] == [
        (1, "Trobada"),
        (2, "Briefing"),
        (3, "Immersió"),
    ]
    stored = list(outing.programme_blocks.values_list("order", "starts_at", "ends_at", "label"))
    assert stored == [
        (1, T(8, 0), None, "Trobada"),
        (2, T(8, 30), T(9, 0), "Briefing"),
        (3, T(9, 30), None, "Immersió"),
    ]
    assert outing.programme_blocks.get(order=3).responsible_label == "Cap d'immersió"
    (entry,) = entries(sessions.PROGRAMME_CHANGED)
    assert (entry.actor_account, entry.old_value, entry.new_value) == (manager, 0, 3)


def test_saving_the_same_programme_changes_nothing(manager):
    outing = an_outing(manager)
    sessions.set_programme(outing, PROGRAMME, by=manager)
    ids = set(outing.programme_blocks.values_list("pk", flat=True))
    sessions.set_programme(outing, PROGRAMME, by=manager)
    assert set(outing.programme_blocks.values_list("pk", flat=True)) == ids
    assert entries(sessions.PROGRAMME_CHANGED).count() == 1


def test_a_new_programme_replaces_the_old_one(manager):
    outing = an_outing(manager)
    sessions.set_programme(outing, PROGRAMME, by=manager)
    sessions.set_programme(outing, [PROGRAMME[2], PROGRAMME[0]], by=manager)
    assert list(outing.programme_blocks.values_list("order", "label")) == [
        (1, "Immersió"),
        (2, "Trobada"),
    ]
    sessions.set_programme(outing, [], by=manager)
    assert not ProgrammeBlock.objects.exists()
    assert [
        (e.old_value, e.new_value) for e in entries(sessions.PROGRAMME_CHANGED).order_by("pk")
    ] == [
        (0, 3),
        (3, 2),
        (2, 0),
    ]


WRONG_BLOCKS = {
    "sense dir què s'hi fa": {"starts_at": T(8, 0), "label": "  "},
    "sense hora": {"label": "Trobada"},
    "hora com a text": {"starts_at": "08:00", "label": "Trobada"},
    "acaba abans de començar": {"starts_at": T(9, 0), "ends_at": T(8, 0), "label": "Trobada"},
    "text massa llarg": {"starts_at": T(8, 0), "label": "x" * 81},
    "camp desconegut": {"starts_at": T(8, 0), "label": "Trobada", "order": 7},
    "un correu a la funció": {
        "starts_at": T(8, 0),
        "label": "Trobada",
        "responsible_label": "anna@example.org",
    },
    "un telèfon a la funció": {
        "starts_at": T(8, 0),
        "label": "Trobada",
        "responsible_label": "Anna, 600 000 000",
    },
}


@pytest.mark.parametrize("block", WRONG_BLOCKS.values(), ids=WRONG_BLOCKS.keys())
def test_a_wrong_block_rejects_the_whole_programme(manager, block):
    """Qui se n'encarrega és una funció, mai dades de contacte (M02-6)."""
    outing = an_outing(manager)
    sessions.set_programme(outing, PROGRAMME[:1], by=manager)
    with pytest.raises(ValidationError):
        sessions.set_programme(outing, [PROGRAMME[1], block], by=manager)
    assert list(outing.programme_blocks.values_list("label", flat=True)) == ["Trobada"]


def test_the_programme_is_not_changed_once_the_activity_is_done(manager):
    outing = an_outing(manager)
    Activity.objects.filter(pk=outing.pk).update(status="done")
    with pytest.raises(ValidationError):
        sessions.set_programme(outing, PROGRAMME, by=manager)


def test_two_blocks_cannot_share_the_order(manager):
    outing = an_outing(manager)
    ProgrammeBlock.objects.create(activity=outing, order=1, starts_at=T(8, 0), label="Trobada")
    with pytest.raises(IntegrityError), transaction.atomic():
        ProgrammeBlock.objects.create(activity=outing, order=1, starts_at=T(9, 0), label="Briefing")
