"""`campaigns.mandates_signed` per al dashboard (T-M08-05; indicador «Mandats signats»): socis
que han signat un mandat mentre la campanya era oberta. Només dades inventades."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.payments import campaigns
from apps.payments.models import MandateCampaign
from apps.payments.tests import test_mandates

pytestmark = pytest.mark.django_db
member, account, text, sign = (
    test_mandates.member,
    test_mandates.account,
    test_mandates.text,
    test_mandates.sign,
)


def test_counts_members_who_signed_while_the_campaign_was_open(sign, account, text):
    now = timezone.now()

    def a_campaign(opened_at):
        return MandateCampaign.objects.create(
            name="Campanya inventada", opened_by=account, invitation_text=text, opened_at=opened_at
        )

    campaign = a_campaign(now - timedelta(days=1))
    sign()
    sign(iban=test_mandates.OTHER_IBAN)  # el mateix soci el torna a signar: un sol soci
    assert campaigns.mandates_signed(campaign) == 1
    campaign.closed_at = now - timedelta(hours=1)  # tancada abans de signar
    campaign.save()
    assert campaigns.mandates_signed(campaign) == 0
    assert campaigns.mandates_signed(a_campaign(now + timedelta(hours=1))) == 0
