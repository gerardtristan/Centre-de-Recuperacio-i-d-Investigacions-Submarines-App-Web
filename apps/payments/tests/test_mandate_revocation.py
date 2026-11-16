"""Canviar l'IBAN i revocar el mandat (T-M05a-10; P-M05a-C; RN-M05a-02 i 12; CA-M05a-08; P-127).
Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.models import Account, FailedLogin
from apps.accounts.tests.test_reauth import NOT_IT
from apps.core.models import AuditEntry
from apps.members.tests.test_cards import make_member
from apps.payments import mandates
from apps.payments.models import FeePaymentPreference, SepaMandate
from apps.payments.tests.test_mandate_signing import (  # noqa: F401
    CREDITOR,
    IBAN,
    URL,
    account,
    age_session,
    browser,
    member,
    sign,
    signing_on,
    text,
)
from apps.payments.tests.test_preferences import card, prefer
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

REVOKE = reverse("payments:mandate_revoke")
S = SepaMandate.Status
OTHER_IBAN = "ES2800000000000000000002"


@pytest.fixture
def mandate(member, account, text):  # noqa: F811
    mandate = mandates.create_mandate(
        member,
        iban=IBAN,
        holder_name="Anna Prova",
        holder_is_member=True,
        legal_text=text,
        account=account,
        creditor_identifier=CREDITOR,
        evidence={"channel": "web", "text_version": text.version},
    )
    prefer(member, account, "direct_debit", mandate=mandate)
    return mandate


def reloaded(mandate):
    mandate.refresh_from_db()
    return mandate


class TestRevoke:
    def test_p_m05a_c_revoking_keeps_date_reason_and_who_and_switches_to_pay_each_time(
        self,
        browser,  # noqa: F811
        mandate,
        account,  # noqa: F811
    ):
        page = browser.get(REVOKE).content.decode()
        assert mandate.reference in page and "ES … 0001" in page and IBAN[4:] not in page
        assert 'name="password"' not in page  # sessió recent

        response = browser.post(REVOKE)
        assert response.status_code == 302 and response.url == URL
        mandate = reloaded(mandate)
        assert mandate.status == S.REVOKED and mandate.revoked_at is not None
        assert (mandate.revoked_reason, mandate.revoked_by) == (mandates.MEMBER_REQUEST, account)
        assert FeePaymentPreference.objects.get().method == "pay_each_time"
        entry = AuditEntry.objects.get(action="payments.mandate.revoked")
        assert entry.reason == mandates.MEMBER_REQUEST
        assert entry.details == {"reference": mandate.reference}
        page = browser.get(URL).content.decode()
        assert "revocat" in page and "Revoca el mandat" not in page

    def test_ca_m05a_08_an_old_session_must_type_the_password(self, browser, mandate, account):  # noqa: F811
        age_session(browser, 16)
        assert 'name="password"' in browser.get(REVOKE).content.decode()
        browser.post(REVOKE, {"password": NOT_IT})
        assert reloaded(mandate).status == S.ACTIVE
        assert FailedLogin.objects.filter(account=account).count() == 1
        browser.post(REVOKE, {"password": PASSWORD})
        assert reloaded(mandate).status == S.REVOKED

    def test_p_127_revoking_works_with_signing_switched_off(self, browser, mandate, settings):  # noqa: F811
        settings.MANDATE_SIGNING_ENABLED = False
        page = browser.get(URL).content.decode()
        assert mandate.reference in page and "Revoca el mandat" in page
        assert "Canvia l" not in page and 'name="iban"' not in page
        response = browser.post(REVOKE)
        assert response.url == reverse("payments:fee_method")
        assert reloaded(mandate).status == S.REVOKED
        # Sense cap mandat actiu, la pàgina torna a no existir.
        assert browser.get(URL).status_code == 404

    def test_a_saved_card_preference_does_not_change(self, browser, mandate, member, account):  # noqa: F811
        FeePaymentPreference.objects.all().delete()
        prefer(member, account, "saved_card", saved_card=card(member))
        browser.post(REVOKE)
        assert reloaded(mandate).status == S.REVOKED
        assert FeePaymentPreference.objects.get().method == "saved_card"

    def test_only_the_own_mandate_is_revoked(self, login_as, mandate):  # noqa: F811
        other = make_member("Pere", number=1288, document="00000001R")
        other_account = Account.objects.create_personal(other.person, "pere@example.org", PASSWORD)
        other_account.status = Account.Status.ACTIVE
        other_account.save()
        client = login_as(other_account, "personal")
        assert client.post(REVOKE).status_code == 302
        assert reloaded(mandate).status == S.ACTIVE

    def test_without_an_active_mandate_there_is_nothing_to_confirm(self, browser, text):  # noqa: F811
        assert browser.get(REVOKE).url == URL
        assert not AuditEntry.objects.filter(action="payments.mandate.revoked").exists()


class TestChangeIban:
    def test_the_form_only_shows_when_asked_and_signing_replaces_the_mandate(
        self,
        browser,  # noqa: F811
        mandate,
    ):
        assert 'name="iban"' not in browser.get(URL).content.decode()
        assert 'name="iban"' in browser.get(URL + "?canvia=1").content.decode()

        sign(browser, iban=OTHER_IBAN)
        old, new = SepaMandate.objects.order_by("pk")
        assert (old.status, old.revoked_reason) == (S.REVOKED, SepaMandate.REPLACED)
        assert new.status == S.ACTIVE and new.reference.endswith("M02")
        assert "ES … 0002" in browser.get(URL).content.decode()
