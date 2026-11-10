"""Doble factor opcional del compte personal (spec 00, HU-05; CA-05.1 i CA-05.2; V-01).

Només dades inventades.
"""

import logging
from datetime import timedelta

import pyotp
import pytest
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from apps.accounts import totp
from apps.accounts.models import FailedLogin, RecoveryCode, TotpDevice
from apps.accounts.security import (
    AREA_ADMIN,
    AREA_PERSONAL,
    TOO_MANY_ATTEMPTS,
    WRONG_CODE,
    WRONG_PASSWORD,
)
from apps.core import audit
from apps.core.models import AuditEntry
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

SECURITY = "accounts:security"
ENROL = "accounts:totp_enrol"
DISABLE = "accounts:totp_disable"


def code_for(device, offset_steps=0):
    return pyotp.TOTP(totp.secret_of(device)).at(
        timezone.now() + timedelta(seconds=30 * offset_steps)
    )


def with_totp(account):
    device = totp.start_enrolment(account)
    totp.confirm_enrolment(device, code_for(device), recovery_codes=False)
    device.refresh_from_db()
    device.last_used_step = None  # que el codi d'alta no impedeixi fer servir l'actual
    device.save()
    return device


@pytest.fixture
def session(login_as, personal_account):
    return login_as(personal_account, AREA_PERSONAL)


class TestEnable:
    def test_security_page_shows_the_state(self, session, personal_account):
        page = session.get(reverse(SECURITY))
        assert page.status_code == 200
        assert page.context["has_totp"] is False
        assert reverse(ENROL) in page.content.decode()

    def test_enable_then_logins_ask_for_the_code(self, client, session, personal_account):
        # CA-05.1
        page = session.get(reverse(ENROL))
        assert page.status_code == 200
        device = TotpDevice.objects.get(account=personal_account)
        assert device.confirmed_at is None

        done = session.post(reverse(ENROL), {"code": code_for(device)})
        assert done["Location"] == reverse(SECURITY)
        personal_account.refresh_from_db()
        assert personal_account.has_totp
        # V-01: codis de recuperació només per als comptes d'administrador.
        assert not RecoveryCode.objects.filter(account=personal_account).exists()
        entry = AuditEntry.objects.get(action=audit.Action.TOTP_ENROLLED)
        assert entry.details == {"area": "personal"}

        response = client.post(
            reverse("accounts:login"), {"login": "anna@example.org", "password": PASSWORD}
        )
        assert response["Location"] == reverse("accounts:login_totp")
        assert "_auth_user_id" not in client.session

    def test_a_wrong_code_does_not_enable_or_count(self, session, personal_account):
        session.get(reverse(ENROL))
        response = session.post(reverse(ENROL), {"code": "000000"})
        assert response.status_code == 200
        personal_account.refresh_from_db()
        assert not personal_account.has_totp
        assert personal_account.failed_login_count == 0

    def test_no_secret_in_the_log(self, session, caplog, personal_account):
        caplog.set_level(logging.DEBUG)
        session.get(reverse(ENROL))
        device = TotpDevice.objects.get(account=personal_account)
        secret = totp.secret_of(device)
        session.post(reverse(ENROL), {"code": code_for(device)})
        assert not any(secret in record.getMessage() for record in caplog.records)
        assert not any(secret in str(row) for row in AuditEntry.objects.values_list())

    def test_already_enabled_goes_back(self, session, personal_account):
        with_totp(personal_account)
        assert session.get(reverse(ENROL))["Location"] == reverse(SECURITY)

    def test_needs_a_personal_session(self, client, login_as, admin_account):
        assert client.get(reverse(ENROL)).status_code == 302
        admin = login_as(admin_account, AREA_ADMIN)
        assert admin.get(reverse(SECURITY)).status_code == 302
        assert not TotpDevice.objects.filter(account=admin_account).exists()


class TestDisable:
    def test_password_and_code_disable_it(self, session, personal_account):
        # CA-05.2
        device = with_totp(personal_account)
        response = session.post(reverse(DISABLE), {"password": PASSWORD, "code": code_for(device)})
        assert response["Location"] == reverse(SECURITY)
        personal_account.refresh_from_db()
        assert not personal_account.has_totp
        entry = AuditEntry.objects.get(action=audit.Action.TOTP_DISABLED)
        assert entry.actor_account_id == personal_account.pk
        assert entry.details == {"area": "personal"}
        assert entry.old_value is None and entry.new_value is None

    def test_wrong_password_is_refused_and_counts(self, session, personal_account):
        device = with_totp(personal_account)
        response = session.post(
            reverse(DISABLE), {"password": "no-es-aquesta", "code": code_for(device)}
        )
        assert str(WRONG_PASSWORD) in response.content.decode()
        assert response.context["disable_form"].has_error("password")
        personal_account.refresh_from_db()
        assert personal_account.has_totp
        assert personal_account.failed_login_count == 1
        # El codi no s'ha gastat: es pot tornar a fer servir amb la contrasenya bona.
        assert session.post(reverse(DISABLE), {"password": PASSWORD, "code": code_for(device)})[
            "Location"
        ] == reverse(SECURITY)

    def test_wrong_code_is_refused_and_counts(self, session, personal_account):
        with_totp(personal_account)
        response = session.post(reverse(DISABLE), {"password": PASSWORD, "code": "000000"})
        assert str(WRONG_CODE) in response.content.decode()
        assert response.context["disable_form"].has_error("code")
        personal_account.refresh_from_db()
        assert personal_account.has_totp
        assert personal_account.failed_login_count == 1
        assert FailedLogin.objects.filter(account=personal_account).count() == 1

    def test_missing_fields(self, session, personal_account):
        with_totp(personal_account)
        response = session.post(reverse(DISABLE), {"password": PASSWORD})
        assert response.context["disable_form"].has_error("code")
        personal_account.refresh_from_db()
        assert personal_account.has_totp

    def test_lockout_after_the_attempts_of_v01(self, session, personal_account):
        device = with_totp(personal_account)
        for _ in range(5):
            response = session.post(reverse(DISABLE), {"password": "no-es-aquesta", "code": "1"})
        assert escape(str(TOO_MANY_ATTEMPTS)) in response.content.decode()
        personal_account.refresh_from_db()
        assert personal_account.is_locked(timezone.now())
        # Bloquejat: la sessió s'ha tancat (RN-M01-80, T-M00-05) i ni amb les dades bones.
        response = session.post(reverse(DISABLE), {"password": PASSWORD, "code": code_for(device)})
        assert response.status_code != 200
        personal_account.refresh_from_db()
        assert personal_account.has_totp
        assert AuditEntry.objects.filter(action=audit.Action.ACCOUNT_LOCKED).count() == 1

    def test_no_password_or_code_in_logs_or_activity(self, session, caplog, personal_account):
        caplog.set_level(logging.DEBUG)
        device = with_totp(personal_account)
        code = code_for(device)
        session.post(reverse(DISABLE), {"password": PASSWORD, "code": code})
        messages = [record.getMessage() for record in caplog.records]
        assert not any(PASSWORD in message or code in message for message in messages)
        rows = [str(row) for row in AuditEntry.objects.values_list()]
        assert not any(PASSWORD in row or code in row for row in rows)

    def test_get_is_not_allowed(self, session, personal_account):
        with_totp(personal_account)
        assert session.get(reverse(DISABLE)).status_code == 405
