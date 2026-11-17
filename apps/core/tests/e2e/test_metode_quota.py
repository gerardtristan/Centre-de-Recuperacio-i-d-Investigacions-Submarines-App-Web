"""«Com pago la quota» al navegador (T-M05a-11; P-M05a-A; CA-M05a-01; P-134, opció per defecte).
Proveïdor fals, que guarda targetes (092): la targeta guardada surt recomanada (RN-M05a-19).
Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.core.models import LegalText
from apps.payments import mandates

from .test_carnet_079 import login_personal

pytestmark = pytest.mark.e2e


def test_member_chooses_how_to_pay_the_fee(page, live_server, builder, member, review):
    account = builder.personal(member.person)
    text = LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")
    mandate = mandates.create_mandate(
        member, iban="ES5500000000000000000001", holder_name="Pere Prova", holder_is_member=True,
        legal_text=text, account=account, creditor_identifier="ES00ZZZ00000000",
        evidence={"channel": "web", "text_version": 1},
    )  # fmt: skip
    login_personal(page, live_server.url, account)
    page.goto(f"{live_server.url}/socis/pagaments/metode/")

    expect(page.get_by_role("heading", name="Com pago la quota")).to_be_visible()
    expect(page.get_by_text("Encara no has triat com pagues la quota.")).to_be_visible()
    options = page.get_by_role("radiogroup", name="Com vols pagar-la?").get_by_role("radio")
    expect(options).to_have_count(3)
    expect(page.get_by_text("Targeta guardada (recomanada)")).to_be_visible()
    review("metode-quota")

    page.get_by_label("Domiciliació bancària").check()
    page.get_by_role("button", name="Continua").click()
    expect(page.get_by_role("status")).to_have_text("Hem desat com vols pagar la quota.")
    expect(page.get_by_text(f"(mandat {mandate.reference})")).to_be_visible()

    page.get_by_label("Pagar cada vegada").check()
    page.get_by_role("button", name="Continua").click()
    expect(page.get_by_text(f"El mandat {mandate.reference} continua actiu")).to_be_visible()
    expect(page.get_by_label("Pagar cada vegada")).to_be_checked()
    review("metode-quota-cada-vegada")
