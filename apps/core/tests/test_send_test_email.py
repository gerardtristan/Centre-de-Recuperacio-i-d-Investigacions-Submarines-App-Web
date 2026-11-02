"""Ordre `send_test_email` (T-M01-10). Només adreces inventades."""

import pytest
from django.core import mail as django_mail
from django.core.management import CommandError, call_command

from apps.core import mail
from apps.core.models import OutgoingEmail

pytestmark = pytest.mark.django_db


def test_queues_the_test_email_in_catalan():
    call_command("send_test_email", "proves@example.org")

    email = OutgoingEmail.objects.get()
    assert (email.template, email.language, email.to_address) == (
        "prova",
        "ca",
        "proves@example.org",
    )
    assert django_mail.outbox == []  # surt quan la cua el processa
    mail.deliver(email.pk)
    assert django_mail.outbox[0].to == ["proves@example.org"]


def test_rejects_an_invalid_address():
    with pytest.raises(CommandError):
        call_command("send_test_email", "no-es-una-adreca")
    assert not OutgoingEmail.objects.exists()
