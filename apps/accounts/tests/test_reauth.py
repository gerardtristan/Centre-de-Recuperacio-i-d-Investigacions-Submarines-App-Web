"""Reautenticació (T-M00-05; RN-M01-57, RN-M05a-12; V-01) i sessions d'un compte bloquejat per
intents (RN-M01-80, CA-M01-79; Q-088 de la 072 i 074, punt 19). Només dades inventades.
"""

import time

import pytest
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory
from django.urls import reverse

from apps.accounts.models import Account, FailedLogin
from apps.accounts.reauth import REAUTH_AT_SESSION_KEY, require_recent_auth
from apps.accounts.security import AREA_PERSONAL, TOO_MANY_ATTEMPTS, WRONG_CODE, WRONG_PASSWORD
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.accounts.tests.test_personal_totp import code_for, with_totp
from apps.core import audit
from apps.core.models import AuditEntry
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

MINUTE = 60
NOT_IT = "no-es-aquesta"  # una contrasenya que no és la del compte


def request_for(account, auth_age_seconds=0):
    """Petició d'un compte que va entrar fa `auth_age_seconds` segons."""
    request = RequestFactory().post("/", REMOTE_ADDR="10.9.0.1")
    request.user = account
    request.session = SessionStore()
    request.session[AUTH_AT_SESSION_KEY] = time.time() - auth_age_seconds
    return request


def failures(account):
    return FailedLogin.objects.filter(account=account).count()


class TestWindow:
    def test_recent_login_inside_the_window_needs_nothing(self, personal_account):
        # RN-M05a-12: dins dels N minuts, n'hi ha prou amb l'entrada.
        request = request_for(personal_account, 5 * MINUTE)
        assert require_recent_auth(request, 15) is None
        assert failures(personal_account) == 0

    def test_old_login_outside_the_window_asks_for_the_password(self, personal_account):
        request = request_for(personal_account, 16 * MINUTE)
        assert require_recent_auth(request, 15) == WRONG_PASSWORD
        assert failures(personal_account) == 1
        assert require_recent_auth(request, 15, password=PASSWORD) is None

    def test_a_correct_reauth_opens_a_new_window(self, personal_account):
        request = request_for(personal_account, 60 * MINUTE)
        auth_at = request.session[AUTH_AT_SESSION_KEY]
        assert require_recent_auth(request, 15, password=PASSWORD) is None
        assert request.session[REAUTH_AT_SESSION_KEY] >= time.time() - 5
        assert require_recent_auth(request, 15) is None
        # L'hora de l'entrada no canvia: fixa el màxim de 8 hores de l'administració (V-01).
        assert request.session[AUTH_AT_SESSION_KEY] == auth_at

    def test_zero_minutes_always_asks_even_just_after_login(self, personal_account):
        # RN-M01-57: sempre, a la mateixa petició.
        request = request_for(personal_account, 0)
        assert require_recent_auth(request, 0) == WRONG_PASSWORD
        assert require_recent_auth(request, 0, password=PASSWORD) is None
        assert require_recent_auth(request, 0) == WRONG_PASSWORD


class TestCredentials:
    def test_account_without_totp_needs_only_the_password(self, personal_account):
        assert require_recent_auth(request_for(personal_account), 0, password=PASSWORD) is None

    def test_account_with_totp_needs_the_code(self, personal_account):
        device = with_totp(personal_account)
        request = request_for(personal_account)
        assert require_recent_auth(request, 0, password=PASSWORD) == WRONG_CODE
        assert require_recent_auth(request, 0, password=PASSWORD, code=code_for(device)) is None

    def test_wrong_code_counts_and_is_recorded(self, personal_account):
        device = with_totp(personal_account)
        bad = "111111" if code_for(device) != "111111" else "222222"
        request = request_for(personal_account)
        assert require_recent_auth(request, 0, password=PASSWORD, code=bad) == WRONG_CODE
        personal_account.refresh_from_db()
        assert personal_account.failed_login_count == 1
        entry = AuditEntry.objects.get(action=audit.Action.LOGIN_FAILED)
        assert entry.target_id == str(personal_account.pk)
        assert entry.details == {"area": AREA_PERSONAL, "reason": "bad_code"}

    def test_wrong_password_counts_and_is_recorded(self, personal_account):
        request = request_for(personal_account)
        assert require_recent_auth(request, 0, password=NOT_IT) == WRONG_PASSWORD
        personal_account.refresh_from_db()
        assert personal_account.failed_login_count == 1
        entry = AuditEntry.objects.get(action=audit.Action.LOGIN_FAILED)
        assert entry.details == {"area": AREA_PERSONAL, "reason": "bad_password"}

    def test_inactive_account_is_not_checked(self, personal_account):
        personal_account.status = Account.Status.DISABLED
        personal_account.save()
        with pytest.raises(PermissionDenied):
            require_recent_auth(request_for(personal_account), 0, password=PASSWORD)
        assert failures(personal_account) == 0

    def test_five_failures_lock_and_say_nothing_about_attempts_left(self, personal_account):
        request = request_for(personal_account)
        epoch = personal_account.session_epoch
        messages = [require_recent_auth(request, 0, password=NOT_IT) for _ in range(5)]
        assert messages == [WRONG_PASSWORD] * 4 + [TOO_MANY_ATTEMPTS]
        personal_account.refresh_from_db()
        assert personal_account.locked_until is not None
        assert personal_account.session_epoch == epoch + 1  # RN-M01-80
        # Bloquejat: ni la contrasenya correcta passa.
        assert require_recent_auth(request, 0, password=PASSWORD) == TOO_MANY_ATTEMPTS


def open_session(account, area=AREA_PERSONAL):
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = area
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client


def session_is_valid(client):
    return client.get(reverse("members:profile")).status_code == 200


class TestLockedAccountSessions:
    def test_ca_m01_79_lock_by_login_attempts_ends_both_sessions(self, personal_account):
        """CA-M01-79: dues sessions obertes; cinc intents fallits a l'entrada → cap no val."""
        first, second = open_session(personal_account), open_session(personal_account)
        assert session_is_valid(first) and session_is_valid(second)
        attacker = Client()
        for _ in range(5):
            attacker.post(
                reverse("accounts:login"), {"login": "anna@example.org", "password": "no"}
            )
        assert not session_is_valid(first)
        assert not session_is_valid(second)

    def test_ca_m01_79_lock_during_a_reauth_ends_both_sessions(self, personal_account):
        """CA-M01-79 i RN-M01-80: el bloqueig durant una reautenticació (esborrar el compte)
        també tanca la sessió que la fa i les altres."""
        first, second = open_session(personal_account), open_session(personal_account)
        for _ in range(5):
            first.post(reverse("members:erase"), {"confirm": "on", "password": "no"})
        assert not session_is_valid(first)
        assert not session_is_valid(second)

    def test_failures_below_the_limit_keep_the_sessions(self, personal_account):
        first = open_session(personal_account)
        for _ in range(4):
            first.post(reverse("members:erase"), {"confirm": "on", "password": "no"})
        assert session_is_valid(first)
