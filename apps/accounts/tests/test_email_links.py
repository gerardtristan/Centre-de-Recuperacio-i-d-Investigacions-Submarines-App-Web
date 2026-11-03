"""Enllaços d'un sol ús i verificació del correu del compte personal (spec 00, HU-04, RN-18;
CA-04.2; CK C5). Només dades inventades.
"""

import logging
import re
import time

import pytest
from django.core import mail as django_mail
from django.core import signing
from django.urls import reverse
from django.utils.html import escape

from apps.accounts import email_links, tokens
from apps.accounts.models import Account
from apps.accounts.security import PENDING_ERROR
from apps.core import audit, mail
from apps.core.models import AuditEntry, OutgoingEmail
from conftest import PASSWORD

pytestmark = pytest.mark.django_db


@pytest.fixture
def pending_account(make_person):
    return Account.objects.create_personal(make_person(), "anna@example.org", PASSWORD)


def queued_link(account) -> str:
    """L'enllaç del darrer correu a la cua de l'adreça, com el rebria la persona."""
    email = OutgoingEmail.objects.filter(to_address=account.login).latest("pk")
    return re.search(r"https?://\S+", email.body_text).group(0)


def path_of(link: str) -> str:
    return "/" + link.split("://", 1)[1].split("/", 1)[1]


def token_of(link: str) -> str:
    return path_of(link).rstrip("/").rsplit("/", 1)[1]


def token_made_hours_ago(monkeypatch, account, purpose, hours):
    past = time.time() - hours * 3600
    with monkeypatch.context() as patch:
        patch.setattr(signing.time, "time", lambda: past)
        return tokens.make_token(account, purpose)


class TestTokens:
    def test_purposes_are_not_interchangeable(self, pending_account):
        verify = tokens.make_token(pending_account, tokens.VERIFY_EMAIL)
        reset = tokens.make_token(pending_account, tokens.RESET_PASSWORD)
        assert tokens.account_for_token(verify, tokens.VERIFY_EMAIL) == pending_account
        assert tokens.account_for_token(reset, tokens.RESET_PASSWORD) == pending_account
        assert tokens.account_for_token(verify, tokens.RESET_PASSWORD) is None
        assert tokens.account_for_token(reset, tokens.VERIFY_EMAIL) is None

    @pytest.mark.parametrize("token", ["", "x", "a:b:c", "eyJhIjoxfQ:1abc:ZmFsc2U"])
    def test_garbage_is_rejected(self, pending_account, token):
        assert tokens.account_for_token(token, tokens.VERIFY_EMAIL) is None

    def test_tampered_token_is_rejected(self, pending_account):
        token = tokens.make_token(pending_account, tokens.VERIFY_EMAIL)
        tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
        assert tokens.account_for_token(tampered, tokens.VERIFY_EMAIL) is None

    def test_verification_expires_after_48_hours(self, monkeypatch, pending_account):
        # V-01
        fresh = token_made_hours_ago(monkeypatch, pending_account, tokens.VERIFY_EMAIL, 47.9)
        old = token_made_hours_ago(monkeypatch, pending_account, tokens.VERIFY_EMAIL, 48.1)
        assert tokens.account_for_token(fresh, tokens.VERIFY_EMAIL) == pending_account
        assert tokens.account_for_token(old, tokens.VERIFY_EMAIL) is None

    def test_reset_expires_after_one_hour(self, monkeypatch, personal_account):
        # V-01
        fresh = token_made_hours_ago(monkeypatch, personal_account, tokens.RESET_PASSWORD, 0.9)
        old = token_made_hours_ago(monkeypatch, personal_account, tokens.RESET_PASSWORD, 1.1)
        assert tokens.account_for_token(fresh, tokens.RESET_PASSWORD) == personal_account
        assert tokens.account_for_token(old, tokens.RESET_PASSWORD) is None

    def test_admin_accounts_never_match(self, admin_account):
        # RN-16 i RN-19: cap enllaç per correu per als comptes d'administrador.
        for purpose in (tokens.VERIFY_EMAIL, tokens.RESET_PASSWORD):
            token = tokens.make_token(admin_account, purpose)
            assert tokens.account_for_token(token, purpose) is None

    def test_verification_dies_when_the_state_changes(self, pending_account):
        token = tokens.make_token(pending_account, tokens.VERIFY_EMAIL)
        pending_account.status = Account.Status.DISABLED
        pending_account.save()
        assert tokens.account_for_token(token, tokens.VERIFY_EMAIL) is None

    def test_verification_dies_when_the_email_changes(self, pending_account):
        token = tokens.make_token(pending_account, tokens.VERIFY_EMAIL)
        pending_account.login = "anna.nova@example.org"
        pending_account.save()
        assert tokens.account_for_token(token, tokens.VERIFY_EMAIL) is None

    def test_reset_dies_when_the_password_changes(self, personal_account):
        token = tokens.make_token(personal_account, tokens.RESET_PASSWORD)
        personal_account.set_password(f"{PASSWORD}-altra")
        personal_account.save()
        assert tokens.account_for_token(token, tokens.RESET_PASSWORD) is None

    def test_reset_dies_after_a_new_login(self, client, personal_account):
        token = tokens.make_token(personal_account, tokens.RESET_PASSWORD)
        client.post(reverse("accounts:login"), {"login": "anna@example.org", "password": PASSWORD})
        assert tokens.account_for_token(token, tokens.RESET_PASSWORD) is None

    def test_a_new_token_does_not_kill_the_previous_one(self, pending_account):
        # Documentat a `tokens`: sense estat desat, tots dos valen fins que se'n fa servir un.
        first = tokens.make_token(pending_account, tokens.VERIFY_EMAIL)
        second = tokens.make_token(pending_account, tokens.VERIFY_EMAIL)
        assert tokens.account_for_token(first, tokens.VERIFY_EMAIL) == pending_account
        email_links.confirm_email(second)
        assert tokens.account_for_token(first, tokens.VERIFY_EMAIL) is None


class TestSendVerification:
    def test_queues_a_link_for_a_pending_account(self, pending_account):
        assert email_links.send_verification(pending_account) is True
        email = OutgoingEmail.objects.get(to_address="anna@example.org")
        assert email.template == "verificacio-correu"
        link = queued_link(pending_account)
        assert path_of(link).startswith("/compte/verificar/")
        assert "48 hores" in email.body_text

    @pytest.mark.parametrize("status", [Account.Status.ACTIVE, Account.Status.DISABLED])
    def test_not_for_accounts_that_are_not_pending(self, pending_account, status):
        pending_account.status = status
        pending_account.save()
        assert email_links.send_verification(pending_account) is False
        assert not OutgoingEmail.objects.exists()

    def test_never_for_admin_accounts(self, admin_account):
        # RN-19
        assert email_links.send_verification(admin_account) is False
        assert not OutgoingEmail.objects.exists()

    def test_no_link_in_the_activity_log(self, pending_account):
        email_links.send_verification(pending_account)
        token = token_of(queued_link(pending_account))
        assert not any(token in str(values) for values in AuditEntry.objects.values_list())


class TestVerificationEndToEnd:
    def test_pending_until_confirmed_then_active(self, client, pending_account):
        # CA-04.2 i CK C5, de principi a fi amb el correu de la cua.
        email_links.send_verification(pending_account)
        link = queued_link(pending_account)
        mail.deliver(OutgoingEmail.objects.get().pk)
        assert django_mail.outbox[0].to == ["anna@example.org"]
        assert link in django_mail.outbox[0].body

        login = {"login": "anna@example.org", "password": PASSWORD}
        refused = client.post(reverse("accounts:login"), login)
        assert escape(str(PENDING_ERROR)) in refused.content.decode()

        first = client.get(path_of(link))
        assert first.status_code == 302
        assert first["Location"] == reverse("accounts:verify_email")

        page = client.get(first["Location"])
        assert page.context["state"] == "ready"
        pending_account.refresh_from_db()
        assert pending_account.status == Account.Status.PENDING  # obrir-lo no ho fa

        done = client.post(reverse("accounts:verify_email"))
        assert done.context["state"] == "done"
        pending_account.refresh_from_db()
        assert pending_account.status == Account.Status.ACTIVE
        entry = AuditEntry.objects.get(action=audit.Action.EMAIL_VERIFIED)
        assert (entry.target_id, entry.old_value, entry.new_value) == (
            str(pending_account.pk),
            "pending",
            "active",
        )

        client.post(reverse("accounts:login"), login)
        assert "_auth_user_id" in client.session

    def test_the_link_works_only_once(self, client, pending_account):
        email_links.send_verification(pending_account)
        link = queued_link(pending_account)
        client.get(path_of(link))
        client.post(reverse("accounts:verify_email"))

        other = type(client)()
        other.get(path_of(link))
        assert other.get(reverse("accounts:verify_email")).context["state"] == "invalid"
        assert other.post(reverse("accounts:verify_email")).context["state"] == "invalid"
        assert AuditEntry.objects.filter(action=audit.Action.EMAIL_VERIFIED).count() == 1

    def test_invalid_link_is_a_normal_page_not_an_error(self, client, pending_account):
        # Un 404 deixaria la ruta, amb el testimoni, al registre `django.request`.
        response = client.get(path_of("http://x/compte/verificar/fals:fals:fals/"), follow=True)
        assert response.status_code == 200
        assert response.context["state"] == "invalid"

    def test_without_a_link_there_is_nothing_to_confirm(self, client, pending_account):
        assert client.get(reverse("accounts:verify_email")).context["state"] == "invalid"
        client.post(reverse("accounts:verify_email"))
        pending_account.refresh_from_db()
        assert pending_account.status == Account.Status.PENDING

    def test_a_reset_token_does_not_verify(self, client, pending_account):
        token = tokens.make_token(pending_account, tokens.RESET_PASSWORD)
        client.get(reverse("accounts:verify_email_link", args=[token]))
        assert client.post(reverse("accounts:verify_email")).context["state"] == "invalid"
        pending_account.refresh_from_db()
        assert pending_account.status == Account.Status.PENDING


class TestTokenExposure:
    def test_token_stays_out_of_urls_headers_and_logs(self, client, caplog, pending_account):
        caplog.set_level(logging.DEBUG)
        email_links.send_verification(pending_account)
        link = queued_link(pending_account)
        token = token_of(link)

        first = client.get(path_of(link))
        page = client.get(first["Location"])
        done = client.post(reverse("accounts:verify_email"))
        again = client.get(path_of(link), follow=True)

        for response in (first, page, done, again):
            assert response["Referrer-Policy"] == "no-referrer"
            assert "no-cache" in response["Cache-Control"]
            assert token not in response.get("Location", "")
            assert token not in response.content.decode()
        assert token not in first["Location"]
        assert not any(token in record.getMessage() for record in caplog.records)
        assert not any(token in str(values) for values in AuditEntry.objects.values_list())
        # Un cop tancat el correu, el cos (amb l'enllaç) no es guarda (T-M01-10).
        mail.deliver(OutgoingEmail.objects.get().pk)
        assert token not in str(OutgoingEmail.objects.values_list().get())

    def test_used_token_is_removed_from_the_session(self, client, pending_account):
        token = tokens.make_token(pending_account, tokens.VERIFY_EMAIL)
        client.get(reverse("accounts:verify_email_link", args=[token]))
        assert client.session[email_links.VERIFY_SESSION_KEY] == token
        client.post(reverse("accounts:verify_email"))
        assert email_links.VERIFY_SESSION_KEY not in client.session

    def test_expired_token_page(self, client, monkeypatch, pending_account):
        token = token_made_hours_ago(monkeypatch, pending_account, tokens.VERIFY_EMAIL, 49)
        client.get(reverse("accounts:verify_email_link", args=[token]))
        response = client.post(reverse("accounts:verify_email"))
        assert response.context["state"] == "invalid"
        pending_account.refresh_from_db()
        assert pending_account.status == Account.Status.PENDING


def test_no_email_route_on_the_admin_entry():
    # CA-07.4: l'entrada d'administració continua sense cap ruta de verificació ni recuperació.
    from apps.accounts import admin_urls

    names = {pattern.name for pattern in admin_urls.urlpatterns}
    assert not any("verify_email" in name or "password_reset" in name for name in names)
