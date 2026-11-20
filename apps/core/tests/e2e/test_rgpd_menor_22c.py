"""Esborrat d'un menor de 14 anys demanat en persona, al navegador (T-M01-22c; 085, A-2; P-417):
la secretaria el registra des de «Més» de la fitxa del soci amb la identitat del representant
comprovada; queda pendent a «Sol·licituds RGPD», on l'administrador veu que és presencial.
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.core.models import ErasureRequest

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


@pytest.fixture
def minor(builder):
    return builder.approve(
        builder.submit(
            "Mia",
            "Donzella Prova",
            "",
            builder.born(10),
            builder.supporter,
            guardian=True,
            privacy=True,
            membership_terms=True,
        )
    )


def test_the_secretary_registers_the_erasure_of_a_minor(page, live_server, minor, review):
    clerk = make_admin("secretaria.rgpd", "secretary")
    login_admin(page, live_server.url, clerk.login)
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/socis/{minor.pk}/")
    page.locator("summary", has_text="Més").click()
    page.get_by_role("link", name="Registra un esborrat demanat en persona…").click()
    expect(
        page.get_by_role("heading", name="Esborrat demanat en persona: Mia Donzella Prova")
    ).to_be_visible()
    review("esborrat-presencial")

    page.get_by_role("button", name="Registra la sol·licitud").click()
    expect(page.get_by_text("Cal comprovar-ho abans de registrar-la.")).to_be_visible()
    review("esborrat-presencial-sense-comprovar")

    page.get_by_label("He comprovat en persona la identitat", exact=False).check()
    page.get_by_role("button", name="Registra la sol·licitud").click()
    expect(page.get_by_text("Sol·licitud d'esborrat registrada.", exact=False)).to_be_visible()
    review("esborrat-presencial-registrat")
    item = ErasureRequest.objects.get(person=minor.person)
    assert (item.status, item.channel) == ("pending", "in_person")

    page.context.clear_cookies()  # una altra sessió: la de l'administrador
    login_admin(page, live_server.url, make_admin("administracio.rgpd", "administrator").login)
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/rgpd/{item.pk}/")
    expect(page.get_by_text("Presencial", exact=True)).to_be_visible()
    expect(page.get_by_text("Registrada pel compte")).to_be_visible()
    review("sollicitud-presencial-administrador")
