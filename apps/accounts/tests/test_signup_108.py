"""Compte personal ràpid (T-M01-53; decisió 108, D.1 i D.4): una pantalla, només nom, correu,
contrasenya, la casella del butlletí i la privacitat; compte pendent fins a confirmar el correu;
la mateixa resposta tant si el correu ja té compte com si no; tornar on volia anar. Només dades
inventades."""

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts import email_links, signup, tokens
from apps.accounts.models import Account, EmailLinkRequest
from apps.core import consents
from apps.core.models import Consent, OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_join import strip_tokens
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
URL = reverse("accounts:signup")
EMAIL = "nura.blau@example.org"


@pytest.fixture
def texts(make_admin):  # noqa: F811
    publisher = make_admin("administrator")
    for kind in ("privacy", "newsletter"):
        consents.publish_text(kind, f"Text de prova: {kind}.", by=publisher)


def _versions():
    return ";".join(f"{k}:{t.version}" for k, t in signup.current_texts().items())


def _data(**overrides):
    data = {"first_name": "Nura", "last_name": "Blau Fons", "email": EMAIL, "password": PASSWORD,
            "accept_privacy": "on", "text_versions": _versions()}  # fmt: skip
    data.update(overrides)
    return {k: v for k, v in data.items() if v is not None}


def _confirmation(client):
    return client.get(URL).content.decode()


def test_one_screen_creates_a_pending_account_with_privacy_and_sends_the_link(texts):
    client = Client()
    response = client.post(URL, _data())
    assert response.status_code == 303 and response["Location"] == URL
    account = Account.objects.get(login=EMAIL)
    assert account.kind == Account.Kind.PERSONAL and account.status == Account.Status.PENDING
    person = account.person
    assert (person.first_name, person.last_name, person.contact_email) == (
        "Nura",
        "Blau Fons",
        EMAIL,
    )
    assert not person.id_document_number and not person.phone and person.birth_date is None
    assert consents.has_consent(person, "privacy")
    assert not consents.has_consent(person, "newsletter")  # no marcada per defecte
    assert (
        OutgoingEmail.objects.filter(template="verificacio-correu", to_address=EMAIL).count() == 1
    )
    assert "Revisa el correu" in _confirmation(client)
    assert "_auth_user_id" not in client.session  # pendent: cap sessió (RN-18)


def test_the_form_asks_nothing_else_and_the_newsletter_box_comes_unchecked(texts):
    html = Client().get(URL).content.decode()
    assert "Vull rebre les sortides, els cursos i les novetats del C.R.I.S." in html
    assert 'name="accept_newsletter" id="id_accept_newsletter">' in html  # sense «checked»
    for absent in ("id_document", "birth_date", "phone", "address"):
        assert f'name="{absent}"' not in html
    assert html.index("accept_newsletter") < html.index('name="first_name"')  # el més destacat


def test_the_newsletter_box_only_saves_the_choice(texts):
    Client().post(URL, _data(accept_newsletter="on"))
    person = Account.objects.get(login=EMAIL).person
    consent = Consent.objects.get(person=person, legal_text__kind="newsletter")
    assert consent.action == Consent.Action.GRANTED and consent.channel == Consent.Channel.WEB
    from apps.website.models import NewsletterSubscription

    assert not NewsletterSubscription.objects.exists()  # la subscripció és de la T-M07-32


def test_an_existing_email_gets_the_same_answer_and_only_a_notice(texts):
    person = Person.objects.create(first_name="Ja", origin=Person.Origin.WEB)
    Account.objects.create_personal(person, EMAIL, PASSWORD)
    before = Person.objects.count()
    client = Client()
    fresh = Client()
    assert client.post(URL, _data()).status_code == 303
    assert fresh.post(URL, _data(email="nou.compte@example.org")).status_code == 303
    assert strip_tokens(_confirmation(client)) == strip_tokens(_confirmation(fresh))
    assert Person.objects.count() == before + 1  # només el compte nou
    notice = OutgoingEmail.objects.get(template=signup.EXISTING_TEMPLATE)
    assert notice.to_address == EMAIL
    assert not OutgoingEmail.objects.filter(template="verificacio-correu", to_address=EMAIL)


@pytest.mark.parametrize(
    "overrides",
    [
        {"accept_privacy": None},
        {"password": "curta"},
        {"password": "nura.blau@example.org"},
        {"email": "no-es-un-correu"},
        {"first_name": ""},
    ],  # fmt: skip
)
def test_invalid_data_creates_nothing(texts, overrides):
    response = Client().post(URL, _data(**overrides))
    assert response.status_code == 200
    assert not Account.objects.filter(kind=Account.Kind.PERSONAL).exists()
    assert not OutgoingEmail.objects.filter(template="verificacio-correu").exists()


def test_password_errors_are_in_catalan(texts):
    html = Client().post(URL, _data(password="curta")).content.decode()  # noqa: S106 (invàlida)
    assert "La contrasenya és massa curta" in html and "too short" not in html


def test_without_a_privacy_text_no_account_can_be_created():
    assert Client().get(URL).status_code == 503


def test_the_origin_limit_saves_nothing(texts, settings):
    settings.JOIN_FORM_ORIGIN_MAX = 1
    client = Client()
    client.post(URL, _data())
    response = client.post(URL, _data(email="segon@example.org"))
    assert response.status_code == 429
    assert not Account.objects.filter(login="segon@example.org").exists()
    assert EmailLinkRequest.objects.filter(purpose=EmailLinkRequest.Purpose.SIGNUP).count() == 1


@pytest.mark.parametrize(
    ("next_url", "kept"),
    [("/fer-se-soci/", True), ("https://exemple.cat/", False), ("//exemple.cat/", False)],
)
def test_next_is_validated_and_the_confirmed_email_returns_there(texts, next_url, kept):
    client = Client()
    html = client.get(f"{URL}?next={next_url}").content.decode()
    assert (f'name="next" value="{next_url}"' in html) is kept
    client.post(URL, {**_data(), "next": next_url})
    account = Account.objects.get(login=EMAIL)
    session = client.session
    session[email_links.VERIFY_SESSION_KEY] = tokens.make_token(account, tokens.VERIFY_EMAIL)
    session.save()
    done = client.post(reverse("accounts:verify_email")).content.decode()
    assert ("?next=/fer-se-soci/" in done) is kept
    assert "exemple.cat" not in done
    account.refresh_from_db()
    assert account.status == Account.Status.ACTIVE


def test_the_login_page_offers_to_create_the_account_keeping_next():
    html = Client().get(reverse("accounts:login") + "?next=/fer-se-soci/").content.decode()
    assert f"{URL}?next=/fer-se-soci/" in html


# --- Revisió independent (28/11/2026) -------------------------------------------------------


def _verify(client, account, data=None):
    session = client.session
    session[email_links.VERIFY_SESSION_KEY] = tokens.make_token(account, tokens.VERIFY_EMAIL)
    session.save()
    return client.post(reverse("accounts:verify_email"), data or {})


def test_a_squatter_password_never_activates_the_account(texts):
    """(A) Algú crea el compte amb el correu d'una altra persona: la víctima, des d'un altre
    navegador, l'activa només triant-hi una contrasenya nova; la de l'atacant deixa de valer."""
    Client().post(URL, _data())  # l'atacant
    account = Account.objects.get(login=EMAIL)
    victim = Client()
    assert _verify(victim, account).status_code == 200  # sense contrasenya nova, res
    account.refresh_from_db()
    assert account.status == Account.Status.PENDING
    new = "contrasenya-de-proves-1954-nova"  # noqa: S105 gitleaks:allow (dada inventada)
    _verify(victim, account, {"new_password1": new, "new_password2": new})
    account.refresh_from_db()
    assert account.status == Account.Status.ACTIVE
    assert account.check_password(new) and not account.check_password(PASSWORD)


def test_a_pending_address_gets_the_verification_again_not_a_dead_end(texts):
    """(A) Si l'adreça ja té un compte pendent, rep l'enllaç de verificació (que deixa triar la
    contrasenya), no l'avís sense enllaç."""
    Client().post(URL, _data())
    Client().post(URL, _data())
    sent = OutgoingEmail.objects.filter(to_address=EMAIL)
    assert sent.filter(template="verificacio-correu").count() == 2
    assert not sent.filter(template=signup.EXISTING_TEMPLATE).exists()


def test_expired_pending_signups_are_purged_and_free_the_address(texts):
    """(A) Passat el termini de la verificació, el compte pendent i la persona d'aquesta pantalla
    s'anonimitzen i l'adreça torna a estar lliure."""
    from datetime import timedelta

    from django.utils import timezone

    Client().post(URL, _data())
    account = Account.objects.get(login=EMAIL)
    Account.objects.filter(pk=account.pk).update(created_at=timezone.now() - timedelta(hours=49))
    assert signup.purge_expired() == 1
    account.refresh_from_db()
    assert account.status == Account.Status.DISABLED and account.login != EMAIL
    assert account.person.status == Person.Status.ANONYMISED
    assert Client().post(URL, _data()).status_code == 303
    assert Account.objects.filter(login=EMAIL, status=Account.Status.PENDING).exists()


def test_an_existing_person_without_account_gets_the_invitation_not_a_duplicate(texts):
    """(C) Una persona activa amb aquest correu i sense compte personal (p. ex. un soci importat):
    cap persona nova; rep la invitació, i la resposta és la mateixa."""
    person = Person.objects.create(
        first_name="Ja", origin=Person.Origin.IN_PERSON, contact_email=EMAIL
    )
    before = Person.objects.count()
    client = Client()
    assert client.post(URL, _data()).status_code == 303
    assert Person.objects.count() == before and not Account.objects.filter(login=EMAIL).exists()
    assert OutgoingEmail.objects.filter(template="invitacio-compte", person=person).count() == 1
    assert "Revisa el correu" in _confirmation(client)


def test_a_new_privacy_version_between_get_and_post_is_rejected(texts, make_admin):  # noqa: F811
    """(D) Es desa la versió exacta que la persona ha vist."""
    shown = consents.current_text("privacy").version
    consents.publish_text("privacy", "Text de prova: privacy v2.", by=make_admin("administrator"))
    response = Client().post(URL, _data(text_versions=f"privacy:{shown};newsletter:1"))
    assert response.status_code == 200 and not Account.objects.filter(login=EMAIL).exists()
