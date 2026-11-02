"""Textos legals i consentiments (T-M01-08; spec 00, HU-17, CA-17.1 a CA-17.3, RN-80, RN-53).
Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404

from apps.core import audit, consents
from apps.core.models import AppendOnlyError, AuditEntry, Consent, LegalText, Role

pytestmark = pytest.mark.django_db
R = Role.Code
WEB, IN_PERSON = Consent.Channel.WEB, Consent.Channel.IN_PERSON


@pytest.fixture
def publisher(make_admin):
    return make_admin(R.ADMINISTRATOR)


@pytest.fixture
def newsletter(publisher):
    return consents.publish_text("newsletter", "Vull rebre el butlletí del club.", by=publisher)


@pytest.fixture
def person(make_person):
    return make_person("Laia", "Ferrer")


class TestPublishing:
    def test_versions_go_up_per_kind(self, publisher):
        first = consents.publish_text("privacy", "Política v1", by=publisher)
        second = consents.publish_text("privacy", "Política v2", by=publisher)
        other = consents.publish_text("newsletter", "Butlletí", by=publisher)
        assert (first.version, second.version, other.version) == (1, 2, 1)
        assert consents.current_text("privacy") == second
        assert second.published_by == publisher

    def test_needs_the_permission(self, make_admin):
        # M12: sense permís, «no trobat».
        with pytest.raises(Http404):
            consents.publish_text("privacy", "Text", by=make_admin(R.SECRETARY))
        assert not LegalText.objects.exists()

    def test_empty_text_is_refused(self, publisher):
        with pytest.raises(ValidationError):
            consents.publish_text("privacy", "   ", by=publisher)

    def test_kind_must_be_a_code(self, publisher):
        with pytest.raises(ValidationError):
            consents.publish_text("dret d'imatge", "Text", by=publisher)

    def test_a_published_version_cannot_change(self, newsletter):
        newsletter.content = "Un altre text"
        with pytest.raises(AppendOnlyError):
            newsletter.save()
        with pytest.raises(AppendOnlyError):
            LegalText.objects.update(content="x")
        with pytest.raises(AppendOnlyError):
            newsletter.delete()
        assert LegalText.objects.get().content == "Vull rebre el butlletí del club."

    def test_publishing_is_recorded(self, newsletter, publisher):
        row = AuditEntry.objects.get(action=consents.PUBLISHED)
        assert row.actor_account == publisher
        assert row.details == {"kind": "newsletter", "version": 1}


class TestGranting:
    def test_web_consent_keeps_person_version_time_and_channel(self, newsletter, person):
        # CA-17.1
        consent = consents.grant(person, "newsletter", channel=WEB)
        consent.refresh_from_db()
        assert consent.person == person
        assert consent.legal_text == newsletter
        assert consent.action == Consent.Action.GRANTED
        assert consent.channel == WEB
        assert consent.recorded_by is None
        assert consent.created_at is not None
        assert consents.has_consent(person, "newsletter")

    def test_in_person_consent_keeps_the_recording_account(self, newsletter, person, make_admin):
        secretary = make_admin(R.SECRETARY)
        consent = consents.grant(person, "newsletter", channel=IN_PERSON, by=secretary)
        assert consent.recorded_by == secretary
        row = AuditEntry.objects.get(action=consents.GRANTED)
        assert row.actor_account == secretary
        assert row.actor_roles == [R.SECRETARY]

    def test_in_person_needs_an_account(self, newsletter, person):
        with pytest.raises(ValidationError):
            consents.grant(person, "newsletter", channel=IN_PERSON)
        assert not Consent.objects.exists()

    def test_the_database_also_refuses_in_person_without_account(self, newsletter, person):
        with pytest.raises(IntegrityError), transaction.atomic():
            Consent.objects.create(
                person=person, legal_text=newsletter, action="granted", channel=IN_PERSON
            )

    def test_without_a_published_text_there_is_nothing_to_accept(self, person):
        with pytest.raises(ValidationError):
            consents.grant(person, "image", channel=WEB)

    def test_granting_again_the_same_version_adds_nothing(self, newsletter, person):
        first = consents.grant(person, "newsletter", channel=WEB)
        assert consents.grant(person, "newsletter", channel=WEB) == first
        assert Consent.objects.count() == 1

    def test_a_guest_or_a_visitor_is_recorded_as_such(self, newsletter, person):
        consents.grant(person, "newsletter", channel=WEB, by=audit.guest(person, 5))
        row = AuditEntry.objects.get(action=consents.GRANTED)
        assert (row.actor_kind, row.actor_origin) == ("guest", "guest_link:5")
        assert (row.target_type, row.target_id) == ("core.person", str(person.pk))
        assert (row.field, row.new_value) == ("consent:newsletter", "granted")
        assert row.details == {"version": 1, "channel": "web"}

    def test_consents_cannot_be_edited(self, newsletter, person):
        consent = consents.grant(person, "newsletter", channel=WEB)
        with pytest.raises(AppendOnlyError):
            consent.save()
        with pytest.raises(AppendOnlyError):
            Consent.objects.filter(pk=consent.pk).update(action="withdrawn")


class TestNewVersion:
    def test_old_consents_stay_with_the_accepted_version(self, newsletter, person, publisher):
        # CA-17.2. Si cal tornar a demanar-lo depèn de Q-16: de moment, continua vigent.
        old = consents.grant(person, "newsletter", channel=WEB)
        consents.publish_text("newsletter", "Butlletí, versió nova", by=publisher)
        old.refresh_from_db()
        assert old.legal_text == newsletter
        assert consents.has_consent(person, "newsletter")

    def test_accepting_the_new_version_adds_a_row(self, newsletter, person, publisher):
        consents.grant(person, "newsletter", channel=WEB)
        second = consents.publish_text("newsletter", "Butlletí, versió nova", by=publisher)
        new = consents.grant(person, "newsletter", channel=WEB)
        assert new.legal_text == second
        assert Consent.objects.count() == 2


class TestWithdrawing:
    def test_withdrawal_is_a_new_row_with_immediate_effect(self, newsletter, person):
        # CA-17.3
        given = consents.grant(person, "newsletter", channel=WEB)
        withdrawn = consents.withdraw(person, "newsletter", channel=WEB)
        given.refresh_from_db()
        assert given.action == Consent.Action.GRANTED
        assert withdrawn.action == Consent.Action.WITHDRAWN
        assert withdrawn.legal_text == newsletter
        assert not consents.has_consent(person, "newsletter")
        assert AuditEntry.objects.get(action=consents.WITHDRAWN).new_value == "withdrawn"

    def test_withdrawing_without_consent_does_nothing(self, newsletter, person):
        assert consents.withdraw(person, "newsletter", channel=WEB) is None
        consents.grant(person, "newsletter", channel=WEB)
        consents.withdraw(person, "newsletter", channel=WEB)
        assert consents.withdraw(person, "newsletter", channel=WEB) is None
        assert Consent.objects.count() == 2

    def test_granting_after_withdrawing(self, newsletter, person):
        consents.grant(person, "newsletter", channel=WEB)
        consents.withdraw(person, "newsletter", channel=WEB)
        consents.grant(person, "newsletter", channel=WEB)
        assert consents.has_consent(person, "newsletter")
        assert Consent.objects.count() == 3

    def test_each_kind_is_independent(self, newsletter, person, publisher):
        consents.publish_text("image", "Dret d'imatge", by=publisher)
        consents.grant(person, "newsletter", channel=WEB)
        assert not consents.has_consent(person, "image")
        consents.grant(person, "image", channel=WEB)
        consents.withdraw(person, "image", channel=WEB)
        assert consents.has_consent(person, "newsletter")
