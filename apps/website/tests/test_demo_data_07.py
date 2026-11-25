"""T-M07-17: `seed_demo_data` deixa les dades inventades del 07 (contacte en cada estat,
subscripcions confirmada, pendent i de baixa i un butlletí esborrany). Només dades inventades."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.website.models import ContactMessage, Newsletter, NewsletterSubscription

pytestmark = pytest.mark.django_db
DEV = override_settings(SETTINGS_MODULE="config.settings.dev", DEBUG=True)


def test_t_m07_17_the_command_loads_the_website_data(tmp_path):
    out = StringIO()
    with DEV:
        call_command("seed_demo_data", "--cluber-file", str(tmp_path / "c.csv"), stdout=out)
    assert "Mòdul 07: 3 missatges de contacte" in out.getvalue()
    assert set(ContactMessage.objects.values_list("status", flat=True)) == {
        "new", "answered", "closed",
    }  # fmt: skip
    assert set(NewsletterSubscription.objects.values_list("status", flat=True)) == {
        "confirmed", "pending", "unsubscribed",
    }  # fmt: skip
    assert list(Newsletter.objects.values_list("status", flat=True)) == ["draft"]
    for message in ContactMessage.objects.all():
        assert message.email.endswith("@example.org")
