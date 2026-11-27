"""Entrar amb un enllaç pel correu, sense contrasenya (T-M01-56; decisió 108, D.3) al navegador:
demanar l'enllaç des de l'entrada, la resposta que no diu si l'adreça té compte, i el botó
«Entra» de l'enllaç. Pantalles a 1280, 390 i 320 px. Dades inventades."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.accounts import tokens
from apps.accounts.models import Account
from apps.core.models import Person

from .conftest import PASSWORD

pytestmark = pytest.mark.e2e


def test_a_member_enters_with_a_link_by_email(
    page, live_server, transactional_db, settings, review
):
    settings.PERSONAL_EMAIL_LOGIN_ENABLED = True
    person = Person.objects.create(first_name="Nura", origin=Person.Origin.WEB)
    account = Account.objects.create_personal(person, "nura.blau@example.org", PASSWORD)
    Account.objects.filter(pk=account.pk).update(status=Account.Status.ACTIVE)
    page.goto(f"{live_server.url}{reverse('accounts:login')}")
    page.get_by_role("link", name="Entra amb un enllaç pel correu").click()
    page.get_by_label("Correu electrònic").fill("nura.blau@example.org")
    page.get_by_role("button", name="Envia'm l'enllaç").click()
    expect(page.get_by_text("Si l'adreça té un compte actiu")).to_be_visible()
    review("entrada-correu-enviat")
    account.refresh_from_db()
    token = tokens.make_token(account, tokens.EMAIL_LOGIN, n="")
    page.goto(f"{live_server.url}{reverse('accounts:email_login_link', args=[token])}")
    expect(page.get_by_role("button", name="Entra")).to_be_visible()
    review("entrada-correu-boto")
    page.get_by_role("button", name="Entra").click()
    expect(page.get_by_role("button", name="Surt").first).to_be_visible()
