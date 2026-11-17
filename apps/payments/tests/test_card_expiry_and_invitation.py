"""Addenda de la 058 al 05a (T-M05a-23): mètode recomanat segons el proveïdor (CA-M05a-19), avís
de caducitat de la targeta guardada (CA-M05a-20; VC-48) i invitació als qui paguen cada vegada
(CA-M05a-21; RN-M05a-22). Proveïdor fals, sense xarxa; només dades inventades."""

from dataclasses import replace
from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.security import AREA_PERSONAL
from apps.core.models import AuditEntry, LegalText, OutgoingEmail
from apps.members.tests.test_cards import make_member
from apps.payments import campaigns, cards
from apps.payments.models import FeePaymentPreference, MandateCampaignRecipient
from apps.payments.providers import fake
from apps.payments.tests.test_fee_method import active_account
from apps.payments.tests.test_preferences import card, prefer

pytestmark = pytest.mark.django_db
NOTICE = "targeta-caduca"


@pytest.fixture
def member():
    member = make_member()
    member.person.contact_email = "anna.prova@example.org"
    member.person.save()
    return member


@pytest.fixture
def account(member):
    return active_account(member.person, "anna.prova@example.org")


# --- CA-M05a-19 ---


def test_ca_m05a_19_the_recommended_method_follows_the_provider(login_as, account, monkeypatch):
    browser = login_as(account, AREA_PERSONAL)
    html = browser.get(reverse("payments:fee_method")).content.decode()
    assert "Targeta guardada (recomanada)" in html
    assert 'value="direct_debit"' in html and 'value="pay_each_time"' in html

    original = fake.FakeProvider.capabilities
    monkeypatch.setattr(
        fake.FakeProvider, "capabilities", lambda self: replace(original(self), tokenization=False)
    )
    html = browser.get(reverse("payments:fee_method")).content.decode()
    assert "Domiciliació bancària (recomanada)" in html and 'value="saved_card"' not in html
    assert not FeePaymentPreference.objects.exists()  # recomanar no canvia el mètode de ningú


# --- CA-M05a-20 ---


def notices():
    return OutgoingEmail.objects.filter(template=NOTICE)


def test_ca_m05a_20_one_notice_when_the_card_expires_within_the_setting(member):
    saved = card(member, expiry_month=12, expiry_year=2026)  # caduca el 31/12/2026

    assert cards.send_expiry_notices(date(2026, 11, 30)) == 0  # 31 dies: encara no (30)
    assert cards.send_expiry_notices(date(2026, 12, 2)) == 1
    assert cards.send_expiry_notices(date(2026, 12, 3)) == 0  # un sol avís

    email = notices().get()
    assert email.to_address == "anna.prova@example.org"
    assert "… 4242" in email.body_text and "12/2026" in email.body_text
    assert "/socis/pagaments/targeta/" in email.body_text
    assert saved.provider_card_id not in email.body_text
    assert AuditEntry.objects.filter(action=cards.EXPIRY_NOTICE).count() == 1


def test_no_notice_for_an_expired_removed_or_undated_card(member):
    card(member, provider_card_id="c-1", expiry_month=10, expiry_year=2026, status="removed")
    card(member, provider_card_id="c-2", expiry_month=10, expiry_year=2026, status="expired")
    other = make_member(first="Pau", number=1288, document="87654321X")
    card(other, provider_card_id="c-3")  # sense caducitat

    assert cards.send_expiry_notices(date(2026, 10, 15)) == 0
    assert not notices().exists()


# --- CA-M05a-21 ---


@pytest.fixture
def campaign(settings, account):
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    LegalText.objects.create(kind=campaigns.INVITATION_TEXT, version=1, content="Text de prova.")
    return campaigns.open_campaign("Campanya de prova", by=account)


def test_ca_m05a_21_who_pays_each_time_gets_the_invitation_once_and_keeps_the_method(
    campaign, member, account
):
    prefer(member, account, "pay_each_time")
    assert [m for m, _ in campaigns.to_invite_each_time(campaign)] == [member]

    assert campaigns.send_each_time_invitations(campaign, by=account) == 1
    assert campaigns.send_each_time_invitations(campaign, by=account) == 0

    assert OutgoingEmail.objects.filter(template=campaigns.INVITATION_TEMPLATE).count() == 1
    assert MandateCampaignRecipient.objects.get().member == member
    assert FeePaymentPreference.objects.get(member=member).method == "pay_each_time"
    assert campaigns.send_due_reminders(date(2030, 1, 1)) == 0  # no és obligatori respondre-hi


def test_the_each_time_invitation_does_not_reach_members_with_another_method(
    campaign, member, account
):
    prefer(member, account, "saved_card", saved_card=card(member))
    assert campaigns.to_invite_each_time(campaign) == []
