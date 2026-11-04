"""Demanar enllaços pel correu: recuperació i reenviament de la verificació (spec 00, HU-04,
CA-04.3; decisió 065: RN-M01-58 i RN-M01-59, CA-M01-48 a CA-M01-52). Només dades inventades.

Les proves amb peticions simultànies són a `test_concurrency.py`.
"""

import re
import time
from datetime import timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts import email_links, limits, tokens
from apps.accounts.models import Account, EmailLinkRequest, FailedLogin
from apps.core import audit
from apps.core.models import AuditEntry, OutgoingEmail
from conftest import NEW_PASSWORD, PASSWORD

pytestmark = pytest.mark.django_db

REQUEST = "accounts:password_reset_request"
RESEND = "accounts:resend_verification"
RESET_TEMPLATE = "recuperacio-contrasenya"
VERIFY_TEMPLATE = "verificacio-correu"
WINDOW = limits.ORIGIN_WINDOW
PER_HOUR, PER_DAY = limits.RECIPIENT_WINDOWS


def ask_reset(email, ip="10.2.0.1"):
    return Client(REMOTE_ADDR=ip).post(reverse(REQUEST), {"email": email})


def sent(template, to=None):
    emails = OutgoingEmail.objects.filter(template=template)
    return emails.filter(to_address=to).count() if to else emails.count()


def page_text(response):
    return response.context["sent"]


def visible(response):
    """La resposta sense el testimoni CSRF de la pàgina, que és diferent per a cada client."""
    return re.sub(r'"X-CSRFToken": "[^"]*"', "", response.content.decode())


@pytest.fixture
def pending_account(make_person):
    return Account.objects.create_personal(
        make_person("Pere", "Roca"), "pere@example.org", PASSWORD
    )


class TestRecoveryRequest:
    def test_same_answer_for_every_address(
        self, make_person, personal_account, pending_account, admin_account
    ):
        # CA-M01-48 i CA-04.3: actiu, pendent, desactivat, d'administrador i inexistent.
        disabled = Account.objects.create_personal(
            make_person("Laia", "Mas"), "laia@example.org", PASSWORD
        )
        disabled.status = Account.Status.DISABLED
        disabled.save()
        answers = [
            ask_reset(email, ip=f"10.2.1.{i}")
            for i, email in enumerate(
                [
                    "anna@example.org",
                    "pere@example.org",
                    "laia@example.org",
                    "joan@example.org",  # correu de notificació de l'administrador
                    "joan.vila@example.org",
                    "ningu@example.org",
                ]
            )
        ]
        assert len({visible(response) for response in answers}) == 1
        assert all(response.status_code == 200 for response in answers)
        # Només el compte personal actiu rep l'enllaç (RN-M01-59: el pendent, no).
        assert sent(RESET_TEMPLATE) == 1
        assert sent(RESET_TEMPLATE, "anna@example.org") == 1

    def test_the_email_works_end_to_end(self, client, personal_account):
        # CK C4 de principi a fi: petició, correu de la cua, enllaç i contrasenya nova.
        ask_reset(" ANNA@example.org ")
        email = OutgoingEmail.objects.get(template=RESET_TEMPLATE)
        link = next(word for word in email.body_text.split() if word.startswith("http"))
        path = "/" + link.split("://", 1)[1].split("/", 1)[1]
        client.get(path)
        done = client.post(
            reverse("accounts:password_reset"),
            {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD},
        )
        assert done.context["state"] == "done"
        personal_account.refresh_from_db()
        assert personal_account.check_password(NEW_PASSWORD)

    def test_message_and_email_say_one_hour(self, personal_account):
        response = ask_reset("anna@example.org")
        assert "caduca d'aquí a 1 hora i només serveix una vegada" in page_text(response)
        assert "48" not in page_text(response)
        email = OutgoingEmail.objects.get(template=RESET_TEMPLATE)
        assert "caduca d'aquí a 1 hora" in email.body_text

    def test_invalid_address_shows_the_form_again(self):
        response = Client().post(reverse(REQUEST), {"email": "no-es-un-correu"})
        assert response.context["form"].has_error("email")
        assert not EmailLinkRequest.objects.exists()

    def test_no_address_is_stored_only_a_fingerprint(self, personal_account):
        ask_reset("anna@example.org")
        ask_reset("ningu@example.org")
        rows = list(EmailLinkRequest.objects.order_by("pk"))
        assert [bool(row.recipient_hash) for row in rows] == [True, False]
        stored = str(list(EmailLinkRequest.objects.values_list()))
        assert "anna" not in stored and "ningu" not in stored
        entry = AuditEntry.objects.get(action=audit.Action.EMAIL_LINK_SENT)
        assert entry.target_id == str(personal_account.pk)
        assert entry.details == {"purpose": "reset"}
        assert "anna@" not in str(AuditEntry.objects.values_list())

    def test_does_not_touch_the_entry(self, client, personal_account):
        for _ in range(WINDOW.max_count + 3):
            ask_reset("ningu@example.org", ip="10.2.9.9")
        # El límit de l'entrada és un altre: la persona entra amb normalitat des d'aquí.
        entry = Client(REMOTE_ADDR="10.2.9.9")
        entry.post(reverse("accounts:login"), {"login": "anna@example.org", "password": PASSWORD})
        assert "_auth_user_id" in entry.session
        assert not FailedLogin.objects.exists()
        personal_account.refresh_from_db()
        assert personal_account.failed_login_count == 0


class TestRecipientLimit:
    def test_per_hour(self, personal_account):
        # CA-M01-49: per a cada adreça i finalitat, vinguin d'on vinguin.
        answers = [
            ask_reset("anna@example.org", ip=f"10.3.0.{i}") for i in range(PER_HOUR.max_count + 2)
        ]
        assert sent(RESET_TEMPLATE) == PER_HOUR.max_count
        assert len({visible(response) for response in answers}) == 1
        limited = AuditEntry.objects.filter(action=audit.Action.EMAIL_LINK_LIMITED)
        assert limited.count() == 2
        assert limited.first().details == {"purpose": "reset", "scope": "recipient"}

    def test_per_day(self, personal_account):
        key = limits.recipient_key("anna@example.org")
        for hours_ago in range(2, 2 + PER_DAY.max_count - 1):
            row = EmailLinkRequest.objects.create(
                ip_address="10.3.1.1", purpose="reset", recipient_hash=key
            )
            EmailLinkRequest.objects.filter(pk=row.pk).update(
                created_at=timezone.now() - timedelta(hours=hours_ago)
            )
        ask_reset("anna@example.org")
        assert sent(RESET_TEMPLATE) == 1  # el sisè del dia
        ask_reset("anna@example.org", ip="10.3.1.2")
        assert sent(RESET_TEMPLATE) == 1  # el setè, no

    def test_limited_requests_do_not_extend_the_window(self, personal_account):
        for i in range(PER_HOUR.max_count + 4):
            ask_reset("anna@example.org", ip=f"10.3.2.{i}")
        stored = EmailLinkRequest.objects.exclude(recipient_hash="")
        assert stored.count() == PER_HOUR.max_count
        key = limits.recipient_key("anna@example.org")
        later = timezone.now() + PER_HOUR.period + timedelta(seconds=1)
        assert not limits.recipient_limited(key, "reset", now=later)

    def test_each_purpose_has_its_own_limit(self, client, pending_account):
        pending_account.status = Account.Status.ACTIVE
        pending_account.save()
        for i in range(PER_HOUR.max_count):
            ask_reset("pere@example.org", ip=f"10.3.3.{i}")
        pending_account.status = Account.Status.PENDING
        pending_account.save()
        client.post(reverse("accounts:login"), {"login": "pere@example.org", "password": PASSWORD})
        client.post(reverse(RESEND))
        assert sent(VERIFY_TEMPLATE, "pere@example.org") == 1


class TestOriginLimit:
    def test_joint_for_recovery_and_resend(self, pending_account):
        # CA-M01-50: les dues finalitats sumen al mateix límit per origen.
        ip = "10.4.0.1"
        for _ in range(WINDOW.max_count - 1):
            ask_reset("ningu@example.org", ip=ip)
        resend = Client(REMOTE_ADDR=ip)
        resend.post(reverse("accounts:login"), {"login": "pere@example.org", "password": PASSWORD})
        resend.post(reverse(RESEND))  # la desena, acceptada
        assert sent(VERIFY_TEMPLATE) == 1
        assert EmailLinkRequest.objects.filter(ip_address=ip).count() == WINDOW.max_count

        resend.post(reverse("accounts:login"), {"login": "pere@example.org", "password": PASSWORD})
        resend.post(reverse(RESEND))  # l'onzena, limitada
        assert sent(VERIFY_TEMPLATE) == 1
        assert EmailLinkRequest.objects.filter(ip_address=ip).count() == WINDOW.max_count
        entry = AuditEntry.objects.filter(action=audit.Action.EMAIL_LINK_LIMITED).get()
        assert entry.details == {"purpose": "verify", "scope": "origin"}

    def test_fifteen_minutes_from_the_tenth_and_no_extension(self, personal_account):
        ip = "10.4.1.1"
        for _ in range(WINDOW.max_count):
            ask_reset("ningu@example.org", ip=ip)
        tenth = EmailLinkRequest.objects.filter(ip_address=ip).latest("created_at").created_at
        for _ in range(5):
            ask_reset("anna@example.org", ip=ip)  # limitades: ni s'envien ni compten
        assert sent(RESET_TEMPLATE) == 0
        assert EmailLinkRequest.objects.filter(ip_address=ip).count() == WINDOW.max_count
        assert limits.origin_limited(ip, now=tenth + limits.ORIGIN_COOLDOWN - timedelta(seconds=1))
        assert not limits.origin_limited(ip, now=tenth + limits.ORIGIN_COOLDOWN)

    def test_after_the_cooldown_it_accepts_again(self, personal_account):
        ip = "10.4.2.1"
        for _ in range(WINDOW.max_count):
            ask_reset("ningu@example.org", ip=ip)
        EmailLinkRequest.objects.filter(ip_address=ip).update(
            created_at=timezone.now() - limits.ORIGIN_COOLDOWN - timedelta(seconds=1)
        )
        ask_reset("anna@example.org", ip=ip)
        assert sent(RESET_TEMPLATE) == 1

    @pytest.mark.parametrize(
        "target",
        [
            "anna@example.org",  # compte actiu: 3 enviades i la resta limitades per destinatari
            "ningu@example.org",  # sense compte
            "pere@example.org",  # pendent: no rep recuperació
        ],
    )
    def test_the_origin_counts_the_same_with_or_without_an_account(
        self, make_person, personal_account, pending_account, target
    ):
        # RN-M01-58 amb el text de la 066: les limitades per destinatari compten per a
        # l'origen. Si no, deu peticions per a una adreça i una per a una bústia pròpia
        # dirien si l'adreça té compte actiu (la pròpia rebria el correu només en aquest cas).
        own = Account.objects.create_personal(
            make_person("Joan", "Vila"), "propia@example.org", PASSWORD
        )
        own.status = Account.Status.ACTIVE
        own.save()
        ip = "10.4.4.1"
        for _ in range(WINDOW.max_count):
            ask_reset(target, ip=ip)
        assert EmailLinkRequest.objects.filter(ip_address=ip).count() == WINDOW.max_count
        assert limits.origin_limited(ip)
        ask_reset("propia@example.org", ip=ip)
        assert sent(RESET_TEMPLATE, "propia@example.org") == 0

    def test_other_origins_are_not_affected(self, personal_account):
        for _ in range(WINDOW.max_count + 1):
            ask_reset("ningu@example.org", ip="10.4.3.1")
        ask_reset("anna@example.org", ip="10.4.3.2")
        assert sent(RESET_TEMPLATE) == 1


class TestResendVerification:
    def login(self, client, password=PASSWORD):
        return client.post(
            reverse("accounts:login"), {"login": "pere@example.org", "password": password}
        )

    def test_offered_only_after_the_right_password(self, client, pending_account):
        # CA-M01-51
        wrong = self.login(client, "no-es-aquesta")
        assert not wrong.context["can_resend"]
        assert email_links.RESEND_SESSION_KEY not in client.session
        right = self.login(client)
        assert right.context["can_resend"]
        assert "Encara has de confirmar el correu" in right.content.decode()
        assert reverse(RESEND) in right.content.decode()

    def test_not_offered_to_active_accounts(self, client, personal_account):
        response = Client().post(
            reverse("accounts:login"), {"login": "anna@example.org", "password": "no-es-aquesta"}
        )
        assert not response.context["can_resend"]

    def test_resends_go_to_the_account_address(self, client, pending_account):
        self.login(client)
        # Una adreça enviada pel navegador no es fa servir mai.
        response = client.post(reverse(RESEND), {"email": "atacant@example.org"})
        assert not response.context["expired"]
        assert "48 hores" in response.context["message"]
        assert "1 hora" not in response.context["message"]
        assert sent(VERIFY_TEMPLATE) == 1
        assert sent(VERIFY_TEMPLATE, "pere@example.org") == 1
        # 066: l'estat no és d'un sol ús; dins dels 10 minuts se'n pot demanar un altre.
        again = client.post(reverse(RESEND))
        assert not again.context["expired"]
        assert sent(VERIFY_TEMPLATE, "pere@example.org") == 2
        assert sent(VERIFY_TEMPLATE) == 2

    def test_resends_follow_the_recipient_limit(self, client, pending_account):
        # 066: sense el límit d'un sol ús, el límit per destinatari de RN-M01-58 continua.
        self.login(client)
        answers = [client.post(reverse(RESEND)) for _ in range(PER_HOUR.max_count + 1)]
        assert sent(VERIFY_TEMPLATE, "pere@example.org") == PER_HOUR.max_count
        assert len({response.context["message"] for response in answers}) == 1
        assert not any(response.context["expired"] for response in answers)
        limited = AuditEntry.objects.filter(action=audit.Action.EMAIL_LINK_LIMITED).get()
        assert limited.details == {"purpose": "verify", "scope": "recipient"}

    def limited(self, scope):
        return AuditEntry.objects.filter(
            action=audit.Action.EMAIL_LINK_LIMITED, details__scope=scope
        ).count()

    def test_the_same_state_cannot_bypass_the_origin_limit(self, pending_account):
        # 066: el mateix estat de 10 minuts, sense tornar a escriure la contrasenya. Des d'un
        # origen amb 6 peticions acceptades: 3 reenviaments s'envien, el quart queda limitat
        # per destinatari (i compta: ja en són 10) i el cinquè, per origen.
        ip = "10.5.0.1"
        for _ in range(WINDOW.max_count - PER_HOUR.max_count - 1):
            ask_reset("ningu@example.org", ip=ip)
        browser = Client(REMOTE_ADDR=ip)
        self.login(browser)
        answers = [browser.post(reverse(RESEND)) for _ in range(PER_HOUR.max_count + 2)]

        assert sent(VERIFY_TEMPLATE, "pere@example.org") == PER_HOUR.max_count
        sent_entries = AuditEntry.objects.filter(action=audit.Action.EMAIL_LINK_SENT)
        assert sent_entries.count() == PER_HOUR.max_count
        assert self.limited("recipient") == 1
        assert self.limited("origin") == 1
        assert EmailLinkRequest.objects.filter(ip_address=ip).count() == WINDOW.max_count
        # La resposta és la mateixa en els tres casos, i l'estat continua vàlid.
        assert len({response.context["message"] for response in answers}) == 1
        assert not any(response.context["expired"] for response in answers)

    def test_recipient_limited_resends_count_for_the_origin(self, pending_account):
        # RN-M01-58 amb el text de la 066, amb reenviaments: 3 enviats i 7 limitats per
        # destinatari fan les 10 de l'origen; els següents queden limitats per origen i no
        # allarguen la finestra, que s'acaba 15 minuts després de la desena.
        ip = "10.5.1.1"
        browser = Client(REMOTE_ADDR=ip)
        self.login(browser)
        for _ in range(WINDOW.max_count):
            browser.post(reverse(RESEND))
        assert sent(VERIFY_TEMPLATE) == PER_HOUR.max_count
        assert self.limited("recipient") == WINDOW.max_count - PER_HOUR.max_count
        rows = EmailLinkRequest.objects.filter(ip_address=ip)
        assert rows.count() == WINDOW.max_count
        tenth = rows.latest("created_at").created_at
        assert limits.origin_limited(ip)

        for _ in range(5):
            browser.post(reverse(RESEND))
        assert self.limited("origin") == 5
        assert rows.count() == WINDOW.max_count
        assert rows.latest("created_at").created_at == tenth
        assert limits.origin_limited(ip, now=tenth + limits.ORIGIN_COOLDOWN - timedelta(seconds=1))
        assert not limits.origin_limited(ip, now=tenth + limits.ORIGIN_COOLDOWN)
        assert sent(VERIFY_TEMPLATE) == PER_HOUR.max_count

    def test_each_resend_checks_the_state_again(self, client, pending_account):
        self.login(client)
        client.post(reverse(RESEND))
        assert sent(VERIFY_TEMPLATE) == 1
        pending_account.status = Account.Status.ACTIVE
        pending_account.save()
        response = client.post(reverse(RESEND))
        assert not response.context["expired"]  # la resposta no diu res de l'estat
        assert sent(VERIFY_TEMPLATE) == 1

    def test_the_state_expires(self, client, pending_account):
        self.login(client)
        session = client.session
        state = session[email_links.RESEND_SESSION_KEY]
        state["at"] = time.time() - limits.RESEND_STATE.total_seconds() - 1
        session[email_links.RESEND_SESSION_KEY] = state
        session.save()
        assert client.post(reverse(RESEND)).context["expired"]
        assert sent(VERIFY_TEMPLATE) == 0

    def test_state_is_checked_again_before_sending(self, client, pending_account):
        self.login(client)
        pending_account.status = Account.Status.ACTIVE
        pending_account.save()
        response = client.post(reverse(RESEND))
        assert not response.context["expired"]  # la resposta no diu res de l'estat
        assert sent(VERIFY_TEMPLATE) == 0

    def test_without_the_state(self):
        response = Client().post(reverse(RESEND))
        assert response.context["expired"]
        assert sent(VERIFY_TEMPLATE) == 0

    def test_the_state_is_not_a_session(self, client, pending_account):
        self.login(client)
        assert "_auth_user_id" not in client.session
        for name in ("core:home", "accounts:security", "accounts:totp_enrol"):
            assert client.get(reverse(name)).status_code == 302

    def test_only_post(self, client):
        assert client.get(reverse(RESEND)).status_code == 405


class TestLinksOfTheSameOperation:
    def test_using_one_reset_link_kills_the_others(self, client, monkeypatch, personal_account):
        # CA-M01-52: dos enllaços vigents de la mateixa operació.
        from django.core import signing

        earlier = time.time() - 60
        with monkeypatch.context() as patch:
            patch.setattr(signing.time, "time", lambda: earlier)
            first = tokens.make_token(personal_account, tokens.RESET_PASSWORD)
        second = tokens.make_token(personal_account, tokens.RESET_PASSWORD)
        assert first != second
        result = email_links.reset_password(
            second,
            {"new_password1": NEW_PASSWORD, "new_password2": NEW_PASSWORD},
        )
        assert result.done
        assert tokens.account_for_token(first, tokens.RESET_PASSWORD) is None


def test_old_requests_are_purged(personal_account):
    old = EmailLinkRequest.objects.create(ip_address="10.5.0.1", purpose="reset")
    EmailLinkRequest.objects.filter(pk=old.pk).update(
        created_at=timezone.now() - limits.RETENTION - timedelta(seconds=1)
    )
    recent = EmailLinkRequest.objects.create(ip_address="10.5.0.1", purpose="reset")
    assert limits.purge_old() == 1
    assert list(EmailLinkRequest.objects.values_list("pk", flat=True)) == [recent.pk]
