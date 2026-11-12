"""Data de naixement que falta, al navegador (T-M01-35; RN-M01-55, CA-M01-43): l'avís a l'inici
i el camp al perfil, completat només amb el teclat. Pantalles a 1280, 390 i 320 px (clar i fosc).
"""

import pytest
from playwright.sync_api import expect

from apps.core.models import Person
from conftest import PASSWORD

pytestmark = pytest.mark.e2e


def test_member_without_birth_date_completes_it(page, live_server, builder, member, review):
    Person.objects.filter(pk=member.person_id).update(birth_date=None)
    account = builder.personal(member.person)
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    expect(page.get_by_text("Falta la teva data de naixement")).to_be_visible()
    review("inici-avis")

    page.get_by_role("link", name="Completa-la al teu perfil").click()
    expect(page.get_by_role("heading", name="Falta la teva data de naixement")).to_be_visible()
    review("perfil-naixement")
    page.get_by_role("textbox", name="Data de naixement").focus()
    page.keyboard.type("12041985")
    # El camp de data té subcamps (dia, mes i any) i el Tab hi navega per dins: s'envia amb Intro.
    page.keyboard.press("Enter")
    expect(page.get_by_text("Data de naixement desada.")).to_be_visible()
    expect(page.get_by_role("heading", name="Falta la teva data de naixement")).to_be_hidden()
    review("perfil-naixement-desada")
    assert Person.objects.get(pk=member.person_id).birth_date is not None
