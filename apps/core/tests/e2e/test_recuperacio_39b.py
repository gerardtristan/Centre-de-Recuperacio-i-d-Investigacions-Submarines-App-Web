"""«He oblidat la contrasenya» amb una cua, al navegador (T-M01-39b; Q-085): la mateixa
resposta per a un compte actiu i per a una adreça sense compte, amb la frase dels 5 minuts; el
correu surt quan la cua processa la petició. Pantalles a 1280, 390 i 320 px (clar i fosc).
Només dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.accounts import email_links
from apps.accounts.models import Account, EmailLinkRequest
from apps.core.models import OutgoingEmail, Person
from conftest import PASSWORD

pytestmark = pytest.mark.e2e

PHRASE = "Si d'aquí a 5 minuts no t'ha arribat, mira el correu brossa i torna-ho a demanar."


@pytest.fixture
def account(transactional_db):
    person = Person.objects.create(first_name="Clara", last_name="Prova Inventada", origin="web")
    account = Account.objects.create_personal(person, "clara.prova@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


def ask(page, base_url, email):
    page.goto(f"{base_url}/entrar/")
    page.get_by_role("link", name="He oblidat la contrasenya").click()
    page.get_by_label("Correu electrònic").fill(email)
    page.get_by_role("button", name="Envia'm l'enllaç").click()
    expect(page.get_by_role("status")).to_contain_text(PHRASE)
    return page.get_by_role("status").inner_text()


def test_the_same_answer_and_the_email_comes_from_the_queue(page, live_server, account, review):
    with_account = ask(page, live_server.url, "clara.prova@example.org")
    review("recuperacio-enviada")
    without = ask(page, live_server.url, "ningu.prova@example.org")
    assert with_account == without
    assert not OutgoingEmail.objects.exists()  # encara a la cua

    for request_id in EmailLinkRequest.objects.order_by("pk").values_list("pk", flat=True):
        email_links.process_password_reset(request_id)  # com el worker
    assert list(OutgoingEmail.objects.values_list("to_address", flat=True)) == [
        "clara.prova@example.org"
    ]
