# Plataforma C.R.I.S.

Plataforma web pròpia per al C.R.I.S. (Centre de Recuperació i Investigacions Submarines, club de busseig sense ànim de lucre fundat el 1954). Centralitza socis, cursos, sortides, material, tresoreria, llicències, web pública i dashboard en una sola base de dades, i calcula sola el marge de cada activitat.

Projecte de l'assignatura Emprenedoria Digital (Grau en Empresa i Tecnologia, UAB, curs 26-27) amb client real.

## Objectiu
Dissenyar i construir, per mòduls prioritzats i validats amb la junta, una plataforma que substitueixi el creuament manual entre Cluber, el banc, Excel, Gmail i WhatsApp, i deixar-la documentada perquè el club en pugui continuar el desenvolupament i el manteniment. Context complet: [docs/context-projecte.md](docs/context-projecte.md).

## Estat actual (27/10/2026)
| Àmbit | Estat |
|---|---|
| Context, entrevistes i funcionalitats | Fets; funcionalitats pendents de validació de la junta |
| Metodologia (SDD) i checklist de producció | Definides |
| Arquitectura d'integracions | Proposada: [docs/arquitectura-integracions.md](docs/arquitectura-integracions.md) |
| Decisions | Registrades a [docs/decisions/](docs/decisions/); contradiccions a [pendents.md](docs/decisions/pendents.md) |
| Especificacions de mòduls (`specs/`) | No començades. Ordre proposat a l'arquitectura, §9 |
| Codi (`backend/`, `frontend/`) | No començat (no s'hi crea res fins que hi hagi una spec revisada) |
| Comptes de proveïdors | No creats. Llista de tasques manuals a l'arquitectura, §7 |

## Mapa de carpetes
```
/README.md                     aquest fitxer
/CLAUDE.md                     instruccions per a l'assistent (constitució del projecte)
/docs/
  context-projecte.md          context del club (Markdown del context v3)
  checklist-produccio.md       portes de qualitat 0-3
  metodologia-sdd.md           com es treballa amb especificacions
  arquitectura-integracions.md components, proveïdors, fluxos de pagament, riscos
  decisions/                   una decisió per fitxer (NNN-nom.md) i pendents.md
  funcionalitats-processos/    funcionalitats i processos per mòdul (.pdf i .docx)
  context/                     fonts originals (context, instruccions; entrevistes fora de Git)
  entregues/                   lliuraments de l'assignatura
  arxiu/                       versions antigues (mai s'esborren)
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
