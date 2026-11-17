# Estat de la fase 1 sense «feta en part» (§2.5 del pla d'acceleració)

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 17/11/2026 | cd0b904e | cap prova nova (només documentació); la línia cronològica llegeix l'estat sense cap fila no vàlida | [A comprovar] |

**En tres línies:** l'estat del 00, el 01, el 04, el 05a i el 05b ja només fa servir quatre estats: per fer, en curs, feta i bloquejada. Cada tasca que tenia una part feta i una part pendent s'ha partit: la part feta és «feta» i el que queda és una tasca nova amb el seu bloqueig. Moltes notes de «Falta» eren velles: la feina ja era a master.

## Què s'ha fet
- Comprovades amb el codi i les proves de master les files que no eren «feta» (uns 85), segons el [§2.5 del pla d'acceleració](../plans/pla-acceleracio.md) i el [README de l'estat](../estat/README.md).
- «Implementada, pendent de validació», «feta, pendent de revisió» i «esborrany»: «feta», amb «Pendent de validació del propietari» o «Esborrany pendent de revisió del tresorer» a la nota, i les PR de master.
- Files noves per al que queda: per exemple T-M04-12e (casar a mà), T-M04-13b, T-M05a-10b, T-M05a-13c, T-M05b-16b, T-M05b-22c i, bloquejades, E4b (servidor), T-M05b-19b (portes del nivell 2) i les del 01 que esperen tercers.
- Les tres tasques aturades de la targeta guardada (T-M05a-23, T-M05a-26 i T-M05b-24) passen a «bloquejada» pel proveïdor real; la T-M01-31, pel mòdul 06.

## Decisions i perquè
- El que es basa en una pregunta oberta amb opció per defecte queda «per fer» (la pregunta no atura el codi, 089); «bloquejada» només quan cal algú o alguna cosa de fora (junta, tresorer, servidor, proveïdor real, dispositius reals).
- El que no s'ha pogut comprovar queda escrit amb [A comprovar], sense inventar cap pregunta nova.

## Problemes trobats
- Notes velles: el permís A5, la revocació des de l'administració (A6), la pantalla de remeses (B3), el permís d'edició de la VC-16, el lector pain.002, les entrades al menú de tresoreria i pagaments i el segell «Anul·lat» del rebut ja eren a master.

## Com se sap que funciona
- Cap fila de `docs/estat/` del 00 al 05b amb un estat fora dels quatre.
- `tools/linia-cronologica/generate.py --ref HEAD`: llegeix tots els fitxers sense cap «fila no vàlida».

## Evidències
- Sortida del generador · commit cd0b904e · executada el 17/11/2026 en local: 286 tasques, 93 decisions, 199 pendents, cap fila no vàlida.
