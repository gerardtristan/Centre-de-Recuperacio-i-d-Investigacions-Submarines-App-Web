"""Full d'avaluació d'una pràctica (T-M02-17b; P-M02-F pas 1; HU-M02-12; AC10a). Només dades
inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities import permissions
from apps.activities.models import PracticeAssessment, Session
from apps.core.models import AuditEntry
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .test_attendance import manager  # noqa: F401 (fixtures)
from .test_attendance_views import roll_url, today_course  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db


def sheet_url(course, session):
    return reverse("administration:assessment_sheet", args=[course.activity.pk, session.pk])


@pytest.fixture
def practice(today_course):  # noqa: F811
    Session.objects.filter(pk=today_course.first.pk).update(is_practice=True)
    today_course.first.refresh_from_db()
    return today_course


def test_the_instructor_assesses_their_practice(login_as, practice):
    client = login_as(practice.own, AREA_ADMIN)
    roll = main_of(client.get(roll_url(practice, practice.first)).content.decode())
    assert sheet_url(practice, practice.first) in roll  # l'enllaç des de la llista
    page = main_of(client.get(sheet_url(practice, practice.first)).content.decode())
    assert "Alumna Prova" in page and "Sense avaluar" in page and "Sense dades de salut" in page
    data = {
        "inscripcio": practice.student.pk,
        "resultat": "needs_reinforcement",
        "observacio": "Cal practicar la flotabilitat.",
    }
    response = client.post(sheet_url(practice, practice.first), data, follow=True)
    assert "Avaluació desada." in response.content.decode()
    mark = PracticeAssessment.objects.get()
    assert (mark.result, mark.notes) == ("needs_reinforcement", "Cal practicar la flotabilitat.")
    response = client.post(
        sheet_url(practice, practice.first), {**data, "resultat": "x"}, follow=True
    )
    assert "Resultat desconegut." in response.content.decode()


def test_another_instructor_gets_not_found_and_it_is_logged(login_as, practice):
    client = login_as(practice.other, AREA_ADMIN)
    assert client.get(sheet_url(practice, practice.first)).status_code == 404
    assert AuditEntry.objects.filter(action=permissions.OUT_OF_SCOPE).exists()
    assert not PracticeAssessment.objects.exists()


def test_a_theory_session_is_not_assessed(login_as, today_course):  # noqa: F811
    client = login_as(today_course.own, AREA_ADMIN)
    roll = main_of(client.get(roll_url(today_course, today_course.first)).content.decode())
    assert sheet_url(today_course, today_course.first) not in roll
    page = main_of(client.get(sheet_url(today_course, today_course.first)).content.decode())
    assert "Encara no es pot avaluar" in page and "Desa l" not in page
