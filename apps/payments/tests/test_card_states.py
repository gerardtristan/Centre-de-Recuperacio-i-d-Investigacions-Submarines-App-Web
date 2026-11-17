"""Estats de la targeta guardada (T-M05a-26; RN-M05a-23; CA-M05a-22): `expired` per la caducitat
coneguda i `declined` (RN-M05b-28). Una targeta caducada o denegada no torna a ser activa ni es fa
servir. Proveïdor fals, sense xarxa; només dades inventades."""

from datetime import UTC, date, datetime

import pytest
from django.db import IntegrityError, transaction

from apps.accounts.security import AREA_PERSONAL
from apps.core.models import AuditEntry, OutgoingEmail
from apps.members.tests.test_cards import add_fee, make_member
from apps.payments import cards, checkout
from apps.payments.models import PaymentAttempt, SavedCard
from apps.payments.providers import fake
from apps.payments.tests.test_fee_method import active_account
from apps.payments.tests.test_preferences import card, prefer

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clean_orders(settings):
    settings.PUBLIC_SITE_URL = "https://socis.example.org"
    fake.reset()
    yield
    fake.reset()


@pytest.fixture
def member():
    member = make_member()
    member.person.contact_email = "anna.prova@example.org"
    member.person.save()
    return member


@pytest.fixture
def account(member):
    return active_account(member.person, "anna.prova@example.org")


def test_declined_is_a_valid_state():
    assert "declined" in SavedCard.Status.values


def test_ca_m05a_22_a_card_past_its_expiry_becomes_expired_and_is_not_used(
    member, account, monkeypatch
):
    saved = card(member, expiry_month=3, expiry_year=2026)  # caduca el 31/03/2026
    prefer(member, account, "saved_card", saved_card=saved)
    add_fee(member)  # venç l'1/1/2026: es cobraria avui

    assert cards.expire_cards(date(2026, 3, 31)) == 0  # encara serveix l'últim dia
    assert cards.expire_cards(date(2026, 4, 15)) == 1
    saved.refresh_from_db()
    assert saved.status == "expired"
    entry = AuditEntry.objects.get(action=cards.EXPIRED)
    assert (entry.old_value, entry.new_value) == ("active", "expired")

    monkeypatch.setattr(checkout.timezone, "localdate", lambda *args: date(2026, 4, 15))
    checkout.charge_due_saved_cards()
    assert not PaymentAttempt.objects.exists()


def test_an_expired_or_declined_card_never_becomes_active_again(member):
    for status in ("expired", "declined"):
        saved = card(member, provider_card_id=status, status=status)
        saved.status = "active"
        with pytest.raises(SavedCard.Closed):
            saved.save()
        saved.refresh_from_db()
        assert saved.status == status


def test_the_card_page_says_it_expired_and_offers_a_new_one(login_as, member, account):
    card(member, expiry_month=3, expiry_year=2026, status="expired")
    html = login_as(account, AREA_PERSONAL).get("/socis/pagaments/targeta/").content.decode()

    assert "La teva targeta ha caducat" in html
    assert "Guarda una targeta nova" in html


def test_one_active_card_still_allows_closed_ones(member):
    card(member, provider_card_id="a", status="expired")
    card(member, provider_card_id="b", status="declined")
    card(member, provider_card_id="c")
    with pytest.raises(IntegrityError), transaction.atomic():
        card(member, provider_card_id="d")


@pytest.mark.xfail(reason="T-M05a-26 aturada (17/11/2026): falta caducar a la tasca de cobrament")
def test_ca_m05a_22_the_daily_charge_closes_the_card_and_links_a_new_one(
    member, account, monkeypatch
):
    saved = card(member, expiry_month=3, expiry_year=2026)
    prefer(member, account, "saved_card", saved_card=saved, since=datetime(2025, 12, 1, tzinfo=UTC))
    add_fee(member)
    monkeypatch.setattr(checkout.timezone, "localdate", lambda *args: date(2026, 4, 15))

    checkout.charge_due_saved_cards()  # sense la tasca de les 9:40

    saved.refresh_from_db()
    assert saved.status == "expired" and not PaymentAttempt.objects.exists()
    (email,) = OutgoingEmail.objects.filter(template="alternativa-pagament")
    assert "https://socis.example.org/socis/pagaments/targeta/" in email.body_text
