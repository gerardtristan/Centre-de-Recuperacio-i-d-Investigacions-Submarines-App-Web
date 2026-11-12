"""Concurrència amb PostgreSQL real: peticions alhora, cadascuna amb la seva connexió.

Fan servir `CommittedDataTestCase` (vegeu `conftest.py`): les dades es confirmen de debò
perquè els altres fils les vegin, i s'esborren en acabar. Només dades inventades.

Inclou la prova de càrrega de la checklist C3 (limitació de peticions i bloqueig temporal),
amb el criteri de V-01: amb moltes peticions alhora, el compte i l'origen es bloquegen igual
que amb peticions d'una en una, i no s'avaluen més contrasenyes de les que permet el límit.
"""

import copy
import time
from unittest import mock

from django.core import signing
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts import email_links, limits, tokens
from apps.accounts.models import Account, EmailLinkRequest, FailedLogin, TotpDevice
from apps.accounts.security import ACCOUNT_MAX_FAILURES, IP_MAX_FAILURES
from apps.core import audit
from apps.core.crypto import encrypt
from apps.core.models import AuditEntry, OutgoingEmail, Person
from conftest import (
    NEW_PASSWORD,
    OTHER_PASSWORD,
    PASSWORD,
    CommittedDataTestCase,
    run_together,
)

WRONG = "no-es-aquesta"


def make_account(email="anna@example.org", status=Account.Status.PENDING):
    person = Person.objects.create(first_name="Anna", last_name="Puig", origin=Person.Origin.WEB)
    account = Account.objects.create_personal(person, email, PASSWORD)
    if status != Account.Status.PENDING:
        account.status = status
        account.save()
    return account


def login_attempt(ip, login, password=WRONG):
    def attempt():
        client = Client(REMOTE_ADDR=ip)
        client.post(reverse("accounts:login"), {"login": login, "password": password})
        return "_auth_user_id" in client.session

    return attempt


def passwords_checked(reason="bad_password"):
    """Intents en què s'ha arribat a comparar la contrasenya (no rebutjats abans pel límit)."""
    return AuditEntry.objects.filter(
        action=audit.Action.LOGIN_FAILED, details__reason=reason
    ).count()


class TestSingleUse(CommittedDataTestCase):
    def test_two_simultaneous_confirmations_verify_once(self):
        account = make_account()
        token = tokens.make_token(account, tokens.VERIFY_EMAIL)

        results = run_together([lambda: email_links.confirm_email(token)] * 2)

        assert sum(result is not None for result in results) == 1
        account.refresh_from_db()
        assert account.status == Account.Status.ACTIVE
        assert AuditEntry.objects.filter(action=audit.Action.EMAIL_VERIFIED).count() == 1

    def test_two_simultaneous_resets_change_the_password_once(self):
        account = make_account(status=Account.Status.ACTIVE)
        token = tokens.make_token(account, tokens.RESET_PASSWORD)
        first = {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD}
        second = {"new_password1": OTHER_PASSWORD, "new_password2": OTHER_PASSWORD}

        results = run_together(
            [
                lambda: email_links.reset_password(token, first),
                lambda: email_links.reset_password(token, second),
            ]
        )

        assert sum(result.done for result in results) == 1
        winner = first if results[0].done else second
        account.refresh_from_db()
        assert account.check_password(winner["new_password1"])
        assert AuditEntry.objects.filter(action=audit.Action.PASSWORD_RESET).count() == 1


class TestLoadC3(CommittedDataTestCase):
    """CK C3: prova de càrrega i bloqueig temporal de l'entrada (V-01)."""

    def test_burst_on_one_account_from_many_origins(self):
        # 30 contrasenyes alhora contra un compte, cadascuna des d'un origen diferent: el límit
        # per origen no hi intervé, només el del compte.
        account = make_account(status=Account.Status.ACTIVE)
        attempts = [login_attempt(f"10.0.0.{i}", "anna@example.org") for i in range(1, 31)]

        assert not any(run_together(attempts))

        account.refresh_from_db()
        assert account.is_locked(timezone.now())
        assert passwords_checked() <= ACCOUNT_MAX_FAILURES
        assert FailedLogin.objects.filter(account=account).count() == 30
        # Bloquejat: ni la contrasenya bona obre sessió.
        assert not login_attempt("10.0.1.1", "anna@example.org", PASSWORD)()

    def test_burst_from_one_origin_against_many_accounts(self):
        # Des d'un sol origen, contra comptes diferents: el límit per origen.
        for i in range(40):
            make_account(f"soci{i}@example.org", status=Account.Status.ACTIVE)
        attempts = [login_attempt("10.9.9.9", f"soci{i}@example.org") for i in range(40)]

        assert not any(run_together(attempts))

        assert passwords_checked() <= IP_MAX_FAILURES
        assert FailedLogin.objects.filter(ip_address="10.9.9.9").count() <= IP_MAX_FAILURES
        assert AuditEntry.objects.filter(action=audit.Action.IP_BLOCKED).exists()
        # Origen bloquejat: ni amb dades bones.
        assert not login_attempt("10.9.9.9", "soci0@example.org", PASSWORD)()
        # Un altre origen continua entrant amb normalitat.
        assert login_attempt("10.9.9.8", "soci0@example.org", PASSWORD)()

    def test_burst_at_the_edge_of_the_origin_limit(self):
        # 19 intents ja fets; 10 més alhora: només n'hi cap un abans del bloqueig.
        make_account(status=Account.Status.ACTIVE)
        for _ in range(IP_MAX_FAILURES - 1):
            FailedLogin.objects.create(ip_address="10.8.8.8", area="personal")
        attempts = [login_attempt("10.8.8.8", f"ningu{i}@example.org") for i in range(10)]

        run_together(attempts)

        assert FailedLogin.objects.filter(ip_address="10.8.8.8").count() == IP_MAX_FAILURES
        assert passwords_checked("unknown_login") == 1

    def test_burst_of_codes_on_one_account(self):
        # Qui ja té la contrasenya prova codis TOTP alhora des de 30 entrades a mig fer.
        account = make_account(status=Account.Status.ACTIVE)
        TotpDevice.objects.create(
            account=account,
            secret_encrypted=encrypt("JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP"),
            confirmed_at=timezone.now(),
        )
        clients = []
        for i in range(30):
            client = Client(REMOTE_ADDR=f"10.1.0.{i}")
            client.post(
                reverse("accounts:login"), {"login": "anna@example.org", "password": PASSWORD}
            )
            clients.append(client)

        def guess(client):
            return lambda: client.post(reverse("accounts:login_totp"), {"code": "000000"})

        run_together([guess(client) for client in clients])

        account.refresh_from_db()
        assert account.is_locked(timezone.now())
        assert passwords_checked("bad_code") <= ACCOUNT_MAX_FAILURES


def slow(function):
    """Versió lenta d'una comprovació: eixampla la finestra entre llegir el comptador i desar
    la petició, perquè una cursa es vegi a la prova si la serialització falla."""

    def wrapper(*args, **kwargs):
        result = function(*args, **kwargs)
        time.sleep(0.05)
        return result

    return wrapper


class TestLinkLimitsConcurrent(CommittedDataTestCase):
    """RN-M01-58 amb peticions simultànies (CA-M01-49 i CA-M01-50)."""

    def setUp(self):
        for name in ("origin_limited", "recipient_limited"):
            patcher = mock.patch.object(limits, name, slow(getattr(limits, name)))
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_burst_to_one_recipient_from_many_origins(self):
        make_account(status=Account.Status.ACTIVE)

        def ask(ip):
            return lambda: Client(REMOTE_ADDR=ip).post(
                reverse("accounts:password_reset_request"), {"email": "anna@example.org"}
            )

        run_together([ask(f"10.6.0.{i}") for i in range(12)])

        hour = limits.RECIPIENT_WINDOWS[0]
        assert OutgoingEmail.objects.filter(template="recuperacio-contrasenya").count() == (
            hour.max_count
        )

    def test_burst_from_one_origin(self):
        def ask(i):
            return lambda: Client(REMOTE_ADDR="10.6.1.1").post(
                reverse("accounts:password_reset_request"), {"email": f"ningu{i}@example.org"}
            )

        run_together([ask(i) for i in range(25)])

        accepted = EmailLinkRequest.objects.filter(ip_address="10.6.1.1").count()
        assert accepted == limits.ORIGIN_WINDOW.max_count
        # No toca l'entrada: cap intent fallit ni cap bloqueig.
        assert not FailedLogin.objects.exists()

    # Reenviaments de la verificació alhora (066). Cada fil fa servir el seu propi client de
    # proves; l'estat de 10 minuts es prepara abans, d'un en un, amb la contrasenya correcta.

    @staticmethod
    def pending_browser(ip, email="anna@example.org", session_of=None):
        """Un navegador amb l'estat del reenviament. Amb `session_of`, una altra pestanya del
        mateix navegador: un client nou amb la mateixa galeta de sessió (el mateix estat)."""
        browser = Client(REMOTE_ADDR=ip)
        if session_of is not None:
            # Una còpia: cap objecte del client es comparteix entre fils.
            browser.cookies = copy.deepcopy(session_of.cookies)
            return browser
        browser.post(reverse("accounts:login"), {"login": email, "password": PASSWORD})
        assert email_links.RESEND_SESSION_KEY in browser.session
        return browser

    @staticmethod
    def resend(browser):
        return lambda: browser.post(reverse("accounts:resend_verification")).status_code

    @staticmethod
    def limited(scope):
        return AuditEntry.objects.filter(
            action=audit.Action.EMAIL_LINK_LIMITED, details__scope=scope
        ).count()

    def test_resends_to_one_recipient_from_many_origins(self):
        # Límit per destinatari: 12 navegadors del mateix compte pendent, cadascun amb la seva
        # sessió i el seu origen. Només en surten 3; la resta compten per al seu origen.
        make_account()
        browsers = [self.pending_browser(f"10.6.2.{i}") for i in range(12)]

        assert run_together([self.resend(b) for b in browsers]) == [303] * 12

        hour = limits.RECIPIENT_WINDOWS[0]
        assert OutgoingEmail.objects.filter(template="verificacio-correu").count() == (
            hour.max_count
        )
        assert self.limited("recipient") == 12 - hour.max_count
        assert EmailLinkRequest.objects.filter(ip_address__startswith="10.6.2.").count() == 12

    def test_resends_from_one_origin_for_many_accounts(self):
        # Límit per origen: 14 comptes pendents diferents des d'una sola IP, cadascun amb el
        # seu navegador. Cap destinatari arriba al seu límit; només n'accepta 10 l'origen.
        browsers = []
        for i in range(14):
            make_account(f"soci{i}@example.org")
            browsers.append(self.pending_browser("10.6.3.1", f"soci{i}@example.org"))

        run_together([self.resend(b) for b in browsers])

        window = limits.ORIGIN_WINDOW
        assert EmailLinkRequest.objects.filter(ip_address="10.6.3.1").count() == (window.max_count)
        assert OutgoingEmail.objects.filter(template="verificacio-correu").count() == (
            window.max_count
        )
        assert self.limited("origin") == 14 - window.max_count
        assert not FailedLogin.objects.exists()

    def test_resends_from_one_state_in_many_tabs(self):
        # Els dos límits alhora: 12 pestanyes amb el mateix estat i el mateix origen. Surten 3
        # (destinatari); 7 més queden limitades per destinatari però compten, i fan les 10 de
        # l'origen; les 2 últimes queden limitades per origen.
        make_account()
        first = self.pending_browser("10.6.4.1")
        tabs = [first] + [self.pending_browser("10.6.4.1", session_of=first) for _ in range(11)]

        run_together([self.resend(tab) for tab in tabs])

        hour, window = limits.RECIPIENT_WINDOWS[0], limits.ORIGIN_WINDOW
        assert OutgoingEmail.objects.filter(template="verificacio-correu").count() == (
            hour.max_count
        )
        assert EmailLinkRequest.objects.filter(ip_address="10.6.4.1").count() == (window.max_count)
        assert self.limited("recipient") == window.max_count - hour.max_count
        assert self.limited("origin") == 12 - window.max_count

    def test_two_different_links_of_the_same_operation_at_once(self):
        # CA-M01-52: dos enllaços vigents i diferents, fets servir alhora: només un.
        account = make_account(status=Account.Status.ACTIVE)
        earlier = time.time() - 60
        with mock.patch.object(signing.time, "time", lambda: earlier):
            first = tokens.make_token(account, tokens.RESET_PASSWORD)
        second = tokens.make_token(account, tokens.RESET_PASSWORD)
        assert first != second
        data = {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD}

        results = run_together(
            [
                lambda: email_links.reset_password(first, data),
                lambda: email_links.reset_password(second, data),
            ]
        )

        assert sum(result.done for result in results) == 1
        assert AuditEntry.objects.filter(action=audit.Action.PASSWORD_RESET).count() == 1
