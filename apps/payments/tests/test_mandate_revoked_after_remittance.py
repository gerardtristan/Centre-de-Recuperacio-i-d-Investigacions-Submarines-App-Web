"""Revocar un mandat amb un rebut en una remesa que ja pot ser al banc (T-M05a-10b; RN-M05a-09;
L-M05a-04 i L-M05b-03): el banc el presentarà igualment, i el tresorer ho ha de saber. Només
dades inventades."""

import pytest

from apps.core.models import AuditEntry, OutgoingEmail, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import mandates, remittances, sepa_xml
from apps.payments.models import DirectDebitRemittance
from apps.payments.tests.test_remittances import (  # noqa: F401 (fixtures)
    collection_date,
    iban,
    new_member,
    signer,
    text,
)

pytestmark = pytest.mark.django_db
R = Role.Code
NOTICE = mandates.REVOKED_IN_REMITTANCE_TEMPLATE
REASON = "Correu del soci demanant la baixa de la domiciliació."


@pytest.fixture(autouse=True)
def club(settings):
    settings.SEPA_CREDITOR_IDENTIFIER = "ES00ZZZ00000000"
    settings.CLUB_IBAN_TRANSFERENCIES = iban(999)


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    account = make_admin(R.TREASURER)
    account.notification_email = "tresoreria@example.org"
    account.save()
    return account


@pytest.fixture
def built(signer, text, treasurer):  # noqa: F811
    """Remesa de dos rebuts, avisada (encara sense fitxer)."""
    first = new_member(1, signer=signer, text=text)
    new_member(2, signer=signer, text=text)
    remittance = remittances.build_remittance("2026-12", collection_date(), treasurer)
    return remittance, first.member


def send(remittance, treasurer):
    sepa_xml.remittance_file(remittance, treasurer)
    return remittances.mark_remittance_sent(remittance, file_deleted=True, by=treasurer)


def test_revoking_after_the_remittance_was_sent_warns_the_treasurer_once(
    built,
    treasurer,
    make_admin,  # noqa: F811
):
    remittance, member = built
    send(remittance, treasurer)
    make_admin(R.SECRETARY)  # sense T1: no rep res
    mandate = mandates.revoke_mandate(member, by=treasurer, reason=REASON)

    (email,) = OutgoingEmail.objects.filter(template=NOTICE)
    assert email.to_address == "tresoreria@example.org"
    body = email.body_text + email.subject
    assert mandate.reference in body and "2026-12" in body
    assert iban(1)[-8:] not in body and "…" not in body  # cap IBAN, ni emmascarat (P-121)
    assert "Soci1" not in body  # cap nom
    entry = AuditEntry.objects.get(action=mandates.REVOKED_IN_REMITTANCE)
    assert entry.actor_account == treasurer and entry.target_id == str(mandate.pk)
    assert entry.details == {"reference": mandate.reference, "remittances": [remittance.pk]}

    # Un mandat només es revoca una vegada: cap segon avís.
    assert mandates.revoke_mandate(member, by=treasurer, reason=REASON) is None
    assert OutgoingEmail.objects.filter(template=NOTICE).count() == 1


def test_the_file_already_downloaded_counts_as_possibly_at_the_bank(built, treasurer):
    remittance, member = built
    sepa_xml.remittance_file(remittance, treasurer)  # avisada amb el fitxer descarregat
    mandates.revoke_mandate(member, by=treasurer, reason=REASON)
    assert OutgoingEmail.objects.filter(template=NOTICE).count() == 1


@pytest.mark.parametrize("status", ["notified", "settled", "cancelled"])
def test_no_notice_when_the_bank_does_not_have_it(built, treasurer, status):
    # Avisada sense fitxer: el fitxer no es podrà generar amb el mandat revocat (sepa_xml).
    remittance, member = built
    DirectDebitRemittance.objects.filter(pk=remittance.pk).update(status=status)
    mandates.revoke_mandate(member, by=treasurer, reason=REASON)
    assert not OutgoingEmail.objects.filter(template=NOTICE).exists()
    assert not AuditEntry.objects.filter(action=mandates.REVOKED_IN_REMITTANCE).exists()


def test_no_notice_without_any_remittance(signer, text, treasurer):  # noqa: F811
    member = new_member(3, signer=signer, text=text).member
    mandates.revoke_mandate(member, by=treasurer, reason=REASON)
    assert not OutgoingEmail.objects.filter(template=NOTICE).exists()


def test_another_members_revocation_does_not_warn(built, signer, text, treasurer):  # noqa: F811
    remittance, _member = built
    send(remittance, treasurer)
    other = new_member(4, signer=signer, text=text).member  # no és a la remesa
    mandates.revoke_mandate(other, by=treasurer, reason=REASON)
    assert not OutgoingEmail.objects.filter(template=NOTICE).exists()
