"""Activitats destacades al navegador (T-M07-29; RN-M07-21; CA-M07-30): el President en destaca
dues des del selector, en canvia l'ordre i en treu una. Sense entrada de menú (DISSENY): s'hi va
per l'adreça. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.activities.models import Activity
from apps.activities.tests.helpers import an_outing
from apps.website.models import FeaturedActivity

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_the_president_picks_and_orders_featured_activities(
    page, live_server, transactional_db, review
):
    manager = make_admin("cursos.destacades", "courses_manager")
    for title in ("Sortida a les Medes (inventada)", "Curs de nit (inventat)"):
        outing = an_outing(manager, title=title)
        Activity.objects.filter(pk=outing.pk).update(
            status=Activity.Status.OPEN, published_at=timezone.now()
        )
    login_admin(page, live_server.url, make_admin("presidencia.destacades", "president").login)
    page.goto(f"{live_server.url}{reverse('administration:website_featured')}")
    expect(page.get_by_role("heading", name="Activitats destacades", level=1)).to_be_visible()
    review("destacades-buit")
    for title in ("Sortida a les Medes (inventada)", "Curs de nit (inventat)"):
        page.locator("#id_activity").select_option(label=f"{title} · 14/06/2027")
        page.get_by_role("button", name="Destaca-la").click()
        expect(page.get_by_text("Activitat destacada.")).to_be_visible()
    review("destacades-dues")
    page.get_by_role("row", name="Curs de nit").get_by_role("button", name="Puja").click()
    rows = page.locator("tbody th")
    expect(rows.first).to_have_text("Curs de nit (inventat)")
    page.get_by_role("row", name="Sortida a les Medes").get_by_role(
        "button", name="Treu-la"
    ).click()
    expect(page.get_by_text("Ja no és destacada.")).to_be_visible()
    review("destacades-una")
    assert FeaturedActivity.objects.count() == 1
