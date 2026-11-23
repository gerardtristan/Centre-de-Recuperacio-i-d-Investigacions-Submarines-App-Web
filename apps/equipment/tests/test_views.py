"""Pantalles del 03 (T-M03-19 i T-M03-22): informes de material, cost d'una activitat i cost d'ús
per tipus, amb les proves de permisos. Només dades inventades."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN
from apps.activities.models import Activity
from apps.activities.tests.test_attendance import a_session, enrolled
from apps.core.models import Role
from apps.core.tests.conftest import main_of, make_admin  # noqa: F401 (fixture)
from apps.equipment import assignments, handover, inventory
from apps.equipment.models import EquipmentType, UsageRate

from .test_assignments import JUNE, jacket, keeper, kind, manager, outing  # noqa: F401 (fixtures)

pytestmark = pytest.mark.django_db
R = Role.Code
REPORTS = reverse("administration:equipment_reports")
RATES = reverse("administration:equipment_usage_rates")


def cost_page(activity):
    return reverse("administration:equipment_activity_cost", args=[activity.pk])


@pytest.fixture
def used(manager, keeper):  # noqa: F811
    """Una sortida amb un jaquet del club fet servir (dos dies a 1,50 €) i un regulador vençut."""
    UsageRate.objects.create(equipment_type=kind("Jaquet"), cost_per_day_cents=150, valid_from=JUNE)
    activity = outing(manager)
    row = assignments.assign_club(enrolled(activity, "Ana"), jacket(keeper), by=keeper)
    handover.deliver(row, by=keeper, now=timezone.now())
    yesterday = timezone.localdate() - datetime.timedelta(days=1)
    regulator = EquipmentType.objects.get(name="Regulador")
    inventory.create_item(equipment_type=regulator, by=keeper, next_review_on=yesterday)
    return activity, row


def test_the_keeper_sees_the_three_reports_csv_and_the_activity_cost(login_as, used, keeper):  # noqa: F811
    activity, row = used
    client = login_as(keeper, AREA_ADMIN)
    params = {"des_de": "2027-06-01", "fins_a": "2027-06-30"}
    html = main_of(client.get(REPORTS, params).content.decode())
    assert "Material més usat" in html and "Revisions properes" in html and "Vençuda" in html
    assert "Jaquet" in html and activity.title in html and "Ana" not in html
    csv = client.get(REPORTS, {**params, "format": "csv"})
    assert csv["Content-Type"].startswith("text/csv")
    assert "Jaquet;Del club;1" in csv.content.decode("utf-8-sig")
    html = main_of(client.get(cost_page(activity)).content.decode())
    assert "3,00" in html and str(row.enrolment_id) in html and "Ana" not in html
    csv = client.get(cost_page(activity), {"format": "csv"}).content.decode("utf-8-sig")
    assert f"{row.enrolment_id};3,00" in csv


def test_each_block_only_with_its_permission(login_as, used, make_admin):  # noqa: F811
    activity, _ = used
    # La junta: MT4 i MT12 de consulta, sense MT11.
    html = main_of(login_as(make_admin(R.BOARD), AREA_ADMIN).get(REPORTS).content.decode())
    assert "Material més usat" in html and "Revisions properes" not in html
    assert activity.title in html
    # Sense cap dels tres permisos, «no trobat»; també el cost i el CSV.
    client = login_as(make_admin(R.SECRETARY), AREA_ADMIN)
    assert client.get(REPORTS).status_code == 404
    assert client.get(REPORTS, {"format": "csv"}).status_code == 404
    assert client.get(cost_page(activity)).status_code == 404


def test_the_activity_cost_by_object(login_as, used, manager, make_admin):  # noqa: F811
    activity, _ = used
    Activity.objects.filter(pk=activity.pk).update(responsible=manager.person)
    other = make_admin(R.COURSES_MANAGER)  # «les seves activitats»: aquesta no és seva
    assert login_as(other, AREA_ADMIN).get(cost_page(activity)).status_code == 404
    assert login_as(manager, AREA_ADMIN).get(cost_page(activity)).status_code == 200
    html = main_of(login_as(other, AREA_ADMIN).get(REPORTS).content.decode())
    assert activity.title not in html


def test_the_treasurer_changes_the_usage_cost(login_as, make_admin, keeper):  # noqa: F811
    treasurer = make_admin(R.TREASURER)
    client = login_as(treasurer, AREA_ADMIN)
    assert "Desa el cost" in main_of(client.get(RATES).content.decode())
    jacket_type = kind("Jaquet")
    today = timezone.localdate()
    data = {"tipus": jacket_type.pk, "cost": "1,25", "des_de": today.isoformat(), "nota": "Prova"}
    response = client.post(RATES, data, follow=True)
    assert "desat. S&#x27;ha avisat el tresorer" in response.content.decode()
    assert UsageRate.objects.get(equipment_type=jacket_type).cost_per_day_cents == 125
    # La data passada la rebutja el servei i es mostra al formulari.
    past = {**data, "des_de": (today - datetime.timedelta(days=1)).isoformat()}
    html = main_of(client.post(RATES, past).content.decode())
    assert "no pot ser anterior a avui" in html
    # El responsable de material veu l'apartat però no el pot canviar.
    keeper_client = login_as(keeper, AREA_ADMIN)
    assert "Desa el cost" not in main_of(keeper_client.get(RATES).content.decode())
    assert keeper_client.post(RATES, data).status_code == 404
    assert login_as(make_admin(R.INSTRUCTOR), AREA_ADMIN).get(RATES).status_code == 404


def test_the_instructor_only_sees_the_most_used(login_as, used, manager, make_admin):  # noqa: F811
    activity, _ = used
    teacher = make_admin(R.INSTRUCTOR)  # MT4 de consulta: només el material més usat
    a_session(manager, activity, JUNE, teacher.person)
    html = main_of(login_as(teacher, AREA_ADMIN).get(REPORTS).content.decode())
    assert "Material més usat" in html and "Cost de material per activitat" not in html
