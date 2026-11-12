# 083 — Quarta excepció de gitleaks: les dues empremtes exactes d'un fals positiu d'una prova

- **Data:** 11/11/2026
- **Estat:** Acceptada pel responsable del projecte l'11/11/2026 (resposta a l'informe del CI de `f96387c`).
- **Abast:** amplia la norma d'excepcions de gitleaks de `CLAUDE.md` i la llista de `.gitleaksignore` de la [076](076-segona-excepcio-de-gitleaks-empremta-d-un-fals-positiu.md) i la [077](077-tercera-excepcio-de-gitleaks-empremta-de-la-cita-a-la-076.md) amb dues empremtes. La 076, la 077 i l'excepció de valor de `.gitleaks.toml` no canvien.

## Context
El commit `6c73807` (11/11/2026, T-M01-51) va afegir la prova `apps/members/tests/test_totp_reset_081.py`. A les línies 165 i 166, la prova feia servir com a contrasenya «nova» d'una recuperació per correu un valor inventat que no era el valor únic de les credencials de proves que fixa `CLAUDE.md`, sinó una variant seva. La variant no queda coberta per l'excepció de valor de `.gitleaks.toml`.

Les execucions del CI 43081028066 (push) i 43081038374 (PR #7), a `f96387c`, van fallar només al job «secrets», amb dues troballes de la regla `generic-api-key` en aquelles dues línies d'aquell commit. La resta de jobs van passar.

No és cap secret: és un valor inventat dins d'una prova. Comprovat l'11/11/2026:
- només apareix al commit `6c73807`, que l'afegeix, i desapareix al `65b2c81`, que el substitueix pel valor únic de proves;
- no és al HEAD, ni al flux del CI, ni a `.env.example`, ni a `docker-compose.yml`, ni a cap fitxer d'entorn local, ni a la documentació.

El valor ja no és al codi, però continua a l'historial de `6c73807`, i gitleaks revisa commit per commit. La 076 (punt 5) i la 077 (punt 6) demanen una decisió nova per a cada empremta nova.

## Decisió
1. **Causa:** fals positiu de la regla `generic-api-key` a l'historial, en un valor inventat d'una prova que no seguia la norma del valor únic.
2. **Abast:** dues entrades noves a `.gitleaksignore`, les empremtes exactes
   - `6c7380731f4822cb1b8fcebc4f581b5b7848da7e:apps/members/tests/test_totp_reset_081.py:generic-api-key:165`
   - `6c7380731f4822cb1b8fcebc4f581b5b7848da7e:apps/members/tests/test_totp_reset_081.py:generic-api-key:166`

   Cap patró genèric, cap ruta, cap altra regla, cap altre commit ni cap altra línia.
3. **Excepcions anteriors sense canvis:** el valor exacte de `.gitleaks.toml` i les empremtes de la 076 i la 077. L'excepció de `.gitleaks.toml` no s'amplia.
4. **Cap reescriptura:** ni `force-push` ni canvis de l'historial.
5. **Si gitleaks troba una tercera troballa o una empremta diferent,** no s'afegeix: s'informa el responsable.
6. **Per no repetir-ho:**
   - les proves fan servir sempre el valor únic de `CLAUDE.md`, també quan necessiten una contrasenya «nova» o «diferent»; si cal de debò un altre valor que sembli un secret, la línia porta `gitleaks:allow` i un comentari que digui per què (norma que ja hi havia);
   - corregir el valor al HEAD no n'hi ha prou: gitleaks llegeix cada commit. Abans d'un push, es passa gitleaks en local sobre el mateix rang que el CI.
7. **Entrades noves:** cada empremta nova continua demanant una decisió nova amb la causa, l'abast i la data.

## Conseqüències
- `.gitleaksignore`: quatre empremtes, cadascuna amb un comentari que remet a la seva decisió.
- `CLAUDE.md`: la norma de proves enumera les excepcions (el valor de `.gitleaks.toml` i les empremtes de la 076, la 077 i la 083).
- **Comprovació:** gitleaks 8.24.3 en local sobre el rang de la PR #7 (de la base `496da19` al cap), i després el CI del push i de la PR.

## Fonts
- Resposta escrita del responsable del projecte, 11/11/2026.
- Execucions del CI 43081028066 i 43081038374 (fallada a «secrets», a `f96387c`).
