"""Sessions i programa a la fitxa d'administració (T-M02-06c2; CA-M02-47; M02-6; AC7). Els serveis
tenen les seves proves a `test_sessions.py`. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities.models import ProgrammeBlock, Session
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_place, an_open_course, an_outing

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def detail(activity):
    return reverse("administration:activity_detail", args=[activity.pk])


def session_post(place, **fields):
    data = {"sessio-kind": "pool", "sessio-starts_at": "2027-06-14T09:00",
            "sessio-ends_at": "2027-06-14T11:00", "sessio-place": place.pk if place else "",
            "sessio_nova": "1", **fields}  # fmt: skip
    return data


def test_ca_m02_47_a_session_needs_a_place_and_can_be_cancelled(login_as, manager):
    course = an_open_course(manager)
    client = login_as(manager, AREA_ADMIN)
    response = client.post(detail(course), session_post(None))
    assert response.status_code == 200 and not Session.objects.exists()
    assert client.post(detail(course), session_post(a_place(manager))).status_code == 303
    session = Session.objects.get()
    client.post(detail(course), {"cancel_sessio": session.pk, "motiu": ""})
    session.refresh_from_db()
    assert not session.cancelled
    client.post(detail(course), {"cancel_sessio": session.pk, "motiu": "Piscina tancada."})
    session.refresh_from_db()
    assert session.cancelled and session.cancellation_reason == "Piscina tancada."


def test_programme_blocks_are_added_and_removed_in_order(login_as, manager):
    outing = an_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    for start, label in (("09:00", "Briefing"), ("10:00", "Immersió")):
        data = {"bloc-starts_at": start, "bloc-label": label, "bloc_nou": "1"}
        assert client.post(detail(outing), data).status_code == 303
    assert list(ProgrammeBlock.objects.values_list("label", flat=True)) == ["Briefing", "Immersió"]
    assert client.post(detail(outing), {"treu_bloc": "1"}).status_code == 303
    assert list(ProgrammeBlock.objects.values_list("label", flat=True)) == ["Immersió"]


def test_m02_6_no_contact_details_in_who_is_in_charge(login_as, manager):
    outing = an_outing(manager)
    data = {"bloc-starts_at": "09:00", "bloc-label": "Briefing", "bloc_nou": "1",
            "bloc-responsible_label": "Anna 600 123 456"}  # fmt: skip
    response = login_as(manager, AREA_ADMIN).post(detail(outing), data)
    assert response.status_code == 200 and not ProgrammeBlock.objects.exists()


def test_without_ac7_nothing_changes(login_as, make_admin, manager):  # noqa: F811
    outing = an_outing(manager)
    client = login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN)
    data = {"bloc-starts_at": "09:00", "bloc-label": "Briefing", "bloc_nou": "1"}
    assert client.post(detail(outing), data).status_code == 404
    assert not ProgrammeBlock.objects.exists()


def test_a_block_without_label_or_out_of_range_changes_nothing(login_as, manager):
    outing = an_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    response = client.post(detail(outing), {"bloc-starts_at": "09:00", "bloc_nou": "1"})
    assert response.status_code == 200 and not ProgrammeBlock.objects.exists()
    assert client.post(detail(outing), {"treu_bloc": "3"}).status_code == 404


def test_the_instructors_are_offered_by_name(login_as, make_admin, manager):  # noqa: F811
    teacher = make_admin(Role.Code.INSTRUCTOR)
    page = login_as(manager, AREA_ADMIN).get(detail(an_open_course(manager))).content.decode()
    assert f">{teacher.person.first_name}" in page
