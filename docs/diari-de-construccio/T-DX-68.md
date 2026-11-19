# T-DX-68 · Escalfament de les proves e2e (P-313)

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 19/11/2026 02:14 | fe7018ff | 1 e2e nova; fumada i logotip: 9 passen, 4 se salten | [A comprovar] (PR #255) |

**En tres línies:** la primera prova e2e d'una tanda fallava de vegades per temps en obrir `/entrar/`. El propietari va dir que és un error (19/11/2026). Ara el `conftest` fa una visita d'escalfament abans de la primera prova amb el servidor en viu, una sola vegada per tanda.

## Què s'ha fet
- `apps/core/tests/e2e/test_smoke.py`: `test_first_load_is_warm`, la prova que reprodueix l'error. Comprova que, quan arriba la primera prova, el servidor ja ha servit `/entrar/` una vegada. Sense l'arreglo falla.
- `apps/core/tests/e2e/conftest.py`: `_warm_first_load`, una visita a `/entrar/` en un context del navegador a part, abans de la primera prova que fa servir `live_server`. Té un temps màxim de 120 s, només per a aquesta visita. Els temps de les proves no canvien i no hi ha reintents.
- `docs/decisions/pendents.md` i el tauler: la P-313 i la P-314 (opció A) passen a resoltes.
- Diari: les files de la T-DX-65 i la T-DX-67 sortien dues vegades a l'índex després dels rebases. Queda una fila de cadascuna, amb el commit de la tasca que hi ha a master (9e01e8d1 i 4cead49e).

## Decisions i perquè
- **La prova no mesura el temps.** La primera càrrega va trigar 9,3 s amb la memòria cau del disc buida i 0,3 s les següents. En repetir-la, la càrrega en fred ja era d'1 s, perquè el disc ja tenia els fitxers a la memòria cau. Un límit de temps hauria estat una prova que falla de tant en tant, que és justament el que es vol treure. Per això la prova comprova l'estat: que l'escalfament s'ha fet.
- **Escalfament amb el navegador, no amb una petició HTTP.** El cost en fred és del servidor (2,6 s per a l'HTML) i també dels fitxers estàtics i del navegador (1 s per a cada JavaScript). Una petició només amb l'HTML no ho cobreix tot.
- **Dins la primera prova, no a l'inici de la sessió.** El servidor en viu consulta la base de dades, i a l'inici de la sessió pytest-django encara no hi deixa entrar.

## Problemes trobats
- La primera versió de la prova, amb un límit de 5 s, va fallar la primera vegada i va passar les dues següents sense l'arreglo. Es va canviar per la comprovació d'estat.

## Com se sap que funciona
- `test_first_load_is_warm` sola: falla sense l'arreglo (`_warmed` no existeix) i passa amb l'arreglo.
- Fumada i logotip: 9 passen i 4 se salten (Firefox i WebKit, com sempre a la màquina local).

## Comprovació §15.5
- Cap pantalla tocada: no calen captures ni axe.
