"""Resultats del curs i certificat (T-M02-19b; P-M02-F passos 5 i 6; CA-M02-19; AC12 i AC13). Només
dades inventades."""

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.activities import permissions
from apps.activities.models import CertificationLevel, CourseOutcome
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import an_outing
from .test_attendance import manager  # noqa: F401 (fixtures)
from .test_attendance_views import roll_url, today_course  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
R = Role.Code


def page(course):
    return reverse("administration:course_outcomes", args=[course.activity.pk])


def test_the_instructor_records_the_outcome(login_as, today_course):  # noqa: F811
    client = login_as(today_course.own, AREA_ADMIN)
    roll = main_of(client.get(roll_url(today_course, today_course.first)).content.decode())
    assert page(today_course) in roll  # l'enllaç des de la llista
    html = main_of(client.get(page(today_course)).content.decode())
    assert "Alumna Prova" in html and "Sense resultat" in html and "Emet el certificat" not in html
    data = {"inscripcio": today_course.student.pk, "resultat": "fail", "motiu": ""}
    response = client.post(page(today_course), data, follow=True)
    assert "cal un motiu" in response.content.decode()
    client.post(page(today_course), {**data, "resultat": "pass"})
    assert CourseOutcome.objects.get().result == "pass"


def test_an_instructor_outside_the_course_gets_not_found_and_it_is_logged(
    login_as,
    today_course,  # noqa: F811
    make_admin,  # noqa: F811
):
    client = login_as(make_admin(R.INSTRUCTOR), AREA_ADMIN)
    assert client.get(page(today_course)).status_code == 404
    assert AuditEntry.objects.filter(action=permissions.OUT_OF_SCOPE).count() == 1
    # Una sortida no té resultats.
    outing = an_outing(today_course.manager)
    url = reverse("administration:course_outcomes", args=[outing.pk])
    assert login_as(today_course.own, AREA_ADMIN).get(url).status_code == 404


def test_ca_m02_19_the_manager_issues_the_certificate(login_as, today_course, manager):  # noqa: F811
    CertificationLevel.objects.create(name="Nivell inventat", rank=99)
    instructor = login_as(today_course.own, AREA_ADMIN)
    data = {"inscripcio": today_course.student.pk, "resultat": "pass", "motiu": ""}
    instructor.post(page(today_course), data)
    client = login_as(manager, AREA_ADMIN)
    html = main_of(client.get(page(today_course)).content.decode())
    assert "Emet el certificat" in html and "Desa el resultat" not in html
    level = CertificationLevel.objects.get(name="Nivell inventat")
    issue = {"inscripcio": today_course.student.pk, "emet": "1", "nivell": level.pk}
    response = client.post(page(today_course), issue, follow=True)
    assert "Certificat emès." in response.content.decode()
    number = CourseOutcome.objects.get().certificate_number
    assert number == f"C-{timezone.localdate().year}-0001"
    url = reverse(
        "administration:course_certificate",
        args=[today_course.activity.pk, today_course.student.pk],
    )
    cert = main_of(client.get(url).content.decode())
    assert number in cert and "Alumna Prova" in cert and "Desa com a PDF" in cert
    # L'instructor no té AC13: el certificat, «no trobat».
    assert login_as(today_course.own, AREA_ADMIN).get(url).status_code == 404


def test_without_ac12_or_ac13_not_found(login_as, today_course, make_admin):  # noqa: F811
    client = login_as(make_admin(R.SECRETARY), AREA_ADMIN)
    assert client.get(page(today_course)).status_code == 404
    assert AuditEntry.objects.filter(action=permissions.OUT_OF_SCOPE).count() == 0
