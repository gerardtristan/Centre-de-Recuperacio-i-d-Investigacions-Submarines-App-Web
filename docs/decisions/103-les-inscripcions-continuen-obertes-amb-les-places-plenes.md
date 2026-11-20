# 103. Les inscripcions continuen obertes amb les places plenes

- **Data:** 12/11/2026
- **Número:** 103 (era la 088 de la branca aparcada `feature/t-m02-activitats`; renumerada el 20/11/2026 perquè la 088 de `master` és una altra decisió)
- **Estat:** Acceptada (responsable del projecte, 12/11/2026)
- **Completa:** el pla del mòdul 02 ([processos](../planning.md#M02-5-processos), taula d'estats i P-M02-D pas 5; [regles](../planning.md#M02-7-regles), RN-M02-07 i RN-M02-09; [tasques](../planning.md#M02-10-tasques), T-M02-12). Resol una contradicció; no canvia cap regla.

## Context

El pla deia dues coses diferents sobre què passa quan s'omplen les places d'una activitat:

- La taula d'estats deia que el sistema passa l'activitat a «tancada a inscripcions» per «places plenes o data límit».
- El pas 5 de P-M02-D deia que, amb les places plenes, l'activitat continua oberta amb llista d'espera fins a la data límit. RN-M02-09 i CA-M02-08 també donen per fet que qui arriba amb les places plenes entra a la llista d'espera.

La frase de la taula venia del document de funcionalitats («Tancar inscripcions quan s'omplen les places o arriba la data límit»). La T-M02-12 no es podia implementar sense saber quina de les dues valia.

## Alternatives

- **A.** Les inscripcions continuen obertes fins a la data límit encara que s'hagin ocupat totes les places. Qui s'hi apunta sense places lliures va a la llista d'espera.
- **B.** Omplir les places tanca les inscripcions. Ningú més s'hi pot apuntar, i la llista d'espera només es podria omplir si el responsable les reobre.

## Decisió

**Opció A.**

- Omplir les places no provoca, per si sol, el tancament de les inscripcions.
- Són tres coses diferents: les **places disponibles** (un recompte, RN-M02-07), la **llista d'espera** (RN-M02-09) i l'**estat** de l'activitat, oberta o tancada a inscripcions (RN-M02-02).
- Les inscripcions es tanquen com fins ara: el sistema, quan arriba la data límit, o el responsable, a mà.
- Aquesta decisió no autoritza cap excepció per inscriure's després del tancament: ni inscripcions noves ni entrades noves a la llista d'espera.

## Conseqüències

- **Pla:** la taula d'estats ja no diu «places plenes»; el pas 5 de P-M02-D hi afegeix el tancament a mà i que després del tancament ningú no s'hi pot inscriure. Criteri nou, **CA-M02-40**, amb la seva prova a la T-M02-12.
- **Mapa de la plataforma** (`design/mapa-plataforma.html`): la frase del procés de sortides s'ha corregit.
- **Document de funcionalitats** (`docs/funcionalitats-processos/`, PDF i DOCX): conserva la frase antiga al procés de sortides. No s'ha regenerat. Mana el pla, que és la font única de l'especificació (decisió 047); queda per corregir quan se'n faci una versió nova.
- **Codi:** `states.advance_by_clock` ja només tancava per la data límit; no hi ha res a desfer. El control de places i la llista d'espera són de la T-M02-12.
- La T-M02-12 ja no espera cap resposta del responsable.
