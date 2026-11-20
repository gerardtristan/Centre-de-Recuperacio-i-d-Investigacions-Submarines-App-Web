"""Duplicar una activitat (T-M02-07; decisió 026; RN-M02-21 i RN-M02-44; CA-M02-04, la part de
duplicar de CA-M02-47; L-M02-10). Portades de la branca aparcada, sense la pantalla (T-M02-06) ni
l'avís del preu diferent. Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.http import Http404

from apps.activities import catalogue, duplicate, extensions, services, sessions, states
from apps.activities.models import Activity, Session
from apps.core import roles
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .test_activities import (
    TODAY,
    a_course,
    a_place,
    a_project,
    an_outing,
    at,
    cleaning,
    outing_type,
)

pytestmark = pytest.mark.django_db

T = datetime.time
S = Activity.Status
REASON = "Motiu inventat de proves"
BEFORE_DEADLINE = at(2027, 6, 1, 9)
NEW_START = datetime.date(2028, 6, 13)


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def a_session(activity, manager, day, hour, *instructors, month=6, place=None):
    return sessions.add_session(
        activity,
        by=manager,
        kind=Session.Kind.SEA,
        starts_at=at(2027, month, day, hour),
        ends_at=at(2027, month, day, hour + 2),
        place=place or a_place(manager, prices=None),
        is_practice=True,
        instructors=instructors,
    )


def blocks(port):
    return [
        {"starts_at": T(8, 0), "label": "Trobada", "place": port},
        {"starts_at": T(8, 30), "ends_at": T(9, 0), "label": "Briefing"},
        {"starts_at": T(9, 30), "label": "Immersió", "responsible_label": "Cap d'immersió"},
    ]


# --- CA-M02-04 i l'exemple de RN-M02-21 -----------------------------------------------------------


def test_ca_m02_04_a_copy_364_days_later(manager, make_admin):  # noqa: F811
    teacher = make_admin(Role.Code.INSTRUCTOR).person
    original = a_course(manager, description="Descripció inventada.")
    pool = a_place(manager, prices=None)
    a_session(original, manager, 14, 9, teacher, place=pool)
    a_session(original, manager, 15, 10, place=pool)
    sessions.set_programme(original, blocks(pool), by=manager)
    states.publish(original, by=manager, now=BEFORE_DEADLINE)

    new_start = original.starts_on + datetime.timedelta(days=364)
    copy = duplicate.duplicate(original, new_start, by=manager)

    assert (copy.status, copy.duplicated_from) == (S.DRAFT, original)
    assert (copy.published_at, copy.done_at, copy.cancellation_reason) == (None, None, "")
    assert (copy.starts_on, copy.ends_on) == (new_start, new_start + datetime.timedelta(days=1))
    assert copy.registration_closes_at == at(2028, 6, 8, 20)
    for name in duplicate.COPIED_FIELDS:
        assert getattr(copy, name) == getattr(original, name), name
    copied = list(copy.sessions.order_by("starts_at"))
    assert [(s.starts_at, s.ends_at) for s in copied] == [
        (at(2028, 6, 12, 9), at(2028, 6, 12, 11)),
        (at(2028, 6, 13, 10), at(2028, 6, 13, 12)),
    ]
    assert [(s.kind, s.place, s.is_practice) for s in copied] == [("sea", pool, True)] * 2
    assert list(copied[0].instructors.all()) == [teacher]
    assert not copied[1].instructors.exists()
    fields = ("order", "starts_at", "ends_at", "label", "place", "responsible_label")
    assert list(copy.programme_blocks.values_list(*fields)) == list(
        original.programme_blocks.values_list(*fields)
    )
    original.refresh_from_db()
    assert (original.status, original.sessions.count()) == (S.OPEN, 2)


def test_rn_m02_21_the_example_of_the_plan(manager):
    original = an_outing(manager)
    a_session(original, manager, 14, 9)
    a_session(original, manager, 15, 10)
    copy = duplicate.duplicate(original, NEW_START, by=manager)
    assert [s.starts_at for s in copy.sessions.order_by("starts_at")] == [
        at(2028, 6, 13, 9),
        at(2028, 6, 14, 10),
    ]
    assert (copy.starts_on, copy.ends_on) == (NEW_START, datetime.date(2028, 6, 14))
    assert copy.registration_closes_at == at(2028, 6, 9, 20)


def test_the_clock_time_is_kept_across_a_daylight_saving_change(manager):
    winter = an_outing(
        manager,
        starts_on=datetime.date(2027, 3, 20),
        ends_on=datetime.date(2027, 3, 20),
        registration_closes_at=at(2027, 3, 18, 20),
    )
    a_session(winter, manager, 20, 9, month=3)
    copy = duplicate.duplicate(winter, datetime.date(2027, 4, 3), by=manager)  # hora d'estiu
    assert copy.sessions.get().starts_at == at(2027, 4, 3, 9)
    assert copy.registration_closes_at == at(2027, 4, 1, 20)


def test_a_copy_can_also_go_back_in_time(manager):
    original = an_outing(manager)
    copy = duplicate.duplicate(
        original, original.starts_on - datetime.timedelta(days=7), by=manager
    )
    assert (copy.starts_on, copy.registration_closes_at) == (
        datetime.date(2027, 6, 7),
        at(2027, 6, 3, 20),
    )


# --- L-M02-10 i què no es copia -------------------------------------------------------------------


@pytest.mark.parametrize("status", [S.DRAFT, S.OPEN, S.IN_PROGRESS, S.DONE, S.CLOSED, S.CANCELLED])
def test_l_m02_10_any_activity_can_be_duplicated_and_the_copy_is_clean(manager, status):
    original = an_outing(manager)
    Activity.objects.filter(pk=original.pk).update(
        status=status,
        cancellation_reason=REASON if status == S.CANCELLED else "",
        published_at=at(2027, 5, 1, 9),
        done_at=at(2027, 6, 15, 18) if status in (S.DONE, S.CLOSED) else None,
    )
    copy = duplicate.duplicate(original, NEW_START, by=manager)
    assert copy.status == S.DRAFT
    assert (copy.published_at, copy.done_at, copy.cancellation_reason) == (None, None, "")


def test_cancelled_sessions_and_former_instructors_are_not_copied(manager, make_admin):  # noqa: F811
    admin = make_admin(Role.Code.ADMINISTRATOR)
    stays, leaves = make_admin(Role.Code.INSTRUCTOR), make_admin(Role.Code.INSTRUCTOR)
    original = a_course(manager)
    a_session(original, manager, 14, 9, stays.person, leaves.person)
    gone = a_session(original, manager, 15, 9, stays.person)
    sessions.cancel_session(gone, by=manager, reason=REASON)
    Activity.objects.filter(pk=original.pk).update(status=S.DONE)
    roles.remove_role(leaves, Role.Code.INSTRUCTOR, by=admin, note="Nota inventada.")
    (session,) = duplicate.duplicate(original, NEW_START, by=manager).sessions.all()
    assert session.cancelled is False
    assert list(session.instructors.all()) == [stays.person]


def test_an_environmental_outing_keeps_its_subtype_and_project(manager):
    project = a_project()
    original = an_outing(
        manager, outing_type=outing_type("Medi ambient"), subtype=cleaning(), project=project
    )
    copy = duplicate.duplicate(original, NEW_START, by=manager)
    assert (copy.subtype, copy.project) == (cleaning(), project)


def test_what_is_deactivated_in_the_catalogue_cannot_be_chosen_for_the_copy(manager):
    course = a_course(manager)
    catalogue.set_active(course.catalogue_entry, False, by=manager)
    outing = an_outing(manager, outing_type=outing_type("Sèniors"))
    catalogue.set_active(outing.outing_type, False, by=manager)
    for original in (course, outing):
        with pytest.raises(ValidationError):
            duplicate.duplicate(original, NEW_START, by=manager)
    assert Activity.objects.count() == 2


@pytest.mark.parametrize("wrong", [None, "2028-06-13", at(2028, 6, 13, 9), 20280613])
def test_the_new_start_must_be_a_date(manager, wrong):
    with pytest.raises(ValidationError):
        duplicate.duplicate(an_outing(manager), wrong, by=manager)
    assert Activity.objects.count() == 1


# --- RN-M02-44 i CA-M02-47: preus i llocs ---------------------------------------------------------


def test_rn_m02_44_prices_and_their_standard_copy_come_from_the_activity(manager):
    place = a_place(manager, (4500, 6000))
    original = an_outing(manager, place=place, price_member_cents=4000, price_override_note=REASON)
    catalogue.change_place_price(
        place,
        by=manager,
        price_member_cents=5000,
        price_non_member_cents=7000,
        valid_from=TODAY,
        note="Puja (nota inventada).",
        today=TODAY,
    )
    copy = duplicate.duplicate(original, NEW_START, by=manager)
    assert (copy.price_member_cents, copy.standard_price_member_cents) == (4000, 4500)
    assert (copy.price_override_note, copy.material_cost_cents) == (REASON, None)


def test_ca_m02_47_a_deactivated_place_is_left_empty_and_blocks_publishing(manager):
    port, pool = a_place(manager), a_place(manager, prices=None)
    original = an_outing(manager, place=port)
    a_session(original, manager, 14, 9, place=pool)
    sessions.set_programme(original, blocks(port), by=manager)
    for place in (port, pool):
        catalogue.set_active(place, False, by=manager)

    copy = duplicate.duplicate(original, NEW_START, by=manager)
    assert copy.place is None and copy.status == S.DRAFT
    assert copy.programme_blocks.get(order=1).place is None
    assert copy.sessions.get().place == pool  # una sessió no pot quedar sense lloc (P-455)
    publish = lambda: states.publish(copy, by=manager, now=at(2028, 6, 1, 9))  # noqa: E731
    with pytest.raises(ValidationError):
        publish()  # sense lloc
    services.update_activity(copy, by=manager, place=a_place(manager))
    with pytest.raises(ValidationError):
        publish()  # la sessió encara té el lloc desactivat
    sessions.update_session(copy.sessions.get(), by=manager, place=a_place(manager, prices=None))
    assert publish().status == S.OPEN


# --- Registre, senyal i permís --------------------------------------------------------------------


def test_duplicating_is_recorded_and_other_modules_are_told(manager):
    original = an_outing(manager)
    sessions.set_programme(original, blocks(None), by=manager)
    heard = []

    def listener(sender, original, copy, by, **kwargs):
        heard.append((original.pk, copy.pk, copy.status, by))

    extensions.activity_duplicated.connect(listener)
    try:
        copy = duplicate.duplicate(original, NEW_START, by=manager)
    finally:
        extensions.activity_duplicated.disconnect(listener)
    assert heard == [(original.pk, copy.pk, S.DRAFT, manager)]
    entry = AuditEntry.objects.get(action=duplicate.ACTIVITY_DUPLICATED)
    assert (entry.actor_account, entry.target_id) == (manager, str(copy.pk))
    assert entry.details == {"original": original.pk, "days": 365, "sessions": 0, "blocks": 3}


def test_if_a_subscriber_fails_no_copy_is_left_behind(manager):
    original = an_outing(manager)

    def broken(sender, **kwargs):
        raise RuntimeError("El mòdul fals falla")

    extensions.activity_duplicated.connect(broken)
    try:
        with pytest.raises(RuntimeError):
            duplicate.duplicate(original, NEW_START, by=manager)
    finally:
        extensions.activity_duplicated.disconnect(broken)
    assert Activity.objects.count() == 1
    assert not AuditEntry.objects.filter(action=duplicate.ACTIVITY_DUPLICATED).exists()


@pytest.mark.parametrize("role", [Role.Code.INSTRUCTOR, Role.Code.SECRETARY, Role.Code.BOARD])
def test_without_ac7_nothing_is_duplicated(make_admin, manager, role):  # noqa: F811
    original = an_outing(manager)
    with pytest.raises(Http404):
        duplicate.duplicate(original, NEW_START, by=make_admin(role))
    assert Activity.objects.count() == 1
