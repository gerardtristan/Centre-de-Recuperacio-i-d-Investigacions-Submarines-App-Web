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


def test_filters_by_kind_and_department(done):
    assert [a.pk for a in public.public_past_list({"kind": "outing"}, today=LATER)] == [done.pk]
    assert public.public_past_list({"kind": "course"}, today=LATER) == []
    other = {"department": done.department_id + 1000}
    assert public.public_past_list(other, today=LATER) == []
    same = {"department": done.department_id}
    assert [a.pk for a in public.public_past_list(same, today=LATER)] == [done.pk]


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
