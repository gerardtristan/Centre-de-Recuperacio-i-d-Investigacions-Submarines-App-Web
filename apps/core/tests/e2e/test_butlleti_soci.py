"""T-M07-13 (P-492, opció A; P-631): un soci se subscriu al butlletí des de la seva àrea, el
confirma amb l'enllaç del correu (i hi queda el consentiment de la 00) i se'n dona de baixa. Sense
entrada de menú (DISSENY): s'hi va per l'adreça. Dades inventades."""

import re
from urllib.parse import urlsplit

import pytest
from playwright.sync_api import expect

from apps.activities.tests.helpers import a_member
from apps.core import consents
from apps.core.models import Consent, OutgoingEmail, Setting
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
    expect(page.get_by_text("T'hem enviat un correu per confirmar la subscripció.")).to_be_visible()
    review("butlleti-soci-pendent")
    assert not Consent.objects.filter(person=account.person).exists()

    # P-631: l'enllaç del correu de la cua i el botó (doble confirmació també des de l'àrea).
    email = OutgoingEmail.objects.get(template=newsletter.CONFIRMATION_TEMPLATE)
    link = re.search(r"https?://\S+", email.body_text).group(0)
    page.goto(live_server.url + urlsplit(link).path)
    page.get_by_role("button", name="Confirma la subscripció").click()
    expect(page.get_by_text("Subscripció confirmada")).to_be_visible()
    assert NewsletterSubscription.objects.get().status == "confirmed"
    assert Consent.objects.get(person=account.person).action == "granted"

    page.goto(f"{live_server.url}/socis/butlleti/")
    expect(page.get_by_text("Reps el butlletí")).to_be_visible()
    review("butlleti-soci-subscrit")

    page.get_by_role("button", name="Dona'm de baixa").click()
    expect(page.get_by_text("T'has donat de baixa del butlletí.")).to_be_visible()
    assert NewsletterSubscription.objects.get().status == "unsubscribed"
