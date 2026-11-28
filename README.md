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
| Codi | Fet (01/11/2026): esquelet Django + HTMX (T-M01-03); `Person` i el model d'usuari `Account` (T-M01-04); entrades separades de socis i d'administració amb TOTP obligatori a l'administració, codis de recuperació i bloqueig per intents (T-M01-05, en part; el 03/11/2026 s'hi afegeixen la verificació del correu, la contrasenya nova amb l'enllaç de recuperació, el doble factor opcional del compte personal, la preparació del restabliment per un altre administrador i la prova de càrrega de C3; el mateix dia, amb la decisió 065, s'hi afegeixen la pantalla per demanar l'enllaç, el reenviament de la verificació amb límits i l'acció de restabliment; queden el CI i la revisió). Rols i permisos de la 059 (T-M01-06, T-RP-01 i T-RP-04; T-RP-02 en part): catàleg al codi, matriu inicial de la 00 i del 01 com a dades, motor per rol, objecte i camp, regles protegides i administrador operatiu. Registre d'activitat immutable (T-M01-07, 02/11/2026): bloquejat a l'ORM i a PostgreSQL, amb els rols actius de qui actua i els esdeveniments d'entrada, TOTP i rols. Textos legals i consentiments amb versió i canal (T-M01-08). Càrrec, pagament i departament bàsics amb les transicions de RN-67 (T-M01-09). Preparada per traduir-se amb el català com a única llengua activa (T-M01-09b, decisió 061). Següent: T-M01-10 (correu mínim i fitxers privats) |
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
  esborranys/                  esborranys a validar, no vigents (terminis de conservació, textos legals)
  funcionalitats-processos/    funcionalitats i processos per mòdul (.pdf i .docx)
  context/                     fonts originals (instruccions; entrevistes fora de Git)
  diari-de-construccio/        una entrada per tasca acabada, índex i captures
  guies/                       guies d'ús per a la secretaria, el tresorer i els socis (esborranys, T-M01-29, T-M04-19, T-M05b-20)
  entregues/                   lliuraments de l'assignatura
  arxiu/                       versions antigues (mai s'esborren), p. ex. context v3
/deploy/proves/                 servidor de proves al portàtil (Docker, túnel i scripts; decisió 099)
/specs/                        spec 00 (vigent fins que el 00 tingui secció a planning.md; la 04 és a l'arxiu)
/design/                       mapa de la plataforma i arbre de processos (HTML)
  wireframes/                  prototips de les pantalles (HTML, amb els tokens de static/)
  recorreguts/                 índex dels recorreguts pels wireframes (index.html, obert des del disc);
                               dades a recorreguts.json i comprovació amb `python design/recorreguts/comprova.py`
  extern/                      recursos de disseny externs, els zip originals sense canvis (pla a docs/plans/recursos-disseny-extern.md)
/assets/marca/                 logotips del club
/config/                       projecte Django: settings per entorn (base, dev, prod, test) i URL
/apps/                         core (base comuna, 00), accounts (comptes), members (socis, 01)
/templates/                    plantilles de Django
/static/                       fitxers estàtics; vendor/htmx i vendor/sortablejs servits des del VPS (046, 106)
/.github/workflows/ci.yml      pipeline: lint, migracions, proves, check --deploy, gitleaks
```

## Documents clau
- [Context del projecte](docs/context-projecte.md)
- [Funcionalitats i processos (PDF)](docs/funcionalitats-processos/funcionalitats-processos.pdf)
- [Metodologia SDD](docs/metodologia-sdd.md)
- [Checklist de producció](docs/checklist-produccio.md)
- [Arquitectura d'integracions](docs/arquitectura-integracions.md)
- [Decisions](docs/decisions/) · [Pendents de validar](docs/decisions/pendents.md)
- [Diari de construcció](docs/diari-de-construccio/README.md)
- Guies d'ús (esborrany, pendents de revisió): [secretaria](docs/guies/guia-secretaria.md) · [tresorer](docs/guies/guia-tresorer.md) · [tresoreria](docs/guies/guia-tresoreria.md) · [remeses, retornats i devolucions](docs/guies/guia-cobraments.md) · [ajuda per als socis: pagar la quota](docs/guies/ajuda-socis-pagaments.md) · [servidor de proves al portàtil](docs/guies/servidor-de-proves-al-portatil.md)
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

Correu i cua de tasques (T-M01-10): els correus es posen a la cua i els envia el procés de la cua, `python manage.py procrastinate worker` (amb `--one-shot`, buida la cua i s'atura; a Windows funciona, però sense gestionar els senyals del sistema). En local van a la bústia de proves **Mailpit**, una eina de desenvolupament que no forma part del repositori: es baixa l'executable de [mailpit](https://github.com/axllent/mailpit/releases), s'engega amb `mailpit --smtp 127.0.0.1:1025 --listen 127.0.0.1:8025` i els correus es veuen a http://127.0.0.1:8025. No envia res fora de l'ordinador. Correu de prova: `python manage.py send_test_email proves@example.org`. Les proves automàtiques fan servir el correu en memòria de Django. Límit diari (T-M00-06): amb `EMAIL_DAILY_LIMIT` enviaments en un dia (300 per defecte), els correus queden «ajornats» i tornen a la cua l'endemà per l'ordre de prioritat de la seva plantilla, que es declara a `apps/core/mail.py` (`TEMPLATE_PRIORITIES`); una plantilla nova sense prioritat declarada fa fallar les proves. Els fitxers privats, fora de producció, van a `var/fitxers-privats/` (fora de Git).

Dades inventades per a captures, demostracions i la revisió conjunta ([diari de l'eina](docs/diari-de-construccio/eina-seed_demo_data.md), [T-M01-27](docs/diari-de-construccio/T-M01-27.md)): sobre una base de dades local, nova i migrada (`python manage.py migrate`), `python manage.py seed_demo_data` (llavor 1954 per defecte; `--seed N` per canviar-la). Crea persones fictícies (correus `@example.org`, documents `PROVA…`), textos legals de prova (els del butlletí i de les imatges, provisionals i marcats [A validar]), consentiments i càrrecs en diversos estats, i els socis de cada cas de la revisió (pagats, exempt, importats de Cluber, impagat, canvis de tipus, baixes, menors i altes pendents) amb quotes, carnets i llicències. Escriu també una exportació de Cluber inventada, sense cap IBAN, a la carpeta temporal del sistema (`--cluber-file RUTA` per triar-ne una altra); com que la base ja té una importació confirmada, per provar-ne la previsualització cal una altra base nova amb `--without-cluber-batch`. Es nega a executar-se fora de `config.settings.dev` o `.test`, sense `DEBUG`, amb una base de dades que no sigui local o que no sigui buida, i llavors no crea res. **Comptes de prova** (074, punt 21): `admin-demo`, `secretaria-demo`, `tresorer-demo`, `president-demo` i `instructor-demo` per a l'administració (`/gestio/entrar/`), i comptes personals per a alguns socis (`/entrar/`, amb el correu que imprimeix l'ordre); tots amb la contrasenya de proves `contrasenya-de-proves-1954`. Els d'administració porten el mateix secret TOTP **de prova i públic**, `PROVESCRISNOESSECRETPROVESCRIS22`: afegeix-lo a una app d'autenticació o calcula el codi amb `python -c "import pyotp; print(pyotp.TOTP('PROVESCRISNOESSECRETPROVESCRIS22').now())"`. L'ordre imprimeix tots aquests accessos. Amb un sol administrador, la plataforma avisa que n'hi ha menys de dos d'operatius: és el comportament esperat.

## Responsables
- Desenvolupament i documentació: equip de l'assignatura.
- Responsable de manteniment a la junta: [A validar].
