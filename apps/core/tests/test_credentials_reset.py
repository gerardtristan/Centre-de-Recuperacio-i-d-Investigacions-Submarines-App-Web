"""Restabliment per un altre administrador (spec 00, HU-08; CA-08.1, 08.2 i 08.4; RN-16, RN-17;
V-01; decisió 065: RN-M01-60 i RN-M01-61, CA-M01-53 a CA-M01-55). Servei, entrada amb la
credencial temporal, llista amb M4 i acció de la pantalla.

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
NOTE = "Ha perdut el mòbil; trucada verificada"


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
        credential = reset_password(b, by=a, note=NOTE)[0]
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
        credential = reset_password(b, by=a, note=NOTE)[0]
        email = OutgoingEmail.objects.get(template="restabliment-acces")
        assert email.to_address == "bernat@example.org"
        text = email.subject + email.body_text + email.body_html
        assert credential not in text
        assert "http" not in text
        assert "bernat.tresor" not in text
        assert "contrasenya" in email.body_text

    def test_totp_reset_also_sends_the_notice(self, pair):
        a, b = pair
        reset_totp(b, by=a, note=NOTE)
        email = OutgoingEmail.objects.get(template="restabliment-acces")
        assert "doble factor" in email.body_text
        assert "http" not in email.body_text

    def test_no_notice_without_a_notification_email(self, pair):
        # RN-M01-61 i CA-M01-55: es restableix, l'avís queda «no enviat, sense adreça» i no
        # s'avisa ningú més.
        a, b = pair
        b.notification_email = ""
        b.save()
        credential, notice = reset_password(b, by=a, note=NOTE)
        b.refresh_from_db()
        assert b.check_password(credential)
        assert not notice.queued
        assert notice.reason == "sense adreça"
        assert not OutgoingEmail.objects.exists()
        reset = AuditEntry.objects.get(action=audit.Action.PASSWORD_RESET_BY_ADMIN)
        notice_entry = AuditEntry.objects.get(action=audit.Action.RESET_NOTICE)
        assert reset.reason == NOTE
        assert notice_entry.reason == "sense adreça"
        assert notice_entry.details == {
            "result": "not_sent",
            "email_id": None,
            "second_factor": False,
        }

    def test_queued_notice_is_not_called_delivered(self, pair):
        a, b = pair
        _, notice = reset_password(b, by=a, note=NOTE)
        email = OutgoingEmail.objects.get(template="restabliment-acces")
        assert notice.queued and notice.email_id == email.pk
        entry = AuditEntry.objects.get(action=audit.Action.RESET_NOTICE)
        assert entry.details["result"] == "queued"
        assert entry.details["email_id"] == email.pk

    def test_a_reason_is_required(self, pair):
        # CA-M01-54
        a, b = pair
        with pytest.raises(ValidationError):
            reset_password(b, by=a, note="   ")
        b.refresh_from_db()
        assert b.check_password(PASSWORD)
        assert not AuditEntry.objects.filter(action=audit.Action.PASSWORD_RESET_BY_ADMIN).exists()

    def test_recovery_codes_are_kept(self, pair):
        from apps.accounts.models import RecoveryCode

        a, b = pair
        RecoveryCode.objects.create(account=b, code_hash="b" * 64)
        reset_password(b, by=a, note=NOTE)
        assert RecoveryCode.objects.filter(account=b).exists()

    def test_nobody_resets_their_own_account(self, pair):
        # CA-08.2 i RN-16
        a, _ = pair
        with pytest.raises(ValidationError):
            reset_password(a, by=a, note=NOTE)

    @pytest.mark.parametrize("role", [R.PRESIDENT, R.TREASURER, R.SECRETARY])
    def test_only_with_m4(self, make_admin, pair, role):
        _, b = pair
        with pytest.raises(Http404):
            reset_password(b, by=make_admin(role), note=NOTE)
        b.refresh_from_db()
        assert b.check_password(PASSWORD)

    def test_never_a_personal_account(self, pair, personal_account):
        a, _ = pair
        with pytest.raises(ValidationError):
            reset_password(personal_account, by=a, note=NOTE)
        personal_account.refresh_from_db()
        assert personal_account.password_temporary_until is None

    def test_a_new_reset_kills_the_previous_credential(self, pair):
        a, b = pair
        first = reset_password(b, by=a, note=NOTE)[0]
        second = reset_password(b, by=a, note=NOTE)[0]
        b.refresh_from_db()
        assert not b.check_password(first)
        assert b.check_password(second)

    def test_open_sessions_are_closed(self, pair, login_as):
        a, b = pair
        session = login_as(b, AREA_ADMIN)
        assert session.get(reverse("administration:home")).status_code == 200
        reset_password(b, by=a, note=NOTE)
        assert session.get(reverse("administration:home")).status_code == 302

    def test_totp_and_lockout_are_left_alone(self, pair):
        a, b = pair
        b.locked_until = timezone.now() + timedelta(minutes=10)
        b.save()
        reset_password(b, by=a, note=NOTE)
        b.refresh_from_db()
        assert b.has_totp
        assert b.is_locked(timezone.now())


class TestEntryWithTemporaryCredential:
    def test_must_change_before_getting_a_session(self, client, pair):
        # CA-08.1: «B ha de canviar en entrar».
        a, b = pair
        credential = reset_password(b, by=a, note=NOTE)[0]
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
        credential = reset_password(b, by=a, note=NOTE)[0]
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
        credential = reset_password(b, by=a, note=NOTE)[0]
        Account.objects.filter(pk=b.pk).update(
            password_temporary_until=timezone.now() - timedelta(seconds=1)
        )
        response = log_in(client, "bernat.tresor", credential)
        assert escape(str(GENERIC_ERROR)) in response.content.decode()
        assert FailedLogin.objects.filter(account=b).count() == 1

    def test_password_and_totp_reset_together(self, client, pair):
        a, b = pair
        reset_totp(b, by=a, note=NOTE)
        credential = reset_password(b, by=a, note=NOTE)[0]
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
        reset_totp(b, by=a, note=NOTE)
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


ACTION = "administration:reset_credentials"


def code_for(account, steps_ahead=0):
    device = TotpDevice.objects.get(account=account)
    moment = timezone.now() + timedelta(seconds=30 * steps_ahead)
    return pyotp.TOTP(totp.secret_of(device)).at(moment)


def post_reset(session, target, what="password", note=NOTE, code=None, actor=None):
    data = {"what": what, "note": note, "code": code if code is not None else code_for(actor)}
    return session.post(reverse(ACTION, args=[target.pk]), data)


class TestResetAction:
    def test_password_with_a_fresh_code_and_a_reason(self, pair, login_as):
        # CA-M01-53 i CA-08.1
        a, b = pair
        session = login_as(a, AREA_ADMIN)
        page = session.get(reverse(ACTION, args=[b.pk]))
        assert page.status_code == 200
        assert page.context["no_address_warning"] is None
        done = post_reset(session, b, actor=a)
        credential = done.context["credential"]
        b.refresh_from_db()
        assert b.check_password(credential)
        html = done.content.decode()
        assert credential in html
        assert "mai per correu" in html
        assert "lliura" not in html  # «a la cua», mai «lliurat»
        assert "no-cache" in done["Cache-Control"]

    def test_totp_reset_also_needs_the_code(self, pair, login_as):
        a, b = pair
        session = login_as(a, AREA_ADMIN)
        done = post_reset(session, b, what="totp", actor=a)
        assert done.context["credential"] is None
        assert not TotpDevice.objects.filter(account=b).exists()

    @pytest.mark.parametrize("code", ["", "000000"])
    def test_missing_or_wrong_code_resets_nothing(self, pair, login_as, code):
        a, b = pair
        session = login_as(a, AREA_ADMIN)
        response = post_reset(session, b, code=code)
        assert response.context["form"].has_error("code")
        b.refresh_from_db()
        assert b.check_password(PASSWORD)
        a.refresh_from_db()
        assert a.failed_login_count == (1 if code else 0)
        assert not AuditEntry.objects.filter(action=audit.Action.PASSWORD_RESET_BY_ADMIN).exists()

    def test_a_code_already_accepted_is_not_new(self, pair, login_as):
        # El codi de l'entrada (o qualsevol ja acceptat) no serveix: ha de ser nou.
        a, b = pair
        code = code_for(a)
        assert totp.verify_code(TotpDevice.objects.get(account=a), code)
        session = login_as(a, AREA_ADMIN)
        response = post_reset(session, b, code=code)
        assert response.context["form"].has_error("code")
        b.refresh_from_db()
        assert b.check_password(PASSWORD)
        # El següent interval sí que és nou.
        done = post_reset(session, b, code=code_for(a, steps_ahead=1))
        assert done.context["credential"]

    def test_the_actor_gets_locked_after_the_attempts_of_v01(self, pair, login_as):
        a, b = pair
        session = login_as(a, AREA_ADMIN)
        for _ in range(5):
            post_reset(session, b, code="000000")
        a.refresh_from_db()
        assert a.is_locked(timezone.now())
        response = post_reset(session, b, actor=a)
        assert response.context["form"].non_field_errors()
        b.refresh_from_db()
        assert b.check_password(PASSWORD)

    def test_reason_is_required(self, pair, login_as):
        a, b = pair
        session = login_as(a, AREA_ADMIN)
        response = post_reset(session, b, note="", actor=a)
        assert response.context["form"].has_error("note")
        b.refresh_from_db()
        assert b.check_password(PASSWORD)

    def test_without_notification_address(self, pair, login_as):
        # CA-M01-55: advertiment abans, missatge després, registre «sense adreça».
        a, b = pair
        b.notification_email = ""
        b.save()
        session = login_as(a, AREA_ADMIN)
        page = session.get(reverse(ACTION, args=[b.pk]))
        before = (
            "Aquest compte no té correu de notificació. El restabliment es pot fer, però no se "
            "li podrà enviar l&#x27;avís."
        )
        assert before in page.content.decode()
        done = post_reset(session, b, actor=a)
        after = (
            "Restabliment completat. No s&#x27;ha pogut enviar l&#x27;avís perquè el compte no "
            "té correu de notificació. Avisa la persona afectada per una altra via."
        )
        assert after in done.content.decode()
        assert done.context["credential"]
        assert not OutgoingEmail.objects.exists()
        entry = AuditEntry.objects.get(action=audit.Action.RESET_NOTICE)
        assert (entry.reason, entry.details["result"]) == ("sense adreça", "not_sent")

    def test_emergency_exception_also_needs_the_code(self, make_admin, login_as):
        # RN-RP-18 amb RN-M01-60: l'últim administrador operatiu, des d'un compte d'emergència.
        only = make_admin(R.ADMINISTRATOR, username="unic.admin")
        emergency = make_admin(R.ADMINISTRATOR, emergency=True, username="emergencia1")
        session = login_as(emergency, AREA_ADMIN)
        refused = post_reset(session, only, what="totp", code="000000")
        assert refused.context["form"].has_error("code")
        assert TotpDevice.objects.filter(account=only).exists()
        done = post_reset(session, only, what="totp", actor=emergency)
        assert done.status_code == 200
        assert not TotpDevice.objects.filter(account=only).exists()

    def test_own_account_is_refused(self, pair, login_as):
        a, _ = pair
        session = login_as(a, AREA_ADMIN)
        assert session.get(reverse(ACTION, args=[a.pk])).context["own_account"]
        response = post_reset(session, a, actor=a)
        assert response.context["form"].non_field_errors()

    @pytest.mark.parametrize("role", [R.PRESIDENT, R.TREASURER])
    def test_without_m4_not_found(self, pair, make_admin, login_as, role):
        _, b = pair
        actor = make_admin(role)
        session = login_as(actor, AREA_ADMIN)
        assert session.get(reverse(ACTION, args=[b.pk])).status_code == 404
        assert post_reset(session, b, actor=actor).status_code == 404
        b.refresh_from_db()
        assert b.check_password(PASSWORD)

    def test_personal_accounts_are_not_found(self, pair, login_as, personal_account):
        a, _ = pair
        session = login_as(a, AREA_ADMIN)
        assert session.get(reverse(ACTION, args=[personal_account.pk])).status_code == 404

    def test_no_credential_or_code_in_logs_or_activity(self, pair, login_as, caplog):
        caplog.set_level(logging.DEBUG)
        a, b = pair
        code = code_for(a)
        done = post_reset(login_as(a, AREA_ADMIN), b, code=code)
        credential = done.context["credential"]
        messages = [record.getMessage() for record in caplog.records]
        assert not any(credential in m or code in m for m in messages)
        rows = [str(row) for row in AuditEntry.objects.values_list()]
        assert not any(credential in row for row in rows)
        email = OutgoingEmail.objects.get()
        assert credential not in email.body_text + email.subject
