"""Nucli del 06 Llicències (T-M06-14, 15, 05, 12 i 20): el tipus de lot «licences», els
esdeveniments aprovats de la llicència i les dues plantilles de correu. Només dades inventades."""

import pytest

from apps.core import events, mail
from apps.core.models import ImportBatch, OutgoingEmail

pytestmark = pytest.mark.django_db


def test_a_licences_import_batch_is_allowed(admin_account):
    batch = ImportBatch.objects.create(
        kind=ImportBatch.Kind.LICENCES,
        status=ImportBatch.Status.PREVIEW,
        file_sha256="0" * 64,
        created_by=admin_account,
    )
    assert batch.get_kind_display() == "Llicències del 01"


@pytest.mark.parametrize(
    "name", ["licence.issued", "licence.renewed", "licence.expired", "licence.cancelled"]
)
def test_the_licence_events_are_approved(name, monkeypatch):
    # RN-M06-17 (052, 054): el 06 els emet i qualsevol mòdul s'hi pot subscriure.
    monkeypatch.setattr(events, "_subscribers", {})
    events.subscribe(name, lambda event: None)
    assert events.emit(name, {"licence": 1, "version": 1}).name == name


@pytest.mark.parametrize(
    ("template", "context", "expected"),
    [
        ("avis-llicencia-pagada", {"licence_id": 41, "licence_type": "Aficionat"}, "41"),
        ("avis-devolucio-llicencia", {"licence_id": 42, "amount": "90,00 €"}, "90,00 €"),
    ],
)
def test_the_two_licence_notices_render_without_personal_data(template, context, expected):
    email = mail.queue_email(template, to="secretaria@example.org", context=context)
    assert isinstance(email, OutgoingEmail) and expected in email.body_text
    assert email.subject and "{" not in email.subject


def test_the_expiry_reminder_and_the_digest_render():
    # T-M06-11 (RN-M06-12): el titular rep el tipus, la data i l'enllaç; el resum, només recomptes.
    reminder = mail.queue_email(
        "avis-venciment-llicencia", to="titular@example.org",
        context={"licence_type": "Aficionat", "expires_on": "31/12/2027", "days_before": 60,
                 "link": "https://cris1954.cat/socis/llicencia/"},
    )  # fmt: skip
    assert reminder.subject == "La teva llicència federativa caduca el 31/12/2027"
    assert "d'aquí a 60 dies" in reminder.body_text and "/socis/llicencia/" in reminder.body_text
    digest = mail.queue_email(
        "resum-venciments-llicencies", to="secretaria@example.org",
        context={"days_before": 7, "total": 3, "groups": [
            {"expires_on": "31/12/2027", "category": "Aficionat", "count": 2},
            {"expires_on": "31/12/2027", "category": "Tècnic", "count": 1},
        ]},
    )  # fmt: skip
    assert digest.subject == "3 llicències caduquen d'aquí a 7 dies"
    assert "- 31/12/2027 · Tècnic: 1" in digest.body_text and "http" not in digest.body_text
