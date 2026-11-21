"""Marge d'una activitat al navegador (P-M09-D; MG5, MG6 i MG7): el tresorer hi posa un cost
previst, veu el marge previst i tanca una activitat feta, amb el marge congelat. Pantalles a 1280,
390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities.models import Activity
from apps.activities.tests.helpers import an_outing

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_treasurer_plans_and_closes(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    activity = an_outing(manager, title="Sortida inventada a les Medes")
    Activity.objects.filter(pk=activity.pk).update(status=Activity.Status.DONE)
    treasurer = make_admin("tresorer.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)

    page.goto(f"{live_server.url}{reverse('administration:activity_margin', args=[activity.pk])}")
    expect(page.get_by_role("heading", name="Sortida inventada a les Medes")).to_be_visible()
    expect(page.get_by_role("heading", name="Marge previst")).to_be_visible()
    page.get_by_label("Categoria").select_option(label="Embarcació")
    page.get_by_label("Import previst (€)").fill("250,00")
    page.get_by_role("button", name="Desa el cost previst").click()
    expect(page.get_by_text("Cost previst desat.")).to_be_visible()
    expect(
        page.get_by_role(
            "table", name="Per categoria. Compten mentre la categoria no té costos reals."
        )
    ).to_contain_text("Embarcació")
    review("marge-previst")

    page.get_by_role("button", name="Tanca l'activitat").click()
    expect(page.get_by_text("Activitat tancada: el marge real queda congelat.")).to_be_visible()
    expect(page.get_by_role("heading", name="Marge congelat")).to_be_visible()
    review("marge-congelat")
