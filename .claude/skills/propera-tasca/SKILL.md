---
name: propera-tasca
description: Calcula l'apartat «Propera tasca» de l'informe final d'una tasca del pla C.R.I.S. (docs/planning.md), llegint només les taules de tasques del mòdul per àncora. Fes-la servir quan una tasca passa a «Feta» amb revisió d'una persona i CI en verd, o quan el responsable del projecte ho demana explícitament.
---

# Propera tasca

Regla de CLAUDE.md («Qualitat»): l'apartat només va a l'informe final quan la tasca passa a «**Feta**» i ja té la revisió d'una persona i el CI en verd, segons el «Feta quan» del pla. No va en informes intermedis, en tasques «Feta en part» ni en tasques aturades per una decisió. Si el responsable del projecte ho demana explícitament, es calcula sempre. **No es comença cap altra tasca sense confirmació.**

## 1. Llegir només el que cal (mai `docs/planning.md` sencer)

El fitxer té més de 6.000 línies. Treballa amb números de línia:

1. Àncores i línies: `grep -n '<a id="' docs/planning.md`. Cada secció va de la seva àncora fins a la següent.
2. Les seccions que toca la tasca del mòdul `MNN` (per exemple, `M01`):
   - taula principal: `MNN-10-tasques`;
   - addendes, en l'ordre del fitxer: `MNN-addenda-*`;
   - apèndixs comuns, al final: `valors-configurables-055` (T-AJ), `rols-i-permisos-059` (T-RP) i `ajustos-060-peces-00` (T-M00).
3. Només les files de tasques: `grep -nE '^\| *T-' docs/planning.md` i queda't amb les que cauen dins dels rangs del punt 2. Si una fila és llarga, llegeix-la amb `Read` i `offset`/`limit` d'una línia.
4. Per comprovar una dependència d'un altre mòdul, busca'n només la fila: `grep -nE '^\| *T-M04-03 ' docs/planning.md`.

## 1 bis. L'estat és a `docs/estat/` (decisió 089, D1)

Mentre l'interruptor D1 de `CLAUDE.md` sigui actiu, l'estat d'una tasca es llegeix de `docs/estat/<mòdul>.md` (`M00.md` porta també T-RP i T-AJ): `grep -nE '^\| *T-M04-' docs/estat/M04.md`. Quatre estats: per fer, en curs, feta i bloquejada. El pla es continua llegint per a l'ordre de les files i per a «Depèn de». Si una tasca no té fila a `docs/estat/`, val l'estat de la seva fila del pla. Amb D1 inactiu, s'ignora aquest apartat.

## 2. Criteri

1. **Recorregut:** la taula principal del mòdul, després les addendes en l'ordre del fitxer i, al final, els apèndixs comuns (T-RP, T-AJ, T-M00).
2. **Propera:** la primera fila del recorregut que no està «feta» i que té totes les dependències («Depèn de») «fetes». «En curs», «bloquejada» i «feta en part» compten com a no fetes; una tasca «bloquejada» no pot ser la propera.
3. **Font:** fitxer, línia i fila de la taula, i cada dependència comprovada amb el seu estat.
4. Les altres candidates vàlides es llisten com a informació, sense triar-ne cap.
5. **Contrast amb el diari:** si l'estat del pla i l'índex de `docs/diari-de-construccio/README.md` no coincideixen, es llisten totes les candidates amb el motiu i decideix el responsable del projecte. Si no es pot determinar amb seguretat, es diu.

## 3. Format a l'informe

```
## Propera tasca
T-MNN-XX — <títol curt> (docs/planning.md:<línia>)
Dependències: T-… Feta (línia …); T-… Feta (línia …)
Altres candidates vàlides (només informació): …
```
