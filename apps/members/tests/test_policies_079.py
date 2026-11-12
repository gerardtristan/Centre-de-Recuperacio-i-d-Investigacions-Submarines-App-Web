"""Polítiques a la primera entrada dels importats de Cluber (T-M01-25; 079, A-27 punt 4;
RN-M01-95, CA-M01-109). Només dades inventades.
"""

import time

import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Account
from apps.accounts.security import AREA_PERSONAL
from apps.accounts.sessions import AREA_SESSION_KEY, AUTH_AT_SESSION_KEY
from apps.core import consents
from apps.core.models import AuditEntry, Consent, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import policies
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
PAGE = "members:accept_policies"


@pytest.fixture
def texts(make_admin):  # noqa: F811
    publisher = make_admin("administrator")
    for kind in ("privacy", "membership_terms"):
        consents.publish_text(kind, f"Text de prova: {kind}.", by=publisher)


def personal(origin, email="importat@example.org"):
    person = Person.objects.create(first_name="Importat", last_name="Prova", origin=origin)
    account = Account.objects.create_personal(person, email, PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    client = Client()
    client.force_login(account)
    session = client.session
    session[AREA_SESSION_KEY] = AREA_PERSONAL
    session[AUTH_AT_SESSION_KEY] = time.time()
    session.save()
    return client, account


class TestCaM01109:
    def test_ca_m01_109_imported_member_cannot_continue_without_accepting(self, texts):
        client, account = personal(Person.Origin.CLUBER_IMPORT)
        for name in ("core:home", "members:profile", "accounts:security"):
            response = client.get(reverse(name))
            assert response.status_code == 302
            assert response["Location"].startswith(reverse(PAGE))
        page = client.get(reverse(PAGE))
        assert page.status_code == 200
        assert "Text de prova: privacy." in page.content.decode()

    def test_ca_m01_109_accepting_records_the_version_and_lets_them_in(self, texts):
        client, account = personal(Person.Origin.CLUBER_IMPORT)
        response = client.post(
            reverse(PAGE),
            {"accept_privacy": "on", "accept_membership_terms": "on", "next": "/socis/perfil/"},
        )
        assert response.status_code == 303 and response["Location"] == "/socis/perfil/"
        for kind in ("privacy", "membership_terms"):
            consent = Consent.objects.get(person=account.person, legal_text__kind=kind)
            assert consent.action == Consent.Action.GRANTED
            assert consent.channel == Consent.Channel.WEB
            assert consent.legal_text == consents.current_text(kind)
        assert (
            AuditEntry.objects.filter(action=consents.GRANTED, actor_account=account).count() == 2
        )
        assert client.get(reverse("members:profile")).status_code != 302

    def test_ca_m01_109_both_boxes_are_required(self, texts):
        client, account = personal(Person.Origin.CLUBER_IMPORT)
        response = client.post(reverse(PAGE), {"accept_privacy": "on"})
        assert response.status_code == 200
        assert "Cal que l&#x27;acceptis per continuar." in response.content.decode()
        assert not Consent.objects.filter(person=account.person).exists()
        assert client.get(reverse("core:home")).status_code == 302

    def test_ca_m01_109_next_cannot_leave_the_site(self, texts):
        client, _account = personal(Person.Origin.CLUBER_IMPORT)
        response = client.post(
            reverse(PAGE),
            {"accept_privacy": "on", "accept_membership_terms": "on", "next": "https://x.invalid/"},
        )
        assert response["Location"] == reverse("core:home")

    def test_the_member_can_log_out_without_accepting(self, texts):
        client, _account = personal(Person.Origin.CLUBER_IMPORT)
        response = client.post(reverse("accounts:logout"))
        assert response.status_code == 302
        assert response["Location"] == reverse("accounts:login")

    @pytest.mark.parametrize("origin", [Person.Origin.WEB, Person.Origin.IN_PERSON])
    def test_people_who_did_not_come_from_cluber_are_not_asked(self, texts, origin):
        client, _account = personal(origin, email=f"{origin}@example.org")
        assert client.get(reverse("core:home")).status_code == 200
        page = client.get(reverse(PAGE)).content.decode()
        assert "No tens cap text pendent d'acceptar." in page

    def test_an_imported_member_who_already_accepted_is_not_asked_again(self, texts):
        client, account = personal(Person.Origin.CLUBER_IMPORT)
        for kind in ("privacy", "membership_terms"):
            consents.grant(account.person, kind, channel=Consent.Channel.WEB, by=account)
        assert client.get(reverse("core:home")).status_code == 200

    def test_without_published_texts_nothing_is_asked(self, db):
        client, account = personal(Person.Origin.CLUBER_IMPORT)
        assert policies.pending_texts(account.person) == []
        assert client.get(reverse("core:home")).status_code == 200

    def test_the_administration_is_not_affected(self, texts, make_admin):  # noqa: F811
        person = Person.objects.create(
            first_name="Admin", last_name="Importat", origin=Person.Origin.CLUBER_IMPORT
        )
        admin = make_admin("secretary", person=person)
        from apps.members.tests.test_roster import admin_client

        assert admin_client(admin).get(reverse("administration:home")).status_code == 200
