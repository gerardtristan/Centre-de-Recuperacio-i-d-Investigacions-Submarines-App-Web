"""Correu mínim (spec 00, annex A; decisió 061, punt 7; T-M01-10). Només dades inventades."""

import ast
import inspect

import pytest
from django.conf import settings
from django.core import mail as django_mail
from django.core.mail.backends.base import BaseEmailBackend
from django.db import transaction
from django.template import TemplateDoesNotExist
from django.test import override_settings
from django.utils import translation
from procrastinate.contrib.django.models import ProcrastinateJob

from apps.core import mail, tasks
from apps.core.models import AuditEntry, OutgoingEmail, Person

pytestmark = pytest.mark.django_db

TWO_LANGUAGES = [("ca", "Català"), ("es", "Castellano")]


class FailingBackend(BaseEmailBackend):
    def send_messages(self, messages):
        raise ConnectionError("servidor de proves no disponible")


class OtherProviderBackend(BaseEmailBackend):
    """Un altre «proveïdor»: guarda els missatges en una llista pròpia."""

    sent = []

    def send_messages(self, messages):
        type(self).sent.extend(messages)
        return len(messages)


def _queue_test(person=None, to="anna@example.org", **context):
    return mail.queue_email("prova", to=to, person=person, context=context)


# --- Posar a la cua -------------------------------------------------------------------------


def test_queue_stores_message_and_defers_task(make_person):
    person = make_person()
    email = _queue_test(person)

    assert email.status == OutgoingEmail.Status.QUEUED
    assert email.template == "prova"
    assert email.language == "ca"
    assert email.to_address == "anna@example.org"
    assert email.subject == "Correu de prova de la plataforma del C.R.I.S."
    assert "Si l'has rebut, l'enviament funciona." in email.body_text
    assert '<html lang="ca">' in email.body_html
    job = ProcrastinateJob.objects.get(task_name="core.send_email")
    assert job.args == {"email_id": email.pk}
    assert job.queue_name == "email"
    assert django_mail.outbox == []  # RN-A13: no s'envia dins la petició


def test_rolled_back_action_leaves_neither_email_nor_task(make_person):
    person = make_person()
    with pytest.raises(RuntimeError), transaction.atomic():
        _queue_test(person)
        raise RuntimeError("l'acció falla després de posar el correu a la cua")

    assert not OutgoingEmail.objects.exists()
    assert not ProcrastinateJob.objects.filter(task_name="core.send_email").exists()


def test_anonymised_person_gets_no_email(make_person):
    person = make_person()
    person.status = Person.Status.ANONYMISED
    person.anonymous_ref = "A-0001"
    person.save()

    assert _queue_test(person) is None
    assert not OutgoingEmail.objects.exists()
    assert not ProcrastinateJob.objects.filter(task_name="core.send_email").exists()


def test_email_queued_before_anonymising_is_still_sent(make_person):
    """La confirmació d'un esborrat RGPD es posa a la cua abans d'anonimitzar."""
    person = make_person()
    email = _queue_test(person)
    person.status = Person.Status.ANONYMISED
    person.anonymous_ref = "A-0002"
    person.save()

    mail.deliver(email.pk)

    assert len(django_mail.outbox) == 1


@pytest.mark.parametrize("key", ["password", "new_password", "contrasenya", "totp_secret"])
def test_context_never_carries_passwords_or_secrets(key):
    with pytest.raises(ValueError, match="RN-A12"):
        mail.queue_email("prova", to="anna@example.org", context={key: "x"})
    assert not OutgoingEmail.objects.exists()


def test_one_time_links_are_allowed_in_context(email_templates):
    email_templates("enllac", "ca", "Verifica", "{{ link }}")
    email = mail.queue_email(
        "enllac", to="anna@example.org", context={"link": "https://cris1954.cat/v/abc"}
    )
    assert "https://cris1954.cat/v/abc" in email.body_text


@pytest.mark.parametrize("name", ["../base", "Prova", "", "prova.ca"])
def test_template_name_is_validated(name):
    with pytest.raises(ValueError):
        mail.queue_email(name, to="anna@example.org")


def test_subject_is_a_single_line(email_templates):
    email_templates("linies", "ca", "Primera\nsegona\r\n", "cos")
    email = mail.queue_email("linies", to="anna@example.org")
    assert email.subject == "Primera segona"


# --- Llengua (061, punt 7) ------------------------------------------------------------------


@override_settings(LANGUAGES=TWO_LANGUAGES)
def test_template_in_the_person_language(email_templates, make_person):
    email_templates(
        "avis",
        "ca",
        "{% load i18n %}{% get_current_language as L %}Avís {{ L }}",
        "{% load i18n %}{% get_current_language as L %}cos {{ L }}",
    )
    email_templates(
        "avis",
        "es",
        "{% load i18n %}{% get_current_language as L %}Aviso {{ L }}",
        "{% load i18n %}{% get_current_language as L %}cuerpo {{ L }}",
    )
    email = mail.queue_email(
        "avis", to="a@example.org", person=make_person(preferred_language="es")
    )

    assert email.language == "es"
    assert email.subject == "Aviso es"
    assert email.body_text == "cuerpo es"  # generat dins de translation.override("es")


@override_settings(LANGUAGES=TWO_LANGUAGES)
def test_missing_language_template_falls_back_to_catalan(email_templates, make_person):
    email_templates(
        "avis", "ca", "{% load i18n %}{% get_current_language as L %}Avís {{ L }}", "cos"
    )
    email = mail.queue_email(
        "avis", to="a@example.org", person=make_person(preferred_language="es")
    )

    assert email.language == "ca"
    assert email.subject == "Avís ca"


def test_inactive_preferred_language_uses_catalan(email_templates, make_person):
    email_templates("avis", "ca", "Avís", "cos")
    email_templates("avis", "fr", "Avis", "corps")
    email = mail.queue_email(
        "avis", to="a@example.org", person=make_person(preferred_language="fr")
    )
    assert email.language == "ca"


def test_without_person_the_email_is_in_catalan():
    assert _queue_test().language == "ca"


@override_settings(LANGUAGES=TWO_LANGUAGES)
def test_active_language_is_restored_after_rendering(email_templates, make_person):
    email_templates("avis", "es", "Aviso", "cuerpo")
    email_templates("avis", "ca", "Avís", "cos")
    with translation.override("ca"):
        mail.queue_email("avis", to="a@example.org", person=make_person(preferred_language="es"))
        assert translation.get_language() == "ca"


def test_missing_catalan_template_is_an_error(monkeypatch):
    # Amb la prioritat declarada (RN-A8), el que falla és que no hi ha el fitxer.
    monkeypatch.setitem(mail.TEMPLATE_PRIORITIES, "no-existeix", OutgoingEmail.Priority.REMINDER)
    with pytest.raises(TemplateDoesNotExist):
        mail.queue_email("no-existeix", to="anna@example.org")


# --- Enviament ------------------------------------------------------------------------------


def test_delivery_uses_club_sender_and_reply_to(make_person):
    """CA-A1, amb el remitent de la decisió 085 (I-2): els correus surten de cris@cris.es, que
    també és l'adreça de resposta. Substitueix el remitent de cris1954.cat de la 019."""
    email = _queue_test(make_person())
    tasks.send_email(email_id=email.pk)

    [message] = django_mail.outbox
    assert message.from_email == "C.R.I.S. <cris@cris.es>"
    assert message.reply_to == ["cris@cris.es"]
    assert message.to == ["anna@example.org"]
    assert message.subject == "Correu de prova de la plataforma del C.R.I.S."
    assert message.attachments == []
    assert [mimetype for _, mimetype in message.alternatives] == ["text/html"]


@override_settings(EMAIL_FROM_TRANSACCIONAL="Club de proves <no-respon@cris1954.cat>")
def test_sender_name_is_configurable():
    mail.deliver(_queue_test().pk)
    assert django_mail.outbox[0].from_email == "Club de proves <no-respon@cris1954.cat>"


def test_sent_email_keeps_metadata_and_drops_body():
    """RN-A7: plantilla, destinatari, estat i data; el cos, fora en enviar-lo bé."""
    email = _queue_test()
    mail.deliver(email.pk)
    email.refresh_from_db()

    assert email.status == OutgoingEmail.Status.SENT
    assert email.sent_at is not None
    assert email.attempts == 1
    assert (email.template, email.to_address, email.language) == ("prova", "anna@example.org", "ca")
    assert email.body_text == "" and email.body_html == ""


def test_delivery_is_idempotent():
    email = _queue_test()
    mail.deliver(email.pk)
    mail.deliver(email.pk)
    assert len(django_mail.outbox) == 1


def test_delivery_of_unknown_email_does_nothing():
    mail.deliver(999_999)
    assert django_mail.outbox == []


@override_settings(EMAIL_BACKEND="apps.core.tests.test_mail.FailingBackend", EMAIL_MAX_ATTEMPTS=3)
def test_failed_delivery_keeps_body_until_attempts_run_out():
    email = _queue_test()

    for attempt in (1, 2):
        with pytest.raises(mail.EmailDeliveryError):
            mail.deliver(email.pk)
        email.refresh_from_db()
        assert email.status == OutgoingEmail.Status.QUEUED
        assert email.attempts == attempt
        assert email.body_text != ""  # encara s'ha de poder reintentar
        assert email.last_error.startswith("ConnectionError")

    mail.deliver(email.pk)  # darrer intent: ja no aixeca, no es reintenta més
    email.refresh_from_db()
    assert email.status == OutgoingEmail.Status.FAILED
    assert email.attempts == 3
    assert email.body_text == "" and email.body_html == ""
    assert email.sent_at is None


def test_the_task_retries_through_the_queue():
    """La tasca deixa passar l'error perquè procrastinate la reprogrami."""
    email = _queue_test()
    with (
        override_settings(EMAIL_BACKEND="apps.core.tests.test_mail.FailingBackend"),
        pytest.raises(mail.EmailDeliveryError),
    ):
        tasks.send_email(email_id=email.pk)
    assert tasks.send_email.retry_strategy.max_attempts == settings.EMAIL_MAX_ATTEMPTS


def test_body_cannot_stay_once_the_email_is_closed():
    email = _queue_test()
    email.status = OutgoingEmail.Status.FAILED
    with pytest.raises(Exception, match="outgoing_email_body_only_while_queued"):
        with transaction.atomic():
            email.save()


# --- Canvi de proveïdor i registre d'activitat ----------------------------------------------


def test_changing_provider_is_only_configuration():
    """El mateix codi envia pel transport configurat, sigui quin sigui (decisions 004 i 042)."""
    OtherProviderBackend.sent.clear()
    first = _queue_test(to="primer@example.org")
    mail.deliver(first.pk)

    with override_settings(EMAIL_BACKEND="apps.core.tests.test_mail.OtherProviderBackend"):
        second = _queue_test(to="segon@example.org")
        mail.deliver(second.pk)

    assert [m.to for m in django_mail.outbox] == [["primer@example.org"]]
    assert [m.to for m in OtherProviderBackend.sent] == [["segon@example.org"]]
    assert OtherProviderBackend.sent[0].reply_to == ["cris@cris.es"]


@pytest.mark.parametrize("module", [mail, tasks])
def test_mail_code_does_not_depend_on_a_provider(module):
    tree = ast.parse(inspect.getsource(module))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    roots = {name.split(".")[0] for name in imported}
    assert roots <= {"re", "django", "procrastinate", "models", "persons", "tasks", "files", ""}


def test_nothing_of_the_email_goes_to_the_audit_log(email_templates):
    """RN-52: ni el cos, ni els enllaços, ni els testimonis al registre d'activitat."""
    email_templates("enllac", "ca", "Verifica", "{{ link }}")
    before = AuditEntry.objects.count()
    email = mail.queue_email(
        "enllac", to="anna@example.org", context={"link": "https://cris1954.cat/v/testimoni-xyz"}
    )
    mail.deliver(email.pk)

    assert AuditEntry.objects.count() == before
