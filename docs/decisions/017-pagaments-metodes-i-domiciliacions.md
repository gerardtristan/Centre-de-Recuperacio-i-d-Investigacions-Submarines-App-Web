# 017 — Pagaments: mètodes per cobrament i domiciliacions

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-09; substitueix [007](007-pagaments-stripe.md) amb l'abast de P-01 ja resolt a [014](014-migracio-cluber-i-entrada-en-produccio.md)). El registre manual continua obert (P-12).

## Context
La 007 triava Stripe, però quedava oberta a l'abast dels cobraments (P-01) i als mètodes de pagament de les quotes (P-09).

## Alternatives
Vegeu 007 (Cluber, passarel·la del banc, Stripe).

## Decisió
**Proveïdor:** Stripe per a domiciliació SEPA, targeta (amb Apple Pay i Google Pay) i Bizum. Fora de Stripe: transferència amb referència única i registre manual.

**Mètodes per tipus de cobrament:**

| Cobrament | Domiciliació SEPA | Targeta / Apple / Google Pay | Bizum | Transferència | Manual |
|---|---|---|---|---|---|
| Quota anual (recurrent) | Sí, **per defecte** | Sí | Sí | Sí | Sí, amb motiu (P-12) |
| Inscripció | No | Sí | Sí | Sí | Sí, amb motiu (P-12) |
| Llicència | No | Sí | Sí | Sí | Sí, amb motiu (P-12) |

La domiciliació només s'aplica a pagaments recurrents.

**Requisits de les domiciliacions per a la spec del mòdul 05:**
1. **Avís previ** al soci abans de cada cobrament (import i data). Qui l'envia (Stripe o la plataforma) i l'antelació són [A validar].
2. **Reintent controlat** si un cobrament falla: nombre màxim de reintents i dies entre intents [A validar]; cada intent fallit pot generar comissió.
3. **Alternativa de pagament** si falla: enllaç per pagar la quota amb targeta, Bizum o transferència.
4. **Estat «retornat»** amb conseqüències definides (impagat, carnet, qui assumeix la comissió) [A validar a la spec 05].

**Regles que es mantenen de la 007:** el pagament només es dona per fet amb un webhook verificat per signatura i processat de manera idempotent; no es guarden dades de targeta; Stripe sempre en mode de proves fins a l'autorització escrita de la junta; entrada en producció segons [014](014-migracio-cluber-i-entrada-en-produccio.md).

## Conseqüències
- **Comissions** segons la pàgina de Stripe Espanya consultada el 27/10/2026:

  | Concepte | Comissió |
  |---|---|
  | Targeta EEE estàndard | 1,5 % + 0,25 € |
  | Bizum | 1,5 % + 0,25 € |
  | Domiciliació SEPA | 0,35 € per cobrament |
  | Domiciliació fallida | 3,50 € [A validar a la font oficial] |
  | Rebut retornat (disputa) | 15 € [A validar a la font oficial] |

  Les comissions de quotes s'imputen a «General / Quotes de socis» ([013](013-imputacio-comissions.md)).
- La quota per defecte es domicilia, però el soci pot triar un altre mètode: la spec 01 (quotes) i la 05 han de contemplar el canvi de mètode.

## Fonts
- Resolució de P-09 i requisits de domiciliació comunicats per l'equip el 27/10/2026
- [007](007-pagaments-stripe.md) i les fonts que cita
- `docs/funcionalitats-processos/funcionalitats-processos.pdf`, §3 i §9.5
- `docs/arquitectura-integracions.md`, §3-4
