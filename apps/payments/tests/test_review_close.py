"""Tancar un intent «a revisar» (T-M05b-16b i 16c; 097, P-82 opció C; B6 amb edició): el tresorer
decideix «pagat» (registra el pagament, una sola vegada) o «fallit» (cap diner), amb la nota.
Proves de permisos per rol, nota i decisió obligatòries, llista oberta i «Tancats», doble
tancament, registre i diners. Només dades inventades."""

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.http import Http404
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Account
from apps.core import charges
from apps.core import privacy as core_privacy
from apps.core.models import AppendOnlyError, AuditEntry, Charge, Payment, Person
from apps.core.tests.conftest import make_admin  # noqa: F401 (fixture)
from apps.payments import attempts, payment_admin_views, processing, reviews
from apps.payments.models import PaymentAttempt, Receipt, ReviewClosure, ReviewCode
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
from conftest import CommittedDataTestCase

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
    closure = ReviewClosure.objects.get(attempt=to_review)
    assert closure.outcome == ReviewClosure.Outcome.PAID and closure.closed_by == treasurer
    assert payment.charge_id == closure.attempt.charge_id
    # T-M05b-30: l'origen propi, al pagament mateix, amb qui i el motiu (quan: `created_at`).
    assert payment.origin == Payment.Origin.TREASURER_DECISION
    assert payment.recorded_by == treasurer
    assert payment.reason == f"Decisió del tresorer (tancament {closure.pk})"
    assert payment.created_at is not None
    paid = AuditEntry.objects.get(action="charges.status_changed", new_value="paid")
    assert paid.details["origin"] == "treasurer_decision"
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
    with pytest.raises(reviews.PaidRefused):
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
    # La taula de tancaments no té cap text del tresorer (el motiu és el del sistema); la nota,
    # al registre, passa a la referència.
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    assert {f.name for f in ReviewClosure._meta.fields} == {
        "id",
        "attempt",
        "closed_by",
        "closed_at",
        "outcome",
        "review_reason",
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


def test_paid_is_refused_with_another_attempt_that_may_collect(treasurer, to_review):  # noqa: F811
    in_progress_again = attempts.create_attempt(to_review.charge, PaymentAttempt.Method.BIZUM)
    attempts.transition(in_progress_again, S.IN_PROGRESS, by=SYSTEM)
    response = client_for(treasurer).post(close_url(to_review), {"outcome": PAID, "note": NOTE})
    # El missatge és el de la guarda comuna del pagament a mà (una sola llista).
    assert "té un pagament en curs o per revisar" in response.content.decode()
    with pytest.raises(reviews.PaidRefused):
        reviews.close(to_review, outcome=PAID, note=NOTE, by=treasurer)
    assert not Payment.objects.exists() and not ReviewClosure.objects.exists()


def test_paid_is_refused_when_the_amount_did_not_match(treasurer, person):  # noqa: F811
    # CA-M05b-05: han entrat 80 €, no 90 €. La plataforma no apunta 90 €.
    attempt = attempts.transition(
        in_progress(fee(person)),
        S.TO_REVIEW,
        by=SYSTEM,
        reason=str(processing.AMOUNT_MISMATCH),
        code=ReviewCode.AMOUNT,
    )
    with pytest.raises(reviews.PaidRefused):
        reviews.close(attempt, outcome=PAID, note=NOTE, by=treasurer)
    assert not Payment.objects.exists()
    reviews.close(attempt, outcome=FAILED, note=NOTE, by=treasurer)  # «Fallit» sí


def test_paid_needs_the_manual_payment_permission(make_admin, to_review):  # noqa: F811
    # L'administrador té B6 amb edició però no M14: no veu «Pagat» i el servidor el rebutja.
    admin = make_admin(R.ADMINISTRATOR)
    client = client_for(admin)
    page = client.get(close_url(to_review)).content.decode()
    assert "«Pagat» no està disponible" in page and 'value="paid"' not in page
    response = client.post(close_url(to_review), {"outcome": PAID, "note": NOTE})
    assert response.status_code == 200 and not ReviewClosure.objects.exists()
    with pytest.raises(Http404):
        reviews.close(to_review, outcome=PAID, note=NOTE, by=admin)
    assert not Payment.objects.exists()
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=admin)


def test_tancats_shows_the_reason_when_closed_and_not_the_login(treasurer, to_review):  # noqa: F811
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    attempts.transition(to_review, S.TO_REVIEW, by=SYSTEM, reason="Un altre motiu (prova)")
    page = html(client_for(treasurer))
    closed = page.split("Tancats", 1)[1].split("Tots els intents", 1)[0]
    assert "L&#x27;import de la notificació no quadra (prova)" in closed
    assert "Un altre motiu (prova)" not in closed
    assert str(treasurer.person) in closed and treasurer.login not in closed


def test_a_16b_closure_is_still_open_and_can_be_decided(treasurer, to_review):  # noqa: F811
    # Un tancament d'abans de la 0025: «sense decisió» i l'intent encara «a revisar». No compta
    # com a tancat: surt a «A revisar», marcat, i el tresorer el pot decidir.
    ReviewClosure.objects.create(
        attempt=to_review,
        outcome=ReviewClosure.Outcome.UNDECIDED,
        review_reason=to_review.review_reason,
        closed_by=treasurer,
    )
    page = html(client_for(treasurer))
    assert "1 intent de pagament a revisar" in page
    assert "(tancat sense decisió, T-M05b-16b)" in page and "(tancat sense decisió)" in page
    assert close_url(to_review) in page
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    page = html(client_for(treasurer))
    assert "No hi ha cap pagament a revisar." in page and "(decisió del tresorer)" in page


def test_the_decision_label_only_when_the_status_matches(treasurer, to_review):  # noqa: F811
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    assert "(decisió del tresorer)" in html(client_for(treasurer))
    # Torna «a revisar» (una confirmació tardana d'un càrrec ja pagat): ja no és la decisió.
    attempts.transition(to_review, S.TO_REVIEW, by=SYSTEM, reason="Pagament duplicat (prova)")
    page = html(client_for(treasurer))
    assert "1 intent de pagament a revisar" in page and "(decisió del tresorer)" not in page


def test_a_registered_guard_also_blocks_paid(treasurer, to_review, monkeypatch):  # noqa: F811
    def guard(charge, **context):
        raise ValidationError("Bloquejat per una guarda de prova.")

    monkeypatch.setattr(charges, "_MANUAL_PAYMENT_GUARDS", [*charges._MANUAL_PAYMENT_GUARDS, guard])
    with pytest.raises(reviews.PaidRefused, match="guarda de prova"):
        reviews.close(to_review, outcome=PAID, note=NOTE, by=treasurer)
    assert not Payment.objects.exists() and not ReviewClosure.objects.exists()


def test_an_unrelated_save_does_not_reopen_a_decided_attempt(treasurer, to_review):  # noqa: F811
    reviews.close(to_review, outcome=FAILED, note=NOTE, by=treasurer)
    to_review.refresh_from_db()
    to_review.expires_at = timezone.now()
    to_review.save(update_fields=["expires_at", "updated_at"])
    assert "No hi ha cap pagament a revisar." in html(client_for(treasurer))


class TestMigration0025(CommittedDataTestCase):
    """Un tancament de la T-M05b-16b, d'abans de la 0025: queda «sense decisió», amb el motiu, i
    el codi «altre»."""

    def test_an_existing_closure_is_undecided_and_keeps_the_reason(self):
        payer = Person.objects.create(first_name="Núria", last_name="Coll", origin="web")
        attempt = attempts.transition(
            in_progress(fee(payer)), S.TO_REVIEW, by=SYSTEM, reason="Motiu antic (prova)"
        )
        admin = Account.objects.create_admin(
            Person.objects.create(first_name="Tresorer", origin="in_person"), "tresoreria.antiga"
        )
        leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
        try:
            MigrationExecutor(connection).migrate([("payments", "0024_paisos_iban")])
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO payments_reviewclosure (attempt_id, closed_by_id, closed_at) "
                    "VALUES (%s, %s, now())",
                    [attempt.pk, admin.pk],
                )
        finally:
            MigrationExecutor(connection).migrate(leaves)
        closure = ReviewClosure.objects.get()
        assert (closure.outcome, closure.review_reason) == ("undecided", "Motiu antic (prova)")
        attempt.refresh_from_db()
        assert attempt.status == S.TO_REVIEW
        assert attempt.review_code == ""  # «altre»: cap guarda no el confon amb un import


def test_t_m05b_30_a_payment_from_the_provider_keeps_its_origin(person):  # noqa: F811
    """La notificació del proveïdor continua creant pagaments amb l'origen «provider», sense qui
    ni motiu."""
    attempt = in_progress(fee(person))
    with transaction.atomic():
        locked_charge = Charge.objects.select_for_update().get(pk=attempt.charge_id)
        locked = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        processing.pay(locked, locked_charge, by=SYSTEM, status="paid", reference="ORDRE-1")
    payment = Payment.objects.get()
    assert (payment.origin, payment.recorded_by, payment.reason) == (
        Payment.Origin.PROVIDER,
        None,
        "",
    )


def test_t_m05b_30_the_database_keeps_the_origin_consistent(treasurer, to_review):  # noqa: F811
    charge = to_review.charge
    cases = [
        {"method": Payment.Method.CARD, "origin": "inventat"},
        {"method": Payment.Method.MANUAL, "origin": Payment.Origin.PROVIDER},
        {"method": Payment.Method.CARD, "origin": Payment.Origin.MANUAL},
        {"method": Payment.Method.CARD, "origin": Payment.Origin.TREASURER_DECISION},
        {
            "method": Payment.Method.CARD,
            "origin": Payment.Origin.TREASURER_DECISION,
            "recorded_by": treasurer,
        },
    ]
    for fields in cases:
        with pytest.raises(DatabaseError), transaction.atomic():
            Payment.objects.create(charge=charge, amount_cents=9000, **fields)


def test_t_m05b_30_a_decision_needs_a_reason_in_the_service(treasurer, to_review):  # noqa: F811
    with pytest.raises(ValidationError), transaction.atomic():
        charges.record_payment(
            to_review.charge,
            method=Payment.Method.CARD,
            origin=Payment.Origin.TREASURER_DECISION,
            by=treasurer,
        )
    assert not Payment.objects.exists()


class TestMigrationOrigin(CommittedDataTestCase):
    """T-M05b-30 (`core/0057` i `payments/0028`): els pagaments d'abans reben l'origen: «manual»
    els del mètode manual, «reconciliation» els que el registre diu que van entrar per una
    conciliació, «treasurer_decision» el d'un tancament «Pagat» (amb qui i el motiu) i
    «provider» la resta."""

    def test_existing_payments_get_their_origin(self):
        from apps.core import audit

        payer = Person.objects.create(first_name="Núria", last_name="Coll", origin="web")
        admin = Account.objects.create_admin(
            Person.objects.create(first_name="Tresorer", origin="in_person"), "tresoreria.origen"
        )
        decided = attempts.transition(
            in_progress(fee(payer)), S.TO_REVIEW, by=SYSTEM, reason="Sense resposta (prova)"
        )
        charges_ids = [fee(payer).pk for _ in range(3)]
        leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
        try:
            MigrationExecutor(connection).migrate(
                [("payments", "0027_transaccio_del_proveidor"), ("core", "0056_erasure_in_person")]
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO payments_reviewclosure (attempt_id, outcome, review_reason, "
                    "closed_by_id, closed_at) VALUES (%s, 'paid', '', %s, now() - interval '1 "
                    "minute') RETURNING id",
                    [decided.pk, admin.pk],
                )
                closure_id = cursor.fetchone()[0]
                ids = {}
                rows = [
                    ("decidit", decided.charge_id, "card", None, ""),
                    ("manual", charges_ids[0], "manual", admin.pk, "Efectiu (prova)"),
                    ("conciliat", charges_ids[1], "transfer", None, ""),
                    ("proveidor", charges_ids[2], "bizum", None, ""),
                ]
                for name, charge_id, method, who, why in rows:
                    cursor.execute(
                        "INSERT INTO core_payment (charge_id, method, amount_cents, "
                        "provider_status, needs_review, provider_reference, transfer_reference, "
                        "paid_at, recorded_by_id, reason, created_at) VALUES (%s, %s, 9000, '', "
                        "false, '', '', now(), %s, %s, now()) RETURNING id",
                        [charge_id, method, who, why],
                    )
                    ids[name] = cursor.fetchone()[0]
            audit.record(
                "charges.status_changed",
                actor=SYSTEM,
                details={"origin": "reconciliation", "payment": ids["conciliat"]},
            )
        finally:
            MigrationExecutor(connection).migrate(leaves)
        origins = dict(Payment.objects.values_list("pk", "origin"))
        assert {name: origins[pk] for name, pk in ids.items()} == {
            "decidit": "treasurer_decision",
            "manual": "manual",
            "conciliat": "reconciliation",
            "proveidor": "provider",
        }
        decision = Payment.objects.get(pk=ids["decidit"])
        assert decision.recorded_by == admin
        assert decision.reason == f"Decisió del tresorer (tancament {closure_id})"
