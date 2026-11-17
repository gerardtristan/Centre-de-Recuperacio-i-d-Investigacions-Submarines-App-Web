"""Fitxer pain.008 de la remesa (T-M05b-10; CA-M05b-15; RN-M05b-12). Només dades inventades:
IBAN de format vàlid amb un compte de zeros i un identificador de creditor fictici."""

import hashlib

import pytest
from defusedxml.ElementTree import fromstring

from apps.core.models import AuditEntry, PrivateFile
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import mandates, remittances, sepa_xml
from apps.payments.models import DirectDebitRemittance, SepaMandate
from apps.payments.providers.base import LIVE, LiveChargesNotAllowed
from apps.payments.tests.test_remittances import (  # noqa: F401 (fixtures)
    collection_date,
    iban,
    new_member,
    signer,
    text,
    treasurer,
)

pytestmark = pytest.mark.django_db
NS = {"p": sepa_xml.NAMESPACE}
CREDITOR = "ES00ZZZ00000000"
CLUB = iban(999)


@pytest.fixture(autouse=True)
def club(settings):
    settings.SEPA_CREDITOR_IDENTIFIER = CREDITOR
    settings.CLUB_IBAN_TRANSFERENCIES = CLUB


@pytest.fixture
def remittance(signer, text, treasurer):  # noqa: F811
    new_member(1, signer=signer, text=text, cents=3500)
    new_member(2, signer=signer, text=text)
    return remittances.build_remittance("2026-12", collection_date(), treasurer)


def test_ca_m05b_15_fitxer_valid_amb_empremta_i_registre(remittance, treasurer):  # noqa: F811
    content = sepa_xml.remittance_file(remittance, treasurer)

    sepa_xml.check(content)  # el que el servei ja ha comprovat
    root = fromstring(content)
    assert root.findtext("p:CstmrDrctDbtInitn/p:GrpHdr/p:NbOfTxs", namespaces=NS) == "2"
    assert root.findtext("p:CstmrDrctDbtInitn/p:GrpHdr/p:CtrlSum", namespaces=NS) == "125.00"
    info = root.find("p:CstmrDrctDbtInitn/p:PmtInf", NS)
    assert info.findtext("p:ReqdColltnDt", namespaces=NS) == collection_date().isoformat()
    assert info.findtext("p:CdtrAcct/p:Id/p:IBAN", namespaces=NS) == CLUB
    assert info.findtext("p:CdtrSchmeId/p:Id/p:PrvtId/p:Othr/p:Id", namespaces=NS) == CREDITOR
    debtors = [n.text for n in info.findall("p:DrctDbtTxInf/p:DbtrAcct/p:Id/p:IBAN", NS)]
    assert debtors == [iban(1), iban(2)]
    references = [n.text for n in info.findall(".//p:MndtId", NS)]
    assert references == [
        m.reference for m in SepaMandate.objects.order_by("member__member_number")
    ]

    remittance.refresh_from_db()
    assert remittance.file_hash == hashlib.sha256(content).hexdigest()
    assert remittance.file_format == "pain.008.001.02"
    entry = AuditEntry.objects.get(action="payments.remittance.file_generated")
    assert entry.actor_account == treasurer
    assert entry.details["sha256"] == remittance.file_hash
    assert iban(1) not in str(entry.details) and iban(2) not in str(entry.details)
    assert not PrivateFile.objects.exists()  # no es desa a l'emmagatzematge (RN-M05b-12)


def test_els_noms_es_transliteren_al_joc_de_caracters_sepa():
    assert sepa_xml.sepa_text("Núria Çervera & Pujol·là", 70) == "Nuria Cervera Pujolla"
    assert len(sepa_xml.sepa_text("x" * 100, 70)) == 70


@pytest.mark.parametrize(
    "spoil",
    [
        lambda c: c.replace(b"<CtrlSum>125.00</CtrlSum>", b"<CtrlSum>125.01</CtrlSum>", 1),
        lambda c: c.replace(b"<NbOfTxs>2</NbOfTxs>", b"<NbOfTxs>3</NbOfTxs>", 1),
        lambda c: c.replace(b'Ccy="EUR"', b'Ccy="USD"', 1),
        lambda c: c.replace(iban(1).encode(), ("ES00" + iban(1)[4:]).encode()),  # control
        lambda c: c.replace(b"<Ustrd>Quota</Ustrd>", b"<Ustrd>Quota &amp; extra</Ustrd>", 1),
        lambda c: c[:-20],
    ],
)
def test_la_validacio_atura_un_fitxer_que_no_quadra(remittance, treasurer, spoil):  # noqa: F811
    content = sepa_xml.remittance_file(remittance, treasurer)
    with pytest.raises(sepa_xml.InvalidFile) as error:
        sepa_xml.check(spoil(content))
    assert iban(1) not in str(error.value)


def test_nomes_una_remesa_avisada_te_fitxer(remittance, treasurer):  # noqa: F811
    DirectDebitRemittance.objects.filter(pk=remittance.pk).update(status="draft")
    with pytest.raises(sepa_xml.RemittanceNotReady):
        sepa_xml.remittance_file(remittance, treasurer)


def test_un_mandat_revocat_despres_de_l_avis_atura_el_fitxer(remittance, treasurer, signer):  # noqa: F811
    revoked = SepaMandate.objects.order_by("member__member_number").first()
    mandates.revoke_mandate(revoked.member, by=signer)

    with pytest.raises(sepa_xml.MandateNoLongerActive) as error:
        sepa_xml.remittance_file(remittance, treasurer)

    assert error.value.args == ([revoked.reference],)
    remittance.refresh_from_db()
    assert remittance.file_hash == ""


def test_sense_creditor_o_compte_del_club_no_hi_ha_fitxer(remittance, treasurer, settings):  # noqa: F811
    settings.CLUB_IBAN_TRANSFERENCIES = ""
    with pytest.raises(sepa_xml.NotConfigured):
        sepa_xml.remittance_file(remittance, treasurer)


def test_amb_el_nivell_1_no_hi_ha_fitxer(remittance, treasurer, settings):  # noqa: F811
    settings.PAYMENTS_ENVIRONMENT = LIVE
    settings.PAYMENTS_LIVE_CHARGES_ALLOWED = False
    with pytest.raises(LiveChargesNotAllowed):
        sepa_xml.remittance_file(remittance, treasurer)
