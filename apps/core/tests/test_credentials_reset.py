"""Restabliment per un altre administrador (spec 00, HU-08; CA-08.1, 08.2 i 08.4; RN-16, RN-17;
V-01). Preparació del flux: servei, entrada amb la credencial temporal i llista amb M4. L'acció
de la pantalla espera l'aprovació de la revalidació del TOTP de qui la fa.

Només dades inventades.
"""

import logging
import re
from datetime import timedelta

import pyotp
import pytest
from django.core.exceptions import ValidationError
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from apps.accounts import totp
from apps.accounts.models import Account, FailedLogin, TotpDevice
from apps.accounts.security import AREA_ADMIN, GENERIC_ERROR
from apps.core import audit
from apps.core.models import AuditEntry, OutgoingEmail
from apps.core.models import Role as RoleModel
from apps.core.roles import reset_password, reset_totp
from conftest import NEW_PASSWORD, PASSWORD

pytestmark = pytest.mark.django_db

R = RoleModel.Code
LOGIN = "administration:login"
CODE = "administration:login_totp"
CHANGE = "administration:change_temporary_credential"


def current_code(account):
    return pyotp.TOTP(totp.secret_of(TotpDevice.objects.get(account=account))).now()


@pytest.fixture
def pair(make_admin):
    """A (administrador operatiu) i B (un altre compte d'administrador amb contrasenya)."""
    a = make_admin(R.ADMINISTRATOR, username="anna.admin")
    b = make_admin(R.TREASURER, username="bernat.tresor")
    b.set_password(PASSWORD)
    b.notification_email = "bernat@example.org"
    b.save()
    return a, b


def log_in(client, username, password):
    return client.post(reverse(LOGIN), {"login": username, "password": password})


class TestService:
    def test_temporary_credential(self, pair, caplog):
        # CA-08.1
        caplog.set_level(logging.DEBUG)
        a, b = pair
        credential = reset_password(b, by=a)
        assert re.fullmatch(r"[A-Z2-9]{4}(-[A-Z2-9]{4}){3}", credential)
        b.refresh_from_db()
        assert b.check_password(credential)
        assert not b.check_password(PASSWORD)
        assert b.password_temporary_until - timezone.now() > timedelta(hours=23, minutes=59)
        assert b.password_temporary_until - timezone.now() <= timedelta(hours=24)

        entry = AuditEntry.objects.get(action=audit.Action.PASSWORD_RESET_BY_ADMIN)
        assert entry.actor_account_id == a.pk
        assert entry.target_id == str(b.pk)
        rows = [str(row) for row in AuditEntry.objects.values_list()]
        assert not any(credential in row for row in rows)
        assert not any(credential in record.getMessage() for record in caplog.records)

    def test_notice_without_link_or_credential(self, pair):
        # CA-08.4 i RN-17
        a, b = pair
        credential = reset_password(b, by=a)
        email = OutgoingEmail.objects.get(template="restabliment-acces")
        assert email.to_address == "bernat@example.org"
        text = email.subject + email.body_text + email.body_html
        assert credential not in text
        assert "http" not in text
        assert "bernat.tresor" not in text
        assert "contrasenya" in email.body_text

    def test_totp_reset_also_sends_the_notice(self, pair):
        a, b = pair
        reset_totp(b, by=a)
        email = OutgoingEmail.objects.get(template="restabliment-acces")
        assert "doble factor" in email.body_text
        assert "http" not in email.body_text

    def test_no_notice_without_a_notification_email(self, pair):
        a, b = pair
        b.notification_email = ""
        b.save()
        reset_password(b, by=a)
        assert not OutgoingEmail.objects.exists()

    def test_nobody_resets_their_own_account(self, pair):
        # CA-08.2 i RN-16
        a, _ = pair
        with pytest.raises(ValidationError):
            reset_password(a, by=a)

    @pytest.mark.parametrize("role", [R.PRESIDENT, R.TREASURER, R.SECRETARY])
    def test_only_with_m4(self, make_admin, pair, role):
        _, b = pair
        with pytest.raises(Http404):
            reset_password(b, by=make_admin(role))
        b.refresh_from_db()
        assert b.check_password(PASSWORD)

    def test_never_a_personal_account(self, pair, personal_account):
        a, _ = pair
        with pytest.raises(ValidationError):
            reset_password(personal_account, by=a)
        personal_account.refresh_from_db()
        assert personal_account.password_temporary_until is None

    def test_a_new_reset_kills_the_previous_credential(self, pair):
        a, b = pair
        first = reset_password(b, by=a)
        second = reset_password(b, by=a)
        b.refresh_from_db()
        assert not b.check_password(first)
        assert b.check_password(second)

    def test_open_sessions_are_closed(self, pair, login_as):
        a, b = pair
        session = login_as(b, AREA_ADMIN)
        assert session.get(reverse("administration:home")).status_code == 200
        reset_password(b, by=a)
        assert session.get(reverse("administration:home")).status_code == 302

    def test_totp_and_lockout_are_left_alone(self, pair):
        a, b = pair
        b.locked_until = timezone.now() + timedelta(minutes=10)
        b.save()
        reset_password(b, by=a)
        b.refresh_from_db()
        assert b.has_totp
        assert b.is_locked(timezone.now())


class TestEntryWithTemporaryCredential:
    def test_must_change_before_getting_a_session(self, client, pair):
        # CA-08.1: «B ha de canviar en entrar».
        a, b = pair
        credential = reset_password(b, by=a)
        assert log_in(client, "bernat.tresor", credential)["Location"] == reverse(CODE)
        response = client.post(reverse(CODE), {"code": current_code(b)})
        assert response["Location"] == reverse(CHANGE)
        assert "_auth_user_id" not in client.session
        assert client.get(reverse("administration:home")).status_code == 302

        same = client.post(
            reverse(CHANGE), {"new_password1": credential, "new_password2": credential}
        )
        assert same.context["form"].has_error("new_password1")

        new = NEW_PASSWORD
        done = client.post(reverse(CHANGE), {"new_password1": new, "new_password2": new})
        assert done["Location"] == reverse("administration:home")
        assert "_auth_user_id" in client.session
        b.refresh_from_db()
        assert b.password_temporary_until is None
        assert b.check_password(new)
        entry = AuditEntry.objects.get(action=audit.Action.PASSWORD_CHANGED)
        assert entry.actor_account_id == b.pk
        assert entry.details == {"after_reset": True}

    def test_change_needs_the_second_factor_first(self, client, pair):
        a, b = pair
        credential = reset_password(b, by=a)
        log_in(client, "bernat.tresor", credential)
        new = NEW_PASSWORD
        response = client.post(reverse(CHANGE), {"new_password1": new, "new_password2": new})
        assert response["Location"] == reverse(LOGIN)
        b.refresh_from_db()
        assert b.check_password(credential)

    def test_change_without_any_pending_entry(self, client):
        assert client.get(reverse(CHANGE))["Location"] == reverse(LOGIN)

    def test_expired_credential_is_refused(self, client, pair):
        a, b = pair
        credential = reset_password(b, by=a)
        Account.objects.filter(pk=b.pk).update(
            password_temporary_until=timezone.now() - timedelta(seconds=1)
        )
        response = log_in(client, "bernat.tresor", credential)
        assert escape(str(GENERIC_ERROR)) in response.content.decode()
        assert FailedLogin.objects.filter(account=b).count() == 1

    def test_password_and_totp_reset_together(self, client, pair):
        a, b = pair
        reset_totp(b, by=a)
        credential = reset_password(b, by=a)
        assert log_in(client, "bernat.tresor", credential)["Location"] == reverse(
            "administration:totp_enrol"
        )
        client.get(reverse("administration:totp_enrol"))
        codes_page = client.post(reverse("administration:totp_enrol"), {"code": current_code(b)})
        assert codes_page.context["continue_url"] == reverse(CHANGE)
        assert "_auth_user_id" not in client.session
        new = NEW_PASSWORD
        client.post(reverse(CHANGE), {"new_password1": new, "new_password2": new})
        assert "_auth_user_id" in client.session

    def test_a_reset_during_a_pending_entry_cancels_it(self, client, pair):
        # L'estat pendent depèn de l'empremta del compte: qui tenia la contrasenya anterior i
        # era al pas del codi no pot acabar d'entrar després del restabliment.
        a, b = pair
        log_in(client, "bernat.tresor", PASSWORD)
        reset_totp(b, by=a)
        assert client.get(reverse(CODE))["Location"] == reverse(LOGIN)
        assert client.get(reverse("administration:totp_enrol"))["Location"] == reverse(LOGIN)
        assert not TotpDevice.objects.filter(account=b).exists()


class TestAccountsList:
    def test_administrator_sees_the_list(self, pair, login_as):
        a, b = pair
        page = login_as(a, AREA_ADMIN).get(reverse("administration:accounts"))
        assert page.status_code == 200
        html = page.content.decode()
        assert "anna.admin" in html and "bernat.tresor" in html

    @pytest.mark.parametrize("role", [R.PRESIDENT, R.TREASURER])
    def test_without_m4_not_found(self, make_admin, login_as, role):
        assert (
            login_as(make_admin(role), AREA_ADMIN)
            .get(reverse("administration:accounts"))
            .status_code
            == 404
        )

    def test_link_only_with_m4(self, pair, login_as, make_admin):
        a, _ = pair
        url = reverse("administration:accounts")
        assert url in login_as(a, AREA_ADMIN).get(reverse("administration:home")).content.decode()
        other = type(login_as(a, AREA_ADMIN))()
        other.force_login(make_admin(R.PRESIDENT))
        session = other.session
        session["auth_area"] = AREA_ADMIN
        session["auth_at"] = timezone.now().timestamp()
        session.save()
        assert url not in other.get(reverse("administration:home")).content.decode()

    def test_personal_session_cannot_open_it(self, personal_account, login_as):
        response = login_as(personal_account, "personal").get(reverse("administration:accounts"))
        assert response.status_code == 302
