# T-M09-marge-pantalla · Pantalla del marge d'una activitat (sense obrir)

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 21/11/2026 09:03 | (vegeu la PR) | 3 noves; 1 e2e | [A comprovar] |

**En tres línies:** el tresorer (i el responsable de cursos i sortides, per a les seves activitats) ja té preparada la pantalla del marge d'una activitat: el previst, el real que es congelaria, el congelat amb els ajustos posteriors, els costos previstos i el botó per tancar-la amb els motius que ho impedeixen. Encara no surt al menú.

## Què s'ha fet
- `apps/margins/admin_urls.py`, `apps/margins/views.py` i les plantilles `templates/margins/activity.html` i `_lines.html`.

## Decisions i perquè
- La junta hi té consulta (MG6): veu el marge però no els formularis.
- Els formularis només surten amb el permís; el servidor el torna a comprovar.

## Problemes trobats
Cap.

## Com se sap que funciona
`apps/margins/tests/test_views.py` (previst i cost previst, motius i tancament amb el marge congelat, per objecte i per rol) i `apps/core/tests/e2e/test_marge_activitat.py` (captures a 1280, 390 i 320 px, mirades).

## Termes nous
Cap.
