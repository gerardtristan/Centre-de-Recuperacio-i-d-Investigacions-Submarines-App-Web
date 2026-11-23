"""«Les meves activitats», el calendari d'una inscripció i «Què falta per tancar» (T-M02-22b; C16;
RN-M02-25 i 45; CA-M02-23). Només dades inventades."""

import html

import pytest
from django.db import transaction
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.activities import enrolment
from apps.activities.models import Activity, Enrolment
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import a_member, an_open_outing

pytestmark = pytest.mark.django_db
MINE = reverse("activities:mine")


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def enrol(activity, account):
    with transaction.atomic():
        return enrolment.enrol(activity, account.person, channel="account", actor=account)


def test_c16_the_member_sees_only_her_enrolments_with_pay_and_calendar(login_as, manager):
    outing = an_open_outing(manager, title="Sortida meva inventada", price_member_cents=4500)
    account, other = a_member(), a_member("Altra")
    row = enrol(outing, account)
    enrol(an_open_outing(manager, title="Sortida d'una altra"), other)
    client = login_as(account, AREA_PERSONAL)
    page = html.unescape(client.get(MINE).content.decode())
    assert "Sortida meva inventada" in page and "Sortida d'una altra" not in page
    assert reverse("payments:charge", args=[row.charge_id]) in page
    calendar = reverse("activities:enrolment_calendar", args=[row.pk])
    response = client.get(calendar)
    assert response["Content-Type"].startswith("text/calendar")
    body = response.content.decode()
    assert "BEGIN:VCALENDAR" in body and "Sortida meva inventada" in body
    assert account.person.first_name not in body  # RN-M02-25: cap persona


def test_the_calendar_of_someone_else_is_not_found(login_as, manager):
    outing = an_open_outing(manager)
    theirs = enrol(outing, a_member("Altra"))
    client = login_as(a_member(), AREA_PERSONAL)
    url = reverse("activities:enrolment_calendar", args=[theirs.pk])
    assert client.get(url).status_code == 404


def test_empty_state(login_as):
    page = html.unescape(login_as(a_member(), AREA_PERSONAL).get(MINE).content.decode())
    assert "Encara no t'has inscrit a cap activitat." in page


def test_ca_m02_23_what_is_left_to_close_without_personal_data(login_as, manager):
    outing = an_open_outing(manager, price_member_cents=4500)
    account = a_member()
    enrol(outing, account)
    Activity.objects.filter(pk=outing.pk).update(status=Activity.Status.DONE)
    client = login_as(manager, AREA_ADMIN)
    detail = reverse("administration:activity_detail", args=[outing.pk])
    page = html.unescape(client.get(detail).content.decode())
    assert "Què falta per tancar" in page and "pendent de pagament" in page
    assert Enrolment.objects.filter(status="pending_payment").exists()
