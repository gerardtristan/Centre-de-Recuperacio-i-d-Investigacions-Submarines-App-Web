"""«Mètodes i mandats» al navegador (T-M05a-14; C6, A4): el tresorer veu el mètode de cada soci
actiu, la referència del mandat i l'IBAN emmascarat («…», P-121), i filtra els que no han
respost. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.models import LegalText
from apps.members.tests.test_cards import make_member
from apps.payments import mandates
from apps.payments.tests.test_preferences import card, prefer

from .conftest import PASSWORD, login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_treasurer_sees_methods_and_masked_mandates(page, live_server, transactional_db, review):
    marta = make_member("Marta", number=427, document="00000005M")
    account = Account.objects.create_personal(marta.person, "marta.prova@example.org", PASSWORD)
    text = LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")
    mandate = mandates.create_mandate(
        marta, iban="ES5500000000000000000001", holder_name="Marta Prova", holder_is_member=True,
        legal_text=text, account=account, creditor_identifier="ES00ZZZ00000000",
        evidence={"channel": "web", "text_version": 1},
    )  # fmt: skip
    prefer(marta, account, "direct_debit", mandate=mandate)
    jordi = make_member("Jordi", number=311, document="00000001R")
    prefer(jordi, account, "saved_card", saved_card=card(jordi, expiry_month=8, expiry_year=2029))
    make_member("Laia", number=502, document="00000003A")
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:payments_mandates')}")
    expect(page.get_by_role("heading", name="Mètodes i mandats")).to_be_visible()
    row = page.get_by_role("row", name="Marta Prova")
    expect(row).to_contain_text("CRIS000427M01")
    expect(row).to_contain_text("ES … 0001")
    expect(page.get_by_role("row", name="Jordi Prova")).to_contain_text("… 4242 · 08/2029")
    expect(page.get_by_role("row", name="Laia Prova")).to_contain_text("Sense resposta")
    review("metodes-i-mandats")

    page.get_by_label("Mètode").select_option(label="Sense resposta")
    page.get_by_role("button", name="Filtra").click()
    expect(page.get_by_text("1 de 3 socis actius")).to_be_visible()
    expect(page.get_by_role("row", name="Marta Prova")).to_have_count(0)
    review("metodes-i-mandats-sense-resposta")
