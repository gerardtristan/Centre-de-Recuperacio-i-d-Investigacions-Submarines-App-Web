# 054 — Addenda a la 052: versió dels esdeveniments de llicència i comprovació diària

- **Data:** 27/10/2026
- **Estat:** Acceptada com a **addenda de la [052](052-llicencia-font-unica-al-06.md)**, que no s'edita. No canvia cap regla existent del 01. Bloc al pla: [M01-addenda-054](../planning.md#M01-addenda-054).

## Context
- La cua de la 049 pot lliurar els esdeveniments de llicència en un ordre diferent del que es van emetre, o reintentar-ne un d'antic.
- Si un lliurament falla del tot, la còpia de lectura del 01 es pot quedar diferent del 06 sense que ningú ho vegi.

## Decisió
1. **Marca de versió.** Cada llicència del 06 té un comptador `version` que puja en 1 a cada canvi, dins la mateixa transacció. Cada esdeveniment porta `version` i `occurred_at` (data i hora en què es va emetre).
2. El 01 guarda la versió a la còpia (`source_version`) i **ignora un esdeveniment amb una versió igual o més vella** que la que ja té. Compara la versió, no l'hora, perquè un comptador no depèn del rellotge.
3. **Comprovació diària.** Un cop al dia, el 01 compara la seva còpia amb les dades del 06 i **corregeix les diferències**: crea la fila que falta, actualitza la que és diferent i marca la cancel·lada. Res s'esborra. Si una fila del 01 apunta a una llicència que el 06 no té, no la toca i la deixa a la llista per revisar.
4. **Registre.** Cada correcció queda al registre d'activitat amb el valor anterior i l'actor «comprovació diària». La tasca guarda quantes files ha revisat i quantes ha corregit.
5. **Sense cicle.** El 01 no importa codi del 06. El 06, que ja depèn del 01, li registra en arrencar una funció de lectura (`members.register_licence_source`). Si no hi ha cap font registrada (abans del 06), la comprovació no fa res.
6. Tot s'afegeix a la tasca T-M01-31. Al 06, la T-M06-15 hi afegeix la versió i el registre de la font.

## Conseqüències
- La còpia del 01 queda bé encara que la cua perdi o desordeni un esdeveniment, com a molt un dia més tard.
- Preguntes noves per a informàtica: a quina hora corre la comprovació i qui rep l'avís si troba diferències.

## Fonts
- Aprovació del responsable del projecte, 27/10/2026 (punt 2b de les aprovacions)
- [`planning.md`, M01-addenda-054](../planning.md#M01-addenda-054)
