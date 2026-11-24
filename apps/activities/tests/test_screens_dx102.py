"""T-DX-102 (revisió de DISSENY de la #531 i la #535): l'estat de l'activitat surt amb l'etiqueta
d'estat als informes, els botons que es repeteixen a cada targeta (emetre un certificat, confirmar
un reforç) no són el botó principal de la pantalla (D19) i el número del certificat va en
monoespai (D7). Només dades inventades."""

import html
import re

import pytest
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.activities import certificates
from apps.activities.models import CertificationLevel, CourseOutcome
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .test_attendance import manager  # noqa: F401 (fixtures)
from .test_attendance_views import today_course  # noqa: F401 (fixtures)
from .test_certificates import course  # noqa: F401 (fixture)
from .test_reports import world  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db


def test_the_occupancy_report_shows_the_status_label(login_as, world):  # noqa: F811
    client = login_as(world.manager, AREA_ADMIN)
    body = main_of(client.get(reverse("administration:activity_reports")).content.decode())
    cell = re.search(r'<td data-etiqueta="Estat">(.*?)</td>', body, re.S).group(1)
    assert 'class="estat estat-' in cell


def test_issuing_a_certificate_is_not_the_main_button(login_as, today_course, manager):  # noqa: F811
    CertificationLevel.objects.create(name="Nivell inventat", rank=99)
    url = reverse("administration:course_outcomes", args=[today_course.activity.pk])
    data = {"inscripcio": today_course.student.pk, "resultat": "pass", "motiu": ""}
    login_as(today_course.own, AREA_ADMIN).post(url, data)
    page = main_of(login_as(manager, AREA_ADMIN).get(url).content.decode())
    assert "Emet el certificat" in page and "boto-principal" not in page


def test_the_certificate_number_is_monospaced_in_my_activities(login_as, course):  # noqa: F811
    certificates.record_outcome(course.student, result=CourseOutcome.Result.PASS, by=course.teacher)
    issued = certificates.issue(course.student, by=course.manager)
    student = login_as(Account.objects.get(person=course.student.person), AREA_PERSONAL)
    page = html.unescape(student.get(reverse("activities:mine")).content.decode())
    assert f'<span class="codi">{issued.certificate_number}</span>' in page
