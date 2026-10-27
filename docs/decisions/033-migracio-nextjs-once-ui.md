# 033 — Migrar els wireframes a Next.js i Once UI Core

- **Data:** 27/10/2026
- **Estat:** Descartada. Es manté HTML i CSS plans, amb els patrons de Magic Portfolio com a referència visual ([034](034-patrons-magic-portfolio.md)).

## Context
En incorporar patrons de Magic Portfolio, s'ha valorat migrar els wireframes, i potser el frontend, a Next.js amb Once UI Core (la llibreria de components de Once UI, amb llicència MIT), que és la base tecnològica de la plantilla.

## Alternatives
1. **Migrar a Next.js i Once UI Core.** Permetria fer servir els components de Once UI directament.
2. **Mantenir HTML i CSS plans amb els tokens propis i fer servir Magic Portfolio només com a referència visual.** És l'opció triada (034).

## Motius per descartar la migració
- **Llicència de la plantilla:** Magic Portfolio té llicència CC BY-NC 4.0 (cal citar l'autor i no se'n permet l'ús comercial). Once UI Core és MIT, però partir de la plantilla obligaria a complir la CC BY-NC, i el seu codi no es pot reaprofitar lliurement. Fer-la servir només com a referència evita el problema.
- **Cost de migració:** caldria refer els tres wireframes, el sistema de tokens (dos temes, zones, neumorfisme limitat, moviment) i les proves de contrast en un altre sistema, en una etapa que només ha de fixar l'estructura i no el disseny final.
- **Pila del frontend encara [A validar]:** la pila acordada és Django amb API REST, i la web pública i la PWA van a Cloudflare Pages (CLAUDE.md, arquitectura). El framework del frontend no està decidit (`design-system.md` §12). Triar Next.js ara seria decidir la pila per la porta del darrere.

## Conseqüències
- Els wireframes continuen en HTML i CSS plans, sense dependències.
- Si més endavant es decideix la pila del frontend i surt Next.js, aquesta decisió es pot tornar a obrir amb una decisió nova. Els tokens de `tokens.css` es podrien traslladar a qualsevol sistema.

## Fonts
- Encàrrec de l'equip (27/10/2026)
- [034](034-patrons-magic-portfolio.md); `docs/analisi-magic-portfolio.md`; `docs/design-system.md` §12
