"""Remesa: selecció, previsualització i confirmació (T-M05b-09; CA-M05b-12, 13 i 16; RN-M05b-10
i 11). Només dades inventades: IBAN de format vàlid amb un compte de zeros."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import audit, business_settings, charges
from apps.core.models import AuditEntry, Charge, LegalText, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.models import AnnualFee
from apps.members.tests.test_cards import make_member
from apps.payments import attempts, mandates, remittances
from apps.payments.models import (
    DirectDebitItem,
    DirectDebitRemittance,
    PaymentAttempt,
    SepaMandate,
)
from apps.payments.providers.base import LIVE, LiveChargesNotAllowed
from apps.payments.tests.test_preferences import prefer
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(Role.Code.TREASURER)


@pytest.fixture
def text():
    return LegalText.objects.create(kind="sepa_mandate", version=1, content="Text de prova.")


@pytest.fixture
def signer(text):
    holder = make_member(first="Signant", number=9999, document="99999999R")
    return Account.objects.create_personal(holder.person, "signant@example.org", PASSWORD)


def iban(n):
    """IBAN espanyol inventat amb els dígits de control correctes (compte de zeros)."""
    bban = f"{n:020d}"
    check = 98 - int(bban + "142800") % 97
    return f"ES{check:02d}{bban}"


def due_today():
    return timezone.localdate()


def new_fee(member, cents=9000, due_on=None, period=2026):
    charge = charges.create_charge(
        member.person,
        kind=Charge.Kind.FEE,
        amount_cents=cents,
        concept="Quota",
        origin="members",
        by=audit.system("proves"),
    )
    return AnnualFee.objects.create(
        member=member,
        period=period,
        kind=AnnualFee.Kind.ANNUAL,
        charge=charge,
        due_on=due_on or due_today(),
    )


def new_member(n, *, mandate=True, debit=True, signer=None, text=None, cents=9000):
    member = make_member(first=f"Soci{n}", number=n, document=f"{n:08d}{LETTERS[n % 23]}")
    if mandate:
        signed = mandates.create_mandate(
            member,
            iban=iban(n),
            holder_name="Titular Prova",
            holder_is_member=True,
            legal_text=text,
            account=signer,
            creditor_identifier="ES00ZZZ00000000",
            evidence={"channel": "web"},
        )
        if debit:
            prefer(member, signer, "direct_debit", mandate=signed)
    return new_fee(member, cents)


def collection_date():
    return remittances.earliest_collection_date()


def test_ca_m05b_12_previsualitzacio_amb_130_rebuts_i_20_exclosos(signer, text):
    for n in range(1, 91):
        new_member(n, signer=signer, text=text, cents=3500)
    for n in range(91, 131):
        new_member(n, signer=signer, text=text, cents=9000)
    for n in range(131, 151):
        new_member(n, mandate=False, signer=signer, text=text)

    selection = remittances.preview(collection_date())

    assert len(selection.included) == 130
    assert selection.total_cents == 675_000
    assert len(selection.excluded) == 20
    assert {str(reason) for _fee, reason in selection.excluded} == {"Sense mandat actiu"}
    assert not DirectDebitRemittance.objects.exists()


def test_motius_d_exclusio(signer, text):
    included = new_member(1, signer=signer, text=text)
    no_mandate = new_member(2, mandate=False)
    each_time = new_member(3, debit=False, signer=signer, text=text)
    busy = new_member(4, signer=signer, text=text)
    attempts.create_attempt(busy.charge, "card")
    attempts.transition(
        busy.charge.attempts.get(), PaymentAttempt.Status.IN_PROGRESS, by=audit.system("proves")
    )
    revoked = new_member(5, signer=signer, text=text)
    mandates.revoke_mandate(revoked.member, by=signer)
    new_fee(
        included.member, due_on=collection_date() + timedelta(days=1), period=2027
    )  # encara no venç
    cancelled = new_fee(included.member, period=2025)
    charges.cancel(cancelled.charge, "Prova", by=audit.system("proves"))

    selection = remittances.preview(collection_date())

    assert [fee for fee, _m in selection.included] == [included]
    assert {fee: str(reason) for fee, reason in selection.excluded} == {
        no_mandate: "Sense mandat actiu",
        each_time: "No ha triat la domiciliació",
        busy: "Té un pagament en curs o en una altra remesa",
        revoked: "Sense mandat actiu",
    }


def test_confirmar_crea_la_remesa_els_rebuts_i_els_intents(signer, text, treasurer):
    first = new_member(1, signer=signer, text=text, cents=3500)
    second = new_member(2, signer=signer, text=text)
    new_member(3, mandate=False)

    remittance = remittances.build_remittance("2026-12", collection_date(), treasurer)

    assert (remittance.status, remittance.item_count, remittance.total_cents) == ("draft", 2, 12500)
    items = DirectDebitItem.objects.filter(remittance=remittance).order_by("amount_cents")
    assert [i.attempt.charge_id for i in items] == [first.charge_id, second.charge_id]
    for item in items:
        assert item.attempt.method == PaymentAttempt.Method.DIRECT_DEBIT
        assert item.attempt.status == PaymentAttempt.Status.SENT_TO_BANK
        assert item.mandate.status == SepaMandate.Status.ACTIVE
        assert item.amount_cents == item.attempt.charge.amount_cents
        assert (item.attempt_number, item.prenotified_at) == (1, None)
        assert len(item.end_to_end_id) <= 35
    entry = AuditEntry.objects.get(action="payments.remittance.created")
    assert entry.actor_account == treasurer
    assert iban(1)[-8:] not in str(entry.details)  # cap IBAN al registre

    # RN-M05b-10: una quota no pot ser en dues remeses obertes.
    with pytest.raises(remittances.EmptyRemittance):
        remittances.build_remittance("2026-12", collection_date(), treasurer)
    assert DirectDebitRemittance.objects.count() == 1


def test_ca_m05b_13_data_massa_propera_per_a_l_avis_previ(signer, text, treasurer):
    new_member(1, signer=signer, text=text)
    assert business_settings.get(remittances.PRENOTIFICATION_DAYS) == 14

    with pytest.raises(remittances.PrenotificationTooLate):
        remittances.build_remittance("2026-12", due_today() + timedelta(days=13), treasurer)

    assert not DirectDebitRemittance.objects.exists()
    assert not PaymentAttempt.objects.exists()
    remittances.build_remittance("2026-12", due_today() + timedelta(days=14), treasurer)


def test_ca_m05b_16_amb_el_nivell_1_no_es_genera_cap_remesa(signer, text, treasurer, settings):
    new_member(1, signer=signer, text=text)
    settings.PAYMENTS_ENVIRONMENT = LIVE
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False

    with pytest.raises(LiveChargesNotAllowed):
        remittances.build_remittance("2026-12", collection_date(), treasurer)

    assert not DirectDebitRemittance.objects.exists()
    assert not PaymentAttempt.objects.exists()


def test_sense_cap_quota_no_es_crea_cap_remesa(treasurer):
    with pytest.raises(remittances.EmptyRemittance):
        remittances.build_remittance("2026-12", collection_date(), treasurer)
