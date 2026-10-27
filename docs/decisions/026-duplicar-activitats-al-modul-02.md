# 026 — Duplicar activitats es construeix al mòdul 02

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-34)

## Context
El document de funcionalitats (§2 i §10) i l'encàrrec de la spec 00 situaven «duplicar cursos, sortides i conferències» a la base comuna. L'arquitectura (§9.1) el deixava fora de l'abast mínim de la 00 («va amb el 02»). A la 00 no hi ha activitats per duplicar.

## Alternatives
- Construir el servei a la 00 sense activitats: codi sense cap ús fins a la fase 2.
- Construir-lo al 02, quan existeixen les activitats.

## Decisió
- Duplicar activitats es construeix al **mòdul 02**.
- A la spec 00 només hi consta com a **servei comú previst**.
- Les regles de funcionalitats §9.18 (es copien el programa, les sessions, els preus, els instructors i el material típic; no es copien inscrits ni pagaments) s'especifiquen a la spec 02.

## Conseqüències
- La 00 no té cap història ni criteri d'acceptació de duplicar.
- Les conferències (Departament d'Història) faran servir el mateix servei quan s'especifiquin.

## Fonts
- Resolució de P-34 comunicada per l'equip el 27/10/2026 (revisió del commit 8156443)
- `docs/funcionalitats-processos/funcionalitats-processos.docx`, §2, §9.18 i §10
- `docs/arquitectura-integracions.md`, §9.1
