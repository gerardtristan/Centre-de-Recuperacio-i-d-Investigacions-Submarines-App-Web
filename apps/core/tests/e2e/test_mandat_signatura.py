"""Signar el mandat SEPA al navegador (T-M05a-09; P-M05a-B; CA-M05a-02, 03 i 08): sense
identificador de creditor, la marca [A verificar]; amb el text d'esborrany, un IBAN amb els
dígits de control canviats o d'un país no admès (P-123) torna amb error i el camp buit; un de
vàlid, amb la contrasenya, deixa el mandat actiu amb l'IBAN emmascarat («…», P-121). Només dades
inventades."""

from pathlib import Path

import pytest
from django.conf import settings as django_settings
from django.urls import reverse
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.models import LegalText
from apps.members.tests.test_cards import make_member
from apps.payments import mandates

from .conftest import PASSWORD

pytestmark = pytest.mark.e2e

EMAIL = "marta.prova@example.org"
DRAFT = Path(django_settings.BASE_DIR) / "docs/esborranys/mandat-sepa.md"


def test_member_signs_the_mandate(page, live_server, transactional_db, settings, review):
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = ""
    settings.MANDATE_REAUTH_MINUTES = 0  # sempre demana la contrasenya: es veu el camp
    marta = make_member("Marta", number=427, document="00000005M")
    account = Account.objects.create_personal(marta.person, EMAIL, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    draft = DRAFT.read_text(encoding="utf-8").split("---", 1)[1].replace("**", "").strip()
    LegalText.objects.create(kind="sepa_mandate", version=1, content=draft)

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}{reverse('payments:mandate')}")
    expect(page.get_by_text("Encara no disponible")).to_be_visible()
    review("mandat-no-disponible")

    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    page.reload()
    expect(page.get_by_role("heading", name="Signa el mandat SEPA")).to_be_visible()
    expect(page.get_by_text("CRIS000427M01")).to_be_visible()
    page.get_by_label("IBAN").fill("ES56 0000 0000 0000 0000 0001")
    page.get_by_label("Accepto el mandat SEPA amb aquest text.").check()
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Signa el mandat").click()
    expect(page.locator("#id_iban_error")).to_contain_text("L'IBAN no és vàlid")
    expect(page.get_by_label("IBAN")).to_have_value("")
    review("mandat-iban-no-valid")

    # P-123: un IBAN vàlid d'un país que no és a la llista admesa (de bon principi, la zona SEPA).
    page.get_by_label("IBAN").fill("TR20 0000 0000 0000 0000 0000 01")
    page.get_by_label("Accepto el mandat SEPA amb aquest text.").check()
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Signa el mandat").click()
    expect(page.locator("#id_iban_error")).to_contain_text("no admet IBAN d'aquest país")
    expect(page.get_by_label("IBAN")).to_have_value("")
    review("mandat-pais-no-admes")

    page.get_by_label("IBAN").fill("ES55 0000 0000 0000 0000 0001")
    page.get_by_label("Accepto el mandat SEPA amb aquest text.").check()
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Signa el mandat").click()
    expect(page.get_by_role("status")).to_contain_text("CRIS000427M01")
    expect(page.get_by_text("ES … 0001")).to_be_visible()
    expect(page.get_by_text("0000 0000")).to_have_count(0)
    review("mandat-signat")


def test_member_revokes_the_mandate(page, live_server, transactional_db, settings, review):
    """T-M05a-10 (P-M05a-C): «Revoca el mandat…», confirmació amb la contrasenya i el mandat
    revocat; la preferència passa a «pagar cada vegada»."""
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.MANDATE_REAUTH_MINUTES = 0  # sempre demana la contrasenya: es veu el camp
    marta = make_member("Marta", number=427, document="00000005M")
    account = Account.objects.create_personal(marta.person, EMAIL, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    text = LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")
    mandates.create_mandate(
        marta, iban="ES5500000000000000000001", holder_name="Marta Prova", holder_is_member=True,
        legal_text=text, account=account, creditor_identifier="ES00ZZZ00000000",
        evidence={"channel": "web", "text_version": 1},
    )  # fmt: skip

    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.goto(f"{live_server.url}{reverse('payments:mandate')}")
    expect(page.get_by_role("link", name="Canvia l'IBAN")).to_be_visible()
    review("mandat-actiu")

    page.get_by_role("link", name="Revoca el mandat…").click()
    expect(page.get_by_role("heading", name="Revoques el mandat?")).to_be_visible()
    expect(page.get_by_text("ES … 0001")).to_be_visible()
    review("mandat-revoca")
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Sí, revoca'l").click()
    expect(page.get_by_role("status")).to_contain_text("CRIS000427M01 revocat")
    expect(page.get_by_role("link", name="Revoca el mandat…")).to_have_count(0)
    review("mandat-revocat")
