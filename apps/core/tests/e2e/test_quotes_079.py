"""«Quotes i impagats» al navegador (T-M01-18; 079, RN-M01-86 i RN-M01-91): l'estat de la quota
del llistat i el de la revisió són el mateix, i la marca d'impagat amb motiu. Les pantalles es
desen a 1280, 390 i 320 px (clar i fosc).
"""

import pytest
from django.conf import settings
from playwright.sync_api import expect

from apps.members.models import Member

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e

ADMIN = settings.ADMIN_URL_PATH


def test_fee_review_and_manual_unpaid_mark(page, live_server, builder, member, review):
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}/{ADMIN}/quotes/")
    expect(page.get_by_role("heading", name="Quotes i impagats")).to_be_visible()
    expect(page.get_by_text("Pagada fins al")).to_be_visible()
    review("quotes")

    # El mateix estat al llistat de socis (un sol càlcul).
    page.goto(f"{live_server.url}/{ADMIN}/socis/")
    expect(page.get_by_text("Pagada fins al")).to_be_visible()
    review("llistat-amb-quota")

    page.goto(f"{live_server.url}/{ADMIN}/quotes/")
    page.get_by_text("Marca impagat…").click()
    review("marca-impagat-oberta")
    # Només amb el teclat: motiu i enviar. La data ja és la d'avui i no admet futures.
    page.get_by_label("Motiu").focus()
    page.keyboard.type("Rebut retornat (prova inventada)")
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Marca com a impagat")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.get_by_text("queda marcat com a impagat")).to_be_visible()
    review("marcat-impagat")
    assert Member.objects.get(pk=member.pk).status == Member.Status.UNPAID
