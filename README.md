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
| Especificacions de mòduls | Font única: [`docs/planning.md`](docs/planning.md) ([decisió 047](docs/decisions/047-planning-font-unica-de-l-especificacio.md)). Numeració fixa 00–13. 01, 04, 05a i 05b aprovats (ampliats per les decisions [049](docs/decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md), [050](docs/decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md), [052](docs/decisions/052-llicencia-font-unica-al-06.md), [053](docs/decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md), [054](docs/decisions/054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md) , [055](docs/decisions/055-ajustos-configurables-i-addendes.md) i [058](docs/decisions/058-respostes-fecdas-gestoria-i-cursos.md)); 02, 03, 06 i 09 (amb l'apartat d'ajuts) aprovats el 28/10/2026; [primer mòdul per construir](docs/planning.md#primer-modul): el 01, amb les peces de la 00 que necessita; ordre del dia per a la junta a l'apèndix. Spec 00 v2 a `specs/`; la spec 04 v2, a l'arxiu. Ordre ([decisió 024](docs/decisions/024-abast-minim-i-ordre-per-deixar-cluber.md)): 00 → 01 → 04 → 05a → 05b; després, 02, 03, 09, 06, 07, 08 |
| Codi | Fet (01/11/2026): esquelet Django + HTMX (T-M01-03); `Person` i el model d'usuari `Account` (T-M01-04); entrades separades de socis i d'administració amb TOTP obligatori a l'administració, codis de recuperació i bloqueig per intents (T-M01-05, en part: falten la verificació i la recuperació per correu, que depenen de la T-M01-10). Rols i permisos de la 059 (T-M01-06, T-RP-01 i T-RP-04; T-RP-02 en part): catàleg al codi, matriu inicial de la 00 i del 01 com a dades, motor per rol, objecte i camp, regles protegides i administrador operatiu. Registre d'activitat immutable (T-M01-07, 02/11/2026): bloquejat a l'ORM i a PostgreSQL, amb els rols actius de qui actua i els esdeveniments d'entrada, TOTP i rols. Textos legals i consentiments amb versió i canal (T-M01-08). Càrrec, pagament i departament bàsics amb les transicions de RN-67 (T-M01-09). Preparada per traduir-se amb el català com a única llengua activa (T-M01-09b, decisió 061). Següent: T-M01-10 (correu mínim i fitxers privats) |
| Comptes de proveïdors | No creats. Tasques amb temps d'espera que han de començar ja: compte del proveïdor de pagaments en mode de proves (decisió 043; candidat PaynoPain [A verificar]), Bizum, exportació de prova de Cluber, comunicació als socis (arquitectura, §9.3) |
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
  planning.md                  font única de l'especificació i el pla de cada mòdul (047)
  decisions/                   una decisió per fitxer (NNN-nom.md) i pendents.md
  funcionalitats-processos/    funcionalitats i processos per mòdul (.pdf i .docx)
  context/                     fonts originals (instruccions; entrevistes fora de Git)
  entregues/                   lliuraments de l'assignatura
  arxiu/                       versions antigues (mai s'esborren), p. ex. context v3
/specs/                        spec 00 (vigent fins que el 00 tingui secció a planning.md; la 04 és a l'arxiu)
/design/                       mapa de la plataforma i arbre de processos (HTML)
/assets/marca/                 logotips del club
/config/                       projecte Django: settings per entorn (base, dev, prod, test) i URL
/apps/                         core (base comuna, 00), accounts (comptes), members (socis, 01)
/templates/                    plantilles de Django
/static/                       fitxers estàtics; vendor/htmx servit des del VPS (046)
/.github/workflows/ci.yml      pipeline: lint, migracions, proves, check --deploy, gitleaks
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
Requisits: Python 3.12 i, per a la base de dades local, Docker (o un PostgreSQL 16 propi).

```bash
python -m venv .venv && source .venv/Scripts/activate   # Linux/macOS: .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # i omple-hi els valors (mai dades reals)
docker compose up -d db         # PostgreSQL local
python manage.py runserver      # http://localhost:8000
pytest                          # proves
ruff check . && ruff format --check .   # lint
```

Base de dades: `python manage.py migrate`. Primer compte d'administrador: `python manage.py createsuperuser` (entra amb nom d'usuari, mai amb correu). L'àrea de socis és a `/entrar/`; l'administració, a `/<ADMIN_URL_PATH>/entrar/` (per defecte `/gestio/entrar/`), on la primera entrada demana donar d'alta el TOTP i mostra els 10 codis de recuperació una sola vegada. Desplegament, còpies i restauració: pendent (requisit A5 de la checklist).

## Responsables
- Desenvolupament i documentació: equip de l'assignatura.
- Responsable de manteniment a la junta: [A validar].
