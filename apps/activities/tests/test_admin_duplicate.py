"""Duplicar des de la fitxa d'administració (T-M02-06c3; decisió 026; RN-M02-21 i 44; AC7). El
servei té les seves proves a `test_duplicate.py`. Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities.models import Activity
from apps.core.models import Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)

from .helpers import an_open_outing

pytestmark = pytest.mark.django_db


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(Role.Code.COURSES_MANAGER)


def detail(activity):
    return reverse("administration:activity_detail", args=[activity.pk])


def test_ca_m02_04_the_copy_is_a_draft_and_opens_for_editing(login_as, manager):
    outing = an_open_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    response = client.post(detail(outing), {"duplica": "1", "nou_inici": "2027-09-14"})
    copy = Activity.objects.exclude(pk=outing.pk).get()
    assert response.status_code == 303
    assert response["Location"] == reverse("administration:activity_edit", args=[copy.pk])
    assert (copy.status, copy.starts_on.isoformat(), copy.duplicated_from) == (
        "draft",
        "2027-09-14",
        outing,
    )


def test_a_missing_date_is_rejected(login_as, manager):
    outing = an_open_outing(manager)
    client = login_as(manager, AREA_ADMIN)
    assert client.post(detail(outing), {"duplica": "1", "nou_inici": ""}).status_code == 303
    assert Activity.objects.count() == 1


def test_without_ac7_nothing_is_copied(login_as, make_admin, manager):  # noqa: F811
    outing = an_open_outing(manager)
    client = login_as(make_admin(Role.Code.SECRETARY), AREA_ADMIN)
    assert (
        client.post(detail(outing), {"duplica": "1", "nou_inici": "2027-09-14"}).status_code == 404
    )
    assert Activity.objects.count() == 1
