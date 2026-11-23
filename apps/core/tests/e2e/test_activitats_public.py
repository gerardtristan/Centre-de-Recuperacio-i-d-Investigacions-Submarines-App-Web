"""Pàgines públiques de les activitats al navegador (T-M02-08b): qualsevol persona veu el llistat,
filtra les sortides i obre el detall d'una, amb els enllaços per inscriure's. Pantalles a 1280,
390 i 320 px (clar i fosc). Només dades inventades."""

import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.activities.tests.helpers import an_open_course, an_open_outing

from .conftest import make_admin

pytestmark = pytest.mark.e2e


def test_anyone_lists_and_opens_an_activity(page, live_server, transactional_db, review):
    manager = make_admin("cursos.prova", "courses_manager")
    an_open_outing(
        manager, title="Sortida pública inventada", open_to_non_members=True,
        meeting_point="Port inventat",
    )  # fmt: skip
    an_open_course(manager, title="Curs públic inventat")

    page.goto(f"{live_server.url}{reverse('activities:public_list')}")
    expect(page.get_by_role("heading", name="Cursos i sortides")).to_be_visible()
    review("activitats-public-llistat")
    page.get_by_label("Classe").select_option(value="outing")
    page.get_by_role("button", name="Filtra").click()
    expect(page.get_by_text("Curs públic inventat")).to_have_count(0)
    page.get_by_role("link", name=re.compile("^Més informació")).click()
    expect(page.get_by_role("heading", name="Sortida pública inventada")).to_be_visible()
    expect(page.get_by_role("link", name="Inscriu-te sense ser soci")).to_be_visible()
    review("activitats-public-detall")
