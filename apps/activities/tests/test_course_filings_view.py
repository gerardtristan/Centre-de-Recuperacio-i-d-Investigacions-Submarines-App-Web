# ruff: noqa: F811 (fixtures importades com a paràmetres)
"""«Titulacions i llicències per tramitar» (T-M02-45b; RN-M02-52 i 58; RN-M06-28; CA-M02-55 i
58): la llista de la primera estrella amb «Cal llicència» i «Demana la primera llicència». Només
dades inventades."""

import html

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities.models import CertificationFiling
from apps.core.models import Charge, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.licences.models import Licence

from .test_certificates import course  # noqa: F401 (fixture)
from .test_first_licence_02 import includes, licence_type  # noqa: F401 (fixture)
from .test_first_star import pass_and_issue, with_official_level

pytestmark = pytest.mark.django_db
URL = reverse("administration:course_filings")


@pytest.fixture
def secretary(make_admin):
    return make_admin(Role.Code.SECRETARY)


def page(client):
    response = client.get(URL)
    assert response.status_code == 200
    return html.unescape(response.content.decode())


def test_the_list_shows_who_needs_a_licence_and_asks_for_it(
    login_as, course, licence_type, secretary
):
    with_official_level(course)
    pass_and_issue(course, course.student)
    client = login_as(secretary, AREA_ADMIN)
    text = page(client)
    assert "1 titulació per tramitar" in text and "Cal llicència" in text
    assert "Demana la primera llicència" in text

    filing = CertificationFiling.objects.get()
    charges = Charge.objects.count()
    response = client.post(URL, {"filing": filing.pk, "licence_type": licence_type.pk})
    assert response.status_code == 303
    licence = Licence.objects.get(person=course.student.person)
    assert (licence.status, licence.list_entry) == ("requested", filing)
    assert Charge.objects.count() == charges + 1
    text = page(client)
    assert "Primera llicència demanada" in text and "Demana la primera llicència" not in text


def test_a_course_that_includes_it_never_offers_the_paid_path(
    login_as, course, licence_type, secretary
):
    with_official_level(course)
    includes(course)
    pass_and_issue(course, course.student)  # sense el tipus triat (P-530): no es crea cap
    client = login_as(secretary, AREA_ADMIN)
    text = page(client)
    assert "falta triar a Ajustos" in text and "Demana la primera llicència" not in text

    filing = CertificationFiling.objects.get()
    client.post(URL, {"filing": filing.pk, "licence_type": licence_type.pk})
    assert "inclosa al curs" in page(client)
    assert not Licence.objects.filter(person=course.student.person).exists()


def test_bad_requests_and_permissions(login_as, course, licence_type, secretary, make_admin):
    client = login_as(secretary, AREA_ADMIN)
    assert client.post(URL, {"filing": 999, "licence_type": licence_type.pk}).status_code == 404
    client.post(URL, {"filing": 1})
    assert "Tria un tipus de llicència" in page(client)
    for role in (Role.Code.INSTRUCTOR, Role.Code.TREASURER):  # sense AC26
        assert login_as(make_admin(role), AREA_ADMIN).get(URL).status_code == 404
