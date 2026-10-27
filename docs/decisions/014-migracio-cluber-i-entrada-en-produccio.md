# 014 — Migració única de Cluber i criteri d'entrada en producció

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-01). Contradiu el context v3 i el document incremental: els canvis proposats a aquests documents estan pendents d'aprovació (P-19).

## Context
- Context v3 (§6-7) i document incremental (§2.3, §4.3, §4.5): Cluber continua per als cobraments al principi; substituir-los queda fora d'abast.
- Funcionalitats (§1, §2, §9.13): Cluber es deixa de fer servir; els cobraments es fan dins l'app.

## Alternatives
- Mantenir Cluber per a les quotes i importar-ne els CSV de manera periòdica: dues fonts de veritat i la quota de Cluber es manté.
- Migració per parts (primer socis, després quotes): dues eines actives durant més temps.
- Migració única quan la plataforma ja cobra.

## Decisió
- La migració de Cluber es fa **una sola vegada** (socis, dates d'alta, rebuts i, si es pot, mandats de domiciliació; procés de funcionalitats §9.13).
- Cluber es deixa quan la plataforma està activa **amb els pagaments inclosos**: domiciliació, targeta i Bizum.
- **Criteri d'entrada en producció:** mòdul 05 (pagaments) acabat i provat, a més de les portes 0-3 de la checklist i l'autorització escrita de la junta per activar Stripe en producció.

## Conseqüències
- Fins que el mòdul 05 estigui acabat i provat, Cluber continua sent l'eina de cobrament i la plataforma no entra en producció.
- La campanya de quotes en paral·lel prevista a funcionalitats §9.13 (sense cobrar a l'app mentre Cluber és actiu) i el moment de donar de baixa Cluber (en vèncer el contracte) s'han de casar amb aquest criteri [A validar] (P-20).
- Si els mandats de Cluber no es poden traspassar, els socis en signen un de nou a la plataforma.

## Fonts
- Resolució de P-01 comunicada per l'equip el 27/10/2026
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §1, §2 i §9.13
- `docs/context-projecte.md`, §6 i §7; `docs/entregues/document-incremental.pdf`, §2.3, §4.3 i §4.5 (contradicció)
