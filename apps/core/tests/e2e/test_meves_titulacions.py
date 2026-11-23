"""«Les meves titulacions» al navegador (T-M02-44c; RN-M02-50): una sòcia entra a la seva àrea,
veu les seves titulacions i demana l'homologació de la PADI. Pantalles a 1280, 390 i 320 px.
Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import catalogue
from apps.activities.models import CertificationAgency, DiverCertification
from apps.activities.tests.helpers import a_member
from conftest import PASSWORD

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def test_a_member_requests_a_homologation(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    padi = CertificationAgency.objects.get(name="PADI")
    level = catalogue.create_level(by=manager, name="Open Water (inventat)", rank=10, agency=padi)
    account = a_member("Sòcia")
    account.set_password(PASSWORD)
    account.save()
    DiverCertification.objects.create(
        person=account.person, level=level, agency=padi, number="PADI-0001", source="declared"
    )

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}{reverse('activities:my_certifications')}")
    expect(page.get_by_role("heading", name="Les meves titulacions")).to_be_visible()
    page.get_by_role("button", name="Demana l'homologació").click()
    expect(page.get_by_text("Homologació demanada.")).to_be_visible()
    expect(page.get_by_role("table")).to_contain_text("Demanada")
    review("meves-titulacions")
