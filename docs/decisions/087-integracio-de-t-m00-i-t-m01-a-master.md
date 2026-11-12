# 087. Integració de T-M00 i T-M01 a la branca principal

- **Data:** 12/11/2026
- **Estat:** Acceptada i executada (responsable del projecte, 12/11/2026)
- **Substitueix:** la instrucció anterior de no fusionar la PR #7 ni modificar `master`, només per a aquesta integració.

## Decisió

Tota la feina de T-M00 i T-M01 feta i verificada als plans nocturns s'integra a la branca principal, amb push sense force, CI verd al cap final i una fusió que conserva els commits. No s'hi integra el mòdul 02 (`feature/t-m02-activitats`), ni els canvis locals de la carpeta del responsable, ni feina d'altres sessions.

## Què s'ha comprovat abans

- **Branca principal:** `master` (la branca per defecte del remot), sense proteccions ni comprovacions obligatòries.
- **On era la feina:** tota a `feature/night-2026-11-11` (PR #7). Contenia per ascendència la PR #4 (`feature/fase-1-fundacio-i-socis`), `feature/t-m00-verificacion`, `feature/night-2026-11-10`, les branques `night/2026-11-09/*`, `integracio/2026-11-09` i `night/2026-11-11-a11y`.
- **Worktrees auxiliars** (`correu`, `guest`, `rgpd`, `simp` i `ui`): integrats per contingut, amb les migracions renumerades. Tots els seus fitxers són a la branca; les cinc proves que no hi són amb el mateix nom van ser substituïdes per decisions posteriors (079, 081 i 085).
- **Cap commit de T-M00 o T-M01 era només en local.**
- **Desplegaments:** el repositori no té cap desplegament de la plataforma ni cap webhook. Una fusió a `master` només torna a generar la línia cronològica xifrada de GitHub Pages, com ja passava a cada push.

## Com s'ha fet

1. `master` (`b0ada4b`, amb la línia cronològica de la PR #6) fusionat dins `night/2026-11-11`: commit `ad80447`. Un sol conflicte, a `.gitignore`, resolt conservant les línies de les dues bandes.
2. Verificació completa local en verd a `ad80447` (4030 proves i 42 e2e) i gitleaks net sobre els 361 commits del rang, sense cap excepció nova (decisions 078 i 083).
3. Push sense force i PR #7 redirigida a `master`. CI verd a `ad80447`: push (43218385051) i PR contra `master` (43219374839), amb proves, e2e, captures i secrets.
4. PR #7 fusionada amb un commit de fusió: `c8d7f66`. L'arbre de `master` és idèntic al verificat. CI de `master` verd (43220357195).
5. La PR #4 no s'ha fusionat a part: el seu cap (`bbcd7eb`) ja era dins, i GitHub l'ha marcada com a fusionada.

## Estats de les tasques

La fusió no canvia cap estat. Ja estaven posats amb la regla de la 083 i la 085. Continuen obertes, amb el motiu al pla: T-AJ-01, T-M01-16, T-M01-18, T-M01-19, T-M01-21, T-M01-22, T-M01-25, T-M01-28, T-M01-39, T-M01-42, T-M01-45 i T-RP-02 (funcionalitat, dependències, decisions externes o proves manuals pendents). Cap d'elles té pendent només disseny o wireframe.

## Què queda fora

- `feature/t-m02-activitats`: continua separada, ara amb `master` (`c8d7f66`) com a base, per fusió.
- `backup/master-local-2026-10-31` i el `stash`: còpies antigues, no són feina dels plans nocturns.
- `claude/project-thread-2z1nn1` (proposta al client) i `claude/project-thread-r2yv97`: alienes a T-M00 i T-M01.
- No s'ha esborrat cap branca ni cap worktree.
