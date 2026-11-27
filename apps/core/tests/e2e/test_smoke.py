"""Suite de prova ràpida al navegador (T-M00-07, CA-M00-07a a 07d): els quatre fluxos crítics.

No comprova la columna de l'estat de la quota (P-71) ni el tancament de sol·licituds (P-72).
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.members.models import MemberRequest
from conftest import PASSWORD

from . import conftest as e2e_conftest
from .conftest import login_admin, login_visitor

pytestmark = pytest.mark.e2e


def test_personal_login(page, live_server, builder, member, capture):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    capture("entrada")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page).to_have_url(f"{live_server.url}/")
    expect(page.get_by_role("button", name="Surt")).to_be_visible()
    capture("inici")


def test_admin_login_with_totp(page, live_server, secretary, capture):
    login_admin(page, live_server.url, secretary.login, capture)
    expect(page).to_have_url(f"{live_server.url}/{settings.ADMIN_URL_PATH}/")
    expect(page.get_by_role("heading", name="Administració del C.R.I.S.")).to_be_visible()
    capture("inici")


def test_join_on_the_web(page, live_server, texts, capture):
    login_visitor(page, live_server.url)  # T-M01-53: amb sessió
    expect(page.get_by_role("heading", name="Sol·licitud d'alta")).to_be_visible()
    capture("formulari")
    page.locator('[name="first_name"]').fill("Laia")
    page.locator('[name="last_name"]').fill("Dorada Rap")
    # La data torna a dibuixar la part variable (HTMX) abans de les caselles.
    with page.expect_response(lambda r: r.request.method == "POST"):
        page.locator('[name="birth_date"]').fill("1990-05-20")
        page.locator('[name="birth_date"]').dispatch_event("change")
    page.locator('[name="id_document"]').fill("12345678Z")
    page.locator('[name="contact_email"]').fill("laia.dorada@example.org")
    page.locator('[name="phone"]').fill("600 000 001")
    page.locator("label", has=page.locator('[name="membership_type"]')).first.click()
    page.locator('[name="accept_privacy"]').check()
    page.locator('[name="accept_membership_terms"]').check()
    pending = MemberRequest.objects.filter(
        kind=MemberRequest.Kind.JOIN, status=MemberRequest.Status.PENDING
    )
    before = pending.count()
    page.get_by_role("button", name="Envia la sol·licitud").click()
    expect(page.get_by_text("Sol·licitud enviada")).to_be_visible()
    capture("enviada")
    assert pending.count() == before + 1


def test_members_list_and_detail(page, live_server, secretary, member, capture):
    login_admin(page, live_server.url, secretary.login)
    page.goto(f"{live_server.url}/{settings.ADMIN_URL_PATH}/socis/")
    expect(page.get_by_role("heading", name="Llistat de socis")).to_be_visible()
    name = str(member.person)
    expect(page.get_by_role("rowheader", name=name)).to_be_visible()
    capture("llistat")
    # Nom accessible «Fitxa : <soci>» (el text amagat de la cel·la és un bloc a part).
    page.get_by_role("link", name=name).click()
    expect(page.get_by_role("heading", level=1, name=name)).to_be_visible()
    # El nom del text, no el codi intern (error trobat per aquesta suite, test_roster.py).
    expect(page.get_by_role("rowheader", name="Política de privacitat")).to_be_visible()
    capture("fitxa")


def test_first_load_is_warm(page, live_server, transactional_db):
    """P-313: la primera càrrega d'una tanda arrenca en fred el servidor i el navegador (9 s amb
    la memòria cau del disc buida, 0,3 s les següents) i, amb la màquina carregada, passava dels
    30 s de Playwright. Quan arriba la primera prova, `conftest` ja ha visitat `/entrar/` una
    vegada en aquest mateix servidor. El temps no es comprova: depèn de la càrrega."""
    assert e2e_conftest._warmed == [live_server.url]
    page.goto(f"{live_server.url}/entrar/")
    expect(page.get_by_label("Correu electrònic")).to_be_visible()
