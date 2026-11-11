"""Pàgines 404 i 500 pròpies al navegador (T-M01-47). Cada pantalla es desa a 1280, 390 i 320 px
(clar i fosc) i es comprova que a 320 px no es desplaça de costat. L'enllaç de tornada es fa
servir amb el teclat.
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from conftest import PASSWORD

from .conftest import login_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH
NOT_FOUND = "No s'ha trobat la pàgina"


def test_not_found_page_without_session_and_in_both_areas(
    page, live_server, page_checks, builder, member, secretary, review
):
    # Sense sessió: també sota la ruta de l'administració, sense dir que ho és.
    for path in ("/no-existeix/", f"/{ADMIN}/no-existeix/"):
        page_checks.expect(404, path)
        page.goto(f"{live_server.url}{path}")
        expect(page.get_by_role("heading", name=NOT_FOUND)).to_be_visible()
        expect(page.get_by_text("Administració")).to_have_count(0)
    review("404-sense-sessio")
    page.get_by_role("link", name="Tornar a l'inici").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Entrar a l'àrea de socis")).to_be_visible()

    # Àrea de socis: la quota d'un altre (o que no existeix) respon «no trobat».
    account = builder.personal(member.person)
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page_checks.expect(404, "/socis/quotes/987654/")
    page.goto(f"{live_server.url}/socis/quotes/987654/")
    expect(page.get_by_role("heading", name=NOT_FOUND)).to_be_visible()
    review("404-area-de-socis")
    page.context.clear_cookies()

    # Administració: un soci que no existeix; la pàgina porta a l'inici de l'administració.
    login_admin(page, live_server.url, secretary.login)
    page_checks.expect(404, f"/{ADMIN}/socis/987654/")
    page.goto(f"{live_server.url}/{ADMIN}/socis/987654/")
    expect(page.get_by_role("heading", name=NOT_FOUND)).to_be_visible()
    review("404-administracio")
    page.get_by_role("link", name="Tornar a l'administració").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Administració del C.R.I.S.")).to_be_visible()


@pytest.mark.urls("apps.core.tests.urls_errors")
def test_server_error_page(page, live_server, page_checks, transactional_db, review):
    page_checks.expect(500, "/prova-error-500/")
    page.goto(f"{live_server.url}/prova-error-500/")
    expect(page.get_by_role("heading", name="Hi ha hagut un error")).to_be_visible()
    expect(page.get_by_text("detall-intern")).to_have_count(0)
    review("500")
    page.get_by_role("link", name="Tornar a l'inici").focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Entrar a l'àrea de socis")).to_be_visible()
