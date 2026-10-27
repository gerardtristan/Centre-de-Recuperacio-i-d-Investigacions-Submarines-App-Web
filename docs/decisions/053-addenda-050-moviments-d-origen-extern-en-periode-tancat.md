# 053 — Addenda a la 050: moviments d'origen extern i període tancat

- **Data:** 27/10/2026
- **Estat:** Acceptada com a **addenda de la [050](050-addenda-tresoreria-despeses-ingressos-i-periodes.md)**, que no s'edita. Precisa l'abast del bloqueig de període tancat (RN-T28) **sense canviar cap altra regla**. Bloc al pla: [M04-addenda-053](../planning.md#M04-addenda-053).

## Context
- La 050 diu que la 04 rebutja **qualsevol** moviment nou amb data de valor dins un període tancat.
- Molts moviments no els decideix el club: un pagament confirmat pel proveïdor (05b), una devolució, un retorn, una comissió del banc, una remesa o una liquidació poden arribar quan el període de la seva data ja és tancat.
- Si la 04 els rebutgés, el club perdria diners de la tresoreria i el 05b no podria confirmar un cobrament (la notificació s'ha de processar sempre, de manera idempotent).

## Decisió
1. **El bloqueig s'aplica només als moviments que crea el 09:** `expense`, `other_income` i les **anul·lacions manuals** (les que demana una persona amb `treasury.reverse`, des del 09 o des de la pantalla de P-M04-C). Amb data dins un període tancat, es rebutgen (`PeriodClosed`), com diu la 050.
2. **Els moviments d'origen extern no es rebutgen mai.** Són tots els altres: els que creen `record_income`, `record_fee`, `record_refund`, `record_return` i `record_settlement` (pagaments de la 05b, devolucions, retorns, comissions del banc i del proveïdor, remeses i liquidacions), també els que es creen en conciliar l'extracte.
3. Si la data de valor d'un moviment d'origen extern és dins un període tancat, **entra al període obert**: la seva data de valor passa a ser el primer dia del període obert i la data real es guarda al camp nou `original_value_date` (buit en tots els altres moviments).
4. La conciliació de l'extracte compara amb `original_value_date` quan el camp és ple.
5. El punt d'extensió de la 050 es precisa: el bloqueig registrat (`guard`) diu fins a quina data és tancat el període, i la 04 decideix segons l'origen del moviment (rebutjar o portar-lo al període obert). La 04 continua sense dependre del 09.
6. Lectura triada: els traspassos i els arqueigs de caixa no els crea el 09, per tant segueixen el punt 3. Si la gestoria hi veu un problema, es revisa ([preguntes de la gestoria](../planning.md#preguntes-gestoria)).

## Conseqüències
- La tasca T-M04-20 inclou el camp i la regla nova. Les regles RN-M09-11 i RN-M09-16 del 09 s'ajusten.
- Un moviment que entra tard compta al període obert, com ja diu RN-M09-07 per a les desviacions posteriors al tancament.
- Preguntes noves per a la gestoria (tractament comptable de la data) i per a informàtica (quan s'importa l'extracte).

## Fonts
- Aprovació del responsable del projecte, 27/10/2026 (punt 2a de les aprovacions)
- [`planning.md`, M04-addenda-053](../planning.md#M04-addenda-053)
