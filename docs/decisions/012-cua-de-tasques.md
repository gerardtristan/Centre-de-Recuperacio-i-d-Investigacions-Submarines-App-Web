# 012 — Cua de tasques sobre PostgreSQL

- **Data:** 27/10/2026
- **Estat:** Acceptada

## Context
Cal processar en segon pla les notificacions de Stripe, els enviaments de correu en tandes, els recordatoris, les còpies i les importacions. CLAUDE.md preveu «tasques en segon pla».

## Alternatives
- Celery amb Redis: estàndard, però afegeix un servei més per mantenir i fer-ne còpia.
- Cua que guarda les tasques a la mateixa base de dades PostgreSQL.

## Decisió
Cua de tasques sobre PostgreSQL, sense Redis. La llibreria concreta es tria al pla tècnic de la base comuna [A validar en `specs/00-base-comuna/plan.md`].

## Conseqüències
- Un sol servei de dades: les tasques pendents entren a les còpies de la base de dades.
- Suficient per al volum del club; si algun dia no n'hi ha prou, es pot canviar a Redis sense tocar la lògica de negoci, si les tasques es criden a través d'una capa pròpia.

## Fonts
- `CLAUDE.md`, «Pila»
- Decisió de l'equip del 27/10/2026
