# Metodologia de treball: Spec-Driven Development (versió C.R.I.S.)

## 1. Què és
Spec-Driven Development (SDD) vol dir escriure primer una especificació clara i fer-la servir com a font de veritat: d'ella surten el pla tècnic, les tasques, el codi, les proves i la documentació. La persona passa de picar codi a definir què es vol i revisar el resultat. Té sis fases: constitució, especificar, aclarir, planificar, tasques, implementar i iterar. Si alguna cosa canvia després, es modifica primer l'especificació.

## 2. Com encaixa amb el que ja tenim
| Fase SDD | Fitxer | Què és al projecte C.R.I.S. |
|---|---|---|
| Constitució | constitution.md | Instruccions del projecte + checklist de producció (portes 0-3) + decisions d'arquitectura |
| Especificar | specs/NN-modul/spec.md | Funcionalitats i processos de cada mòdul (què i per què, històries d'usuari, criteris d'acceptació) |
| Aclarir | secció «Preguntes obertes» de cada spec | Les decisions marcades [A validar] i les respostes de les entrevistes |
| Planificar | specs/NN-modul/plan.md, data-model.md | Arquitectura de backend, entitats, contractes d'API, dependències |
| Tasques | specs/NN-modul/tasks.md | Tasques de 1-4 hores, una per canvi, ordenades per dependències; cadascuna és un issue |
| Implementar | codi + proves | El codi i les proves es generen i es revisen contra l'especificació |

## 3. Estructura del repositori
```
/constitution.md
/README.md
/docs/checklist-produccio.md
/docs/context-projecte.md
/specs/
  00-base-comuna/      spec.md  plan.md  data-model.md  tasks.md
  01-socis-carnet/     ...
  02-activitats-cursos-sortides/ ...
  03-material/         ...
  04-tresoreria/       ...
  05-pagaments/        ...
  06-llicencies/       ...
  07-web-publica/      ...
  08-dashboard/        ...
/backend/
/frontend/
```

## 4. Esborrany de constitution.md
- Meta: plataforma app-web pròpia per al C.R.I.S.; primer web (PWA), app més endavant.
- Idioma: català per a documents i interfície.
- Abast: només els mòduls de l'especificació aprovada; res d'un mòdul sense spec revisada.
- Decisions pendents: si una spec té una pregunta oberta que afecta una regla de negoci, no s'implementa aquesta part; es pregunta.
- Diners: imports en cèntims, moviments immutables, correccions amb anul·lació, marge = ingressos - despeses - cost de material.
- Dades: persona separada de soci; dades de salut fora; només dades de prova fora de producció.
- Seguretat: autenticació i permís a cada endpoint, doble factor per a administradors, secrets fora del repositori, registre d'activitat.
- Arquitectura: monòlit modular; una app no escriu als models d'una altra, només a través de serveis.
- Proves: cada criteri d'acceptació té una prova; càlculs econòmics amb cobertura completa.
- Definició de fet: pipeline verd, proves passades, porta corresponent de la checklist revisada, documentació actualitzada.
- Canvis: es modifica primer l'especificació i després el codi.

## 5. Plantilla d'especificació (spec.md)
1. Context i objectiu del mòdul
2. Rols i permisos
3. Històries d'usuari
4. Criteris d'acceptació (Donat... Quan... Llavors...)
5. Regles de negoci
6. Entitats i camps
7. Casos límit, estats buits i errors
8. Requisits no funcionals (rendiment, privacitat, accessibilitat)
9. Fora d'abast
10. Preguntes obertes ([A validar]) amb responsable i data
11. Proves derivades

## 6. Flux per mòdul i punts de control
1. Escriure la spec (revisió: la persona de la junta responsable del mòdul).
2. Aclarir: respondre les preguntes obertes (revisió: equip).
3. Pla tècnic (revisió d'arquitectura: l'equip abans de generar codi).
4. Tasques de 1-4 hores (revisió d'ordre i abast).
5. Implementar tasca a tasca: codi + proves; es fusiona només si ho validen la IA i una persona.
6. Si canvia una regla, es revisa primer la spec.

## 7. Quanta formalitat per a cada tipus de canvi
- Especificació completa (constitució, spec revisada, pla, tasques): finances, pagaments, autenticació i permisos, RGPD, importacions i qualsevol canvi que afecti diversos mòduls.
- Especificació lleugera (una pàgina amb criteris d'acceptació i llista de tasques): mòduls de risc mitjà com contingut web, dashboard o conferències.
- Sense spec (ticket, canvi i proves): errors petits, textos, ajustos visuals i proves de concepte descartables.

## 8. Ordre d'especificació
00 base comuna → 01 socis i carnet → 02 activitats (cursos i sortides) → 03 material → 04 tresoreria i marge → 05 pagaments → 06 llicències → 07 web pública → 08 dashboard.

## 9. Riscos de la metodologia i com els evitem
- Sobrecàrrega de documents: només spec completa quan el risc ho justifica i un màxim d'una spec revisada per setmana per persona.
- Especificacions massa grans: descompondre un mòdul abans de planificar-lo.
- Requisits vagues emmagatzemats en markdown: cada criteri s'escriu de manera comprovable i s'aclareix amb la junta.
- Divergència entre spec i codi: revisar la spec a cada canvi de regla i comparar-la amb el codi abans de tancar el mòdul.
