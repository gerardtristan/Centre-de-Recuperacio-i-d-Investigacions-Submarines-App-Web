# 025 — Dos nivells de producció: mandats (05a) i producció completa (05b)

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-30; refina la [014](014-migracio-cluber-i-entrada-en-produccio.md)). Quines comprovacions de la porta 3 s'apliquen a la producció de mandats és [A validar] (P-31).

## Context
La [024](024-abast-minim-i-ordre-per-deixar-cluber.md) fa que el 05a reculli mandats SEPA en mode real abans del 05b. La [014](014-migracio-cluber-i-entrada-en-produccio.md) i CLAUDE.md, en canvi, mantenien Stripe en mode de proves fins que el 05 estigués acabat i provat. Els mandats signats en mode de proves no serveixen ([022](022-mandats-sepa-escenari-base-b.md)).

## Alternatives
- Un sol nivell de producció (05 sencer): la campanya de mandats s'endarrereix fins que els cobraments estan acabats.
- Dos nivells, amb el primer limitat a recollir mandats i sense cap cobrament.

## Decisió
| | **Nivell 1: producció de mandats** | **Nivell 2: producció completa** |
|---|---|---|
| Quan | 05a acabat i provat | 05b acabat i provat |
| Què s'hi pot fer | Stripe en mode real **només per recollir mandats** (alta del mètode de pagament) | Cobraments reals amb tots els mètodes |
| Cobraments reals | **Cap** | Sí |
| Requisits | Autorització **expressa** de la junta per a aquest nivell. Portes de la checklist aplicables a producció superades: HTTPS (A7), secrets fora del repositori (A3), còpies i prova de restauració (D1, D2), RGPD i consentiments (H1, H3; text del mandat), registre d'activitat (C8). Com que hi ha dades reals de socis, s'aplica tota la porta 2 | Autorització expressa de la junta per a la producció completa; portes 0-3 |
| Cluber | Continua cobrant | **Criteri per deixar Cluber** (migració única, [014](014-migracio-cluber-i-entrada-en-produccio.md) i [020](020-baixa-de-cluber-sense-restriccio-de-data.md)) |

**Condició sobre l'IBAN (escenari B):**
- La plataforma **no guarda l'IBAN**: només identificadors de Stripe (client, mètode de pagament, mandat) i la referència del mandat.
- **Stripe té la custòdia** de l'IBAN i del mandat.
- La importació de Cluber no inclou IBAN.

**Salvaguardes tècniques del nivell 1:**
- La plataforma no crea cap cobrament real. Una opció de configuració (per exemple, `STRIPE_LIVE_CHARGES_ALLOWED`, fals fins al nivell 2) bloqueja qualsevol creació de cobrament en mode real, i hi ha proves que ho comproven.
- La clau de Stripe d'aquest nivell té els permisos mínims per a mandats [A validar si Stripe permet restringir-la així].

## Conseqüències
- La [014](014-migracio-cluber-i-entrada-en-produccio.md) es manté: «entrada en producció» passa a voler dir **producció completa** (05b acabat i provat). El nivell 1 és una excepció limitada.
- CLAUDE.md, la checklist (§2 i C9) i l'arquitectura s'alineen amb aquests dos nivells.
- El nivell 1 obre la plataforma als socis (signatura de mandats). Quines comprovacions de la porta 3 («abans d'obrir-ho als socis»: monitoratge, alertes, correu, dispositius, marxa enrere, cookies, accessibilitat) s'hi apliquen està [A validar] (P-31).

## Fonts
- Resolució de P-30 comunicada per l'equip el 27/10/2026
- [014](014-migracio-cluber-i-entrada-en-produccio.md), [022](022-mandats-sepa-escenari-base-b.md), [024](024-abast-minim-i-ordre-per-deixar-cluber.md)
- `docs/checklist-produccio.md`, §2 i categories A, C, D i H
