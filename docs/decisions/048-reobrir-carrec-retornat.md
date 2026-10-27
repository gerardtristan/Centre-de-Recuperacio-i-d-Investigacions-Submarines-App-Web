# 048 — Reobrir un càrrec retornat: transició «retornat → pendent»

- **Data:** 27/10/2026
- **Estat:** Acceptada (aprova la regla RN-M05b-14 de [`planning.md`](../planning.md#M05b-7-regles)). Amplia la RN-67 de la spec 00 amb una transició nova; la spec 00 no s'edita (s'hi aplica aquesta decisió, com la [045](045-correccio-transferencia-conciliada-per-error.md)).

## Context
- La RN-67 de la spec 00 admet «pagat → retornat», però no diu què passa després: ho deixa a la 05b (Q-22).
- Amb les remeses SEPA, un rebut retornat s'ha de poder tornar a cobrar (reintent controlat) o pagar d'una altra manera (alternativa de pagament), tal com demana la [017](017-pagaments-metodes-i-domiciliacions.md).
- Crear un càrrec nou per a la mateixa quota trencaria la regla «una quota per soci i període» del mòdul 01.

## Alternatives
- Deixar «retornat» com a estat final i crear un càrrec nou: duplica la quota i complica el seguiment.
- **Permetre «retornat → pendent»** quan es reintenta o s'ofereix l'alternativa.

## Decisió
- Transició nova **«retornat → pendent»**, permesa **només** quan el tresorer confirma un **reintent** a una remesa posterior o envia l'**alternativa de pagament** (targeta, Bizum o transferència).
- **Motiu obligatori** i **registre d'activitat** (qui, quan, valor anterior).
- El retorn i la seva comissió ja són a la tresoreria i **no es toquen**; el pagament nou genera un ingrés nou (una sola vegada per pagament, RN-T09).
- El nombre màxim d'intents per domiciliació i què es fa segons el motiu del retorn són a RN-M05b-15 (validada pel tresorer).
- Només la pot fer el tresorer o el procés que aplica la regla de reintent confirmada pel tresorer.

## Conseqüències
- La 00 ha d'oferir el servei `charges.reopen_returned(charge, reason)` (tasca T-M05b-01).
- Mentre el càrrec torna a ser «pendent», el carnet del soci segueix RN-M01-18 i RN-M05b-18.

## Fonts
- Aprovació de la secció M05b de `planning.md`, comunicada pel responsable del projecte el 27/10/2026
