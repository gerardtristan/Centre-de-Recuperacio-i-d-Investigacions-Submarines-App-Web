"""Fotos d'una sortida de medi ambient al navegador (T-M02-20; CA-M02-22; P-41 oberta, aquí amb
l'interruptor encès només per a la prova): la responsable puja una foto amb l'autor i el permís
d'ús, la veu a la llista i la retira amb motiu. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities import environment, environment_photos
from apps.activities.models import Activity, EnvironmentalSubtype, OutingType
from apps.activities.tests.helpers import an_outing
from apps.activities.tests.test_card_photos import JPEG
from apps.core.models import Setting

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_manager_uploads_and_retires_a_photo(
    page, live_server, transactional_db, review, tmp_path
):
    Setting.objects.filter(key=environment_photos.SWITCH).update(initial_value=True)
    manager = make_admin("cursos.prova", "courses_manager")
    outing = an_outing(
        manager, title="Neteja inventada del port",
        outing_type=OutingType.objects.get(name="Medi ambient"),
        subtype=EnvironmentalSubtype.objects.get(name="Neteja"),
    )  # fmt: skip
    Activity.objects.filter(pk=outing.pk).update(status=Activity.Status.DONE)
    environment.record_results(outing, by=manager, waste_grams=12500)
    photo = tmp_path / "foto.jpg"
    photo.write_bytes(JPEG)

    login_admin(page, live_server.url, manager.login)
    page.goto(
        f"{live_server.url}{reverse('administration:activity_environment', args=[outing.pk])}"
    )
    expect(page.get_by_role("heading", name="Fotos de la sortida")).to_be_visible()
    page.get_by_label("Foto (JPEG o PNG)").set_input_files(str(photo))
    page.get_by_label("Autor de la foto").fill("Autora Inventada")
    page.get_by_label("L'autor ha donat permís").check()
    page.get_by_role("button", name="Desa la foto").click()
    expect(page.get_by_text("Foto desada.")).to_be_visible()
    expect(page.get_by_role("cell", name="Autora Inventada")).to_be_visible()
    review("fotos-medi-ambient")
    page.get_by_label("Motiu de la retirada").fill("Foto equivocada (inventat)")
    page.get_by_role("button", name="Retira-la").click()
    expect(page.get_by_text("Foto retirada.")).to_be_visible()
    expect(page.get_by_text("Encara no hi ha cap foto.")).to_be_visible()
