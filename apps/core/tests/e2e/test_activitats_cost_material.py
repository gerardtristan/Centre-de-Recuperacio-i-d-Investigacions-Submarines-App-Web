"""Cost de material previst a la fitxa de l'activitat al navegador (T-M02-40c; CA-M02-45): el
responsable de cursos i sortides canvia el cost d'una sortida seva, primer sense motiu (error) i
després amb motiu. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import datetime

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.activities import catalogue, services
from apps.activities.models import Activity, OutingType

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_manager_changes_the_material_cost_with_a_note(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    place = catalogue.create_place(by=manager, name="Cala inventada")
    outing = services.create_outing(
        by=manager, outing_type=OutingType.objects.get(name="Immersió"), place=place,
        title="Sortida inventada a la cala", starts_on=datetime.date(2027, 6, 14),
        ends_on=datetime.date(2027, 6, 14), max_places=10, responsible=manager.person,
        registration_closes_at=timezone.make_aware(datetime.datetime(2027, 6, 10, 20)),
        price_member_cents=5000, price_non_member_cents=6000,
    )  # fmt: skip
    Activity.objects.filter(pk=outing.pk).update(
        standard_material_cost_cents=2500, material_cost_cents=2500
    )

    login_admin(page, live_server.url, manager.login)
    page.goto(f"{live_server.url}{reverse('administration:activity_detail', args=[outing.pk])}")
    expect(page.get_by_role("heading", name="Cost de material previst")).to_be_visible()
    page.get_by_label("Cost de material previst per participant").fill("18")
    page.get_by_role("button", name="Desa el cost previst").click()
    expect(page.locator("[data-errata]")).to_contain_text("Cal dir per què")
    page.get_by_label("Motiu si no és l'estàndard").fill("Material propi del club (inventat).")
    page.get_by_role("button", name="Desa el cost previst").click()
    expect(page.get_by_text("Cost de material previst desat.")).to_be_visible()
    expect(page.get_by_text("Material propi del club (inventat).").first).to_be_visible()
    review("activitats-cost-material")
    assert Activity.objects.get().material_cost_cents == 1800
