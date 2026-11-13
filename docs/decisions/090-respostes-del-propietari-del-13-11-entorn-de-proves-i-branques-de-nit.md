# 090. Respostes del propietari del 13/11/2026: entorn de proves, branques de nit i estat de les tasques

- **Data:** 13/11/2026
- **Estat:** Acceptada (propietari, instrucció escrita del 13/11/2026)
- **Origen:** preguntes F-001 i F-002 del [tauler](tauler-preguntes.yml) i resum de la primera sessió de la prova d'acceleració ([089](089-prova-d-acceleracio-interruptors-d1-a-d6.md)).

## Decisió

1. **Entorn de proves (F-001): opció A.** Un servidor CX23 temporal de Hetzner, a Alemanya, amb una adreça provisional i només dades inventades. Cost aprovat: uns 3 € durant la prova (5,99 €/mes sense IVA). Es crea quan el propietari hagi obert el compte de Hetzner i ho avisi; fins llavors no es crea res. Es destrueix quan s'acabi la prova, si no es decideix una altra cosa.
2. **Branques de nit (F-002): arxivades amb una etiqueta.** Les cinc branques de nit de l'11/11/2026 ja eren a `master`. Queden a les etiquetes `arxiu/night-2026-11-11-ui`, `-correu`, `-guest`, `-rgpd` i `-simp`, que són al repositori després de passar l'escaneig de secrets. Les branques locals i les seves carpetes de treball, que no tenien cap canvi sense desar, s'han esborrat.
3. **PR de risc alt aprovades:** la 12 (T-M05a-03, adaptador del proveïdor de pagaments i proveïdor fals) i la 15 (T-M04-01, comptes de tresoreria).
4. **L'estat de les tasques passa a [`docs/estat/`](../estat/README.md)** i la línia cronològica el llegeix d'allà. Les tasques del 00 i del 01 s'hi passen tal com les llegia la línia cronològica; les que eren «feta en part» o «implementada, pendent de validació» hi consten com a «en curs».

## Conseqüències

- F-001 i F-002 surten del tauler.
- Partir les tasques «en curs» del 00 i del 01 en una part feta i una de bloquejada (apartat 2.5 del [pla d'acceleració](../plans/pla-acceleracio.md)) queda per fer, cas per cas.
- Les branques de nit anteriors (`night/2026-11-09/…`, `night/2026-11-10`, `night/2026-11-11` i `night/2026-11-11-a11y`) no s'han tocat.

## Fonts

- Instrucció escrita del propietari del 13/11/2026.
