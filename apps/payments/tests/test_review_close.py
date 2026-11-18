"""Tancar un intent «a revisar» (T-M05b-16b i 16c; 097, P-82 opció C; B6 amb edició): el tresorer
decideix «pagat» (registra el pagament, una sola vegada) o «fallit» (cap diner), amb la nota.
Proves de permisos per rol, nota i decisió obligatòries, llista oberta i «Tancats», doble
tancament, registre i diners. Només dades inventades."""

import pytest
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.urls import reverse

from apps.core import charges
from apps.core import privacy as core_privacy
from apps.core.models import AppendOnlyError, AuditEntry, Charge, Payment
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import attempts, payment_admin_views, reviews
from apps.payments.models import PaymentAttempt, Receipt, ReviewClosure
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
from apps.payments.tests.test_processing import transit  # noqa: F401 (fixture)
from apps.treasury.models import Movement
from apps.treasury.tests.test_views import client_for

pytestmark = pytest.mark.django_db
S = PaymentAttempt.Status
CHANGED = "payments.attempt_status_changed"
NOTE = "Comprovat al proveïdor (prova)"
PAID, FAILED = S.PAID, S.FAILED


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
    response = client.post(close_url(to_review), {"outcome": FAILED, "note": NOTE})
    assert response.status_code == (302 if allowed else 404)
    assert ReviewClosure.objects.exists() == allowed


def test_the_list_links_to_the_close_page(treasurer, to_review):  # noqa: F811
    assert close_url(to_review) in html(client_for(treasurer))


def test_service_refuses_without_the_permission(make_admin, to_review):  # noqa: F811
    with pytest.raises(Http404):
        reviews.close(to_review, outcome=FAILED, note=NOTE, by=make_admin(R.SECRETARY))


def test_note_required(treasurer, to_review):  # noqa: F811
    response = client_for(treasurer).post(close_url(to_review), {"outcome": FAILED, "note": "   "})
    assert response.status_code == 200
    assert "Cal una nota per tancar-lo." in response.content.decode()
    assert not ReviewClosure.objects.exists()
    with pytest.raises(ValueError):
        reviews.close(to_review, outcome=FAILED, note=" ", by=treasurer)


def test_097_failed_closes_it_with_no_money(treasurer, to_review):  # noqa: F811
    client = client_for(treasurer)
    response = client.post(close_url(to_review), {"outcome": FAILED, "note": NOTE}, follow=True)
    assert "Intent tancat com a fallit. No s&#x27;ha mogut cap diner." in response.content.decode()
    page = html(client)
    assert "No hi ha cap pagament a revisar." in page
    assert "1 intent a revisar tancat" in page and NOTE in page
    to_review.refresh_from_db()
    assert to_review.status == S.FAILED and ReviewClosure.objects.get().outcome == FAILED
    assert not Payment.objects.exists() and not Movement.objects.exists()
    assert Charge.objects.get(pk=to_review.charge_id).status == Charge.Status.PENDING


def test_097_paid_records_the_payment_once(treasurer, to_review, transit):  # noqa: F811
    response = client_for(treasurer).post(
        close_url(to_review), {"outcome": PAID, "note": NOTE}, follow=True
    )
    assert (
        "Intent tancat com a pagat: s&#x27;ha registrat el pagament." in response.content.decode()
    )
    to_review.refresh_from_db()
    assert to_review.status == S.PAID
    assert Charge.objects.get(pk=to_review.charge_id).status == Charge.Status.PAID
    payment = Payment.objects.get()
    assert (payment.amount_cents, payment.method) == (9000, Payment.Method.CARD)
    assert Movement.objects.filter(kind=Movement.Kind.INCOME).count() == 1
    assert Receipt.objects.filter(attempt=to_review).exists()
    entry = AuditEntry.objects.get(action=CHANGED, new_value=PAID)
    assert entry.actor_account == treasurer and NOTE not in entry.reason  # la nota, al tancament


def test_097_paid_is_refused_if_the_charge_is_already_paid(treasurer, to_review):  # noqa: F811
    transfer = Payment.objects.create(
        charge=to_review.charge, method=Payment.Method.TRANSFER, amount_cents=9000
    )
    charges.mark_paid(to_review.charge, transfer, origin="reconciliation", by=SYSTEM)
    response = client_for(treasurer).post(
        close_url(to_review), {"outcome": PAID, "note": NOTE}, follow=True
    )
    assert "El càrrec ja no és pendent" in response.content.decode()
    with pytest.raises(reviews.ChargeNotPending):
        reviews.close(to_review, outcome=PAID, note=NOTE, by=treasurer)
    to_review.refresh_from_db()
    assert to_review.status == S.TO_REVIEW and not ReviewClosure.objects.exists()
    assert list(Payment.objects.all()) == [transfer]


def test_the_outcome_is_required(treasurer, to_review):  # noqa: F811
    response = client_for(treasurer).post(close_url(to_review), {"note": NOTE})
    assert response.status_code == 200 and not ReviewClosure.objects.exists()
    for outcome in ("", "cancelled", S.EXPIRED):
        with pytest.raises(ValueError):
            reviews.close(to_review, outcome=outcome, note=NOTE, by=treasurer)


def test_an_attempt_can_be_reviewed_again(treasurer, to_review):  # noqa: F811
    # Tancat com a fallit; una confirmació tardana d'un càrrec ja pagat el torna «a revisar».
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    attempts.transition(to_review, S.TO_REVIEW, by=SYSTEM, reason="Pagament duplicat (prova)")
    reviews.close(to_review, outcome=FAILED, note="Devolució feta (prova)", by=treasurer)
    assert ReviewClosure.objects.filter(attempt=to_review).count() == 2


def test_closing_twice_is_refused(treasurer, to_review):  # noqa: F811
    client = client_for(treasurer)
    client.post(close_url(to_review), {"outcome": FAILED, "note": NOTE})
    again = client.post(close_url(to_review), {"outcome": PAID, "note": "Una altra (prova)"})
    assert again.status_code == 404  # ja no és «a revisar»
    with pytest.raises(reviews.NotClosable):
        reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    assert ReviewClosure.objects.count() == 1
    assert AuditEntry.objects.get(action=reviews.CLOSED).reason == NOTE


def test_only_an_attempt_to_review(treasurer, person):  # noqa: F811
    attempt = in_progress(fee(person))
    assert client_for(treasurer).get(close_url(attempt)).status_code == 404
    with pytest.raises(reviews.NotClosable):
        reviews.close(attempt, outcome=FAILED, note=NOTE, by=treasurer)


def test_audit_with_the_note(treasurer, to_review):  # noqa: F811
    client_for(treasurer).post(close_url(to_review), {"outcome": FAILED, "note": f"  {NOTE} "})
    closure = ReviewClosure.objects.get()
    assert closure.closed_by == treasurer
    entry = AuditEntry.objects.get(action=reviews.CLOSED)
    assert entry.reason == NOTE and entry.actor_account == treasurer
    assert (entry.target_type, entry.target_id) == ("payments.reviewclosure", str(closure.pk))
    assert entry.details == {"attempt": to_review.pk, "outcome": FAILED}


def test_the_note_has_a_limit_also_in_the_service(treasurer, to_review):  # noqa: F811
    response = client_for(treasurer).post(
        close_url(to_review), {"outcome": FAILED, "note": "x" * 501}
    )
    assert response.status_code == 200 and not ReviewClosure.objects.exists()
    with pytest.raises(ValueError):
        reviews.close(to_review, outcome=FAILED, note="x" * 501, by=treasurer)
    assert reviews.close(to_review, outcome=FAILED, note="x" * 500, by=treasurer)


def test_erasure_leaves_no_note(treasurer, to_review, make_admin):  # noqa: F811
    # La taula de tancaments no té cap text lliure; la nota, al registre, passa a la referència.
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    assert {f.name for f in ReviewClosure._meta.fields} == {
        "id",
        "attempt",
        "closed_by",
        "closed_at",
        "outcome",
    }
    payer = to_review.charge.person
    assert core_privacy.blockers(payer) == []
    core_privacy.anonymise_person(payer, by=make_admin(R.ADMINISTRATOR))
    payer.refresh_from_db()
    entry = AuditEntry.objects.get(action=reviews.CLOSED)
    assert entry.reason == payer.anonymous_ref != NOTE


@pytest.mark.parametrize("role", sorted(WITH_B6))
def test_the_note_is_shown_with_p4_or_to_who_closes(make_admin, treasurer, to_review, role):  # noqa: F811
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    assert NOTE in html(client_for(make_admin(role)))


def test_without_p4_or_edit_the_note_is_hidden(treasurer, to_review, monkeypatch):  # noqa: F811
    # B6 avui només admet l'abast «tot» (amb edició): un B6 de consulta sense P4 se simula.
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    monkeypatch.setattr(payment_admin_views, "has_perm", lambda *args, **kwargs: False)
    page = html(client_for(treasurer))
    assert "1 intent a revisar tancat" in page and NOTE not in page and "—" in page


def test_the_caption_does_not_give_a_false_total(treasurer, person, monkeypatch):  # noqa: F811
    monkeypatch.setattr(payment_admin_views, "CLOSED_SHOWN", 1)
    for concept in ("Quota A (prova)", "Quota B (prova)"):
        attempt = attempts.transition(
            in_progress(fee(person, concept=concept)), S.TO_REVIEW, by=SYSTEM, reason="Prova"
        )
        reviews.close(attempt, outcome=FAILED, note=NOTE, by=treasurer)
    assert "Els 1 tancaments més recents, de 2" in html(client_for(treasurer))


def test_append_only(treasurer, to_review):  # noqa: F811
    closure = reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    with pytest.raises(AppendOnlyError):
        closure.save()
    with pytest.raises(AppendOnlyError):
        closure.delete()
    for sql in ("UPDATE {} SET closed_at = now()", "DELETE FROM {}"):
        with pytest.raises(DatabaseError), transaction.atomic(), connection.cursor() as cur:
            cur.execute(sql.format(ReviewClosure._meta.db_table))
