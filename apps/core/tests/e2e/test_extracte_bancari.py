"""Extracte bancari al navegador (T-M00-01; HU-21, CA-21.1 a CA-21.4): el tresorer puja un CSV
inventat, veu la previsualització amb el número de compte tapat, exclou la línia amb error,
confirma, i després desfà la importació amb un motiu. Pantalles a 1280, 390 i 320 px (clar i
fosc). El fitxer no toca el disc: va a la pujada des de la memòria.
"""

import pytest
from playwright.sync_api import expect

from apps.core import imports

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e

CSV = "\n".join(
    [
        "Data;Concepte;Import;Saldo",
        "02/11/2026;TRANSF CRIS-AB2CD-K PROVA ES91 2100 0418 4502 0005 1332;50,00;1050,00",
        "03/11/2026;REBUT INVENTAT;-12,30;1037,70",
        "31/02/2026;DATA IMPOSSIBLE;1,00;1038,70",
    ]
).encode()


def test_treasurer_imports_and_undoes_a_statement(page, live_server, transactional_db, review):
    treasurer = make_admin("tresoreria.prova", "treasurer")
    login_admin(page, live_server.url, treasurer.login)
    page.get_by_role("main").get_by_role("link", name="Tresoreria: extracte bancari").click()
    expect(page.get_by_role("heading", name="Extracte bancari", exact=True)).to_be_visible()
    expect(page.get_by_text("Encara no s'ha importat cap extracte.")).to_be_visible()
    review("buida")

    page.get_by_label("Fitxer CSV del banc").set_input_files(
        {"name": "extracte-inventat.csv", "mimeType": "text/csv", "buffer": CSV}
    )
    page.get_by_role("button", name="Previsualitza").click()
    expect(page.get_by_role("heading", name="Previsualització")).to_be_visible()
    expect(page.get_by_text("TRANSF CRIS-AB2CD-K PROVA [número tapat]")).to_be_visible()
    expect(page.get_by_text("ES91")).to_have_count(0)
    expect(page.get_by_text("La data no és vàlida.")).to_be_visible()
    review("previsualitzacio")

    page.get_by_label("Exclou les línies amb error").check()
    page.get_by_role("button", name="Confirma la importació").click()
    expect(page.get_by_text("Extracte importat")).to_be_visible()
    assert imports.statement_lines().count() == 2
    review("importat")

    page.get_by_label("Motiu per desfer-lo").fill("Extracte equivocat (prova inventada)")
    page.get_by_role("button", name="Desfés").click()
    expect(page.get_by_text("Extracte desfet")).to_be_visible()
    assert not imports.statement_lines().exists()
    review("desfet")
