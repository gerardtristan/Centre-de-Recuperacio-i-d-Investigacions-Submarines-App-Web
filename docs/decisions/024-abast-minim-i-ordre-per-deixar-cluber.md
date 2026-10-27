# 024 — Abast mínim i ordre de construcció per deixar Cluber

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-26). L'ús de Stripe en mode real per al 05a abans d'acabar el 05b està pendent (P-30).

## Context
La proposta de l'arquitectura §9 (commit 103fe66) definia l'abast mínim per substituir Cluber i un ordre revisat (00 → 01 → 04 mínim → 05). Aquest ordre contradeia l'ordre de construcció de CLAUDE.md i de la metodologia (P-26). A més, la campanya de mandats nous només es pot fer amb Stripe en mode real ([022](022-mandats-sepa-escenari-base-b.md)).

## Alternatives
- Mantenir l'ordre original (0, 1, 2, 3, 4, 5…): Cluber no es podria deixar fins tenir activitats i material.
- Ordre revisat amb un sol mòdul 05: la campanya de mandats hauria d'esperar que tot el 05 estigués acabat.
- Ordre revisat amb el 05 dividit: es poden recollir mandats abans d'acabar els cobraments.

## Decisió
1. **Ordre nou, que mana:** 00 → 01 → 04 mínim → **05a** → **05b**. Després: 02, 03, resta de la 04, 06, 07, 08.
2. **05a, alta del mètode de pagament:** alta del mètode de pagament i signatura de mandats SEPA en mode real (campanya de mandats nous, escenari B).
3. **05b, cobraments:** cobraments, remeses, avís previ, reintents, retornats, devolucions i conciliació.
4. **Registre mínim de llicència al mòdul 01:** tipus, data d'alta i data de caducitat, perquè no es perdin dades en deixar Cluber. El mòdul 06 Llicències (preus, renovacions, recordatoris, no socis, exportació a la federació) queda per a després.
5. **Abast mínim:** el de l'arquitectura §9.1, amb els canvis anteriors.
6. [A validar amb Stripe] Si es poden recollir mandats abans d'acabar el 05a (per exemple, amb un formulari allotjat de Stripe, sense la integració completa).

## Conseqüències
- CLAUDE.md i la metodologia (§3 i §8) s'actualitzen amb l'ordre nou.
- La [014](014-migracio-cluber-i-entrada-en-produccio.md) i CLAUDE.md diuen que Stripe es fa servir en mode de proves fins que el 05 està acabat i provat i hi ha autorització escrita de la junta. El 05a en mode real ho canvia: s'ha de decidir si el 05a pot entrar en mode real amb una autorització pròpia i si el criteri per deixar Cluber passa a ser el 05b (P-30). Fins que es decideixi, mana la 014.
- P-28 (què fa Cluber amb les llicències) continua obert; el registre mínim de llicència n'evita la pèrdua de dades, però no resol el procés.

## Fonts
- Aprovació del §9 amb canvis i resolució de P-26 comunicades per l'equip el 27/10/2026
- `docs/arquitectura-integracions.md`, §9
- [014](014-migracio-cluber-i-entrada-en-produccio.md), [022](022-mandats-sepa-escenari-base-b.md)
