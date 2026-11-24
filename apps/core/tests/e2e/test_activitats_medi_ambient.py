"""Resultats ambientals al navegador (T-M02-20b): la responsable registra els quilos i les espècies
d'una sortida de neteja feta i obre la fitxa del projecte des del catàleg. Pantalles a 1280, 390 i
320 px (clar i fosc). Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import catalogue
from apps.activities.models import Activity, EnvironmentalSubtype, OutingType
from apps.activities.tests.helpers import an_outing, general

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_manager_records_results_and_sees_the_project(
    page, live_server, transactional_db, review
):
    manager = make_admin("cursos.prova", "courses_manager")
    project = catalogue.create_project(
        by=manager, name="Projecte inventat de neteja", objective="Objectiu inventat.",
        department=general(),
    )  # fmt: skip
    outing = an_outing(
        manager, title="Neteja inventada del port", project=project,
        outing_type=OutingType.objects.get(name="Medi ambient"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"),
    )  # fmt: skip
    Activity.objects.filter(pk=outing.pk).update(status=Activity.Status.DONE)

    login_admin(page, live_server.url, manager.login)
    page.goto(f"{live_server.url}{reverse('administration:activity_detail', args=[outing.pk])}")
    page.get_by_role("link", name="Resultats ambientals").click()
    page.get_by_label("Residus recollits (kg)").fill("12,5")
    page.get_by_label("Espècies observades").fill("Nacra\nPop roquer")
    page.get_by_role("button", name="Desa els resultats").click()
    expect(page.get_by_text("Resultats desats.")).to_be_visible()
    review("resultats-ambientals")
    page.get_by_role("link", name="Projecte «Projecte inventat de neteja»").click()
    expect(page.get_by_text("12,5 kg")).to_be_visible()
    review("fitxa-projecte")
