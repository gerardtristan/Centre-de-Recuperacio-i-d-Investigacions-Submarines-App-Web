"""Flux de la foto i l'homologació al navegador (T-M02-49; addenda de la 104; RN-M02-47, 48, 50 i
51): amb VC-56 encès, una sòcia puja l'anvers del carnet PADI i demana l'homologació; la secretaria
obre la fitxa, veu la foto (vista amb registre) i la marca tramitada i feta. Captures a 1280, 1024,
390 i 320 px, en clar i en fosc (amb E2E_CAPTURES_ALL=1). Només dades inventades."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import catalogue
from apps.activities.models import CertificationAgency, DiverCertification
from apps.activities.tests.helpers import a_member
from apps.activities.tests.test_card_photos import JPEG
from apps.core.audit import Action
from apps.core.models import AuditEntry, Setting, SettingVersion
from conftest import PASSWORD

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_photo_then_homologation_from_member_to_secretary(
    page, live_server, transactional_db, review, tmp_path
):
    manager = make_admin("cursos.prova", "courses_manager")
    SettingVersion.objects.create(
        setting=Setting.objects.get(key="activities.card_photos_enabled"), value=True,
        changed_by=make_admin("admin.prova", "administrator"), note="Prova.",
    )  # fmt: skip
    padi = CertificationAgency.objects.get(name="PADI")
    fecdas = CertificationAgency.objects.get(name="FECDAS")
    level = catalogue.create_level(by=manager, name="Open Water (inventat)", rank=10, agency=padi)
    catalogue.create_level(by=manager, name="B1E (inventat)", rank=11, agency=fecdas)
    account = a_member("Sòcia")
    account.set_password(PASSWORD)
    account.save()
    DiverCertification.objects.create(
        person=account.person, level=level, agency=padi, number="PADI-0001", source="declared"
    )
    photo = tmp_path / "anvers.jpg"
    photo.write_bytes(JPEG)

    # La sòcia: foto de l'anvers i petició d'homologació.
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}{reverse('activities:my_certifications')}")
    page.get_by_role("link", name=re.compile(r"^Foto del carnet")).click()
    page.get_by_label("Foto o PDF").set_input_files(photo)
    page.get_by_role("button", name="Desa la foto").click()
    page.get_by_role("button", name=re.compile(r"^Demana l'homologació")).click()
    expect(page.get_by_text("Homologació demanada.")).to_be_visible()
    review("flux-titulacions-soci")

    # La secretaria: la fitxa, la foto i la tramitació.
    page.context.clear_cookies()
    login_admin(page, live_server.url, make_admin("secretaria.prova", "secretary").login)
    page.goto(f"{live_server.url}{reverse('administration:filings')}")
    page.get_by_role("link", name=re.compile(r"^Fitxa")).click()
    page.get_by_role("link", name="Puja la foto del carnet").click()
    with page.expect_response(re.compile(r"/fitxers/")) as shown:
        page.get_by_role("link", name=re.compile(r"^Veure-la")).click()
    assert shown.value.status == 200
    assert AuditEntry.objects.filter(action=Action.FILE_OPENED).count() == 1
    page.go_back()
    review("flux-foto-secretaria")
    page.goto(f"{live_server.url}{reverse('administration:filings')}")
    page.get_by_role("link", name=re.compile(r"^Fitxa")).click()
    page.get_by_role("button", name="Marca tramitada").click()
    page.get_by_label("Nivell de destinació").select_option(label="B1E (inventat)")
    page.get_by_label("Número de la titulació nova").fill("FED-123")
    page.get_by_label("Data").fill("2027-03-01")
    page.get_by_role("button", name="Marca feta").click()
    expect(
        page.get_by_text("Homologació feta: la titulació nova ja és a la fitxa.")
    ).to_be_visible()
    review("flux-homologacio-feta")
