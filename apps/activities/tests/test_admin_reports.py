"""Pàgines d'impressió i descàrregues dels informes operatius (T-M02-24b; AC20, AC19 i C3). El
contingut de cada informe té les seves proves a `test_reports.py`. Només dades inventades."""

import html

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities import reports
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .test_reports import world  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
REPORTS = reverse("administration:activity_reports")


def page(client, url):
    response = client.get(url)
    assert response.status_code == 200
    return html.unescape(response.content.decode())


def urls(activity):
    return (
        reverse("administration:activity_participants", args=[activity.pk]),
        reverse("administration:activity_schedule", args=[activity.pk]),
    )


def test_occupancy_page_and_csv_without_names(login_as, world):  # noqa: F811
    client = login_as(world.manager, AREA_ADMIN)
    body = page(client, REPORTS)
    assert world.course.title in body
    assert "Alumna Prova" not in body and "Espera Prova" not in body
    participants, schedule = urls(world.course)
    assert participants in body and schedule in body
    response = client.get(REPORTS, {"format": "csv"})
    assert response["Content-Type"].startswith("text/csv")
    assert "attachment" in response["Content-Disposition"]


def test_c3_each_role_sees_its_columns(login_as, world):  # noqa: F811
    participants, _schedule = urls(world.course)
    manager = page(login_as(world.manager, AREA_ADMIN), participants)
    assert "Espera Prova" in manager and "Preu (cèntims)" not in manager
    assert '<th scope="col">Preu</th>' in manager and "45,00 €" in manager  # T-DX-102 (B18)
    teacher = page(login_as(world.teacher, AREA_ADMIN), participants)
    assert "Alumna Prova" in teacher and "Espera Prova" not in teacher
    assert "alumna@example.org" not in manager + teacher


def test_the_participants_csv_is_a_post_and_is_logged_without_names(login_as, world):  # noqa: F811
    participants, _schedule = urls(world.course)
    response = login_as(world.manager, AREA_ADMIN).post(participants)
    assert response["Content-Type"].startswith("text/csv")
    assert "Alumna Prova" in response.content.decode("utf-8-sig")
    entry = AuditEntry.objects.get(action=reports.PARTICIPANTS_EXPORTED)
    assert entry.details["rows"] == 2 and "Prova" not in str(entry.details)


def test_the_schedule_page_has_no_names(login_as, world):  # noqa: F811
    _participants, schedule = urls(world.course)
    body = page(login_as(world.teacher, AREA_ADMIN), schedule)
    assert "Horari" in body and "Alumna Prova" not in body and "Espera Prova" not in body


def test_outside_the_scope_or_without_ac20_not_found(login_as, make_admin, world):  # noqa: F811
    stranger = login_as(world.stranger, AREA_ADMIN)
    for url in urls(world.course):
        assert stranger.get(url).status_code == 404
    assert stranger.post(urls(world.course)[0]).status_code == 404
    assert not AuditEntry.objects.filter(action=reports.PARTICIPANTS_EXPORTED).exists()
    secretary = login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN)
    assert secretary.get(REPORTS).status_code == 404


def test_the_activity_detail_links_the_reports(login_as, world):  # noqa: F811
    detail = reverse("administration:activity_detail", args=[world.course.pk])
    body = page(login_as(world.manager, AREA_ADMIN), detail)
    assert all(url in body for url in urls(world.course))
