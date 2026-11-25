"""Butlletí des de l'àrea del soci (T-M07-13; P-492, opció A; P-630 i P-631). Només dades
inventades."""

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core.models import Consent, LegalText, Setting
from apps.website import newsletter
from apps.website.models import NewsletterSubscription

pytestmark = pytest.mark.django_db
URL = reverse("website:my_newsletter")
S = NewsletterSubscription.Status


@pytest.fixture
def enabled():
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)


@pytest.fixture
def text():
    return LegalText.objects.create(kind="newsletter", version=1, content="Butlletí inventat")


@pytest.fixture
def member(login_as, personal_account):
    login_as(personal_account, AREA_PERSONAL)
    return personal_account


def test_switched_off_it_is_not_found(member, client, text):
    assert client.get(URL).status_code == 404


def test_an_administrator_account_does_not_use_it(login_as, admin_account, enabled, text):
    client = login_as(admin_account, AREA_ADMIN)
    assert client.get(URL).status_code in (302, 404)  # l'àrea d'administració no hi entra
    assert not NewsletterSubscription.objects.exists()


def test_p631_subscribing_sends_the_link_and_the_button_confirms_it_with_the_consent(
    member, client, enabled, text
):
    """P-631 (decisió del pilot del 25/11/2026, D2): doble confirmació també des de l'àrea."""
    from apps.core.models import OutgoingEmail

    assert client.post(URL, {"accio": "alta"}).status_code == 303  # sense acceptar el text
    assert not NewsletterSubscription.objects.exists()
    client.post(URL, {"accept_newsletter": "on"})
    subscription = NewsletterSubscription.objects.get()
    assert (subscription.email, subscription.status) == (member.login, S.PENDING)
    assert not Consent.objects.filter(person=member.person).exists()
    email = OutgoingEmail.objects.get(template=newsletter.CONFIRMATION_TEMPLATE)
    assert email.to_address == member.login and subscription.token in email.body_text
    assert "Pendent de confirmar" in client.get(URL).content.decode()

    confirm = reverse("website:newsletter_confirm", args=[subscription.token])
    client.post(confirm)
    subscription.refresh_from_db()
    assert (subscription.status, subscription.legal_text) == (S.CONFIRMED, text)
    consent = Consent.objects.get(person=member.person)
    assert (consent.action, consent.legal_text, consent.channel) == ("granted", text, "web")
    assert "Reps el butlletí" in client.get(URL).content.decode()
    assert list(newsletter.recipients()) == [subscription]


def test_p492_unsubscribing_withdraws_the_consent_and_keeps_only_the_trace(
    member, client, enabled, text
):
    client.post(URL, {"accept_newsletter": "on"})
    newsletter.confirm(NewsletterSubscription.objects.get().token)
    client.post(URL, {"accio": "baixa"})
    subscription = NewsletterSubscription.objects.get()
    assert subscription.status == S.UNSUBSCRIBED and member.login not in subscription.email
    actions = list(
        Consent.objects.filter(person=member.person).order_by("pk").values_list("action", flat=True)
    )
    assert actions == ["granted", "withdrawn"]
    assert not newsletter.recipients().exists()


def test_the_unsubscribe_link_of_an_email_also_withdraws_the_consent(member, client, enabled, text):
    client.post(URL, {"accept_newsletter": "on"})
    subscription = NewsletterSubscription.objects.get()
    newsletter.confirm(subscription.token)
    client.get(reverse("website:newsletter_unsubscribe", args=[subscription.token]))
    last = Consent.objects.filter(person=member.person).order_by("pk").last()
    assert last.action == "withdrawn"


def test_a_member_already_subscribed_from_the_web_is_shown_as_subscribed(
    member, client, enabled, text
):
    pending, _ = newsletter.subscribe(member.login, legal_text=text)
    newsletter.confirm(pending.token)
    assert "Reps el butlletí" in client.get(URL).content.decode()


# --- Revisió de la 13c ------------------------------------------------------------------------


def test_the_consent_is_the_version_accepted_when_subscribing_not_the_current_one(
    member, client, enabled, text
):
    client.post(URL, {"accept_newsletter": "on"})
    subscription = NewsletterSubscription.objects.get()
    LegalText.objects.create(kind="newsletter", version=2, content="Butlletí inventat v2")
    newsletter.confirm(subscription.token)
    consent = Consent.objects.get(person=member.person)
    assert consent.legal_text == text  # la v1, la que va acceptar


@pytest.mark.parametrize("status", ["pending", "disabled"])
def test_a_personal_account_that_is_not_active_does_not_get_the_consent(
    personal_account, enabled, text, status
):
    personal_account.status = status
    personal_account.save()
    subscription, _ = newsletter.subscribe(personal_account.login, legal_text=text)
    newsletter.confirm(subscription.token)
    assert NewsletterSubscription.objects.get().status == S.CONFIRMED
    assert not Consent.objects.filter(person=personal_account.person).exists()


def test_a_pending_subscription_offers_to_send_the_link_again(member, client, enabled, text):
    client.post(URL, {"accept_newsletter": "on"})
    page = client.get(URL).content.decode()
    assert "Torna a enviar l'enllaç" in page and 'name="accept_newsletter"' in page


def test_when_the_link_is_not_sent_the_page_does_not_say_it_was(
    member, client, enabled, text, settings
):
    from apps.core.models import OutgoingEmail

    settings.JOIN_FORM_RECIPIENT_MAX_PER_DAY = 0
    response = client.post(URL, {"accept_newsletter": "on"}, follow=True)
    page = response.content.decode()
    assert not OutgoingEmail.objects.exists()
    assert "T&#x27;hem enviat" not in page and "T'hem enviat" not in page
    assert "no s&#x27;ha pogut enviar" in page or "no s'ha pogut enviar" in page


def test_a_limited_origin_does_not_record_another_request(member, client, enabled, text, settings):
    from apps.website.models import NewsletterEvent

    settings.JOIN_FORM_ORIGIN_MAX = 1
    client.post(URL, {"accept_newsletter": "on"})
    client.post(URL, {"accept_newsletter": "on"})
    assert NewsletterEvent.objects.filter(kind="requested").count() == 1
