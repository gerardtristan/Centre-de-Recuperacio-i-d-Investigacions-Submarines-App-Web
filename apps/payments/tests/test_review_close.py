"""Tancar un intent «a revisar» (T-M05b-16b; P-82, opció per defecte; B6 amb edició). Proves de
permisos per rol, nota obligatòria, llista oberta i «Tancats», doble tancament, registre i que no
es mou cap diner. Només dades inventades."""

import pytest
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.urls import reverse

from apps.core import privacy as core_privacy
from apps.core.models import AppendOnlyError, AuditEntry, Charge, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import attempts, payment_admin_views, reviews
from apps.payments.models import PaymentAttempt, ReviewClosure
from apps.payments.tests.test_payments_list import (  # noqa: F401 (fixtures)
    MANAGEMENT_ROLES,
    SYSTEM,
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
    with pytest.raises(reviews.NotClosable):
        reviews.close(to_review, note=NOTE, by=treasurer)
    assert ReviewClosure.objects.count() == 1
    assert AuditEntry.objects.get(action=reviews.CLOSED).reason == NOTE


def test_only_an_attempt_to_review(treasurer, person):  # noqa: F811
    attempt = in_progress(fee(person))
    assert client_for(treasurer).get(close_url(attempt)).status_code == 404
    with pytest.raises(reviews.NotClosable):
        reviews.close(attempt, note=NOTE, by=treasurer)


def test_audit_with_the_note(treasurer, to_review):  # noqa: F811
    client_for(treasurer).post(close_url(to_review), {"note": f"  {NOTE} "})
    closure = ReviewClosure.objects.get()
    assert closure.closed_by == treasurer
    entry = AuditEntry.objects.get(action=reviews.CLOSED)
    assert entry.reason == NOTE and entry.actor_account == treasurer
    assert (entry.target_type, entry.target_id) == ("payments.reviewclosure", str(closure.pk))
    assert entry.details == {"attempt": to_review.pk}


def test_the_note_has_a_limit_also_in_the_service(treasurer, to_review):  # noqa: F811
    response = client_for(treasurer).post(close_url(to_review), {"note": "x" * 501})
    assert response.status_code == 200 and not ReviewClosure.objects.exists()
    with pytest.raises(ValueError):
        reviews.close(to_review, note="x" * 501, by=treasurer)
    assert reviews.close(to_review, note="x" * 500, by=treasurer)


def test_erasure_leaves_no_note(treasurer, to_review, make_admin):  # noqa: F811
    # La taula de tancaments no té cap text lliure; la nota, al registre, passa a la referència.
    reviews.close(to_review, note=NOTE, by=treasurer)
    assert {f.name for f in ReviewClosure._meta.fields} == {
        "id",
        "attempt",
        "closed_by",
        "closed_at",
    }
    payer = to_review.charge.person
    assert core_privacy.blockers(payer) == []
    core_privacy.anonymise_person(payer, by=make_admin(R.ADMINISTRATOR))
    payer.refresh_from_db()
    entry = AuditEntry.objects.get(action=reviews.CLOSED)
    assert entry.reason == payer.anonymous_ref != NOTE


@pytest.mark.parametrize("role", sorted(WITH_B6))
def test_the_note_is_shown_with_p4_or_to_who_closes(make_admin, treasurer, to_review, role):  # noqa: F811
    reviews.close(to_review, note=NOTE, by=treasurer)
    assert NOTE in html(client_for(make_admin(role)))


def test_without_p4_or_edit_the_note_is_hidden(treasurer, to_review, monkeypatch):  # noqa: F811
    # B6 avui només admet l'abast «tot» (amb edició): un B6 de consulta sense P4 se simula.
    reviews.close(to_review, note=NOTE, by=treasurer)
    monkeypatch.setattr(payment_admin_views, "has_perm", lambda *args, **kwargs: False)
    page = html(client_for(treasurer))
    assert "1 intent a revisar tancat" in page and NOTE not in page and "—" in page


def test_the_caption_does_not_give_a_false_total(treasurer, person, monkeypatch):  # noqa: F811
    monkeypatch.setattr(payment_admin_views, "CLOSED_SHOWN", 1)
    for concept in ("Quota A (prova)", "Quota B (prova)"):
        attempt = attempts.transition(
            in_progress(fee(person, concept=concept)), S.TO_REVIEW, by=SYSTEM, reason="Prova"
        )
        reviews.close(attempt, note=NOTE, by=treasurer)
    assert "Els 1 tancaments més recents, de 2" in html(client_for(treasurer))


def test_append_only(treasurer, to_review):  # noqa: F811
    closure = reviews.close(to_review, note=NOTE, by=treasurer)
    with pytest.raises(AppendOnlyError):
        closure.save()
    with pytest.raises(AppendOnlyError):
        closure.delete()
    for sql in ("UPDATE {} SET closed_at = now()", "DELETE FROM {}"):
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
            cur.execute(sql.format(ReviewClosure._meta.db_table))
