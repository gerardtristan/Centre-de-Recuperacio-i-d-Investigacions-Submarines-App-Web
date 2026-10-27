# 045 — Corregir una transferència conciliada amb el càrrec equivocat

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol QT-04 de la spec 04). Amplia la RN-67 de la spec 00 amb una transició nova per a un sol cas; la spec 00 no s'edita (s'hi aplica aquesta decisió).

## Context
La RN-67 de la spec 00 no admet «pagat → pendent». Si el tresorer concilia una transferència amb el càrrec d'una altra persona, el càrrec equivocat queda «pagat» i no es pot corregir.

## Alternatives
- Fer una devolució i tornar a cobrar: mou diners que no s'han de moure.
- **Permetre «pagat → pendent» només per a aquest cas.**

## Decisió
- Transició nova **«pagat → pendent»**, permesa **només** quan el càrrec va passar a pagat per la **conciliació d'una transferència** (spec 04, CA-T10.1).
- Cal **motiu obligatori**; queda al **registre d'activitat** (qui, quan, valor anterior).
- En fer-la: la conciliació es desfà, la línia de l'extracte torna a «pendent», l'ingrés es compensa amb un contramoviment i el pagament queda anul·lat amb el mateix motiu. Res s'esborra.
- Només la pot fer el tresorer (o l'administrador).
- Per a la resta de mètodes (targeta, Bizum, domiciliació) no s'aplica: es corregeix amb una devolució.

## Conseqüències
- La spec 04 hi afegeix els criteris i les proves (CA-T10.4, CA-T10.5).
- Si la persona correcta ja havia rebut el rebut, el rebut equivocat s'anul·la i se n'emet un de nou.

## Fonts
- Aprovació de la spec 04 amb canvis, comunicada per l'equip el 27/10/2026
