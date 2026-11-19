"""Esborrar la targeta guardada (T-M05a-12c; P-132, opció A: com revocar el mandat; RN-M05a-12).
Proveïdor fals (092). Només dades inventades."""

import pytest
from django.urls import reverse

from apps.accounts.models import Account, FailedLogin
from apps.accounts.tests.test_reauth import NOT_IT
from apps.core.models import AuditEntry
from apps.members.tests.test_cards import make_member
from apps.payments import cards
from apps.payments.models import FeePaymentPreference, SavedCard
from apps.payments.tests.test_mandate_signing import age_session
from apps.payments.tests.test_preferences import card, prefer
from apps.payments.tests.test_saved_card import account, browser, clean_orders, member  # noqa: F401
from conftest import PASSWORD

pytestmark = pytest.mark.django_db
REMOVE = reverse("payments:saved_card_remove")
FEE_METHOD = reverse("payments:fee_method")
S = SavedCard.Status


@pytest.fixture
def saved(member, account):  # noqa: F811
    saved = card(member, last4="4821", provider_card_id="ref-opaca-proveidor")
    prefer(member, account, "saved_card", saved_card=saved)
    return saved


def status(saved):
    saved.refresh_from_db()
    return saved.status


def test_removing_marks_it_removed_and_switches_to_pay_each_time(browser, saved, account):  # noqa: F811
    page = browser.get(REMOVE).content.decode()
    assert "4821" in page and "ref-opaca-proveidor" not in page  # mai la referència del proveïdor
    assert 'name="password"' not in page  # sessió recent
    response = browser.post(REMOVE)
    assert response.status_code == 302 and response.url == FEE_METHOD
    assert status(saved) == S.REMOVED
    assert FeePaymentPreference.objects.get().method == "pay_each_time"
    entry = AuditEntry.objects.get(action=cards.REMOVED)
    assert entry.actor_account == account
    assert "ref-opaca-proveidor" not in str(entry.details)
    assert "4821" in browser.get(FEE_METHOD).content.decode()  # el missatge


def test_an_old_session_must_type_the_password(browser, saved, account):  # noqa: F811
    age_session(browser, 16)
    assert 'name="password"' in browser.get(REMOVE).content.decode()
    browser.post(REMOVE, {"password": NOT_IT})
    assert status(saved) == S.ACTIVE
    assert FailedLogin.objects.filter(account=account).count() == 1
    browser.post(REMOVE, {"password": PASSWORD})
    assert status(saved) == S.REMOVED


def test_a_direct_debit_preference_does_not_change(browser, member, account):  # noqa: F811
    saved = card(member)
    FeePaymentPreference.objects.create(member=member, method="pay_each_time", set_by=account)
    browser.post(REMOVE)
    assert status(saved) == S.REMOVED
    assert FeePaymentPreference.objects.get().method == "pay_each_time"


def test_it_works_when_the_provider_no_longer_saves_cards(browser, saved, monkeypatch):  # noqa: F811
    monkeypatch.setattr(
        "apps.payments.preferences.offered_methods", lambda: ["direct_debit", "pay_each_time"]
    )
    assert browser.get(reverse("payments:saved_card")).status_code == 404
    browser.post(REMOVE)
    assert status(saved) == S.REMOVED


def test_only_the_own_card(login_as, saved):
    other = make_member("Pere", number=1288, document="00000001R")
    other_account = Account.objects.create_personal(other.person, "pere@example.org", PASSWORD)
    other_account.status = Account.Status.ACTIVE
    other_account.save()
    client = login_as(other_account, "personal")
    assert client.post(REMOVE).url == FEE_METHOD  # no en té cap: res a esborrar
    assert status(saved) == S.ACTIVE


def test_the_service_refuses_anyone_else(saved, member):  # noqa: F811
    from django.http import Http404

    with pytest.raises(Http404):
        cards.remove_card(member, by=None)
    assert status(saved) == S.ACTIVE


def test_without_an_active_card_there_is_nothing_to_confirm(browser):  # noqa: F811
    assert browser.get(REMOVE).url == FEE_METHOD
    assert not AuditEntry.objects.filter(action=cards.REMOVED).exists()


def test_the_card_page_links_to_removing(browser, saved):  # noqa: F811
    assert REMOVE in browser.get(reverse("payments:saved_card")).content.decode()
