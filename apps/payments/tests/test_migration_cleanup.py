"""Les proves que desfan i tornen a fer migracions dels pagaments no esborren les dades de les
migracions (rols, matriu de permisos, ajustos) amb la neteja de `CommittedDataTestCase`: en
refer-les, es tornen a crear amb claus noves, i la neteja esborra les claus noves. Les proves que
venien després es quedaven sense permisos ni ajustos segons l'ordre (com a la PR #434)."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.core.models import Person
from conftest import CommittedDataTestCase

VERSIONS = "core_permissionmatrixversion"


def row_counts(tables):
    with connection.cursor() as cursor:
        counts = {}
        for table, _column in tables:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')  # noqa: S608
            counts[table] = cursor.fetchone()[0]
    return counts


class TestMigrationDataSurvivesTheCleanup(CommittedDataTestCase):
    def test_undoing_the_payments_migrations_keeps_the_matrix_and_the_settings(self):
        before = row_counts(self._tables)
        Person.objects.create(first_name="Prova", origin="in_person")  # i aquesta sí que s'esborra
        leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
        try:
            # El que fa TestMigrationIsReversible: desfà també el nucli de la 0044 en endavant.
            MigrationExecutor(connection).migrate([("payments", "0001_provider_event")])
        finally:
            self.migrate_back(leaves)
        self._fixture_teardown()  # la neteja del final de la prova
        after = row_counts(self._tables)
        # Historial: dues migracions no esborren la seva versió de la matriu en desfer-se i, en
        # refer-les, n'afegeixen una altra. Sobra una fila d'historial; no en falta cap.
        assert after.pop(VERSIONS) >= before.pop(VERSIONS)
        assert {t: (before[t], after[t]) for t in before if before[t] != after[t]} == {}
