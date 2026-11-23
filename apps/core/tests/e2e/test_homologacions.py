"""Homologacions al navegador (T-M02-44b; AC25 i AC26; RN-M02-50 i 51; CA-M02-53): la secretaria
demana l'homologació d'una titulació PADI en nom d'una sòcia, la marca tramitada i feta, i la
titulació nova queda a la fitxa. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import catalogue
from apps.activities.models import CertificationAgency, DiverCertification
from apps.activities.tests.helpers import a_member

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_secretary_files_a_homologation(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    padi = CertificationAgency.objects.get(name="PADI")
    fecdas = CertificationAgency.objects.get(name="FECDAS")
    origin = catalogue.create_level(by=manager, name="Open Water (inventat)", rank=10, agency=padi)
    catalogue.create_level(by=manager, name="B1E (inventat)", rank=11, agency=fecdas)
    person = a_member("Laia").person
    DiverCertification.objects.create(
        person=person, level=origin, agency=padi, number="PADI-0001", source="declared"
    )
    secretary = make_admin("secretaria.prova", "secretary")
    login_admin(page, live_server.url, secretary.login)

    page.goto(f"{live_server.url}{reverse('administration:filings')}")
    expect(page.get_by_role("heading", name="Homologacions pendents")).to_be_visible()
    page.get_by_role("link", name="Demana una homologació").click()
    page.get_by_label("Titulació").select_option(index=1)
    page.get_by_role("button", name="Demana l'homologació").click()
    expect(page.get_by_text("Homologació demanada: ja surt a les pendents.")).to_be_visible()
    expect(page.get_by_role("table")).to_contain_text("Prova, Laia")
    review("homologacions-pendents")

    page.get_by_role("link", name=re.compile(r"^Fitxa")).click()
    page.get_by_role("button", name="Marca tramitada").click()
    expect(page.get_by_text("Homologació marcada com a tramitada.")).to_be_visible()
    page.get_by_role("button", name="Marca feta").click()
    expect(page.get_by_role("heading", name="Hi ha 3 errors")).to_be_visible()
    review("homologacio-fitxa-errors")
    page.get_by_label("Nivell de destinació").select_option(label="B1E (inventat)")
    page.get_by_label("Número de la titulació nova").fill("FED-123")
    page.get_by_label("Data").fill("2027-03-01")
    page.get_by_role("button", name="Marca feta").click()
    expect(
        page.get_by_text("Homologació feta: la titulació nova ja és a la fitxa.")
    ).to_be_visible()
    expect(page.get_by_text("Cap homologació oberta.")).to_be_visible()
