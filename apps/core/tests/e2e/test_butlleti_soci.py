"""T-M07-13 (P-492, opció A): un soci se subscriu al butlletí des de la seva àrea, amb el
consentiment de la 00, i se'n dona de baixa. Sense entrada de menú (DISSENY): s'hi va per l'adreça.
Dades inventades."""

import pytest
from playwright.sync_api import expect

from apps.activities.tests.helpers import a_member
from apps.core import consents
from apps.core.models import Consent, Setting
from apps.website import newsletter
from apps.website.models import NewsletterSubscription

from .conftest import PASSWORD

pytestmark = pytest.mark.e2e


def test_a_member_subscribes_and_unsubscribes(page, live_server, texts, review):
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)
    consents.publish_text("newsletter", "Text de prova: newsletter.", by=texts)
    account = a_member("Sòcia")
    account.set_password(PASSWORD)
    account.save()
    page.goto(f"{live_server.url}/entrar/")
    page.get_by_label("Correu electrònic").fill(account.login)
    page.get_by_label("Contrasenya").fill(PASSWORD)
    page.get_by_role("button", name="Entrar").click()

    page.goto(f"{live_server.url}/socis/butlleti/")
    expect(page.get_by_role("heading", name="Butlletí del club")).to_be_visible()
    review("butlleti-soci-alta")
    page.locator("input[name='accept_newsletter']").check()
    page.get_by_role("button", name="Subscriu-me").click()
    expect(page.get_by_text("Ja estàs subscrit al butlletí.")).to_be_visible()
    review("butlleti-soci-subscrit")
    assert NewsletterSubscription.objects.get().status == "confirmed"
    assert Consent.objects.get(person=account.person).action == "granted"

    page.get_by_role("button", name="Dona'm de baixa").click()
    expect(page.get_by_text("T'has donat de baixa del butlletí.")).to_be_visible()
    assert NewsletterSubscription.objects.get().status == "unsubscribed"
