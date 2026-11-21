# Proves · Les dades de les migracions sobreviuen a la neteja

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 21/11/2026 09:00 | (vegeu la PR) | 1 nova | [A comprovar] |

**En tres línies:** una prova del nucli desfà i torna a fer les migracions per comprovar que es poden desfer. En refer-les, els rols i la matriu de permisos es tornaven a crear amb identificadors nous, i la neteja del final de la prova els esborrava. Les proves de concurrència que venien després (les inscripcions del 02) es quedaven sense permisos i fallaven amb «no trobat» segons l'ordre.

## Què s'ha fet
- `apps/core/tests/test_imports.py`: després de refer les migracions, la prova torna a fer la foto de les claus (`committed_snapshot`), i una prova nova comprova que la neteja no esborra la matriu.

## Decisions i perquè
- Es corregeix la prova que causa el problema, no la que en patia: la de concurrència no se salta.

## Problemes trobats
Es reprodueix amb `pytest apps/core/tests/test_imports.py::TestMigrationsAreReversible apps/activities/tests/test_enrolment.py::TestConcurrentEnrolments` (abans: 2 fallades; després: 4 en verd). Altres proves que desfan migracions (`apps/payments`) poden tenir el mateix risc amb les seves dades.

## Com se sap que funciona
`TestMigrationsAreReversible.test_migration_data_survives_the_cleanup` i la seqüència de dalt.

## Termes nous
Cap.
