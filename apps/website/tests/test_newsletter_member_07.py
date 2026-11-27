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


def test_108_subscribing_is_immediate_with_the_consent_and_no_email(member, client, enabled, text):
    """108 (C.2; substitueix la P-631): el correu d'entrada és verificat, la subscripció és ara."""
    from apps.core.models import OutgoingEmail

    assert client.post(URL, {"accio": "alta"}).status_code == 303  # sense acceptar el text
    assert not NewsletterSubscription.objects.exists()
    client.post(URL, {"accept_newsletter": "on"})
    subscription = NewsletterSubscription.objects.get()
    assert (subscription.email, subscription.status) == (member.login, S.CONFIRMED)
    assert subscription.legal_text == text
    consent = Consent.objects.get(person=member.person)
    assert (consent.action, consent.legal_text, consent.channel) == ("granted", text, "web")
    assert not OutgoingEmail.objects.exists()
    assert "Reps el butlletí" in client.get(URL).content.decode()
    assert list(newsletter.recipients()) == [subscription]


def test_a_pending_subscription_from_the_public_form_is_confirmed_from_the_area(
    member, client, enabled, text
):
    newsletter.subscribe(member.login, legal_text=text)
    assert "Pendent de confirmar" in client.get(URL).content.decode()
    client.post(URL, {"accept_newsletter": "on"})
    assert NewsletterSubscription.objects.get().status == S.CONFIRMED


def test_p492_unsubscribing_withdraws_the_consent_and_keeps_only_the_trace(
    member, client, enabled, text
):
    client.post(URL, {"accept_newsletter": "on"})
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
