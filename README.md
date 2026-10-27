# Plataforma C.R.I.S.

Plataforma web pròpia per al C.R.I.S. (Centre de Recuperació i d'Investigacions Submarines, club de busseig sense ànim de lucre fundat el 1954). Centralitza socis, cursos, sortides, material, tresoreria, llicències, web pública i dashboard en una sola base de dades, i calcula sola el marge de cada activitat.

Projecte de l'assignatura Emprenedoria Digital (Grau en Empresa i Tecnologia, UAB, curs 26-27) amb client real. Domini de la plataforma: cris1954.cat. Es treballa per mòduls i passos.

## Objectiu
Dissenyar i construir, per mòduls prioritzats i validats amb la junta, una plataforma que substitueixi el creuament manual entre Cluber, el banc, Excel, Gmail i WhatsApp, i deixar-la documentada perquè el club en pugui continuar el desenvolupament i el manteniment. Context complet: [docs/context-projecte.md](docs/context-projecte.md).

## Estat actual (27/10/2026)
| Àmbit | Estat |
|---|---|
| Context | v4 del 27/10/2026 a [docs/context-projecte.md](docs/context-projecte.md); el v3 és a `docs/arxiu/` |
| Entrevistes i funcionalitats | Fetes. Al .docx de funcionalitats encara falten els textos de substitució de [pendents.md](docs/decisions/pendents.md) (P-22) |
| Metodologia (SDD) i checklist de producció | Definides; checklist actualitzada (C2, C4, C5, C9, G1) |
| Arquitectura d'integracions | Acceptada, v3: [docs/arquitectura-integracions.md](docs/arquitectura-integracions.md) |
| Decisions | 001-025 a [docs/decisions/](docs/decisions/). Resoltes: Cluber i entrada en producció, comptes i doble factor, convidats, pressupost (producció mínima), mètodes de pagament, comissions, domini (cris1954.cat), mandats (escenari base B, provisional) |
| Pendents de la junta | [pendents.md](docs/decisions/pendents.md): creditor i cost de Cluber (P-21, P-27), calendari de quotes (P-29), llicències a Cluber (P-28), socis menors (P-33), accés al DNS (P-25) i altres |
| Especificacions de mòduls (`specs/`) | No començades. Ordre aprovat ([decisió 024](docs/decisions/024-abast-minim-i-ordre-per-deixar-cluber.md)): 00 → 01 → 04 mínim → 05a → 05b; després, 02, 03, resta de la 04, 06, 07, 08 |
| Codi (`backend/`, `frontend/`) | No començat (no s'hi crea res fins que hi hagi una spec revisada) |
| Comptes de proveïdors | No creats. Tasques amb temps d'espera que han de començar ja: compte de Stripe en mode de proves i verificació, Bizum, exportació de prova de Cluber, comunicació als socis (arquitectura, §9.3) |
| Entrada en producció | Dos nivells ([decisió 025](docs/decisions/025-dos-nivells-de-produccio.md)). Nivell 1 (05a): només recollida de mandats, sense cobraments reals. Nivell 2 (05b acabat i provat): producció completa i migració única de Cluber. Objectiu orientatiu, no compromès: finals de gener o principis de febrer de 2027 |

## Mapa de carpetes
```
/README.md                     aquest fitxer
/CLAUDE.md                     instruccions per a l'assistent (constitució del projecte)
/docs/
  context-projecte.md          context del club (v4)
  checklist-produccio.md       portes de qualitat 0-3
  metodologia-sdd.md           com es treballa amb especificacions
  arquitectura-integracions.md components, proveïdors, fluxos de pagament, riscos
  decisions/                   una decisió per fitxer (NNN-nom.md) i pendents.md
  funcionalitats-processos/    funcionalitats i processos per mòdul (.pdf i .docx)
  context/                     fonts originals (instruccions; entrevistes fora de Git)
  entregues/                   lliuraments de l'assignatura
  arxiu/                       versions antigues (mai s'esborren), p. ex. context v3
/specs/                        una carpeta per mòdul (NN-modul/)
/design/                       mapa de la plataforma i arbre de processos (HTML)
/assets/marca/                 logotips del club
```

## Documents clau
- [Context del projecte](docs/context-projecte.md)
- [Funcionalitats i processos (PDF)](docs/funcionalitats-processos/funcionalitats-processos.pdf)
- [Metodologia SDD](docs/metodologia-sdd.md)
- [Checklist de producció](docs/checklist-produccio.md)
- [Arquitectura d'integracions](docs/arquitectura-integracions.md)
- [Decisions](docs/decisions/) · [Pendents de validar](docs/decisions/pendents.md)
- [Document incremental (vigent)](docs/entregues/document-incremental.pdf)

## Fitxers fora del repositori
`.gitignore` exclou secrets (`.env`, claus), dades reals, vídeos (`*.mp4`) i `docs/context/entrevistes.docx` (pot contenir dades personals; [A validar] fins que s'anonimitzi). Aquests fitxers existeixen a la carpeta compartida però no al control de versions.

## Instal·lar, executar, provar, desplegar, còpies i restauració
[Completar quan existeixi el codi; requisit A5 de la checklist.]

## Responsables
- Desenvolupament i documentació: equip de l'assignatura.
- Responsable de manteniment a la junta: [A validar].
