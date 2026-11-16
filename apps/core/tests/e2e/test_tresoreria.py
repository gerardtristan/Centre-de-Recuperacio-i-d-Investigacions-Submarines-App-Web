"""Tresoreria al navegador, primer tall de la T-M04-15 (llesca 2: «el tresorer veu el moviment i
el saldo»). Dues quotes cobrades amb targeta i apuntades amb `record_income`; el tresorer entra,
veu el saldo del trànsit i els moviments, i filtra per compte. Pantalles a 1280, 390 i 320 px
(clar i fosc). Només dades inventades.
"""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core import audit, charges
from apps.core.models import Person
from apps.treasury.references import transfer_reference
from apps.treasury.tests.test_reconciliation import lines
from apps.treasury.tests.test_record_income import new_transit, paid, record

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_treasurer_sees_the_movement_and_the_balance(page, live_server, transactional_db, review):
    transit = new_transit()
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    record(paid(person, amount=9000))
    record(paid(person, amount=3500))
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    page.get_by_role("main").get_by_role("link", name="Tresoreria: comptes i saldos").click()
    expect(page.get_by_role("heading", name="Comptes i saldos")).to_be_visible()
    expect(page.get_by_role("row", name=transit.name)).to_contain_text("125,00 €")
    expect(page.get_by_role("row", name="Caixa")).to_contain_text("0,00 €")
    review("comptes-i-saldos")

    page.get_by_role("link", name="Mira els moviments").click()
    expect(page.get_by_role("heading", name="Moviments de tresoreria")).to_be_visible()
    expect(page.get_by_text("+90,00 €")).to_be_visible()
    expect(page.get_by_text("+35,00 €")).to_be_visible()
    expect(page.get_by_text("Prova Inventat")).to_have_count(0)  # el concepte no porta noms
    review("moviments")

    page.get_by_label("Compte").select_option(label="Caixa")
    page.get_by_role("button", name="Filtra").click()
    expect(page.get_by_text("Cap moviment amb aquests filtres.")).to_be_visible()
    review("moviments-filtrats")


def test_treasurer_excludes_a_line_to_review(page, live_server, transactional_db, review):
    """T-M04-14 (C6; CA-T12.1, CA-T13.1): una transferència de més surt «a revisar» amb el motiu i
    sense el concepte; el tresorer l'exclou amb motiu i la llista queda buida."""
    person = Person.objects.create(first_name="Marta", last_name="Prova Inventada", origin="web")
    quota = charges.create_charge(
        person, kind="fee", amount_cents=9000, concept="Quota", origin="proves",
        by=audit.system("proves-e2e"),
    )  # fmt: skip
    treasurer = make_admin("tresoreria.prova", "treasurer")
    lines(treasurer, (9500, f"TRANSF {transfer_reference(quota)} MARTA INVENTADA"))

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:treasury_review')}")
    expect(page.get_by_role("heading", name="A revisar")).to_be_visible()
    row = page.get_by_role("row", name="02/11/2026")
    expect(row).to_contain_text("L'import no coincideix amb el dels càrrecs")
    expect(row).to_contain_text("95,00 €")
    expect(page.get_by_text("MARTA INVENTADA")).to_have_count(0)
    review("a-revisar")

    row.get_by_text("Exclou…").click()
    row.get_by_label("Motiu de l'exclusió").fill("Transferència d'una altra entitat (prova)")
    review("a-revisar-motiu")
    row.get_by_role("button", name="Exclou la línia").click()
    expect(page.get_by_role("status")).to_contain_text("Línia exclosa")
    expect(page.get_by_text("No hi ha res a revisar.")).to_be_visible()
    review("a-revisar-buida")
