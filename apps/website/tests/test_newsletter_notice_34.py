"""Avís del butlletí a l'inici de l'àrea del soci (T-M07-34; decisió 108, C.6; P-630 A). Només
dades inventades."""

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.security import AREA_ADMIN, AREA_PERSONAL
from apps.core.models import LegalText, Setting
from apps.website import newsletter
from apps.website.models import NewsletterNoticeDismissal, NewsletterSubscription

pytestmark = pytest.mark.django_db
HOME = reverse("core:home")
DISMISS = reverse("website:newsletter_notice_dismiss")
NOTICE = "Vols rebre les sortides, els cursos i les novetats del C.R.I.S.?"
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


def test_switched_off_there_is_no_notice(member, client, text):
    assert NOTICE not in client.get(HOME).content.decode()


def test_without_the_published_text_there_is_no_notice(member, client, enabled):
    assert NOTICE not in client.get(HOME).content.decode()


def test_the_notice_shows_and_closing_it_is_remembered_for_the_account(
    member, client, enabled, text
):
    page = client.get(HOME).content.decode()
    assert NOTICE in page and reverse("website:my_newsletter") in page
    response = client.post(DISMISS)
    assert response.status_code == 303 and response["Location"] == HOME
    assert NewsletterNoticeDismissal.objects.filter(account=member).exists()
    assert NOTICE not in client.get(HOME).content.decode()
    client.post(DISMISS)  # dues vegades: una sola fila
    assert NewsletterNoticeDismissal.objects.count() == 1
    assert not NewsletterSubscription.objects.exists()


@pytest.mark.parametrize("status", [S.PENDING, S.CONFIRMED, S.UNSUBSCRIBED])
def test_not_shown_to_who_already_asked_is_subscribed_or_left(
    member, client, enabled, text, status
):
    NewsletterSubscription.objects.create(
        email=newsletter.normalise(member.login), status=status, legal_text=text,
        token=f"testimoni-{status}", requested_at=timezone.now(),
    )  # fmt: skip
    assert NOTICE not in client.get(HOME).content.decode()


def test_an_administrator_account_cannot_dismiss(login_as, admin_account, enabled, text):
    client = login_as(admin_account, AREA_ADMIN)
    assert client.post(DISMISS).status_code in (302, 404)
    assert not NewsletterNoticeDismissal.objects.exists()
    assert newsletter.show_member_notice(admin_account) is False


def test_dismissing_needs_post(member, client, enabled, text):
    assert client.get(DISMISS).status_code == 405
