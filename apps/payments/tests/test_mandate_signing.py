"""Signatura del mandat des del compte personal (T-M05a-09; P-M05a-B; CA-M05a-02, 03 i 08;
RN-M05a-12). Només dades inventades: IBAN de format vàlid amb un compte de zeros."""

import logging
import time

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account, FailedLogin
from apps.accounts.security import AREA_PERSONAL
from apps.accounts.sessions import AUTH_AT_SESSION_KEY
from apps.accounts.tests.test_reauth import NOT_IT
from apps.core.models import AuditEntry, LegalText, OutgoingEmail
from apps.members.models import Member
from apps.members.tests.test_cards import make_member
from apps.payments.models import MandateBankAccount, SepaMandate
from conftest import PASSWORD

pytestmark = pytest.mark.django_db

URL = reverse("payments:mandate")
IBAN = "ES5500000000000000000001"
BAD_IBAN = "ES5600000000000000000001"  # un dígit de control canviat
CREDITOR = "ES00ZZZ00000000"


@pytest.fixture(autouse=True)
def signing_on(settings):
    settings.MANDATE_SIGNING_ENABLED = True
    settings.SEPA_CREDITOR_IDENTIFIER = CREDITOR
    settings.MANDATE_REAUTH_MINUTES = 15


@pytest.fixture
def text():
    return LegalText.objects.create(kind="sepa_mandate", version=3, content="Esborrany de prova.")


@pytest.fixture
def member():
    member = make_member()
    member.person.contact_email = "anna.prova@example.org"
    member.person.save()
    return member


@pytest.fixture
def account(member):
    account = Account.objects.create_personal(member.person, "anna.prova@example.org", PASSWORD)
    account.status = Account.Status.ACTIVE
    account.save()
    return account


@pytest.fixture
def browser(login_as, account):
    return login_as(account, AREA_PERSONAL)


def age_session(client, minutes):
    session = client.session
    session[AUTH_AT_SESSION_KEY] = time.time() - minutes * 60
    session.save()


def sign(client, **extra):
    data = {"holder_name": "Anna Prova", "iban": IBAN, "accept": "on", **extra}
    return client.post(URL, data)


class TestAvailability:
    def test_off_by_default_the_route_does_not_exist(self, browser, text, settings):
        settings.MANDATE_SIGNING_ENABLED = False
        assert browser.get(URL).status_code == 404
        assert sign(browser).status_code == 404
        assert not SepaMandate.objects.exists()

    def test_without_creditor_identifier_the_placeholder_shows_and_nothing_is_signed(
        self, browser, text, settings
    ):
        settings.SEPA_CREDITOR_IDENTIFIER = ""
        response = browser.get(URL)
        assert "A verificar: banc (P-45 punt 5)" in response.content.decode()
        sign(browser)
        assert not SepaMandate.objects.exists()

    def test_without_a_published_text_nothing_is_signed(self, browser):
        assert "Encara no es pot signar" in browser.get(URL).content.decode()
        sign(browser)
        assert not SepaMandate.objects.exists()

    @pytest.mark.parametrize("status", [Member.Status.PENDING, Member.Status.LEFT])
    def test_only_an_active_or_unpaid_member_signs(self, browser, member, text, status):
        Member.objects.filter(pk=member.pk).update(status=status)
        assert browser.get(URL).status_code == 404


class TestIban:
    def test_ca_m05a_02_bad_check_digits_are_rejected_and_nothing_keeps_the_iban(
        self, browser, text, caplog
    ):
        caplog.set_level(logging.DEBUG)
        response = sign(browser, iban=BAD_IBAN)
        page = response.content.decode()
        assert response.status_code == 200
        assert "L&#x27;IBAN no és vàlid" in page
        assert not SepaMandate.objects.exists() and not MandateBankAccount.objects.exists()
        digits = BAD_IBAN[4:]
        assert digits not in page and digits not in caplog.text
        assert not any(digits in str(entry.__dict__) for entry in AuditEntry.objects.all())

    def test_a_valid_iban_never_comes_back_when_another_field_fails(self, browser, text):
        page = sign(browser, accept="").content.decode()
        assert IBAN[4:] not in page
        assert not SepaMandate.objects.exists()


class TestSigning:
    def test_ca_m05a_03_signing_keeps_reference_text_version_date_and_account(
        self, browser, text, account
    ):
        response = sign(browser)
        assert response.status_code == 302
        mandate = SepaMandate.objects.get()
        assert mandate.reference == "CRIS001287M01"
        assert mandate.legal_text == text and mandate.signed_by_account == account
        assert mandate.creditor_identifier == CREDITOR and mandate.holder_is_member
        assert mandate.evidence == {"channel": "web", "text_version": 3}
        assert mandate.bank_account.iban_last4 == "0001"
        page = browser.get(URL).content.decode()
        assert "ES … 0001" in page and IBAN[4:] not in page
        assert "CRIS001287M02" in page  # la referència del mandat següent, si canvia l'IBAN

    def test_another_holder_is_declared(self, browser, text):
        sign(browser, holder_name="Pere Prova", other_holder="on")
        assert not SepaMandate.objects.get().holder_is_member


class TestReauthentication:
    def test_a_recent_session_does_not_ask_for_the_password(self, browser, text):
        assert 'name="password"' not in browser.get(URL).content.decode()

    def test_ca_m05a_08_an_old_session_must_type_the_password(self, browser, text, account):
        age_session(browser, 16)
        assert 'name="password"' in browser.get(URL).content.decode()
        sign(browser, password=NOT_IT)
        assert not SepaMandate.objects.exists()
        assert FailedLogin.objects.filter(account=account).count() == 1
        assert sign(browser, password=PASSWORD).status_code == 302
        assert SepaMandate.objects.count() == 1

    def test_a_session_that_aged_after_opening_the_page_is_asked_without_counting_a_failure(
        self, browser, text, account
    ):
        age_session(browser, 16)
        page = sign(browser).content.decode()  # el formulari no portava el camp
        assert "Torna a escriure la contrasenya" in page
        assert not SepaMandate.objects.exists()
        assert not FailedLogin.objects.filter(account=account).exists()

    def test_the_window_is_a_setting(self, browser, text, settings):
        settings.MANDATE_REAUTH_MINUTES = 30
        age_session(browser, 16)
        assert sign(browser).status_code == 302


class TestConfirmationEmail:
    def test_ca_m05a_04_g3_has_reference_creditor_date_and_how_to_revoke_but_not_the_iban(
        self, browser, text
    ):
        sign(browser)
        email = OutgoingEmail.objects.get(template="mandat-signat")
        mandate = SepaMandate.objects.get()
        assert email.to_address == "anna.prova@example.org"
        assert mandate.reference in email.subject
        body = email.body_text
        assert mandate.reference in body and CREDITOR in body
        # El correu porta la data local, no la UTC (entre les 23 i les 24 h UTC canvia).
        assert timezone.localdate(mandate.signed_at).strftime("%d/%m/%Y") in body
        assert "ES … 0001" in body and URL in body
        assert IBAN[4:] not in body + email.subject + email.body_html

    def test_nothing_is_sent_when_the_signature_fails(self, browser, text):
        sign(browser, iban=BAD_IBAN)
        assert not OutgoingEmail.objects.exists()
