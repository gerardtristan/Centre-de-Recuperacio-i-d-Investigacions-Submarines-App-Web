"""Sessions d'un curs i programa del dia d'una sortida (T-M02-03d; M02-6; P-M02-B, pas 2; addenda
de llocs: RN-M02-38 i la part de serveis de CA-M02-47). Les activitats es creen directament.
Només dades inventades.
"""

import datetime
import itertools

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.utils import timezone

from apps.accounts.models import Account
from apps.activities import catalogue, sessions
from apps.activities.models import Activity, ProgrammeBlock, Session, TrainingCatalogueEntry
from apps.core.models import AccountRole, AuditEntry, Person, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import outing_data

pytestmark = pytest.mark.django_db

T = datetime.time
REASON = "Motiu inventat de proves"
_numbers = itertools.count(1)


def at(year, month, day, hour=0, minute=0):
    return timezone.make_aware(datetime.datetime(year, month, day, hour, minute))


NINE, ELEVEN = at(2027, 6, 14, 9), at(2027, 6, 14, 11)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def a_place(manager):
    return catalogue.create_place(by=manager, name=f"Lloc inventat {next(_numbers)}")


@pytest.fixture
def pool(manager):
    return a_place(manager)


def a_person(first_name="Responsable"):
    return Person.objects.create(first_name=first_name, last_name="Prova", origin="in_person")


def a_course(manager):
    data = outing_data(None, kind="course", outing_type=None)
    entry = TrainingCatalogueEntry.objects.create(
        kind="course",
        name=f"Curs inventat {next(_numbers)}",
        default_places=8,
        price_member_cents=4500,
        price_non_member_cents=6000,
        department=data["department"],
    )
    return Activity.objects.create(catalogue_entry=entry, **data)


def an_outing(manager):
    return Activity.objects.create(**outing_data(a_place(manager)))


@pytest.fixture
def teacher(make_admin):  # noqa: F811
    return make_admin("instructor").person


def add(course, manager, **fields):
    data = {"kind": Session.Kind.POOL, "starts_at": NINE, "ends_at": ELEVEN, **fields}
    data.setdefault("place", a_place(manager))
    return sessions.add_session(course, by=manager, **data)


def entries(action):
    return AuditEntry.objects.filter(action=action)


# --- Sessions -------------------------------------------------------------------------------------


def test_a_session_has_kind_time_place_and_instructors(manager, teacher, pool):
    course = a_course(manager)
    session = add(course, manager, place=pool, is_practice=True, instructors=[teacher])
    session.refresh_from_db()
    assert session.activity == course
    assert (session.kind, session.starts_at, session.ends_at) == ("pool", NINE, ELEVEN)
    assert (session.place, session.is_practice, session.cancelled) == (pool, True, False)
    assert list(session.instructors.all()) == [teacher]
    # «Les seves sessions» d'un instructor són aquelles on fa classe (RN-43 de la 00).
    assert list(teacher.taught_sessions.all()) == [session]
    (entry,) = entries(sessions.SESSION_ADDED)
    assert entry.actor_account == manager
    assert entry.details["activity"] == course.pk
    assert entry.details["instructors"] == [teacher.pk]
    assert entry.details["place"] == pool.pk


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
    "sense lloc": {"place": None},
    "lloc que no és de la llista": {"place": "Piscina inventada"},
}


@pytest.mark.parametrize("fields", WRONG_SESSIONS.values(), ids=WRONG_SESSIONS.keys())
def test_adding_rejects_wrong_sessions(manager, fields):
    with pytest.raises(ValidationError):
        add(a_course(manager), manager, **fields)
    assert not Session.objects.exists()


@pytest.mark.parametrize("fields", WRONG_SESSIONS.values(), ids=WRONG_SESSIONS.keys())
def test_editing_rejects_the_same_wrong_sessions(manager, fields, pool):
    session = add(a_course(manager), manager, place=pool)
    with pytest.raises(ValidationError):
        sessions.update_session(session, by=manager, **fields)
    assert Session.objects.values("kind", "starts_at", "ends_at", "place").get() == {
        "kind": "pool",
        "starts_at": NINE,
        "ends_at": ELEVEN,
        "place": pool.pk,
    }


def test_editing_a_session_records_the_previous_values(manager, pool):
    session = add(a_course(manager), manager, place=pool)
    later, sea = at(2027, 6, 14, 10), a_place(manager)
    changed = sessions.update_session(session, by=manager, starts_at=later, place=sea, kind="pool")
    assert changed == ["place", "starts_at"]
    session.refresh_from_db()
    assert (session.starts_at, session.place) == (later, sea)
    logged = {e.field: (e.old_value, e.new_value) for e in entries(sessions.SESSION_UPDATED)}
    assert logged["place"] == (pool.pk, sea.pk)  # l'identificador, mai el nom
    assert set(logged) == {"place", "starts_at"}
    assert sessions.update_session(session, by=manager, place=sea) == []
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
            sessions.update_session(Session.objects.first(), by=manager, is_practice=True)
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
        lambda: sessions.update_session(session, by=manager, is_practice=True),
        lambda: sessions.set_instructors(session, [], by=manager),
        lambda: sessions.cancel_session(session, by=manager, reason=REASON),
    ):
        with pytest.raises(ValidationError):
            call()
    assert Session.objects.count() == 1


# --- Programa del dia -----------------------------------------------------------------------------

PROGRAMME = [
    {"starts_at": T(8, 0), "label": "Trobada"},
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


# --- Llocs (RN-M02-38, CA-M02-47) i permís (AC7) ------------------------------------------------


def test_a_deactivated_place_is_not_chosen_but_is_kept(manager, pool):
    session = add(a_course(manager), manager, place=pool)
    catalogue.set_active(pool, False, by=manager)
    with pytest.raises(ValidationError):
        add(a_course(manager), manager, place=pool)
    assert sessions.update_session(session, by=manager, place=pool, is_practice=True) == [
        "is_practice"
    ]
    outing = an_outing(manager)
    with pytest.raises(ValidationError):
        sessions.set_programme(outing, [{**PROGRAMME[0], "place": pool}], by=manager)


def test_a_block_with_its_own_place_or_the_one_of_the_activity(manager):
    outing, port = an_outing(manager), a_place(manager)
    sessions.set_programme(outing, [{**PROGRAMME[0], "place": port}, PROGRAMME[1]], by=manager)
    first, second = outing.programme_blocks.order_by("order")
    assert (first.shown_place, second.shown_place) == (port, outing.place)
    catalogue.set_active(port, False, by=manager)  # el que ja hi era es conserva en tornar a desar
    sessions.set_programme(outing, [{**PROGRAMME[0], "place": port}], by=manager)
    assert outing.programme_blocks.get().place == port


@pytest.mark.parametrize("role", [Role.Code.INSTRUCTOR, Role.Code.SECRETARY, Role.Code.BOARD])
def test_without_ac7_sessions_and_programme_are_not_found(make_admin, manager, role):  # noqa: F811
    other, course = make_admin(role), a_course(manager)
    session = add(course, manager)
    for call in (
        lambda: add(course, other),
        lambda: sessions.update_session(session, by=other, is_practice=True),
        lambda: sessions.set_instructors(session, [], by=other),
        lambda: sessions.cancel_session(session, by=other, reason=REASON),
        lambda: sessions.set_programme(course, PROGRAMME, by=other),
    ):
        with pytest.raises(Http404):
            call()
    assert Session.objects.count() == 1 and not ProgrammeBlock.objects.exists()
