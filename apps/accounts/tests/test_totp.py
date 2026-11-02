"""Doble factor TOTP i codis de recuperació (spec 00, HU-05, HU-07, HU-09; V-01; CK C2).

Només dades inventades.
"""

import hashlib
import time
from datetime import timedelta

import pyotp
import pytest
from cryptography.fernet import Fernet
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts import totp
from apps.accounts.models import Account, RecoveryCode, TotpDevice
from apps.accounts.views import BAD_CODE
from apps.core import crypto
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

ADMIN_LOGIN = "administration:login"
ENROL = "administration:totp_enrol"
ADMIN_CODE = "administration:login_totp"


def is_logged_in(client):
    return "_auth_user_id" in client.session


def code_for(device, offset_steps=0):
    secret = totp.secret_of(device)
    return pyotp.TOTP(secret).at(timezone.now() + timedelta(seconds=30 * offset_steps))


def enrolled(account):
    """Factor TOTP ja confirmat, amb codis de recuperació."""
    device = totp.start_enrolment(account)
    codes = totp.confirm_enrolment(device, code_for(device))
    device.refresh_from_db()
    # Que el codi d'alta no impedeixi fer servir el codi actual a les proves.
    device.last_used_step = None
    device.save()
    return device, codes


def password_step(client, login="joan.vila"):
    return client.post(reverse(ADMIN_LOGIN), {"login": login, "password": PASSWORD})


class TestEncryption:
    def test_round_trip(self):
        assert crypto.decrypt(crypto.encrypt("JBSWY3DPEHPK3PXP")) == "JBSWY3DPEHPK3PXP"

    def test_ciphertext_is_not_the_secret_and_changes(self):
        first, second = crypto.encrypt("JBSWY3DPEHPK3PXP"), crypto.encrypt("JBSWY3DPEHPK3PXP")
        assert "JBSWY3DPEHPK3PXP" not in first
        assert first != second

    def test_key_rotation_keeps_old_data_readable(self, settings):
        old_token = crypto.encrypt("secret-antic")
        new_key = Fernet.generate_key().decode()
        crypto._fernet.cache_clear()
        try:
            with override_settings(
                FIELD_ENCRYPTION_KEYS=[new_key, *settings.FIELD_ENCRYPTION_KEYS]
            ):
                assert crypto.decrypt(old_token) == "secret-antic"
        finally:
            crypto._fernet.cache_clear()


class TestEnrolment:
    def test_secret_is_stored_encrypted(self, admin_account):
        device = totp.start_enrolment(admin_account)
        secret = totp.secret_of(device)
        assert len(secret) >= 32
        assert secret not in device.secret_encrypted

    def test_enrolment_page_shows_qr_and_key(self, client, admin_account):
        password_step(client)
        response = client.get(reverse(ENROL))
        html = response.content.decode()
        assert response.status_code == 200
        assert "<svg" in html
        device = TotpDevice.objects.get(account=admin_account)
        assert totp.secret_of(device)[:4] in html
        assert "no-store" in response["Cache-Control"]

    def test_provisioning_uri_follows_rfc_6238_format(self, admin_account):
        uri = totp.provisioning_uri(totp.start_enrolment(admin_account))
        assert uri.startswith("otpauth://totp/")
        assert "issuer=C.R.I.S." in uri

    def test_reloading_keeps_the_same_secret(self, client, admin_account):
        password_step(client)
        client.get(reverse(ENROL))
        first = TotpDevice.objects.get(account=admin_account).secret_encrypted
        client.get(reverse(ENROL))
        assert TotpDevice.objects.get(account=admin_account).secret_encrypted == first

    def test_wrong_code_does_not_confirm(self, client, admin_account):
        password_step(client)
        client.get(reverse(ENROL))
        response = client.post(reverse(ENROL), {"code": "000000"})
        assert str(BAD_CODE) in response.content.decode()
        assert not is_logged_in(client)
        assert TotpDevice.objects.get(account=admin_account).confirmed_at is None

    def test_right_code_confirms_logs_in_and_shows_recovery_codes(self, client, admin_account):
        # CA-07.1 i CA-09.1
        password_step(client)
        client.get(reverse(ENROL))
        device = TotpDevice.objects.get(account=admin_account)
        response = client.post(reverse(ENROL), {"code": code_for(device)})
        assert response.status_code == 200
        assert is_logged_in(client)
        device.refresh_from_db()
        assert device.confirmed_at is not None

        html = response.content.decode()
        stored = RecoveryCode.objects.filter(account=admin_account)
        assert stored.count() == 10
        for row in stored:
            assert row.code_hash not in html  # només l'empremta, a la base de dades
        assert html.count("<code>") == 10
        assert client.get(reverse("administration:home")).status_code == 200

    def test_without_password_step_it_redirects_to_login(self, client, admin_account):
        response = client.get(reverse(ENROL))
        assert response["Location"] == reverse(ADMIN_LOGIN)

    def test_enrolled_account_cannot_enrol_again(self, client, admin_account):
        enrolled(admin_account)
        password_step(client)
        response = client.get(reverse(ENROL))
        assert response["Location"] == reverse(ADMIN_CODE)


class TestAdminSecondStep:
    def test_password_step_asks_for_the_code(self, client, admin_account):
        enrolled(admin_account)
        response = password_step(client)
        assert response["Location"] == reverse(ADMIN_CODE)
        assert not is_logged_in(client)

    def test_right_code_opens_the_session(self, client, admin_account):
        device, _ = enrolled(admin_account)
        password_step(client)
        response = client.post(reverse(ADMIN_CODE), {"code": code_for(device)})
        assert response["Location"] == reverse("administration:home")
        assert is_logged_in(client)

    def test_code_from_previous_interval_is_accepted(self, client, admin_account):
        device, _ = enrolled(admin_account)
        password_step(client)
        client.post(reverse(ADMIN_CODE), {"code": code_for(device, -1)})
        assert is_logged_in(client)

    @pytest.mark.parametrize("code", ["", "000000", "12345", "abcdef", "1234567"])
    def test_missing_or_wrong_code_gives_no_session(self, client, admin_account, code):
        # CA-07.2
        enrolled(admin_account)
        password_step(client)
        client.post(reverse(ADMIN_CODE), {"code": code})
        assert not is_logged_in(client)

    def test_old_code_is_rejected(self, client, admin_account):
        device, _ = enrolled(admin_account)
        password_step(client)
        client.post(reverse(ADMIN_CODE), {"code": code_for(device, -3)})
        assert not is_logged_in(client)

    def test_a_code_cannot_be_used_twice(self, client, admin_account):
        device, _ = enrolled(admin_account)
        code = code_for(device)
        password_step(client)
        client.post(reverse(ADMIN_CODE), {"code": code})
        client.post(reverse("administration:logout"))
        password_step(client)
        response = client.post(reverse(ADMIN_CODE), {"code": code})
        assert str(BAD_CODE) in response.content.decode()
        assert not is_logged_in(client)

    def test_wrong_codes_lock_the_account(self, client, admin_account):
        # V-01: els codis incorrectes compten com a intents fallits.
        enrolled(admin_account)
        password_step(client)
        for _ in range(5):
            response = client.post(reverse(ADMIN_CODE), {"code": "000000"})
        assert response["Location"] == reverse(ADMIN_LOGIN)
        admin_account.refresh_from_db()
        assert admin_account.is_locked(timezone.now())
        # L'estat pendent s'ha esborrat: cal tornar a començar.
        assert client.get(reverse(ADMIN_CODE))["Location"] == reverse(ADMIN_LOGIN)

    def test_pending_step_expires(self, client, admin_account):
        device, _ = enrolled(admin_account)
        password_step(client)
        session = client.session
        session["pending_auth"]["at"] = time.time() - 11 * 60
        session.save()
        client.post(reverse(ADMIN_CODE), {"code": code_for(device)})
        assert not is_logged_in(client)

    def test_account_disabled_between_steps_gets_no_session(self, client, admin_account):
        device, _ = enrolled(admin_account)
        password_step(client)
        Account.objects.filter(pk=admin_account.pk).update(status=Account.Status.DISABLED)
        client.post(reverse(ADMIN_CODE), {"code": code_for(device)})
        assert not is_logged_in(client)


class TestRecoveryCodes:
    def test_hashes_only(self, admin_account):
        _, codes = enrolled(admin_account)
        stored = set(RecoveryCode.objects.values_list("code_hash", flat=True))
        assert not stored & set(codes)
        normalized = codes[0].replace("-", "")
        assert hashlib.sha256(normalized.encode()).hexdigest() in stored

    def test_codes_are_unique_and_long_enough(self, admin_account):
        _, codes = enrolled(admin_account)
        assert len(set(codes)) == 10
        assert all(len(code.replace("-", "")) == 16 for code in codes)

    def test_recovery_code_requires_re_enrolment(self, client, admin_account):
        # CA-09.2
        _, codes = enrolled(admin_account)
        password_step(client)
        response = client.post(reverse(ADMIN_CODE), {"code": codes[0].lower()})
        assert response["Location"] == reverse(ENROL)
        assert not TotpDevice.objects.filter(account=admin_account).exists()
        assert RecoveryCode.objects.get(account=admin_account, used_at__isnull=False)

        client.get(reverse(ENROL))
        device = TotpDevice.objects.get(account=admin_account)
        client.post(reverse(ENROL), {"code": code_for(device)})
        assert is_logged_in(client)
        # Els codis antics han quedat substituïts pels nous.
        assert not RecoveryCode.objects.filter(account=admin_account, used_at__isnull=False)

    def test_used_code_is_rejected(self, admin_account):
        # CA-09.3
        _, codes = enrolled(admin_account)
        assert totp.use_recovery_code(admin_account, codes[0])
        assert not totp.use_recovery_code(admin_account, codes[0])
        assert totp.use_recovery_code(admin_account, codes[1])

    def test_recovery_codes_do_not_work_on_the_personal_entry(self, client, personal_account):
        _, codes = enrolled(personal_account)
        client.post(reverse("accounts:login"), {"login": "anna@example.org", "password": PASSWORD})
        client.post(reverse("accounts:login_totp"), {"code": codes[0]})
        assert not is_logged_in(client)


class TestPersonalOptionalTotp:
    def test_without_totp_no_code_is_asked(self, client, personal_account):
        client.post(reverse("accounts:login"), {"login": "anna@example.org", "password": PASSWORD})
        assert is_logged_in(client)

    def test_with_totp_the_code_is_asked(self, client, personal_account):
        # CA-05.1
        device, _ = enrolled(personal_account)
        response = client.post(
            reverse("accounts:login"), {"login": "anna@example.org", "password": PASSWORD}
        )
        assert response["Location"] == reverse("accounts:login_totp")
        assert not is_logged_in(client)
        client.post(reverse("accounts:login_totp"), {"code": code_for(device)})
        assert is_logged_in(client)

    def test_admin_pending_state_does_not_serve_the_personal_step(self, client, admin_account):
        enrolled(admin_account)
        password_step(client)
        response = client.get(reverse("accounts:login_totp"))
        assert response["Location"] == reverse("accounts:login")
