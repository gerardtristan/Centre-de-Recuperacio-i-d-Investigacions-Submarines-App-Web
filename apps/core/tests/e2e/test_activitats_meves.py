"""«Les meves activitats» al navegador (T-M02-22b): una sòcia inscrita a una sortida en veu
l'estat, el botó per pagar-la i el calendari. Pantalles a 1280, 390 i 320 px (clar i fosc).
Només dades inventades."""

import pytest
from django.db import transaction
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import enrolment
from apps.activities.tests.helpers import a_member, an_open_outing
from conftest import PASSWORD

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def test_a_member_sees_her_activities(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    outing = an_open_outing(manager, title="Sortida inventada meva", price_member_cents=4500)
    account = a_member("Sòcia")
    account.set_password(PASSWORD)
    account.save()
    with transaction.atomic():
        enrolment.enrol(outing, account.person, channel="account", actor=account)

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}{reverse('activities:mine')}")
    expect(page.get_by_role("heading", name="Sortida inventada meva")).to_be_visible()
    expect(page.get_by_text("Pendent de pagament")).to_be_visible()
    review("meves-activitats")
