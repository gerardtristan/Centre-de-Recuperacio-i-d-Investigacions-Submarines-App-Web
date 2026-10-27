# 047 — `docs/planning.md` és la font única de l'especificació de cada mòdul

- **Data:** 27/10/2026
- **Estat:** Acceptada. Amplia la [008](008-metodologia-sdd.md) (metodologia): canvia **on** s'escriu l'especificació, no el flux de treball.

## Context
- CLAUDE.md i la metodologia preveien una carpeta `specs/NN-modul/` per mòdul, amb `spec.md`, `plan.md`, `data-model.md` i `tasks.md`.
- Només existeixen `specs/00-base-comuna/spec.md` i `specs/04-tresoreria/spec.md`. El pla del mòdul 01 es va escriure a `docs/planning.md` amb una plantilla de 14 seccions que ja inclou intenció, entitats, regles, contractes, criteris, tasques i proves.
- Tenir la mateixa regla en dos llocs fa que un dels dos quedi desfasat.

## Alternatives
- Mantenir `specs/NN/` i que `planning.md` només hi enllaci.
- Extreure de `planning.md` un `spec.md` per mòdul.
- **Fer de `planning.md` la font única** i no duplicar-ne el contingut.

## Decisió
- **`docs/planning.md` és la font única de l'especificació i del pla de cada mòdul.** La secció del mòdul (14 seccions) substitueix `spec.md`, `plan.md`, `data-model.md` i `tasks.md`.
- **No es duplica el contingut:** cap altre fitxer copia regles, criteris ni tasques d'un mòdul; com a molt, hi enllaça per l'àncora estable (per exemple, `planning.md#M01-7-regles`).
- **Una secció de mòdul aprovada** compleix el punt 1 de CLAUDE.md («no s'escriu codi sense especificació revisada»).
- **Specs existents:**
  - `specs/00-base-comuna/spec.md` (v2) continua sent la font del mòdul 00 fins que el mòdul 00 tingui secció aprovada a `planning.md`. No s'edita.
  - `specs/04-tresoreria/spec.md` (v2) és la font de la secció M04 de `planning.md`. Quan la secció M04 s'aprovi, la spec 04 passa a ser històrica: es mou a `docs/arxiu/` (les versions antigues no s'esborren mai) i el que en quedi vigent és a `planning.md`. Els identificadors de la spec 04 (RN-T, CA-T, VT, QT) es mantenen perquè ja els citen altres documents.
- **Canvis de regla:** primer es canvia la secció de `planning.md` i després el codi (CLAUDE.md, punt 4).

## Conseqüències
- CLAUDE.md apunta a `docs/planning.md` en lloc de `specs/NN-modul/`.
- La metodologia ([`metodologia-sdd.md`](../metodologia-sdd.md)) s'ha d'alinear en un canvi posterior; mentre no es faci, mana aquesta decisió.
- `planning.md` creixerà molt: les àncores estables i l'índex del principi són obligatoris.

## Fonts
- Aprovació del pla del mòdul 01, resposta 6, comunicada pel responsable del projecte el 27/10/2026
