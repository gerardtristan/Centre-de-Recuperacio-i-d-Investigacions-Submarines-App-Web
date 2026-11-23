"""Inscripció d'un soci des de l'àrea personal (T-M02-11; CA-M02-06, 12, 13, 28 i 29). El servei
té les seves proves a `test_enrolment.py`. Només dades inventades."""

import html

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.activities.models import Enrolment
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member, an_open_outing, an_outing

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def url(activity):
    return reverse("activities:member_enrol", args=[activity.pk])


def page(client, activity):
    return html.unescape(client.get(url(activity)).content.decode())


def test_ca_m02_06_a_member_sees_the_member_price_enrols_and_goes_to_pay(login_as, manager):
    outing = an_open_outing(manager, price_member_cents=4500, price_non_member_cents=6000)
    account = a_member()
    client = login_as(account, AREA_PERSONAL)
    assert "Preu de soci" in page(client, outing) and "45,00" in page(client, outing)
    response = client.post(url(outing))
    row = Enrolment.objects.get()
    assert (row.person, row.channel, row.price_cents) == (account.person, "account", 4500)
    assert response.status_code == 302
    assert response["Location"] == reverse("payments:charge", args=[row.charge_id])
    assert "La teva inscripció: Pendent de pagament." in page(client, outing)
    assert client.post(url(outing)).status_code == 200  # una de viva per persona
    assert Enrolment.objects.count() == 1


def test_ca_m02_28_a_blocking_requirement_shows_and_nothing_is_sent(login_as, manager):
    outing = an_open_outing(manager, licence_required=True, requirements_mode="block")
    client = login_as(a_member(), AREA_PERSONAL)
    text = page(client, outing)
    assert "No compleixes" in text and "Inscriu-me" not in text
    assert client.post(url(outing)).status_code == 200
    assert not Enrolment.objects.exists()


def test_ca_m02_29_a_warning_lets_enrol_and_stays_on_the_enrolment(login_as, manager):
    outing = an_open_outing(manager, licence_required=True, requirements_mode="warn")
    client = login_as(a_member(), AREA_PERSONAL)
    assert "Es revisarà" in page(client, outing)
    client.post(url(outing))
    assert Enrolment.objects.get().requirements_warning


def test_non_public_activity_is_not_found(login_as, manager):
    client = login_as(a_member(), AREA_PERSONAL)
    assert client.get(url(an_outing(manager))).status_code == 404
