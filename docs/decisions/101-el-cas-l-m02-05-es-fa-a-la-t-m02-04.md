# 101. El cas L-M02-05 es fa a la T-M02-04

- **Data:** 12/11/2026
- **Número:** 101 (era la 086 de la branca aparcada `feature/t-m02-activitats`; renumerada el 20/11/2026 perquè la 086 de `master` és una altra decisió)
- **Estat:** Acceptada (responsable del projecte, 12/11/2026)
- **Completa:** el pla del mòdul 02 ([casos límit](../planning.md#M02-9-criteris), L-M02-05; [tasques](../planning.md#M02-10-tasques), T-M02-04). No canvia cap regla.

## Context

El cas límit L-M02-05 diu que, si un instructor deixa de tenir el rol, les seves sessions futures queden sense instructor i surten marcades al responsable. En construir la T-M02-03 es va veure que cap tasca del pla el recollia: la sessió conservava l'instructor fins que algú el canviava a mà.

## Alternatives

- **A.** Fer-ho a la T-M02-04 (permisos per objecte), que ja tracta «les seves sessions».
- **B.** Fer-ho a la T-M02-06, amb la pantalla on el responsable ho veuria marcat.
- **C.** Una tasca nova al final del mòdul.

## Decisió

**Opció A.** L-M02-05 s'implementa a la **T-M02-04**, perquè el permís i la neteja vagin junts.

## Conseqüències

- La T-M02-04 hi afegeix: quan un compte perd el rol d'instructor, la persona surt de les sessions futures on feia classe, amb una entrada al registre per sessió; una sessió futura sense cap instructor es pot llistar com a «sense instructor».
- Mostrar la marca al responsable és de la pantalla de l'activitat (T-M02-06), que llegeix aquesta llista.
- Les sessions passades no es toquen: conserven qui hi va fer classe.
- No queda cap pregunta oberta sobre aquest punt.
