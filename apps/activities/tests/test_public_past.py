"""Activitats fetes i fotos publicables per a la web (T-M02-53; RP-M07-02 de l'addenda de la 106;
RN-M02-23; RN-M07-21 i 22). Prova de contracte: cap nom de persona ni cap foto privada a la
sortida. Només dades inventades."""

import dataclasses
import datetime

import pytest
from django.utils import timezone

from apps.activities import environment, environment_photos, public
from apps.activities.models import Activity, EnvironmentalPhoto
from apps.core.models import Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_person
from .test_environment import env_outing, manager  # noqa: F401 (fixture)
from .test_environment_photos import upload

pytestmark = pytest.mark.django_db

S = Activity.Status
LATER = datetime.date(2028, 1, 1)  # després de totes les activitats de prova
NAME = "Nomdepersona"


def published(activity):
    Activity.objects.filter(pk=activity.pk).update(published_at=timezone.now())
    activity.refresh_from_db()
    return activity


@pytest.fixture
def switch_on():
    Setting.objects.filter(key=environment_photos.SWITCH).update(initial_value=True)


@pytest.fixture
def done(manager):  # noqa: F811
    activity = published(env_outing(manager, responsible=a_person(NAME)))
    environment.record_results(activity, by=manager, waste_grams=1000)
    return activity


def test_only_published_activities_already_done_are_listed(manager, done):  # noqa: F811
    closed = published(env_outing(manager, status=S.CLOSED))
    ended = published(env_outing(manager, status=S.IN_PROGRESS))  # data de final passada
    env_outing(manager)  # feta però mai publicada
    published(env_outing(manager, status=S.CANCELLED))
    published(env_outing(manager, status=S.DRAFT))
    pks = {a.pk for a in public.public_past_list(today=LATER)}
    assert pks == {done.pk, closed.pk, ended.pk}
    assert ended.pk not in {a.pk for a in public.public_past_list(today=ended.ends_on)}


def test_filters_by_type_and_department(done):
    """Els filtres com els desa l'esquema de blocs del 07 (#615): `type` i `department`."""
    assert [a.pk for a in public.public_past_list({"type": "outing"}, today=LATER)] == [done.pk]
    assert public.public_past_list({"type": "course"}, today=LATER) == []
    other = {"department": done.department_id + 1000}
    assert public.public_past_list(other, today=LATER) == []
    same = {"department": done.department_id}
    assert [a.pk for a in public.public_past_list(same, today=LATER)] == [done.pk]


@pytest.mark.parametrize("department", ["abc", "", None, [1], {"x": 1}, True, 2**70])
def test_an_invalid_department_is_ignored_never_an_error(done, department):
    """La web pública mai no dona un 500 per un filtre estrany: s'ignora."""
    items = public.public_past_list({"department": department}, today=LATER)
    assert [a.pk for a in items] == [done.pk]


def test_contract_no_person_name_in_the_past_list(done):
    (item,) = public.public_past_list(today=LATER)
    assert NAME not in repr(item)
    assert "responsible" not in {f.name for f in dataclasses.fields(item)}


def test_photos_are_closed_while_the_p41_switch_is_off(manager, done):  # noqa: F811
    Setting.objects.filter(key=environment_photos.SWITCH).update(initial_value=True)
    photo = environment_photos.mark_publishable(upload(done, manager), by=manager)
    Setting.objects.filter(key=environment_photos.SWITCH).update(initial_value=False)
    assert photo.publishable and public.publishable_photos(done, today=LATER) == []


def test_contract_only_publishable_photos_and_no_names(manager, done, switch_on):  # noqa: F811
    ok = environment_photos.mark_publishable(upload(done, manager), by=manager)
    consent = environment_photos.mark_publishable(
        upload(done, manager, shows_people=True, people_consent=True), by=manager
    )
    upload(done, manager)  # no marcada
    no_consent = upload(done, manager, shows_people=True)
    EnvironmentalPhoto.objects.filter(pk=no_consent.pk).update(publishable=True)  # forçada
    retired = environment_photos.mark_publishable(upload(done, manager), by=manager)
    environment_photos.retire(retired, by=manager, reason="Motiu inventat")
    photos = public.publishable_photos(done.pk, today=LATER)
    assert {p.pk for p in photos} == {ok.pk, consent.pk}
    assert "Autora Inventada" not in repr(photos) and NAME not in repr(photos)
    assert {f.name for f in dataclasses.fields(photos[0])} == {
        "pk", "activity", "content_type", "alt_text",
    }  # fmt: skip
    assert done.title in photos[0].alt_text


def test_no_photos_of_an_activity_that_is_not_public(manager, done, switch_on):  # noqa: F811
    environment_photos.mark_publishable(upload(done, manager), by=manager)
    Activity.objects.filter(pk=done.pk).update(published_at=None)
    assert public.publishable_photos(done, today=LATER) == []
    Activity.objects.filter(pk=done.pk).update(
        published_at=timezone.now(), status=S.CANCELLED, cancellation_reason="Motiu inventat"
    )
    assert public.publishable_photos(done, today=LATER) == []


def test_p683_price_cents_is_what_a_visitor_sees(manager, done):  # noqa: F811
    Activity.objects.filter(pk=done.pk).update(
        open_to_non_members=True, price_member_cents=4500, price_non_member_cents=6000
    )
    (item,) = public.public_past_list(today=LATER)
    assert item.price_cents == 6000
    Activity.objects.filter(pk=done.pk).update(open_to_non_members=False)
    (item,) = public.public_past_list(today=LATER)
    assert item.price_cents == 4500  # només socis: el de soci, com a la fitxa


def test_p683_the_photo_is_the_first_publishable_one_or_none(manager, done, switch_on):  # noqa: F811
    (item,) = public.public_past_list(today=LATER)
    assert item.photo is None
    upload(done, manager)  # no marcada
    first = environment_photos.mark_publishable(upload(done, manager), by=manager)
    environment_photos.mark_publishable(upload(done, manager), by=manager)
    (item,) = public.public_past_list(today=LATER)
    assert item.photo.pk == first.pk and "Autora Inventada" not in repr(item)
    Setting.objects.filter(key=environment_photos.SWITCH).update(initial_value=False)
    assert public.public_past_list(today=LATER)[0].photo is None


@pytest.mark.parametrize("department", ["abc", None, [1], True, 2**70])
def test_public_list_filters_by_department_and_ignores_invalid_ones(manager, department):  # noqa: F811
    upcoming = env_outing(manager, status=S.OPEN)
    today = upcoming.starts_on
    assert [a.pk for a in public.public_list(department=department, today=today)] == [upcoming.pk]
    same = public.public_list(department=upcoming.department_id, today=today)
    assert [a.pk for a in same] == [upcoming.pk]
    assert public.public_list(department=upcoming.department_id + 1000, today=today) == []
    (item,) = same
    assert item.photo is None and item.price_cents is not None and NAME not in repr(item)
