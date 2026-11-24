# ruff: noqa: F811 (fixtures importades com a paràmetres)
"""«El meu progrés» a l'àrea personal (T-M02-17c; HU-M02-14; RN-M02-17): el resultat i
l'observació de les pràctiques d'una inscripció seva, sense dades d'altres alumnes. Només dades
inventades."""

import html

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.activities import assessment
from apps.activities.models import PracticeAssessment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member
from .test_assessment import DAY, course  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db
R = PracticeAssessment.Result


def text(response):
    return html.unescape(response.content.decode())


def test_hu_m02_14_the_student_sees_her_practices_and_nobody_elses(login_as, course):
    assessment.assess(course.practice, course.student, result=R.NEEDS_REINFORCEMENT,
                      notes="Equilibri per treballar.", by=course.own, today=DAY)  # fmt: skip
    assessment.assess(course.practice, course.mate, result=R.ACHIEVED,
                      notes="Observació de la companya.", by=course.own, today=DAY)  # fmt: skip
    client = login_as(course.account, AREA_PERSONAL)
    url = reverse("activities:enrolment_progress", args=[course.student.pk])
    assert url in text(client.get(reverse("activities:mine")))

    page = text(client.get(url))
    assert "Necessita reforç" in page and "Equilibri per treballar." in page
    assert "Encara sense avaluar" in page  # la pràctica de mar, encara no
    assert "2 pràctiques" in page  # la teoria no hi surt
    assert "Observació de la companya." not in page


def test_someone_elses_enrolment_or_an_admin_session_is_not_found(login_as, course, make_admin):
    url = reverse("activities:enrolment_progress", args=[course.student.pk])
    assert login_as(a_member("Pau"), AREA_PERSONAL).get(url).status_code == 404
    assert login_as(make_admin("instructor"), AREA_ADMIN).get(url).status_code in (302, 401, 404)
