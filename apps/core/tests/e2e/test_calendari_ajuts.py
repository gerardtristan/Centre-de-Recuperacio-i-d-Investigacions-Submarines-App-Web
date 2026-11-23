"""Calendari d'ajuts al navegador (HU-M09A-03; AJ3; T-M09A-05): la junta hi veu el tancament
d'una convocatòria a les properes dates i canvia de mes amb el teclat. Pantalles a 1280, 390 i
320 px. Dades inventades."""

import datetime
import re

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.grants.models import GrantCall

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_board_sees_the_grants_calendar(page, live_server, transactional_db, review):
    board = make_admin("junta.prova", "board")
    GrantCall.objects.create(
        body="Diputació Inventada", name="Medi marí", edition_label="2027", created_by=board,
        closes_on=timezone.localdate() + datetime.timedelta(days=3),
    )  # fmt: skip
    login_admin(page, live_server.url, board.login)
    page.goto(f"{live_server.url}{reverse('administration:grants_calendar')}")
    expect(page.get_by_role("heading", name="Calendari d'ajuts")).to_be_visible()
    upcoming = page.get_by_role(
        "table", name="A partir d'avui, de la més propera a la més llunyana."
    )
    expect(upcoming).to_contain_text("Tancament de la convocatòria")
    expect(upcoming).to_contain_text("Medi marí 2027")
    review("calendari-ajuts")

    page.get_by_role("link", name="Mes següent").focus()
    page.keyboard.press("Enter")
    expect(page).to_have_url(re.compile(r"mes=\d{4}-\d{2}"))
    expect(page.get_by_role("link", name="Mes anterior")).to_be_visible()
