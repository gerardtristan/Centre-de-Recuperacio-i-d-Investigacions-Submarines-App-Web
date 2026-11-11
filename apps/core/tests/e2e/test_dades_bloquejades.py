"""Dades bloquejades al navegador (T-M00-04; M13; CA-19.3, RN-91): el tresorer obre la llista, que
només mostra la referència, i consulta una persona escrivint el motiu només amb el teclat.
Pantalles a 1280, 390 i 320 px (clar i fosc).
"""

import pytest
from playwright.sync_api import expect

from apps.core import locked_data, privacy
from apps.core.models import AuditEntry, Person

from .conftest import login_admin, make_admin

pytestmark = pytest.mark.e2e


def test_treasurer_consults_blocked_data_with_a_reason(page, live_server, member, texts, review):
    Person.objects.filter(pk=member.person_id).update(
        id_document_type="dni", id_document_number="12345678Z"
    )
    privacy.anonymise_person(Person.objects.get(pk=member.person_id), by=texts)
    ref = Person.objects.get(pk=member.person_id).anonymous_ref
    treasurer = make_admin("tresoreria.prova", "treasurer")

    login_admin(page, live_server.url, treasurer.login)
    page.get_by_role("main").get_by_role("link", name="Dades bloquejades").click()
    expect(page.get_by_role("heading", name="Dades bloquejades")).to_be_visible()
    expect(page.get_by_text("Prova Inventat")).to_have_count(0)
    review("llista")

    page.get_by_role("link", name=f"Consulta: {ref}").click()
    expect(page.get_by_text("12345678Z")).to_have_count(0)
    review("abans-del-motiu")

    page.get_by_label("Motiu de la consulta").focus()
    page.keyboard.type("Requeriment de la gestoria (prova inventada)")
    page.keyboard.press("Tab")
    page.keyboard.press("Enter")
    expect(page.get_by_text("Consulta registrada.")).to_be_visible()
    expect(page.get_by_text("DNI 12345678Z")).to_be_visible()
    review("consultades")
    assert AuditEntry.objects.filter(action=locked_data.VIEWED).count() == 1
