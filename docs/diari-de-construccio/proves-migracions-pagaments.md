# Proves · Desfer migracions dels pagaments sense perdre les dades de les migracions

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 21/11/2026 09:57 | (vegeu la PR) | 1 nova | [A comprovar] |

**En tres línies:** cinc proves dels pagaments desfan i tornen a fer migracions per comprovar-les. En tornar-les a fer, la matriu de permisos, les versions de la matriu i els ajustos es tornaven a crear amb claus noves, i la neteja del final de la prova els esborrava. Les proves que venien després es quedaven sense una bona part dels permisos i dels ajustos, segons l'ordre (el mateix problema que la PR #434 al nucli).

## Què s'ha fet
- `conftest.py`: `CommittedDataTestCase.migrate_back(targets)` torna a aplicar les migracions i apunta les files que creen mentre ho fa; la neteja no les esborra, i sí les que la prova ha creat abans o després.
- Les cinc proves (`test_attempts`, `test_review_close` dues, `test_settings` i `test_saved_card_charge`) fan servir `migrate_back`.
- `apps/payments/tests/test_migration_cleanup.py`: la prova que ho reprodueix.

## Decisions i perquè
- No n'hi ha prou amb una foto nova després de refer les migracions (la correcció de la #434): quatre de les cinc proves creen dades abans de desfer-les, i una foto nova les deixaria a la base per a les proves següents. Per això es guarda només el tram de claus que creen les migracions en tornar-se a aplicar.
- Es corregeixen les proves que causen el problema, no les que el patien.

## Problemes trobats
Abans: desfer els pagaments fins a la 0001 (com fa `TestMigrationIsReversible`) i fer la neteja deixava 84 de 389 cel·les de la matriu, 36 de 47 ajustos i 18 de 40 versions de la matriu. Després: les mateixes files que abans de la prova, amb dues versions de la matriu de més (dues migracions no esborren la seva versió en desfer-se i n'afegeixen una altra en refer-se; és historial i no hi falta res).

## Com se sap que funciona
`TestMigrationDataSurvivesTheCleanup` compta les files de cada taula abans de la prova i després de la neteja (amb una persona creada abans de desfer les migracions, que sí que s'ha d'esborrar), i les cinc proves que desfan migracions passen igual.

## Termes nous
Cap.
