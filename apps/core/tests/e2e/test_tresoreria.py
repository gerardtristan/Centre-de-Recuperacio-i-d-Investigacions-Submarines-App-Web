"""Tresoreria al navegador, primer tall de la T-M04-15 (llesca 2: «el tresorer veu el moviment i
el saldo»). Dues quotes cobrades amb targeta i apuntades amb `record_income`; el tresorer entra,
veu el saldo del trànsit i els moviments, i filtra per compte. Pantalles a 1280, 390 i 320 px
(clar i fosc). Només dades inventades.
"""

from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core import audit, charges
from apps.core.models import Person
from apps.treasury.references import transfer_reference
from apps.treasury.settlements import SettlementLine
from apps.treasury.tests.test_reconciliation import lines
from apps.treasury.tests.test_record_income import new_transit, paid, record
from apps.treasury.tests.test_settlements import collected, data, record_it

from .conftest import login_admin, make_admin, menu_entry

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


def test_treasurer_confirms_and_undoes_a_reconciliation(
    page, live_server, transactional_db, review
):
    """T-M04-15, segon tall (C5, C6): una transferència amb la referència i l'import exactes surt
    «proposada» amb el càrrec; el tresorer la confirma i després la desfà amb el motiu (045)."""
    person = Person.objects.create(first_name="Jordi", last_name="Prova Inventat", origin="web")
    quota = charges.create_charge(
        person, kind="fee", amount_cents=9000, concept="Quota 2026", origin="proves",
        by=audit.system("proves-e2e"),
    )  # fmt: skip
    treasurer = make_admin("tresoreria.prova", "treasurer")
    lines(treasurer, (9000, f"TRANSF {transfer_reference(quota)} J INVENTAT"))

    login_admin(page, live_server.url, treasurer.login)
    # Hi arriba pel menú (T-DX-44): l'entrada només surt amb T1.
    entry = menu_entry(page, "Tresoreria: conciliació")
    entry.click()
    # T-DX-72: el títol diu el que queda per conciliar (D13)
    expect(page.get_by_role("heading", level=1, name="Queda 1 línia per conciliar")).to_be_visible()
    expect(page).to_have_url(
        f"{live_server.url}{reverse('administration:treasury_reconciliation')}"
    )
    expect(entry).to_have_attribute("aria-current", "page")
    row = page.get_by_role("row", name="02/11/2026")
    expect(row).to_contain_text("J INVENTAT")
    expect(row).to_contain_text("Proposada")
    expect(row).to_contain_text("Jordi Prova Inventat")
    review("conciliacio-proposada")

    row.get_by_role("button", name="Confirma").click()
    expect(page.get_by_role("status")).to_contain_text("Conciliació confirmada")
    expect(row).to_contain_text("Conciliada")
    review("conciliacio-conciliada")

    row.get_by_text("Desfés…").click()
    row.get_by_label("Motiu per desfer-la").fill("Casada amb el càrrec equivocat (prova)")
    review("conciliacio-desfer-motiu")
    row.get_by_role("button", name="Desfés la conciliació").click()
    expect(page.get_by_role("status")).to_contain_text("Conciliació desfeta")
    # P-113 (opció per defecte): amb la mateixa referència, la línia es torna a proposar.
    expect(row).to_contain_text("Proposada")


def test_treasurer_downloads_the_csv_for_the_gestoria(
    page, live_server, transactional_db, review, page_checks
):
    """T-M04-16 (C8, T9; CA-T15.1): el tresorer filtra per compte i descarrega el CSV amb els
    mateixos filtres, en euros amb dos decimals i sense el nom de la persona."""
    transit = new_transit()
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    record(paid(person, amount=9000))
    record(paid(person, amount=3500))
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:treasury_movements')}")
    page.get_by_label("Compte").select_option(label=transit.name)
    page.get_by_role("button", name="Filtra").click()
    button = page.get_by_role("button", name="Descarrega el CSV per a la gestoria")
    expect(button).to_be_visible()
    review("moviments-exportacio")

    export = reverse("administration:treasury_export")
    page_checks.expect_download(export)  # Chromium avorta la petició quan passa a descàrrega
    with page.expect_download() as download:
        button.click()
    assert download.value.suggested_filename.startswith("moviments-")
    text = Path(download.value.path()).read_text(encoding="utf-8-sig")
    lines_ = text.splitlines()
    assert lines_[0] == "Data;Compte;Concepte;Departament;Centre de cost;Entrada;Sortida;Referència"
    assert len(lines_) == 3 and "90,00" in text and "35,00" in text
    assert "Prova Inventat" not in text


def test_treasurer_matches_a_line_by_hand(page, live_server, transactional_db, review):
    """T-M04-12e (P-M04-E pas 3; LT2): una transferència sense referència per a dues quotes;
    el tresorer busca els càrrecs per referència, en revisa la suma i la casa a mà."""
    system = audit.system("proves-e2e")
    quotes = [
        charges.create_charge(
            Person.objects.create(first_name=name, last_name="Prova Inventada", origin="web"),
            kind="fee",
            amount_cents=amount,
            concept="Quota 2026",
            origin="proves",
            by=system,
        )  # fmt: skip
        for name, amount in (("Laia", 9000), ("Pau", 3500))
    ]
    treasurer = make_admin("tresoreria.prova", "treasurer")
    lines(treasurer, (12500, "TRANSF QUOTES GERMANS INVENTATS"))

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:treasury_reconciliation')}")
    page.get_by_role("row", name="02/11/2026").get_by_role("link", name="Casa a mà…").click()
    expect(page.get_by_role("heading", name="Casa la línia a mà")).to_be_visible()
    search = " ".join(transfer_reference(quota) for quota in quotes)
    page.get_by_label("Referències de transferència o números de soci").fill(search)
    page.get_by_role("button", name="Cerca").click()
    page.get_by_label("Laia Prova Inventada").check()
    page.get_by_label("Pau Prova Inventada").check()
    review("casa-a-ma-cerca")

    page.get_by_role("button", name="Revisa el casament").click()
    expect(page.get_by_role("status")).to_contain_text("Els càrrecs sumen 125,00 €")
    review("casa-a-ma-revisio")
    page.get_by_role("button", name="Sí, casa-la").click()
    expect(page.get_by_role("status")).to_contain_text("Línia casada")
    expect(page.get_by_role("row", name="02/11/2026")).to_contain_text("Conciliada")
    review("casa-a-ma-conciliada")


def test_treasurer_sees_a_settlement_to_review(page, live_server, transactional_db, review):
    """T-M04-14b (CA-T13.1; P-191, opció per defecte): una liquidació amb un cobrament desconegut
    surt a «A revisar» amb la referència i el problema, sense cap nom, i l'enllaç porta a
    «Liquidacions»; els intents del 05b, a la llista de pagaments."""
    record_it(data(SettlementLine("REF-DESCONEGUDA", 2500), external_id="LIQ-DUBTE"))
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:treasury_review')}")
    row = page.get_by_role("row", name="LIQ-DUBTE")
    expect(row).to_contain_text("Cap cobrament amb aquesta referència")
    expect(row).to_contain_text("REF-DESCONEGUDA")
    expect(row).to_contain_text("23,80 €")
    expect(page.get_by_role("link", name="Pagaments «a revisar»")).to_be_visible()
    review("a-revisar-liquidacio")
    page.get_by_role("link", name="Revisa-les a «Liquidacions»").click()
    expect(page.get_by_role("heading", name="Liquidacions")).to_be_visible()


def test_treasurer_closes_a_settlement_to_review(page, live_server, transactional_db, review):
    """T-M04-14c (P-390, resposta B): «Tanca» porta a la confirmació; sense nota, l'error; amb la
    nota, la liquidació surt de la llista i passa a «Tancades». No es mou cap diner."""
    record_it(data(SettlementLine("REF-DESCONEGUDA", 2500), external_id="LIQ-DUBTE"))
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:treasury_review')}")
    page.get_by_role("row", name="LIQ-DUBTE").get_by_role("link", name="Tanca").click()
    expect(page.get_by_role("heading", name="Tanca una liquidació a revisar")).to_be_visible()
    page.get_by_role("button", name="Sí, tanca-la").click()
    expect(page.get_by_text("Cal una nota per tancar-la.").first).to_be_visible()
    review("tanca-liquidacio-sense-nota")
    page.get_by_label("Nota").fill("Cobrament duplicat al proveïdor, comprovat per telèfon (prova)")
    page.get_by_role("button", name="Sí, tanca-la").click()
    expect(page.get_by_role("status")).to_contain_text("Liquidació tancada")
    expect(page.get_by_text("No hi ha res a revisar.")).to_be_visible()
    expect(page.get_by_role("heading", name="Tancades")).to_be_visible()
    expect(page.get_by_role("row", name="LIQ-DUBTE")).to_contain_text("comprovat per telèfon")
    review("liquidacions-tancades")


def test_treasurer_reconciles_a_provider_settlement(page, live_server, transactional_db, review):
    """T-M04-13b (P-M04-F, passos 2 a 4): la línia del banc pel net d'una liquidació rebuda surt
    proposada amb la liquidació; el tresorer en revisa les comissions, la confirma i la desfà amb
    el motiu, i es torna a proposar."""
    new_transit()
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    collected(person, 9000, "REF-A")
    collected(person, 3500, "REF-B")
    record_it(replace(data(), settled_on=date(2026, 11, 1)))
    treasurer = make_admin("tresoreria.prova", "treasurer")
    lines(treasurer, (12380, "ABONAMENT PROVEIDOR LIQ-001"))

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:treasury_reconciliation')}")
    row = page.get_by_role("row", name="02/11/2026")
    expect(row).to_contain_text("Proposada")
    expect(row).to_contain_text("LIQ-001")
    review("conciliacio-liquidacio-proposada")

    row.get_by_role("link", name="Revisa i confirma…").click()
    expect(page.get_by_role("heading", name="Confirma la liquidació")).to_be_visible()
    expect(page.get_by_role("row", name="REF-A")).to_contain_text("0,87 €")
    review("conciliacio-liquidacio-confirma")
    page.get_by_role("button", name="Sí, confirma-la").click()
    expect(page.get_by_role("status")).to_contain_text("Liquidació conciliada")
    expect(row).to_contain_text("Conciliada")

    row.get_by_text("Desfés…").click()
    row.get_by_label("Motiu per desfer-la").fill("Casada amb una altra liquidació (prova)")
    row.get_by_role("button", name="Desfés la conciliació").click()
    expect(page.get_by_role("status")).to_contain_text("la liquidació torna a «rebuda»")
    # La mateixa parella no es torna a proposar (revisió de la #212, punt 8).
    expect(row).to_contain_text("Pendent")


def test_treasurer_chooses_between_two_settlements(page, live_server, transactional_db, review):
    """Revisió de la #212, punt 3: dues liquidacions amb el mateix net deixen la línia «a revisar»
    i el tresorer en tria una, la revisa i la confirma."""
    new_transit()
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    collected(person, 9000, "REF-A")
    collected(person, 3500, "REF-B")
    collected(person, 12500, "REF-C")
    record_it(replace(data(), settled_on=date(2026, 11, 1)))
    record_it(
        replace(
            data(SettlementLine("REF-C", 12500), external_id="LIQ-002"),
            settled_on=date(2026, 11, 1),
        )
    )
    treasurer = make_admin("tresoreria.prova", "treasurer")
    lines(treasurer, (12380, "ABONAMENT PROVEIDOR"))

    login_admin(page, live_server.url, treasurer.login)
    page.goto(f"{live_server.url}{reverse('administration:treasury_reconciliation')}")
    row = page.get_by_role("row", name="02/11/2026")
    expect(row).to_contain_text("A revisar")
    row.get_by_role("link", name="Revisa i tria…").click()
    page.get_by_label("LIQ-002").check()
    review("conciliacio-liquidacio-tria")
    page.get_by_role("button", name="Revisa aquesta liquidació").click()
    expect(page.get_by_role("row", name="REF-C")).to_contain_text("1,20 €")
    page.get_by_role("button", name="Sí, confirma-la").click()
    expect(page.get_by_role("status")).to_contain_text("Liquidació conciliada")
    expect(row).to_contain_text("LIQ-002")
