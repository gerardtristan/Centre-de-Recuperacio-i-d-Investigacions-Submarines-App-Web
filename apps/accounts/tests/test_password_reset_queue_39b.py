"""«He oblidat la contrasenya» amb una cua (T-M01-39b; 072, Q-084 i Q-085; pla, «T-M01-39 en
detall», part b). La petició fa la mateixa feina per a qualsevol adreça; la tasca troba el
compte per l'empremta, aplica el límit per destinatari i envia. Només dades inventades."""

import io
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.accounts import email_links, limits
from apps.accounts.models import Account, EmailLinkRequest
from apps.core import audit
from apps.core.models import AuditEntry, OutgoingEmail
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

REQUEST = "accounts:password_reset_request"
S = EmailLinkRequest.Status


def ask(email, ip="10.9.0.1"):
    return Client(REMOTE_ADDR=ip).post(reverse(REQUEST), {"email": email})


def last_row():
    return EmailLinkRequest.objects.filter(purpose="reset").latest("pk")


def sent(to=None):
    emails = OutgoingEmail.objects.filter(template="recuperacio-contrasenya")
    return emails.filter(to_address=to).count() if to else emails.count()


def process(row):
    return email_links.process_password_reset(row.pk)


@pytest.fixture
def active(personal_account):
    return personal_account  # anna@example.org, actiu


class TestRequest:
    @pytest.mark.parametrize("email", ["anna@example.org", "ningu@example.org"])
    def test_the_same_work_for_any_address(self, active, email):
        response = ask(email)
        assert response.status_code == 200
        row = last_row()
        assert (row.status, row.recipient_hash) == (S.PENDING, limits.recipient_key(email))
        job = ProcrastinateJob.objects.get(task_name="accounts.send_password_reset")
        assert job.args == {"request_id": row.pk}  # només l'identificador
        assert sent() == 0  # res no s'envia a la petició
        assert not AuditEntry.objects.exists()

    def test_an_origin_limited_request_leaves_no_row_and_no_task(self, active):
        for i in range(limits.ORIGIN_WINDOW.max_count):
            ask(f"ningu{i}@example.org", ip="10.9.1.1")
        ask("anna@example.org", ip="10.9.1.1")
        assert EmailLinkRequest.objects.filter(ip_address="10.9.1.1").count() == 10
        assert (
            ProcrastinateJob.objects.filter(task_name="accounts.send_password_reset").count() == 10
        )

    def test_the_page_says_five_minutes(self, active):
        text = ask("ningu@example.org").context["sent"]
        assert "Si d'aquí a 5 minuts no t'ha arribat, mira el correu brossa i torna-ho a" in text


class TestTask:
    def test_an_active_account_gets_the_email(self, active):
        ask(" ANNA@example.org ")
        row = last_row()
        assert process(row) == S.SENT
        row.refresh_from_db()
        assert row.recipient_hash == limits.recipient_key("anna@example.org")
        assert sent("anna@example.org") == 1
        entry = AuditEntry.objects.get(action=audit.Action.EMAIL_LINK_SENT)
        assert entry.target_id == str(active.pk) and entry.details == {"purpose": "reset"}

    def test_twice_is_still_one_email(self, active):
        ask("anna@example.org")
        row = last_row()
        process(row)
        assert process(row) == "skipped"
        assert sent() == 1

    @pytest.mark.parametrize("email", ["ningu@example.org", "joan@example.org"])
    def test_no_account_or_an_admin_address_sends_nothing(self, active, admin_account, email):
        # joan@example.org és el correu de notificació d'un administrador: mai recuperació.
        ask(email)
        row = last_row()
        assert process(row) == S.NOT_SENT
        row.refresh_from_db()
        assert row.recipient_hash == "" and sent() == 0

    @pytest.mark.parametrize("status", [Account.Status.PENDING, Account.Status.DISABLED])
    def test_pending_or_disabled_sends_nothing(self, active, status):
        active.status = status
        active.save()
        ask("anna@example.org")
        assert process(last_row()) == S.NOT_SENT
        assert sent() == 0

    def test_after_five_minutes_it_expires(self, active):
        ask("anna@example.org")
        row = last_row()
        EmailLinkRequest.objects.filter(pk=row.pk).update(
            created_at=timezone.now() - limits.RESET_MAX_DELAY - timedelta(seconds=1)
        )
        assert process(row) == S.EXPIRED
        row.refresh_from_db()
        assert row.recipient_hash == "" and sent() == 0

    def test_the_recipient_limit_is_applied_in_the_task(self, active):
        for i in range(limits.RECIPIENT_WINDOWS[0].max_count + 1):
            ask("anna@example.org", ip=f"10.9.2.{i}")
            process(last_row())
        assert sent() == limits.RECIPIENT_WINDOWS[0].max_count
        row = last_row()
        assert (row.status, row.recipient_hash) == (S.LIMITED, "")
        entry = AuditEntry.objects.get(action=audit.Action.EMAIL_LINK_LIMITED)
        assert entry.details == {"purpose": "reset", "scope": "recipient"}

    def test_pending_rows_do_not_count_for_the_recipient(self, active):
        for i in range(limits.RECIPIENT_WINDOWS[0].max_count + 2):
            ask("anna@example.org", ip=f"10.9.3.{i}")
        key = limits.recipient_key("anna@example.org")
        assert not limits.recipient_limited(key, "reset")


def test_ca_m01_50_the_origin_counts_the_same_with_and_without_an_account(make_person):
    """Prova obligatòria de la (b): el comptatge de l'origen no depèn de si el compte existeix,
    ni abans ni després d'executar la tasca."""
    account = Account.objects.create_personal(make_person(), "anna@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    for email, ip in (("anna@example.org", "10.9.4.1"), ("ningu@example.org", "10.9.4.2")):
        for _ in range(4):
            ask(email, ip=ip)
    counts = {
        ip: EmailLinkRequest.objects.filter(ip_address=ip).count()
        for ip in ("10.9.4.1", "10.9.4.2")
    }
    assert counts == {"10.9.4.1": 4, "10.9.4.2": 4}
    for row in EmailLinkRequest.objects.filter(status=S.PENDING):
        process(row)
    after = {ip: EmailLinkRequest.objects.filter(ip_address=ip).count() for ip in counts}
    assert after == counts


def test_the_login_fingerprint_follows_the_login(active):
    assert active.login_hash == limits.recipient_key("anna@example.org")
    active.login = "anna.nova@example.org"
    active.save(update_fields=["login"])
    active.refresh_from_db()
    assert active.login_hash == limits.recipient_key("anna.nova@example.org")
    ask("anna@example.org")
    assert process(last_row()) == S.NOT_SENT
    ask("anna.nova@example.org", ip="10.9.5.1")
    assert process(last_row()) == S.SENT


def test_an_admin_account_has_no_fingerprint(admin_account):
    assert admin_account.login_hash == ""


def test_the_command_recalculates_the_fingerprints(active):
    Account.objects.filter(pk=active.pk).update(login_hash="x")
    call_command("recalcula_empremtes_login", stdout=io.StringIO())
    active.refresh_from_db()
    assert active.login_hash == limits.recipient_key("anna@example.org")


def test_the_purge_expires_stale_requests_and_drops_the_ip(active):
    ask("anna@example.org")
    row = last_row()
    EmailLinkRequest.objects.filter(pk=row.pk).update(
        created_at=timezone.now() - limits.RESET_IP_RETENTION - timedelta(seconds=1)
    )
    limits.purge_old()
    row.refresh_from_db()
    assert (row.status, row.recipient_hash, row.ip_address) == (S.EXPIRED, "", None)


class TestQueueHealth:
    URL = "core:queue_health"

    def heartbeat(self, ago=timedelta(0)):
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO procrastinate_workers (last_heartbeat) VALUES (%s)",
                [timezone.now() - ago],
            )

    def test_ok_with_a_live_worker_and_nothing_waiting(self, client):
        self.heartbeat()
        response = client.get(reverse(self.URL))
        assert (response.status_code, response.content) == (200, b"ok")

    def test_error_without_a_worker(self, client):
        self.heartbeat(ago=timedelta(minutes=3))
        assert client.get(reverse(self.URL)).status_code == 503

    def test_error_with_a_request_waiting_more_than_two_minutes(self, client, active):
        self.heartbeat()
        ask("anna@example.org")
        EmailLinkRequest.objects.update(created_at=timezone.now() - timedelta(minutes=3))
        response = client.get(reverse(self.URL))
        assert (response.status_code, response.content) == (503, b"error")
