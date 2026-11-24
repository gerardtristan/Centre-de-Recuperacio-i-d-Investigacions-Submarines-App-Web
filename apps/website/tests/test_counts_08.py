"""`website.counts()` per al dashboard (T-M08-08; M08-2): només recomptes. Dades inventades."""

import pytest
from django.utils import timezone

from apps.core.models import LegalText
from apps.website import counts
from apps.website.models import ContactMessage, NewsletterSubscription

from .test_contact_07 import _message

pytestmark = pytest.mark.django_db
SUB = NewsletterSubscription.Status
MSG = ContactMessage.Status


def subscription(n, status):
    text = LegalText.objects.get_or_create(kind="privacy", version=1, defaults={"content": "P"})[0]
    return NewsletterSubscription.objects.create(
        email=f"subscriptor{n}@example.com", status=status, legal_text=text, token=f"t{n}",
        requested_at=timezone.now(),
    )  # fmt: skip


def test_confirmed_subscribers_and_new_contact_messages():
    for n, status in enumerate([SUB.CONFIRMED, SUB.CONFIRMED, SUB.PENDING, SUB.UNSUBSCRIBED]):
        subscription(n, status)
    _message()
    _message(status=MSG.ANSWERED)
    _message(status=MSG.CLOSED, closed_reason="Motiu inventat")
    result = counts.counts()
    assert result == {"confirmed_subscribers": 2, "pending_contact_messages": 1}
    assert "example.com" not in repr(result) and "Nom Inventat" not in repr(result)
