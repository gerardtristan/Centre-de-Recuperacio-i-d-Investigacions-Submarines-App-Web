"""Moviment de tresoreria immutable (T-M04-03; HU-T06; CA-T06.3, CA-T17.1 i la segona meitat de
CA-T01.3; RN-T05 a RN-T07, RN-T09, RN-T12 i RN-T25). Només dades inventades."""

from datetime import date
from importlib import import_module

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, connection, migrations, transaction
from django.db.migrations.executor import MigrationExecutor

from apps.core.models import AppendOnlyError, Charge, Department, Payment
from apps.treasury.models import CostCentre, Movement, TreasuryAccount

pytestmark = pytest.mark.django_db
K = Movement.Kind
IN, OUT = Movement.Direction.IN, Movement.Direction.OUT
TRIGGERS = {"treasury_movement_no_update_or_delete", "treasury_movement_no_truncate"}
IMMUTABLE = "moviments de tresoreria no es poden modificar ni esborrar"


@pytest.fixture
def cash():
    return TreasuryAccount.objects.get(name="Caixa")


@pytest.fixture
def adjustments():
    return CostCentre.objects.select_related("department").get(name="Ajustos de caixa")


@pytest.fixture
def fields(cash, adjustments):
    """Un ajust d'arqueig vàlid: el moviment més senzill que no depèn de cap pagament."""
    return {
        "account": cash,
        "direction": OUT,
        "amount_cents": 50,
        "value_date": date(2026, 11, 13),
        "kind": K.CASH_ADJUSTMENT,
        "concept": "Ajust d'arqueig de la caixa",
        "department": adjustments.department,
        "cost_centre": adjustments,
        "reason": "Falten 50 cèntims en el recompte",
    }


@pytest.fixture
def movement(fields):
    return Movement.objects.create(**fields)


def reversal_of(original, **fields):
    """Els camps del contramoviment d'un moviment (P-M04-C, pas 3)."""
    reason = "L'ajust es va apuntar dues vegades"
    opposite = IN if original.direction == OUT else OUT
    return {
        **fields,
        "kind": K.REVERSAL,
        "direction": opposite,
        "reverses": original,
        "reason": reason,
    }


def insert(**fields):
    """Sense les comprovacions del model: el que es prova és la base de dades."""
    with transaction.atomic():
        return Movement._base_manager.bulk_create([Movement(**fields)])[0]


def db_rejects(**fields):
    with pytest.raises(IntegrityError):
        insert(**fields)


def row(pk):
    return Movement.objects.filter(pk=pk).values().get()


def triggers():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT tgname FROM pg_trigger WHERE tgrelid = 'treasury_movement'::regclass"
            " AND NOT tgisinternal"
        )
        return {name for (name,) in cursor.fetchall()}


class TestImmutable:
    def test_ca_t06_3_the_application_cannot_change_or_delete_a_movement(self, movement):
        before = row(movement.pk)
        movement.amount_cents = 1
        for attempt in (
            movement.save,
            movement.delete,
            lambda: Movement.objects.filter(pk=movement.pk).update(amount_cents=1),
            lambda: Movement.objects.filter(pk=movement.pk).delete(),
            lambda: Movement.objects.bulk_update([movement], ["amount_cents"]),
        ):
            with pytest.raises(AppendOnlyError):
                attempt()
        assert row(movement.pk) == before

    @pytest.mark.parametrize(
        "sql",
        [
            "UPDATE treasury_movement SET amount_cents = 1 WHERE id = %s",
            "UPDATE treasury_movement SET concept = 'canviat', reason = 'x' WHERE id = %s",
            "DELETE FROM treasury_movement WHERE id = %s",
        ],
        ids=["update-amount", "update-text", "delete"],
    )
    def test_ca_t06_3_a_direct_sql_query_cannot_change_or_delete_a_movement(self, movement, sql):
        before = row(movement.pk)
        with pytest.raises(DatabaseError, match=IMMUTABLE), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql, [movement.pk])
        assert row(movement.pk) == before

    def test_ca_t06_3_a_direct_truncate_is_rejected(self, movement):
        # Amb les claus foranes de la fila nova encara per comprovar, PostgreSQL rebutja el
        # TRUNCATE ell sol, abans de l'activador: es comproven primer, i el rebuig és l'activador.
        connection.check_constraints()
        with pytest.raises(DatabaseError, match=IMMUTABLE), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("TRUNCATE treasury_movement CASCADE")
        assert Movement.objects.filter(pk=movement.pk).exists()

    def test_ca_t06_3_skipping_the_model_guard_is_stopped_by_the_database(self, movement):
        rows = Movement._base_manager.filter(pk=movement.pk)
        with pytest.raises(DatabaseError, match=IMMUTABLE), transaction.atomic():
            rows.update(amount_cents=1)
        with pytest.raises(DatabaseError, match=IMMUTABLE), transaction.atomic():
            rows.delete()

    def test_both_migrations_can_be_undone_and_applied_again(self):
        module = import_module("apps.treasury.migrations.0006_movement_immutable")
        assert all(
            isinstance(op, migrations.RunSQL) and op.reverse_sql
            for op in module.Migration.operations
        )
        assert triggers() == TRIGGERS
        MigrationExecutor(connection).migrate([("treasury", "0005_movement")])
        assert triggers() == set()
        MigrationExecutor(connection).migrate([("treasury", "0004_initial_cost_centres")])
        assert "treasury_movement" not in connection.introspection.table_names()
        MigrationExecutor(connection).migrate([("treasury", "0006_movement_immutable")])
        assert triggers() == TRIGGERS


class TestReversedIsDerived:
    def test_ca_t17_1_a_reversed_movement_shows_as_reversed_and_its_row_is_the_same(
        self, movement, fields
    ):
        before = row(movement.pk)
        assert not Movement.objects.get(pk=movement.pk).is_reversed
        reversal = Movement.objects.create(**reversal_of(movement, **fields))
        original = Movement.objects.get(pk=movement.pk)
        assert original.is_reversed and original.reversal == reversal
        assert not Movement.objects.get(pk=reversal.pk).is_reversed
        assert row(movement.pk) == before
        assert not {"reversed", "is_reversed", "status"} & set(before)  # cap camp que es modifiqui

    def test_ca_t17_1_a_second_reversal_of_the_same_movement_is_rejected(self, movement, fields):
        Movement.objects.create(**reversal_of(movement, **fields))
        with pytest.raises(IntegrityError), transaction.atomic():
            Movement.objects.create(**reversal_of(movement, **fields))
        db_rejects(**reversal_of(movement, **fields))
        assert Movement.objects.filter(reverses=movement).count() == 1

    def test_a_listing_knows_what_is_reversed_without_a_query_per_row(
        self, movement, fields, django_assert_num_queries
    ):
        Movement.objects.create(**fields)
        Movement.objects.create(**reversal_of(movement, **fields))
        with django_assert_num_queries(1):
            flags = [m.is_reversed for m in Movement.objects.with_reversal().order_by("pk")]
        assert flags == [True, False, False]

    def test_only_a_reversal_points_to_the_movement_it_reverses(self, movement, fields):
        db_rejects(**fields, reverses=movement)
        db_rejects(**{**fields, "kind": K.REVERSAL})
        db_rejects(**{**reversal_of(movement, **fields), "reason": " "})  # sempre amb motiu


class TestAccount:
    def test_ca_t01_3_a_deactivated_account_admits_no_new_movements(self, movement, fields, cash):
        cash.active = False
        cash.save()
        with pytest.raises(ValidationError, match="desactivat"):
            Movement.objects.create(**fields)
        with pytest.raises(ValidationError, match="desactivat"):
            Movement.objects.bulk_create([Movement(**fields)])
        with pytest.raises(ValidationError, match="desactivat"):
            Movement.objects.create(**reversal_of(movement, **fields))
        assert list(Movement.objects.all()) == [movement]  # els que ja hi eren es conserven

    def test_ca_t01_3_the_account_is_checked_in_the_database_not_in_memory(self, fields, cash):
        # Un altre procés desactiva el compte després que aquest l'hagi llegit.
        TreasuryAccount.objects.filter(pk=cash.pk).update(active=False)
        assert fields["account"].active  # la còpia en memòria encara diu «actiu»
        with pytest.raises(ValidationError, match="desactivat"):
            Movement.objects.create(**fields)
        with pytest.raises(ValidationError, match="desactivat"):
            Movement.objects.bulk_create([Movement(**fields)])

    def test_ca_t01_3_an_account_with_movements_cannot_be_deleted_with_direct_sql(self, movement):
        with pytest.raises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM treasury_treasuryaccount WHERE id = %s", [movement.account_id]
                )
            connection.check_constraints()


class TestRules:
    @pytest.mark.parametrize("amount", [0, -1, 12.5, "50", True, None])
    def test_amount_is_a_positive_integer_of_cents(self, fields, amount):
        with pytest.raises(ValidationError):
            Movement.objects.create(**{**fields, "amount_cents": amount})

    @pytest.mark.parametrize(
        "change",
        [
            {"amount_cents": 0},
            {"direction": "xx"},
            {"kind": "gift"},
            {"reason": " "},  # obligatori a l'ajust d'arqueig
            {"department": None, "cost_centre": None},  # RN-T05: obligatori fora dels traspassos
            {"kind": K.TRANSFER},  # RN-T12: un traspàs no porta departament
        ],
        ids=lambda change: ",".join(change),
    )
    def test_the_database_rejects_a_movement_that_breaks_a_rule(self, fields, change):
        db_rejects(**{**fields, **change})

    def test_cost_centre_belongs_to_the_department_of_the_movement(self, fields):
        courses = Department.objects.create(name="Cursos")
        for department in (courses, None):
            with pytest.raises(ValidationError, match="centre de cost"):
                Movement.objects.create(**{**fields, "department": department})

    def test_rn_t09_a_payment_has_at_most_one_income(self, fields, make_person):
        charge = Charge.objects.create(
            person=make_person("Núria", "Coll"),
            kind="fee",
            concept="Quota 2026, soci 1954",
            amount_cents=50,
            department=fields["department"],
            origin="members",
        )
        payment = Payment.objects.create(charge=charge, method="card", amount_cents=50)
        income = {**fields, "kind": K.INCOME, "direction": IN, "payment": payment, "reason": ""}
        assert Movement.objects.create(**income)
        db_rejects(**income)
        # El mateix pagament sí que pot tenir altres moviments: la comissió, una devolució…
        assert Movement.objects.create(**{**income, "kind": K.FEE, "direction": OUT})

    def test_rn_t12_a_transfer_has_two_linked_legs_without_department(self, fields):
        leg = {**fields, "kind": K.TRANSFER, "department": None, "cost_centre": None, "reason": ""}
        out = Movement.objects.create(**leg)
        bank = TreasuryAccount.objects.get(name="Banc principal")
        entry = Movement.objects.create(
            **{**leg, "account": bank, "direction": IN, "linked_movement": out}
        )
        assert entry.linked_movement == out and list(out.linked_from.all()) == [entry]
        # El contramoviment d'una pota tampoc no porta departament: la base de dades l'admet.
        assert Movement.objects.create(**reversal_of(out, **leg)).department is None

    def test_lt10_a_deactivated_cost_centre_keeps_receiving_the_movements_of_its_charges(
        self, fields, adjustments
    ):
        # «No es pot triar» (CA-T14.2) és de qui tria, amb `CostCentre.selectable`: un cobrament
        # confirmat d'un càrrec antic no es rebutja perquè el seu centre de cost ja no s'ofereix.
        CostCentre.objects.filter(pk=adjustments.pk).update(active=False)
        assert Movement.objects.create(**fields)

    def test_no_field_can_hold_an_iban_a_card_or_a_person(self, movement):
        names = {field.name for field in Movement._meta.get_fields()}
        assert not names & {"iban", "pan", "cvv", "cvc", "card_number", "account_number", "person"}
        assert movement.recorded_by is None  # sense compte: l'ha creat el sistema
        assert str(movement) == "Ajust d'arqueig −50 c (Caixa)"
