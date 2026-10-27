# 035 — Totes les dades personals es tracten només dins la UE

- **Data:** 27/10/2026
- **Estat:** Acceptada. Afecta la [002](002-pila-tecnologica.md), la [004](004-correu.md), la [007](007-pagaments-stripe.md), l'[011](011-monitoratge-i-errors.md), la [017](017-pagaments-metodes-i-domiciliacions.md), la [022](022-mandats-sepa-escenari-base-b.md), la [023](023-gestio-del-dns.md), la [024](024-abast-minim-i-ordre-per-deixar-cluber.md) i la [025](025-dos-nivells-de-produccio.md): els proveïdors que hi xoquen se substitueixen a la [042](042-proveidors-substituits-pel-requisit-ue.md). Origen: decisió 0002 del repositori anterior (històric).

## Context
La plataforma tractarà dades personals de socis, alumnes i no socis: identificació, contacte, quotes, pagaments, llicències, inscripcions, missatges i fotos. Fins ara, la pila (002) feia servir alguns proveïdors amb seu fora de la UE (Cloudflare, Stripe, Sentry).

## Alternatives
- Acceptar proveïdors de fora de la UE amb servidors a la UE i clàusules contractuals tipus.
- **Tractar totes les dades personals només dins la UE.**

## Decisió
**Totes les dades personals es tracten únicament dins la Unió Europea.** És un requisit ferm, no una preferència.

S'aplica a tots els proveïdors i serveis que toquin dades personals: allotjament, base de dades, còpies, pagaments, facturació (Verifactu), correu, missatges, vídeos tutorials, monitoratge d'errors, analítica, CDN i tipografies.

Un servei compleix el requisit només si:
1. l'empresa que tracta les dades té la seu a la UE; **i**
2. els servidors on es guarden i es processen les dades són a la UE; **i**
3. no fa transferències de dades personals fora de la UE (tampoc a empreses del mateix grup ni a subencarregats); **i**
4. signa un contracte d'encarregat del tractament (RGPD, art. 28).

Un servei d'una empresa de fora de la UE amb servidors a la UE **no compleix**: es marca com a CONFLICTE i s'hi proposa una alternativa.

L'app no guarda mai dades de targeta ni credencials del banc.

## Conseqüències
- Tot proveïdor nou s'afegeix al registre [`docs/proveidors-i-dades-ue.md`](../proveidors-i-dades-ue.md) abans de fer-lo servir, amb seu, servidors, subencarregats i contracte.
- Al repositori i a les eines de desenvolupament no hi entren mai dades reals (ja ho diu la [010](010-entorns.md)).
- És un requisit no funcional de tots els mòduls.

## Fonts
- Decisió comunicada per l'equip el 27/10/2026
