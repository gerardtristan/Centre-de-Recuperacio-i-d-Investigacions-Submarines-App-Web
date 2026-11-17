# T-B8 · Auditoria d'accessibilitat (axe) de la tresoreria i del 05b

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 17/11/2026 | 7dea85d9 | 5 noves al navegador | [A comprovar] |

**En tres línies:** les pantalles de la tresoreria i dels cobraments ja passen la mateixa revisió automàtica d'accessibilitat que les del soci i del mandat. Cap no té cap problema greu, en clar ni en fosc, a l'ordinador ni al mòbil. Ho demanava la revisió de les portes del nivell 2 (punt B8).

## Què s'ha fet
- `test_accessibilitat_tresoreria.py`: 15 pantalles i estats de la 04 (comptes, moviments, anul·lar, traspàs, arqueig, liquidacions, conciliació amb una línia proposada, «a revisar» amb el formulari d'exclusió obert, extracte bancari importat i previsualització).
- `test_accessibilitat_05b.py`: 26 del 05b. Administració: pagaments i «a revisar», remeses (buida, previsualització, detall, enviada, abonament, llista), retornats (per decidir i fitxer del banc) i ajustos de pagaments. Soci: «Les meves quotes», pagament pendent, en curs, fallit, Bizum esperant i no confirmat, transferència, pagat, rebut i rebut anul·lat. I el convidat.
- Cada pantalla, a 1280 i 390 px, amb la funció `audit` de la T-M01-28: axe WCAG 2.0 a 2.2 A i AA en clar i en fosc, estructura, noms accessibles i recorregut amb el tabulador.
- Mapa del hook (`.claude/hooks/e2e_map.py`) i fila B8 de [les portes del nivell 2](../estat/portes-nivell-2.md).

## Decisions i perquè
- Es reutilitza `audit` de la 028 i els ajudants de dades de les proves existents: cap comprovació nova ni cap dada nova que mantenir.
- Les dues amplades (no les tres del mandat): a 320 px ja hi ha `review` a les proves de cada pantalla.
- El fitxer de la remesa es genera pel servei en lloc de descarregar-lo: la descàrrega ja la prova `test_remeses.py`.

## Problemes trobats
- Cap violació greu: no s'ha tocat cap plantilla ni cap estil.
- axe deixa per a revisió manual el contrast de les pestanyes de la barra inferior del mòbil (`.ramillete-pestanya`: no sap llegir el color `oklch` amb un component `none`), el del segell del rebut (`.rebut-segell`, superposat) i el de les icones decoratives. Queden per a la revisió de persona ([P-301](../decisions/pendents.md)).
- Una vegada, amb l'ordinador carregat, l'espera de «xarxa en repòs» abans d'axe va passar dels 30 s; a les execucions següents, no.

## Com se sap que funciona
Les cinc proves passen i desen l'informe de cada pantalla a `.e2e-captures/accessibilitat/` (`tresoreria.json`, `05b-*.json`); cada informe té el mateix nombre d'elements visitats amb el tabulador que d'elements que es poden activar.

## Evidències
- Sortida de proves · commit 7dea85d9 · executada el 17/11/2026 en local (PostgreSQL 16):
  ```
  $ pytest -m e2e apps/core/tests/e2e/test_accessibilitat_tresoreria.py apps/core/tests/e2e/test_accessibilitat_05b.py
  5 passed
  ```

## Termes nous
Cap.
