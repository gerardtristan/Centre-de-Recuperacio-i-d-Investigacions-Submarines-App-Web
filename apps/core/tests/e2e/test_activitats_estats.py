"""Estat d'una activitat al navegador (T-M02-06c1): el responsable publica una sortida en esborrany
des de la fitxa i després la cancel·la amb motiu. Pantalles a 1280, 390 i 320 px (clar i fosc).
Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities.tests.helpers import an_outing

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_manager_publishes_and_cancels_an_outing(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    outing = an_outing(manager, title="Sortida inventada per publicar")
    login_admin(page, live_server.url, manager.login)
    page.goto(f"{live_server.url}{reverse('administration:activity_detail', args=[outing.pk])}")
    review("activitat-esborrany")
    page.get_by_role("button", name="Publica").click()
    expect(page.get_by_text("Estat desat.")).to_be_visible()
    expect(page.get_by_role("button", name="Tanca les inscripcions")).to_be_visible()
    page.get_by_text("Cancel·la l'activitat…").click()  # plegat (T-DX-99)
    page.get_by_label("Motiu de la cancel·lació").fill("Mal temps inventat.")
    page.get_by_role("button", name="Cancel·la l'activitat").click()
    expect(page.get_by_text("Mal temps inventat.").first).to_be_visible()
    review("activitat-cancellada")
