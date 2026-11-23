"""Duplicar una activitat al navegador (T-M02-06c3): el responsable en crea una còpia per a una
altra data des de la fitxa i arriba al formulari per revisar-la. Pantalles a 1280, 390 i 320 px
(clar i fosc). Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities.tests.helpers import an_open_outing

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_manager_duplicates_an_outing(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    outing = an_open_outing(manager, title="Sortida inventada per duplicar")
    login_admin(page, live_server.url, manager.login)
    page.goto(f"{live_server.url}{reverse('administration:activity_detail', args=[outing.pk])}")
    page.get_by_text("Duplica l'activitat").click()
    page.get_by_label("Data d'inici de la còpia").fill("2027-09-14")
    review("activitat-duplicar")
    page.get_by_role("button", name="Crea la còpia").click()
    expect(page.get_by_text("Còpia creada en esborrany.")).to_be_visible()
    expect(page.get_by_role("heading", name="Edita l'activitat")).to_be_visible()
