# Arquitectura d'integracions — Plataforma C.R.I.S.

- **Versió:** 6 · 27/10/2026. Incorpora les decisions [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md) a [025](decisions/025-dos-nivells-de-produccio.md). El §9 (abast mínim per substituir Cluber i ordre de construcció) està **aprovat**.
- **Domini de la plataforma:** cris1954.cat ([019](decisions/019-domini-i-correu.md)).
- **Estat:** acceptada per l'equip; els punts marcats [A validar] i els de [decisions/pendents.md](decisions/pendents.md) continuen oberts.
- **Producció en dos nivells** ([025](decisions/025-dos-nivells-de-produccio.md)), cadascun amb autorització expressa de la junta:
  - **Nivell 1, mandats** (05a acabat i provat): Stripe en mode real només per recollir mandats; cap cobrament real.
  - **Nivell 2, producció completa** (05b acabat i provat): cobraments reals; llavors es migra Cluber una sola vegada i es deixa ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md)).
- **IBAN:** la plataforma no el guarda; Stripe en té la custòdia.
- **Abast:** com es connecta la plataforma amb els serveis externs (allotjament, base de dades, fitxers, correu, pagaments, còpies, DNS, monitoratge). No és una especificació de mòdul: cada mòdul afectat tindrà la seva a `specs/`.
- **Volum de referència:** uns 150 socis i uns 300 subscriptors del butlletí [A validar amb dades reals].
- **Decisions relacionades:** [002](decisions/002-pila-tecnologica.md) a [013](decisions/013-imputacio-comissions.md).

> Preus consultats el 27/10/2026, sense IVA. Tots són [A validar] abans de contractar: els proveïdors els canvien sovint.

---

## 1. Components i fluxos

```
                    Visitants, socis i junta (navegador / PWA al mòbil)
                         │                                │
                 HTTPS   │                                │  HTTPS (API REST, sessió + TOTP a l'admin)
                         ▼                                ▼
      ┌──────────────────────────────┐      ┌────────────────────────────────────────────┐
      │ Cloudflare                   │      │ VPS Hetzner (UE) · Coolify                 │
      │  · DNS del domini            │      │  ┌──────────────┐   ┌────────────────────┐ │
      │  · Pages: web pública + PWA  │─────▶│  │ Django + API │◀─▶│ PostgreSQL         │ │
      │    (estàtica, sense dades)   │ API  │  │ (monòlit)    │   │ (dades + cua de    │ │
      └──────────────────────────────┘      │  └──────┬───────┘   │  tasques)          │ │
                                            │         │           └─────────┬──────────┘ │
                                            │  ┌──────▼───────┐             │ bolcat     │
                                            │  │ Treballador  │             │ diari      │
                                            │  │ de tasques   │      ┌──────▼──────────┐ │
                                            │  └──┬───┬───┬───┘      │ restic (xifra)  │ │
                                            └─────┼───┼───┼──────────┴───┬────────┬────┘
                    URL signades (només lectura)  │   │   │              │        │
      ┌───────────────────────────────┐           │   │   │              │        │
      │ Scaleway Object Storage (París)│◀──────────┘   │   │              │        │
      │  · bucket privat de fitxers   │◀──────────────┼───┼──────────────┘        │
      │  · bucket de còpies (xifrades)│               │   │   còpia BD           │
      └───────────────┬───────────────┘               │   │                      │
                      │ còpia xifrada dels fitxers    │   │                      │
                      ▼                               │   │                      ▼
      ┌───────────────────────────────┐               │   │      ┌───────────────────────────┐
      │ Hetzner Storage Box (UE)      │◀──────────────┼───┼──────│ còpia BD (2a destinació)  │
      └───────────────────────────────┘               │   │      └───────────────────────────┘
                                                      │   │
      ┌───────────────────────────────┐   API / SMTP  │   │  API (crear pagament, devolució)
      │ Brevo (correu)                │◀──────────────┘   ▼
      │  · transaccionals             │      ┌───────────────────────────────────────────┐
      │  · butlletí (en tandes)       │      │ Stripe (formulari allotjat: targeta,      │
      └───────────────────────────────┘      │ Apple/Google Pay, Bizum, SEPA)            │
                                             │  ──webhook signat──▶ /api/stripe/webhook  │
                                             │  ──liquidacions────▶ compte bancari club  │
                                             └───────────────────────────────────────────┘
      ┌───────────────────────────────┐      ┌───────────────────────────────────────────┐
      │ UptimeRobot: comprova la web  │      │ Seguiment d'errors (GlitchTip o Sentry,   │
      │ i l'API cada pocs minuts      │      │ regió UE [A validar]), sense dades de     │
      │ → avís per correu             │      │ socis                                     │
      └───────────────────────────────┘      └───────────────────────────────────────────┘

      Fora de línia: extracte del banc en CSV → importació a tresoreria (conciliació)
```

### Fluxos principals

| Flux | Recorregut | Regla clau |
|---|---|---|
| Web pública | Navegador → Cloudflare Pages (HTML estàtic) → API per a llistats i formularis | Pages no guarda dades personals |
| Àrea de socis i administració | PWA → API Django (sessió) → PostgreSQL | Permís per rol i per objecte a cada endpoint; TOTP obligatori per a qualsevol compte que entri per l'administració ([018](decisions/018-perfil-comptes-i-rols.md)) |
| Fitxers | Pujada: navegador → API (valida tipus, mida i permís) → bucket privat. Descàrrega: API comprova el permís → URL signada de curta durada | Cap bucket públic amb dades personals |
| Correu | Esdeveniment → tasca a la cua → comptador diari → Brevo | Reserva per als transaccionals; el butlletí en tandes |
| Pagament | Càrrec pendent → sessió de Stripe → el participant paga al formulari de Stripe → **webhook signat** → tasca idempotent → pagament confirmat → ingrés i comissió a tresoreria | El navegador mai confirma un pagament |
| Conciliació | CSV del banc → importació → casament amb liquidacions de Stripe, transferències i despeses | Confirmació del tresorer |
| Còpies | Bolcat diari → xifrat al servidor → Scaleway i Storage Box; fitxers de Scaleway → Storage Box | Prova de restauració mensual fins a producció; després, trimestral |

---

## 2. Taula d'integracions

| Eina | Per a què | Regió de les dades | Cost mensual estimat | Pla actual | Límits rellevants | Via de sortida |
|---|---|---|---|---|---|---|
| **Hetzner Cloud** (VPS producció) | Django, PostgreSQL, cua, Coolify | Alemanya (Nuremberg o Falkenstein) | CX33 (4 vCPU, 8 GB): 8,99 €; CX23 (2 vCPU, 4 GB): 5,99 €; IPv4 inclosa | Cap (cal crear el compte) | Un sol servidor = punt únic de fallada. La pàgina consultada marcava els plans com a «no disponibles» temporalment [A validar] | Contenidors estàndard: es poden moure a qualsevol VPS amb Docker |
| **Còpies de Hetzner** | Imatge completa del VPS (recuperació ràpida) | Alemanya | Uns 20 % del VPS (≈1,20-1,80 €) | — | Mateix proveïdor que el servidor: no serveix si es perd el compte | Complementària; no és la còpia principal |
| **Hetzner Storage Box BX11** | Segona destinació de les còpies (BD i fitxers) | Alemanya o Finlàndia | 3,20 € (1 TB) | — | Accés per SFTP/rsync, compatible amb restic | Còpies xifrades en format restic, llegibles des de qualsevol lloc |
| **Coolify** | Desplegaments, variables d'entorn, bolcats programats | Al mateix VPS | 0 € (autoallotjat, codi obert) | — | Actualitzacions a càrrec del club | Fitxers Docker Compose estàndard |
| **PostgreSQL** | Base de dades única i cua de tasques | Al VPS | 0 € | — | Ha de tenir RAM suficient al mateix VPS | `pg_dump` estàndard |
| **Scaleway Object Storage** | Fitxers privats (factures, justificants, fotos, PDF) i bucket de còpies | França (París) | ≈0,0146 €/GB/mes (Standard Multi-AZ); per a uns 20 GB, < 1 € | — | Sortida de dades gratuïta fins a 75 GB/mes | API S3: es migra amb rclone a qualsevol proveïdor compatible |
| **Cloudflare Pages + DNS** | Web pública i PWA estàtiques; DNS de cris1954.cat (si el club en controla el DNS, P-25). Opció futura: Email Routing per als àlies d'administrador | Xarxa global; empresa dels EUA (transferència documentada, marc UE-EUA) [A validar] | 0 € | — | Pages no ha d'allotjar dades personals | HTML estàtic: qualsevol allotjament estàtic; DNS exportable en fitxer de zona |
| **Brevo** | Correu transaccional i butlletí. Remitent cris@cris.es, que també rep les respostes (decisió 085; abans, una adreça de cris1954.cat amb resposta a cris@cris.es, decisió 019) | França / UE | Gratuït: 0 € · Starter: des d'uns 9 $/mes (5.000 correus/mes, sense límit diari) [A validar a brevo.com] | Cap | Gratuït: 300 enviaments/dia sumant-ho tot; marca de Brevo als correus | Plantilles i llista de subscriptors viuen a la plataforma; canviar de proveïdor = canviar credencials SMTP/API |
| **Stripe** | Targeta, Apple Pay, Google Pay, Bizum, domiciliació SEPA | Entitat contractant a la UE (Irlanda); possibles transferències als EUA (documentades) [A validar al DPA] | 0 € fix; comissions per cobrament (§3) | Cap | Bizum s'ha d'activar al compte del club [A validar]; SEPA: devolucions sense motiu fins a 8 setmanes | Exportació de clients i pagaments; migració de mandats SEPA a demanar a Stripe [A validar] |
| **Transferència bancària** | Cobrament sense comissió de passarel·la | Banc del club | 0 € (comissions del banc [A validar]) | Compte existent | Conciliació amb CSV, no instantània | Independent de qualsevol proveïdor |
| **UptimeRobot** | Avís de caiguda de la web i l'API | Fora del VPS; ubicació de l'empresa [A validar] | 0 € (pla gratuït) | Cap | Només comprova URL públiques; no rep dades de socis | Qualsevol altre monitor extern |
| **GlitchTip o Sentry** | Seguiment d'errors amb traça | Sentry: Frankfurt (empresa dels EUA); GlitchTip: instància a la UE segons la seva web [A validar totes dues] | 0 € (GlitchTip: 1.000 esdeveniments/mes; Sentry: pla Developer) | Cap | La regió de Sentry no es pot canviar un cop creada l'organització | Tots dos fan servir el mateix SDK; GlitchTip es pot autoallotjar |
| **Domini cris1954.cat** | Plataforma i web nova (el remitent dels correus és a cris.es des de la decisió 085) | — | 0 € addicionals (ja pagat pel club) | Existent | Control del DNS [A validar, P-25] | Transferible a qualsevol registrador |
| **cris.es** | Adreça de contacte cris@cris.es (resposta dels correus) | — | No canvia | Existent | La plataforma no en toca el DNS | — |
| **cris.barcelona** | Web WordPress actual | — | No canvia | Existent | Redirecció cap a la web nova [A validar, P-25] | — |

### Afegits avaluats amb els cinc criteris
Cap eina de la decisió inicial canvia. Les tres peces afegides passen els criteris:

| Afegit | 1. UE o transferència documentada | 2. Doble factor per a administradors | 3. Cost | 4. Còpia restaurable | 5. Via de sortida |
|---|---|---|---|---|---|
| Hetzner Storage Box | Sí (DE/FI) | Sí (compte de Hetzner) | 3,20 €/mes | És la destinació de còpia | Format restic obert |
| UptimeRobot | No guarda dades personals | Sí | 0 € | No aplica (sense dades) | Substituïble en minuts |
| GlitchTip o Sentry | Regió UE [A validar] | Sí | 0 € | No aplica (dades efímeres) | Mateix SDK per a tots dos |

### Domini, DNS, correu i comptes d'accés ([018](decisions/018-perfil-comptes-i-rols.md), [019](decisions/019-domini-i-correu.md))
| Element | Configuració |
|---|---|
| Web pública i PWA | `cris1954.cat` (i `www`) → Cloudflare Pages |
| API i administració | Subdomini de cris1954.cat cap al VPS (per exemple, `api.`) [A validar el nom]. L'entrada d'administració és una ruta discreta de l'API |
| DNS | El club controla el DNS de cris1954.cat i de cris.es (confirmat el 27/10/2026); qui té l'accés concret [A validar, P-25]. **Recomanació** ([023](decisions/023-gestio-del-dns.md)): delegar la zona de cris1954.cat a Cloudflare després de fer inventari dels registres actuals, i guardar les credencials del registrador i de Cloudflare en un gestor de contrasenyes compartit amb dues persones |
| Correu sortint | Brevo amb remitent `cris@cris.es`, que també rep les respostes (decisió 085) |
| SPF | Registre TXT a **cris.es** que autoritza Brevo, sense treure el del servei de correu actual del club (decisió 085; cal accés al DNS de cris.es, P-25) |
| DKIM | Clau de Brevo publicada a **cris.es** (decisió 085) |
| DMARC | Registre a cris1954.cat; començar en mode d'observació i endurir-lo quan els informes estiguin nets (checklist G1) |
| cris.es | No es toca: només rep les respostes a cris@cris.es |
| cris.barcelona | Redirecció cap a cris1954.cat [A validar, P-25] |
| Comptes de soci | Entren amb el correu personal (únic); verificació i recuperació per correu |
| Comptes d'administrador | Entren amb nom d'usuari per l'entrada d'administració; doble factor obligatori; correu només per a notificacions; recuperació per un altre administrador o amb codis fora de línia |
| Àlies d'administrador (futur) | Opció: **Cloudflare Email Routing** sobre cris1954.cat (per exemple, `tresoreria@cris1954.cat` reenviat a l'adreça personal), perquè les notificacions no depenguin de correus personals. Requereix el DNS a Cloudflare [A validar] |

---

## 3. Cost mensual estimat

**Escenari aprovat: producció mínima** ([016](decisions/016-pressupost-produccio-minima.md)). La junta coneix el cost. Substitueix la previsió anterior de 100-120 €/any (context v3 §9; document incremental §4.2).

### Cost fix (sense IVA, preus consultats el 27/10/2026)

| Partida | Ara (desenvolupament) | **Producció mínima (aprovada)** | Producció recomanada (si cal créixer) |
|---|---|---|---|
| VPS producció | — | CX23: 5,99 € | CX33: 8,99 € |
| Còpies de Hetzner (≈20 %) | — | 1,20 € | 1,80 € |
| Storage Box BX11 | — | 3,20 € | 3,20 € |
| Scaleway (fitxers + còpies) | < 1 € | < 1 € | < 1 € |
| Correu (Brevo) | 0 € (gratuït) | 0 € (gratuït, en tandes) | ≈8,50 € (Starter, 9 $) [A validar] |
| VPS de proves (des de la integració de Stripe) | CX23 temporal: ≤5,99 € | creat i destruït quan calgui: ≈2 € [A validar] | CX23 permanent: 5,99 € |
| Cloudflare, UptimeRobot, seguiment d'errors, Coolify | 0 € | 0 € | 0 € |
| **Total aproximat** | **≈6-7 €/mes** | **≈13 €/mes (≈160 €/any)** | **≈29,50 €/mes (≈355 €/any)** |
| Total amb IVA del 21 %, si el club no el recupera [A validar amb la gestoria] | ≈8 €/mes | ≈16 €/mes | ≈36 €/mes |

- Domini: cris1954.cat ja està pagat pel club, i per tant no hi ha cost addicional ([019](decisions/019-domini-i-correu.md)).
- **Respecte a la previsió anterior:** els documents d'origen preveien 100-120 €/any. La producció mínima costa ≈160 €/any sense IVA (≈195 €/any amb IVA del 21 %), perquè hi suma la segona destinació de còpies i el VPS de proves.

### Comparació amb Cluber

| | Plataforma (producció mínima) | Cluber |
|---|---|---|
| Cost fix | ≈160 €/any sense IVA (consultat el 27/10/2026) | Des de 599 €/any, pla fins a 200 esportistes (preu publicat segons el document incremental §4.2). Si el club paga aquesta quota a més del percentatge: [A validar, P-27] |
| Cost variable | Comissions de Stripe (vegeu la taula següent): ≈53-110 €/any per a les quotes, més ≈1,9 % del que es cobri per targeta o Bizum | **Percentatge descomptat de cada ingrés** que Cluber cobra pel seu compte abans d'ingressar-lo al club (tresoreria, 27/10/2026). Percentatge [A validar, P-27] |
| Exemple per a les quotes (≈10.500 €/any: 150 quotes de 70 €) | ≈53-110 €/any | Si el percentatge fos de l'1 %, uns 105 €; del 3 %, uns 315 €; del 5 %, uns 525 €/any. Il·lustratiu: depèn del percentatge real |
| Total orientatiu, quotes incloses | ≈215-270 €/any sense IVA | Percentatge × ingressos cobrats per Cluber, més la quota fixa si n'hi ha (P-27) |

Cluber es deixa en entrar en producció ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md)). Fins llavors els dos costos conviuen.

- **CX23 o CX33:** Coolify, Django, PostgreSQL i el treballador de tasques poden funcionar amb 4 GB, però amb poc marge. Proposta: començar amb CX23 i ampliar si cal (a Hetzner es pot ampliar sense reinstal·lar) [A validar amb una prova de càrrega a proves].

### Cost variable: comissions de Stripe
Tarifes de la pàgina oficial de Stripe Espanya (consultada el 27/10/2026):

| Mètode | Comissió | Exemple |
|---|---|---|
| Targeta EEE estàndard | 1,5 % + 0,25 € | Inscripció de 60 € → 1,15 € |
| Apple Pay / Google Pay | La pàgina no en dona un preu propi; s'espera el de la targeta [A validar] | — |
| Bizum | 1,5 % + 0,25 € | Inscripció de 60 € → 1,15 € |
| Domiciliació SEPA | 0,35 € per cobrament | Quota de 90 € → 0,35 € |
| SEPA fallit | 3,50 € [A validar a la font oficial] | Rebut sense fons; cada reintent fallit pot tornar a cobrar-la |
| SEPA en disputa (retornat pel soci) | 15,00 € [A validar a la font oficial] | Retorn d'un rebut |
| Transferència (fora de Stripe) | 0 € de Stripe; comissions del banc [A validar] | — |
| Efectiu (fora de Stripe) | 0 € | — |

**Estimació anual de les quotes** (hipòtesi [A validar]: 150 quotes amb una mitjana de 70 €; la domiciliació és el mètode per defecte):
- Totes per SEPA: 150 × 0,35 € ≈ **53 €/any**.
- 60 % per SEPA i 40 % per targeta o Bizum: 90 × 0,35 € + 60 × 1,30 € ≈ **110 €/any**.
- No inclou rebuts fallits ni retornats (vegeu la taula).

**Inscripcions i llicències:** ≈1,9 % de l'import cobrat per targeta o Bizum (per exemple, 100 inscripcions de 60 € ≈ 115 €/any). El volum real és [A validar].

Les devolucions no retornen la comissió: la despesa es manté.

---

## 4. Fluxos de cada mètode de pagament

### 4.1 Model comú (estructura bàsica a la 00; la 04, tresoreria, hi construeix al damunt: [027](decisions/027-estructura-basica-de-carrec-i-pagament.md))
- **Càrrec** (quota, inscripció o llicència): import en cèntims, moneda EUR, departament, activitat (si n'hi ha) i estat `pendent → pagat → retornat`, o `anul·lat` (amb motiu).
- **Pagament**: lligat a un càrrec, amb el mètode (`sepa`, `targeta`, `bizum`, `transferencia`, `manual`), l'import, l'estat del proveïdor i els identificadors externs (o la referència de transferència).
- **Moviment de tresoreria**: immutable. Cada cobrament genera un ingrés; cada comissió, una despesa del mateix departament o activitat ([013](decisions/013-imputacio-comissions.md)); cada devolució o retorn, un moviment nou de signe contrari. No s'esborra res.
- **Compte de trànsit «Stripe»** (proposta per a la spec 04): els cobraments de Stripe entren en aquest compte i les liquidacions passen de Stripe al banc. Així el saldo de Stripe quadra i el banc es concilia per liquidació.
- **Esdeveniment rebut** (mòdul 05): identificador de l'esdeveniment de Stripe únic a la base de dades, tipus, data de recepció, data de processament i resultat.
- Una activitat no es pot tancar econòmicament si té càrrecs pendents o pagaments en curs.

### 4.2 Regles de processament dels webhooks (mòdul 05)
1. Es verifica la signatura amb el cos original de la petició i el secret del webhook; si no és vàlida, es respon 400 i no es fa res.
2. Es desa l'esdeveniment amb el seu identificador únic. Si ja existia, es respon 200 i no es torna a processar (idempotència).
3. Es respon 200 de seguida; el processament el fa la cua de tasques.
4. La tasca comprova que l'import, la moneda i l'identificador del càrrec (a les metadades) coincideixen amb el càrrec. Si no coincideixen, el pagament queda «a revisar» i s'avisa el tresorer.
5. Només s'apliquen transicions d'estat vàlides des de l'estat actual (per exemple, un `pagat` repetit no crea un segon ingrés).
6. Cada canvi queda al registre d'activitat.
7. Una tasca diària consulta a Stripe els esdeveniments dels darrers dies i processa els que no hagin arribat (xarxa de seguretat).
8. Les crides cap a Stripe (crear pagaments i devolucions) porten una clau d'idempotència basada en l'identificador intern.
9. L'aplicació rebutja les claus de producció de Stripe si `STRIPE_LIVE_MODE_ALLOWED` no és cert.

### 4.3 Domiciliació SEPA (només pagaments recurrents: quotes; mètode per defecte)
Requisits per a la spec del mòdul 05 ([017](decisions/017-pagaments-metodes-i-domiciliacions.md)): avís previ, reintent controlat, alternativa de pagament si falla i estat «retornat» amb conseqüències definides.

| Pas | Què passa | Esdeveniments de Stripe (orientatius) |
|---|---|---|
| **Alta de mandat** | El soci accepta el mandat al formulari allotjat de Stripe (IBAN i acceptació). Es guarden només els identificadors del client, del mètode de pagament i del mandat, mai l'IBAN complet. | `checkout.session.completed` (mode configuració), `setup_intent.succeeded`; `mandate.updated` si es revoca |
| **Avís previ** | Abans de cada cobrament s'avisa el soci amb la **data**, l'**import**, la **referència del mandat** i l'**ID de creditor** [A validar: si ho envia Stripe o la plataforma, amb quanta antelació i quin ID de creditor hi figura, P-24] | — |
| **Cobrament** | A la data fixada, una tasca crea el cobrament de cada quota amb el mandat. El càrrec queda «pendent» fins a la confirmació, que triga uns dies hàbils [A validar] | `payment_intent.processing` → `payment_intent.succeeded` (→ `pagat`, ingrés i comissió de 0,35 €) o `payment_intent.payment_failed` |
| **Fallada i reintent controlat** | Si falla, el càrrec continua `pendent`, es registra la comissió de fallada [A validar l'import a la font oficial] i s'avisa el soci i el tresorer. Es reintenta fins a un màxim d'intents i amb uns dies entre intents [A validar tots dos valors]; mai de manera indefinida | `payment_intent.payment_failed` |
| **Alternativa de pagament** | Després de la fallada (o en esgotar els reintents), el soci rep un enllaç per pagar la quota amb targeta, Bizum o transferència. Pot canviar de mètode per a les quotes següents | Com a 4.4-4.6 |
| **Retornat** | El soci pot retornar el rebut fins a 8 setmanes sense motiu (13 mesos si no l'havia autoritzat). El càrrec passa a `retornat`, es crea un moviment negatiu i la comissió de retorn [A validar l'import a la font oficial]; s'avisa el tresorer. Les conseqüències (impagat, carnet, qui assumeix la comissió) s'han de definir a la spec 05 [A validar] | `charge.dispute.created`, `charge.dispute.closed` |
| **Devolució** (la inicia el club) | El tresorer la demana des de la plataforma amb motiu; és un moviment nou | `charge.refunded`, `refund.updated` |
| **Conciliació** | La liquidació de Stripe arriba al banc agrupada. La plataforma casa la línia del CSV amb la liquidació i aquesta amb els cobraments que conté | `payout.paid`, `payout.failed` |

### 4.4 Targeta (amb Apple Pay i Google Pay)
| Pas | Què passa | Esdeveniments |
|---|---|---|
| **Alta** | No n'hi ha: cada pagament és puntual. No es guarda cap dada de targeta | — |
| **Cobrament** | La plataforma crea una sessió de pagament per al càrrec; el participant paga al formulari de Stripe. La pàgina de retorn només diu «estem confirmant el pagament»: l'estat canvia amb el webhook | `checkout.session.completed` amb `payment_status = paid` → `pagat`, ingrés i comissió |
| **Retornat** (contracàrrec) | El titular disputa el pagament amb el seu banc. Moviment negatiu i avís al tresorer | `charge.dispute.created`, `charge.dispute.closed` |
| **Devolució** | El tresorer la demana amb motiu. Total: el càrrec passa a `anul·lat`; parcial: [A validar] | `charge.refunded`, `refund.updated` |
| **Conciliació** | Com a SEPA: per liquidació de Stripe | `payout.paid` |

### 4.5 Bizum
Cal confirmar l'activació al compte de Stripe del club [A validar]. El flux és el de la targeta: sessió de pagament → el participant confirma a l'app del seu banc → webhook. Si Stripe el tracta com a mètode asíncron, la confirmació arriba amb `checkout.session.async_payment_succeeded` o `async_payment_failed` [A validar]. Devolució i conciliació, com a la targeta. Des del 2026 els bancs informen mensualment l'Agència Tributària dels cobraments per Bizum que reben les entitats (Ordre HAC/747/2025, segons Stripe): cal comentar-ho amb la gestoria [A validar].

### 4.6 Transferència amb referència única (fora de Stripe)
| Pas | Què passa |
|---|---|
| **Alta** | En triar transferència, la plataforma genera una referència única per càrrec (per exemple, `CRIS-` més un codi amb dígit de control) i mostra l'IBAN del club, l'import i la referència |
| **Cobrament** | El càrrec queda `pendent`. No hi ha webhook: la prova és l'extracte bancari |
| **Conciliació** | En importar el CSV, la plataforma proposa coincidències per referència i import; el tresorer les confirma. Només llavors el càrrec passa a `pagat` i es crea l'ingrés. Import diferent o referència absent → «a revisar» |
| **Retornat** | No aplica (una transferència no es retorna sola). Si el banc la rebutja, el càrrec continua `pendent` |
| **Devolució** | Transferència sortint feta des del banc; el tresorer la registra a la plataforma amb motiu i justificant, com a moviment nou |
| **Caducitat** | Termini per pagar i què passa si no es paga: [A validar] |

### 4.7 Registre manual (efectiu o presencial, fora de Stripe)
| Pas | Què passa |
|---|---|
| **Cobrament** | Un rol autoritzat (proposta: tresorer o administrador, P-12) registra el pagament amb import, data, compte («Caixa» o banc), motiu obligatori i, si n'hi ha, justificant adjunt. El càrrec passa a `pagat` i es genera el rebut |
| **Registre d'activitat** | Qui, quan, què i valor anterior; no es pot editar, només anul·lar amb motiu |
| **Devolució** | Moviment nou amb motiu |
| **Conciliació** | Arqueig de caixa periòdic i, si l'efectiu s'ingressa al banc, casament amb l'extracte |

### 4.8 Quin mètode per a cada cobrament
| Cobrament | SEPA | Targeta / Apple / Google Pay | Bizum | Transferència | Manual |
|---|---|---|---|---|---|
| Quota anual | Sí (per defecte) | Sí | Sí | Sí | Sí, amb motiu [A validar, P-12] |
| Inscripció | No | Sí | Sí | Sí | Sí, amb motiu [A validar, P-12] |
| Llicència | No | Sí | Sí | Sí | Sí, amb motiu [A validar, P-12] |

Font: [017](decisions/017-pagaments-metodes-i-domiciliacions.md). La domiciliació només s'aplica a pagaments recurrents.

### 4.9 Migració dels mandats de domiciliació actuals
Avui Cluber gestiona els rebuts domiciliats. Stripe té un procediment oficial de migració de dades que permet importar mandats SEPA d'altres proveïdors i mantenir-ne les referències (condicions concretes [A validar amb Stripe]).

**Escenari base: B** ([022](decisions/022-mandats-sepa-escenari-base-b.md)). Segons tresoreria (27/10/2026), Cluber cobra els rebuts pel seu compte i ingressa al club l'import menys un percentatge: el creditor seria Cluber [A validar amb un rebut o la documentació de Cluber]. L'escenari A només s'aplica si Stripe confirma per escrit que accepta migrar mandats en aquest cas. Cluber exporta socis, IBAN i referències (format [A validar]). En l'escenari B no cal importar IBAN a la plataforma.

**Condició de calendari:** els mandats signats en mode de proves de Stripe no serveixen. La campanya B es fa al **05a**, al **nivell 1 de producció**: Stripe en mode real només per recollir mandats, sense cap cobrament real i amb autorització expressa de la junta ([024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), [025](decisions/025-dos-nivells-de-produccio.md)). La plataforma no guarda l'IBAN; Stripe en té la custòdia. Si es poden recollir mandats abans d'acabar el 05a és [A validar amb Stripe]. A més, la campanya ha d'acabar abans de la propera remesa de quotes (P-29).

| | **Escenari A: migració a Stripe** | **Escenari B: mandats nous** |
|---|---|---|
| Quan s'aplica | El club és el creditor (té ID de creditor SEPA propi) i Cluber exporta els mandats | Cluber és el creditor, o no exporta els mandats, o l'exportació és incompleta |
| Passos | 1. Exportar de Cluber els mandats (IBAN, referència, data de signatura). 2. Sol·licitar la migració a Stripe pel procediment oficial i enviar-li el fitxer per un canal segur, mai per correu ni pel repositori. 3. Stripe crea els clients i mètodes de pagament amb els mandats. 4. La plataforma importa la correspondència entre soci i identificadors de Stripe (importació de mandats a la spec 05). 5. Comprovació amb un cobrament de prova i avís als socis | 1. Campanya única: cada soci rep un enllaç per signar un mandat nou al formulari de Stripe. 2. Seguiment de qui l'ha signat i recordatoris. 3. Qui no el signi paga la quota amb targeta, Bizum o transferència |
| Avantatge | El soci no ha de fer res; es mantenen les referències | No depèn de Cluber |
| Inconvenient | Depèn del format d'exportació de Cluber i de l'acceptació de Stripe; manipula IBAN (dades sensibles) | Esforç dels socis; probablement alguns no el signaran a temps |
| Dades | L'IBAN complet només passa de Cluber a Stripe. La plataforma guarda només identificadors | La plataforma no veu mai l'IBAN |

En tots dos casos, els socis han de rebre un avís si canvien el creditor o la referència que veuen al banc (P-24).

**Preguntes obertes [A validar] per a tresoreria i informàtica (P-21, P-29):**
1. Confirmar amb un rebut o la documentació de Cluber que el creditor és Cluber (i el seu ID de creditor).
2. Format de l'exportació de Cluber (CSV, XML SEPA, un altre).
3. En quin moment de l'any es cobren les quotes anuals.
4. Si Stripe accepta migrar mandats amb un tercer com a creditor (escenari A).

**A preveure a la spec 05a:**
- Campanya de signatura de mandats nous (escenari base B): enviament d'enllaços, seguiment, recordatoris i alternativa de pagament per a qui no signi.
- Importació de mandats (només si s'aplica l'escenari A): previsualització, validació, correspondència per soci i opció de desfer, com les altres importacions.

**A preveure a la spec 05b:**
- Avís previ amb data, import, referència del mandat i ID de creditor.

---

## 5. Variables d'entorn (sense valors)

Cada entorn (local, proves, producció) té els seus valors, guardats a Coolify o en un fitxer `.env` local que mai es puja al repositori. Al repositori només hi haurà `.env.example` amb aquests noms buits.

### Aplicació (Django)
| Variable | Ús |
|---|---|
| `APP_ENV` | `local`, `proves` o `produccio` |
| `DJANGO_SECRET_KEY` | Clau de signatura de Django |
| `DJANGO_DEBUG` | Sempre fals fora de local |
| `DJANGO_ALLOWED_HOSTS` | Dominis acceptats per l'API |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígens de confiança per a formularis |
| `CORS_ALLOWED_ORIGINS` | Domini de la web de Cloudflare Pages |
| `DATABASE_URL` | Connexió a PostgreSQL |
| `PUBLIC_SITE_URL` | URL de la web pública (per als enllaços dels correus) |
| `API_BASE_URL` | URL pública de l'API |
| `ADMIN_URL_PATH` | Ruta discreta de l'administració |
| `TOTP_ISSUER_NAME` | Nom que surt a l'aplicació d'autenticació |
| `FIELD_ENCRYPTION_KEYS` | Claus Fernet per xifrar camps sensibles (secrets TOTP), separades per comes; la primera xifra i totes desxifren (rotació). Es guarden fora de línia com les de les còpies |
| `CARD_QR_KEYS`, `CARD_QR_ACTIVE_KEY` | Claus del QR del carnet (decisió 079): «identificador:clau» separades per comes, i l'identificador de la que es fa servir per emetre. Obligatòries a producció. Per rotar: s'afegeix la nova, es posa com a activa i es conserva l'antiga; si una s'ha filtrat, `manage.py reemet_carnets --clau <id>` i després es treu. Es guarden fora de línia com les de les còpies |
| `MANDATE_ENCRYPTION_KEYS` | Claus de l'IBAN del mandat (044, `apps/payments/crypto.py`): «versió:clau Fernet» separades per comes. Xifra la de versió més alta; cada IBAN es desxifra només amb la clau de la seva versió (`key_version`). Sense cap clau no es desa cap mandat: no hi ha clau per defecte. Obligatòria a producció. Rotació (`manage.py rota_clau_mandats`) i restauració: checklist C13. Còpia fora del servidor per les persones que fixi la junta |
| `DJANGO_NUM_PROXIES` | Proxies de confiança davant de Django (1 amb Coolify); decideix d'on es llegeix l'IP per al límit d'intents |

### Fitxers (Scaleway)
| Variable | Ús |
|---|---|
| `S3_ENDPOINT_URL` | Punt d'accés de Scaleway |
| `S3_REGION` | Regió (París) |
| `S3_ACCESS_KEY_ID` | Clau d'accés de l'aplicació (només al bucket de fitxers) |
| `S3_SECRET_ACCESS_KEY` | Secret de la clau |
| `S3_BUCKET_FITXERS` | Bucket privat de l'entorn |
| `S3_SIGNED_URL_TTL_SECONDS` | Durada de les URL signades |
| `UPLOAD_MAX_BYTES` | Mida màxima de pujada |

### Correu (Brevo)
| Variable | Ús |
|---|---|
| `BREVO_API_KEY` (o `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` si es fa per SMTP) | Enviament |
| `EMAIL_FROM_TRANSACCIONAL` | Remitent dels transaccionals |
| `EMAIL_FROM_BUTLLETI` | Remitent del butlletí |
| `EMAIL_REPLY_TO` | Adreça de resposta (cris@cris.es) |
| `EMAIL_DAILY_LIMIT` | Límit diari del pla, sumant totes les categories (per defecte 300, el del pla gratuït). El dia és el de l'hora local. Amb el límit ple, els correus queden ajornats i surten l'endemà per l'ordre de V-07 (T-M00-06) |
| `EMAIL_TRANSACTIONAL_RESERVE` | Enviaments reservats cada dia per als transaccionals (per defecte 100): el butlletí només pot gastar el límit menys la reserva |
| `EMAIL_ALERT_THRESHOLD_PCT` | Percentatge del límit que dispara l'únic avís del dia (per defecte 80) |
| `EMAIL_ALERT_TO` | Adreça de l'administrador, l'únic que rep l'avís (decisió 081, punt 21; Q-26 resolta). **A producció, per defecte `cris@cris.es`** (decisió 084; `config/settings/prod.py`); la variable d'entorn la pot canviar. En local i a les proves no té valor per defecte i l'avís només queda al registre d'activitat. Si quedés buida a producció, `check --deploy` ho marca (`core.W001`); una adreça mal escrita és un error (`core.E001`) |
| `BREVO_WEBHOOK_SECRET` | Verificació dels avisos de rebots i baixes |

### Pagaments (Stripe i transferència)
| Variable | Ús |
|---|---|
| `STRIPE_SECRET_KEY` | Clau restringida amb els permisos mínims |
| `STRIPE_WEBHOOK_SECRET` | Verificació de la signatura dels webhooks |
| `STRIPE_LIVE_MODE_ALLOWED` | Fals per defecte; cert només amb l'autorització de la junta per al nivell 1 o 2 ([025](decisions/025-dos-nivells-de-produccio.md)) |
| `STRIPE_LIVE_CHARGES_ALLOWED` | Fals fins al nivell 2 (producció completa). Mentre sigui fals, la plataforma no pot crear cap cobrament en mode real |
| `STRIPE_API_VERSION` | Versió de l'API fixada |
| `CLUB_IBAN_TRANSFERENCIES` | IBAN que es mostra per a les transferències |
| `TRANSFER_REFERENCE_PREFIX` | Prefix de les referències (per exemple, `CRIS`) |

### Observabilitat
| Variable | Ús |
|---|---|
| `ERROR_TRACKING_DSN` | DSN del GlitchTip del club (P-294). Buida (per defecte): el seguiment d'errors no s'activa i no surt res per la xarxa. Només la llegeix la configuració de producció (`config/settings/prod.py`) |
| `ERROR_TRACKING_ENVIRONMENT` | Nom de l'entorn als errors (per defecte `production`) |
| `LOG_LEVEL` | Nivell dels registres |

El DSN ha de ser `https` i el host, a la llista `ERROR_TRACKING_ALLOWED_HOSTS` de `apps/core/error_tracking.py`; si no, producció no arrenca. La llista és al codi i no a l'entorn, perquè qui posa el DSN no pugui posar també el host: hi ha només `errors.cris1954.cat`, el GlitchTip autoallotjat al mateix VPS que va triar el propietari ([P-294](decisions/pendents.md), 17/11/2026; nom del subdomini [A validar]). Un host nou entra al codi amb una PR revisada. Instal·lació i encesa: [`guies/servidor-glitchtip.md`](guies/servidor-glitchtip.md); no s'encén fins que el servidor existeixi i el propietari ho confirmi.

Què no s'envia mai al seguiment d'errors (`apps/core/error_tracking.py`; R11): el cos, les galetes, la cadena de consulta i l'URL de la petició (a la transacció, els trossos del camí que semblen un testimoni es tapen), les capçaleres fora de `User-Agent`, `Content-Type`, `Accept` i `Accept-Language`, l'usuari, les variables locals, els `extra`, els paràmetres dels registres i les consultes SQL de les traces. Als missatges d'error i de registre es tapen els IBAN, les targetes i altres números llargs, els correus, els DNI i NIE, els telèfons i les IP. Sense traça de rendiment (`traces_sample_rate=0`), sense perfils ni repetició de sessions. Els identificadors interns (per exemple, el número d'un compte) sí que hi poden sortir.

### Còpies (al servidor, fora de l'aplicació)
| Variable | Ús |
|---|---|
| `RESTIC_PASSWORD_FILE` | Fitxer amb la clau de xifratge (també guardada fora de línia) |
| `RESTIC_REPO_SCALEWAY` | Repositori de còpies al bucket de còpies |
| `RESTIC_REPO_STORAGEBOX` | Repositori de còpies al Storage Box |
| `BACKUP_S3_ACCESS_KEY_ID`, `BACKUP_S3_SECRET_ACCESS_KEY` | Claus només del bucket de còpies (diferents de les de l'aplicació) |
| `STORAGEBOX_SSH_KEY_PATH` | Clau SSH per al Storage Box |
| `BACKUP_ALERT_TO` | Qui rep l'avís si una còpia falla |

### Web pública (Cloudflare Pages, compilació)
| Variable | Ús |
|---|---|
| `PUBLIC_API_BASE_URL` | URL de l'API |
| `PUBLIC_APP_ENV` | Entorn |

Tot el que es posa a la compilació de la web és públic: mai s'hi posa cap secret.

---

## 6. Riscos i mitigacions

| # | Risc | Probabilitat / impacte | Mitigació | Responsable suggerit |
|---|---|---|---|---|
| R1 | Dependència d'una sola persona voluntària per mantenir el sistema | Alta / alt | Repositori i comptes amb dos administradors; README i runbook; calendari de manteniment | Presidència + responsable de manteniment |
| R2 | Pèrdua de dades (servidor, compte o error humà) | Baixa / molt alt | Còpies creuades xifrades a dos proveïdors; prova de restauració mensual fins a producció i trimestral després | Responsable de manteniment |
| R3 | Pèrdua de la clau de xifratge de les còpies | Baixa / molt alt | Clau guardada fora de línia en dos llocs; comprovació a cada prova de restauració | Responsable de manteniment + tresorer [A validar] |
| R4 | Arribar al límit de 300 correus diaris i que no surtin correus importants | Alta en dies de butlletí / mitjà | Reserva per als transaccionals, butlletí en tandes, avís al 80 %; pla Starter en producció | Responsable de comunicació |
| R5 | Webhook perdut, duplicat o falsificat | Mitjana / alt | Signatura, identificador únic, transicions vàlides, tasca diària de reconciliació, proves amb notificacions repetides i falses (checklist C9) | Equip de desenvolupament |
| R6 | Activar la producció de Stripe abans d'hora | Baixa / alt | Comprovació de `STRIPE_LIVE_MODE_ALLOWED`; claus restringides; autorització escrita de la junta | Administrador |
| R7 | Rebuts SEPA retornats o en disputa (15 € cadascun) | Mitjana / mitjà | Mandat i prenotificació clars; avís immediat al tresorer; política d'impagats [A validar] | Tresorer |
| R8 | Bizum no disponible al compte del club | Mitjana / baix | Targeta i transferència com a alternatives | Tresorer |
| R9 | Caiguda del VPS únic | Mitjana / alt | UptimeRobot; còpies de Hetzner per recuperar ràpid; temps màxim de recuperació acordat [A validar] | Responsable de manteniment |
| R10 | Compte d'administració compromès | Baixa / molt alt | Comptes d'administrador separats dels de soci, amb nom d'usuari i sense recuperació per correu; TOTP obligatori; limitació d'intents; registre d'activitat per compte; comptes d'emergència ([015](decisions/015-doble-factor-i-comptes-administrador.md)) | Administrador |
| R10b | Pèrdua d'accés de tots els administradors (sense recuperació per correu) | Baixa / alt | Com a mínim dos administradors actius (la plataforma rebutja qualsevol canvi que en deixi menys d'un operatiu i avisa per sota de dos; els permisos del rol administrador sobre usuaris, rols i permisos no es poden treure, decisió 059), dos comptes d'emergència i codis de recuperació fora de línia en dos llocs; procediment de restabliment escrit | Presidència + responsable de manteniment |
| R11 | Dades personals en registres o errors | Mitjana / mitjà | Filtres als registres; enviament a GlitchTip o Sentry sense dades personals; revisió d'exemples (E1) | Equip de desenvolupament |
| R12 | Cost per sobre del pressupost aprovat (producció mínima, [016](decisions/016-pressupost-produccio-minima.md)) | Mitjana / mitjà | Límits i alertes de facturació a cada proveïdor (D3); qualsevol pas a l'escenari recomanat es decideix i es registra | Tresorer |
| R13 | Dependència de Stripe | Baixa / mitjà | Model de pagaments propi i independent del proveïdor; transferència i efectiu com a alternatives; exportació periòdica | Tresorer + equip de desenvolupament |
| R14 | Una actualització de Coolify o del sistema trenca el desplegament | Mitjana / mitjà | Instantània abans d'actualitzar; versió fixada; primer a proves | Responsable de manteniment |
| R15 | Canviar els servidors de noms de cris1954.cat a Cloudflare trenca algun servei que ja hi funciona | Mitjana / alt | Inventari previ de tots els registres DNS abans del canvi; cris.es no es toca | Responsable d'informàtica |
| R17 | Migració de mandats SEPA incompleta o fuita d'IBAN | Mitjana / alt | Escenari A només amb exportació completa i canal segur cap a Stripe; si no, escenari B; la plataforma no guarda IBAN complets | Tresorer + responsable d'informàtica |
| R16 | Obligacions fiscals (IVA, Verifactu, informació de Bizum a l'Agència Tributària) | Mitjana / alt | Consulta a la gestoria abans d'activar els cobraments (P-02) | Tresorer |

---

## 7. Tasques manuals (per a l'equip i la junta)

No s'ha creat cap compte. Cada compte ha de ser **del club** (correu del club, dades de facturació del club), amb **dos administradors** i doble factor activat.

### Ara (abans del primer codi, porta 0)
- [ ] Decidir el responsable de manteniment a la junta i el segon administrador de tots els comptes.
- [ ] Crear l'organització del repositori (GitHub o GitLab) amb dos propietaris i doble factor.
- [ ] Triar un gestor de contrasenyes del club per guardar credencials i codis de recuperació [A validar quin].
Les tasques amb temps d'espera (marcades ⏳) han de començar ja: vegeu §9.3.

- [ ] **DNS:** anotar qui té l'accés concret al registrador i al DNS de cris1954.cat i de cris.es [A validar]; guardar les credencials en un gestor compartit amb dues persones; fer inventari dels registres de cris1954.cat; decidir si es redirigeix **cris.barcelona** (P-25, [023](decisions/023-gestio-del-dns.md)).
- [ ] ⏳ **Stripe:** obrir el compte de Stripe del club **en mode de proves** i iniciar la verificació de l'entitat (NIF, estatuts, representant legal, compte bancari).
- [ ] ⏳ **Bizum:** demanar a Stripe si es pot activar al compte del club i amb quines condicions.
- [ ] ⏳ **Stripe, mandats:** preguntar si accepta migrar mandats on el creditor és un tercer (Cluber), i només llavors s'aplica l'escenari A (§4.9). Preguntar també si es poden recollir mandats en mode real abans d'acabar el 05a (per exemple, amb un formulari allotjat de Stripe) [A validar amb Stripe].
- [ ] ⏳ **Cluber, exportació:** demanar una exportació de prova (socis i referències; sense IBAN si s'aplica l'escenari B), anonimitzada, per conèixer el format (P-21).
- [ ] **Cluber, creditor i cost:** confirmar amb un rebut o la documentació de Cluber qui és el creditor i quin percentatge descompta (P-21, P-27).
- [ ] **Tresoreria:** confirmar en quin moment de l'any es cobren les quotes anuals (P-29).
- [ ] ⏳ **Comunicació als socis:** preparar amb la junta l'avís del canvi de domiciliació (nou creditor, mandat nou a signar, calendari, alternatives de pagament). S'envia quan hi hagi data de campanya.
- [ ] Portar a la junta els punts oberts de [pendents.md](decisions/pendents.md) (sobretot P-24, P-27 a P-29 i P-33) i aplicar al .docx els textos de P-22.

### Abans de l'entorn de proves i la primera demo (porta 1)
- [ ] Crear el compte de **Hetzner** (Cloud i Storage Box), activar el doble factor i fixar un límit o alerta de despesa.
- [ ] Crear el compte de **Scaleway**, regió París, amb doble factor; crear els buckets privats per entorn i el bucket de còpies amb claus separades.
- [ ] Crear el compte de **Cloudflare** i afegir-hi **cris1954.cat**; canviar els servidors de noms al registrador **només** després de copiar tots els registres actuals.
- [ ] Crear el compte de **Brevo**, verificar **cris.es** com a domini remitent i publicar-hi SPF, DKIM i DMARC (checklist G1; decisió 085: els correus surten de cris@cris.es). Cal l'accés al DNS de cris.es, que ara gestiona una empresa per compte de la junta.
- [ ] Crear el monitor a **UptimeRobot** amb avís al correu del responsable.
- [ ] Confirmar per escrit la regió de dades de **GlitchTip** o **Sentry**; si és Sentry, triar la regió UE en crear l'organització (no es pot canviar després).

### Abans d'integrar els pagaments
- [ ] Completar la verificació de l'entitat a **Stripe** (iniciada a la fase «Ara») i continuar **només en mode de proves**.
- [ ] Demanar a Stripe l'activació de **Bizum** i de la **domiciliació SEPA** per al compte del club, i confirmar a la font oficial les comissions de cobrament fallit i de rebut retornat.
- [ ] Confirmar amb la gestoria IVA, Verifactu i la informació de cobraments per Bizum a l'Agència Tributària.
- [ ] Confirmar l'IBAN del club per a les transferències i el format d'exportació CSV de l'extracte del banc (enviar-ne un d'anonimitzat).
- [ ] Crear el VPS de proves separat.

### Abans de dades reals (porta 2)
- [ ] Acceptar o signar l'**acord d'encarregat del tractament (DPA)** de cada proveïdor que tracta dades personals: Hetzner, Scaleway, Brevo, Stripe, Cloudflare i GlitchTip o Sentry. Guardar-ne una còpia.
- [ ] Actualitzar el **registre d'activitats de tractament** del club amb aquests proveïdors i les transferències internacionals (Cloudflare, Stripe, Sentry si escau).
- [ ] Redactar amb la junta la política de privacitat i el text del mandat SEPA i dels consentiments.
- [ ] Guardar fora de línia la clau de xifratge de les còpies i els codis de recuperació del doble factor (dos llocs).
- [ ] Fer i documentar la primera prova de restauració.
- [ ] Comprovar que els registres d'accés del proxy de Coolify no guarden les rutes amb testimoni dels enllaços del correu (`/compte/verificar/…`, `/compte/contrasenya/…`): la primera petició porta el testimoni a la ruta, i la plataforma només el treu de les peticions següents (T-M01-05) [A verificar: informàtica].
- [ ] El mateix per a l'enllaç de convidat (`/convidat/<testimoni>/`, T-M00-02; RN-32 i CA-02.8 de la spec 00): ni els registres d'accés del proxy ni el seguiment d'errors, quan es configuri, n'han de guardar la ruta. La plataforma no l'escriu als seus registres i redirigeix a `/convidat/`, sense testimoni [A verificar: informàtica].

### Abans del nivell 1 de producció (mandats, [025](decisions/025-dos-nivells-de-produccio.md))
- [ ] Comprovar que el 05a està acabat i provat, que les portes 0-2 estan superades (HTTPS, secrets, còpies i restauració, RGPD i consentiments, registre d'activitat) i que els punts «N1» de la porta 3 també (A6, E3, E4, B5, B8, G3).
- [ ] Preguntar al club si hi ha socis menors d'edat; si n'hi ha, el mandat l'ha de signar el titular del compte bancari (P-33).
- [ ] Comprovar que `STRIPE_LIVE_CHARGES_ALLOWED` és fals i que la prova de «cap cobrament real» passa.
- [ ] Autorització expressa de la junta per al nivell 1.
- [ ] Enviar la comunicació als socis i obrir la campanya de mandats nous.

### Abans del nivell 2 de producció (producció completa)
- [ ] Comprovar que el 05b està acabat i provat (criteri per deixar Cluber, [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md) refinada per [025](decisions/025-dos-nivells-de-produccio.md)) i que les portes 0-3 estan superades.
- [ ] Autorització expressa de la junta per a la producció completa (activar `STRIPE_LIVE_CHARGES_ALLOWED`).
- [ ] Fer la migració única de Cluber (funcionalitats §9.13) i la campanya de mandats nous (escenari base B, §4.9) abans de la propera remesa de quotes. Decidir si es fa la campanya de quotes en paral·lel, que és opcional ([020](decisions/020-baixa-de-cluber-sense-restriccio-de-data.md)), i donar de baixa Cluber (no hi ha contracte ni data límit).
- [ ] Decidir si es contracta Brevo Starter (preu a confirmar en aquell moment).

---

## 8. Preguntes obertes [A validar]

Resolts el 27/10/2026:
- abast dels cobraments (P-01 → [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md));
- pressupost (P-06 → [016](decisions/016-pressupost-produccio-minima.md));
- mètodes de les quotes (P-09 → [017](decisions/017-pagaments-metodes-i-domiciliacions.md));
- comptes i doble factor (P-16 a P-18 → [018](decisions/018-perfil-comptes-i-rols.md));
- domini (P-15 → [019](decisions/019-domini-i-correu.md));
- baixa de Cluber (P-20 → [020](decisions/020-baixa-de-cluber-sense-restriccio-de-data.md));
- persones no sòcies (P-23 → [021](decisions/021-persones-no-socies-com-a-convidades.md)).

1. **DNS:** qui té l'accés concret? Es redirigeix cris.barcelona? Quin nom té l'adreça remitent i el subdomini de l'API? (P-25)
2. **Cluber:** confirmar el creditor i el percentatge que descompta; format de l'exportació; quan es cobren les quotes anuals (P-21, P-27, P-29).
3. **Creditor amb Stripe:** quin ID de creditor veuran els socis? (P-24)
4. **Bizum:** està disponible al compte de Stripe del club? És un mètode síncron o asíncron a Stripe?
5. **SEPA:** qui envia l'avís previ (Stripe o la plataforma) i amb quanta antelació? Quant triga a confirmar-se un cobrament? Quants reintents i amb quants dies entre ells? Comissions de fallada i de retorn a la font oficial.
6. **Rebut retornat:** què passa amb el soci (impagat, carnet desactivat, qui assumeix la comissió)? Termini d'impagat.
7. **Devolucions parcials:** es permeten? Qui les autoritza?
8. **Registre manual:** quins rols el poden fer i quin justificant cal? (P-12)
9. **Transferència:** termini per pagar i què passa si no arriba.
10. **Comissions de llicències:** a quin departament s'imputen? ([013](decisions/013-imputacio-comissions.md))
11. **Talla del VPS:** CX23 o CX33, segons una prova de càrrega a proves.
12. **Seguiment d'errors:** GlitchTip o Sentry, un cop confirmada la regió de la UE.
13. **IVA:** el club recupera l'IVA de les factures dels proveïdors? (afecta el cost real)
14. **Migració de mandats a Stripe:** condicions i terminis del procediment oficial de migració de dades (§4.9).
15. **Temps màxim de recuperació** acceptable si cau el servidor (hores o dies).
16. **Custòdia de claus:** qui guarda la clau de les còpies i els codis de recuperació.
17. **Preus:** confirmar tots els preus d'aquest document a les pàgines oficials en el moment de contractar.

---

## 9. Abast mínim per substituir Cluber i ordre d'especificació

> **Estat: aprovat el 27/10/2026, amb canvis** ([024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), resol P-26). Mòdul 05 dividit en 05a i 05b; registre mínim de llicència al 01. CLAUDE.md i la metodologia ja recullen aquest ordre.
>
> **Objectiu orientatiu de canvi de Cluber:** finals de gener o principis de febrer de 2027. **No és una data compromesa.** Mana la [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md): Cluber només es deixa quan el mòdul 05 estigui acabat i provat. Sense contracte, el canvi es pot posposar sense cost ([020](decisions/020-baixa-de-cluber-sense-restriccio-de-data.md)).

### 9.1 Abast mínim per substituir Cluber
Criteri: només el que avui fa Cluber (socis, quotes, cobraments domiciliats, carnet i àrea de socis), més el que cal per cobrar i quadrar els diners a la plataforma.

| Dins de l'abast mínim | Què inclou | Què es deixa fora d'aquest abast |
|---|---|---|
| **00 Base comuna** | Perfil únic, comptes de soci i d'administrador, convidats amb enllaç segur ([021](decisions/021-persones-no-socies-com-a-convidades.md)), rols i permisos, doble factor, registre d'activitat, RGPD (consentiments, exportar i esborrar), importacions (Cluber i extracte bancari), correu (annex), fitxers (annex), còpies i entorns | Duplicar activitats (va amb el 02) |
| **01 Socis i carnet** | Alta (presencial per la secretaria; el formulari web es pot afegir després [A validar]), baixa, canvi de tipus, generació de quotes anuals, impagats, carnet digital amb QR i verificació, fitxa i historial, àrea de socis (perfil, carnet, quotes, rebuts). **Registre mínim de llicència:** tipus, data d'alta i data de caducitat, perquè no es perdin dades en deixar Cluber | Avatars, antiguitat corregible (es pot fer després), informes avançats; el procés complet de llicències va al 06 |
| **04 Tresoreria, part mínima** | Càrrec genèric i estats, pagaments, moviments immutables, departaments i centres de cost, comptes (banc, caixa, trànsit Stripe), ingressos automàtics, comissions, devolucions com a moviments nous, conciliació amb l'extracte en CSV | Marge per activitat, despeses amb factura obligatòria, ajuts i justificació, facturació Verifactu (P-02), tancament de període |
| **05a Pagaments: alta del mètode i mandats** | Alta del mètode de pagament del soci; signatura de mandats SEPA en mode real (campanya de mandats nous, escenari B); importació de mandats si s'aplica l'escenari A; webhooks de mandats (signat, revocat) | Cobraments |
| **05b Pagaments: cobraments** | Cobraments amb domiciliació, targeta, Bizum, transferència amb referència i registre manual; remeses de quotes; avís previ; reintent controlat; alternativa de pagament; retornats; devolucions; conciliació; webhooks i idempotència | — |
| **Importació única de Cluber** | Socis, dates d'alta, quotes, rebuts, referències i llicències (tipus, data d'alta i de caducitat); sense IBAN en l'escenari B. Previsualització, validació i opció de desfer | — |

**Queda per a després:** 02 Activitats (cursos i sortides), 03 Material, 09 Marge, despeses, ajuts i facturació (abans «resta de la 04»), 06 Llicències (preus, renovacions, recordatoris, no socis, exportació a la federació), 07 Web pública i butlletí, 08 Dashboard.

**Llicències:** segons el document incremental §1.2, avui es gestionen amb «Cluber i federació». El registre mínim del 01 evita perdre dades; què fa Cluber amb les llicències i com es tramiten entre la baixa de Cluber i el 06 continua pendent (P-28).

### 9.2 Ordre d'especificació (aprovat)
| Ordre | Especificació | Formalitat | Per què | Depèn de |
|---|---|---|---|---|
| 1 | **00 Base comuna**: perfil únic, comptes de soci i d'administrador amb diversos rols, convidats amb enllaç segur i compte opcional, permisos per rol i objecte, TOTP obligatori a l'entrada d'administració, restabliment sense correu per als administradors, registre d'activitat per compte, RGPD, importacions, entorns, cua de tasques, còpies | **Completa** | Tot la fa servir ([015](decisions/015-doble-factor-i-comptes-administrador.md), [018](decisions/018-perfil-comptes-i-rols.md), [021](decisions/021-persones-no-socies-com-a-convidades.md)) | P-04 |
| 1a | 00 · annex **Fitxers** | **Lleugera** | Carnet en PDF, rebuts i justificants | 00 |
| 1b | 00 · annex **Correu**: plantilles, registre, comptador i reserva diària, tandes, avís al 80 %, remitent a cris1954.cat | **Lleugera** | Avisos previs, recordatoris i campanya de mandats | 00 |
| 2 | **01 Socis i carnet** (abast mínim, amb registre mínim de llicència) | **Completa** (dades personals i RGPD) | Defineix els socis i les quotes que la 05b ha de cobrar | 00; preguntes de la junta de funcionalitats §3 (canvi a ple dret, impagats, número de soci); P-28 |
| 3 | **04 Tresoreria**, part mínima | **Completa** (finances) | Model de càrrec, pagament i ingrés; el 05 hi escriu a través de serveis | 00, 01; P-02 només per a la part de facturació (fora del mínim) |
| 4 | **05a Alta del mètode de pagament i mandats** | **Completa** (pagaments). Acabat i provat, habilita el **nivell 1 de producció** (només mandats, cap cobrament real) | Permet començar la campanya de mandats nous abans d'acabar els cobraments | 01, 04; P-21, P-31; [A validar amb Stripe] recollida de mandats abans d'acabar el 05a |
| 5 | **05b Cobraments, remeses, retornats, devolucions i conciliació** | **Completa** (pagaments). Acabat i provat, habilita el **nivell 2, producció completa**: criteri per deixar Cluber ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md), [025](decisions/025-dos-nivells-de-produccio.md)) | Fa servir els mandats del 05a | 05a; P-12, P-24, P-29 |
| 6 | Fase 2: 02, 03, 09, 06, 07, 08 (numeració de `planning.md#estat`) | Segons CLAUDE.md | Després de deixar Cluber | — |

Cada especificació completa segueix la plantilla de [metodologia-sdd.md](metodologia-sdd.md) §5 i acaba amb les preguntes obertes, el responsable i la data.

### 9.3 Riscos del calendari i tasques que han de començar ja
Del 27/10/2026 a finals de gener de 2027 hi ha unes 13 setmanes, amb les vacances de Nadal pel mig. Calen cinc especificacions completes (00, 01, 04 mínim, 05a i 05b). La metodologia limita a una spec revisada per setmana i persona. A més, cal construir-les, provar-les i fer la migració.

| Risc | Per què | Efecte | Mitigació |
|---|---|---|---|
| La campanya de mandats depèn de tenir Stripe en mode real | Els mandats de proves no són vàlids; la campanya B es fa al nivell 1 de producció (05a), que exigeix les portes 0-2 i l'autorització de la junta | Si la remesa de quotes cau abans, no hi ha temps de recollir mandats | Nivell 1 de producció per avançar la campanya ([025](decisions/025-dos-nivells-de-produccio.md)); consultar Stripe sobre la recollida anticipada; saber ja quan es cobren les quotes (P-29). Si la remesa és abans del canvi, es cobra amb Cluber i la campanya es fa per a la remesa següent |
| Llicències | Cluber en porta una part (P-28) | Pèrdua de dades | Registre mínim de llicència al 01 i importació des de Cluber |
| Verificació de l'entitat a Stripe i activació de Bizum | Depèn de documents del club (estatuts, NIF, representant) i de la resposta de Stripe | Retarda les proves reals de pagament | Començar-les ja (en mode de proves no hi ha cap risc) |
| Format d'exportació de Cluber desconegut | Sense una mostra no es pot especificar la importació | Retarda la 00 (importacions) i la 01 | Demanar ja una exportació de prova anonimitzada |
| Respostes de la junta | Les preguntes de la 01 (impagats, canvi a ple dret) i la 05 (retornats, reintents) bloquegen parts de les specs | Specs aturades | Llista de preguntes per sessió de junta; data límit de resposta |
| Disponibilitat dels voluntaris i dels estudiants | Nadal i tancament del semestre | Menys capacitat a desembre i gener | Objectiu no compromès; es pot posposar sense cost |
| Comunicació als socis | Els socis han de saber que canvia el creditor i que han de signar un mandat nou | Rebuts retornats o socis sense mandat | Preparar ja l'avís amb la junta; enviar-lo quan hi hagi data |
| Procés de llicències sense mòdul 06 | Si Cluber en tramita una part (P-28) i el 06 queda per a després | Tramitació manual mentre no hi hagi 06 | Aclarir-ho ara; registre mínim al 01 i tramitació manual provisional |

**Tasques amb temps d'espera que han de començar ja** (també a §7, «Ara»):
1. Compte de Stripe en mode de proves i verificació de l'entitat.
2. Petició d'activació de Bizum, i consulta sobre la migració de mandats i la recollida de mandats abans d'acabar el 05a.
3. Exportació de prova de les dades de Cluber (format).
4. Comunicació als socis sobre el canvi de domiciliació (redacció amb la junta).
5. Confirmar amb tresoreria quan es cobren les quotes i quin percentatge descompta Cluber.

---

## Fonts consultades el 27/10/2026
- Hetzner Cloud, plans Cost-Optimized: https://www.hetzner.com/cloud/cost-optimized/
- Hetzner Storage Box: https://www.hetzner.com/storage/storage-box/
- Stripe Espanya, mètodes de pagament locals: https://stripe.com/es/pricing/local-payment-methods
- Stripe, Bizum per a empreses a Espanya: https://stripe.com/resources/more/bizum-for-buisinesses-spain
- Scaleway, preus d'emmagatzematge: https://www.scaleway.com/en/pricing/storage
- Brevo, preus (fonts secundàries; cal confirmar a brevo.com): https://www.omnisend.com/blog/brevo-pricing/
- Sentry, ubicació de les dades: https://docs.sentry.io/organization/data-storage-location/
- GlitchTip, preus: https://glitchtip.com/pricing
