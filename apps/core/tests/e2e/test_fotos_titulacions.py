"""Foto del carnet d'una titulació al navegador (T-M02-42b i T-M02-43; RN-M02-47 i 49): amb
VC-56 encès, una sòcia puja l'anvers des de «Les meves titulacions» i la secretaria el revers en
nom seu, el veu i l'esborra. Pantalles a 1280, 390 i 320 px. Només dades inventades."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import catalogue
from apps.activities.models import CertificationAgency, CertificationCardPhoto, DiverCertification
from apps.activities.tests.helpers import a_member
from apps.activities.tests.test_card_photos import JPEG
from apps.core.models import Setting, SettingVersion
from conftest import PASSWORD

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_member_and_secretary_upload_the_card_photos(
    page, live_server, transactional_db, review, tmp_path
):
    manager = make_admin("cursos.prova", "courses_manager")
    SettingVersion.objects.create(
        setting=Setting.objects.get(key="activities.card_photos_enabled"), value=True,
        changed_by=make_admin("admin.prova", "administrator"), note="Prova.",
    )  # fmt: skip
    padi = CertificationAgency.objects.get(name="PADI")
    level = catalogue.create_level(by=manager, name="Open Water (inventat)", rank=10, agency=padi)
    account = a_member("Sòcia")
    account.set_password(PASSWORD)
    account.save()
    cert = DiverCertification.objects.create(
        person=account.person, level=level, agency=padi, number="PADI-0001", source="declared"
    )
    photo = tmp_path / "carnet.jpg"
    photo.write_bytes(JPEG)

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}{reverse('activities:my_certifications')}")
    page.get_by_role("link", name="Foto del carnet").click()
    expect(page.get_by_text("No hi pugis cap document de salut.")).to_be_visible()
    review("foto-carnet-soci")
    # T-DX-117: la zona per arrossegar-hi la foto (zona-magnetica.js) diu el fitxer triat i rebutja
    # el que no és una foto ni un PDF abans d'enviar-lo (el servidor ho torna a comprovar).
    zone = page.locator("[data-zona-magnetica]")
    note = tmp_path / "nota.txt"
    note.write_text("no és una foto")
    page.get_by_label("Foto o PDF").set_input_files(note)
    expect(zone).to_have_class(re.compile("te-error"))
    expect(zone.locator(".zm-error")).to_contain_text("no és una foto ni un PDF")
    page.get_by_label("Foto o PDF").set_input_files(photo)
    expect(zone).to_have_class(re.compile("te-fitxer"))
    expect(zone.locator(".zm-resum")).to_contain_text("carnet.jpg")
    review("foto-carnet-soci-triada")
    page.get_by_role("button", name="Desa la foto").click()
    expect(page.get_by_text("Foto desada, xifrada")).to_be_visible()

    page.context.clear_cookies()
    login_admin(page, live_server.url, make_admin("secretaria.prova", "secretary").login)
    page.goto(f"{live_server.url}{reverse('administration:certification_photo', args=[cert.pk])}")
    expect(page.get_by_text("Foto pujada el")).to_be_visible()
    page.get_by_label("Cara del carnet").select_option("back")
    page.get_by_label("Foto o PDF").set_input_files(photo)
    page.get_by_role("button", name="Desa la foto").click()
    expect(page.get_by_text("Foto desada, xifrada")).to_be_visible()
    review("foto-carnet-secretaria")
    assert CertificationCardPhoto.objects.filter(certification=cert).count() == 2
    # T-M02-43: cada cara es pot veure (vista amb registre) i esborrar.
    expect(page.get_by_role("link", name=re.compile(r"^Veure-la")).first).to_be_visible()
    page.get_by_role("button", name=re.compile(r"^Esborra-la")).last.click()
    expect(page.get_by_text("Foto esborrada.")).to_be_visible()
    assert CertificationCardPhoto.objects.filter(certification=cert).count() == 1
