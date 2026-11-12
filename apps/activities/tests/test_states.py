"""Estats i transicions d'una activitat (T-M02-03; RN-M02-02 i RN-M02-20; estats de M02-5).

La taula `EXPECTED` és una transcripció de RN-M02-02 feta a mà: no surt del codi que es prova.
Només dades inventades.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.activities import sessions, states, tasks
from apps.activities.models import Activity, Session
from apps.core.models import AuditEntry
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import (
    AFTER_DEADLINE,
    BEFORE_DEADLINE,
    CLOSES,
    REASON,
    a_course,
    an_outing,
    at,
)

pytestmark = pytest.mark.django_db

S = Activity.Status
DRAFT, OPEN, REG_CLOSED = S.DRAFT, S.OPEN, S.REGISTRATION_CLOSED
IN_PROGRESS, DONE, CLOSED, CANCELLED = S.IN_PROGRESS, S.DONE, S.CLOSED, S.CANCELLED
COURSE, OUTING = "course", "outing"

# RN-M02-02. Curs: draft → open → registration_closed → in_progress → done → closed. Sortida:
# open → done i registration_closed → done, sense «en curs». Abans de `done`, sempre → cancelled.
# Cap pas enrere, tret de registration_closed → open.
EXPECTED = {
    COURSE: {
        DRAFT: {OPEN, CANCELLED},
        OPEN: {REG_CLOSED, CANCELLED},
        REG_CLOSED: {OPEN, IN_PROGRESS, CANCELLED},
        IN_PROGRESS: {DONE, CANCELLED},
        DONE: {CLOSED},
        CLOSED: set(),
        CANCELLED: set(),
    },
    OUTING: {
        DRAFT: {OPEN, CANCELLED},
        OPEN: {REG_CLOSED, DONE, CANCELLED},
        REG_CLOSED: {OPEN, DONE, CANCELLED},
        DONE: {CLOSED},
        CLOSED: set(),
        CANCELLED: set(),
    },
}
STATES = [(kind, status) for kind, table in EXPECTED.items() for status in table]
LAST_EVENING = at(2027, 6, 15, 18)  # el vespre de l'últim dia de l'activitat


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


def make(kind, manager, status=DRAFT, **fields):
    activity = (a_course if kind == COURSE else an_outing)(manager, **fields)
    return force(activity, status)


def force(activity, status):
    """Deixa l'activitat en un estat sense passar pels serveis (preparació de la prova)."""
    reason = REASON if status == CANCELLED else ""
    Activity.objects.filter(pk=activity.pk).update(status=status, cancellation_reason=reason)
    activity.refresh_from_db()
    return activity


def status_changes(activity):
    return list(
        AuditEntry.objects.filter(
            action=states.STATUS_CHANGED, target_id=str(activity.pk)
        ).order_by("pk")
    )


def stored(activity):
    return Activity.objects.get(pk=activity.pk).status


# --- La taula -------------------------------------------------------------------------------------


@pytest.mark.parametrize(("kind", "status"), STATES)
def test_rn_m02_02_allowed_targets(manager, kind, status):
    assert states.allowed_targets(make(kind, manager, status)) == EXPECTED[kind][status]


def test_an_outing_does_not_use_in_progress():
    assert all(IN_PROGRESS not in targets for targets in EXPECTED[OUTING].values())
    assert IN_PROGRESS not in EXPECTED[OUTING]


# Cada pas del responsable: (funció, estat d'arribada, estats de sortida on es pot fer).
# `mark_done` es crida el vespre de l'últim dia: un curs obert o tancat a inscripcions hi arriba
# pels passos del sistema que ja toquen (tancar inscripcions i «en curs»), mai d'un salt.
STEPS = {
    "publish": (lambda a, by: states.publish(a, by=by, now=BEFORE_DEADLINE), OPEN, {DRAFT}),
    "close_registration": (
        lambda a, by: states.close_registration(a, by=by, now=BEFORE_DEADLINE),
        REG_CLOSED,
        {OPEN},
    ),
    "reopen_registration": (
        lambda a, by: states.reopen_registration(a, by=by, now=BEFORE_DEADLINE),
        OPEN,
        {REG_CLOSED},
    ),
    "mark_done": (
        lambda a, by: states.mark_done(a, by=by, now=LAST_EVENING),
        DONE,
        {OPEN, REG_CLOSED, IN_PROGRESS},
    ),
    "cancel": (
        lambda a, by: states.cancel(a, by=by, reason=REASON),
        CANCELLED,
        {DRAFT, OPEN, REG_CLOSED, IN_PROGRESS},
    ),
}


@pytest.mark.parametrize("step", sorted(STEPS))
@pytest.mark.parametrize(("kind", "status"), STATES)
def test_rn_m02_02_every_step_from_every_state(manager, kind, status, step):
    """Cada pas del responsable des de cada estat: es fa si és a la taula; si no, es rebutja,
    l'estat no canvia i no queda res al registre."""
    call, target, sources = STEPS[step]
    activity = make(kind, manager, status)
    if status in sources:
        call(activity, manager)
        assert activity.status == stored(activity) == target
        last = status_changes(activity)[-1]
        assert last.new_value == target
        assert last.actor_account == manager
        return
    with pytest.raises(states.InvalidTransition):
        call(activity, manager)
    assert stored(activity) == status
    assert status_changes(activity) == []


def test_nothing_here_closes_an_activity_economically(manager):
    """`done → closed` només el fa el 09 amb les comprovacions de tancament (T-M02-22): aquí no
    hi ha cap funció que hi porti, ni el rellotge."""
    for kind in (COURSE, OUTING):
        activity = make(kind, manager, DONE)
        for call, _target, _sources in STEPS.values():
            with pytest.raises(ValidationError):
                call(activity, manager)
        states.advance_by_clock(now=at(2028, 1, 1))
        assert stored(activity) == DONE


# --- Publicar -------------------------------------------------------------------------------------


def test_publishing_records_who_and_when(manager):
    outing = an_outing(manager)
    states.publish(outing, by=manager, now=BEFORE_DEADLINE)
    assert outing.published_at == BEFORE_DEADLINE
    (entry,) = status_changes(outing)
    assert (entry.field, entry.old_value, entry.new_value) == ("status", DRAFT, OPEN)
    assert entry.actor_account == manager
    assert entry.target_type == "activities.activity"


def test_publishing_needs_a_deadline_that_has_not_passed(manager):
    outing = an_outing(manager)
    for now in (CLOSES, AFTER_DEADLINE):
        with pytest.raises(ValidationError):
            states.publish(outing, by=manager, now=now)
    assert stored(outing) == DRAFT
    assert outing.published_at is None


def test_publish_is_not_a_way_to_reopen(manager):
    """Reobrir té les seves condicions (data límit futura): `publish` no les pot saltar."""
    outing = make(OUTING, manager, REG_CLOSED)
    with pytest.raises(states.InvalidTransition):
        states.publish(outing, by=manager, now=AFTER_DEADLINE)
    assert stored(outing) == REG_CLOSED


# --- Tancar i reobrir inscripcions ----------------------------------------------------------------


def test_reopening_keeps_the_first_publication_date(manager):
    outing = an_outing(manager)
    states.publish(outing, by=manager, now=BEFORE_DEADLINE)
    states.close_registration(outing, by=manager, now=at(2027, 6, 2, 9))
    states.reopen_registration(outing, by=manager, now=at(2027, 6, 3, 9))
    assert outing.status == OPEN
    assert outing.published_at == BEFORE_DEADLINE
    assert [(e.old_value, e.new_value) for e in status_changes(outing)] == [
        (DRAFT, OPEN),
        (OPEN, REG_CLOSED),
        (REG_CLOSED, OPEN),
    ]


def test_reopening_needs_a_future_deadline_before_the_start(manager):
    """«Abans de l'inici»: amb la data límit passada cal donar-ne una de nova, futura i que no
    passi del dia d'inici. El canvi de data queda al registre amb el valor anterior."""
    outing = make(OUTING, manager, REG_CLOSED)
    with pytest.raises(ValidationError):
        states.reopen_registration(outing, by=manager, now=AFTER_DEADLINE)
    with pytest.raises(ValidationError):  # una data nova que ja ha passat
        states.reopen_registration(
            outing, by=manager, now=AFTER_DEADLINE, closes_at=at(2027, 6, 11, 8)
        )
    with pytest.raises(ValidationError):  # passa del dia d'inici
        states.reopen_registration(
            outing, by=manager, now=AFTER_DEADLINE, closes_at=at(2027, 6, 15, 8)
        )
    assert stored(outing) == REG_CLOSED
    assert Activity.objects.get(pk=outing.pk).registration_closes_at == CLOSES
    new_deadline = at(2027, 6, 13, 20)
    states.reopen_registration(outing, by=manager, now=AFTER_DEADLINE, closes_at=new_deadline)
    outing.refresh_from_db()
    assert (outing.status, outing.registration_closes_at) == (OPEN, new_deadline)
    change = AuditEntry.objects.get(
        action="activities.activity.updated", field="registration_closes_at"
    )
    assert change.actor_account == manager
    assert change.old_value != change.new_value


# --- Cancel·lar -----------------------------------------------------------------------------------


@pytest.mark.parametrize("reason", ["", "   ", None])
def test_cancelling_needs_a_reason(manager, reason):
    outing = make(OUTING, manager, OPEN)
    with pytest.raises(ValidationError):
        states.cancel(outing, by=manager, reason=reason)
    assert stored(outing) == OPEN


def test_cancelling_keeps_the_reason(manager):
    course = make(COURSE, manager, IN_PROGRESS)
    states.cancel(course, by=manager, reason=f"  {REASON}  ")
    course.refresh_from_db()
    assert (course.status, course.cancellation_reason) == (CANCELLED, REASON)
    (entry,) = status_changes(course)
    assert (entry.old_value, entry.new_value, entry.reason) == (IN_PROGRESS, CANCELLED, REASON)


# --- RN-M02-20: marcar com a feta -----------------------------------------------------------------


def test_rn_m02_20_an_outing_is_not_done_before_its_day(manager):
    outing = make(OUTING, manager, OPEN)  # del 14 al 15 de juny
    with pytest.raises(ValidationError) as error:
        states.mark_done(outing, by=manager, now=at(2027, 6, 14, 23, 59))
    assert not isinstance(error.value, states.InvalidTransition)
    assert stored(outing) == OPEN  # tampoc queda a mig camí: el pas del rellotge es desfà
    states.mark_done(outing, by=manager, now=at(2027, 6, 15, 0, 1))
    assert outing.status == DONE
    assert outing.done_at == at(2027, 6, 15, 0, 1)


def a_session(course, manager, day, hour=9):
    return sessions.add_session(
        course,
        by=manager,
        kind=Session.Kind.SEA,
        starts_at=at(2027, 6, day, hour),
        ends_at=at(2027, 6, day, hour + 2),
    )


def test_rn_m02_20_a_course_is_not_done_before_its_last_session(manager):
    course = a_course(manager)
    a_session(course, manager, 14)
    a_session(course, manager, 15, hour=16)
    force(course, IN_PROGRESS)
    with pytest.raises(ValidationError):
        states.mark_done(course, by=manager, now=at(2027, 6, 14, 20))
    assert stored(course) == IN_PROGRESS
    # El mateix dia de l'última sessió ja es pot (la regla parla de la data, no de l'hora).
    states.mark_done(course, by=manager, now=at(2027, 6, 15, 8))
    assert course.status == DONE


def test_rn_m02_20_a_cancelled_session_does_not_count(manager):
    course = a_course(manager)
    a_session(course, manager, 14)
    last = a_session(course, manager, 15)
    sessions.cancel_session(last, by=manager, reason=REASON)
    force(course, IN_PROGRESS)
    assert states.last_day(course) == at(2027, 6, 14).date()
    states.mark_done(course, by=manager, now=at(2027, 6, 14, 20))
    assert course.status == DONE


def test_rn_m02_20_a_course_without_sessions_uses_its_last_day(manager):
    course = make(COURSE, manager, IN_PROGRESS)
    assert states.last_day(course) == course.ends_on
    with pytest.raises(ValidationError):
        states.mark_done(course, by=manager, now=at(2027, 6, 14, 20))
    states.mark_done(course, by=manager, now=LAST_EVENING)
    assert course.status == DONE


def test_marking_done_first_takes_the_steps_of_the_clock(manager):
    """El responsable no depèn de si la cua ha passat: un curs obert amb la data límit passada i
    començat es tanca a inscripcions i es posa «en curs» (sistema) abans de marcar-lo com a fet."""
    course = make(COURSE, manager, OPEN)
    states.mark_done(course, by=manager, now=LAST_EVENING)
    changes = status_changes(course)
    assert [(e.old_value, e.new_value) for e in changes] == [
        (OPEN, REG_CLOSED),
        (REG_CLOSED, IN_PROGRESS),
        (IN_PROGRESS, DONE),
    ]
    assert [e.actor_kind for e in changes] == ["system", "system", "account"]
    assert changes[-1].actor_account == manager


def test_a_draft_is_never_done(manager):
    for kind in (COURSE, OUTING):
        draft = make(kind, manager)
        with pytest.raises(states.InvalidTransition):
            states.mark_done(draft, by=manager, now=LAST_EVENING)
        assert stored(draft) == DRAFT


# --- Passos del sistema ---------------------------------------------------------------------------


def test_the_clock_closes_registration_at_the_deadline(manager):
    outing = make(OUTING, manager, OPEN)
    assert states.advance_by_clock(now=BEFORE_DEADLINE) == []
    assert stored(outing) == OPEN
    assert states.advance_by_clock(now=CLOSES) == [(outing.pk, REG_CLOSED)]
    assert stored(outing) == REG_CLOSED
    (entry,) = status_changes(outing)
    assert (entry.actor_kind, entry.actor_origin) == ("system", states.CLOCK_ORIGIN)
    assert entry.actor_account is None
    # Es pot cridar tantes vegades com calgui.
    assert states.advance_by_clock(now=AFTER_DEADLINE) == []
    assert len(status_changes(outing)) == 1


def test_the_clock_starts_a_course_at_its_first_session(manager):
    course = a_course(manager)
    a_session(course, manager, 14, hour=9)
    force(course, REG_CLOSED)
    assert states.advance_by_clock(now=at(2027, 6, 14, 8, 59)) == []
    assert states.advance_by_clock(now=at(2027, 6, 14, 9)) == [(course.pk, IN_PROGRESS)]
    assert stored(course) == IN_PROGRESS


def test_the_clock_ignores_cancelled_sessions_and_falls_back_to_the_start_day(manager):
    course = a_course(manager)
    early = sessions.add_session(
        course,
        by=manager,
        kind=Session.Kind.THEORY,
        starts_at=at(2027, 6, 12, 19),
        ends_at=at(2027, 6, 12, 21),
    )
    sessions.cancel_session(early, by=manager, reason=REASON)
    force(course, REG_CLOSED)
    # Sense cap sessió viva, el curs comença el dia d'inici (14 de juny).
    assert states.advance_by_clock(now=at(2027, 6, 13, 23, 59)) == []
    assert states.advance_by_clock(now=at(2027, 6, 14, 0, 0)) == [(course.pk, IN_PROGRESS)]


def test_the_clock_takes_both_steps_of_a_course_that_has_started(manager):
    course = make(COURSE, manager, OPEN)
    assert states.advance_by_clock(now=at(2027, 6, 14, 12)) == [
        (course.pk, REG_CLOSED),
        (course.pk, IN_PROGRESS),
    ]


def test_the_clock_never_puts_an_outing_in_progress(manager):
    outing = make(OUTING, manager, OPEN)
    states.advance_by_clock(now=at(2027, 6, 14, 12))
    states.advance_by_clock(now=at(2027, 7, 1))
    assert stored(outing) == REG_CLOSED


@pytest.mark.parametrize("status", [DRAFT, DONE, CLOSED, CANCELLED])
def test_the_clock_leaves_the_other_states_alone(manager, status):
    for kind in (COURSE, OUTING):
        activity = make(kind, manager, status)
        assert states.advance_by_clock(now=at(2028, 1, 1)) == []
        assert stored(activity) == status


def test_the_queue_runs_the_clock_every_ten_minutes(manager):
    periodic = tasks.app.periodic_registry.periodic_tasks[("activities.advance_by_clock", "")]
    assert periodic.cron == "*/10 * * * *"
    outing = make(OUTING, manager, OPEN)
    Activity.objects.filter(pk=outing.pk).update(registration_closes_at=at(2020, 1, 1))
    tasks.advance_by_clock(timestamp=0)
    assert stored(outing) == REG_CLOSED


def test_is_editable_until_done(manager):
    for kind, status in STATES:
        activity = make(kind, manager, status)
        assert states.is_editable(activity) == (status in {DRAFT, OPEN, REG_CLOSED, IN_PROGRESS})
