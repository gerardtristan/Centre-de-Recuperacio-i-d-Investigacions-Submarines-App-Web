"""Missatge de l'organitzador als inscrits al navegador (T-M02-21c; AC15). Pantalles a 1280, 390 i
320 px. Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities.tests.helpers import an_open_outing
from apps.activities.tests.test_notifications_21b import enrol, member
from apps.core.models import OutgoingEmail

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_organiser_sends_a_message(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    outing = an_open_outing(manager, max_places=12)
    enrol(outing, member("a@example.org"))
    login_admin(page, live_server.url, manager.login)

    page.goto(f"{live_server.url}{reverse('administration:activity_detail', args=[outing.pk])}")
    page.get_by_role("link", name="Missatge als inscrits").click()
    page.get_by_label("Assumpte").fill("Canvi de punt de trobada")
    page.get_by_label("Text").fill("Ens veiem al moll 3, a les 8.")
    review("missatge-inscrits")
    page.get_by_role("button", name="Envia el missatge").click()
    expect(page.get_by_text("Missatge a la cua per a 1 persona.")).to_be_visible()
    assert OutgoingEmail.objects.filter(template="missatge-activitat").count() == 1
