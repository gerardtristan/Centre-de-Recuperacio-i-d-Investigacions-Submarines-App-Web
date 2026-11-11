"""«La sessió ha caducat» per inactivitat, al navegador (T-M01-45, punt 6; decisió 081, punt 22).

Es simula el que passa quan s'acaba el temps d'inactivitat de V-01: el servidor ja no té la
sessió i el navegador n'ha esborrat la galeta. La pàgina següent ha d'explicar què ha passat,
oferir tornar a entrar amb el teclat i no tornar a sortir després (cap bucle). Captures a 1280,
390 i 320 px, en clar i en fosc. Només dades inventades.
"""

import pytest
from django.conf import settings
from django.contrib.sessions.models import Session
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH
EXPIRED = "La sessió ha caducat"


def _inactivity_passes(page):
    """El servidor tanca la sessió i el navegador n'esborra la galeta, com quan s'acaba el temps
    d'inactivitat de V-01. La galeta auxiliar es queda: només diu que hi havia una sessió."""
    Session.objects.all().delete()
    page.context.clear_cookies(name=settings.SESSION_COOKIE_NAME)
    names = {cookie["name"] for cookie in page.context.cookies()}
    assert "cris_sessio_previa" in names


@pytest.fixture(autouse=True)
def _no_motion(page):
    page.emulate_media(reduced_motion="reduce")


def test_admin_session_expired_by_inactivity(page, live_server, page_checks, secretary, review):
    login_admin(page, live_server.url, secretary.login)
    expect(page.get_by_role("heading", name="Administració del C.R.I.S.")).to_be_visible()
    _inactivity_passes(page)

    path = f"/{ADMIN}/socis/"
    page_checks.expect(401, path)
    page.goto(f"{live_server.url}{path}")
    expect(page.get_by_role("heading", name=EXPIRED)).to_be_visible()
    expect(page.get_by_role("alert")).to_contain_text("Per seguretat, torna a entrar.")
    expect(page.get_by_text(secretary.login)).to_have_count(0)
    review("sessio-caducada-administracio")
    page.get_by_role("link", name="Tornar a entrar").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_label("Nom d'usuari")).to_be_visible()
    assert page.url.endswith(f"/{ADMIN}/entrar/?next=/{ADMIN}/socis/")

    # Cap bucle: tornar a la pàgina sense entrar porta a l'entrada, sense la pàgina de caducada.
    page.goto(f"{live_server.url}{path}")
    expect(page.get_by_label("Nom d'usuari")).to_be_visible()
    expect(page.get_by_role("heading", name=EXPIRED)).to_have_count(0)


def test_personal_session_expired_by_inactivity(
    page, live_server, page_checks, builder, member, review
):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/socis/perfil/")
    expect(page.get_by_role("heading", name="Les meves dades")).to_be_visible()
    _inactivity_passes(page)

    page_checks.expect(401, "/socis/perfil/")
    page.goto(f"{live_server.url}/socis/perfil/")
    expect(page.get_by_role("heading", name=EXPIRED)).to_be_visible()
    expect(page.get_by_text(account.login)).to_have_count(0)
    review("sessio-caducada-area-de-socis")
    page.get_by_role("link", name="Tornar a entrar").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_label("Correu electrònic")).to_be_visible()

    # Tornar a entrar porta a la pàgina que es volia veure.
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_role("heading", name="Les meves dades")).to_be_visible()
