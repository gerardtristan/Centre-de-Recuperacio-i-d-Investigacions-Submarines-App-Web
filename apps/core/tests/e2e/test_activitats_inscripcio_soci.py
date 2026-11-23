"""Inscripció d'un soci al navegador (T-M02-11): una sòcia entra a la seva àrea, obre la inscripció
d'una sortida publicada, veu el preu de soci i un requisit que es revisarà, s'inscriu i arriba a la
pantalla de pagament. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities.tests.helpers import a_member, an_open_outing
from conftest import PASSWORD

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def test_a_member_enrols_and_goes_to_pay(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    outing = an_open_outing(
        manager, title="Sortida inventada per a socis", price_member_cents=4500,
        price_non_member_cents=6000, licence_required=True, requirements_mode="warn",
    )  # fmt: skip
    account = a_member("Sòcia")
    account.set_password(PASSWORD)
    account.save()

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}{reverse('activities:member_enrol', args=[outing.pk])}")
    expect(page.get_by_role("heading", name="Sortida inventada per a socis")).to_be_visible()
    expect(page.get_by_text("Es revisarà")).to_be_visible()
    review("inscripcio-soci")
    page.get_by_role("button", name="Inscriu-me").click()
    expect(page.get_by_text("Inscripció feta. Ara pots pagar-la.")).to_be_visible()
    review("inscripcio-soci-pagament")
