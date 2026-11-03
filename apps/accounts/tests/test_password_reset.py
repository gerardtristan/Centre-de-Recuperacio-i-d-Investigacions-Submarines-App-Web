"""Contrasenya nova amb l'enllaç de recuperació del compte personal (spec 00, HU-04, RN-18;
CA-04.4; CK C4). La pantalla per demanar l'enllaç depèn de regles pendents d'aprovar (límits
i comptes pendents de verificar): aquí el testimoni es fa directament. Només dades inventades.
"""

import logging
import time

import pytest
from django.core import signing
from django.urls import reverse
from django.utils import timezone

from apps.accounts import email_links, tokens
from apps.accounts.models import Account, TotpDevice
from apps.accounts.security import AREA_PERSONAL
from apps.core import audit
from apps.core.crypto import encrypt
from apps.core.models import AuditEntry
from conftest import NEW_PASSWORD, OTHER_PASSWORD, PASSWORD

pytestmark = pytest.mark.django_db

RESET = "accounts:password_reset"


def open_link(client, account):
    token = tokens.make_token(account, tokens.RESET_PASSWORD)
    first = client.get(reverse("accounts:password_reset_link", args=[token]))
    assert first.status_code == 302
    assert first["Location"] == reverse(RESET)
    return token


def submit(client, password=NEW_PASSWORD, again=None):
    data = {"new_password1": password, "new_password2": again or password}
    return client.post(reverse(RESET), data)


def can_log_in(client, password):
    client.post(reverse("accounts:login"), {"login": "anna@example.org", "password": password})
    return "_auth_user_id" in client.session


class TestResetWithLink:
    def test_end_to_end(self, client, personal_account):
        open_link(client, personal_account)
        assert client.get(reverse(RESET)).context["state"] == "ready"

        done = submit(client)
        assert done.context["state"] == "done"
        entry = AuditEntry.objects.get(action=audit.Action.PASSWORD_RESET)
        assert entry.target_id == str(personal_account.pk)
        assert entry.details == {"channel": "email"}
        assert entry.old_value is None and entry.new_value is None

        other = type(client)()
        assert not can_log_in(other, PASSWORD)
        assert can_log_in(type(client)(), NEW_PASSWORD)

    def test_password_rules_of_v01(self, client, personal_account):
        open_link(client, personal_account)
        short = submit(client, "curta-1")
        assert short.context["state"] == "ready"
        assert short.context["form"].errors
        mismatch = submit(client, NEW_PASSWORD, NEW_PASSWORD + "x")
        assert "no coincideixen" in mismatch.content.decode()
        personal_account.refresh_from_db()
        assert personal_account.check_password(PASSWORD)
        assert not AuditEntry.objects.filter(action=audit.Action.PASSWORD_RESET).exists()

    def test_a_used_link_does_not_work_again(self, client, personal_account):
        # CA-04.4
        token = open_link(client, personal_account)
        submit(client)
        other = type(client)()
        other.get(reverse("accounts:password_reset_link", args=[token]))
        assert other.get(reverse(RESET)).context["state"] == "invalid"
        assert submit(other, OTHER_PASSWORD).context["state"] == "invalid"
        personal_account.refresh_from_db()
        assert personal_account.check_password(NEW_PASSWORD)

    def test_an_expired_link_does_not_work(self, client, monkeypatch, personal_account):
        # CA-04.4: una hora (V-01).
        past = time.time() - 3700
        with monkeypatch.context() as patch:
            patch.setattr(signing.time, "time", lambda: past)
            token = tokens.make_token(personal_account, tokens.RESET_PASSWORD)
        client.get(reverse("accounts:password_reset_link", args=[token]))
        assert submit(client).context["state"] == "invalid"
        personal_account.refresh_from_db()
        assert personal_account.check_password(PASSWORD)

    def test_a_verification_link_does_not_reset(self, client, personal_account):
        token = tokens.make_token(personal_account, tokens.VERIFY_EMAIL)
        client.get(reverse("accounts:password_reset_link", args=[token]))
        assert submit(client).context["state"] == "invalid"

    @pytest.mark.parametrize("status", [Account.Status.PENDING, Account.Status.DISABLED])
    def test_only_active_accounts(self, client, personal_account, status):
        personal_account.status = status
        personal_account.save()
        open_link(client, personal_account)
        assert submit(client).context["state"] == "invalid"

    def test_without_a_link(self, client, personal_account):
        assert client.get(reverse(RESET)).context["state"] == "invalid"
        assert submit(client).context["state"] == "invalid"

    def test_open_sessions_are_closed(self, client, login_as, personal_account):
        session_client = login_as(personal_account, AREA_PERSONAL)
        assert session_client.get(reverse("core:home")).status_code == 200
        other = type(client)()
        open_link(other, personal_account)
        submit(other)
        assert session_client.get(reverse("core:home")).status_code == 302

    def test_the_second_factor_stays(self, client, personal_account):
        # La recuperació per correu no desactiva el TOTP del compte personal.
        TotpDevice.objects.create(
            account=personal_account,
            secret_encrypted=encrypt("JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"),
            confirmed_at=timezone.now(),
        )
        open_link(client, personal_account)
        submit(client)
        personal_account.refresh_from_db()
        assert personal_account.has_totp
        other = type(client)()
        response = other.post(
            reverse("accounts:login"), {"login": "anna@example.org", "password": NEW_PASSWORD}
        )
        assert response["Location"] == reverse("accounts:login_totp")
        assert "_auth_user_id" not in other.session

    def test_token_stays_out_of_pages_headers_and_logs(self, client, caplog, personal_account):
        caplog.set_level(logging.DEBUG)
        token = tokens.make_token(personal_account, tokens.RESET_PASSWORD)
        first = client.get(reverse("accounts:password_reset_link", args=[token]))
        page = client.get(reverse(RESET))
        done = submit(client)
        for response in (first, page, done):
            assert response["Referrer-Policy"] == "no-referrer"
            assert "no-cache" in response["Cache-Control"]
            assert token not in response.get("Location", "")
            assert token not in response.content.decode()
        assert not any(token in record.getMessage() for record in caplog.records)
        assert not any(NEW_PASSWORD in record.getMessage() for record in caplog.records)
        values = [str(row) for row in AuditEntry.objects.values_list()]
        assert not any(token in row or NEW_PASSWORD in row for row in values)
        assert email_links.RESET_SESSION_KEY not in client.session
