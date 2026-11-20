"""P-406 (propietari, 20/11/2026): la quota que la targeta guardada no cobra, sense intent, surt a
la llista «a revisar» de Pagaments (B6) i el tresorer la dona per revisada amb una nota, que afegeix
una entrada al registre. Proveïdor fals; només dades inventades."""

# ruff: noqa: F811

import pytest
from django.http import Http404
from django.urls import reverse

from apps.core import business_settings
from apps.core import privacy as core_privacy
from apps.core.models import AuditEntry, Charge, Role
from apps.payments import checkout, reviews
from apps.payments.providers import switch_key
from apps.payments.tests.test_payments_list import MANAGEMENT_ROLES, WITH_B6, html
from apps.payments.tests.test_saved_card_charge import (  # noqa: F401 (fixtures)
    clean_orders,
    fee,
    make_admin,
    member,
    saved,
)
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
R = Role.Code
NOTE = "El soci pagarà amb l'enllaç (prova)"
REASON = "El club ha aturat el cobrament amb la targeta guardada."


@pytest.fixture
def treasurer(make_admin):
    return make_admin(R.TREASURER, username="teresa.tresorera")


@pytest.fixture
def switched_off(make_admin):
    admin = make_admin(R.ADMINISTRATOR, username="anna.admin")
    business_settings.change(switch_key("tokenization"), False, admin, "Aturada (prova)")


def close_url(entry):
    return reverse("administration:payments_charge_review_close", args=[entry.pk])


def test_switched_off_the_fee_is_listed_once(saved, fee, switched_off, treasurer):
    checkout.charge_due_saved_cards()
    checkout.charge_due_saved_cards()
    [entry] = reviews.open_charge_reviews()
    page = html(client_for(treasurer))
    assert page.count(REASON) == 1
    assert close_url(entry) in page
    assert "90,00" in page and str(fee.charge.pk) in page


def test_switched_on_nothing_is_listed(saved, fee, treasurer):
    checkout.charge_due_saved_cards()
    assert not reviews.open_charge_reviews().exists()
    assert REASON not in html(client_for(treasurer))


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_only_b6_sees_and_closes_it(saved, fee, switched_off, make_admin, role):
    checkout.charge_due_saved_cards()
    [entry] = reviews.open_charge_reviews()
    client = client_for(make_admin(role, username=f"prova.{role}"))
    allowed = role in WITH_B6
    listed = client.get(reverse("administration:payments_list"))
    assert listed.status_code == (200 if allowed else 404)
    assert client.get(close_url(entry)).status_code == (200 if allowed else 404)
    response = client.post(close_url(entry), {"note": NOTE})
    assert response.status_code == (302 if allowed else 404)
    assert reviews.open_charge_reviews().exists() != allowed


def test_closing_adds_an_entry_and_takes_it_off_the_list(saved, fee, switched_off, treasurer):
    checkout.charge_due_saved_cards()
    [entry] = reviews.open_charge_reviews()
    before = AuditEntry.objects.count()
    client = client_for(treasurer)

    response = client.post(close_url(entry), {"note": NOTE})

    assert response.status_code == 302
    assert not reviews.open_charge_reviews().exists()
    assert REASON not in html(client)
    closed = AuditEntry.objects.get(action=reviews.CHARGE_CLOSED)
    assert (closed.target_id, closed.reason) == (str(entry.pk), NOTE)
    assert closed.details == {"charge": fee.charge.pk}
    assert AuditEntry.objects.filter(pk=entry.pk, reason__startswith=REASON).exists()  # intacta
    assert AuditEntry.objects.count() == before + 1
    fee.charge.refresh_from_db()
    assert fee.charge.status == Charge.Status.PENDING  # cap diner ni cap canvi del càrrec
    assert client.get(close_url(entry)).status_code == 404  # ja tancada
    with pytest.raises(reviews.NotClosable):
        reviews.close_charge_review(entry, note=NOTE, by=treasurer)


def test_a_note_is_required(saved, fee, switched_off, treasurer):
    checkout.charge_due_saved_cards()
    [entry] = reviews.open_charge_reviews()
    response = client_for(treasurer).post(close_url(entry), {"note": "  "})
    assert response.status_code == 200
    assert "Cal una nota per tancar-lo." in response.content.decode()
    assert reviews.open_charge_reviews().exists()
    with pytest.raises(ValueError):
        reviews.close_charge_review(entry, note=" ", by=treasurer)


def test_the_service_checks_the_permission(saved, fee, switched_off, make_admin):
    checkout.charge_due_saved_cards()
    [entry] = reviews.open_charge_reviews()
    with pytest.raises(Http404):
        reviews.close_charge_review(entry, note=NOTE, by=make_admin(R.SECRETARY))


def test_the_erasure_targets_the_closing_note(saved, fee, switched_off, treasurer, member):
    checkout.charge_due_saved_cards()
    [entry] = reviews.open_charge_reviews()
    reviews.close_charge_review(entry, note=NOTE, by=treasurer)
    targets = core_privacy._MODULES["pagaments"].audit_targets(member.person)
    assert targets[AuditEntry._meta.label_lower] == [entry.pk]  # la nota és text lliure
