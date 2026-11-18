"""Tancar un intent «a revisar» (T-M05b-16b; P-82, opció per defecte; B6 amb edició). Proves de
permisos per rol, nota obligatòria, llista oberta i «Tancats», doble tancament, registre i que no
es mou cap diner. Només dades inventades."""

import pytest
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.urls import reverse

from apps.core.models import AppendOnlyError, AuditEntry, Charge, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import reviews
from apps.payments.models import PaymentAttempt, ReviewClosure
from apps.payments.tests.test_payments_list import (  # noqa: F401 (fixtures)
    MANAGEMENT_ROLES,
    WITH_B6,
    R,
    fee,
    html,
    in_progress,
    person,
    to_review,
)
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
S = PaymentAttempt.Status
NOTE = "Devolució feta des del proveïdor (prova)"


def close_url(attempt):
    return reverse("administration:payments_review_close", args=[attempt.pk])


@pytest.fixture
def treasurer(make_admin):  # noqa: F811
    return make_admin(R.TREASURER)


@pytest.mark.parametrize("role", MANAGEMENT_ROLES)
def test_b6_with_edit_for_each_role(make_admin, to_review, role):  # noqa: F811
    client = client_for(make_admin(role))
    allowed = role in WITH_B6
    assert client.get(close_url(to_review)).status_code == (200 if allowed else 404)
    response = client.post(close_url(to_review), {"note": NOTE})
    assert response.status_code == (302 if allowed else 404)
    assert ReviewClosure.objects.exists() == allowed


def test_the_list_links_to_the_close_page(treasurer, to_review):  # noqa: F811
    assert close_url(to_review) in html(client_for(treasurer))


def test_service_refuses_without_the_permission(make_admin, to_review):  # noqa: F811
    with pytest.raises(Http404):
        reviews.close(to_review, note=NOTE, by=make_admin(R.SECRETARY))


def test_note_required(treasurer, to_review):  # noqa: F811
    response = client_for(treasurer).post(close_url(to_review), {"note": "   "})
    assert response.status_code == 200
    assert "Cal una nota per tancar-lo." in response.content.decode()
    assert not ReviewClosure.objects.exists()
    with pytest.raises(ValueError):
        reviews.close(to_review, note=" ", by=treasurer)


def test_closing_leaves_the_open_list_and_moves_no_money(treasurer, to_review):  # noqa: F811
    client = client_for(treasurer)
    payments, charge_status = Payment.objects.count(), to_review.charge.status
    response = client.post(close_url(to_review), {"note": NOTE}, follow=True)
    assert "Intent tancat. No s&#x27;ha mogut cap diner." in response.content.decode()
    page = html(client)
    assert "No hi ha cap pagament a revisar." in page
    assert "1 intent a revisar tancat" in page and NOTE in page and "(tancat)" in page
    to_review.refresh_from_db()
    assert to_review.status == S.TO_REVIEW  # P-82: d'«a revisar» no se'n surt
    assert Payment.objects.count() == payments
    assert Charge.objects.get(pk=to_review.charge_id).status == charge_status


def test_closing_twice_is_refused(treasurer, to_review):  # noqa: F811
    client = client_for(treasurer)
    client.post(close_url(to_review), {"note": NOTE})
    again = client.post(close_url(to_review), {"note": "Una altra nota (prova)"}, follow=True)
    assert "Aquest intent ja està tancat." in again.content.decode()
    assert client.get(close_url(to_review)).status_code == 302
    with pytest.raises(reviews.NotClosable):
        reviews.close(to_review, note=NOTE, by=treasurer)
    assert ReviewClosure.objects.get().note == NOTE


def test_only_an_attempt_to_review(treasurer, person):  # noqa: F811
    attempt = in_progress(fee(person))
    assert client_for(treasurer).get(close_url(attempt)).status_code == 404
    with pytest.raises(reviews.NotClosable):
        reviews.close(attempt, note=NOTE, by=treasurer)


def test_audit_with_the_note(treasurer, to_review):  # noqa: F811
    client_for(treasurer).post(close_url(to_review), {"note": f"  {NOTE} "})
    entry = AuditEntry.objects.get(action=reviews.CLOSED)
    assert entry.reason == NOTE and entry.actor_account == treasurer
    assert entry.target_id == str(to_review.pk)
    closure = ReviewClosure.objects.get()
    assert closure.note == NOTE and closure.closed_by == treasurer


def test_append_only(treasurer, to_review):  # noqa: F811
    closure = reviews.close(to_review, note=NOTE, by=treasurer)
    with pytest.raises(AppendOnlyError):
        closure.save()
    with pytest.raises(AppendOnlyError):
        closure.delete()
    for sql in ("UPDATE {} SET note = 'x'", "DELETE FROM {}"):
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
            cur.execute(sql.format(ReviewClosure._meta.db_table))
