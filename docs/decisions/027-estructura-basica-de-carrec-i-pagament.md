# 027 — Estructura bàsica de càrrec i pagament a la 00; la 04 hi construeix al damunt

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-35)

## Context
L'encàrrec de la spec 00 demanava definir-hi el model de pagament comú (només l'estructura). CLAUDE.md i l'arquitectura (§4.1) deien que «el model de càrrec, pagament i ingrés viu a 04».

## Alternatives
- Tot el model a la 04: el 01 (quotes) no podria crear càrrecs fins tenir la 04.
- Estructura bàsica a la 00 i la resta a la 04.

## Decisió
- La **00** té l'estructura bàsica de **càrrec** i **pagament**: tipus (quota, inscripció, llicència), import en cèntims, moneda, departament obligatori, estats (pendent, pagat, retornat, anul·lat) i transicions, mètodes (domiciliació, targeta, Bizum, transferència, manual), identificadors externs i cap camp d'IBAN ni de targeta.
- La **04** hi construeix al damunt: moviments de tresoreria immutables, ingressos automàtics, comissions, comptes (banc, caixa, trànsit de Stripe) i conciliació.
- Els altres mòduls hi escriuen a través de serveis (CLAUDE.md, «una app no escriu als models d'una altra»).

## Conseqüències
- CLAUDE.md i l'arquitectura §4.1 s'actualitzen.
- La 04 no pot canviar les regles bàsiques (cèntims, estats, departament, cap IBAN) sense actualitzar primer la spec 00.

## Fonts
- Resolució de P-35 comunicada per l'equip el 27/10/2026 (revisió del commit 8156443)
- `CLAUDE.md`; `docs/arquitectura-integracions.md`, §4.1
