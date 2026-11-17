"""L'esborrat RGPD bloqueja els mandats (T-M05a-17b; L-M05a-06; decisions 044, 028 i 058) i
l'exportació els porta emmascarats. Només dades inventades."""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core import privacy as core_privacy
from apps.core.models import AuditEntry, Role
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.members.tests.test_cards import make_member
from apps.payments import expiry, mandates, preferences
from apps.payments.models import MandateBankAccount, SepaMandate
from apps.payments.tests import test_mandates
from apps.payments.tests.test_preferences import prefer

pytestmark = pytest.mark.django_db
member, account, text, sign = (
    test_mandates.member,
    test_mandates.account,
    test_mandates.text,
    test_mandates.sign,
)
S = SepaMandate.Status


@pytest.fixture
def admin(make_admin):  # noqa: F811
    return make_admin(Role.Code.ADMINISTRATOR)


def erase(person, admin):
    assert core_privacy.blockers(person) == []
    core_privacy.anonymise_person(person, by=admin)


def test_l_m05a_06_l_esborrat_bloqueja_el_mandat_actiu_i_no_esborra_res(
    sign, member, account, admin
):
    mandate = sign()
    prefer(member, account, "direct_debit", mandate=mandate)
    ciphertext = bytes(mandate.bank_account.iban_ciphertext)
    assert preferences.fee_payment_method(member) == "direct_debit"

    erase(member.person, admin)

    mandate.refresh_from_db()
    assert mandate.status == S.BLOCKED
    assert bytes(MandateBankAccount.objects.get(mandate=mandate).iban_ciphertext) == ciphertext
    entry = AuditEntry.objects.get(action="payments.mandate.blocked")
    assert (entry.old_value, entry.new_value, entry.actor_account) == ("active", "blocked", admin)
    assert preferences.fee_payment_method(member) is None


def test_tambe_es_bloquegen_els_revocats_i_els_caducats_sense_perdre_la_revocacio(
    sign, member, admin
):
    revoked = sign()
    expired = sign(iban=test_mandates.OTHER_IBAN)  # revoca l'anterior («substituït»)
    expiry.expire_mandates(today=timezone.localdate() + timedelta(days=4 * 366))
    revoked.refresh_from_db()
    revoked_at = revoked.revoked_at

    erase(member.person, admin)

    revoked.refresh_from_db()
    expired.refresh_from_db()
    assert (revoked.status, expired.status) == (S.BLOCKED, S.BLOCKED)
    assert (revoked.revoked_at, revoked.revoked_reason) == (revoked_at, SepaMandate.REPLACED)
    assert AuditEntry.objects.filter(action="payments.mandate.blocked").count() == 2


def test_un_mandat_bloquejat_no_es_revoca_ni_caduca(sign, member, admin):
    mandate = sign()
    erase(member.person, admin)

    assert mandates.revoke_mandate(member, by=admin) is None
    assert expiry.expire_mandates(today=timezone.localdate() + timedelta(days=4 * 366)) == 0
    mandate.refresh_from_db()
    assert mandate.status == S.BLOCKED


def test_un_soci_sense_mandats_s_esborra_igualment(admin):
    member = make_member("Jordi", number=311, document="00000001R")
    assert not any("mandats" in line for line in core_privacy.describe(member.person))

    erase(member.person, admin)

    member.person.refresh_from_db()
    assert member.person.anonymous_ref
    assert not AuditEntry.objects.filter(action="payments.mandate.blocked").exists()


def test_el_resum_de_l_esborrat_ho_diu(sign, member):
    sign()
    assert any(
        "mandats de domiciliació es bloquegen" in line
        for line in core_privacy.describe(member.person)
    )


def test_l_exportacio_porta_els_mandats_emmascarats(sign, member, account):
    mandate = sign()
    prefer(member, account, "direct_debit", mandate=mandate)

    data = core_privacy.export_person(member.person)["pagaments"]

    assert data["metode_quota"] == "domiciliació"
    assert data["mandats"][0]["referencia"] == mandate.reference
    assert data["mandats"][0]["compte"] == "ES … 0001"
    assert test_mandates.IBAN[4:] not in str(data)
