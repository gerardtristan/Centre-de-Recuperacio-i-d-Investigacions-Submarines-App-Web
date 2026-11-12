"""Límit diari dels correus (spec 00, annex A: RN-A3, RN-A4, RN-A6 i RN-A8; V-07; T-M00-06).
Criteris CA-A2 (part transaccional), CA-A3, CA-A4, CA-A5 i CA-A9. Només dades inventades."""

import datetime

import pytest
from django.conf import settings as django_settings
from django.core import mail as django_mail
from django.core.mail.backends.base import BaseEmailBackend
from django.test import override_settings
from django.utils import timezone
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.core import audit, mail, tasks
from apps.core.models import AuditEntry, EmailDailyUsage, OutgoingEmail
from conftest import PASSWORD, CommittedDataTestCase, run_together

pytestmark = pytest.mark.django_db

Priority = OutgoingEmail.Priority
Status = OutgoingEmail.Status
TODAY = datetime.date(2026, 11, 11)
TOMORROW = TODAY + datetime.timedelta(days=1)


class FailingBackend(BaseEmailBackend):
    def send_messages(self, messages):
        raise ConnectionError("servidor de proves no disponible")


@pytest.fixture(autouse=True)
def spec_limits(settings):
    """Els valors de la spec (RN-A3, RN-A4, RN-A6 i V-07), diguin el que diguin les variables
    d'entorn de qui executa les proves. Sense adreces: qui rep l'avís és la Q-26."""
    settings.EMAIL_DAILY_LIMIT = 300
    settings.EMAIL_TRANSACTIONAL_RESERVE = 100
    settings.EMAIL_ALERT_THRESHOLD_PCT = 80
    settings.EMAIL_ALERT_TO = []
    return settings


@pytest.fixture
def by_priority(email_templates):
    """Una plantilla inventada per a cada prioritat de V-07."""
    names = {}
    for priority in Priority:
        names[priority] = f"proves-{priority.value}"
        email_templates(names[priority], "ca", str(priority.label), "cos", priority=priority)
    return names


def _queue(template="prova", to="anna@example.org"):
    return mail.queue_email(template, to=to)


def _deliver(email, today=TODAY):
    mail.deliver(email.pk, today=today)
    email.refresh_from_db()
    return email


def _usage(day=TODAY):
    return EmailDailyUsage.objects.get(day=day)


def _alerts():
    return AuditEntry.objects.filter(action=audit.Action.EMAIL_LIMIT_ALERT)


def _send_jobs(email):
    return ProcrastinateJob.objects.filter(task_name="core.send_email", args={"email_id": email.pk})


# --- Prioritat declarada (RN-A8, V-07) ------------------------------------------------------


def test_rn_a8_every_template_of_the_project_declares_its_priority():
    """Una plantilla nova a `templates/emails/` sense prioritat declarada fa fallar aquesta
    prova; una prioritat declarada sense plantilla, també."""
    folder = django_settings.BASE_DIR / "templates" / "emails"
    names = {path.name.split(".")[0] for path in folder.glob("*.subject.txt")}

    assert names
    assert names == set(mail.TEMPLATE_PRIORITIES)
    assert set(mail.TEMPLATE_PRIORITIES.values()) <= set(Priority)


def test_rn_a8_template_without_declared_priority_is_rejected(email_templates):
    email_templates("sense-prioritat", "ca", "Assumpte", "cos", priority=None)

    with pytest.raises(ValueError, match="RN-A8"):
        mail.queue_email("sense-prioritat", to="anna@example.org")
    assert not OutgoingEmail.objects.exists()


def test_rn_a8_the_email_keeps_the_priority_of_its_template(by_priority):
    for priority, template in by_priority.items():
        assert _queue(template).priority == priority


def test_v07_priority_order():
    """V-07: comptes, enllaços de convidat, confirmacions, recordatoris i, per últim, butlletí."""
    assert sorted(Priority) == [
        Priority.ACCOUNT,
        Priority.GUEST_LINK,
        Priority.CONFIRMATION,
        Priority.REMINDER,
        Priority.NEWSLETTER,
    ]
    assert mail.TEMPLATE_PRIORITIES["recuperacio-contrasenya"] == Priority.ACCOUNT
    assert mail.TEMPLATE_PRIORITIES["verificacio-correu"] == Priority.ACCOUNT
    assert mail.TEMPLATE_PRIORITIES["recordatori-quota"] == Priority.REMINDER


# --- Comptador diari (RN-A3) ----------------------------------------------------------------


def test_rn_a3_each_email_counts_once_on_the_day_of_its_first_attempt():
    first, second = _deliver(_queue()), _deliver(_queue(to="berta@example.org"))

    assert (first.status, second.status) == (Status.SENT, Status.SENT)
    assert (first.counted_on, second.counted_on) == (TODAY, TODAY)
    assert (_usage().used, _usage().newsletter) == (2, 0)


def test_rn_a3_queueing_does_not_count():
    _queue()
    assert not EmailDailyUsage.objects.exists()


def test_rn_a3_the_counter_day_is_the_local_day(monkeypatch):
    """Les 23.30 UTC de l'11 de novembre ja són el dia 12 a l'hora local (Europe/Madrid)."""
    late = datetime.datetime(2026, 11, 11, 23, 30, tzinfo=datetime.UTC)
    monkeypatch.setattr(timezone, "now", lambda: late)
    email = _queue()

    mail.deliver(email.pk)

    assert _usage(TOMORROW).used == 1
    assert not EmailDailyUsage.objects.filter(day=TODAY).exists()


def test_ca_a9_a_retried_email_is_not_counted_twice():
    """CA-A9: un enviament que falla al proveïdor i es reintenta gasta un sol enviament."""
    email = _queue()
    with override_settings(EMAIL_BACKEND="apps.core.tests.test_mail_limit.FailingBackend"):
        for _ in range(2):
            with pytest.raises(mail.EmailDeliveryError):
                mail.deliver(email.pk, today=TODAY)
    assert _usage().used == 1

    assert _deliver(email).status == Status.SENT
    assert email.attempts == 3
    assert _usage().used == 1
    assert len(django_mail.outbox) == 1


def test_ca_a9_a_retry_after_midnight_does_not_count_on_the_new_day():
    email = _queue()
    with (
        override_settings(EMAIL_BACKEND="apps.core.tests.test_mail_limit.FailingBackend"),
        pytest.raises(mail.EmailDeliveryError),
    ):
        mail.deliver(email.pk, today=TODAY)

    assert _deliver(email, today=TOMORROW).status == Status.SENT
    assert email.counted_on == TODAY
    assert _usage().used == 1
    assert not EmailDailyUsage.objects.filter(day=TOMORROW).exists()


def test_ca_a9_a_failed_first_attempt_at_the_limit_keeps_its_place(spec_limits):
    """El reintent d'un correu que ja ha gastat el seu enviament surt encara que el dia s'hagi
    omplert entremig."""
    spec_limits.EMAIL_DAILY_LIMIT = 2
    retried = _queue()
    with (
        override_settings(EMAIL_BACKEND="apps.core.tests.test_mail_limit.FailingBackend"),
        pytest.raises(mail.EmailDeliveryError),
    ):
        mail.deliver(retried.pk, today=TODAY)
    _deliver(_queue(to="berta@example.org"))

    assert _deliver(retried).status == Status.SENT
    assert _usage().used == 2


# --- Al 100 %: ajornat (RN-A3, CA-A4, L20) --------------------------------------------------


def test_ca_a4_at_the_limit_the_email_is_deferred_and_goes_out_the_next_day(spec_limits):
    """CA-A4: amb el 100 % gastat, el correu queda «ajornat» i surt l'endemà."""
    spec_limits.EMAIL_DAILY_LIMIT = 3
    for n in range(3):
        assert _deliver(_queue(to=f"soci{n}@example.org")).status == Status.SENT
    late = _queue(to="tard@example.org")

    _deliver(late)

    assert late.status == Status.DEFERRED
    assert late.get_status_display() == "Ajornat"
    assert (late.attempts, late.counted_on, late.sent_at) == (0, None, None)
    assert late.body_text != ""  # encara ha de sortir
    assert len(django_mail.outbox) == 3
    assert _usage().used == 3

    # El mateix dia no surt: ni amb la tasca vella ni amb la tasca de cada hora.
    assert _deliver(late).status == Status.DEFERRED
    assert mail.release_deferred(today=TODAY) == 0
    assert _send_jobs(late).count() == 1

    # L'endemà torna a la cua, amb una tasca nova, i surt.
    assert mail.release_deferred(today=TOMORROW) == 1
    late.refresh_from_db()
    assert (late.status, late.counted_on) == (Status.QUEUED, TOMORROW)
    assert _send_jobs(late).count() == 2
    assert _deliver(late, today=TOMORROW).status == Status.SENT
    assert django_mail.outbox[-1].to == ["tard@example.org"]
    assert _usage(TOMORROW).used == 1
    assert mail.release_deferred(today=TOMORROW) == 0  # idempotent


def test_ca_a4_what_does_not_fit_the_next_day_waits_one_more_day(spec_limits):
    spec_limits.EMAIL_DAILY_LIMIT = 2
    EmailDailyUsage.objects.create(day=TODAY, used=2)
    emails = [_deliver(_queue(to=f"soci{n}@example.org")) for n in range(3)]
    assert {email.status for email in emails} == {Status.DEFERRED}

    assert mail.release_deferred(today=TOMORROW) == 2
    assert _usage(TOMORROW).used == 2
    assert OutgoingEmail.objects.filter(status=Status.DEFERRED).count() == 1

    assert mail.release_deferred(today=TOMORROW + datetime.timedelta(days=1)) == 1
    assert not OutgoingEmail.objects.filter(status=Status.DEFERRED).exists()


def test_ca_a4_the_hourly_task_releases_the_deferred_emails(spec_limits):
    spec_limits.EMAIL_DAILY_LIMIT = 1
    yesterday = timezone.localdate() - datetime.timedelta(days=1)
    EmailDailyUsage.objects.create(day=yesterday, used=1)
    email = _deliver(_queue(), today=yesterday)
    assert email.status == Status.DEFERRED

    tasks.release_deferred_emails(timestamp=0)

    email.refresh_from_db()
    assert (email.status, email.counted_on) == (Status.QUEUED, timezone.localdate())
    assert tasks.release_deferred_emails.name == "core.release_deferred_emails"
    assert tasks.release_deferred_emails.queue == "maintenance"
    periodic = tasks.app.periodic_registry.periodic_tasks[("core.release_deferred_emails", "")]
    assert periodic.cron == "5 * * * *"


# --- Ordre de sortida dels ajornats (V-07, CA-A5) -------------------------------------------


def test_ca_a5_deferred_emails_go_out_in_the_priority_order_of_v07(by_priority):
    """CA-A5: l'endemà surten primer els de comptes i, per últim, el butlletí; amb la mateixa
    prioritat, el que fa més que espera."""
    EmailDailyUsage.objects.create(day=TODAY, used=300)
    queued_order = [
        (Priority.NEWSLETTER, "butlleti@example.org"),
        (Priority.REMINDER, "recordatori@example.org"),
        (Priority.CONFIRMATION, "confirmacio-1@example.org"),
        (Priority.ACCOUNT, "compte@example.org"),
        (Priority.GUEST_LINK, "convidat@example.org"),
        (Priority.CONFIRMATION, "confirmacio-2@example.org"),
    ]
    for priority, to in queued_order:
        assert _deliver(_queue(by_priority[priority], to=to)).status == Status.DEFERRED
    last_job = ProcrastinateJob.objects.order_by("-id").first().id

    assert mail.release_deferred(today=TOMORROW) == 6

    # La cua serveix les tasques per ordre d'arribada: s'executen així.
    for job in ProcrastinateJob.objects.filter(id__gt=last_job).order_by("id"):
        mail.deliver(job.args["email_id"], today=TOMORROW)
    assert [message.to[0] for message in django_mail.outbox] == [
        "compte@example.org",
        "convidat@example.org",
        "confirmacio-1@example.org",
        "confirmacio-2@example.org",
        "recordatori@example.org",
        "butlleti@example.org",
    ]


def test_ca_a5_when_not_all_fit_the_highest_priorities_go_first(spec_limits, by_priority):
    spec_limits.EMAIL_DAILY_LIMIT = 2
    EmailDailyUsage.objects.create(day=TODAY, used=2)
    reminder = _deliver(_queue(by_priority[Priority.REMINDER]))
    confirmation = _deliver(_queue(by_priority[Priority.CONFIRMATION]))
    account = _deliver(_queue(by_priority[Priority.ACCOUNT]))

    assert mail.release_deferred(today=TOMORROW) == 2

    for email in (reminder, confirmation, account):
        email.refresh_from_db()
    assert (account.status, confirmation.status) == (Status.QUEUED, Status.QUEUED)
    assert reminder.status == Status.DEFERRED


def test_v07_deferred_emails_go_before_any_new_email_of_the_next_day(spec_limits):
    """V-07, L20: «surten primer l'endemà». Encara que la tasca de cada hora no hagi passat, un
    correu nou no pren el lloc a un d'ajornat."""
    spec_limits.EMAIL_DAILY_LIMIT = 1
    EmailDailyUsage.objects.create(day=TODAY, used=1)
    waiting = _deliver(_queue(to="espera@example.org"))
    assert waiting.status == Status.DEFERRED

    new = _deliver(_queue(to="nou@example.org"), today=TOMORROW)

    waiting.refresh_from_db()
    assert (waiting.status, waiting.counted_on) == (Status.QUEUED, TOMORROW)
    assert new.status == Status.DEFERRED
    assert django_mail.outbox == []


# --- Reserva per als transaccionals (RN-A4, CA-A2) ------------------------------------------


def test_ca_a2_transactional_emails_keep_going_out_up_to_the_limit(by_priority):
    """CA-A2, part transaccional: amb un límit de 300 i una reserva de 100, quan el butlletí ha
    gastat 200 enviaments ja no en pot gastar cap més, i els transaccionals surten fins a 300.
    (Les tandes i el consentiment del butlletí, RN-A5 i RN-A9, no són d'aquesta tasca.)"""
    EmailDailyUsage.objects.create(day=TODAY, used=200, newsletter=200)

    newsletter = _deliver(_queue(by_priority[Priority.NEWSLETTER], to="butlleti@example.org"))
    assert newsletter.status == Status.DEFERRED
    assert (_usage().used, _usage().newsletter) == (200, 200)

    for n in range(100):
        assert _deliver(_queue(to=f"soci{n}@example.org")).status == Status.SENT
    assert (_usage().used, _usage().newsletter) == (300, 200)
    assert len(django_mail.outbox) == 100

    assert _deliver(_queue(to="soci-301@example.org")).status == Status.DEFERRED
    assert _usage().used == 300


def test_rn_a4_transactional_emails_can_use_the_whole_limit(spec_limits, by_priority):
    """La reserva limita el butlletí, no els transaccionals."""
    spec_limits.EMAIL_DAILY_LIMIT = 5
    spec_limits.EMAIL_TRANSACTIONAL_RESERVE = 3
    for n in range(2):
        newsletter = _deliver(_queue(by_priority[Priority.NEWSLETTER], to=f"b{n}@example.org"))
        assert newsletter.status == Status.SENT
    assert _deliver(_queue(by_priority[Priority.NEWSLETTER])).status == Status.DEFERRED

    for n in range(3):
        assert _deliver(_queue(to=f"soci{n}@example.org")).status == Status.SENT
    assert (_usage().used, _usage().newsletter) == (5, 2)


# --- Avís del llindar (RN-A6, CA-A3; qui el rep: Q-26) --------------------------------------


def test_ca_a3_one_single_alert_a_day_at_80_percent(spec_limits):
    """CA-A3: en arribar al 80 % del límit s'avisa, i enviar-ne un més no torna a avisar."""
    spec_limits.EMAIL_DAILY_LIMIT = 10
    spec_limits.EMAIL_ALERT_TO = ["avisos@example.org"]
    for n in range(7):
        _deliver(_queue(to=f"soci{n}@example.org"))
    assert not _alerts().exists()

    _deliver(_queue(to="soci7@example.org"))

    entry = _alerts().get()
    assert entry.actor_kind == AuditEntry.ActorKind.SYSTEM
    assert entry.actor_origin == "core.mail"
    assert entry.details == {"day": "2026-11-11", "used": 8, "limit": 10, "recipients": 1}
    alert = OutgoingEmail.objects.get(template=mail.ALERT_TEMPLATE)
    assert alert.to_address == "avisos@example.org"
    assert "8" in alert.subject and "10" in alert.subject
    assert "11/11/2026" in alert.body_text
    assert _usage().warned_at is not None

    # Se n'envia un més, l'avís mateix i un que ja no hi cap: cap altre avís.
    _deliver(_queue(to="soci8@example.org"))
    assert _deliver(alert).status == Status.SENT
    assert _deliver(_queue(to="soci9@example.org")).status == Status.DEFERRED
    assert _usage().used == 10
    assert _alerts().count() == 1
    assert OutgoingEmail.objects.filter(template=mail.ALERT_TEMPLATE).count() == 1


def test_ca_a3_the_next_day_can_alert_again(spec_limits):
    spec_limits.EMAIL_DAILY_LIMIT = 5
    for day in (TODAY, TOMORROW):
        for n in range(4):
            _deliver(_queue(to=f"soci{n}@example.org"), today=day)

    assert sorted(entry.details["day"] for entry in _alerts()) == ["2026-11-11", "2026-11-12"]


def test_081_without_the_administrator_address_the_alert_is_not_operational(spec_limits):
    """Decisió 081, punt 21: el rep només l'administrador, a l'adreça d'`EMAIL_ALERT_TO`. Si és
    buida, no s'inventa cap destinatari: l'avís queda al registre amb zero destinataris i el
    registre diu que no ha arribat a ningú (zero destinataris)."""
    spec_limits.EMAIL_DAILY_LIMIT = 5
    for n in range(5):
        _deliver(_queue(to=f"soci{n}@example.org"))

    assert _alerts().get().details["recipients"] == 0
    assert not OutgoingEmail.objects.filter(template=mail.ALERT_TEMPLATE).exists()
    assert len(django_mail.outbox) == 5


class TestAlertRecipientCheck:
    """`check --deploy` marca l'avís com a no operatiu mentre no hi ha l'adreça (core.W001), i una
    adreça mal escrita és un error a tots els entorns (core.E001)."""

    def _ids(self, deploy):
        from django.core import checks

        return {m.id for m in checks.run_checks(include_deployment_checks=deploy)}

    def test_empty_address_is_a_deploy_warning(self, spec_limits):
        assert "core.W001" in self._ids(deploy=True)
        assert "core.W001" not in self._ids(deploy=False)

    def test_with_the_administrator_address_there_is_no_warning(self, spec_limits):
        spec_limits.EMAIL_ALERT_TO = ["administracio@example.org"]
        assert not {"core.W001", "core.E001"} & self._ids(deploy=True)

    def test_a_wrong_address_is_an_error(self, spec_limits):
        spec_limits.EMAIL_ALERT_TO = ["no-es-una-adreca"]
        assert "core.E001" in self._ids(deploy=False)


def test_ca_a3_releasing_deferred_emails_also_alerts_once(spec_limits):
    spec_limits.EMAIL_DAILY_LIMIT = 5
    EmailDailyUsage.objects.create(day=TODAY, used=5, warned_at=timezone.now())
    for n in range(5):
        _deliver(_queue(to=f"soci{n}@example.org"))

    assert mail.release_deferred(today=TOMORROW) == 5
    assert mail.release_deferred(today=TOMORROW) == 0

    assert [entry.details["day"] for entry in _alerts()] == ["2026-11-12"]


# --- Concurrència ---------------------------------------------------------------------------


class TestConcurrentDeliveries(CommittedDataTestCase):
    """Vuit enviaments alhora, cadascun amb la seva connexió, amb un límit de 5 i sense cap
    comptador del dia creat: ni passen del límit ni avisen dues vegades."""

    def test_simultaneous_deliveries_never_pass_the_limit_and_alert_once(self):
        emails = [_queue(to=f"soci{n}@example.org") for n in range(8)]

        with self.settings(EMAIL_DAILY_LIMIT=5):
            run_together([lambda pk=email.pk: mail.deliver(pk) for email in emails])

        statuses = list(OutgoingEmail.objects.values_list("status", flat=True))
        assert statuses.count(Status.SENT) == 5
        assert statuses.count(Status.DEFERRED) == 3
        assert len(django_mail.outbox) == 5
        assert EmailDailyUsage.objects.get().used == 5
        assert _alerts().count() == 1

    def test_the_same_email_delivered_twice_at_once_counts_and_goes_out_once(self):
        email = _queue()

        run_together([lambda: mail.deliver(email.pk)] * 2)

        assert len(django_mail.outbox) == 1
        assert EmailDailyUsage.objects.get().used == 1


# --- Adreça de l'avís a producció (decisió 084) ---------------------------------------------

CLUB_ADDRESS = "cris@cris.es"


def _production_alert_addresses(extra_env=None):
    """`EMAIL_ALERT_TO` tal com la carrega la configuració de producció, en un procés a part i
    amb valors de mostra generats aquí (cap secret real). No envia res ni toca cap base."""
    import json
    import os
    import secrets
    import subprocess
    import sys

    from cryptography.fernet import Fernet
    from django.conf import settings as current

    env = {k: v for k, v in os.environ.items() if k != "EMAIL_ALERT_TO"}
    env.update(
        {
            "DJANGO_SETTINGS_MODULE": "config.settings.prod",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(50),
            "FIELD_ENCRYPTION_KEYS": Fernet.generate_key().decode(),
            "CARD_QR_KEYS": f"ci:{secrets.token_urlsafe(32)}",
            "CARD_QR_ACTIVE_KEY": "ci",
            "DJANGO_ALLOWED_HOSTS": "cris1954.cat",
            "EMAIL_HOST": "smtp.example.invalid",
            "EMAIL_HOST_USER": "proves",
            "EMAIL_HOST_PASSWORD": PASSWORD,
            "S3_BUCKET_FITXERS": "cris-ci",
            "S3_ENDPOINT_URL": "https://s3.example.invalid",
            "S3_ACCESS_KEY_ID": "proves",
            "S3_SECRET_ACCESS_KEY": PASSWORD,
            **(extra_env or {}),
        }
    )
    env.setdefault("DATABASE_URL", "postgres://cris:cris-ci@localhost:5432/cris")
    code = (
        "import json, django; from django.conf import settings; "
        "from django.core import checks; django.setup(); "
        "ids = [m.id for m in checks.run_checks(include_deployment_checks=True)]; "
        "print(json.dumps({'to': list(settings.EMAIL_ALERT_TO), 'ids': ids}))"
    )
    done = subprocess.run(  # noqa: S603 (ordre fixa d'aquesta prova)
        [sys.executable, "-c", code],
        cwd=current.BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_084_production_sends_the_alert_to_the_club_address_by_default():
    """Decisió 084: a producció l'avís va a l'adreça de l'administrador que ha donat el
    responsable, sense que calgui cap variable d'entorn, i la comprovació de desplegament no
    marca l'avís com a no operatiu."""
    result = _production_alert_addresses()
    assert result["to"] == [CLUB_ADDRESS]
    assert "core.W001" not in result["ids"] and "core.E001" not in result["ids"]


def test_084_the_environment_variable_still_overrides_it():
    result = _production_alert_addresses({"EMAIL_ALERT_TO": "administracio@example.invalid"})
    assert result["to"] == ["administracio@example.invalid"]


def test_084_outside_production_there_is_no_default_address():
    """Desenvolupament i proves: cap adreça per defecte, perquè mai no surti un avís de prova
    cap a la bústia real del club. Es llegeix el text de la configuració comuna, no el valor
    carregat, que pot venir d'una variable d'entorn de qui executa les proves."""
    from django.conf import settings as current

    base = (current.BASE_DIR / "config" / "settings" / "base.py").read_text(encoding="utf-8")
    assert 'EMAIL_ALERT_TO = env.list("EMAIL_ALERT_TO", default=[])' in base
    assert CLUB_ADDRESS not in base.split("EMAIL_ALERT_TO = env.list")[1].splitlines()[0]


def test_084_the_alert_goes_only_to_the_configured_address(spec_limits, make_person):
    """L'avís del 80 % va només a l'adreça configurada: ni als comptes d'administrador, ni als
    socis, ni a cap altra adreça. La bústia és la de proves: no surt cap correu real."""
    from apps.accounts.models import Account

    Account.objects.create_admin(
        make_person("Nora", "Admin"), "nora.admin", PASSWORD, notification_email="nora@example.org"
    )
    spec_limits.EMAIL_DAILY_LIMIT = 5
    spec_limits.EMAIL_ALERT_TO = [CLUB_ADDRESS]
    for n in range(4):
        _deliver(_queue(to=f"soci{n}@example.org"))

    alerts = OutgoingEmail.objects.filter(template=mail.ALERT_TEMPLATE)
    assert [a.to_address for a in alerts] == [CLUB_ADDRESS]
    assert _alerts().get().details["recipients"] == 1
    _deliver(alerts.get())
    sent_to = [to for message in django_mail.outbox for to in message.to]
    assert sent_to.count(CLUB_ADDRESS) == 1
    assert "nora@example.org" not in sent_to
    assert set(sent_to) == {CLUB_ADDRESS, *(f"soci{n}@example.org" for n in range(4))}
