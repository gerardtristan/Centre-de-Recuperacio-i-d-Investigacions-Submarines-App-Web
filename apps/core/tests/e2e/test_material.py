"""Pantalles del 03 al navegador (T-M03-19 i T-M03-22): el responsable de material mira els
informes i el tresorer canvia el cost d'ús d'un tipus. Pantalles a 1280, 390 i 320 px. Només dades
inventades."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.equipment import inventory
from apps.equipment.models import EquipmentType, UsageRate

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_keeper_reads_the_reports(page, live_server, transactional_db, review):
    keeper = make_admin("material.prova", "equipment_manager")
    regulator = EquipmentType.objects.get(name="Regulador")
    soon = timezone.localdate() + datetime.timedelta(days=10)
    inventory.create_item(equipment_type=regulator, by=keeper, next_review_on=soon)
    login_admin(page, live_server.url, keeper.login)

    page.goto(f"{live_server.url}{reverse('administration:equipment_reports')}")
    expect(page.get_by_role("heading", name="Informes de material")).to_be_visible()
    expect(
        page.get_by_role("table", name="Peces amb la revisió a prop o vençuda, per data")
    ).to_contain_text("MAT-0001")
    review("material-informes")


def test_the_treasurer_changes_the_usage_cost(page, live_server, transactional_db, review):
    treasurer = make_admin("tresorer.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)

    page.goto(f"{live_server.url}{reverse('administration:equipment_usage_rates')}")
    expect(page.get_by_role("heading", name="Cost d'ús del material")).to_be_visible()
    page.get_by_label("Tipus de material").select_option(label="Jaquet")
    page.get_by_label("Cost per dia (€)").fill("1,25")
    page.get_by_label("Nota").fill("Cost revisat (inventat).")
    review("material-cost-us-formulari")
    page.get_by_role("button", name="Desa el cost").click()
    expect(page.get_by_text("Cost d'ús desat.")).to_be_visible()
    review("material-cost-us")
    assert UsageRate.objects.get().cost_per_day_cents == 125
