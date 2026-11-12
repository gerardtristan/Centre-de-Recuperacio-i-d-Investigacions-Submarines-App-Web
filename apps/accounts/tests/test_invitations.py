"""Invitació per crear el compte personal (T-M01-14; decisió 079, A-11; RN-M01-87; CA-M01-90 i
CA-M01-91; especificació a docs/planning.md#M01-079-invitacio). Només dades inventades.
"""

import datetime
import re

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts import invitations
from apps.accounts.models import Account, AccountInvitation
from apps.core.models import AuditEntry, OutgoingEmail, Person
from conftest import NEW_PASSWORD, PASSWORD

pytestmark = pytest.mark.django_db

PAGE = "accounts:invitation"
LINK = "accounts:invitation_link"
ADULT = datetime.date(1990, 2, 14)
EMAIL = "mar@example.org"
INVALID = "Aquest enllaç no és vàlid o ha caducat."


@pytest.fixture
def person(make_person):
    return make_person("Mar", "Soler", contact_email=EMAIL, birth_date=ADULT)


def years_ago(years):
    today = timezone.localdate()
    return today.replace(year=today.year - years, day=min(today.day, 28))


def open_link(client, token):
    first = client.get(reverse(LINK, args=[token]))
    assert first.status_code == 302
    assert first["Location"] == reverse(PAGE)
    assert first["Referrer-Policy"] == "no-referrer"
    return client.get(reverse(PAGE))


def submit(client, password=PASSWORD, again=None):
    return client.post(
        reverse(PAGE), {"new_password1": password, "new_password2": again or password}
    )


def body(response):
    """El cos sense el testimoni CSRF, per comparar respostes."""
    text = re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"', "", response.content.decode())
    return re.sub(r'"X-CSRFToken": "[^"]+"', "", text)


class TestCaM0190CreateAndStore:
    def test_ca_m01_90_only_the_hash_is_stored(self, person):
        token = invitations.create(person)
        invitation = AccountInvitation.objects.get()
        assert invitation.token_hash == invitations._hash(token)
        assert invitation.token_hash != token
        stored = " ".join(str(value) for value in AccountInvitation.objects.values().get().values())
        assert token not in stored
        assert invitation.used_at is None and invitation.invalidated_at is None
        assert invitation.expires_at - invitation.created_at <= invitations.VALIDITY

    def test_ca_m01_90_token_is_never_in_the_audit_log(self, person, admin_account):
        token = invitations.create(person, by=admin_account)
        entry = AuditEntry.objects.get(action=invitations.CREATED)
        assert entry.actor_account == admin_account
        assert token not in str(AuditEntry.objects.values().get(pk=entry.pk))
        assert invitations._hash(token) not in str(AuditEntry.objects.values().get(pk=entry.pk))

    def test_a_new_invitation_invalidates_the_previous_one(self, person):
        old = invitations.create(person)
        new = invitations.create(person)
        assert invitations.invitation_for_token(old) is None
        assert invitations.invitation_for_token(new) is not None
        assert AccountInvitation.objects.filter(invalidated_at__isnull=False).count() == 1

    def test_send_queues_the_email_with_the_link_and_no_personal_data(self, person):
        assert invitations.send(person) is True
        email = OutgoingEmail.objects.get()
        assert email.template == invitations.INVITATION_TEMPLATE
        assert email.to_address == EMAIL
        assert "/compte/invitacio/" in email.body_text
        assert str(invitations.hours()) in email.body_text
        for text in ("Mar", "Soler", EMAIL):
            assert text not in email.body_text
            assert text not in email.subject


class TestEligibility:
    def test_adult_with_email_and_without_account(self, person):
        assert invitations.eligible(person)

    def test_ca_m01_91_under_14_is_never_invited(self, make_person):
        child = make_person(
            "Nil", "Petit", contact_email="nil@example.org", birth_date=years_ago(13)
        )
        assert not invitations.eligible(child)
        assert invitations.send(child) is False
        assert not AccountInvitation.objects.exists()
        assert not OutgoingEmail.objects.exists()

    def test_ca_m01_91_from_14_with_own_email(self, make_person):
        teen = make_person(
            "Aina", "Roig", contact_email="aina@example.org", birth_date=years_ago(15)
        )
        assert invitations.eligible(teen)

    def test_ca_m01_91_without_own_email(self, make_person):
        teen = make_person("Aina", "Roig", birth_date=years_ago(15))
        assert not invitations.eligible(teen)

    def test_unknown_age_is_not_blocked(self, make_person):
        assert invitations.eligible(make_person("Pau", "Mas", contact_email="pau@example.org"))

    def test_ca_m01_91_person_with_personal_account(self, personal_account):
        person = personal_account.person
        Person.objects.filter(pk=person.pk).update(contact_email="anna@example.org")
        person.refresh_from_db()
        assert not invitations.eligible(person)
        assert invitations.send_for_approved_join(person) == invitations.SENT_NOTICE
        assert not AccountInvitation.objects.exists()
        email = OutgoingEmail.objects.get()
        assert email.template == invitations.NOTICE_TEMPLATE
        assert "/compte/invitacio/" not in email.body_text

    def test_anonymised_person(self, person):
        Person.objects.filter(pk=person.pk).update(
            status=Person.Status.ANONYMISED, anonymous_ref="A-0001"
        )
        person.refresh_from_db()
        assert not invitations.eligible(person)


class TestCaM0190Accept:
    def test_ca_m01_90_end_to_end(self, client, person):
        token = invitations.create(person)
        page = open_link(client, token)
        assert page.context["state"] == "ready"
        assert page["Referrer-Policy"] == "same-origin"
        assert token not in page.content.decode()
        for text in ("Mar", "Soler", EMAIL):  # la pàgina no mostra cap dada de la persona
            assert text not in page.content.decode()
        assert not Account.objects.filter(kind=Account.Kind.PERSONAL).exists()  # el GET no crea res

        done = submit(client)
        assert done.context["state"] == "done"
        account = Account.objects.get(kind=Account.Kind.PERSONAL)
        assert (account.person, account.login, account.status) == (
            person,
            EMAIL,
            Account.Status.ACTIVE,
        )
        assert account.check_password(PASSWORD)
        assert "_auth_user_id" not in client.session  # no obre cap sessió
        assert AccountInvitation.objects.get().used_at is not None
        entry = AuditEntry.objects.get(action=invitations.ACCEPTED)
        assert entry.target_id == str(account.pk)

        login = client.post(reverse("accounts:login"), {"login": EMAIL, "password": PASSWORD})
        assert login.status_code == 302
        assert "_auth_user_id" in client.session

    def test_ca_m01_90_same_link_does_not_work_twice(self, client, person):
        token = invitations.create(person)
        open_link(client, token)
        submit(client)
        other = type(client)()
        assert open_link(other, token).context["state"] == "invalid"
        assert Account.objects.filter(kind=Account.Kind.PERSONAL).count() == 1

    def test_ca_m01_90_all_unusable_links_get_the_same_page(self, client, person, make_person):
        expired = invitations.create(person)
        AccountInvitation.objects.update(expires_at=timezone.now() - datetime.timedelta(minutes=1))
        superseded_person = make_person("Ona", "Vidal", contact_email="ona@example.org")
        superseded = invitations.create(superseded_person)
        invitations.create(superseded_person)
        taken_person = make_person("Joana", "Pla", contact_email="anna@example.org")
        Account.objects.create_personal(
            make_person("Altra", "Persona"), "anna@example.org", PASSWORD
        )
        taken = invitations.create(taken_person)
        has_account = make_person("Laia", "Bru", contact_email="laia@example.org")
        with_account = invitations.create(has_account)
        Account.objects.create_personal(has_account, "laia.altre@example.org", PASSWORD)

        pages = [
            body(open_link(type(client)(), token))
            for token in ("no-existeix", expired, superseded, taken, with_account)
        ]
        assert all(INVALID in page for page in pages)
        assert len(set(pages)) == 1
        posts = []
        for token in ("no-existeix", expired, superseded, taken, with_account):
            fresh = type(client)()
            fresh.get(reverse(LINK, args=[token]))
            posts.append(body(submit(fresh)))
        assert len(set(posts)) == 1 and INVALID in posts[0]
        assert Account.objects.filter(kind=Account.Kind.PERSONAL).count() == 2  # cap de nou

    def test_page_without_any_link_is_invalid(self, client):
        assert client.get(reverse(PAGE)).context["state"] == "invalid"
        assert submit(client).context["state"] == "invalid"

    def test_password_rules_apply_and_nothing_is_created(self, client, person):
        open_link(client, invitations.create(person))
        mismatch = submit(client, PASSWORD, NEW_PASSWORD)
        assert mismatch.context["state"] == "ready"
        assert mismatch.context["form"].errors
        weak = submit(client, "1234")
        assert weak.context["form"].errors
        assert not Account.objects.filter(kind=Account.Kind.PERSONAL).exists()
        assert AccountInvitation.objects.get().used_at is None
        assert submit(client).context["state"] == "done"  # l'enllaç encara serveix

    def test_account_is_only_created_with_post_and_csrf(self, person):
        from django.test import Client

        strict = Client(enforce_csrf_checks=True)
        strict.get(reverse(LINK, args=[invitations.create(person)]))
        response = strict.post(
            reverse(PAGE), {"new_password1": PASSWORD, "new_password2": PASSWORD}
        )
        assert response.status_code == 403
        assert not Account.objects.filter(kind=Account.Kind.PERSONAL).exists()

    def test_invalidate_makes_the_link_unusable(self, client, person):
        token = invitations.create(person)
        assert invitations.invalidate(person) == 1
        assert open_link(client, token).context["state"] == "invalid"
