"""Cost de material previst a la fitxa de l'activitat (T-M02-40c; RN-M02-43; CA-M02-45; AC23 i
C7). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN
from apps.activities.material_cost import MATERIAL_COST_CHANGED
from apps.activities.models import Activity
from apps.activities.permissions import OUT_OF_SCOPE
from apps.core.models import AuditEntry, Charge, Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)

from .helpers import an_outing

R = Role.Code
FIELD = "Cost de material previst"
BUTTON = "Desa el cost previst"


@pytest.fixture
def manager(make_admin):  # noqa: F811
    return make_admin(R.COURSES_MANAGER)


@pytest.fixture
def client_of(login_as):
    return lambda account: login_as(account, AREA_ADMIN)


@pytest.fixture
def activity(manager):
    """Una sortida seva amb un cost estàndard de 2500 calculat pel 03."""
    outing = an_outing(manager, responsible=manager.person)
    Activity.objects.filter(pk=outing.pk).update(
        standard_material_cost_cents=2500, material_cost_cents=2500
    )
    return Activity.objects.get(pk=outing.pk)


def urls(activity):
    """La fitxa i on s'envia el cost: la mateixa adreça (POST)."""
    url = reverse("administration:activity_detail", args=[activity.pk])
    return url, url


def test_ca_m02_45_a_different_cost_needs_a_note_and_no_charge(client_of, manager, activity):
    detail, post = urls(activity)
    client = client_of(manager)
    page = main_of(client.get(detail).content.decode())
    assert FIELD in page and "25,00" in page and BUTTON in page
    response = client.post(post, {"cost": "18"})
    assert response.status_code == 200
    assert "Cal dir per què el cost de material difereix" in response.content.decode()
    activity.refresh_from_db()
    assert activity.material_cost_cents == 2500
    charges = Charge.objects.count()
    response = client.post(post, {"cost": "18", "note": "Material propi (inventat)."})
    assert response.status_code == 303
    activity.refresh_from_db()
    assert activity.material_cost_cents == 1800
    assert activity.material_cost_note == "Material propi (inventat)."
    entry = AuditEntry.objects.get(action=MATERIAL_COST_CHANGED)
    assert (entry.old_value, entry.new_value) == (2500, 1800)
    assert Charge.objects.count() == charges


def test_c7_without_ac23_sees_the_cost_but_cannot_change_it(client_of, make_admin, activity):  # noqa: F811
    detail, post = urls(activity)
    client = client_of(make_admin(R.PRESIDENT))  # AC7 i C7, sense AC23
    page = main_of(client.get(detail).content.decode())
    assert FIELD in page and BUTTON not in page
    assert client.post(post, {"cost": "18", "note": "x"}).status_code == 404
    activity.refresh_from_db()
    assert activity.material_cost_cents == 2500


def test_another_manager_neither_sees_nor_changes_it(client_of, make_admin, activity):  # noqa: F811
    detail, post = urls(activity)
    other = make_admin(R.COURSES_MANAGER)  # C7 i AC23 només de les seves activitats
    client = client_of(other)
    assert FIELD not in main_of(client.get(detail).content.decode())
    assert client.post(post, {"cost": "18", "note": "x"}).status_code == 404
    activity.refresh_from_db()
    assert activity.material_cost_cents == 2500
    assert AuditEntry.objects.filter(action=OUT_OF_SCOPE, actor_account=other).exists()
