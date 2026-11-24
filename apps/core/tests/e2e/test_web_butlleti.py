"""T-M07-13 (P-M07-E; CA-M07-06, 07 i 09): subscriure's, confirmar i donar-se de baixa. Dades
inventades. L'enllaç surt de la base de dades: el correu de confirmació és del torn del nucli."""

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.core import consents
from apps.core.models import Setting
from apps.website import newsletter
from apps.website.models import NewsletterSubscription

pytestmark = pytest.mark.e2e


def test_visitor_subscribes_confirms_and_unsubscribes(page, live_server, texts, review):
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)
    consents.publish_text("newsletter", "Text de prova: newsletter.", by=texts)
    page.goto(f"{live_server.url}/butlleti/")
    expect(page.get_by_role("heading", name="Rep el butlletí del club")).to_be_visible()
    review("butlleti-formulari")
    page.get_by_label("Correu electrònic").fill("mar.subscriptora@example.org")
    page.locator("input[name='accept_newsletter']").check()
    page.get_by_role("button", name="Subscriu-me").click()
    expect(page.get_by_text("Revisa el correu")).to_be_visible()
    review("butlleti-revisa-correu")

    token = NewsletterSubscription.objects.get().token
    page.goto(f"{live_server.url}{reverse('website:newsletter_confirm', args=[token])}")
    review("butlleti-confirma")
    page.get_by_role("button", name="Confirma la subscripció").click()
    expect(page.get_by_text("Subscripció confirmada")).to_be_visible()
    assert NewsletterSubscription.objects.get().status == "confirmed"

    page.goto(f"{live_server.url}{reverse('website:newsletter_unsubscribe', args=[token])}")
    expect(page.get_by_text("T'has donat de baixa")).to_be_visible()
    review("butlleti-baixa")
    assert NewsletterSubscription.objects.get().status == "unsubscribed"
