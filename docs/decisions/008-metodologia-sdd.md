# 008 — Metodologia Spec-Driven Development

- **Data:** el document de metodologia no porta data [A validar]; registrada el 27/10/2026
- **Estat:** Acceptada

## Context
Projecte amb poc temps (15 setmanes), un equip petit, codi generat en part amb assistència d'IA i un client que ha de validar les regles de negoci.

## Alternatives
- Desenvolupament directe a partir de les funcionalitats, sense especificacions per mòdul: més ràpid al principi, però amb risc de divergència i regles inventades.
- Especificació completa per a tot: massa documentació.
- SDD amb formalitat segons el risc.

## Decisió
- Cada mòdul segueix: constitució → especificar → aclarir → planificar → tasques → implementar. Si canvia una regla, es modifica primer l'especificació.
- Spec completa per a finances, pagaments, autenticació, permisos, RGPD i importacions; spec lleugera (una pàgina) per a contingut web, dashboard i conferències; només ticket per a errors petits.
- Les preguntes [A validar] que afecten regles de negoci bloquegen la implementació d'aquella part.

## Conseqüències
- Màxim d'una spec revisada per setmana i persona, per evitar la sobrecàrrega de documents.
- La constitució és `CLAUDE.md` (no hi ha `constitution.md` separat).

## Fonts
- `docs/metodologia-sdd.md`
- `CLAUDE.md`, «Com es treballa»
