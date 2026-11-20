"""Disposició a l'escriptori (T-DX-57; sistema de disseny §5.3): a 1280 px les pantalles aprofiten
l'amplada; l'entrada i les pàgines d'error es queden estretes i centrades; a 390 px, com ara.
Les tasques que redistribueixen cada pantalla (T-DX-58 en endavant) hi afegeixen els seus casos."""

import re
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core import audit, charges
from apps.core.models import AccountRole, Department, LegalText, Person, Role
from apps.members.fee_rules import local_today
from apps.members.models import LicenceRecord, Member
from apps.members.tests.test_cards import make_member
from apps.payments import campaigns, mandates
from apps.treasury import services
from apps.treasury.models import TreasuryAccount
from apps.treasury.references import transfer_reference
from apps.treasury.settlements import SettlementLine
from apps.treasury.tests.test_reconciliation import lines
from apps.treasury.tests.test_record_income import new_transit
from apps.treasury.tests.test_settlements import collected, data, record_it
from conftest import PASSWORD

from .conftest import CAPTURES, SETTLED_JS, login_admin, make_admin, menu_entry
from .test_pagaments_llistat import S, attempt

pytestmark = pytest.mark.e2e

WIDTH_JS = "() => document.getElementById('contingut').getBoundingClientRect().width"
OVERFLOW_JS = "() => document.documentElement.scrollWidth - window.innerWidth"


def test_admin_lists_use_the_width_and_login_stays_narrow(page, live_server):
    base = live_server.url
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{base}/entrar/")
    assert page.evaluate(WIDTH_JS) <= 28 * 16 + 1  # cos-estret
    treasurer = make_admin("tresoreria.prova", "administrator", "treasurer")
    login_admin(page, base, treasurer.login)
    for name in ("administration:members_list", "administration:payments_list"):
        page.goto(f"{base}{reverse(name)}")
        assert page.evaluate(WIDTH_JS) > 1000, name  # abans, 960 px
        assert page.evaluate(OVERFLOW_JS) <= 0, name
    for width in (390, 320):
        page.set_viewport_size({"width": width, "height": 800})
        page.goto(f"{base}{reverse('administration:members_list')}")
        assert page.evaluate(OVERFLOW_JS) <= 0, width


GRID_JS = """(classes) => {
  const g = document.createElement('div');
  g.className = classes;
  g.innerHTML = '<p>a</p><p>b</p>';
  document.getElementById('contingut').append(g);
  const s = getComputedStyle(g);
  const out = [s.gridTemplateColumns.split(' ').length, s.columnGap];
  g.remove();
  return out;
}"""


def test_two_columns_on_tablet_and_proportions_beside_the_sidebar(page, live_server):
    """T-DX-57b: graella-2 fa dues columnes a la tauleta (el cos en fa ~42rem) i les proporcions al
    costat de la barra lateral a 1280 px; la regla dels fills del cos no li treu l'espai."""
    admin = make_admin("admin.graella", "administrator")
    login_admin(page, live_server.url, admin.login)
    page.set_viewport_size({"width": 800, "height": 900})
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    assert page.evaluate(GRID_JS, "graella-2")[0] == 2
    page.set_viewport_size({"width": 1024, "height": 900})
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    columns, gap = page.evaluate(GRID_JS, "graella-2 graella-5-7")
    assert columns == 2 and gap == "24px", (columns, gap)  # --e-5, no el --e-4 de comptes.css
    page.set_viewport_size({"width": 1280, "height": 900})  # el cos, al costat de la barra: ~59rem
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    columns, gap = page.evaluate(GRID_JS, "graella-2 graella-5-7")
    assert columns == 2 and gap == "32px", (columns, gap)  # proporcions 5/7, amb --e-6
    page.set_viewport_size({"width": 390, "height": 900})
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    assert page.evaluate(GRID_JS, "graella-2")[0] == 1


# Amplades de la columna esquerra i la dreta d'una graella (els dos primers fills).
COLUMNS_JS = """s => [...document.querySelector(s).children].slice(0, 2)
    .map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.left), r.width]; })"""


def test_member_home_layout(page, live_server, builder, member):
    """T-DX-60: la portada 7/5 i la part de baix 8/4 a l'escriptori; dues columnes iguals que no
    es toquen a la tauleta; una a sota de l'altra al mòbil; res de costat a 320 px."""


# T-DX-65: la columna principal d'un formulari i el primer element de la columna lateral (el resum
# d'Errata, si n'hi ha, o l'ajuda): [esquerra, dreta, dalt] i l'amplada de la principal.
FORM_JS = """() => {
  const g = document.querySelector('.lateral-formulari');
  const r = e => {
    const b = e.getBoundingClientRect();
    return [Math.round(b.left), Math.round(b.right), Math.round(b.top)];
  };
  const main = g.querySelector(':scope > .columna-principal');
  const side = g.querySelector(':scope > .errata') || g.querySelector(':scope > .columna-lateral');
  return [r(main), main.getBoundingClientRect().width, r(side)];
}"""
FORM_MAX = 40 * 16 + 1  # --amplada-formulari


def assert_form_layout(page, errata=False):
    """A 1280 px, la columna principal fa com a màxim 40rem i la lateral és al costat, a la mateixa
    alçada; a 390 px, una sola columna (Errata a sobre del formulari, l'ajuda a sota); res de
    costat a 320 px."""
    page.set_viewport_size({"width": 1280, "height": 900})
    main, width, side = page.evaluate(FORM_JS)
    assert width <= FORM_MAX and side[0] >= main[1] and abs(side[2] - main[2]) <= 2, (main, side)
    page.set_viewport_size({"width": 390, "height": 800})
    main, width, side = page.evaluate(FORM_JS)
    assert side[0] == main[0], (main, side)
    assert (side[2] < main[2]) if errata else (side[2] > main[2]), (main, side)
    page.set_viewport_size({"width": 320, "height": 800})
    assert page.evaluate(OVERFLOW_JS) <= 0
    page.set_viewport_size({"width": 1280, "height": 900})


def test_member_forms_and_payment_layout(page, live_server, settings, builder, member):
    """T-DX-65: el perfil i el mandat (amb errors: Errata al costat, primer al DOM i amb el focus)
    a 40rem amb la columna lateral; la pantalla de pagament, amb els passos de Tramite al costat."""
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    LegalText.objects.create(kind="sepa_mandate", version=1, content="Text del mandat (prova).")
    charge = charges.create_charge(
        member.person,
        kind="fee",
        amount_cents=9000,
        concept="Quota de prova",
        origin="proves",
        by=audit.system("proves-e2e"),
    )
    base = live_server.url
    account = builder.personal(member.person)
    page.goto(f"{base}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(builder.password)
    page.get_by_role("button", name="Entrar").click()
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{base}/")
    (left, right) = page.evaluate(COLUMNS_JS, ".inici-portada")
    assert right[0] > left[0] and abs(left[1] / right[1] - 7 / 5) < 0.1, (left, right)
    # V8 (T-DX-77): a sota, també 7/5, perquè la història comenci on comença el carnet
    (left, right) = page.evaluate(COLUMNS_JS, ".inici-graella")
    assert right[0] > left[0] and abs(left[1] / right[1] - 7 / 5) < 0.1, (left, right)
    page.set_viewport_size({"width": 800, "height": 900})
    (left, right) = page.evaluate(COLUMNS_JS, ".inici-portada")
    assert abs(left[1] - right[1]) < 2 and right[0] - (left[0] + left[1]) >= 24, (left, right)
    page.set_viewport_size({"width": 390, "height": 800})
    (left, right) = page.evaluate(COLUMNS_JS, ".inici-portada")
    assert left[0] == right[0], (left, right)  # l'una a sota de l'altra
    expect(page).not_to_have_url(re.compile("/entrar/"))

    page.goto(f"{base}{reverse('members:profile')}")
    expect(page.locator(".boto-principal")).to_have_count(1)  # D19
    assert_form_layout(page)

    page.goto(f"{base}{reverse('payments:mandate')}")
    page.get_by_role("button", name="Signa el mandat").click()
    expect(page.locator("[data-errata]")).to_be_focused()
    assert page.evaluate(
        "() => !!(document.querySelector('[data-errata]').compareDocumentPosition("
        "document.getElementById('canvia')) & Node.DOCUMENT_POSITION_FOLLOWING)"
    )
    assert_form_layout(page, errata=True)

    page.goto(f"{base}{reverse('payments:charge', args=[charge.pk])}")
    steps = page.locator("#estat-pagament > .tramite")
    expect(steps).to_be_visible()
    first = page.locator("#estat-pagament > :not(.tramite)").first
    box, pay = steps.bounding_box(), first.bounding_box()
    assert box["x"] >= pay["x"] + pay["width"] and pay["width"] <= FORM_MAX, (box, pay)
    page.set_viewport_size({"width": 390, "height": 800})
    box, pay = steps.bounding_box(), first.bounding_box()
    assert box["x"] == pay["x"] and box["y"] < pay["y"], (box, pay)  # a sobre, com abans
    page.set_viewport_size({"width": 320, "height": 800})
    assert page.evaluate(OVERFLOW_JS) <= 0


STICKY_JS = "() => getComputedStyle(document.querySelector('.taula thead th')).position"
FILTER_COLUMNS_JS = (
    "() => getComputedStyle(document.querySelector('.barra-filtres'))"
    ".gridTemplateColumns.split(' ').length"
)


def test_admin_lists_on_the_desktop(page, live_server):
    """T-DX-66 (PR 7b): els llistats de l'administració a 1280 px fan més de 1000 px, tenen els
    filtres en una fila amb els botons al costat i la capçalera de la taula fixa; la fila sencera
    porta a la fitxa (és el mateix enllaç); a 390 px la taula és apilada i a 320 no desborda."""
    for n in (1, 2, 3):
        make_member(first=f"Fila{n}", number=40 + n, document=f"0000004{n}A")
    treasurer = make_admin("tresoreria.llistats", "administrator", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.set_viewport_size({"width": 1280, "height": 900})
    for name in (
        "administration:members_list",
        "administration:fees",
        "administration:treasury_movements",
    ):
        page.goto(f"{live_server.url}{reverse(name)}")
        assert page.evaluate(WIDTH_JS) > 1000, name
        assert page.evaluate(OVERFLOW_JS) <= 0, name
        assert page.evaluate(FILTER_COLUMNS_JS) == 2, name  # els camps i, al costat, els botons
        expect(page.locator(".capcalera-pagina h1")).to_be_visible()

    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    assert page.evaluate(STICKY_JS) == "sticky"
    row = page.locator("tbody tr").filter(has_text="Fila2")
    box = row.locator("td").first.bounding_box()  # la cel·la del tipus: no és cap enllaç
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    member = Member.objects.get(member_number=42)
    expect(page).to_have_url(
        f"{live_server.url}{reverse('administration:member_detail', args=[member.pk])}"
    )

    page.set_viewport_size({"width": 390, "height": 800})
    page.goto(f"{live_server.url}{reverse('administration:members_list')}")
    assert page.evaluate(STICKY_JS) != "sticky"  # taula apilada, amb la capçalera amagada
    assert page.evaluate(FILTER_COLUMNS_JS) == 1
    expect(page.locator("tbody tr").first).to_have_css("display", "block")
    page.set_viewport_size({"width": 320, "height": 800})
    for name in ("administration:members_list", "administration:treasury_movements"):
        page.goto(f"{live_server.url}{reverse(name)}")
        assert page.evaluate(OVERFLOW_JS) <= 0, name


def test_admin_forms_layout(page, live_server, secretary, member):
    """T-DX-65: l'alta presencial (amb errors) i l'edició de les dades d'un soci, a 40rem amb la
    columna lateral a l'escriptori."""
    base = live_server.url
    login_admin(page, base, secretary.login)
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{base}{reverse('administration:join_in_person')}")
    page.get_by_role("button", name="Desa la sol·licitud").click()
    expect(page.locator("[data-errata]")).to_be_focused()
    assert_form_layout(page, errata=True)

    page.goto(f"{base}{reverse('administration:member_edit', args=[member.pk])}")
    expect(page.get_by_role("heading", level=1, name="Edita les dades")).to_be_visible()
    assert_form_layout(page)


def test_member_record_in_two_columns(page, live_server, member):
    """T-DX-67 (PR 9a): la fitxa del soci a 1280 px en dues columnes, l'esquerra més estreta (5/12)
    amb el resum, les dades i el carnet, i la dreta amb les taules; a 800 px, el resum i les dades
    al costat i les taules a tota l'amplada; a 390, una columna; a 320 no desborda. Un sol botó
    principal i «Més» s'obre amb el teclat, amb «Corregeix la data d'alta» a dins."""
    LicenceRecord.objects.create(
        member=member,
        licence_type="Anual FECDAS",
        issued_on=local_today() - timedelta(days=300),
        expires_on=local_today() + timedelta(days=40),
        source=LicenceRecord.Source.MANUAL,
    )
    admin = make_admin("fitxa.columnes", "secretary", "treasurer")
    login_admin(page, live_server.url, admin.login)
    page.set_viewport_size({"width": 1280, "height": 900})
    page.goto(f"{live_server.url}{reverse('administration:member_detail', args=[member.pk])}")
    box = {
        name: page.locator(selector).bounding_box()
        for name, selector in (
            ("resum", ".fitxa-soci > .dades-soci"),
            ("dades", "section:has(#dades-titol)"),
            ("carnet", ".fitxa-carnet"),
            ("taules", ".fitxa-taules"),
        )
    }
    assert box["resum"]["x"] == box["dades"]["x"] == box["carnet"]["x"], box
    assert box["taules"]["x"] > box["resum"]["x"] + box["resum"]["width"], box
    assert abs(box["taules"]["y"] - box["resum"]["y"]) < 2, box  # les dues columnes, a dalt
    assert box["resum"]["width"] < box["taules"]["width"], box  # 5/12 i 7/12
    assert page.evaluate(OVERFLOW_JS) <= 0
    expect(page.locator(".capcalera-pagina .boto-principal")).to_have_count(1)
    expect(page.locator(".boto-principal")).to_have_text("Edita les dades")
    expect(page.locator(".historial-estats .tramite-pas").first).to_have_class(
        "tramite-pas es-actual"
    )

    more = page.locator("summary", has_text="Més")
    more.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("link", name="Corregeix la data d'alta")).to_be_visible()
    expect(page.get_by_role("link", name="Crea una baixa")).to_be_visible()
    assert page.evaluate(OVERFLOW_JS) <= 0  # la llista s'obre cap a l'esquerra
    page.screenshot(path=CAPTURES / "fitxa-soci" / "fitxa-mes-1280.png")
    page.keyboard.press("Escape")
    expect(page.get_by_role("link", name="Corregeix la data d'alta")).to_be_hidden()
    expect(more).to_be_focused()

    page.set_viewport_size({"width": 800, "height": 900})
    resum = page.locator(".fitxa-soci > .dades-soci").bounding_box()
    dades = page.locator("section:has(#dades-titol)").bounding_box()
    taules = page.locator(".fitxa-taules").bounding_box()
    assert dades["x"] > resum["x"] and abs(dades["y"] - resum["y"]) < 2, (resum, dades)
    assert taules["x"] == resum["x"] and taules["width"] > resum["width"] * 1.8, (resum, taules)

    page.set_viewport_size({"width": 390, "height": 800})
    xs = {
        page.locator(s).bounding_box()["x"] for s in (".fitxa-soci > .dades-soci", ".fitxa-taules")
    }
    assert len(xs) == 1, xs  # l'una a sota de l'altra
    page.set_viewport_size({"width": 320, "height": 800})
    assert page.evaluate(OVERFLOW_JS) <= 0

    for width in (1280, 1024, 800, 390):
        page.set_viewport_size({"width": width, "height": 900})
        for theme in ("light", "dark"):
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            page.wait_for_function(SETTLED_JS)
            page.screenshot(
                path=CAPTURES / "fitxa-soci" / f"fitxa-{width}-{theme}.png", full_page=True
            )
    page.evaluate("document.documentElement.removeAttribute('data-theme')")


# T-DX-69 (PR 7c): pagaments i tresoreria. Cada pantalla a 1280, 1024, 390 i 320 px, en clar i en
# fosc; a 320 no desborda.
SCREEN_WIDTHS = (1280, 1024, 390, 320)
FORM_WIDTH_JS = (
    "() => document.querySelector('form.formulari:not(.barra-filtres)')"
    ".getBoundingClientRect().width"
)


def shoot_screen(page, folder, name):
    for width in SCREEN_WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        for theme in ("light", "dark"):
            page.evaluate("t => document.documentElement.setAttribute('data-theme', t)", theme)
            page.wait_for_function(SETTLED_JS)
            page.screenshot(path=CAPTURES / folder / f"{name}-{width}-{theme}.png", full_page=True)
    assert page.evaluate(OVERFLOW_JS) <= 0, name  # a 320 px, l'última amplada
    page.evaluate("document.documentElement.removeAttribute('data-theme')")
    page.set_viewport_size({"width": 1280, "height": 900})


def assert_header(page, principal=1):
    """La capçalera comuna i el nombre de botons principals de la pantalla (com a màxim un, D19)."""
    expect(page.locator(".capcalera-pagina h1")).to_be_visible()
    expect(page.locator(".boto-principal")).to_have_count(principal)


def test_payments_screens_on_the_desktop(page, live_server, transactional_db, settings):
    """T-DX-69 (PR 7c): el llistat de pagaments (capçalera i filtres en una fila), tancar un intent
    i revocar un mandat (les dades i el formulari a 40rem, amb Errata al costat) i la campanya (el
    recompte 5/12 i la invitació 7/12 a l'escriptori; al mòbil, l'un a sota de l'altre)."""
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    LegalText.objects.create(
        kind=campaigns.INVITATION_TEXT, version=1, content="Text de prova de la invitació."
    )
    text = LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")
    payer = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    attempt(payer, "Quota 2027 (prova)", S.TO_REVIEW)
    marta = make_member("Marta", number=427, document="00000005M")
    jordi = make_member("Jordi", number=311, document="00000001R")  # per convidar: «Envia…»
    Person.objects.filter(pk=jordi.person_id).update(contact_email="jordi@example.org")
    account = Account.objects.create_personal(marta.person, "marta.prova@example.org", PASSWORD)
    mandate = mandates.create_mandate(
        marta, iban="ES5500000000000000000001", holder_name="Marta Prova", holder_is_member=True,
        legal_text=text, account=account, creditor_identifier="ES00ZZZ00000000",
        evidence={"channel": "web", "text_version": 1},
    )  # fmt: skip
    treasurer = make_admin("tresoreria.escriptori", "treasurer")
    base, folder = live_server.url, "escriptori-pagaments"
    login_admin(page, base, treasurer.login)
    page.set_viewport_size({"width": 1280, "height": 900})

    page.goto(f"{base}{reverse('administration:payments_list')}")
    assert_header(page)
    assert page.evaluate(WIDTH_JS) > 1000
    assert page.evaluate(FILTER_COLUMNS_JS) == 2  # els camps i, al costat, els botons
    shoot_screen(page, folder, "pagaments")

    page.get_by_role("link", name="Tanca").click()
    page.get_by_role("button", name="Sí, tanca'l").click()
    expect(page.locator("[data-errata]")).to_be_focused()
    assert_header(page)
    assert_form_layout(page, errata=True)
    shoot_screen(page, folder, "tancar-a-revisar")

    page.goto(f"{base}{reverse('administration:payments_mandate_revoke', args=[mandate.pk])}")
    page.get_by_role("button", name="Sí, revoca'l").click()
    expect(page.locator("[data-errata]")).to_be_focused()
    assert_header(page)
    assert_form_layout(page, errata=True)
    shoot_screen(page, folder, "revoca-mandat")

    page.goto(f"{base}{reverse('administration:payments_campaign')}")
    page.get_by_label("Nom de la campanya").fill("Campanya de tardor")
    page.get_by_role("button", name="Obre la campanya").click()
    expect(page.get_by_role("status")).to_contain_text("Campanya oberta")
    assert_header(page)
    (left, right) = page.evaluate(COLUMNS_JS, ".graella-2")
    assert right[0] > left[0] and left[1] < right[1], (left, right)  # 5/12 i 7/12
    page.set_viewport_size({"width": 390, "height": 800})
    (left, right) = page.evaluate(COLUMNS_JS, ".graella-2")
    assert left[0] == right[0], (left, right)  # el recompte a sobre, com abans
    page.set_viewport_size({"width": 1280, "height": 900})
    shoot_screen(page, folder, "campanya")


def test_treasury_screens_on_the_desktop(page, live_server, transactional_db, settings):
    """T-DX-69 (PR 7c): «A revisar» i les liquidacions amb la capçalera comuna i tota l'amplada;
    tancar una liquidació amb Errata al costat; la confirmació d'una liquidació, el traspàs,
    l'arqueig, el pagament a mà i l'anul·lació amb la capçalera, el formulari a 40rem i un sol botó
    principal."""
    new_transit(settings.PAYMENTS_PROVIDER, "Trànsit del proveïdor de prova")
    payer = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    collected(payer, 9000, "REF-A")
    collected(payer, 3500, "REF-B")
    record_it()  # LIQ-001, rebuda: es pot confirmar
    collected(payer, 5000, "REF-C")
    doubt = record_it(data(SettlementLine("REF-C", 4000), external_id="LIQ-DUBTE"))
    treasurer = make_admin("tresoreria.escriptori", "treasurer")
    services.record_expense(
        TreasuryAccount.objects.get(name="Banc principal"), 4200,
        value_date=timezone.localdate(), department=Department.objects.get(name="General"),
        concept="Factura de la llum (prova)", by=treasurer,
    )  # fmt: skip
    fee = charges.create_charge(
        payer, kind="fee", amount_cents=9000, concept="Quota a mà (prova)", origin="proves",
        by=audit.system("proves-e2e"),
    )  # fmt: skip
    base, folder = live_server.url, "escriptori-tresoreria"
    login_admin(page, base, treasurer.login)
    page.set_viewport_size({"width": 1280, "height": 900})

    for name, shot in (
        ("administration:treasury_review", "a-revisar"),
        ("administration:treasury_settlements", "liquidacions"),
    ):
        page.goto(f"{base}{reverse(name)}")
        assert_header(page, principal=0)
        assert page.evaluate(WIDTH_JS) > 1000, name
        shoot_screen(page, folder, shot)

    close = reverse("administration:treasury_settlement_review_close", args=[doubt.pk])
    page.goto(f"{base}{close}")
    page.get_by_role("button", name="Sí, tanca-la").click()
    expect(page.locator("[data-errata]")).to_be_focused()
    assert_header(page)
    assert_form_layout(page, errata=True)
    shoot_screen(page, folder, "tancar-liquidacio")

    page.goto(f"{base}{reverse('administration:treasury_settlements')}")
    page.get_by_role("link", name="Confirma…").click()
    assert_header(page)
    shoot_screen(page, folder, "confirma-liquidacio")

    def transfer():
        page.get_by_label("Des del compte").select_option(label="Caixa")
        page.get_by_label("Cap al compte").select_option(label="Banc principal")
        page.get_by_label("Import (€)").fill("150,00")
        page.get_by_label("Concepte").fill("Ingrés de l'efectiu al banc")
        page.get_by_role("button", name="Revisa el traspàs").click()
        expect(page.get_by_text("Confirma el traspàs")).to_be_visible()

    def cash_count():
        page.get_by_label("Caixa").select_option(label="Caixa")
        page.get_by_label("Import comptat (€)").fill("200,00")
        page.get_by_label("Motiu de l'ajust").fill("Recompte de prova")
        page.get_by_role("button", name="Revisa l'arqueig").click()
        expect(page.get_by_text("Confirma l'arqueig")).to_be_visible()

    def manual_payment():
        page.get_by_label("Compte on entra").select_option(label="Caixa")
        page.get_by_label("Motiu").fill("Pagament en efectiu a la seu (prova)")

    def reverse_movement():
        page.get_by_role("row", name="Factura de la llum (prova)").get_by_role(
            "link", name="Anul·la…"
        ).click()
        page.get_by_label("Motiu").fill("Factura duplicada (prova)")
        page.get_by_role("button", name="Revisa l'anul·lació").click()
        expect(page.get_by_text("Confirma l'anul·lació")).to_be_visible()

    for url, shot, fill in (
        (reverse("administration:treasury_transfer"), "traspas", transfer),
        (reverse("administration:treasury_cash_count"), "arqueig", cash_count),
        (
            reverse("administration:treasury_manual_payment", args=[fee.pk]),
            "pagament-a-ma",
            manual_payment,
        ),
        (reverse("administration:treasury_movements"), "anulla", reverse_movement),
    ):
        page.goto(f"{base}{url}")
        fill()
        assert_header(page)
        assert page.evaluate(FORM_WIDTH_JS) <= FORM_MAX, shot
        shoot_screen(page, folder, shot)


# T-DX-72 (PR 9b): la conciliació, amb la taula (8/12) i el panell de la línia triada (4/12).
# T-DX-73: el concepte (2a columna) i cada càrrec (5a) que ocupen més d'una línia de text.
ONE_LINE_JS = """() => Array.from(document.querySelectorAll(
  '.conciliacio tbody td:nth-child(2), .conciliacio tbody td:nth-child(5) li'
)).filter((el) => el.offsetParent !== null).filter((el) => {
  const range = document.createRange();
  range.selectNodeContents(el);
  const tops = new Set(Array.from(range.getClientRects()).map((r) => Math.round(r.top)));
  return tops.size > 1;
}).map((el) => el.textContent.trim())"""
TABLE_WIDTH_JS = """() => document.querySelector('.conciliacio-taula').getBoundingClientRect().width
  / document.querySelector('.conciliacio').getBoundingClientRect().width"""
PANEL_COLUMNS_JS = """() => ['.conciliacio-taula', '[data-panell]'].map((s) => {
  const r = document.querySelector(s).getBoundingClientRect();
  return [r.x, r.width];
})"""


def test_reconciliation_with_the_panel_of_the_chosen_line(
    page, live_server, transactional_db, page_checks
):
    """A 1280 px, «Casa a mà…» s'obre al panell al costat de la taula (8/4) amb el focus al
    títol; la cerca, la revisió i la confirmació hi funcionen; J i K passen de línia; Esc i «Tanca»
    el tanquen i el focus torna a l'enllaç. Si ja no hi té accés, el panell ho diu. A 390 px,
    l'enllaç porta a la pàgina, com abans. Captures a 1280, 1024, 390 i 320 px, clar i fosc."""
    treasurer = make_admin("tresoreria.escriptori", "treasurer")
    payer = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")

    def charge(amount, concept):
        return charges.create_charge(
            payer, kind="fee", amount_cents=amount, concept=concept, origin="proves",
            by=audit.system("proves-e2e"),
        )  # fmt: skip

    quota, donation = charge(9000, "Quota 2026 (prova)"), charge(4000, "Sortida (prova)")
    lines(
        treasurer,
        (9000, f"TRANSF {transfer_reference(quota)} P INVENTAT"),  # 02/11, proposada
        (4000, "TRANSF SENSE REFERENCIA INVENTADA"),  # 03/11, pendent
        (2500, "TRANSF ALTRA ENTITAT INVENTADA"),  # 04/11, pendent
    )
    base, folder = live_server.url, "escriptori-conciliacio"
    login_admin(page, base, treasurer.login)
    page.set_viewport_size({"width": 1280, "height": 900})
    menu_entry(page, "Tresoreria: conciliació").click()

    title = page.get_by_role("heading", level=1)
    expect(title).to_have_text("Queden 3 línies per conciliar")
    summary = page.get_by_role("list", name="Resum de la conciliació")
    expect(summary).to_contain_text("2pendents")
    expect(summary).to_contain_text("1proposada")
    panel = page.locator("[data-panell]")
    expect(panel).to_be_hidden()  # sense cap línia oberta, la taula fa tota l'amplada (T-DX-73)
    expect(page.get_by_text("per passar de línia")).to_be_visible()
    expect(page.get_by_role("table")).to_have_attribute("aria-keyshortcuts", "J K")
    assert page.evaluate(TABLE_WIDTH_JS) > 0.95, "la taula, a tota l'amplada"
    assert page.evaluate(ONE_LINE_JS) == [], "concepte i càrrecs en una línia"
    assert page.evaluate(OVERFLOW_JS) <= 0, "sense desplaçament de costat a 1280 px"
    assert_header(page, principal=0)
    shoot_screen(page, folder, "conciliacio")

    rows = {day: page.get_by_role("row", name=f"0{day}/11/2026") for day in (2, 3, 4)}
    link = rows[3].get_by_role("link", name="Casa a mà…")
    link.click()
    expect(panel.get_by_role("heading", name="Casa la línia a mà")).to_be_focused()
    expect(panel).to_contain_text("TRANSF SENSE REFERENCIA INVENTADA")
    expect(page).to_have_url(f"{base}{reverse('administration:treasury_reconciliation')}")
    expect(rows[3]).to_have_attribute("aria-current", "true")
    (table, side) = page.evaluate(PANEL_COLUMNS_JS)
    assert side[0] >= table[0] + table[1], (table, side)  # al costat
    assert 1.9 < table[1] / side[1] < 2.1, (table, side)  # 8/12 i 4/12
    assert page.evaluate(ONE_LINE_JS) == [], "concepte en una línia, amb el panell obert"
    assert page.evaluate(OVERFLOW_JS) <= 0, "sense desplaçament de costat, amb el panell obert"
    expect(page.get_by_role("columnheader", name="Càrrecs")).to_be_hidden()
    expect(panel).to_contain_text("TRANSF SENSE REFERENCIA INVENTADA")  # el concepte sencer
    assert_header(page, principal=0)  # la cerca no és el botó principal (D19)
    shoot_screen(page, folder, "conciliacio-panell")

    page.keyboard.press("Escape")
    expect(panel).to_be_hidden()
    expect(link).to_be_focused()
    link.click()
    expect(panel.get_by_role("heading", name="Casa la línia a mà")).to_be_focused()
    panel.get_by_role("button", name="Tanca").click()
    expect(panel).to_be_hidden()
    expect(link).to_be_focused()

    page.keyboard.press("j")  # la línia següent (més antiga), la proposada: sense panell
    expect(rows[2]).to_have_attribute("aria-current", "true")
    expect(rows[2]).to_be_focused()
    page.keyboard.press("k")
    page.keyboard.press("k")
    expect(rows[4]).to_have_attribute("aria-current", "true")
    expect(rows[3]).not_to_have_attribute("aria-current", "true")
    expect(rows[4].get_by_role("link", name="Casa a mà…")).to_be_focused()
    rows[4].get_by_role("link", name="Casa a mà…").click()
    expect(panel).to_contain_text("TRANSF ALTRA ENTITAT INVENTADA")
    page.keyboard.press("j")  # amb el panell obert, J hi porta la línia següent
    expect(panel).to_contain_text("TRANSF SENSE REFERENCIA INVENTADA")
    expect(rows[3]).to_have_attribute("aria-current", "true")

    search = panel.get_by_label("Referències de transferència o números de soci")
    search.fill("CRIS-0000-0 INEXISTENT")
    panel.get_by_role("button", name="Cerca").click()
    expect(panel.get_by_text("Cap càrrec pendent amb aquesta referència")).to_be_focused()
    search.fill(transfer_reference(donation))
    search.press("Enter")  # amb la tecla, igual: el focus no es queda al camp
    expect(panel.get_by_role("group", name="Tria els càrrecs que sumen 40,00 €")).to_be_focused()
    search.fill(transfer_reference(donation))
    panel.get_by_role("button", name="Cerca").click()
    expect(panel.get_by_role("group", name="Tria els càrrecs que sumen 40,00 €")).to_be_focused()
    page.screenshot(path=CAPTURES / folder / "conciliacio-panell-cerca-1280-focus.png")
    panel.get_by_label("Sortida (prova)", exact=False).check()
    panel.get_by_role("button", name="Revisa el casament").click()
    expect(panel.get_by_text("Confirma el casament")).to_be_visible()
    expect(panel.get_by_role("heading", name="Casa la línia a mà")).to_be_focused()
    shoot_screen(page, folder, "conciliacio-panell-confirma")
    panel.get_by_role("button", name="Sí, casa-la").click()
    expect(page.get_by_role("status")).to_contain_text("Línia casada")
    expect(title).to_have_text("Queden 2 línies per conciliar")
    expect(rows[3]).to_contain_text("Conciliada")

    # Accés denegat: el panell ho diu i ofereix la pàgina; no hi encasta cap error.
    href = rows[4].get_by_role("link", name="Casa a mà…").get_attribute("href")
    page_checks.expect(404, href)  # sense T4, «no trobat» (059)
    page_checks.expect(401, href)  # amb la sessió caducada, a sota
    AccountRole.objects.filter(admin_account=treasurer).delete()
    rows[4].get_by_role("link", name="Casa a mà…").click()
    expect(panel.get_by_role("heading", name="No s'ha pogut obrir la línia")).to_be_focused()
    expect(panel.get_by_role("alert")).to_be_visible()
    shoot_screen(page, folder, "conciliacio-panell-error")
    AccountRole.objects.create(admin_account=treasurer, role=Role.objects.get(code="treasurer"))

    page.reload()
    page.set_viewport_size({"width": 390, "height": 800})
    rows[4].get_by_role("link", name="Casa a mà…").click()  # al mòbil, la pàgina a part
    expect(page.get_by_role("heading", level=1, name="Casa la línia a mà")).to_be_visible()
    expect(page).to_have_url(re.compile(r"/conciliacio/\d+/casa/$"))
    page.set_viewport_size({"width": 1280, "height": 900})
    shoot_screen(page, folder, "casa-a-ma")

    # Sessió caducada: HTMX porta tota la pàgina a l'entrada; res s'encasta al panell.
    page.goto(f"{base}{reverse('administration:treasury_reconciliation')}")
    page.context.clear_cookies()
    rows[4].get_by_role("link", name="Casa a mà…").click()
    expect(page).to_have_url(re.compile(r"/entrar/"))
