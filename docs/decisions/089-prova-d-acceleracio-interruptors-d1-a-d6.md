# 089. Prova d'acceleració: sis decisions amb interruptor (D1 a D6)

- **Data:** 13/11/2026
- **Estat:** Acceptada com a **prova de dues setmanes** (propietari, instrucció escrita del 13/11/2026). Inici: 13/11/2026. Revisió: 27/11/2026; llavors el propietari decideix si es manté.
- **Origen:** [pla d'acceleració](../plans/pla-acceleracio.md), apartat 9 (PR 8). El propietari n'aprova les sis decisions amb l'opció recomanada a cadascuna.
- **Numeració:** els números 087 i 088 no es fan servir a `master` perquè ja els té la branca aparcada del mòdul 02 (D6). Aquesta branca també té un 086 propi, diferent de la [086](086-tauler-de-preguntes-pendents.md) de `master`; s'haurà de renumerar quan torni.

## Context

El projecte té molt de codi i moltes proves d'un sol mòdul, cap entorn desplegat i moltes tasques que no es poden tancar. La diagnosi és a l'apartat 1 del pla. Les sis decisions canvien regles de treball; cap no canvia una regla de negoci de [`docs/planning.md`](../planning.md).

## Decisió

Cada decisió té un **interruptor** a [`CLAUDE.md`](../../CLAUDE.md) («Prova d'acceleració»), que diu la regla nova i la regla anterior. L'estat vigent de cada interruptor és el que diu `CLAUDE.md`. Cada interruptor s'activa amb un commit propi titulat «DN (089): actiu», perquè una decisió es pugui desfer sense tocar les altres.

| # | Decisió | Regla nova (interruptor actiu) | Regla anterior (interruptor inactiu) |
|---|---|---|---|
| **D1** | Especificació de la fase 1 congelada | Les seccions i les addendes del 01, el 04, el 05a i el 05b queden com són a l'etiqueta `spec-fase1-v1`. Un canvi nou va a [`pendents.md`](pendents.md) i no atura la feina. L'estat de les tasques s'apunta a `docs/estat/`, no a la fila del pla | Un canvi de regla s'escriu primer al pla, amb una addenda; l'estat de cada tasca és a la seva fila |
| **D2** | Tres tipus de dubte | Un dubte reversible o configurable es construeix amb una opció per defecte. Un d'irreversible es construeix apagat i no s'activa a producció sense resposta. Cada dubte nou va al tauler de preguntes ([086](086-tauler-de-preguntes-pendents.md)) amb opcions A a D i la recomanació | Una pregunta oberta que afecta una regla de negoci atura aquella part fins que es respon |
| **D3** | Llesques verticals | La fase 1 es construeix per llesques que travessen el 04, el 05a i el 05b, començant pel primer cobrament amb un proveïdor fals (apartat 3 del pla) | Mòdul sencer darrere mòdul sencer: 04 → 05a → 05b ([024](024-abast-minim-i-ordre-per-deixar-cluber.md), [060](060-ajustos-de-l-auditoria-del-pla.md)) |
| **D4** | Classes de PR per risc | Cada PR porta l'etiqueta `risc:baix`, `risc:mitja` o `risc:alt`. Les de risc baix i mitjà es fusionen amb el CI verd i una revisió automàtica. El propietari aprova abans les de risc alt | Res no es fusiona sense la validació d'una persona ([metodologia](../metodologia-sdd.md), §6) |
| **D5** | Baranes: cobertura i entorn de proves | El CI mesura la cobertura amb `pytest-cov` i falla si baixa del llindar. L'entorn de proves temporal està aprovat, però no es crea fins que el propietari digui que sí al cost | La cobertura no es mesura; l'aplicació només corre en local |
| **D6** | Branca del mòdul 02 aparcada | `feature/t-m02-activitats` queda aparcada amb una etiqueta. No s'hi treballa ni es fusiona fins que existeixi la llesca del primer cobrament. No s'esborra | S'hi pot continuar treballant |

### Precisions

- **Risc alt (D4):** tot el que toca diners, pagaments i notificacions del proveïdor, permisos, autenticació i sessions, RGPD i anonimització, xifratge, importacions, migracions de base de dades, dependències noves, el CI, `CLAUDE.md` i les regles del pla.
- **Mida (D4):** menys de 800 línies canviades per PR i, com a màxim, 400 de codi d'aplicació (sense proves, migracions ni plantilles).
- **Límit de la revisió automàtica (D4):** GitHub no pot exigir l'aprovació del propietari quan les PR s'obren des del seu mateix compte. La regla «el propietari aprova abans les de risc alt» la compleix qui fusiona: no fusiona una PR `risc:alt` sense un sí escrit del propietari.
- **Nom de les llesques (D3):** el propietari anomena «llesca 1» la que travessa el 04, el 05a i el 05b. És la «llesca 2, el primer euro» de l'apartat 3 del pla. La llesca del mòdul 01 del pla és un tancament, no codi nou.
- **Tipus de dubte (D2):** *reversible* (un text, un detall de comportament que es canvia sense tocar dades), *configurable* (un valor, que va a «Ajustos», [055](055-ajustos-configurables-i-addendes.md)) i *irreversible* (diners, model de dades que afecta dades reals, RGPD, seguretat, permisos i el que veurà un soci real). A `pendents.md` s'escriuen amb la paraula sencera, perquè la «R» de la seva llegenda vol dir una altra cosa.
- **El que no canvia:** dades personals només dins la UE, cap dada real fora de producció, plans sense dates, tot en català, les portes de producció i l'autorització de la junta per als nivells 1 i 2.

## Com es revoca una decisió

Si el propietari escriu «revoca la decisió N», en un sol commit titulat «DN (089): revocada»:

1. l'interruptor DN de `CLAUDE.md` passa a **inactiu**;
2. es restaura la regla anterior d'aquell punt, desfent el que diu la taula següent (o amb `git revert` dels commits «DN (089): …»);
3. s'afegeix una fila al registre d'estat d'aquesta decisió i s'actualitza l'índex de decisions.

No es toca cap altre interruptor.

| # | En revocar |
|---|---|
| D1 | Es treu la nota de congelació del cap de `planning.md`. L'estat de les tasques apuntat a `docs/estat/` es copia a les files del pla. L'etiqueta `spec-fase1-v1` es conserva com a referència |
| D2 | Es treu el paràgraf de D2 de `pendents.md`. Cada dubte construït amb una opció per defecte es revisa amb el propietari. Els interruptors de configuració apagats es queden apagats |
| D3 | Les tasques pendents del 04, el 05a i el 05b es reprenen per ordre de mòdul. El que ja és a `master` s'hi queda |
| D4 | Tota PR torna a necessitar l'aprovació d'una persona abans de fusionar-se. Les etiquetes i la plantilla es poden conservar com a informació |
| D5 | Es treuen el llindar i `pytest-cov` del CI i de `pyproject.toml`. Si l'entorn de proves existeix, es destrueix |
| D6 | Es treu la nota d'aparcament. La branca es pot reprendre. L'etiqueta es conserva |

## Registre d'estat

Només s'hi afegeixen files.

| Data | Interruptor | Canvi | Motiu |
|---|---|---|---|
| 13/11/2026 | D1 a D6 | Aprovades com a prova de dues setmanes; cada una s'activa amb el seu commit | Instrucció escrita del propietari |
| 16/11/2026 | D4 | Les `risc:alt` també les fusiona Claude, amb condicions; fins a tres carrils sense confirmació per tasca ([094](094-fusio-de-les-risc-alt-i-tres-carrils.md)) | Instrucció escrita del propietari |
| 19/11/2026 | D4 | Fins al 27/11/2026, les `risc:alt` es fusionen soles amb condicions; esperen el sí del propietari les de producció o dades i diners reals, `CLAUDE.md`, D1 a D6, rebaixar el CI i secrets o xifratge ([100](100-risc-alt-es-fusionen-soles-fins-al-final-de-la-prova.md); modifica la [098](098-risc-alt-nomes-amb-el-si-escrit-del-propietari.md)) | Instrucció escrita del propietari |

## Conseqüències

- `CLAUDE.md` i la [metodologia](../metodologia-sdd.md) (§10) porten les regles noves al costat de les anteriors.
- La protecció de `master`, les etiquetes de risc i l'etiqueta de la branca aparcada són configuració de GitHub o de Git, no fitxers: s'anoten a la PR que les crea.
- Al final de cada sessió es deixa un resum de cinc línies per al propietari: què s'ha fusionat sense ell, què espera la seva aprovació i quines preguntes noves hi ha al tauler.

## Fonts

- [Pla d'acceleració](../plans/pla-acceleracio.md), PR 8.
- Instrucció escrita del propietari del 13/11/2026.
