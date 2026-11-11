"""Integració de l'RGPD (T-M01-22) amb les peces de la nit de l'11/11/2026: el límit diari de
correu (T-M00-06), la invitació del compte personal (T-M01-14) i el QR del carnet (T-M01-19).
Només dades inventades.
"""

import pytest
from django.test import override_settings

from apps.accounts import invitations
from apps.core import mail, privacy
from apps.core.models import OutgoingEmail, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members import cards, services
from apps.members.tests.test_cards import SYSTEM, paid_member

pytestmark = pytest.mark.django_db


@pytest.fixture
def person():
    return Person.objects.create(
        first_name="Ona",
        last_name="Integració Inventada",
        origin=Person.Origin.WEB,
        contact_email="ona.integracio@example.org",
    )


@override_settings(EMAIL_DAILY_LIMIT=1, EMAIL_TRANSACTIONAL_RESERVE=0)
def test_a_deferred_email_keeps_its_address_until_it_goes_out(person, make_admin):  # noqa: F811
    """RN-A14: el que es va posar a la cua abans d'anonimitzar surt igualment. Un correu ajornat
    pel límit diari (T-M00-06) encara ha de sortir: no perd l'adreça en anonimitzar."""
    first = mail.queue_email("prova", to="una.altra@example.org")
    mail.deliver(first.pk)
    deferred = mail.queue_email("prova", to=person.contact_email, person=person)
    mail.deliver(deferred.pk)
    deferred.refresh_from_db()
    assert deferred.status == OutgoingEmail.Status.DEFERRED

    privacy.anonymise_person(person, by=make_admin("administrator"))

    deferred.refresh_from_db()
    assert deferred.to_address == "ona.integracio@example.org"
    assert deferred.person_id == person.pk


def test_anonymising_invalidates_the_account_invitation(person, make_admin):  # noqa: F811
    token = invitations.create(person)
    privacy.anonymise_person(person, by=make_admin("administrator"))
    assert invitations.invitation_for_token(token) is None


def test_anonymising_a_member_makes_the_card_qr_invalid(make_admin):  # noqa: F811
    member = paid_member()
    token = cards.issue_card(member, by=SYSTEM)
    assert services.verify_card(token)["valid"] is True
    privacy.anonymise_person(member.person, by=make_admin("administrator"))
    assert services.verify_card(token)["valid"] is False
