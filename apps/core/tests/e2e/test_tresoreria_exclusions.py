"""T-M04-14d al navegador (097, P-192 opció C; RN-T15): el tresorer exclou una línia proposada
des de la conciliació, amb motiu, i després desfà l'exclusió amb motiu: la línia torna a sortir
proposada. Pantalles a 1280, 390 i 320 px (clar i fosc). Només dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.core import audit, charges
from apps.core.models import Person
from apps.treasury.references import transfer_reference
from apps.treasury.tests.test_reconciliation import lines

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_treasurer_excludes_a_proposed_line_and_undoes_it(
    page, live_server, transactional_db, review
):
    person = Person.objects.create(first_name="Laia", last_name="Prova Inventada", origin="web")
    quota = charges.create_charge(
        person, kind="fee", amount_cents=9000, concept="Quota 2026", origin="proves",
        by=audit.system("proves-e2e"),
    )  # fmt: skip
    treasurer = make_admin("tresoreria.prova", "treasurer")
    lines(treasurer, (9000, f"TRANSF {transfer_reference(quota)} L INVENTADA"))

    login_admin(page, live_server.url, treasurer.login)
    page.locator("#barra-lateral").get_by_role("link", name="Tresoreria: conciliació").click()
    row = page.get_by_role("row", name="02/11/2026")
    expect(row).to_contain_text("Proposada")

    row.get_by_text("Exclou…").click()
    row.get_by_label("Motiu de l'exclusió").fill("Ingrés repetit pel banc (prova)")
    review("conciliacio-excloure-proposada")
    row.get_by_role("button", name="Exclou la línia").click()
    expect(page.get_by_role("status")).to_contain_text("Línia exclosa")
    expect(row).to_contain_text("Exclosa")
    expect(row.get_by_role("button", name="Confirma")).to_have_count(0)
    review("conciliacio-exclosa")

    row.get_by_text("Desfés l'exclusió…").click()
    row.get_by_label("Motiu per desfer l'exclusió").fill("Era l'ingrés bo (prova)")
    review("conciliacio-desfer-exclusio")
    row.get_by_role("button", name="Desfés l'exclusió").click()
    expect(page.get_by_role("status")).to_contain_text("Exclusió desfeta")
    expect(row).to_contain_text("Proposada")
    expect(row.get_by_role("button", name="Confirma")).to_be_visible()
