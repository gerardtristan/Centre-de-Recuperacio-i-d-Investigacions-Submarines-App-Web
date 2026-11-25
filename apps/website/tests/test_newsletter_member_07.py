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


def test_p492_subscribing_saves_the_row_and_the_consent_of_the_00(member, client, enabled, text):
    assert client.post(URL, {"accio": "alta"}).status_code == 303  # sense acceptar el text
    assert not NewsletterSubscription.objects.exists()
    client.post(URL, {"accept_newsletter": "on"})
    subscription = NewsletterSubscription.objects.get()
    assert (subscription.email, subscription.status, subscription.legal_text) == (
        member.login,
        S.CONFIRMED,
        text,
    )
    consent = Consent.objects.get(person=member.person)
    assert (consent.action, consent.legal_text, consent.channel) == ("granted", text, "web")
    assert "Reps el butlletí" in client.get(URL).content.decode()
    assert list(newsletter.recipients()) == [subscription]


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


def test_a_member_already_subscribed_from_the_web_is_shown_as_subscribed(
    member, client, enabled, text
):
    pending, _ = newsletter.subscribe(member.login, legal_text=text)
    newsletter.confirm(pending.token)
    assert "Reps el butlletí" in client.get(URL).content.decode()
