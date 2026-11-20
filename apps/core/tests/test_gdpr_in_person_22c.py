"""Drets d'un menor de 14 anys, demanats en persona (T-M01-22c; 085, A-2; P-417): la secretaria
(M11b) registra la sol·licitud d'esborrat, amb la identitat del representant comprovada; queda
pendent i l'atén qui té M11. Només dades inventades."""

import datetime

import pytest
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.core import erasure
from apps.core.models import AuditEntry, ErasureRequest, Person, RolePermission
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

pytestmark = pytest.mark.django_db

PAGE = "administration:gdpr_in_person"


def born(years_ago, days=0):
    today = timezone.localdate()
    return datetime.date(today.year - years_ago, today.month, 1) - datetime.timedelta(days=days)


def a_person(birth_date):
    return Person.objects.create(
        first_name="Nil", last_name="Prova Inventat", origin="in_person", birth_date=birth_date
    )


@pytest.fixture
def minor():
    return a_person(born(10))


@pytest.fixture
def clerk(make_admin):  # noqa: F811
    """Un compte de la Secretaria (M11b)."""
    return make_admin("secretary")


def test_m11b_is_only_of_the_secretary_in_the_initial_matrix():
    cells = RolePermission.objects.filter(permission_code=erasure.REGISTER_PERMISSION)
    assert [(c.role.code, c.scope) for c in cells] == [("secretary", "all")]


def test_the_secretary_registers_it_and_it_stays_pending(minor, clerk):
    created = erasure.register_in_person(minor, by=clerk, guardian_checked=True)
    assert (created.status, created.channel) == (
        ErasureRequest.Status.PENDING,
        ErasureRequest.Channel.IN_PERSON,
    )
    assert created.requested_by == clerk
    entry = AuditEntry.objects.get(action=audit_action())
    assert entry.details == {"channel": "in_person", "guardian_checked": True}


def audit_action():
    from apps.core import audit

    return audit.Action.ERASURE_REQUESTED


def test_the_guardian_identity_must_be_checked(minor, clerk):
    with pytest.raises(erasure.ErasureNotAllowed, match="identitat"):
        erasure.register_in_person(minor, by=clerk, guardian_checked=False)
    assert not ErasureRequest.objects.exists()


@pytest.mark.parametrize("birth_date", [None, "14"])
def test_only_a_minor_under_14(clerk, birth_date):
    person = a_person(born(14) if birth_date else None)
    assert not erasure.can_register_in_person(person, clerk)
    with pytest.raises(erasure.ErasureNotAllowed, match="menor de 14"):
        erasure.register_in_person(person, by=clerk, guardian_checked=True)


def test_one_day_before_turning_14_it_still_is(clerk):
    today = timezone.localdate()
    tomorrow = today + datetime.timedelta(days=1)
    person = a_person(datetime.date(tomorrow.year - 14, tomorrow.month, tomorrow.day))
    assert erasure.is_under_14(person, today)


def test_only_one_pending(minor, clerk):
    erasure.register_in_person(minor, by=clerk, guardian_checked=True)
    with pytest.raises(erasure.ErasureNotAllowed, match="pendent"):
        erasure.register_in_person(minor, by=clerk, guardian_checked=True)


@pytest.mark.parametrize("role", ["treasurer", "administrator", "president"])
def test_without_m11b_not_found(minor, make_admin, role):  # noqa: F811
    with pytest.raises(Http404):
        erasure.register_in_person(minor, by=make_admin(role), guardian_checked=True)


class TestScreen:
    def test_the_secretary_registers_it_from_the_screen(self, minor, clerk, login_as):
        client = login_as(clerk, AREA_ADMIN)
        url = reverse(PAGE, args=[minor.pk])
        page = client.get(url).content.decode()
        assert 'name="guardian_checked"' in page
        assert client.post(url, {}).status_code == 200  # sense la casella, res
        assert not ErasureRequest.objects.exists()
        response = client.post(url, {"guardian_checked": "on"})
        assert response.status_code == 302
        assert ErasureRequest.objects.get().channel == "in_person"
        assert "esborrat registrada" in client.get(url).content.decode()

    def test_an_adult_gets_no_form(self, clerk, login_as):
        adult = a_person(born(30))
        page = login_as(clerk, AREA_ADMIN).get(reverse(PAGE, args=[adult.pk])).content.decode()
        assert 'name="guardian_checked"' not in page and "des del seu perfil" in page

    def test_without_m11b_not_found(self, minor, make_admin, login_as):  # noqa: F811
        client = login_as(make_admin("administrator"), AREA_ADMIN)
        url = reverse(PAGE, args=[minor.pk])
        assert client.get(url).status_code == 404
        assert client.post(url, {"guardian_checked": "on"}).status_code == 404
