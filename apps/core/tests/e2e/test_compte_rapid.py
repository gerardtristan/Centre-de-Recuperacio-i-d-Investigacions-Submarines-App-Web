"""Compte personal ràpid (T-M01-53; decisió 108, D) al navegador: una sola pantalla amb la
casella del butlletí al capdamunt, un error de la contrasenya i la confirmació, que no diu si
el correu ja tenia compte. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.accounts.models import Account
from apps.core import consents

from .conftest import PASSWORD, make_admin

pytestmark = pytest.mark.e2e


def test_a_visitor_creates_the_account_in_one_screen(page, live_server, transactional_db, review):
    publisher = make_admin("publica.prova", "administrator")
    for kind in ("privacy", "newsletter"):
        consents.publish_text(kind, f"Text de prova: {kind}.", by=publisher)
    page.goto(f"{live_server.url}{reverse('accounts:signup')}?next=/fer-se-soci/")
    expect(page.get_by_role("heading", name="Crea el teu compte")).to_be_visible()
    page.get_by_label("Vull rebre les sortides, els cursos i les novetats del C.R.I.S.").check()
    page.get_by_label("Nom", exact=True).fill("Nura")
    page.get_by_label("Cognoms").fill("Blau Fons")
    page.get_by_label("Correu electrònic").fill("nura.blau@example.org")
    page.get_by_label("Contrasenya").fill("curta")
    page.get_by_role("button", name="Crea el compte").click()
    expect(page.get_by_role("heading", name="Hi ha 2 errors")).to_be_visible()
    review("compte-rapid-errata")
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.locator("label.casella", has_text="Accepto la").locator("input").check()
    page.get_by_role("button", name="Crea el compte").click()
    expect(page.get_by_text("Revisa el correu")).to_be_visible()
    review("compte-rapid-enviat")
    account = Account.objects.get(login="nura.blau@example.org")
    assert account.status == Account.Status.PENDING
    assert consents.has_consent(account.person, "newsletter")


def test_verifying_from_another_browser_asks_for_a_new_password(
    page, live_server, transactional_db, review
):
    """Revisió A (P-740): des d'un altre navegador, el compte només s'activa triant-hi una
    contrasenya nova."""
    from django.conf import settings as django_settings
    from django.test import Client

    from apps.accounts import email_links, tokens

    publisher = make_admin("publica.prova", "administrator")
    consents.publish_text("privacy", "Text de prova: privacy.", by=publisher)
    Client().post(
        reverse("accounts:signup"),
        {"first_name": "Nura", "last_name": "Blau", "email": "nura.blau@example.org",
         "password": PASSWORD, "accept_privacy": "on", "text_versions": "privacy:1"},
    )  # fmt: skip
    account = Account.objects.get(login="nura.blau@example.org")
    other = Client()  # un altre navegador: el testimoni a la sessió, com fa l'enllaç
    session = other.session
    session[email_links.VERIFY_SESSION_KEY] = tokens.make_token(account, tokens.VERIFY_EMAIL)
    session.save()
    name = django_settings.SESSION_COOKIE_NAME
    page.context.add_cookies(
        [{"name": name, "value": other.cookies[name].value, "url": live_server.url}]
    )
    page.goto(f"{live_server.url}{reverse('accounts:verify_email')}")
    expect(page.get_by_label("Contrasenya nova")).to_be_visible()
    review("verificacio-contrasenya-nova")
    new = "contrasenya-de-proves-1954-nova"  # noqa: S105 gitleaks:allow (dada inventada)
    page.get_by_label("Contrasenya nova").fill(new)
    page.get_by_label("Torna-la a escriure").fill(new)
    page.get_by_role("button", name="Confirmar el correu").click()
    expect(page.get_by_text("Correu confirmat")).to_be_visible()
    account.refresh_from_db()
    assert account.status == Account.Status.ACTIVE and account.check_password(new)
