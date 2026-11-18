"""Intent de pagament (T-M05b-03, tall de targeta; M05b-6; RN-M05b-02, 03 i 04; CA-M05b-25).
Només dades inventades."""

import inspect
from itertools import product

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, models, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import ProtectedError

from apps.core import audit, charges
from apps.core.models import AuditEntry, Department, UndeletableError
from apps.payments import attempts
from apps.payments.models import ATTEMPT_TRANSITIONS, AttemptLocked, InvalidTransition
from apps.payments.models import PaymentAttempt as Attempt
from conftest import CommittedDataTestCase

pytestmark = pytest.mark.django_db
S = Attempt.Status
M = Attempt.Method
SYSTEM = audit.system("proves")
CHANGED = "payments.attempt_status_changed"

# RN-M05b-03, tal com és al pla: cap altra transició no és vàlida.
ALLOWED = {
    *product([S.CREATED], [S.IN_PROGRESS, S.SENT_TO_BANK]),
    *product([S.IN_PROGRESS], [S.PAID, S.FAILED, S.EXPIRED, S.ABANDONED, S.TO_REVIEW]),
    *product([S.SENT_TO_BANK], [S.PAID, S.FAILED]),
}
FORBIDDEN = sorted(set(product(S.values, S.values)) - ALLOWED)


def new_charge(person):
    general = Department.objects.get(name=Department.GENERAL)
    fields = {"kind": "fee", "amount_cents": 9000, "concept": "Inventat", "origin": "proves"}
    return charges.create_charge(person, department=general, by=SYSTEM, **fields)


@pytest.fixture
def charge(make_person):
    return new_charge(make_person("Núria", "Coll"))


def raw(charge, status=S.CREATED, other=None, **fields):
    """Escriu la fila directament, sense el model ni el servei: el que es prova és la base de
    dades, o un estat de partida al qual cap transició no arriba. Només una domiciliació pot
    ser «enviada al banc» (`other`: l'estat on es voldrà anar); la resta són amb targeta."""
    fields.setdefault("amount_cents", charge.amount_cents)
    fields.setdefault("method", M.DIRECT_DEBIT if S.SENT_TO_BANK in (status, other) else M.CARD)
    fields.setdefault("review_reason", "Import diferent" if status == S.TO_REVIEW else "")
    row = Attempt(charge=charge, status=status, **fields)
    with transaction.atomic():
        models.QuerySet(model=Attempt).bulk_create([row])
    return row


def rejected(constraint, charge, **fields):
    with pytest.raises(IntegrityError) as info:
        raw(charge, **fields)
    assert info.value.__cause__.diag.constraint_name == f"payment_attempt_{constraint}"


class TestEntity:
    def test_ca_m05b_25_the_fields_of_the_plan_without_card_iban_or_mandate(self):
        names = {field.name for field in Attempt._meta.get_fields()}
        assert names == set(
            "id charge method amount_cents status provider_code provider_order_id "
            "idempotency_key expires_at guest_link started_by review_reason created_at "
            "updated_at receipt ui_timeout_minutes direct_debit_item".split()
        )  # `receipt`: la relació inversa del rebut (T-M05b-07); `ui_timeout_minutes`: RN-M05b-24;
        # `direct_debit_item`: la del rebut domiciliat (T-M05b-09), que porta el mandat
        assert not [n for n in names if any(w in n for w in ("iban", "pan", "cvv", "card"))]
        # Tall de targeta: l'intent no referencia el mandat (docs/estat/M05a.md).
        related = {f.related_model._meta.label for f in Attempt._meta.fields if f.is_relation}
        assert related == {"core.Charge", "core.GuestLink", "accounts.Account"}
        MANUAL = "manual"  # el rebut d'un pagament registrat a mà (P-12); cap pantalla no el tria
        assert set(M.values) == {"card", "bizum", "transfer", "direct_debit", "saved_card", MANUAL}
        assert len(S.values) == 9

    def test_an_attempt_is_never_deleted_and_protects_its_charge(self, charge):
        attempt = attempts.create_attempt(charge, M.CARD)
        assert str(attempt) == "Targeta 9000 c (Creat)"
        with pytest.raises(UndeletableError):
            attempt.delete()
        with pytest.raises(UndeletableError):
            Attempt.objects.all().delete()
        with pytest.raises(ProtectedError):
            models.Model.delete(charge)

    @pytest.mark.parametrize(
        ("constraint", "fields"),
        [
            ("amount_positive", {"amount_cents": 0}),
            ("method_valid", {"method": "cash"}),
            ("status_valid", {"status": "refunded"}),
            ("review_has_reason", {"status": "to_review", "review_reason": ""}),
        ],
    )
    def test_the_database_refuses_an_incoherent_row(self, charge, constraint, fields):
        rejected(constraint, charge, **fields)

    def test_idempotency_key_and_provider_order_belong_to_one_attempt(self, charge):
        first = raw(charge, provider_code="fake", provider_order_id="o-1")
        raw(charge, provider_code="altre", provider_order_id="o-1")  # un altre proveïdor
        assert raw(charge).idempotency_key != raw(charge).idempotency_key  # i sense ordre encara
        rejected("provider_order_once", charge, provider_code="fake", provider_order_id="o-1")
        with pytest.raises(IntegrityError):
            raw(charge, idempotency_key=first.idempotency_key)


class TestCreate:
    """RN-M05b-02: l'import el fixa el servidor a partir del càrrec, mai ve de fora."""

    def test_rn_m05b_02_the_amount_is_the_charges_and_nobody_can_pass_another(self, charge):
        assert "amount_cents" not in inspect.signature(attempts.create_attempt).parameters
        attempt = attempts.create_attempt(charge, M.CARD)
        attempt.refresh_from_db()
        assert attempt.amount_cents == charge.amount_cents == 9000
        assert isinstance(attempt.amount_cents, int)
        assert (attempt.status, attempt.started_by, attempt.guest_link) == (S.CREATED, None, None)
        entry = AuditEntry.objects.get(action="payments.attempt_created")
        assert (entry.actor_kind, entry.actor_origin) == ("system", "payments")

    @pytest.mark.parametrize("amount", [1, 8999, 9001, 9000.0, "9000", None])
    def test_rn_m05b_02_an_amount_other_than_the_charges_is_refused(self, charge, amount):
        with pytest.raises(ValidationError):
            Attempt.objects.create(charge=charge, method=M.CARD, amount_cents=amount)
        with pytest.raises(AttemptLocked):  # ni en bloc, que no passaria per la comprovació
            Attempt.objects.bulk_create([Attempt(charge=charge, amount_cents=1)])
        assert not Attempt.objects.exists()

    def test_leaves_a_trace_with_the_account_that_pays(self, charge, personal_account):
        attempt = attempts.create_attempt(charge, M.CARD, started_by=personal_account)
        assert (attempt.method, attempt.started_by) == (M.CARD, personal_account)
        assert (attempt.provider_code, attempt.provider_order_id) == ("", "")
        entry = AuditEntry.objects.get(action="payments.attempt_created")
        assert (entry.target_type, entry.target_id) == ("payments.paymentattempt", str(attempt.pk))
        assert entry.actor_account == personal_account
        assert entry.details == {"charge": charge.pk, "method": "card", "amount_cents": 9000}

    def test_a_bizum_attempt_can_be_started(self, charge):
        assert attempts.create_attempt(charge, M.BIZUM).method == M.BIZUM

    def test_a_transfer_attempt_can_be_started(self, charge):
        assert attempts.create_attempt(charge, M.TRANSFER).method == M.TRANSFER

    @pytest.mark.parametrize("method", ["direct_debit", "cash"])
    def test_only_card_bizum_transfer_and_saved_card_attempts_can_be_started(self, charge, method):
        with pytest.raises(attempts.MethodNotAllowed):
            attempts.create_attempt(charge, method)
        assert not Attempt.objects.exists()

    def test_a_charge_that_is_not_pending_cannot_be_paid(self, charge):
        charges.cancel(charge, "Duplicat", by=SYSTEM)
        with pytest.raises(attempts.ChargeNotPayable):
            attempts.create_attempt(charge, M.CARD)
        assert not Attempt.objects.exists()


class TestTransitions:
    """RN-M05b-03: cada transició permesa i cada transició prohibida, una per una."""

    def test_rn_m05b_03_the_table_is_exactly_the_one_of_the_plan(self):
        assert ATTEMPT_TRANSITIONS == ALLOWED

    @pytest.mark.parametrize("status", sorted(set(S.values) - {S.CREATED}))
    def test_rn_m05b_03_an_attempt_is_always_born_created(self, charge, status):
        with pytest.raises(InvalidTransition):  # ni «pagat» d'entrada, desant el model directament
            Attempt.objects.create(charge=charge, method=M.CARD, amount_cents=9000, status=status)

    @pytest.mark.parametrize(("old", "new"), sorted(ALLOWED))
    def test_rn_m05b_03_allowed_transition(self, charge, old, new):
        attempt = raw(charge, old, new)
        result = attempts.transition(attempt, new, by=SYSTEM, reason="Import diferent")
        attempt.refresh_from_db()
        assert result.status == attempt.status == new
        entry = AuditEntry.objects.get(action=CHANGED)
        assert (entry.field, entry.old_value, entry.new_value) == ("status", old, new)
        assert (entry.target_id, entry.actor_origin) == (str(attempt.pk), "proves")

    @pytest.mark.parametrize(("old", "new"), FORBIDDEN)
    def test_rn_m05b_03_forbidden_transition(self, charge, old, new):
        attempt = raw(charge, old, new)
        with pytest.raises(InvalidTransition):
            attempts.transition(attempt, new, by=SYSTEM, reason="Perquè sí")
        attempt.refresh_from_db()
        assert attempt.status == old
        assert not AuditEntry.objects.filter(action=CHANGED).exists()

    @pytest.mark.parametrize("new", [*S.values, "refunded"])
    def test_rn_m05b_03_paid_never_goes_back(self, charge, new):
        attempt = raw(charge, S.PAID, new)
        with pytest.raises(InvalidTransition):
            attempts.transition(attempt, new, by=SYSTEM, reason="Correcció")
        attempt.status = new
        if new != S.PAID:  # ni tan sols desant el model directament
            with pytest.raises(InvalidTransition):
                attempt.save()
            with pytest.raises(InvalidTransition):
                attempt.save(update_fields=["status"])
        attempt.refresh_from_db()
        assert attempt.status == S.PAID

    def test_rn_m05b_03_a_card_attempt_is_never_sent_to_the_bank(self, charge):
        attempt = attempts.create_attempt(charge, M.CARD)
        with pytest.raises(InvalidTransition):
            attempts.transition(attempt, S.SENT_TO_BANK, by=SYSTEM)
        attempt.refresh_from_db()
        assert attempt.status == S.CREATED

    def test_rn_m05b_03_the_stored_status_decides_not_the_copy_in_memory(self, charge):
        attempt = raw(charge, S.IN_PROGRESS)
        stale = Attempt.objects.get(pk=attempt.pk)
        attempts.transition(attempt, S.PAID, by=SYSTEM)
        with pytest.raises(InvalidTransition):
            attempts.transition(stale, S.FAILED, by=SYSTEM)
        stale.status = S.FAILED
        with pytest.raises(InvalidTransition):
            stale.save(update_fields=["status"])
        stale.save(update_fields=["expires_at", "updated_at"])  # no toca l'estat: es pot desar
        assert Attempt.objects.get(pk=attempt.pk).status == S.PAID

    def test_to_review_needs_a_reason_and_keeps_it(self, charge):
        attempt = raw(charge, S.IN_PROGRESS)
        with pytest.raises(ValidationError):
            attempts.transition(attempt, S.TO_REVIEW, by=SYSTEM, reason="  ")
        attempts.transition(attempt, S.TO_REVIEW, by=SYSTEM, reason=" Import diferent ")
        attempt.refresh_from_db()
        assert (attempt.status, attempt.review_reason) == (S.TO_REVIEW, "Import diferent")
        assert AuditEntry.objects.get(action=CHANGED).reason == "Import diferent"


class TestLocked:
    """El que identifica l'intent no canvia mai; l'estat, només amb les transicions."""

    @pytest.mark.parametrize("field", sorted(Attempt.IDENTITY_FIELDS))
    def test_identity_fields_do_not_change(self, charge, field):
        attempt = attempts.create_attempt(charge, M.CARD)
        setattr(attempt, field, 0)
        with pytest.raises(AttemptLocked):
            attempt.save()
        with pytest.raises(AttemptLocked):
            attempt.save(update_fields=[field])

    def test_no_bulk_update(self, charge):
        attempt = attempts.create_attempt(charge, M.CARD)
        with pytest.raises(AttemptLocked):
            Attempt.objects.filter(pk=attempt.pk).update(status=S.PAID)
        with pytest.raises(AttemptLocked), transaction.atomic():
            Attempt.objects.bulk_update([attempt], ["status"])


class TestOnePerCharge:
    """RN-M05b-04: ho garanteix la base de dades, amb dos índexs únics parcials."""

    @pytest.mark.parametrize("first", [S.IN_PROGRESS, S.SENT_TO_BANK])
    @pytest.mark.parametrize("second", [S.IN_PROGRESS, S.SENT_TO_BANK])
    def test_rn_m05b_04_one_in_progress_per_charge_in_the_database(self, charge, first, second):
        raw(charge, first)
        rejected("one_in_progress", charge, status=second)

    def test_rn_m05b_04_one_paid_attempt_per_charge_in_the_database(self, charge):
        raw(charge, S.PAID)
        rejected("one_paid", charge, status=S.PAID)

    def test_rn_m05b_04_a_second_attempt_waits_until_the_first_ends(self, charge):
        first = attempts.create_attempt(charge, M.CARD)
        second = attempts.create_attempt(charge, M.CARD)  # «creat» encara no és «en curs»
        attempts.transition(first, S.IN_PROGRESS, by=SYSTEM)
        with pytest.raises(attempts.AttemptInProgress):
            attempts.transition(second, S.IN_PROGRESS, by=SYSTEM)
        second.refresh_from_db()
        assert second.status == S.CREATED
        assert AuditEntry.objects.filter(action=CHANGED).count() == 1
        attempts.transition(first, S.FAILED, by=SYSTEM)
        assert attempts.transition(second, S.IN_PROGRESS, by=SYSTEM).status == S.IN_PROGRESS

    def test_rn_m05b_04_a_second_paid_attempt_is_refused(self, charge):
        raw(charge, S.PAID)
        second = raw(charge, S.IN_PROGRESS)
        with pytest.raises(attempts.AttemptAlreadyPaid):
            attempts.transition(second, S.PAID, by=SYSTEM)
        second.refresh_from_db()
        assert second.status == S.IN_PROGRESS

    def test_another_database_error_is_not_disguised(self, charge, monkeypatch):
        monkeypatch.setattr(attempts, "_CONFLICTS", {})
        raw(charge, S.IN_PROGRESS)
        second = attempts.create_attempt(charge, M.CARD)
        with pytest.raises(IntegrityError):
            attempts.transition(second, S.IN_PROGRESS, by=SYSTEM)

    def test_rn_m05b_04_each_charge_has_its_own_attempts(self, charge):
        for one in (charge, new_charge(charge.person)):
            for status in (S.IN_PROGRESS, S.PAID, S.FAILED, S.FAILED):
                raw(one, status)
        assert Attempt.objects.count() == 8


class TestMigrationIsReversible(CommittedDataTestCase):
    """La migració de l'intent es desfà i es torna a aplicar a la base de proves."""

    def test_backwards_and_forwards(self):
        table = Attempt._meta.db_table
        leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
        try:
            MigrationExecutor(connection).migrate([("payments", "0001_provider_event")])
            assert table not in connection.introspection.table_names()
        finally:
            MigrationExecutor(connection).migrate(leaves)
        with connection.cursor() as cursor:
            names = set(connection.introspection.get_constraints(cursor, table))
        assert {"payment_attempt_one_in_progress", "payment_attempt_one_paid"} <= names
