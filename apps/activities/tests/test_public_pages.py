"""Llistat i detall públics (T-M02-08b; RN-M02-24 i 45; CA-M02-05 i 48). El servei té les seves
proves a `test_public.py`. Només dades inventades."""

import html

import pytest
from django.urls import reverse

from apps.activities import catalogue
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import an_open_course, an_open_outing, an_outing

pytestmark = pytest.mark.django_db
LIST = reverse("activities:public_list")


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def text(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return html.unescape(response.content.decode())


def detail(activity):
    return reverse("activities:public_detail", args=[activity.pk])


def test_ca_m02_05_anyone_sees_published_activities_and_filters(client, manager):
    an_open_outing(manager, title="Sortida publicada inventada")
    an_open_course(manager, title="Curs publicat inventat")
    an_outing(manager, title="Sortida en esborrany")
    page = text(client, LIST)
    assert "Sortida publicada inventada" in page and "Curs publicat inventat" in page
    assert "Sortida en esborrany" not in page
    outings = text(client, LIST + "?classe=outing")
    assert "Sortida publicada inventada" in outings and "Curs publicat inventat" not in outings


def test_ca_m02_48_the_detail_shows_the_place_name_and_never_its_notes(client, manager):
    place = catalogue.create_place(by=manager, name="Cala pública", notes="Clau a la farmaciola.")
    outing = an_open_outing(manager, place=place, price_member_cents=0, price_non_member_cents=0)
    page = text(client, detail(outing))
    assert "Cala pública" in page and "farmaciola" not in page


def test_enrol_links_follow_the_activity(client, manager):
    open_to_all = an_open_outing(manager, open_to_non_members=True)
    page = text(client, detail(open_to_all))
    assert reverse("activities:member_enrol", args=[open_to_all.pk]) in page
    assert f'href="{reverse("activities:guest_enrol", args=[open_to_all.pk])}"' in page
    members_only = an_open_outing(manager)
    page = text(client, detail(members_only))
    assert f'href="{reverse("activities:guest_enrol", args=[members_only.pk])}"' not in page


def test_a_draft_is_not_found(client, manager):
    assert client.get(detail(an_outing(manager))).status_code == 404
