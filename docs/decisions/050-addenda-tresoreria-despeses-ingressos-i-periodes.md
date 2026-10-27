# 050 — Addenda de la 04: despeses, altres ingressos, anul·lació i bloqueig de període tancat

- **Data:** 27/10/2026
- **Estat:** Acceptada com a **addenda** del [M04](../planning.md#M04-addenda-050) de `planning.md`, que ja estava aprovat. **No canvia cap regla existent de la 04.** La spec 04 arxivada no s'edita.

## Context
- El mòdul 09 (marge, despeses, ajuts i facturació) ha de registrar despeses amb factura i ingressos que no són càrrecs (ajuts, patrocinis, donatius) com a moviments de la 04.
- La 04 aprovada no té cap tipus de moviment per a aquestes dues coses, no ofereix cap servei per anul·lar un moviment des d'un altre mòdul (només la pantalla de P-M04-C) i no sap res dels períodes tancats del 09 ([M09-2](../planning.md#M09-2-dependencies)).

## Alternatives
- Que el 09 escrigui directament als models de la 04: trenca la regla «una app no escriu als models d'una altra».
- Que el 09 guardi les despeses fora de la 04: la tresoreria deixaria de tenir tots els diners que entren i surten.
- **Tres peces noves a la 04, com a addenda, sense tocar les regles que ja hi ha.**

## Decisió
1. **Tipus de moviment nous:** `expense` (sortida amb factura, la crea el 09) i `other_income` (entrada que no és un càrrec), amb els serveis `treasury.record_expense` i `treasury.record_other_income`. Són moviments com els altres: immutables, amb departament i centre de cost, conciliables i al registre d'activitat (RN-T05, RN-T07, RN-T13).
2. **Servei d'anul·lació:** `treasury.reverse(movement, reason, actor)` crea el contramoviment de RN-T07 (estat derivat de RN-T25). El motiu i l'usuari són obligatoris i queden al registre d'activitat.
3. **Bloqueig de període tancat:** punt d'extensió `treasury.register_movement_guard(guard)`. El 09 hi registra el seu bloqueig, i la 04 no depèn del 09.
   - El bloqueig s'aplica **només als moviments nous**: la 04 rebutja un moviment nou (també un contramoviment) amb data de valor dins un període tancat. Els moviments que ja hi són no canvien mai.
   - **Corregir un període tancat** és fer una anul·lació i un moviment nou, tots dos amb data de valor dins el període obert. El moviment original es queda al període tancat.
4. Les peces s'afegeixen al M04 en un bloc d'addenda ([M04-addenda-050](../planning.md#M04-addenda-050)) amb la tasca T-M04-20. Cap fila aprovada del M04 s'edita.

## Conseqüències
- El 09 es pot construir sobre la 04 sense escriure als seus models (T-M09-02 passa a dependre de T-M04-20).
- Les regles RN-M09-11 i RN-M09-16 del 09 s'ajusten a aquest bloqueig: un període tancat no es toca, i la correcció va sempre al període obert.
- La conciliació ja casa moviments (`matched_movements`), per tant les despeses i els altres ingressos es concilien sense cap canvi.

## Fonts
- Aprovació del responsable del projecte, 27/10/2026 (punt 2 de les aprovacions), amb les condicions recollides al punt 3 de la decisió
- [`planning.md`, M09-14](../planning.md#M09-14-aprovar)
