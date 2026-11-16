"""Mètode de pagament de la quota, targeta guardada i campanya: els models (T-M05a-08, segona
part; M05a-6; RN-M05a-01 i 10; P-134). Només dades inventades."""

import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.payments.models import (
    FeePaymentPreference,
    MandateCampaign,
    MandateCampaignRecipient,
    SavedCard,
    SepaMandate,
)
from apps.payments.tests import test_mandates

pytestmark = pytest.mark.django_db
# Les mateixes fixtures que les proves del mandat.
member, account, text, sign = (
    test_mandates.member,
    test_mandates.account,
    test_mandates.text,
    test_mandates.sign,
)


def card(member, **fields):
    return SavedCard.objects.create(
        person=member.person,
        provider_code="fake",
        provider_card_id=fields.pop("provider_card_id", "c-1"),
        last4=fields.pop("last4", "4242"),
        **fields,
    )


def prefer(member, account, method, **fields):
    return FeePaymentPreference.objects.create(
        member=member, method=method, set_by=account, **fields
    )


@pytest.mark.parametrize("method", ["direct_debit", "saved_card", "xec"])
def test_domiciliacio_exigeix_mandat_i_targeta_guardada_exigeix_targeta(member, account, method):
    with pytest.raises(IntegrityError), transaction.atomic():
        prefer(member, account, method)


def test_una_preferencia_per_soci_amb_el_seu_mandat_o_targeta(sign, member, account):
    mandate = sign()
    preference = prefer(member, account, "direct_debit", mandate=mandate)
    assert str(preference) == "direct_debit"
    with pytest.raises(IntegrityError), transaction.atomic():
        prefer(member, account, "pay_each_time")
    preference.method, preference.mandate, preference.saved_card = "saved_card", None, card(member)
    preference.save()


def test_p_134_pagar_cada_vegada_amb_un_mandat_actiu(sign, member, account):
    """Opció per defecte A: el mandat es queda actiu i no es fa servir; cap dada no canvia si la
    resposta és la C."""
    mandate = sign()
    prefer(member, account, "pay_each_time", mandate=mandate)
    mandate.refresh_from_db()
    assert mandate.status == SepaMandate.Status.ACTIVE


@pytest.mark.parametrize(
    "fields",
    [
        {"last4": "4X42"},
        {"last4": "42"},
        {"expiry_month": 13},
        {"expiry_month": 0},
        {"status": "perduda"},
    ],
)
def test_la_targeta_guardada_nomes_desa_el_que_es_mostra(member, fields):
    with pytest.raises(IntegrityError), transaction.atomic():
        card(member, **fields)


def test_una_targeta_per_identificador_del_proveidor(member):
    saved = card(member, expiry_month=12, expiry_year=2030)
    assert str(saved) == "… 4242"
    assert {f.name for f in SavedCard._meta.concrete_fields} == {
        "id",
        "person",
        "provider_code",
        "provider_card_id",
        "last4",
        "expiry_month",
        "expiry_year",
        "status",
        "created_at",
    }
    with pytest.raises(IntegrityError), transaction.atomic():
        card(member, last4="0000")


def test_destinatari_de_la_campanya(member, account, text):
    campaign = MandateCampaign.objects.create(
        name="Campanya de prova", opened_by=account, invitation_text=text
    )
    recipient = MandateCampaignRecipient.objects.create(
        campaign=campaign, member=member, invited_at=timezone.now()
    )
    assert str(campaign) == "Campanya de prova"
    assert str(recipient) == f"{campaign.pk}/{member.pk}"
    with pytest.raises(IntegrityError), transaction.atomic():
        MandateCampaignRecipient.objects.filter(pk=recipient.pk).update(answer="direct_debit")
    with pytest.raises(IntegrityError), transaction.atomic():
        MandateCampaignRecipient.objects.create(
            campaign=campaign, member=member, invited_at=timezone.now()
        )
    recipient.answer, recipient.answered_at = "pay_each_time", timezone.now()
    recipient.save()
    assert list(campaign.recipients.all()) == [recipient]
