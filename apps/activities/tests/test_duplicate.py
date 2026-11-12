"""Duplicar una activitat (T-M02-07; decisió 026; RN-M02-21; CA-M02-04; L-M02-10).

Només dades inventades.
"""

import datetime

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.activities import catalogue, duplicate, extensions, sessions, states
from apps.activities.models import Activity, EnvironmentalSubtype, OutingType, Session
from apps.core import roles
from apps.core.models import AuditEntry, OutgoingEmail
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import (
    BEFORE_DEADLINE,
    REASON,
    TODAY,
    a_course,
    admin_with_mail,
    an_entry,
    an_outing,
    at,
    client_for,
    general,
)

pytestmark = pytest.mark.django_db

T = datetime.time
S = Activity.Status


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin("courses_manager")


def a_session(activity, manager, day, hour, *instructors, month=6, year=2027):
    return sessions.add_session(
        activity,
        by=manager,
        kind=Session.Kind.SEA,
        starts_at=at(year, month, day, hour),
        ends_at=at(year, month, day, hour + 2),
        location="Port inventat",
        is_practice=True,
        instructors=instructors,
    )


BLOCKS = [
    {"starts_at": T(8, 0), "label": "Trobada", "location": "Port inventat"},
    {"starts_at": T(8, 30), "ends_at": T(9, 0), "label": "Briefing"},
    {"starts_at": T(9, 30), "label": "Immersió", "responsible_label": "Cap d'immersió"},
]


# --- CA-M02-04 i l'exemple de RN-M02-21 -----------------------------------------------------------


def test_ca_m02_04_a_copy_364_days_later(manager, make_admin):  # noqa: F811
    """CA-M02-04: 2 sessions i 3 blocs, duplicada 364 dies després: la còpia és `draft`, té les
    mateixes sessions i blocs desplaçats 364 dies, res del que ha passat a l'original, i
    `duplicated_from` apunta a l'original."""
    teacher = make_admin("instructor").person
    original = a_course(manager, description="Descripció inventada.", location="Port inventat")
    a_session(original, manager, 14, 9, teacher)
    a_session(original, manager, 15, 10)
    sessions.set_programme(original, BLOCKS, by=manager)
    states.publish(original, by=manager, now=BEFORE_DEADLINE)

    new_start = original.starts_on + datetime.timedelta(days=364)
    copy = duplicate.duplicate(original, new_start, by=manager, today=TODAY)

    assert copy.pk != original.pk
    assert (copy.status, copy.duplicated_from) == (S.DRAFT, original)
    assert (copy.published_at, copy.done_at, copy.cancellation_reason) == (None, None, "")
    assert (copy.starts_on, copy.ends_on) == (new_start, new_start + datetime.timedelta(days=1))
    assert copy.registration_closes_at == at(2028, 6, 8, 20)  # 364 dies després del 10/06/2027
    for name in duplicate.COPIED_FIELDS:
        assert getattr(copy, name) == getattr(original, name), name
    copied = list(copy.sessions.order_by("starts_at"))
    assert [(s.starts_at, s.ends_at) for s in copied] == [
        (at(2028, 6, 12, 9), at(2028, 6, 12, 11)),
        (at(2028, 6, 13, 10), at(2028, 6, 13, 12)),
    ]
    assert [(s.kind, s.location, s.is_practice) for s in copied] == [
        ("sea", "Port inventat", True)
    ] * 2
    assert list(copied[0].instructors.all()) == [teacher]
    assert not copied[1].instructors.exists()
    fields = ("order", "starts_at", "ends_at", "label", "location", "responsible_label")
    assert list(copy.programme_blocks.values_list(*fields)) == list(
        original.programme_blocks.values_list(*fields)
    )
    assert copy.programme_blocks.count() == 3
    # L'original no canvia.
    original.refresh_from_db()
    assert (original.status, original.sessions.count()) == (S.OPEN, 2)


def test_rn_m02_21_the_example_of_the_plan(manager):
    """Original del 14 al 15 de juny amb sessions el 14 a les 9:00 i el 15 a les 10:00; data
    d'inici nova, 13 de juny de l'any següent: sessions el 13 a les 9:00 i el 14 a les 10:00, i la
    data límit d'inscripció desplaçada el mateix."""
    original = an_outing(manager)
    a_session(original, manager, 14, 9)
    a_session(original, manager, 15, 10)
    copy = duplicate.duplicate(original, datetime.date(2028, 6, 13), by=manager)
    assert [s.starts_at for s in copy.sessions.order_by("starts_at")] == [
        at(2028, 6, 13, 9),
        at(2028, 6, 14, 10),
    ]
    assert (copy.starts_on, copy.ends_on) == (
        datetime.date(2028, 6, 13),
        datetime.date(2028, 6, 14),
    )
    assert copy.registration_closes_at == at(2028, 6, 9, 20)


def test_the_clock_time_is_kept_across_a_daylight_saving_change(manager):
    """Una sessió a les 9:00 del matí continua sent a les 9:00 encara que entre l'original i la
    còpia hi hagi el canvi d'hora."""
    winter = an_outing(
        manager,
        starts_on=datetime.date(2027, 3, 20),
        ends_on=datetime.date(2027, 3, 20),
        registration_closes_at=at(2027, 3, 18, 20),
    )
    a_session(winter, manager, 20, 9, month=3)
    copy = duplicate.duplicate(
        winter, datetime.date(2027, 4, 3), by=manager
    )  # ja amb l'hora d'estiu
    assert copy.sessions.get().starts_at == at(2027, 4, 3, 9)
    assert copy.registration_closes_at == at(2027, 4, 1, 20)


def test_a_copy_can_also_go_back_in_time(manager):
    original = an_outing(manager)
    copy = duplicate.duplicate(
        original, original.starts_on - datetime.timedelta(days=7), by=manager
    )
    assert copy.starts_on == datetime.date(2027, 6, 7)
    assert copy.registration_closes_at == at(2027, 6, 3, 20)


# --- L-M02-10 i què no es copia -------------------------------------------------------------------


@pytest.mark.parametrize("status", [S.DRAFT, S.OPEN, S.IN_PROGRESS, S.DONE, S.CLOSED, S.CANCELLED])
def test_l_m02_10_any_activity_can_be_duplicated_and_the_copy_is_clean(manager, status):
    """L-M02-10: duplicar una activitat cancel·lada és permès; la còpia és `draft` i neta."""
    original = an_outing(manager)
    Activity.objects.filter(pk=original.pk).update(
        status=status,
        cancellation_reason=REASON if status == S.CANCELLED else "",
        published_at=at(2027, 5, 1, 9),
        done_at=at(2027, 6, 15, 18) if status in (S.DONE, S.CLOSED) else None,
    )
    copy = duplicate.duplicate(original, datetime.date(2028, 6, 13), by=manager)
    assert copy.status == S.DRAFT
    assert (copy.published_at, copy.done_at, copy.cancellation_reason) == (None, None, "")


def test_cancelled_sessions_and_former_instructors_are_not_copied(manager, make_admin):  # noqa: F811
    admin = make_admin("administrator")
    stays, leaves = make_admin("instructor"), make_admin("instructor")
    original = a_course(manager)
    a_session(original, manager, 14, 9, stays.person, leaves.person)
    gone = a_session(original, manager, 15, 9, stays.person)
    sessions.cancel_session(gone, by=manager, reason=REASON)
    Activity.objects.filter(pk=original.pk).update(status=S.DONE)  # ja no s'hi toca res
    roles.remove_role(leaves, "instructor", by=admin)
    copy = duplicate.duplicate(original, datetime.date(2028, 6, 13), by=manager, today=TODAY)
    (session,) = copy.sessions.all()
    assert session.cancelled is False
    assert list(session.instructors.all()) == [stays.person]


def test_an_environmental_outing_keeps_its_subtype_and_project(manager):
    project = catalogue.create_project(
        by=manager, name="Projecte inventat", objective="Objectiu.", department=general()
    )
    original = an_outing(
        manager,
        outing_type=OutingType.objects.get(name="Medi ambient"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"),
        project=project,
    )
    copy = duplicate.duplicate(original, datetime.date(2028, 6, 13), by=manager)
    assert (copy.outing_type, copy.subtype, copy.project) == (
        original.outing_type,
        original.subtype,
        project,
    )


# --- El que ja no es pot triar no es pot copiar ---------------------------------------------------


def test_what_is_deactivated_cannot_be_chosen_for_the_copy_either(manager):
    course = a_course(manager)
    catalogue.set_active(course.catalogue_entry, False, by=manager)
    outing = an_outing(manager, outing_type=OutingType.objects.get(name="Sèniors"))
    catalogue.set_active(outing.outing_type, False, by=manager)
    for original in (course, outing):
        with pytest.raises(ValidationError):
            duplicate.duplicate(original, datetime.date(2028, 6, 13), by=manager)
    assert Activity.objects.count() == 2
    catalogue.set_active(course.catalogue_entry, True, by=manager)
    assert duplicate.duplicate(course, datetime.date(2028, 6, 13), by=manager).pk


@pytest.mark.parametrize("wrong", [None, "2028-06-13", at(2028, 6, 13, 9), 20280613])
def test_the_new_start_must_be_a_date(manager, wrong):
    original = an_outing(manager)
    with pytest.raises(ValidationError):
        duplicate.duplicate(original, wrong, by=manager)
    assert Activity.objects.count() == 1


# --- Preus, registre i senyal ---------------------------------------------------------------------


def test_prices_are_copied_from_the_activity_and_a_difference_warns_the_treasurer(
    manager,
    make_admin,  # noqa: F811
):
    """RN-M02-21 copia els preus de l'activitat, no els del catàleg d'avui. Si ara són diferents,
    s'avisa el tresorer com en qualsevol activitat amb un preu diferent (RN-M02-06)."""
    admin_with_mail(make_admin, "treasurer", "tresoreria@example.org")
    entry = an_entry(manager)
    original = a_course(manager, entry)
    same = duplicate.duplicate(original, datetime.date(2028, 6, 13), by=manager, today=TODAY)
    assert (same.price_member_cents, same.price_non_member_cents) == (4500, 6000)
    assert not OutgoingEmail.objects.exists()

    catalogue.change_prices(
        entry,
        by=manager,
        price_member_cents=5000,
        price_non_member_cents=6000,
        valid_from=TODAY,
        note=REASON,
        today=TODAY,
    )
    OutgoingEmail.objects.all().delete()  # el correu del canvi de preu del catàleg no és d'aquí
    later = duplicate.duplicate(original, datetime.date(2028, 7, 13), by=manager, today=TODAY)
    assert later.price_member_cents == 4500  # el de l'original, no el del catàleg
    (email,) = OutgoingEmail.objects.all()
    assert (email.template, email.to_address) == ("avis-preu-activitat", "tresoreria@example.org")


def test_duplicating_is_recorded_and_other_modules_are_told(manager):
    original = an_outing(manager)
    sessions.set_programme(original, BLOCKS, by=manager)
    heard = []

    def listener(sender, original, copy, by, **kwargs):
        heard.append((original.pk, copy.pk, copy.status, by))

    extensions.activity_duplicated.connect(listener)
    try:
        copy = duplicate.duplicate(original, datetime.date(2028, 6, 13), by=manager)
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
            duplicate.duplicate(original, datetime.date(2028, 6, 13), by=manager)
    finally:
        extensions.activity_duplicated.disconnect(broken)
    assert Activity.objects.count() == 1
    assert not AuditEntry.objects.filter(action=duplicate.ACTIVITY_DUPLICATED).exists()


# --- La pantalla ----------------------------------------------------------------------------------


def test_duplicating_from_the_detail_leads_to_the_copy(manager):
    client = client_for(manager)
    original = an_outing(manager, title="Immersió inventada original")
    page = client.get(
        reverse("administration:activity_detail", args=[original.pk])
    ).content.decode()
    url = reverse("administration:activity_duplicate", args=[original.pk])
    assert f'href="{url}"' in page
    assert "L'original comença el 14/06/2027" in client.get(url).content.decode()
    response = client.post(url, {"new_start": ""})
    assert response.status_code == 200
    assert Activity.objects.count() == 1

    response = client.post(url, {"new_start": "2028-06-13"})
    copy = Activity.objects.exclude(pk=original.pk).get()
    assert (response.status_code, response["Location"]) == (
        303,
        reverse("administration:activity_detail", args=[copy.pk]),
    )
    detail = client.get(response["Location"]).content.decode()
    assert "Còpia creada en esborrany" in detail
    assert "Duplicada de" in detail and "Immersió inventada original" in detail
    assert "Esborrany" in detail


def test_a_cancelled_activity_still_offers_to_be_duplicated(manager):
    client = client_for(manager)
    original = an_outing(manager)
    states.cancel(original, by=manager, reason=REASON)
    page = client.get(
        reverse("administration:activity_detail", args=[original.pk])
    ).content.decode()
    assert "Duplica…" in page
    assert ">Edita<" not in page
