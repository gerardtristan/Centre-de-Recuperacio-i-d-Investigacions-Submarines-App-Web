"""Casella del butlletí en crear el compte i a «Fer-se soci» (T-M07-32; decisió 108, C.2;
RN-M07-06): subscriu al moment amb el correu d'entrada verificat, sense doble confirmació; el
compte pendent, en confirmar el correu; tot darrere de `website.newsletter_enabled`. Només dades
inventades."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts import email_links, tokens
from apps.accounts.models import Account
from apps.core import consents
from apps.core.models import AuditEntry, OutgoingEmail, Setting
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_join import form_data, publish_texts, visitor
from apps.members.tests.test_join_041 import versions
from apps.website import newsletter
from apps.website.models import NewsletterSubscription
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
EMAIL = "nura.blau@example.org"
Status = NewsletterSubscription.Status


@pytest.fixture
def texts(make_admin):  # noqa: F811
    publisher = make_admin("administrator")
    publish_texts(publisher)
    consents.publish_text("newsletter", "Text de prova: butlletí.", by=publisher)


@pytest.fixture
def switched_on(db):
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)


def _signup_versions():
    from apps.accounts import signup

    return ";".join(f"{k}:{t.version}" for k, t in signup.current_texts().items())


def _signup(**extra):
    data = {"first_name": "Nura", "last_name": "Blau", "email": EMAIL, "password": PASSWORD,
            "accept_privacy": "on", "text_versions": _signup_versions(), **extra}  # fmt: skip
    Client().post(reverse("accounts:signup"), data)
    return Account.objects.get(login=EMAIL)


def _confirm(account):
    return email_links.confirm_email(tokens.make_token(account, tokens.VERIFY_EMAIL))


def test_the_box_subscribes_when_the_email_is_confirmed(texts, switched_on):
    account = _signup(accept_newsletter="on")
    assert not NewsletterSubscription.objects.exists()  # pendent: encara no
    _confirm(account)
    subscription = NewsletterSubscription.objects.get(email=EMAIL)
    assert subscription.status == Status.CONFIRMED and subscription.token
    assert subscription.legal_text == consents.current_text("newsletter")
    assert not OutgoingEmail.objects.filter(template=newsletter.CONFIRMATION_TEMPLATE).exists()
    entry = AuditEntry.objects.get(action=newsletter.SUBSCRIBED_VERIFIED)
    assert entry.details["source"] == "signup" and entry.actor_account_id == account.pk


def test_without_the_box_or_with_the_switch_off_nothing_is_subscribed(texts):
    account = _signup(accept_newsletter="on")
    _confirm(account)  # interruptor apagat
    assert not NewsletterSubscription.objects.exists()
    assert consents.has_consent(account.person, "newsletter")  # l'elecció queda desada
    Setting.objects.filter(key=newsletter.ENABLED).update(initial_value=True)
    other = Account.objects.get(pk=_signup_other().pk)
    _confirm(other)
    assert not NewsletterSubscription.objects.exists()


def _signup_other():
    data = {"first_name": "Pol", "last_name": "Mar", "email": "pol.mar@example.org",
            "password": PASSWORD, "accept_privacy": "on",
            "text_versions": _signup_versions()}  # fmt: skip
    Client().post(reverse("accounts:signup"), data)
    return Account.objects.get(login="pol.mar@example.org")


def test_a_pending_account_is_never_subscribed(texts, switched_on):
    account = _signup(accept_newsletter="on")
    assert newsletter.subscribe_verified(account, source="signup") is None
    assert not NewsletterSubscription.objects.exists()


def test_an_already_confirmed_address_does_not_change(texts, switched_on):
    account = _signup(accept_newsletter="on")
    _confirm(account)
    first = NewsletterSubscription.objects.get()
    account.refresh_from_db()
    newsletter.subscribe_verified(account, source="join")
    assert NewsletterSubscription.objects.get().token == first.token


def test_join_for_me_subscribes_at_once_and_for_another_person_does_not(texts, switched_on):
    client = visitor()
    account = Account.objects.order_by("-pk").first()
    data = form_data(
        for_whom="self", first_name="Visitant", last_name="Prova", text_versions=versions()
    )
    assert (
        client.post(reverse("members:join"), {**data, "accept_newsletter": "on"}).status_code == 303
    )
    subscription = NewsletterSubscription.objects.get(email=account.login)
    assert subscription.status == Status.CONFIRMED
    assert consents.has_consent(account.person, "newsletter")
    other_client = visitor()
    other = form_data(
        id_document="00000001R", contact_email="fill@example.org", text_versions=versions()
    )
    other_client.post(reverse("members:join"), {**other, "accept_newsletter": "on"})
    assert NewsletterSubscription.objects.count() == 1


def test_join_for_me_does_not_store_the_newsletter_also_as_an_acceptance(texts, switched_on):
    """Revisió F: a l'alta «per a mi» el butlletí ja és consentiment de la 00; si també quedés com
    a acceptació de la sol·licitud, l'aprovació el tornaria a donar després d'una baixa."""
    from apps.members.models import JoinAcceptance

    client = visitor()
    data = form_data(
        for_whom="self", first_name="Visitant", last_name="Prova", text_versions=versions()
    )
    client.post(reverse("members:join"), {**data, "accept_newsletter": "on"})
    assert not JoinAcceptance.objects.filter(legal_text__kind="newsletter").exists()
    assert JoinAcceptance.objects.filter(legal_text__kind="privacy").exists()
