"""Vigencia a l'àrea del soci (T-DX-13): a «Les meves quotes», els dies que queden fins al
venciment, calculats al servidor, amb la regla."""

import re

import pytest
from playwright.sync_api import expect

from conftest import PASSWORD

pytestmark = pytest.mark.e2e


def test_member_sees_the_days_left_of_the_fee(
    page, live_server, builder, member, review, page_checks
):
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}/socis/quotes/")
    vigencia = page.locator(".vigencia")
    expect(vigencia).to_be_visible()
    expect(vigencia).to_have_class(re.compile(r"vigencia-ok"))
    expect(vigencia.locator(".vigencia-dies")).to_have_text(re.compile(r"^Queden \d+ dies$"))
    expect(vigencia.locator("svg.vigencia-regla")).to_be_visible()
    review("quotes-amb-vigencia")
