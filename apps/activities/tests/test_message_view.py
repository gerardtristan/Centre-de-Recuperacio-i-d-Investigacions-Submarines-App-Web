"""Pantalla del missatge de l'organitzador als inscrits (T-M02-21c; AC15). Dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import an_open_outing
from .test_notifications_21b import enrol, member

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def test_the_organiser_writes_from_the_activity_page(login_as, manager):  # noqa: F811
    outing = an_open_outing(manager, max_places=12)
    enrol(outing, member("a@example.org"))
    client = login_as(manager, AREA_ADMIN)
    url = reverse("administration:activity_message", args=[outing.pk])
    detail = main_of(
        client.get(reverse("administration:activity_detail", args=[outing.pk])).content.decode()
    )
    assert url in detail
    page = main_of(client.get(url).content.decode())
    assert "Arribarà a 1 persona" in page and "a@example.org" not in page
    response = client.post(url, {"assumpte": "", "text": "x"})
    assert "Cal l&#x27;assumpte" in response.content.decode()
    response = client.post(url, {"assumpte": "Punt de trobada", "text": "Moll 3."}, follow=True)
    assert "Missatge a la cua per a 1 persona." in response.content.decode()
    assert OutgoingEmail.objects.get(template="missatge-activitat").to_address == "a@example.org"
    assert AuditEntry.objects.filter(action="activities.message.sent").exists()


def test_without_ac15_not_found(login_as, manager, make_admin):  # noqa: F811
    outing = an_open_outing(manager, max_places=12)
    url = reverse("administration:activity_message", args=[outing.pk])
    for role in (Role.Code.INSTRUCTOR, Role.Code.SECRETARY):
        assert login_as(make_admin(role), AREA_ADMIN).get(url).status_code == 404
