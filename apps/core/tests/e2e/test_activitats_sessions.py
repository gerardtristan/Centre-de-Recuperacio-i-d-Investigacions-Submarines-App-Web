"""Sessions i programa al navegador (T-M02-06c2 i 06c4): el responsable afegeix una sessió de
piscina a un curs, n'allarga l'horari i afegeix un bloc al programa d'una sortida des de la fitxa.
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities.models import Session
from apps.activities.tests.helpers import a_place, an_open_course, an_outing

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_manager_adds_a_session_and_a_block(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    course = an_open_course(manager, title="Curs inventat amb sessions")
    a_place(manager)
    outing = an_outing(manager, title="Sortida inventada amb programa")
    login_admin(page, live_server.url, manager.login)

    page.goto(f"{live_server.url}{reverse('administration:activity_detail', args=[course.pk])}")
    page.get_by_text("Afegeix una sessió").click()
    page.get_by_label("Classe").select_option(label="Piscina")
    page.get_by_label("Comença").fill("2027-06-14T09:00")
    page.get_by_label("Acaba").fill("2027-06-14T11:00")
    page.locator("#id_sessio-place").select_option(index=1)
    page.get_by_role("button", name="Afegeix la sessió").click()
    expect(page.get_by_role("rowheader", name="Piscina")).to_be_visible()
    review("activitat-sessio")
    session = Session.objects.get()
    page.get_by_text("Canvia la sessió").click()
    page.locator(f"#id_sessio-{session.pk}-ends_at").fill("2027-06-14T12:00")
    page.get_by_role("button", name="Desa els canvis").click()
    expect(page.get_by_text("14/06/2027 09:00 – 12:00")).to_be_visible()
    review("activitat-sessio-canviada")

    page.goto(f"{live_server.url}{reverse('administration:activity_detail', args=[outing.pk])}")
    page.get_by_text("Afegeix un bloc al programa").click()
    page.get_by_label("Hora d'inici").fill("09:00")
    page.get_by_label("Què s'hi fa").fill("Briefing inventat")
    page.get_by_label("Qui se n'encarrega (una funció)").fill("Cap d'immersió")
    page.get_by_role("button", name="Afegeix el bloc").click()
    expect(page.get_by_role("cell", name="Briefing inventat", exact=True)).to_be_visible()
    review("activitat-programa")
