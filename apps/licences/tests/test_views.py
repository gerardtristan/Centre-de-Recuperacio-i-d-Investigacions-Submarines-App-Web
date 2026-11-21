"""Vistes v1 del 06: llistat, tramitar, deixar vigent i exportar (T-M06-09 i 10; LC4, LC5, C6;
CA-M06-10, 16 i 33). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.core.models import OutgoingEmail, Role, RolePermission
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.licences import day
from apps.licences.models import Licence, ValidityRule

R = Role.Code
LIST = reverse("administration:licences")
EXPORT = reverse("administration:licences_export")


@pytest.fixture
def paid(make_licence, make_person):
    return make_licence(status="paid", person=make_person("Anna", "Vila"))


@pytest.fixture
def as_role(login_as, make_admin):  # noqa: F811
    def login(role):
        return login_as(make_admin(role), AREA_ADMIN)

    return login


def test_the_secretary_sees_the_list_with_actions(as_role, paid):
    html = main_of(as_role(R.SECRETARY).get(LIST).content.decode())
    assert "Vila, Anna" in html and "Marca tramitada" in html and "Número federatiu" in html
    assert "Descarrega el fitxer per a la federació (1 pagada)" in html


def test_lc4_without_lc5_sees_no_actions(as_role, paid):
    html = main_of(as_role(R.COURSES_MANAGER).get(LIST).content.decode())
    assert "Vila, Anna" in html and "Marca tramitada" not in html and "Descarrega" not in html


@pytest.mark.parametrize("role", [R.INSTRUCTOR, R.BOARD, R.EQUIPMENT_MANAGER])
def test_without_lc4_not_found(as_role, role):
    assert as_role(role).get(LIST).status_code == 404


def test_without_c6_no_details_and_no_detail_filters(as_role, paid):
    RolePermission.objects.filter(role__code=R.SECRETARY,
                                  permission_code="licences.field.details").delete()  # fmt: skip
    client = as_role(R.SECRETARY)
    html = main_of(client.get(LIST).content.decode())
    assert "Número federatiu" not in html and 'name="categoria"' not in html
    assert client.get(LIST, {"categoria": "technical", "venciment": "60"}).status_code == 200


def test_filters(as_role, paid, make_licence, make_person):
    make_licence(status="requested", person=make_person("Pere", "Roca"))
    html = main_of(as_role(R.SECRETARY).get(LIST, {"estat": "paid"}).content.decode())
    assert "Vila, Anna" in html and "Roca, Pere" not in html


def test_mark_filed(as_role, paid):
    response = as_role(R.SECRETARY).post(reverse("administration:licences_file", args=[paid.pk]))
    assert response.status_code == 302
    paid.refresh_from_db()
    assert paid.status == "filed"


def test_mark_filed_twice_shows_the_error(as_role, paid):
    client = as_role(R.SECRETARY)
    url = reverse("administration:licences_file", args=[paid.pk])
    client.post(url)
    response = client.post(url, follow=True)
    assert "La llicència no és en" in main_of(response.content.decode())


def test_activate_needs_the_number(as_role, paid):
    client = as_role(R.SECRETARY)
    url = reverse("administration:licences_activate", args=[paid.pk])
    assert "Deixa vigent una llicència" in client.get(url).content.decode()
    assert client.post(url, {"numero": ""}).status_code == 200
    response = client.post(url, {"numero": "F-77"})
    assert response.status_code == 302
    paid.refresh_from_db()
    assert (paid.status, paid.federation_number) == ("active", "F-77")


def test_activate_a_wrong_status_shows_the_error(as_role, make_licence):
    licence = make_licence(status="requested")
    url = reverse("administration:licences_activate", args=[licence.pk])
    response = as_role(R.SECRETARY).post(url, {"numero": "F-1"})
    assert "La llicència no és en" in response.content.decode()


@pytest.mark.parametrize("role", [R.COURSES_MANAGER, R.TREASURER])
def test_lc5_actions_are_not_found_without_it(as_role, paid, role):
    client = as_role(role)
    assert client.post(reverse("administration:licences_file", args=[paid.pk])).status_code == 404
    assert (
        client.get(reverse("administration:licences_activate", args=[paid.pk])).status_code == 404
    )
    assert client.post(EXPORT).status_code == 404


def test_export_downloads_the_csv(as_role, paid):
    response = as_role(R.SECRETARY).post(EXPORT)
    assert response["Content-Type"] == "text/csv; charset=utf-8"
    assert response["Content-Disposition"].startswith('attachment; filename="llicencies-federacio-')
    assert "Vila" in response.content.decode("utf-8-sig")
    assert as_role(R.SECRETARY).get(EXPORT).status_code == 405


def test_a_lapsed_licence_notifies_who_files(make_licence, make_admin):  # noqa: F811
    import datetime

    secretary = make_admin(R.SECRETARY)
    secretary.notification_email = "secretaria@example.org"
    secretary.save()
    day_10 = datetime.date(2027, 5, 10)
    make_licence(status="filed", validity_rule=ValidityRule.SINGLE_DAY, starts_on=day_10,
                 expires_on=day_10)  # fmt: skip
    day.lapse_overdue(datetime.date(2027, 5, 11))
    (email,) = OutgoingEmail.objects.filter(template="avis-llicencia-no-tramitada")
    assert email.to_address == "secretaria@example.org" and "10/05/2027" in email.body_text
    assert Licence.objects.get().status == "lapsed"
