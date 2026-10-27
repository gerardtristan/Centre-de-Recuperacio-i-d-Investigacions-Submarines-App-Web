# 042 — Proveïdors substituïts pel requisit de dades dins la UE

- **Data:** 27/10/2026
- **Estat:** Acceptada. Substitueix en part la [002](002-pila-tecnologica.md) (web i PWA, DNS i pagaments), la [007](007-pagaments-stripe.md), la [011](011-monitoratge-i-errors.md) (Sentry), la [017](017-pagaments-metodes-i-domiciliacions.md) (només el proveïdor) i la [023](023-gestio-del-dns.md) (si feia servir Cloudflare). Les decisions [022](022-mandats-sepa-escenari-base-b.md), [024](024-abast-minim-i-ordre-per-deixar-cluber.md) i [025](025-dos-nivells-de-produccio.md) queden afectades on parlen de Stripe (vegeu Conseqüències).

## Context
La [035](035-dades-nomes-dins-ue.md) exigeix que totes les dades personals es tractin només dins la UE. Quatre proveïdors de la pila hi xoquen.

## Decisió
| Proveïdor anterior | Per què xoca | Substitut |
|---|---|---|
| **Cloudflare** (Pages i DNS) | Empresa dels EUA, xarxa global | La web pública i la PWA se serveixen des del VPS de Hetzner (UE). DNS al registrador del domini o a Hetzner [A verificar] |
| **Sentry** | Empresa dels EUA | **GlitchTip** o **Bugsink** instal·lat al mateix servidor |
| **Brevo** | Empresa francesa; subencarregats [A verificar] | Es manté **només si** es verifica que tots els subencarregats que tracten dades són dins la UE. Si no, **Scaleway Transactional Email** (París) |
| **Stripe** | Transferències a l'empresa matriu dels EUA | **Descartat.** El proveïdor de pagaments es tria a la [043](043-proveidor-de-pagaments-dins-la-ue.md) |

## Conseqüències
- CLAUDE.md i l'arquitectura s'han d'alinear amb aquesta decisió en un canvi posterior (no s'editen les decisions antigues).
- Les variables `STRIPE_*` (arquitectura §5) se substitueixen per les del proveïdor que es triï.
- Els dos nivells de producció de la 025 es mantenen com a criteri, però referits al proveïdor de la 043: nivell 1 = alta del mètode de pagament (i mandats, si s'aplica la [044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md)) sense cobraments reals; nivell 2 = cobraments reals.
- L'escenari B de la 022 (mandats nous) es manté, però la custòdia de l'IBAN ja no és de Stripe: vegeu la 044.
- El cost de la 016 no canvia per Cloudflare (0 €) ni per GlitchTip o Bugsink (0 € al mateix servidor) [A verificar els recursos del VPS].

## Fonts
- Decisió comunicada per l'equip el 27/10/2026
- `docs/proveidors-i-dades-ue.md`
