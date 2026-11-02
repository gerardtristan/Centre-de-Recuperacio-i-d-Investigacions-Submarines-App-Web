"""Entrades separades, credencials i bloqueig (spec 00, HU-04, HU-07; V-01; CK C2, C3, C5).

Només dades inventades.
"""

from datetime import timedelta

import pytest
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from apps.accounts import admin_urls
from apps.accounts.models import Account, FailedLogin
from apps.accounts.security import GENERIC_ERROR, PENDING_ERROR, client_ip
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

PERSONAL_LOGIN = "accounts:login"
ADMIN_LOGIN = "administration:login"


def post_login(client, url_name, login, password=PASSWORD, **extra):
    return client.post(reverse(url_name), {"login": login, "password": password}, **extra)


def is_logged_in(client):
    return "_auth_user_id" in client.session


class TestPersonalEntry:
    def test_active_account_gets_a_personal_session(self, client, personal_account):
        # CA-04.1
        response = post_login(client, PERSONAL_LOGIN, "anna@example.org")
        assert response.status_code == 302
        assert response["Location"] == reverse("core:home")
        assert is_logged_in(client)
        assert client.get(reverse("core:home")).status_code == 200

    def test_email_in_any_case(self, client, personal_account):
        post_login(client, PERSONAL_LOGIN, " ANNA@example.org ")
        assert is_logged_in(client)

    def test_wrong_password(self, client, personal_account):
        response = post_login(client, PERSONAL_LOGIN, "anna@example.org", "no-es-aquesta")
        assert response.status_code == 200
        assert escape(str(GENERIC_ERROR)) in response.content.decode()
        assert not is_logged_in(client)
        personal_account.refresh_from_db()
        assert personal_account.failed_login_count == 1

    def test_unknown_email_gives_the_same_answer(self, client, personal_account):
        wrong = post_login(client, PERSONAL_LOGIN, "anna@example.org", "no-es-aquesta")
        unknown = post_login(client, PERSONAL_LOGIN, "ningu@example.org", "no-es-aquesta")
        assert wrong.status_code == unknown.status_code == 200
        assert escape(str(GENERIC_ERROR)) in unknown.content.decode()
        assert FailedLogin.objects.filter(account__isnull=True).count() == 1

    def test_pending_account_gets_no_session(self, client, make_person):
        # CA-04.2
        Account.objects.create_personal(make_person(), "anna@example.org", PASSWORD)
        response = post_login(client, PERSONAL_LOGIN, "anna@example.org")
        assert escape(str(PENDING_ERROR)) in response.content.decode()
        assert not is_logged_in(client)

    def test_pending_message_needs_the_right_password(self, client, make_person):
        Account.objects.create_personal(make_person(), "anna@example.org", PASSWORD)
        response = post_login(client, PERSONAL_LOGIN, "anna@example.org", "no-es-aquesta")
        assert escape(str(PENDING_ERROR)) not in response.content.decode()
        assert escape(str(GENERIC_ERROR)) in response.content.decode()

    def test_disabled_account_gets_no_session(self, client, personal_account):
        personal_account.status = Account.Status.DISABLED
        personal_account.save()
        response = post_login(client, PERSONAL_LOGIN, "anna@example.org")
        assert escape(str(GENERIC_ERROR)) in response.content.decode()
        assert not is_logged_in(client)

    def test_admin_account_cannot_enter_with_username(self, client, admin_account):
        post_login(client, PERSONAL_LOGIN, "joan.vila")
        assert not is_logged_in(client)

    def test_admin_account_cannot_enter_with_notification_email(self, client, admin_account):
        # CA-07.5
        response = post_login(client, PERSONAL_LOGIN, "joan@example.org")
        assert escape(str(GENERIC_ERROR)) in response.content.decode()
        assert not is_logged_in(client)

    def test_safe_next_is_followed(self, client, personal_account):
        response = client.post(
            reverse(PERSONAL_LOGIN) + "?next=/salut/",
            {"login": "anna@example.org", "password": PASSWORD},
        )
        assert response["Location"] == "/salut/"

    def test_external_next_is_ignored(self, client, personal_account):
        response = client.post(
            reverse(PERSONAL_LOGIN),
            {"login": "anna@example.org", "password": PASSWORD, "next": "https://example.com/"},
        )
        assert response["Location"] == reverse("core:home")


class TestAdminEntry:
    def test_personal_account_cannot_enter(self, client, personal_account):
        # CA-04.5
        response = post_login(client, ADMIN_LOGIN, "anna@example.org")
        assert escape(str(GENERIC_ERROR)) in response.content.decode()
        assert not is_logged_in(client)

    def test_password_alone_never_opens_a_session(self, client, admin_account):
        # RN-21, CA-07.1: sense TOTP, només pot donar-ne d'alta un.
        response = post_login(client, ADMIN_LOGIN, "joan.vila")
        assert response["Location"] == reverse("administration:totp_enrol")
        assert not is_logged_in(client)
        response = client.get(reverse("administration:home"))
        assert response["Location"].startswith(reverse(ADMIN_LOGIN))

    def test_no_email_recovery_on_the_admin_entry(self, client):
        # CA-07.4: cap enllaç ni cap ruta de recuperació per correu.
        html = client.get(reverse(ADMIN_LOGIN)).content.decode().lower()
        assert "recuper" not in html
        assert "contrasenya oblidada" not in html
        names = [pattern.name for pattern in admin_urls.urlpatterns]
        assert not [n for n in names if "password" in n or "recover" in n]


class TestAccountLock:
    def test_five_failures_lock_the_account(self, client, personal_account):
        # V-01: 5 intents fallits seguits → 15 minuts.
        for _ in range(5):
            post_login(client, PERSONAL_LOGIN, "anna@example.org", "no-es-aquesta")
        personal_account.refresh_from_db()
        assert personal_account.locked_until is not None
        expected = timezone.now() + timedelta(minutes=15)
        assert abs((personal_account.locked_until - expected).total_seconds()) < 5

        response = post_login(client, PERSONAL_LOGIN, "anna@example.org")
        assert escape(str(GENERIC_ERROR)) in response.content.decode()
        assert not is_logged_in(client)

    def test_lock_ends_after_fifteen_minutes(self, client, personal_account):
        personal_account.locked_until = timezone.now() - timedelta(seconds=1)
        personal_account.save()
        post_login(client, PERSONAL_LOGIN, "anna@example.org")
        assert is_logged_in(client)
        personal_account.refresh_from_db()
        assert personal_account.locked_until is None

    def test_success_resets_the_consecutive_count(self, client, personal_account):
        for _ in range(4):
            post_login(client, PERSONAL_LOGIN, "anna@example.org", "no-es-aquesta")
        post_login(client, PERSONAL_LOGIN, "anna@example.org")
        personal_account.refresh_from_db()
        assert personal_account.failed_login_count == 0
        assert personal_account.locked_until is None

    def test_admin_account_locks_too(self, client, admin_account):
        for _ in range(5):
            post_login(client, ADMIN_LOGIN, "joan.vila", "no-es-aquesta")
        admin_account.refresh_from_db()
        assert admin_account.is_locked(timezone.now())


class TestOriginLimit:
    def test_twenty_failures_from_one_origin_block_it(self, client, personal_account):
        # V-01: 20 intents fallits des d'un mateix origen en 15 minuts → 15 minuts.
        for i in range(20):
            post_login(client, PERSONAL_LOGIN, f"ningu{i}@example.org", "no-es-aquesta")
        post_login(client, PERSONAL_LOGIN, "anna@example.org")
        assert not is_logged_in(client)

    def test_other_origins_are_not_blocked(self, client, personal_account):
        for i in range(20):
            post_login(client, PERSONAL_LOGIN, f"ningu{i}@example.org", "x")
        post_login(client, PERSONAL_LOGIN, "anna@example.org", REMOTE_ADDR="198.51.100.7")
        assert is_logged_in(client)

    def test_old_failures_do_not_count(self, client, personal_account):
        for i in range(20):
            post_login(client, PERSONAL_LOGIN, f"ningu{i}@example.org", "x")
        FailedLogin.objects.update(created_at=timezone.now() - timedelta(minutes=16))
        post_login(client, PERSONAL_LOGIN, "anna@example.org")
        assert is_logged_in(client)


class TestClientIp:
    def request(self, remote, forwarded=None):
        meta = {"REMOTE_ADDR": remote}
        if forwarded:
            meta["HTTP_X_FORWARDED_FOR"] = forwarded
        return RequestFactory().get("/", **meta)

    def test_direct_connection_ignores_forwarded_header(self):
        assert client_ip(self.request("203.0.113.1", "198.51.100.9")) == "203.0.113.1"

    @override_settings(NUM_PROXIES=1)
    def test_behind_one_proxy_takes_the_rightmost_address(self):
        # El client pot inventar-se les adreces de l'esquerra; la del proxy és la de la dreta.
        request = self.request("10.0.0.2", "6.6.6.6, 198.51.100.9")
        assert client_ip(request) == "198.51.100.9"

    @override_settings(NUM_PROXIES=1)
    def test_behind_proxy_without_header_uses_remote_addr(self):
        assert client_ip(self.request("10.0.0.2")) == "10.0.0.2"

    @override_settings(NUM_PROXIES=1)
    def test_invalid_address_falls_back(self):
        assert client_ip(self.request("10.0.0.2", "no-es-una-ip")) == "0.0.0.0"  # noqa: S104


class TestLogout:
    def test_logout_ends_the_session(self, client, personal_account):
        post_login(client, PERSONAL_LOGIN, "anna@example.org")
        response = client.post(reverse("accounts:logout"))
        assert response["Location"] == reverse(PERSONAL_LOGIN)
        assert not is_logged_in(client)
        assert client.get(reverse("core:home")).status_code == 302

    def test_logout_requires_post(self, client, personal_account):
        post_login(client, PERSONAL_LOGIN, "anna@example.org")
        assert client.get(reverse("accounts:logout")).status_code == 405
        assert is_logged_in(client)
