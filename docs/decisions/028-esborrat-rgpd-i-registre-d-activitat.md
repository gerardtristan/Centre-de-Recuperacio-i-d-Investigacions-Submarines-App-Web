# 028 — Esborrat RGPD i registre d'activitat

- **Data:** 27/10/2026
- **Estat:** Acceptada (resol P-36). Els terminis exactes de conservació estan [A validar amb la gestoria].

## Context
El registre d'activitat «no es pot modificar ni esborrar» i guarda el valor anterior de cada canvi, que pot ser una dada personal (funcionalitats §2). Alhora, el soci pot demanar l'esborrat de les seves dades (context §9, checklist H3), i la llei obliga a conservar algunes dades (factures, cobraments).

## Alternatives
- Esborrar físicament la persona i les seves entrades del registre: trenca la traçabilitat dels diners.
- No esborrar res: no compleix el dret a l'esborrat.
- Anonimitzar, bloquejar el que obliga la llei i substituir la identificació al registre.

## Decisió
1. **Esborrar** vol dir desactivar els comptes de la persona i **anonimitzar** les seves dades personals.
2. **Excepció:** les dades que la llei obliga a conservar (factures i cobraments) es **bloquegen**: no es mostren ni es fan servir, excepte per complir obligacions legals. En acabar el termini legal, **es destrueixen**. Terminis exactes [A validar amb la gestoria].
3. **Registre d'activitat:** no es modifica (accions, dates i objectes es mantenen), però el que identifica la persona se substitueix per una **referència anònima**.
4. Substitueix la proposta de la spec 00 v1 de «no esborrar mai un compte».

## Conseqüències
- Cal una tasca periòdica que destrueixi les dades bloquejades quan venç el termini, i que ho deixi al registre amb la referència anònima.
- Qui pot consultar les dades bloquejades s'ha de fixar (proposta a la spec 00: tresorer i administrador).

## Fonts
- Resolució de P-36 comunicada per l'equip el 27/10/2026 (revisió del commit 8156443)
- `docs/funcionalitats-processos/funcionalitats-processos.docx`, §2 i §9.4
- `docs/context-projecte.md`, §9; `docs/checklist-produccio.md`, H3
