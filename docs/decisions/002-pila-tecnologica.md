# 002 — Pila tecnològica

- **Data:** 27/10/2026 (proposta inicial a CLAUDE.md; confirmada a l'encàrrec d'arquitectura del 26/10/2026)
- **Estat:** Acceptada

## Context
Un grup petit de voluntaris ha de poder mantenir la plataforma. Pressupost molt ajustat, dades a la UE, una sola base de dades (monòlit modular) i tres zones (web pública, àrea de socis, administració).

## Alternatives
- Plataformes gestionades tot en un (PaaS amb base de dades inclosa): menys manteniment, però cost més alt i, sovint, dades fora de la UE o més dependència d'un sol proveïdor.
- Diversos serveis o microserveis: descartat per la mida de l'equip.
- Monòlit Django en un VPS propi gestionat amb Coolify: cost baix, dades a la UE, sortida clara (contenidors estàndard).

## Decisió
| Peça | Eina |
|---|---|
| Web pública i PWA | Cloudflare Pages (gratuït) |
| Backend i API | Django amb API REST, desplegat amb Coolify en un VPS de Hetzner (UE) |
| Base de dades | PostgreSQL al mateix servidor |
| Tasques en segon pla | Cua sobre PostgreSQL, sense Redis ([012](012-cua-de-tasques.md)) |
| Fitxers | Scaleway Object Storage, París ([005](005-fitxers.md)) |
| Correu | Brevo ([004](004-correu.md)) |
| Pagaments | Stripe ([007](007-pagaments-stripe.md)) |
| DNS | Cloudflare |

## Conseqüències
- Un sol servidor de producció és un punt únic de fallada: es mitiga amb còpies creuades i restauració provada ([006](006-copies-de-seguretat.md)).
- Coolify i el sistema operatiu els ha d'actualitzar algú del club: tasca al calendari de manteniment.
- Els detalls, els costos i les vies de sortida són a [arquitectura-integracions.md](../arquitectura-integracions.md).

## Fonts
- `CLAUDE.md`, «Pila»
- `docs/context-projecte.md`, §7 i §9
- Encàrrec d'arquitectura del 26/10/2026 (conversa amb l'equip)
