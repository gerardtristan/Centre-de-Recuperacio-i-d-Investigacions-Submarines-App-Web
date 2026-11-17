"""Accessibilitat de les pantalles de la tresoreria (M04) al navegador (checklist B8; ordre del
responsable del 17/11/2026, per la revisió de les portes del nivell 2).

Les mateixes comprovacions que la T-M01-28 (`test_accessibilitat_028.audit`: axe WCAG 2.0 a 2.2 A
i AA en clar i en fosc, estructura, noms accessibles i recorregut amb el tabulador), a 1280 i
390 px, amb dades inventades perquè cap taula quedi buida: comptes i saldos, moviments (ingressos
i una despesa), anul·lar un moviment, traspàs i arqueig (formulari i confirmació), liquidacions
del proveïdor i la seva confirmació, conciliació amb una línia proposada, «a revisar» (també amb
el formulari d'exclusió obert) i l'extracte bancari (importat i previsualització). L'exportació
de moviments és una descàrrega CSV, no una pantalla.

Els informes es desen a `.e2e-captures/accessibilitat/`. La revisió amb lector de pantalla i en
dispositius reals continua pendent de persona (P-301)."""

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.core import audit as core_audit
from apps.core import charges
from apps.core.models import Department, Person
from apps.treasury import services
from apps.treasury.models import TreasuryAccount
from apps.treasury.references import transfer_reference
from apps.treasury.tests.test_reconciliation import lines
from apps.treasury.tests.test_record_income import new_transit
from apps.treasury.tests.test_settlements import collected, record_it

from .conftest import login_admin, make_admin
from .test_accessibilitat_028 import audit, problems, save
from .test_extracte_bancari import CSV

pytestmark = pytest.mark.e2e

WIDTHS = (1280, 390)


def screen(page, name, results):
    """Audita la pantalla tal com és ara a cada amplada."""
    for width in WIDTHS:
        page.set_viewport_size({"width": width, "height": 900})
        audit(page, f"{name}-{width}", results)
    page.set_viewport_size({"width": WIDTHS[0], "height": 900})


def admin_url(base, name, *args):
    return f"{base}{reverse(f'administration:{name}', args=args)}"


def test_treasury_screens(page, live_server, transactional_db, settings):
    new_transit(settings.PAYMENTS_PROVIDER, "Trànsit del proveïdor de prova")
    person = Person.objects.create(first_name="Pere", last_name="Prova Inventat", origin="web")
    collected(person, 9000, "REF-A")
    collected(person, 3500, "REF-B")
    record_it()
    treasurer = make_admin("tresoreria.prova", "treasurer")
    services.record_expense(
        TreasuryAccount.objects.get(name="Banc principal"), 4200,
        value_date=timezone.localdate(), department=Department.objects.get(name="General"),
        concept="Factura de la llum (prova)", by=treasurer,
    )  # fmt: skip
    system = core_audit.system("proves-e2e")
    quotes = [
        charges.create_charge(
            person,
            kind="fee",
            amount_cents=9000,
            concept=f"Quota {n} (prova)",
            origin="proves",
            by=system,
        )  # fmt: skip
        for n in (1, 2)
    ]
    lines(
        treasurer,
        (9000, f"TRANSF {transfer_reference(quotes[0])} P INVENTAT"),  # proposada
        (9500, f"TRANSF {transfer_reference(quotes[1])} P INVENTAT"),  # a revisar
    )
    results, base = {}, live_server.url
    login_admin(page, base, treasurer.login)

    page.goto(admin_url(base, "treasury_accounts"))
    screen(page, "tresoreria-comptes", results)

    page.goto(admin_url(base, "treasury_movements"))
    screen(page, "tresoreria-moviments", results)

    page.get_by_role("row", name="Factura de la llum (prova)").get_by_role(
        "link", name="Anul·la…"
    ).click()
    screen(page, "tresoreria-anulla", results)
    page.get_by_label("Motiu").fill("Factura duplicada (prova)")
    page.get_by_role("button", name="Revisa l'anul·lació").click()
    screen(page, "tresoreria-anulla-confirma", results)

    page.goto(admin_url(base, "treasury_transfer"))
    screen(page, "tresoreria-traspas", results)
    page.get_by_label("Des del compte").select_option(label="Caixa")
    page.get_by_label("Cap al compte").select_option(label="Banc principal")
    page.get_by_label("Import (€)").fill("150,00")
    page.get_by_label("Concepte").fill("Ingrés de l'efectiu al banc")
    page.get_by_role("button", name="Revisa el traspàs").click()
    screen(page, "tresoreria-traspas-confirma", results)

    page.goto(admin_url(base, "treasury_cash_count"))
    screen(page, "tresoreria-arqueig", results)
    page.get_by_label("Caixa").select_option(label="Caixa")
    page.get_by_label("Import comptat (€)").fill("200,00")
    page.get_by_label("Motiu de l'ajust").fill("Recompte de prova")
    page.get_by_role("button", name="Revisa l'arqueig").click()
    screen(page, "tresoreria-arqueig-confirma", results)

    page.goto(admin_url(base, "treasury_settlements"))
    expect(page.get_by_text("LIQ-001")).to_be_visible()
    screen(page, "tresoreria-liquidacions", results)
    page.get_by_role("link", name="Confirma…").click()
    screen(page, "tresoreria-liquidacio-confirma", results)

    page.goto(admin_url(base, "treasury_reconciliation"))
    expect(page.get_by_role("row", name="02/11/2026")).to_contain_text("Proposada")
    screen(page, "tresoreria-conciliacio", results)

    page.goto(admin_url(base, "treasury_review"))
    expect(page.get_by_role("row", name="03/11/2026")).to_contain_text("95,00 €")
    screen(page, "tresoreria-a-revisar", results)
    page.get_by_text("Exclou…").first.click()
    audit(page, "tresoreria-a-revisar-exclou-1280", results)

    page.goto(admin_url(base, "bank_statement"))
    screen(page, "extracte-importat", results)
    page.get_by_label("Fitxer de l'extracte del banc").set_input_files(
        {"name": "extracte-inventat.csv", "mimeType": "text/csv", "buffer": CSV}
    )
    page.get_by_role("button", name="Previsualitza").click()
    screen(page, "extracte-previsualitzacio", results)

    save(results, "tresoreria")
    assert not problems(results), "\n".join(problems(results))
