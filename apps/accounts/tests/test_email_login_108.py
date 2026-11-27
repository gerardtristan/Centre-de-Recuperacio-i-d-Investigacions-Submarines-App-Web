"""Entrar al compte personal amb un enllaç d'un sol ús pel correu, sense contrasenya (T-M01-56;
decisió 108, D.3): apagat per defecte; la mateixa resposta per a qualsevol adreça; només comptes
personals actius; obrir l'enllaç no fa res; 15 minuts i un sol ús; amb doble factor, el codi;
la petició no busca el compte (la cua envia). I els errors de la contrasenya en català a la
contrasenya nova. Només dades inventades."""

import dataclasses
from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts import email_links, tokens
from apps.accounts.forms import NewPasswordForm
from apps.accounts.models import Account, EmailLinkRequest
from apps.core.models import AuditEntry, OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_join import strip_tokens
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
REQUEST = reverse("accounts:email_login_request")
CONFIRM = reverse("accounts:email_login")
EMAIL = "nura.blau@example.org"


@pytest.fixture
def enabled(settings):
    settings.PERSONAL_EMAIL_LOGIN_ENABLED = True


@pytest.fixture
def account(db):
    person = Person.objects.create(first_name="Nura", origin=Person.Origin.WEB)
    account = Account.objects.create_personal(person, EMAIL, PASSWORD)
    Account.objects.filter(pk=account.pk).update(status=Account.Status.ACTIVE)
    account.refresh_from_db()
    return account


def _token(account):
    return tokens.make_token(account, tokens.EMAIL_LOGIN)


def _process_all():
    rows = EmailLinkRequest.objects.filter(purpose=EmailLinkRequest.Purpose.EMAIL_LOGIN)
    for row in rows.order_by("pk"):
        email_links.process_email_login(row.pk)


def _enter(client, token):
    client.get(reverse("accounts:email_login_link", args=[token]))
    return client.post(CONFIRM)


def test_switched_off_every_route_is_not_found(account):
    client = Client()
    assert client.get(REQUEST).status_code == 404
    assert client.post(REQUEST, {"email": EMAIL}).status_code == 404
    assert (
        client.get(reverse("accounts:email_login_link", args=[_token(account)])).status_code == 404
    )
    assert client.post(CONFIRM).status_code == 404
    assert "/entrar/correu/" not in Client().get(reverse("accounts:login")).content.decode()


def test_the_answer_is_the_same_for_any_address_and_only_an_active_account_gets_the_link(
    enabled, account
):
    pages = []
    for email in (EMAIL, "ningu@example.org"):
        client = Client()
        assert client.post(REQUEST, {"email": email})["Location"] == REQUEST
        pages.append(client.get(REQUEST).content.decode())
    assert strip_tokens(pages[0]) == strip_tokens(pages[1])
    _process_all()
    assert OutgoingEmail.objects.filter(template=email_links.LOGIN_TEMPLATE).count() == 1
    assert OutgoingEmail.objects.get(template=email_links.LOGIN_TEMPLATE).to_address == EMAIL


def test_a_pending_account_or_an_admin_username_gets_nothing(enabled, account, make_admin):  # noqa: F811
    Account.objects.filter(pk=account.pk).update(status=Account.Status.PENDING)
    admin = make_admin("administrator")
    for value in (EMAIL, admin.login, f"{admin.login}@example.org"):
        Client().post(REQUEST, {"email": value})
    _process_all()
    assert not OutgoingEmail.objects.filter(template=email_links.LOGIN_TEMPLATE).exists()


def test_opening_the_link_does_nothing_and_the_button_logs_in_once(enabled, account):
    client = Client()
    token = _token(account)
    client.get(reverse("accounts:email_login_link", args=[token]))
    assert "_auth_user_id" not in client.session  # obrir-lo no entra
    response = client.post(CONFIRM)
    assert response["Location"] == reverse("core:home")
    assert int(client.session["_auth_user_id"]) == account.pk
    assert AuditEntry.objects.filter(action="auth.email_login_used", actor_account=account).exists()
    again = Client()
    assert _enter(again, token).status_code == 200  # un sol ús
    assert "_auth_user_id" not in again.session


def test_an_expired_link_does_not_log_in(enabled, account, monkeypatch):
    token = _token(account)
    expired = dataclasses.replace(tokens.EMAIL_LOGIN, max_age=timedelta(seconds=-1))
    monkeypatch.setattr(tokens, "EMAIL_LOGIN", expired)
    client = Client()
    assert _enter(client, token).status_code == 200
    assert "_auth_user_id" not in client.session


def test_with_totp_the_code_is_still_asked(enabled, account, monkeypatch):
    monkeypatch.setattr(Account, "has_totp", property(lambda self: True))
    client = Client()
    response = _enter(client, _token(account))
    assert response["Location"] == reverse("accounts:login_totp")
    assert "_auth_user_id" not in client.session


def test_a_locked_account_does_not_log_in(enabled, account):
    Account.objects.filter(pk=account.pk).update(locked_until=timezone.now() + timedelta(hours=1))
    client = Client()
    assert _enter(client, _token(account)).status_code == 200
    assert "_auth_user_id" not in client.session


def test_the_origin_limit_is_shared_with_the_other_email_links(enabled, account):
    for _ in range(10):
        EmailLinkRequest.objects.create(ip_address="127.0.0.1", purpose="reset")
    Client().post(REQUEST, {"email": EMAIL})
    _process_all()
    assert not OutgoingEmail.objects.filter(template=email_links.LOGIN_TEMPLATE).exists()


def test_new_password_errors_are_in_catalan(account):
    form = NewPasswordForm(account, {"new_password1": "curta", "new_password2": "curta"})
    assert not form.is_valid()
    assert "La contrasenya és massa curta" in str(form.errors)


# --- Revisió independent (28/11/2026) -------------------------------------------------------


def test_the_request_does_the_same_work_for_any_address_and_the_queue_sends(enabled, account):
    """Revisió G: la petició només desa una fila pendent amb l'empremta (no busca el compte); la
    tasca de la cua envia l'enllaç només a un compte personal actiu."""
    for email in (EMAIL, "ningu@example.org"):
        Client().post(REQUEST, {"email": email})
    rows = EmailLinkRequest.objects.filter(purpose=EmailLinkRequest.Purpose.EMAIL_LOGIN)
    assert [r.status for r in rows] == [EmailLinkRequest.Status.PENDING] * 2
    assert not OutgoingEmail.objects.filter(template=email_links.LOGIN_TEMPLATE).exists()
    results = [email_links.process_email_login(r.pk) for r in rows.order_by("pk")]
    assert results == [EmailLinkRequest.Status.SENT, EmailLinkRequest.Status.NOT_SENT]
    assert OutgoingEmail.objects.get(template=email_links.LOGIN_TEMPLATE).to_address == EMAIL


def test_an_open_session_is_never_replaced_and_the_account_is_shown_masked(
    enabled,
    account,
    make_admin,  # noqa: F811
):
    """Revisió H: amb una sessió oberta, l'enllaç no entra; a «Entra», el correu emmascarat."""
    client = Client()
    client.get(reverse("accounts:email_login_link", args=[_token(account)]))
    assert "n***@example.org" in client.get(CONFIRM).content.decode()
    other = Person.objects.create(first_name="Altra", origin=Person.Origin.WEB)
    signed = Account.objects.create_personal(other, "altra@example.org", PASSWORD)
    Account.objects.filter(pk=signed.pk).update(status=Account.Status.ACTIVE)
    signed.refresh_from_db()
    client.force_login(signed)
    client.get(reverse("accounts:email_login_link", args=[_token(account)]))
    client.post(CONFIRM)
    assert int(client.session["_auth_user_id"]) == signed.pk
