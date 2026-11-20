"""Guardar una targeta per a les quotes, al navegador (T-M05a-12; P-M05a-D; CA-M05a-15).
Proveïdor fals, que guarda targetes (092); només dades inventades.

El soci tria «Targeta guardada» a «Com pago la quota», va a la pàgina del proveïdor fals i en
torna: la pantalla espera la confirmació. Només quan la cua processa la notificació hi ha
targeta, amb els quatre darrers dígits i la caducitat. Després l'esborra (T-M05a-12c, P-132).
Captures a 1280, 390 i 320 px."""

import re

import pytest
from playwright.sync_api import expect

from apps.payments.models import SavedCard
from apps.payments.providers import fake

from .test_carnet_079 import login_personal
from .test_flux_primer_euro import run_queue

pytestmark = pytest.mark.e2e


def test_member_saves_a_card_for_the_fee(page, live_server, settings, builder, member, review):
    settings.PUBLIC_SITE_URL = live_server.url  # on torna el navegador i on arriba l'avís
    fake.reset()
    login_personal(page, live_server.url, builder.personal(member.person))
    page.goto(f"{live_server.url}/socis/pagaments/metode/")
    page.get_by_label("Targeta guardada").check()
    page.get_by_role("button", name="Continua").click()

    expect(page.get_by_role("heading", level=1, name="Targeta per a la quota")).to_be_visible()
    expect(page.locator("main input:not([type=hidden])")).to_have_count(0)  # cap camp de targeta
    review("targeta-sense")

    page.get_by_role("button", name="Guarda la targeta").click()
    expect(page.get_by_role("heading", name="Pagament de proves")).to_be_visible()
    page.get_by_role("button", name="Paga", exact=True).click()
    expect(page).to_have_url(re.compile(r"\?tornada=ok$"))
    expect(page.get_by_role("status")).to_contain_text("Estem confirmant la targeta")
    assert not SavedCard.objects.exists()  # mai pel navegador
    review("targeta-esperant")

    assert run_queue() == ["processed"]
    page.goto(f"{live_server.url}/socis/pagaments/targeta/")
    expect(page.get_by_text("… 4242")).to_be_visible()
    expect(page.get_by_role("heading", name="Guarda una targeta nova")).to_be_visible()
    review("targeta-guardada")
    expect(page.locator('.ramillete-lateral [aria-current="page"]')).to_have_text(
        "Com pago la quota"
    )  # T-DX-76

    page.goto(f"{live_server.url}/socis/pagaments/metode/")
    expect(page.get_by_text("targeta guardada acabada en 4242")).to_be_visible()

    # T-M05a-12c (P-132): esborrar-la, com revocar el mandat; la sessió és recent.
    page.goto(f"{live_server.url}/socis/pagaments/targeta/")
    page.get_by_role("link", name="Esborra la targeta…").click()
    expect(page.get_by_role("heading", name="Esborres la targeta?")).to_be_visible()
    review("targeta-esborrar")
    page.get_by_role("button", name="Sí, esborra-la").click()
    expect(page.get_by_text("Targeta acabada en 4242 esborrada.")).to_be_visible()
    assert SavedCard.objects.get().status == SavedCard.Status.REMOVED
    review("targeta-esborrada")
    fake.reset()
