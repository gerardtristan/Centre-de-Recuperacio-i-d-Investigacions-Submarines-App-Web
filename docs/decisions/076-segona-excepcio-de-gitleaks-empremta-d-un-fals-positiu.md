# 076 — Segona excepció de gitleaks: l'empremta exacta d'un fals positiu de l'historial

- **Data:** 10/11/2026
- **Estat:** Acceptada pel responsable del projecte el 10/11/2026 (opció (a) de l'informe de la tanda del 10/11/2026).
- **Abast:** amplia la norma d'excepcions de gitleaks de `CLAUDE.md` («Regles que sempre s'han de complir», proves), que fins ara només admetia l'excepció de valor de `.gitleaks.toml` (`contrasenya-de-proves-1954`).

## Context
La primera execució del CI de la branca `feature/night-2026-11-10` (42810347688, 10/11/2026) va fallar a la feina «secrets»: la regla per defecte `generic-api-key` de gitleaks va llegir com una clau la línia `leave, by=secretary, effective_on=today + datetime.timedelta(days=30)` de `apps/members/demo_data.py` (dades de prova inventades, commit `6d871bd`), pel tros «secret» de «secretary». No és cap secret. El nom es va canviar a `180bdf8` i el CI següent va ser verd, però la línia continua a l'historial: una revisió de tota la branca (per exemple, en una PR) la tornaria a trobar. No es reescriu l'historial.

## Decisió
1. **Causa:** fals positiu de la regla `generic-api-key` a l'historial, en dades de prova inventades.
2. **Abast:** una sola entrada a `.gitleaksignore`, l'empremta exacta `6d871bd0ce0b95ee5bcc6bbcf65ddb9619670e31:apps/members/demo_data.py:generic-api-key:305`. Cap patró genèric, cap ruta, cap altra regla. No cobreix cap altre commit ni cap altra línia del mateix fitxer.
3. **Primera excepció sense canvis:** `.gitleaks.toml` continua igual (només el valor exacte `contrasenya-de-proves-1954` a la regla `generic-api-key`).
4. **Cap reescriptura:** ni `force-push` ni canvis de l'historial.
5. **Entrades noves:** cada empremta nova a `.gitleaksignore` demana una decisió nova amb la causa, l'abast i la data.

## Conseqüències
- `CLAUDE.md`: la norma de proves diu que hi ha dues excepcions (la de valor de `.gitleaks.toml` i aquesta empremta) i que no se n'afegeix cap altra sense decisió.
- `.gitleaksignore`: fitxer nou a l'arrel, amb un comentari que remet a aquesta decisió.

## Fonts
- Resposta escrita del responsable del projecte, 10/11/2026 (opció (a)).
- Execucions del CI 42810347688 (fallada a «secrets», a `63bdd51`) i 42811548125 (verda, a `180bdf8`).
