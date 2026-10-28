# 055 — Valors configurables: peça comuna d'ajustos a la 00 i addendes al 01, 05a i 05b

- **Data:** 28/10/2026
- **Estat:** Acceptada. Aplica la regla general de [valors de negoci](../planning.md#regles) als mòduls aprovats amb **addendes**, sense canviar-ne cap regla. Blocs al pla: [peça comuna](../planning.md#valors-configurables-055), [M01-addenda-055](../planning.md#M01-addenda-055), [M05a-addenda-055](../planning.md#M05a-addenda-055) i [M05b-addenda-055](../planning.md#M05b-addenda-055). La spec 00 no s'edita.

## Context
- La regla general diu que els valors de negoci (preus, dies d'avís, llindars, textos d'ajuda) són dades editables des de l'app, i no codi ni configuració tècnica.
- L'[apèndix de valors configurables](../planning.md#valors-configurables) (VC-01 a VC-44) mostra que alguns valors dels mòduls aprovats només són al text o no estan definits, i que els `PaymentSettings` del 05b no tenen pantalla.
- Els mòduls 01, 04, 05a i 05b estan aprovats i no s'editen. Els canvis s'hi afegeixen com a addenda, igual que amb les decisions 049 a 054.

## Alternatives
- Deixar els valors al codi o en variables d'entorn: cada canvi passaria per informàtica i un desplegament, sense registre de negoci.
- Que cada mòdul es faci el seu model d'ajustos: el registre, els rangs i la data d'entrada en vigor quedarien repetits i diferents.
- **Una peça comuna d'ajustos a la 00 i una pantalla d'ajustos per mòdul que la fa servir.**

## Decisió
1. **Peça comuna d'ajustos a la 00.** Cada valor té: valor inicial, rang vàlid, rol que el canvia, registre (qui, quan, valor anterior, nota) i, si afecta diners, data d'entrada en vigor. Un canvi no toca el que ja s'ha demanat o cobrat. Els mòduls llegeixen els valors amb un servei, mai amb un valor escrit al codi. Detall: [peça comuna](../planning.md#valors-configurables-055) (T-AJ-01 i T-AJ-02).
2. **01:** pantalla d'ajustos (T-M01-32) amb VC-01 (la quota guanya data d'entrada en vigor), VC-02, VC-03 i VC-04 ([addenda](../planning.md#M01-addenda-055)).
3. **04:** cap valor nou; els departaments i els comptes ja són dades (VC-08). Sense tasca nova.
4. **05a:** pantalla d'ajustos (T-M05a-22) amb VC-11 ([addenda](../planning.md#M05a-addenda-055)).
5. **05b:** pantalla per als `PaymentSettings` que ja existeixen (T-M05b-22), amb VC-16, VC-17 i VC-18. No canvia cap valor inicial ni cap regla ([addenda](../planning.md#M05b-addenda-055)).
6. **Es queden com estan** (codi o entorn): VC-05, 06, 07, 09, 10, 12, 13, 15 i 19 (seguretat, regles, formats d'integritat i secrets).
7. **Condició a), avís dels canvis de diners.** Tot canvi d'un valor que afecta diners (quotes, preus, tarifes, recàrrecs, comissions), en qualsevol mòdul, envia un correu al tresorer i a la junta amb el valor anterior, el valor nou, qui l'ha canviat, la nota i la data d'entrada en vigor. El correu és un avís: el canvi s'aplica igualment i no cal cap segona aprovació (un sol tresorer, sense doble aprovació). Si algun import ha de ser «només amb ratificació» de la junta: [A validar: junta].
8. **Condició b), durada del període.** Hi ha una prova que, quan es canvia la durada del període (VC-32, mòdul 09), el període nou comença l'endemà del darrer període existent, sense forats ni solapaments. La prova és a la tasca d'ajustos del 09 (T-M09-26).

## Conseqüències
- Tasques noves: T-AJ-01 i T-AJ-02 (peça comuna), T-M01-32, T-M05a-22 i T-M05b-22. Les pantalles d'ajustos dels mòduls escrits (T-M02-28, T-M03-22, T-M09-26 i T-M06-20) depenen de la peça comuna.
- La columna «Canvi» de l'apèndix passa de «Proposta 055» a «055».
- Preguntes noves per a la junta: quins imports, si n'hi ha cap, només es poden canviar amb ratificació; i qui forma la llista de destinataris de la junta mentre el rol Junta no estigui validat (P-04).

## Fonts
- Aprovació del responsable del projecte, 28/10/2026 (aprovació de la proposta de l'apèndix, amb les condicions a i b)
- [`planning.md`, apèndix de valors configurables](../planning.md#valors-configurables)
