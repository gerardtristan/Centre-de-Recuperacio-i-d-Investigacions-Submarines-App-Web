"""Remesa enviada i liquidada a la 04 (T-M05b-11; CA-M05b-17, CA-T16.1; RN-M05b-13, RN-T24).
Només dades inventades."""

from datetime import timedelta

import pytest
from django.http import Http404

from apps.core import imports
from apps.core.models import AuditEntry, Charge, OutgoingEmail, Payment, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import remittances, sepa_xml
from apps.payments.models import DirectDebitItem, PaymentAttempt, Receipt, SepaMandate
from apps.payments.providers.base import LIVE, LiveChargesNotAllowed
from apps.payments.tests.test_remittances import (  # noqa: F401 (fixtures)
    collection_date,
    iban,
    new_member,
    signer,
    text,
)
from apps.treasury import services as treasury
from apps.treasury.models import (
    Movement,
    ProviderSettlement,
    Reconciliation,
    StatementLineState,
    TreasuryAccount,
)
from apps.treasury.settlements import SettlementRejected

pytestmark = pytest.mark.django_db
R = Role.Code


@pytest.fixture(autouse=True)
def club(settings):
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.CLUB_IBAN_TRANSFERENCIES = iban(999)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


@pytest.fixture
def sent(signer, text, treasurer):  # noqa: F811
    """Remesa de 2 rebuts (3500 + 9000), avisada, amb el fitxer descarregat i enviada."""
    new_member(1, signer=signer, text=text, cents=3500)
    new_member(2, signer=signer, text=text)
    remittance = remittances.build_remittance("2026-12", collection_date(), treasurer)
    sepa_xml.remittance_file(remittance, treasurer)
    return remittances.mark_remittance_sent(remittance, file_deleted=True, by=treasurer)


def bank_line(amount, by, day=None):
    """Línia d'un extracte confirmat, sense passar pel senyal."""
    batch = imports.open_confirmed(
        "bank_statement", file_sha256="1" * 64, by=by, counts={"new_count": 1}
    )
    row = {
        "row": 2,
        "result": "new",
        "value_date": day or collection_date(),
        "amount_cents": amount,
        "concept": "ABONO REMESA",
        "balance_cents": None,
    }
    imports.add_lines(batch, [row])
    return imports.statement_lines(batch).get()


def sepa_balance():
    account = TreasuryAccount.objects.get(provider_code=treasury.SEPA_REMITTANCE)
    signed = [
        m.amount_cents if m.direction == "in" else -m.amount_cents for m in account.movements.all()
    ]
    return sum(signed)


def test_ca_t16_1_i_ca_m05b_17_l_abonament_liquida_la_remesa(sent, treasurer):
    line = bank_line(12500, treasurer)
    assert list(remittances.candidate_lines(sent)) == [line]

    remittances.settle_remittance(sent, line, by=treasurer)

    sent.refresh_from_db()
    assert sent.status == "settled"
    items = DirectDebitItem.objects.filter(remittance=sent).select_related("attempt__charge")
    for item in items:
        assert item.status == "collected"
        assert item.attempt.status == PaymentAttempt.Status.PAID
        assert item.attempt.charge.status == Charge.Status.PAID
        payment = Payment.objects.get(charge=item.attempt.charge)
        assert (payment.method, payment.provider_reference) == ("direct_debit", item.end_to_end_id)
        assert Receipt.objects.filter(attempt=item.attempt).exists()
    assert set(
        SepaMandate.objects.filter(status="active").values_list("last_collection_on", flat=True)
    ) == {collection_date()}
    assert OutgoingEmail.objects.filter(template="pagament-confirmat").count() == 2

    settlement = ProviderSettlement.objects.get(provider_code=treasury.SEPA_REMITTANCE)
    assert (settlement.status, settlement.source, settlement.net_cents) == (
        "reconciled",
        "remittance",
        12500,
    )
    assert settlement.items.count() == 2
    assert sepa_balance() == 0  # entra 12.500 i surt 12.500 cap al banc
    assert Movement.objects.filter(kind="transfer", settlement=settlement).count() == 2
    assert StatementLineState.objects.get(statement_line=line).status == "reconciled"
    assert set(Reconciliation.objects.get(statement_line=line).matched_charges.all()) == {
        item.attempt.charge for item in items
    }
    assert not remittances.candidate_lines(sent).exists()
    assert AuditEntry.objects.filter(action="payments.remittance.settled").exists()


def test_amb_comissio_el_net_es_casa_i_la_comissio_va_per_rebut(sent, treasurer):
    line = bank_line(12500 - 260, treasurer)
    assert list(remittances.candidate_lines(sent, fees_cents=260)) == [line]

    remittances.settle_remittance(sent, line, fees_cents=260, by=treasurer)

    fees = Movement.objects.filter(kind="fee")
    assert sum(fee.amount_cents for fee in fees) == 260
    assert {fee.cost_centre.full_name for fee in fees} == {"General / Quotes de socis"}


def test_una_linia_que_no_quadra_no_canvia_res(sent, treasurer):
    line = bank_line(12000, treasurer)
    assert not remittances.candidate_lines(sent).exists()

    with pytest.raises(SettlementRejected):
        remittances.settle_remittance(sent, line, by=treasurer)

    assert not Charge.objects.filter(status=Charge.Status.PAID).exists()
    assert not ProviderSettlement.objects.exists()
    sent.refresh_from_db()
    assert sent.status == "sent_to_bank"


def test_una_linia_anterior_al_cobrament_no_es_proposa(sent, treasurer):
    bank_line(12500, treasurer, day=collection_date() - timedelta(days=1))
    assert not remittances.candidate_lines(sent).exists()


def test_nomes_amb_t4_i_sense_canvis_si_no(sent, treasurer, make_admin):  # noqa: F811
    line = bank_line(12500, treasurer)
    with pytest.raises(Http404):
        remittances.settle_remittance(sent, line, by=make_admin(R.SECRETARY))
    assert not Payment.objects.exists()


def test_enviar_demana_el_fitxer_i_que_s_hagi_esborrat(signer, text, treasurer):  # noqa: F811
    new_member(1, signer=signer, text=text)
    remittance = remittances.build_remittance("2026-12", collection_date(), treasurer)
    with pytest.raises(remittances.WrongStatus):  # sense fitxer descarregat
        remittances.mark_remittance_sent(remittance, file_deleted=True, by=treasurer)
    sepa_xml.remittance_file(remittance, treasurer)
    with pytest.raises(remittances.WrongStatus):  # sense confirmar l'esborrat
        remittances.mark_remittance_sent(remittance, file_deleted=False, by=treasurer)
    with pytest.raises(remittances.WrongStatus):  # encara no és enviada
        remittances.settle_remittance(remittance, bank_line(9000, treasurer), by=treasurer)


def test_amb_el_nivell_1_no_es_liquida(sent, treasurer, settings):
    line = bank_line(12500, treasurer)
    settings.PAYMENTS_ENVIRONMENT = LIVE
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False
    with pytest.raises(LiveChargesNotAllowed):
        remittances.settle_remittance(sent, line, by=treasurer)
