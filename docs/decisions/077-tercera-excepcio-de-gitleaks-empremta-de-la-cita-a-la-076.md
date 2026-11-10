# 077 — Tercera excepció de gitleaks: l'empremta exacta de la cita del fals positiu a la decisió 076

- **Data:** 10/11/2026
- **Estat:** Acceptada pel responsable del projecte el 10/11/2026 (resposta a l'informe de la validació de la tanda del 10/11/2026).
- **Abast:** amplia la norma d'excepcions de gitleaks de `CLAUDE.md` i la llista de `.gitleaksignore` de la [076](076-segona-excepcio-de-gitleaks-empremta-d-un-fals-positiu.md) amb una sola empremta. La 076 no canvia.

## Context
La primera versió de la 076 (commit `a31d6b4`) citava literalment, a la línia 8, la crida de dades de prova que havia provocat el fals positiu. L'execució del CI 42832792912 (10/11/2026) va tornar a fallar a «secrets» per aquesta cita, amb la mateixa regla `generic-api-key`. No és cap secret: és el text d'una decisió que descriu dades de prova inventades. El text es va corregir a `9fa6584`, però la cita continua a l'historial de `a31d6b4`, i una revisió de tota la branca (per exemple, en una PR) la tornaria a trobar. La 076 (punt 5) demana una decisió nova per a cada empremta nova.

## Decisió
1. **Causa:** fals positiu de la regla `generic-api-key` a l'historial, a la cita literal de dades de prova dins del text d'una decisió.
2. **Abast:** una sola entrada nova a `.gitleaksignore`, l'empremta exacta `a31d6b4dc188e489aead746fc0dd816bf0abc898:docs/decisions/076-segona-excepcio-de-gitleaks-empremta-d-un-fals-positiu.md:generic-api-key:8`. Cap patró genèric, cap ruta, cap altra regla, cap altre commit ni cap altra línia.
3. **Excepcions anteriors sense canvis:** el valor exacte de `.gitleaks.toml` (`contrasenya-de-proves-1954`) i l'empremta de la 076.
4. **Cap reescriptura:** ni `force-push` ni canvis de l'historial.
5. **Per no repetir-ho:** les decisions i els documents que descriuen un fals positiu en diuen el fitxer, el commit, la línia i la regla, però no en citen el text.
6. **Entrades noves:** cada empremta nova continua demanant una decisió nova amb la causa, l'abast i la data.

## Conseqüències
- `.gitleaksignore`: dues empremtes, cadascuna amb un comentari que remet a la seva decisió.
- `CLAUDE.md`: la norma de proves enumera les tres excepcions (el valor de `.gitleaks.toml` i les empremtes de la 076 i la 077).
- **Comprovació:** un push només fa revisar a gitleaks els commits nous, així que cap execució del CI d'un push no posa a prova aquestes dues empremtes de l'historial. Ho farà una revisió de tota la branca (una PR o una execució manual de gitleaks sobre tot l'historial).

## Fonts
- Resposta escrita del responsable del projecte, 10/11/2026.
- Execució del CI 42832792912 (fallada a «secrets», a `a31d6b4`).
