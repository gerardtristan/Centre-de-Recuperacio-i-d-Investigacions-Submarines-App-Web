"""Campanya de mandats: el darrer recordatori, quan el tresorer fixa la remesa (T-M05a-13c;
RN-M05a-14 i RN-M05a-18; P-M05a-E, pas 4). Només dades inventades."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import campaigns, preferences, remittances
from apps.payments.models import MandateCampaignRecipient
from apps.payments.tests.test_campaigns import (  # noqa: F401 (fixtures)
    anna,
    campaign,
    days_ago,
    emails,
    jordi,
    member_with_email,
    ready,
    treasurer,
)
from apps.payments.tests.test_remittances import collection_date, iban, new_member, signer, text  # noqa: F401

pytestmark = pytest.mark.django_db
FINAL = campaigns.FINAL_REMINDER_TEMPLATE
DAY = timezone.localdate() + timedelta(days=20)


@pytest.fixture
def invited(campaign, treasurer, anna, jordi):  # noqa: F811
    campaigns.send_invitations(campaign, by=treasurer)
    return campaign


def test_only_who_has_not_chosen_gets_it_once(invited, treasurer, anna, jordi):  # noqa: F811
    preferences.set_preference(jordi, "pay_each_time", by=treasurer)
    assert campaigns.send_final_reminders(DAY, by=treasurer) == 1
    assert emails(FINAL) == ["anna.prova@example.org"]
    (email,) = OutgoingEmail.objects.filter(template=FINAL)
    assert (
        DAY.strftime("%d/%m/%Y") in email.body_text and "https://cris1954.cat/" in email.body_text
    )
    entry = AuditEntry.objects.get(action="payments.campaign.final_reminders_sent")
    assert entry.actor_account == treasurer and entry.details["sent"] == 1

    # Una segona remesa a la mateixa campanya: ja era el darrer.
    assert campaigns.send_final_reminders(DAY + timedelta(days=30), by=treasurer) == 0
    assert OutgoingEmail.objects.filter(template=FINAL).count() == 1


def test_after_the_last_one_no_daily_reminder(invited, treasurer, anna):  # noqa: F811
    campaigns.send_final_reminders(DAY, by=treasurer)
    for recipient in MandateCampaignRecipient.objects.all():
        days_ago(recipient, 30)
    assert campaigns.send_due_reminders() == 0


@pytest.mark.parametrize("case", ["closed", "signing_off", "no_campaign"])
def test_nothing_when_it_does_not_apply(case, settings, campaign, treasurer, anna):  # noqa: F811
    if case != "no_campaign":
        campaigns.send_invitations(campaign, by=treasurer)
    if case == "closed":
        campaigns.close_campaign(campaign, by=treasurer)
    if case == "signing_off":
        settings.MANDATE_SIGNING_ENABLED = False
    assert campaigns.send_final_reminders(DAY, by=treasurer) == 0
    assert not OutgoingEmail.objects.filter(template=FINAL).exists()


def test_building_the_remittance_sends_it(invited, signer, text, make_admin):  # noqa: F811
    new_member(5, signer=signer, text=text)  # un rebut perquè la remesa no sigui buida
    remittance = remittances.build_remittance(
        "2026-12", collection_date(), make_admin(Role.Code.TREASURER)
    )
    assert sorted(emails(FINAL)) == ["anna.prova@example.org", "jordi.prova@example.org"]
    body = OutgoingEmail.objects.filter(template=FINAL).first().body_text
    assert remittance.collection_date.strftime("%d/%m/%Y") in body
    assert iban(5)[-8:] not in body and "ES00ZZZ" not in body  # cap dada bancària
