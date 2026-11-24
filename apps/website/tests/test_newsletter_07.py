"""Butlletí: subscripció, confirmació i baixa (T-M07-13; CA-M07-06, 07, 09 i 10, RN-M07-08).
Només dades inventades."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.core import business_settings
from apps.core.models import LegalText, Setting
from apps.core.tests.conftest import main_of
from apps.website import newsletter
from apps.website.models import NewsletterEvent, NewsletterSubscription

pytestmark = pytest.mark.django_db
URL = "/butlleti/"
S = NewsletterSubscription.Status


@pytest.fixture
def enabled():
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)


@pytest.fixture
def text():
    return LegalText.objects.create(kind="newsletter", version=1, content="Butlletí inventat")


def _subscribe(client, email):
    return client.post(URL, {"email": email, "accept_newsletter": "on"})


def test_ca_m07_10_switched_off_every_route_is_not_found(client, text):
    assert business_settings.get(newsletter.ENABLED) is False
    sub, _ = newsletter.subscribe("nou@example.com", legal_text=text)
    for url in (
        URL,
        reverse("website:newsletter_confirm", args=[sub.token]),
        reverse("website:newsletter_unsubscribe", args=[sub.token]),
    ):
        assert client.get(url).status_code == 404
    assert (
        client.post(URL, {"email": "a@example.com", "accept_newsletter": "on"}).status_code == 404
    )


def test_ca_m07_06_the_screen_says_the_same_for_new_confirmed_and_unsubscribed(
    client, enabled, text
):
    confirmed, _ = newsletter.subscribe("confirmat@example.com", legal_text=text)
    newsletter.confirm(confirmed.token)
    gone, _ = newsletter.subscribe("baixa@example.com", legal_text=text)
    newsletter.unsubscribe(gone.token)

    pages = set()
    for email in ("nou@example.com", "Confirmat@example.com", "baixa@example.com"):
        response = _subscribe(client, email)
        assert response.status_code == 303 and response["Location"] == URL
        page = main_of(client.get(URL).content.decode())
        assert email.lower() not in page
        pages.add(page)
    assert len(pages) == 1 and "Revisa el correu" in pages.pop()
    # La baixa d'abans en deixa només la traça (T-M07-15): la fila nova és la del correu.
    states = dict(
        NewsletterSubscription.objects.filter(email__endswith="@example.com").values_list(
            "email", "status"
        )
    )
    assert states == {
        "nou@example.com": S.PENDING,
        "confirmat@example.com": S.CONFIRMED,
        "baixa@example.com": S.PENDING,
    }


def test_ca_m07_06_only_the_new_and_the_unsubscribed_need_a_confirmation(text):
    assert newsletter.subscribe("nou@example.com", legal_text=text)[1] is True
    confirmed, _ = newsletter.subscribe("confirmat@example.com", legal_text=text)
    newsletter.confirm(confirmed.token)
    token = NewsletterSubscription.objects.get(email="confirmat@example.com").token
    assert newsletter.subscribe("confirmat@example.com", legal_text=text)[1] is False
    assert NewsletterSubscription.objects.get(email="confirmat@example.com").token == token
    gone, _ = newsletter.subscribe("baixa@example.com", legal_text=text)
    newsletter.unsubscribe(gone.token)
    again, needs = newsletter.subscribe("baixa@example.com", legal_text=text)
    assert needs is True and again.token != gone.token


@pytest.mark.xfail(
    reason="Plantilla del correu de confirmació al nucli: T-M07-13b (docs/estat/M07.md)",
    strict=True,
)
def test_ca_m07_06_the_confirmation_email_is_queued(client, enabled, text):
    from apps.core.models import OutgoingEmail

    _subscribe(client, "nou@example.com")
    assert OutgoingEmail.objects.filter(to_address="nou@example.com").exists()


def test_ca_m07_06_a_late_confirmation_does_not_subscribe(text):
    sub, _ = newsletter.subscribe("tard@example.com", legal_text=text)
    hours = business_settings.get(newsletter.CONFIRM_HOURS)
    assert newsletter.confirm(sub.token, now=sub.requested_at + timedelta(hours=hours + 1)) is None
    sub.refresh_from_db()
    assert sub.status == S.PENDING


def test_ca_m07_07_opening_the_link_twice_leaves_one_confirmed_subscription(client, enabled, text):
    sub, _ = newsletter.subscribe("nou@example.com", legal_text=text)
    url = reverse("website:newsletter_confirm", args=[sub.token])
    # Obrir l'enllaç (p. ex. un programa que revisa el correu) no confirma res: cal el botó.
    assert "Confirma la subscripció" in client.get(url).content.decode()
    assert NewsletterSubscription.objects.get().status == S.PENDING
    for _ in range(2):
        assert "Subscripció confirmada" in client.post(url).content.decode()
    sub = NewsletterSubscription.objects.get()
    assert (sub.status, sub.legal_text) == (S.CONFIRMED, text)
    confirmations = NewsletterEvent.objects.filter(kind="confirmed")
    assert [event.legal_text for event in confirmations] == [text]


def test_an_unknown_confirmation_link_says_it_is_not_valid(client, enabled):
    url = reverse("website:newsletter_confirm", args=["no-existeix"])
    assert "ja no és vàlid" in client.post(url).content.decode()


def test_ca_m07_09_unsubscribing_is_immediate_and_the_page_is_always_the_same(
    client, enabled, text
):
    sub, _ = newsletter.subscribe("nou@example.com", legal_text=text)
    newsletter.confirm(sub.token)
    url = reverse("website:newsletter_unsubscribe", args=[sub.token])
    first = main_of(client.get(url).content.decode())
    sub.refresh_from_db()
    assert sub.status == S.UNSUBSCRIBED and sub.unsubscribed_at
    assert not newsletter.recipients().exists()
    assert main_of(client.get(url).content.decode()) == first
    unknown = reverse("website:newsletter_unsubscribe", args=["no-existeix"])
    assert main_of(client.get(unknown).content.decode()) == first
    kinds = list(sub.events.values_list("kind", flat=True))
    assert kinds == ["requested", "confirmed", "unsubscribed"]


def test_without_the_newsletter_text_nobody_can_subscribe(client, enabled):
    assert "no et pots subscriure" in client.get(URL).content.decode()
    _subscribe(client, "nou@example.com")
    assert not NewsletterSubscription.objects.exists()


def test_the_text_must_be_accepted(client, enabled, text):
    response = client.post(URL, {"email": "nou@example.com"})
    assert response.status_code == 200
    assert not NewsletterSubscription.objects.exists()


def test_too_many_requests_from_one_origin_save_nothing_more(client, enabled, text, settings):
    settings.JOIN_FORM_ORIGIN_MAX = 1
    _subscribe(client, "u@example.com")
    response = _subscribe(client, "dos@example.com")
    assert response.status_code == 303
    assert list(NewsletterSubscription.objects.values_list("email", flat=True)) == ["u@example.com"]


def test_only_confirmed_subscriptions_are_recipients(text):
    now = timezone.now()
    confirmed, _ = newsletter.subscribe("c@example.com", legal_text=text, now=now)
    newsletter.confirm(confirmed.token, now=now)
    newsletter.subscribe("p@example.com", legal_text=text, now=now)
    gone, _ = newsletter.subscribe("b@example.com", legal_text=text, now=now)
    newsletter.unsubscribe(gone.token)
    assert list(newsletter.recipients()) == [confirmed]


@pytest.mark.parametrize("method", ["head", "put"])
@pytest.mark.parametrize(
    "url", [URL, "/butlleti/confirmar/x/", "/butlleti/baixa/x/"], ids=["form", "confirm", "baixa"]
)
def test_ca_m07_10_switched_off_any_method_is_not_found(client, method, url):
    """Revisió de la #582: l'interruptor es mira abans del mètode."""
    assert getattr(client, method)(url).status_code == 404
