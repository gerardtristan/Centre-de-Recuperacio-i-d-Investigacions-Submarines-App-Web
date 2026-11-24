"""Accions d'estat a la fitxa d'administració (T-M02-06c1; RN-M02-02, 13 i 20; AC7). Els serveis
tenen les seves proves a `test_states.py` i `test_cancellation.py`. Només dades inventades."""

import datetime
import html

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities.models import Activity
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import an_open_outing, an_outing

pytestmark = pytest.mark.django_db
S = Activity.Status


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def detail(activity):
    return reverse("administration:activity_detail", args=[activity.pk])


def act(client, activity, action, **data):
    return client.post(detail(activity), {"accio": action, **data})


def status(activity):
    activity.refresh_from_db()
    return activity.status


def test_publish_close_and_reopen(login_as, manager):
    outing = an_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    page = client.get(detail(outing)).content.decode()
    assert 'value="publica"' in page and 'value="tanca"' not in page
    assert act(client, outing, "publica").status_code == 303 and status(outing) == S.OPEN
    assert act(client, outing, "tanca").status_code == 303
    assert status(outing) == S.REGISTRATION_CLOSED
    assert act(client, outing, "reobre").status_code == 303 and status(outing) == S.OPEN


def test_a_reopen_date_after_the_start_is_rejected(login_as, manager):
    outing = an_open_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    act(client, outing, "tanca")
    late = (outing.starts_on + datetime.timedelta(days=3)).strftime("%Y-%m-%dT20:00")
    response = client.get(act(client, outing, "reobre", closes_at=late)["Location"])
    assert "no pot passar del dia d'inici" in html.unescape(response.content.decode())
    assert status(outing) == S.REGISTRATION_CLOSED


def test_rn_m02_20_not_done_before_the_day(login_as, manager):
    outing = an_open_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    act(client, outing, "feta")
    assert status(outing) == S.OPEN


def test_cancel_needs_a_reason(login_as, manager):
    outing = an_open_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    act(client, outing, "cancella", motiu="")
    assert status(outing) == S.OPEN
    act(client, outing, "cancella", motiu="Mal temps inventat.")
    outing.refresh_from_db()
    assert (outing.status, outing.cancellation_reason) == (S.CANCELLED, "Mal temps inventat.")


def test_without_ac7_nothing_changes(login_as, make_admin, manager):  # noqa: F811
    outing = an_outing(manager)
    client = login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN)
    assert act(client, outing, "publica").status_code == 404
    assert status(outing) == S.DRAFT


def test_an_unknown_action_is_not_found(login_as, manager):
    assert act(login_as(manager, AREA_ADMIN), an_outing(manager), "esborra").status_code == 404


def test_a_reopen_date_that_is_not_a_date_is_rejected(login_as, manager):
    outing = an_open_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    act(client, outing, "tanca")
    response = client.get(act(client, outing, "reobre", closes_at="demà")["Location"])
    assert "Escriu el dia i l'hora" in html.unescape(response.content.decode())
    assert status(outing) == S.REGISTRATION_CLOSED
