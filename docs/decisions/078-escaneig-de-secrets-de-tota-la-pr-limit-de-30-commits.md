# 078 — Escaneig de secrets de tota la PR: el límit de 30 commits de l'acció de gitleaks

- **Data:** 10/11/2026
- **Estat:** Acceptada pel responsable del projecte el 10/11/2026 (opció G2 de l'informe del tall de la revisió de pantalles).
- **Abast:** canvia el pas «secrets» del CI per a les PR i esmena l'apartat «Comprovació» de la [077](077-tercera-excepcio-de-gitleaks-empremta-de-la-cita-a-la-076.md). No afegeix ni treu cap empremta.

## Context
- La PR #5 (en esborrany, de `feature/night-2026-11-10` cap a `master`, oberta i tancada el 10/11/2026 només per a l'escaneig; execució del CI 42900068604, verda a `dfa6517`) havia de posar a prova les empremtes de la 076 i la 077. Gitleaks només va revisar 30 commits dels 271 de la PR (de `0b9debb` a `9b69ff9`).
- **Causa:** a les PR, l'acció `gitleaks/gitleaks-action@v2` demana per l'API la llista de commits de la PR, en rep només la primera pàgina (30 commits) i revisa del primer al darrer d'aquesta pàgina. Una PR de més de 30 commits queda revisada en part, i el CI surt verd igualment.
- `6d871bd` i `a31d6b4`, els commits de les dues empremtes, quedaven fora del rang: no es van comprovar.
- La PR #4 (execució 42540425738, a `710b15f`) també va revisar només 28 commits (de `b39615c` a `d70f300`). Hi entraven `a2babcd` i `d5abc59`, que era el que volia comprovar, però cap dels commits posteriors.
- Es descarta llançar el CI a mà (`workflow_dispatch`): només funciona si el workflow és a la branca per defecte, i `master` només té documents.

## Decisió
1. **PR:** el pas «secrets» revisa amb gitleaks 8.24.3, la mateixa versió que fa servir l'acció, tot el rang de la base al cap de la PR (`base.sha..head.sha`, l'equivalent de `master..HEAD`), amb l'historial complet (`fetch-depth: 0`) i sense `--first-parent`.
2. **Integritat del binari:** es baixa de la versió oficial i es comprova amb la suma SHA-256 del `checksums.txt` d'aquella versió, fixada al `ci.yml`. Canviar de versió vol dir canviar la versió i la suma.
3. **Push:** l'acció de gitleaks continua igual i revisa els commits nous.
4. **Configuració sense canvis:** `.gitleaks.toml` i `.gitleaksignore` (empremtes de la 076 i la 077). Cap empremta nova sense una decisió del responsable del projecte.
5. **Esmena de la 077, «Comprovació»:** amb l'acció, una PR de més de 30 commits no posava a prova les empremtes de l'historial. Amb aquesta decisió, el CI d'una PR sí que les posa a prova.
6. **Si l'escaneig troba res:** se'n dona l'empremta i el fitxer al responsable del projecte i no es toca `.gitleaksignore`.

## Conseqüències
- `.github/workflows/ci.yml`: al treball «secrets», l'acció només als push i un pas propi a les PR. Es treu el permís `pull-requests: read`, que només feia servir l'acció a les PR.
- Primera comprovació: el CI de la PR #4 després del push de `feature/fase-1-fundacio-i-socis`.

## Fonts
- Resposta escrita del responsable del projecte, 10/11/2026.
- Execucions del CI 42900068604 (PR #5) i 42540425738 (PR #4).
