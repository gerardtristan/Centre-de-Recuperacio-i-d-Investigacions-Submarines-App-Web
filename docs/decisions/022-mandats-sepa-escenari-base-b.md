# 022 — Mandats SEPA: escenari base B (mandats nous)

- **Data:** 27/10/2026
- **Estat:** Acceptada de manera provisional. Depèn de confirmar que Cluber és el creditor [A validar amb un rebut o la documentació de Cluber] (P-21).

## Context
La resposta parcial de tresoreria (27/10/2026) és que Cluber cobra els rebuts domiciliats a través del seu propi compte i després ingressa al club l'import menys un percentatge. D'aquí es dedueix, de manera provisional, que el **creditor dels mandats actuals és Cluber**, no el club.

Cluber permet exportar socis, IBAN i referències; el format està [A validar].

## Alternatives
Vegeu l'arquitectura, §4.9:
- **A:** migrar els mandats a Stripe.
- **B:** campanya única de mandats nous.

## Decisió
- **Escenari base: B.** Campanya única perquè cada soci signi un mandat nou al formulari de Stripe.
- **Escenari A** només si Stripe confirma per escrit que accepta migrar mandats on el creditor és un tercer (Cluber).
- En l'escenari B, la plataforma **no importa IBAN** de Cluber: només socis i referències (els mandats nous els recull Stripe directament). Si no calen, es demana l'exportació sense IBAN.
- La campanya ha d'acabar **abans de la propera remesa de quotes**. Quan es cobren les quotes anuals està [A validar amb tresoreria] (P-29).

## Conseqüències
- Els socis veuran un **canvi de creditor** als rebuts (de Cluber al club o a Stripe, segons P-24). Cal una comunicació prèvia (arquitectura §9.3).
- **Dependència crítica:** els mandats signats en mode de proves de Stripe no serveixen. La campanya només es pot fer amb Stripe en producció, és a dir, amb el mòdul 05 acabat i provat i l'autorització de la junta ([014](014-migracio-cluber-i-entrada-en-produccio.md)).
- Qui no signi el mandat a temps paga la quota amb targeta, Bizum o transferència ([017](017-pagaments-metodes-i-domiciliacions.md)).

## Fonts
- Resposta parcial de tresoreria comunicada per l'equip el 27/10/2026
- `docs/arquitectura-integracions.md`, §4.9
- [014](014-migracio-cluber-i-entrada-en-produccio.md), [017](017-pagaments-metodes-i-domiciliacions.md)
