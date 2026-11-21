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
