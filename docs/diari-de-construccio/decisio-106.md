# Decisions 106 i 107 · Editor visual de la web pública i fotos reals del club

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 24/11/2026 18:06 | 48268706 | cap (document) | [A comprovar] |

**En tres línies:** el pas 1 de l'encàrrec del propietari per a l'editor visual de la web: la norma, sense codi. La decisió 106 i una addenda al mòdul 07 diuen com serà l'editor: blocs tancats, vista prèvia, YouTube amb clic, versions i publicació programada, activitats i fotos de l'app. La 107 permet fer servir les fotos reals del club per a les plantilles i les captures.

## Què s'ha fet
- [`docs/decisions/106-editor-visual-de-la-web-publica.md`](../decisions/106-editor-visual-de-la-web-publica.md) i [`107-fotos-reals-del-club-per-a-plantilles-mostres-i-captures.md`](../decisions/107-fotos-reals-del-club-per-a-plantilles-mostres-i-captures.md).
- [Addenda de la 106 a M07](../planning.md#M07-addenda-106): les regles noves o concretades (RN-M07-09, 10 i 15 a 26), el catàleg de 26 blocs amb els camps i les variants (el contracte amb la sessió de disseny), les entitats noves, WP1a, WP1b, WP9 i WP10, quatre ajustos nous, el requisit RP-M07-02 al 02, els criteris CA-M07-23 a 33, les tasques que canvien i les noves (T-M07-19 a 31 i T-M02-53), i qui fa cadascuna.
- P-574 (text de l'avís de YouTube), P-575 (qui revisa abans de publicar) i P-610 (formats i mida d'un vídeo propi), a `pendents.md` i al tauler.
- Estat: files noves a `docs/estat/M07.md` i `docs/estat/M02.md`.

## Decisions i perquè
- Els noms de camp dels blocs són en anglès, com els tipus que ja hi ha al codi (`text`, `image`, `gallery`…), i els tipus antics de M07-6 passen al catàleg nou amb una migració de dades a la T-M07-04.
- Els permisos nous (WP1a, WP1b, WP10 i l'abast per pàgina) són del catàleg del nucli i entren amb la T-M07-26, com diu l'estudi del propietari; el WP9, amb la T-M07-21. La T-M07-02 ja és feta i no canvia.

## Problemes trobats
- L'encàrrec es remet a l'[«Estudi: editor visual de la web pública (M07)»](https://claude.ai/artifact/NpiWqot3HiE225xj2sqpdw), que no es copia al repositori. La primera versió de l'addenda va sortir de l'encàrrec de disseny; el 24/11/2026 es va revisar contra l'estudi i es va corregir:
  - bloc de vídeo amb YouTube o vídeo propi (RN-M07-26; formats a la P-610), accent de la pàgina triat a l'editor i «retirar i recuperar» (RN-M07-25, CA-M07-33);
  - la T-M07-02 no canvia; els permisos nous, a la T-M07-26 (M, després de la 02 i la 06a) i el WP9 a la T-M07-21;
  - T-M07-04 amb l'esborrany per pàgina i el renderitzador únic; 06a (blocs, duplicar, amagar, desfer) i 06b (vista prèvia, clic per seleccionar, desat automàtic i avís); punt focal i WebP a la T-M07-07; la guia (T-M07-18) amb plantilles, vídeos i versions;
  - esforç, dependències i «feta quan» de les T-M07-19 a 29 i de la T-M02-53 (ara després de la T-M02-20), com a l'estudi; les redireccions passen de la 22 a la 24.
- La T-M07-31 es queda com a la 107 (M, fotos amb persones): la taula de l'estudi encara porta la proposta inicial (S, sense persones reconeixibles), que la resposta a E8 del mateix estudi substitueix.

## Com se sap que funciona
És un document: el propietari el revisa abans de fusionar-lo («fusiona la #N»).

## Evidències
- Diferència de la PR: 6 documents i 2 decisions noves, cap fitxer de codi.
