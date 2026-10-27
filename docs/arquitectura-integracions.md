# Arquitectura d'integracions — Plataforma C.R.I.S.

- **Versió:** 2 · 27/10/2026. Incorpora les decisions [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md) a [017](decisions/017-pagaments-metodes-i-domiciliacions.md).
- **Estat:** acceptada per l'equip; els punts marcats [A validar] i els de [decisions/pendents.md](decisions/pendents.md) continuen oberts.
- **Entrada en producció:** mòdul 05 (pagaments) acabat i provat; llavors es migra Cluber una sola vegada i es deixa ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md)).
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
| Àrea de socis i administració | PWA → API Django (sessió) → PostgreSQL | Permís per rol i per objecte a cada endpoint; TOTP per a rols amb diners o dades de socis |
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
| **Cloudflare Pages + DNS** | Web pública i PWA estàtiques; DNS del domini | Xarxa global; empresa dels EUA (transferència documentada, marc UE-EUA) [A validar] | 0 € | — | Pages no ha d'allotjar dades personals | HTML estàtic: qualsevol allotjament estàtic; DNS exportable en fitxer de zona |
| **Brevo** | Correu transaccional i butlletí | França / UE | Gratuït: 0 € · Starter: des d'uns 9 $/mes (5.000 correus/mes, sense límit diari) [A validar a brevo.com] | Cap | Gratuït: 300 enviaments/dia sumant-ho tot; marca de Brevo als correus | Plantilles i llista de subscriptors viuen a la plataforma; canviar de proveïdor = canviar credencials SMTP/API |
| **Stripe** | Targeta, Apple Pay, Google Pay, Bizum, domiciliació SEPA | Entitat contractant a la UE (Irlanda); possibles transferències als EUA (documentades) [A validar al DPA] | 0 € fix; comissions per cobrament (§3) | Cap | Bizum s'ha d'activar al compte del club [A validar]; SEPA: devolucions sense motiu fins a 8 setmanes | Exportació de clients i pagaments; migració de mandats SEPA a demanar a Stripe [A validar] |
| **Transferència bancària** | Cobrament sense comissió de passarel·la | Banc del club | 0 € (comissions del banc [A validar]) | Compte existent | Conciliació amb CSV, no instantània | Independent de qualsevol proveïdor |
| **UptimeRobot** | Avís de caiguda de la web i l'API | Fora del VPS; ubicació de l'empresa [A validar] | 0 € (pla gratuït) | Cap | Només comprova URL públiques; no rep dades de socis | Qualsevol altre monitor extern |
| **GlitchTip o Sentry** | Seguiment d'errors amb traça | Sentry: Frankfurt (empresa dels EUA); GlitchTip: instància a la UE segons la seva web [A validar totes dues] | 0 € (GlitchTip: 1.000 esdeveniments/mes; Sentry: pla Developer) | Cap | La regió de Sentry no es pot canviar un cop creada l'organització | Tots dos fan servir el mateix SDK; GlitchTip es pot autoallotjar |
| **Domini** (cris.barcelona) | Web i correu | — | Cost actual del club [A validar] | Existent | Cal saber qui controla el registrador | Transferible |

### Afegits avaluats amb els cinc criteris
Cap eina de la decisió inicial canvia. Les tres peces afegides passen els criteris:

| Afegit | 1. UE o transferència documentada | 2. Doble factor per a administradors | 3. Cost | 4. Còpia restaurable | 5. Via de sortida |
|---|---|---|---|---|---|
| Hetzner Storage Box | Sí (DE/FI) | Sí (compte de Hetzner) | 3,20 €/mes | És la destinació de còpia | Format restic obert |
| UptimeRobot | No guarda dades personals | Sí | 0 € | No aplica (sense dades) | Substituïble en minuts |
| GlitchTip o Sentry | Regió UE [A validar] | Sí | 0 € | No aplica (dades efímeres) | Mateix SDK per a tots dos |

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

- No inclou el domini (cost actual del club [A validar]; domini a confirmar, P-15).
- **Respecte a la previsió anterior:** els documents d'origen preveien 100-120 €/any. La producció mínima costa ≈160 €/any sense IVA (≈195 €/any amb IVA del 21 %), perquè hi suma la segona destinació de còpies i el VPS de proves.

### Comparació amb Cluber

| | Plataforma (producció mínima) | Cluber |
|---|---|---|
| Cost fix | ≈160 €/any sense IVA (consultat el 27/10/2026) | Des de 599 €/any, pla fins a 200 esportistes (preu publicat segons el document incremental §4.2). Pla i factura reals del club [A validar] |
| Cost variable | Comissions de Stripe (vegeu la taula següent): ≈53-110 €/any per a les quotes, més ≈1,9 % del que es cobri per targeta o Bizum | Comissions de cobrament de Cluber [A validar] |
| Total orientatiu, quotes incloses | ≈215-270 €/any sense IVA | ≥599 €/any més comissions |

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

### 4.1 Model comú (viu al mòdul 04, tresoreria)
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
| **Avís previ** | Abans de cada cobrament s'avisa el soci de l'import i la data [A validar: si ho envia Stripe o la plataforma, i amb quanta antelació] | — |
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
| `EMAIL_DAILY_LIMIT` | Límit diari del pla (300 al gratuït) |
| `EMAIL_TRANSACTIONAL_RESERVE` | Enviaments reservats cada dia per als transaccionals |
| `EMAIL_ALERT_THRESHOLD_PCT` | Percentatge que dispara l'avís (80) |
| `EMAIL_ALERT_TO` | Qui rep l'avís |
| `BREVO_WEBHOOK_SECRET` | Verificació dels avisos de rebots i baixes |

### Pagaments (Stripe i transferència)
| Variable | Ús |
|---|---|
| `STRIPE_SECRET_KEY` | Clau restringida amb els permisos mínims |
| `STRIPE_WEBHOOK_SECRET` | Verificació de la signatura dels webhooks |
| `STRIPE_LIVE_MODE_ALLOWED` | Fals per defecte; només la junta autoritza posar-lo a cert |
| `STRIPE_API_VERSION` | Versió de l'API fixada |
| `CLUB_IBAN_TRANSFERENCIES` | IBAN que es mostra per a les transferències |
| `TRANSFER_REFERENCE_PREFIX` | Prefix de les referències (per exemple, `CRIS`) |

### Observabilitat
| Variable | Ús |
|---|---|
| `ERROR_TRACKING_DSN` | DSN de GlitchTip o Sentry |
| `ERROR_TRACKING_ENVIRONMENT` | Nom de l'entorn als errors |
| `LOG_LEVEL` | Nivell dels registres |

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
| R10b | Pèrdua d'accés de tots els administradors (sense recuperació per correu) | Baixa / alt | Com a mínim dos administradors actius, dos comptes d'emergència i codis de recuperació fora de línia en dos llocs; procediment de restabliment escrit | Presidència + responsable de manteniment |
| R11 | Dades personals en registres o errors | Mitjana / mitjà | Filtres als registres; enviament a GlitchTip o Sentry sense dades personals; revisió d'exemples (E1) | Equip de desenvolupament |
| R12 | Cost per sobre del pressupost aprovat (producció mínima, [016](decisions/016-pressupost-produccio-minima.md)) | Mitjana / mitjà | Límits i alertes de facturació a cada proveïdor (D3); qualsevol pas a l'escenari recomanat es decideix i es registra | Tresorer |
| R13 | Dependència de Stripe | Baixa / mitjà | Model de pagaments propi i independent del proveïdor; transferència i efectiu com a alternatives; exportació periòdica | Tresorer + equip de desenvolupament |
| R14 | Una actualització de Coolify o del sistema trenca el desplegament | Mitjana / mitjà | Instantània abans d'actualitzar; versió fixada; primer a proves | Responsable de manteniment |
| R15 | Canviar els servidors de noms a Cloudflare trenca el correu actual del club | Mitjana / alt | Inventari previ de tots els registres DNS (MX, SPF actuals) abans del canvi | Responsable d'informàtica |
| R16 | Obligacions fiscals (IVA, Verifactu, informació de Bizum a l'Agència Tributària) | Mitjana / alt | Consulta a la gestoria abans d'activar els cobraments (P-02) | Tresorer |

---

## 7. Tasques manuals (per a l'equip i la junta)

No s'ha creat cap compte. Cada compte ha de ser **del club** (correu del club, dades de facturació del club), amb **dos administradors** i doble factor activat.

### Ara (abans del primer codi, porta 0)
- [ ] Decidir el responsable de manteniment a la junta i el segon administrador de tots els comptes.
- [ ] Crear l'organització del repositori (GitHub o GitLab) amb dos propietaris i doble factor.
- [ ] Triar un gestor de contrasenyes del club per guardar credencials i codis de recuperació [A validar quin].
- [ ] Esbrinar quin és el domini actiu del club (cris.es o cris.barcelona, P-15), qui el controla (registrador i accés) i com està gestionat el correu actual; fer inventari dels registres DNS (web WordPress, correu). Necessari per decidir els àlies dels comptes d'administrador ([015](decisions/015-doble-factor-i-comptes-administrador.md)).
- [ ] **Stripe:** obrir el compte de Stripe del club **en mode de proves**, iniciar la verificació de l'entitat (NIF, estatuts, representant legal, compte bancari) i comprovar que s'hi pot activar **Bizum**. Es fa ara perquè la verificació pot trigar.
- [ ] Portar a la junta els punts oberts de [pendents.md](decisions/pendents.md), sobretot P-15 a P-20.

### Abans de l'entorn de proves i la primera demo (porta 1)
- [ ] Crear el compte de **Hetzner** (Cloud i Storage Box), activar el doble factor i fixar un límit o alerta de despesa.
- [ ] Crear el compte de **Scaleway**, regió París, amb doble factor; crear els buckets privats per entorn i el bucket de còpies amb claus separades.
- [ ] Crear el compte de **Cloudflare** i afegir-hi el domini; canviar els servidors de noms al registrador **només** després de copiar tots els registres actuals.
- [ ] Crear el compte de **Brevo**, verificar el domini remitent i publicar SPF, DKIM i DMARC (checklist G1).
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

### Abans de producció
- [ ] Comprovar que el mòdul 05 està acabat i provat (criteri d'entrada, [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md)).
- [ ] Autorització escrita de la junta per activar Stripe en producció.
- [ ] Fer la migració única de Cluber (funcionalitats §9.13) i decidir la data de baixa de Cluber (P-20).
- [ ] Decidir si es contracta Brevo Starter (preu a confirmar en aquell moment).

---

## 8. Preguntes obertes [A validar]

Resolts el 27/10/2026: abast dels cobraments (P-01 → [014](decisions/014-migracio-cluber-i-entrada-en-produccio.md)), pressupost (P-06 → [016](decisions/016-pressupost-produccio-minima.md)) i mètodes de les quotes (P-09 → [017](decisions/017-pagaments-metodes-i-domiciliacions.md)).

1. **Domini:** cris.es o cris.barcelona, i qui el gestiona? (P-15)
2. **Comptes i doble factor:** quins rols compten com a «administrador» (dos comptes) i quins tenen doble factor obligatori? (P-16, P-17)
3. **Cluber:** es manté la campanya de quotes en paral·lel? Quan venç el contracte? (P-20)
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
14. **Domini:** qui el controla i quant costa la renovació?
15. **Temps màxim de recuperació** acceptable si cau el servidor (hores o dies).
16. **Custòdia de claus:** qui guarda la clau de les còpies i els codis de recuperació.
17. **Preus:** confirmar tots els preus d'aquest document a les pàgines oficials en el moment de contractar.

---

## 9. Ordre d'especificació dels mòduls afectats

Correu i fitxers no són mòduls propis a CLAUDE.md: són serveis de la base comuna que fan servir tots els mòduls. Per això s'especifiquen dins de la 00, com a annexos lleugers.

| Ordre | Especificació | Formalitat | Per què en aquest ordre | Depèn de |
|---|---|---|---|---|
| 1 | **00 Base comuna**: persones i comptes (soci i administrador separats), rols, permisos per rol i objecte, TOTP, restabliment sense correu per als administradors, registre d'activitat per compte, RGPD, entorns, cua de tasques, còpies | **Completa** (autenticació, permisos i RGPD) | Tot la fa servir; fixa els rols i els comptes ([015](decisions/015-doble-factor-i-comptes-administrador.md)) | P-04, P-16, P-17, P-18 |
| 1a | 00 · annex **Fitxers** (`specs/00-base-comuna/fitxers.md`): pujada, validació, URL signades, permisos | **Lleugera** | Servei transversal sense regles de negoci pròpies | 00 |
| 1b | 00 · annex **Correu** (`specs/00-base-comuna/correu.md`): plantilles, registre d'enviaments, comptador i reserva diària, tandes, avís al 80 % | **Lleugera** (el butlletí i els consentiments de màrqueting es completen a la 07) | Necessari per a les notificacions de tots els mòduls | 00 |
| 2 | **04 Tresoreria**: càrrecs, estats, moviments immutables, departaments, comptes (banc, caixa, trànsit Stripe), comissions, devolucions com a moviments, conciliació amb CSV, tancament d'activitat | **Completa** (finances) | El model de càrrec, pagament i ingrés viu aquí; pagaments hi escriu a través de serveis. Comissions per departament ([013](decisions/013-imputacio-comissions.md)) | 00; P-02 |
| 3 | **05 Pagaments**: integració amb Stripe (sessions, mandats SEPA amb avís previ, reintent controlat, alternativa de pagament i estat «retornat», webhooks, idempotència, reconciliació diària), transferència amb referència i registre manual | **Completa** (pagaments). És el criteri d'entrada en producció ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md)) | Depèn del model de la 04 | 04; P-12, P-20 |

Notes:
- Les **quotes** (generació anual, remeses) són del mòdul 01 i les **inscripcions**, del 02. La 04 defineix el càrrec genèric que fan servir totes dues. Si la junta vol cobrar quotes abans de tenir el 02, es pot especificar la 01 abans de la 05.
- Com que la 05 inclou les quotes domiciliades i és el criteri d'entrada en producció, la 01 (socis i quotes) s'ha d'especificar abans que la 05.
- Cada especificació completa segueix la plantilla de [metodologia-sdd.md](metodologia-sdd.md) §5 i acaba amb les preguntes obertes, el responsable i la data.

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
