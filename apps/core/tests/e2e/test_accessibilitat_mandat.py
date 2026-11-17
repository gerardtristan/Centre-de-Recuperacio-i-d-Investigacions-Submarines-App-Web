"""Accessibilitat i amplades del flux de mandat (T-M05a-18; checklist B5 i B8 «N1»).

Les mateixes comprovacions que la T-M01-28 (`test_accessibilitat_028`: axe en clar i en fosc,
estructura, noms accessibles i recorregut amb el tabulador), a 1280, 390 i 320 px, per a cada
pantalla del flux: «Com pago la quota», signar el mandat (també amb errors), el mandat actiu
(«Canvia l'IBAN»), revocar-lo (també amb errors) i, a l'administració, «Mètodes i mandats», la
revocació del tresorer (també amb errors) i la campanya. A més:
- cada camp amb error porta `aria-invalid` i `aria-describedby` cap al seu missatge;
- a 320 px cap pantalla es desplaça de costat;
- sense sessió, la pantalla porta a l'entrada i hi torna després d'entrar.

El contrast de les pestanyes de la barra inferior del mòbil en fosc (`.ramillete-pestanya`, P-283)
es va corregir a la T-DX-48: ja no hi ha cap incidència coneguda.

Els informes es desen a `.e2e-captures/accessibilitat/`. Només dades inventades. El que necessita
una persona o un telèfon real és al diari de la tasca."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core.models import LegalText
from apps.members.tests.test_cards import make_member
from apps.payments import campaigns, mandates

from .conftest import PASSWORD, login_admin, make_admin
from .test_accessibilitat_028 import audit, problems, save

pytestmark = pytest.mark.e2e

EMAIL = "marta.prova@example.org"
CREDITOR = "ES00ZZZ00000000"
WIDTHS = (1280, 390, 320)

ERRORS_JS = r"""
() => [...document.querySelectorAll("[aria-invalid=true]")].map((field) => {
  const ids = (field.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean);
  const text = ids.map((id) => document.getElementById(id)?.textContent || "").join(" ").trim();
  return {name: field.name, described: text};
})
"""


@pytest.fixture
def flow(transactional_db, settings):
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = CREDITOR
    settings.MANDATE_REAUTH_MINUTES = 0  # sempre demana la contrasenya: es veu el camp
    marta = make_member("Marta", number=427, document="00000005M")
    account = Account.objects.create_personal(marta.person, EMAIL, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    text = LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")
    LegalText.objects.create(
        kind=campaigns.INVITATION_TEXT, version=1, content="Text de prova de la invitació."
    )
    return marta, account, text


def each_width(page, name, results, prepare=None):
    """Audita la pantalla a cada amplada. `prepare` la torna a l'estat que es vol (per exemple,
    enviar el formulari buit) després de canviar l'amplada."""
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        if prepare:
            prepare()
        audit(page, f"{name}-{width}", results)
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        if overflow > 0:
            results[f"{name}-{width}"]["structure"].append(f"es desplaça de costat ({overflow} px)")
    page.set_viewport_size({"width": 1280, "height": 900})


def errors_are_described(page, expected: set) -> None:
    errors = page.evaluate(ERRORS_JS)
    assert {error["name"] for error in errors} >= expected, errors
    assert all(error["described"] for error in errors), errors


def test_member_mandate_flow(page, live_server, flow):
    marta, account, text = flow
    results = {}
    base = live_server.url
    page.goto(f"{base}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()

    page.goto(f"{base}{reverse('payments:fee_method')}")
    each_width(page, "soci-com-pago", results)

    def no_choice():
        # Sense cap opció: el missatge del servidor, en català i com a alerta (no el del navegador).
        page.goto(f"{base}{reverse('payments:fee_method')}")
        page.get_by_role("button", name="Continua").click()
        expect(page.get_by_role("alert")).to_contain_text("Tria una de les opcions.")

    each_width(page, "soci-com-pago-errors", results, no_choice)

    page.goto(f"{base}{reverse('payments:mandate')}")
    each_width(page, "soci-mandat-signa", results)

    def empty_submit():
        page.goto(f"{base}{reverse('payments:mandate')}")
        page.get_by_role("button", name="Signa el mandat").click()
        expect(page.locator("[aria-invalid=true]").first).to_be_visible()

    each_width(page, "soci-mandat-errors", results, empty_submit)
    errors_are_described(page, {"iban", "accept"})

    mandates.create_mandate(
        marta, iban="ES5500000000000000000001", holder_name="Marta Prova", holder_is_member=True,
        legal_text=text, account=account, creditor_identifier=CREDITOR,
        evidence={"channel": "web", "text_version": 1},
    )  # fmt: skip
    page.goto(f"{base}{reverse('payments:mandate')}")
    expect(page.get_by_role("link", name="Canvia l'IBAN")).to_be_visible()
    each_width(page, "soci-mandat-actiu", results)

    page.goto(f"{base}{reverse('payments:mandate_revoke')}")
    each_width(page, "soci-revoca", results)

    def empty_revoke():
        page.goto(f"{base}{reverse('payments:mandate_revoke')}")
        page.get_by_role("button", name="Sí, revoca'l").click()
        expect(page.locator("[aria-invalid=true]").first).to_be_visible()

    each_width(page, "soci-revoca-errors", results, empty_revoke)
    errors_are_described(page, {"password"})

    page.goto(f"{base}{reverse('payments:fee_method')}")
    each_width(page, "soci-com-pago-amb-mandat", results)

    # Sense sessió: «Com pago la quota» porta a l'entrada i hi torna després d'entrar.
    page.context.clear_cookies()
    page.goto(f"{base}{reverse('payments:fee_method')}")
    expect(page.get_by_label("Correu electrònic")).to_be_visible()
    assert "next=/socis/pagaments/metode/" in page.url
    audit(page, "soci-sense-sessio-1280", results)

    save(results, "mandat-soci")
    assert not problems(results), "\n".join(problems(results))


def test_treasurer_mandate_screens(page, live_server, flow):
    marta, account, text = flow
    mandate = mandates.create_mandate(
        marta, iban="ES5500000000000000000001", holder_name="Marta Prova", holder_is_member=True,
        legal_text=text, account=account, creditor_identifier=CREDITOR,
        evidence={"channel": "web", "text_version": 1},
    )  # fmt: skip
    treasurer = make_admin("tresoreria.prova", "treasurer")
    results = {}
    base = live_server.url
    login_admin(page, base, treasurer.login)

    page.goto(f"{base}{reverse('administration:payments_mandates')}")
    each_width(page, "admin-mandats", results)

    revoke = reverse("administration:payments_mandate_revoke", args=[mandate.pk])
    page.goto(f"{base}{revoke}")
    each_width(page, "admin-revoca", results)

    def empty_revoke():
        page.goto(f"{base}{revoke}")
        page.get_by_role("button", name="Sí, revoca'l").click()
        expect(page.locator("#id_reason_error")).to_contain_text("Cal el motiu.")

    each_width(page, "admin-revoca-errors", results, empty_revoke)
    errors_are_described(page, {"reason"})

    page.goto(f"{base}{reverse('administration:payments_campaign')}")
    each_width(page, "admin-campanya", results)

    save(results, "mandat-administracio")
    assert not problems(results), "\n".join(problems(results))


def test_mobile_tab_bar_contrast_in_dark(page, live_server, flow):
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(EMAIL)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.set_viewport_size({"width": 390, "height": 900})
    page.goto(f"{live_server.url}{reverse('payments:fee_method')}")
    results = {}
    audit(page, "soci-com-pago-390", results)
    assert not problems(results), " | ".join(problems(results))  # P-283 (T-DX-48)
