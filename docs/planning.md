# Pla de la plataforma C.R.I.S., mòdul a mòdul

- **Què és:** l'únic fitxer del pla de tots els mòduls i la **font única de la seva especificació** ([047](decisions/047-planning-font-unica-de-l-especificacio.md)). S'hi afegeixen mòduls amb la mateixa estructura de 14 seccions. Cap altre fitxer en copia el contingut: s'hi enllaça per l'àncora.
- **Data de la versió:** 27/10/2026 (la data només identifica la versió; el pla no té calendari, [038](decisions/038-planificar-sense-dates.md)).
- **Com s'aprova:** cada secció de mòdul passa d'«escrit» a «aprovat» quan el responsable del projecte l'aprova. Cap mòdul nou s'afegeix fins que l'anterior està aprovat, excepte quan el responsable del projecte en demana diversos alhora perquè depenen entre ells (04, 05a i 05b; 02 i 03).

<a id="estat"></a>
## 1. Estat i numeració dels mòduls

«Estat» és l'estat de la secció d'aquest pla, no del codi: **pendent** (no escrita), **escrit** (per aprovar), **aprovat**. Ordre de construcció segons la [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md): fase 1, 00 → 01 → 04 → 05a → 05b; fase 2, 02 → 03 → 09 → 06 → 07 → 08; després, 10, 11 i 12. **El número identifica el mòdul, no l'ordre de construcció.**

| Núm. | Mòdul | Fase | Depèn de | Font de l'especificació | Estat al pla |
|---|---|---|---|---|---|
| **00** | Base comuna | 1 | — | [spec 00](../specs/00-base-comuna/spec.md) v2 (fins que el 00 tingui secció aquí) | pendent (el 01 en defineix la part que necessita) |
| **01** | [Socis i carnet digital](#M01) | 1 | 00 | Aquest pla ([047](decisions/047-planning-font-unica-de-l-especificacio.md)) | **aprovat** |
| **02** | [Activitats (cursos i sortides)](#M02) | 2 | 00, 01, 04, 05b | Aquest pla | **escrit** |
| **03** | [Material](#M03) | 2 | 00, 02 | Aquest pla | **escrit** |
| **04** | [Tresoreria, part mínima](#M04) | 1 | 00, 01 | Aquest pla (la spec 04 v2 és a l'[arxiu](arxiu/spec-04-tresoreria-v2-2026-10-27.md)) | **aprovat** |
| **05a** | [Alta del mètode de pagament i mandats](#M05a) | 1 | 01, 04 | Aquest pla | **aprovat** |
| **05b** | [Cobraments](#M05b) | 1 | 05a | Aquest pla | **aprovat** |
| **06** | Llicències | 2 | 01, 05b | — | pendent |
| **07** | Web pública | 2 | 01, 02 | — | pendent |
| **08** | Dashboard | 2 | 01, 02, 04, 09 | — | pendent |
| **09** | Marge, despeses, ajuts i facturació (abans «resta de la 04») | 2 | 02, 03, 04, 05b | — | pendent |
| **10** | Missatges i xat per activitat | després de la 2 | 01, 02 | — | pendent |
| **11** | Departament d'Història i conferències | després de la 2 | 01, 02, 07 | — | pendent |
| **12** | Idees noves (avatars de fauna marina i bitàcola) | després de la 2 | 01, 02, 03 | — | pendent |
| **13** | Botiga en línia | — | — | Fora d'abast ara | — |

**Regles de la numeració** (fixada el 27/10/2026 pel responsable del projecte)
- Cap mòdul no canvia de número. Un mòdul nou s'afegeix al final (14, 15…).
- La web instal·lable ([041](decisions/041-web-installable-i-avisos-sense-push.md)) no és un mòdul: va amb la interfície des del 01.
- Les decisions existents no s'editen. On diguin «resta de la 04» (per exemple, la [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), la [043](decisions/043-proveidor-de-pagaments-dins-la-ue.md) o la spec 04 arxivada), vol dir el **09**. On diguin «mòdul 05» sense lletra, vol dir el 05a i el 05b junts.

<a id="numeracio"></a>
**Correspondència amb altres numeracions**
| Aquest pla | Mapa de la plataforma v8 | Document de funcionalitats (0–11, P-03) | Textos antics |
|---|---|---|---|
| 00 Base comuna | M00 Base | 0 Base comuna | — |
| 01 Socis i carnet digital | M01 Socis i carnet | 1 Socis i carnet | — |
| 02 Activitats | M02 Cursos i M03 Sortides | 2 Cursos i 3 Sortides | — |
| 03 Material | M04 Material | 4 Material i cost per participant | — |
| 04 Tresoreria, part mínima | M05a Tresoreria: nucli | part de 5 Tresoreria | «04 mínim»; «M05a, tresoreria: nucli» (repositori anterior) |
| 05a Alta del mètode de pagament i mandats | part de M05b Pagaments | part de 5 Tresoreria | «mòdul 05» |
| 05b Cobraments | part de M05b Pagaments | part de 5 Tresoreria | «mòdul 05» |
| 06 Llicències | M06 Llicències | 6 Llicències | — |
| 07 Web pública | M07a Web i M07b Ajuda | 7 Web pública (i ajuda) | — |
| 08 Dashboard | M09 Dashboard | 9 Dashboard | — |
| 09 Marge, despeses, ajuts i facturació | M05c Marge, factures i ajuts | part de 5 Tresoreria | «resta de la 04» |
| 10 Missatges i xat per activitat | M07c Missatges | part de 7 (missatges) | — |
| 11 Departament d'Història i conferències | M08 Història | 8 Departament d'Història | — |
| 12 Idees noves | M11 Idees | 10 Comunitat i idees | — |
| 13 Botiga en línia | M10 Botiga | 11 Botiga en línia | — |
| (no és mòdul) | M12 PWA | — | Web instal·lable (041) |

<a id="index"></a>
## 2. Índex
1. [Estat i numeració dels mòduls](#estat) · [correspondència](#numeracio)
2. [Índex](#index)
3. [Regles generals](#regles)
4. [Glossari](#glossari)
5. [Plantilla de secció de mòdul](#plantilla) (l'ordre del fitxer és l'ordre en què s'han escrit els mòduls, no el número)
6. [Mòdul 01 — Socis i carnet digital](#M01) · [resum](#M01-resum)
   1. [Intenció, abast i fora d'abast](#M01-1-intencio)
   2. [Dependències](#M01-2-dependencies)
   3. [Capacitats i històries d'usuari](#M01-3-capacitats)
   4. [Rols i permisos](#M01-4-rols)
   5. [Processos pas per pas](#M01-5-processos)
   6. [Entitats i camps](#M01-6-entitats)
   7. [Regles de negoci i càlculs](#M01-7-regles)
   8. [Serveis i interfícies](#M01-8-serveis)
   9. [Criteris d'acceptació i casos límit](#M01-9-criteris)
   10. [Tasques](#M01-10-tasques)
   11. [Pla de proves](#M01-11-proves)
   12. [Seguretat i RGPD](#M01-12-seguretat)
   13. [Riscos, supòsits i dubtes](#M01-13-riscos)
   14. [Què cal aprovar abans de començar](#M01-14-aprovar)
7. [Mòdul 04 — Tresoreria, part mínima](#M04) · [resum](#M04-resum)
   1. [Intenció](#M04-1-intencio) · 2. [Dependències](#M04-2-dependencies) · 3. [Capacitats](#M04-3-capacitats) · 4. [Rols](#M04-4-rols) · 5. [Processos](#M04-5-processos) · 6. [Entitats](#M04-6-entitats) · 7. [Regles](#M04-7-regles)
   8. [Serveis](#M04-8-serveis) · 9. [Criteris](#M04-9-criteris) · 10. [Tasques](#M04-10-tasques) · 11. [Proves](#M04-11-proves) · 12. [Seguretat](#M04-12-seguretat) · 13. [Riscos](#M04-13-riscos) · 14. [Aprovar](#M04-14-aprovar)
8. [Mòdul 05a — Alta del mètode de pagament i mandats](#M05a) · [resum](#M05a-resum)
   1. [Intenció](#M05a-1-intencio) · 2. [Dependències](#M05a-2-dependencies) · 3. [Capacitats](#M05a-3-capacitats) · 4. [Rols](#M05a-4-rols) · 5. [Processos](#M05a-5-processos) · 6. [Entitats](#M05a-6-entitats) · 7. [Regles](#M05a-7-regles)
   8. [Serveis](#M05a-8-serveis) · 9. [Criteris](#M05a-9-criteris) · 10. [Tasques](#M05a-10-tasques) · 11. [Proves](#M05a-11-proves) · 12. [Seguretat](#M05a-12-seguretat) · 13. [Riscos](#M05a-13-riscos) · 14. [Aprovar](#M05a-14-aprovar)
9. [Mòdul 05b — Cobraments](#M05b) · [resum](#M05b-resum)
   1. [Intenció](#M05b-1-intencio) · 2. [Dependències](#M05b-2-dependencies) · 3. [Capacitats](#M05b-3-capacitats) · 4. [Rols](#M05b-4-rols) · 5. [Processos](#M05b-5-processos) · 6. [Entitats](#M05b-6-entitats) · 7. [Regles](#M05b-7-regles)
   8. [Serveis](#M05b-8-serveis) · 9. [Criteris](#M05b-9-criteris) · 10. [Tasques](#M05b-10-tasques) · 11. [Proves](#M05b-11-proves) · 12. [Seguretat](#M05b-12-seguretat) · 13. [Riscos](#M05b-13-riscos) · 14. [Aprovar](#M05b-14-aprovar)
10. [Mòdul 02 — Activitats (cursos i sortides)](#M02) · [resum](#M02-resum)
   1. [Intenció](#M02-1-intencio) · 2. [Dependències](#M02-2-dependencies) · 3. [Capacitats](#M02-3-capacitats) · 4. [Rols](#M02-4-rols) · 5. [Processos](#M02-5-processos) · 6. [Entitats](#M02-6-entitats) · 7. [Regles](#M02-7-regles)
   8. [Serveis](#M02-8-serveis) · 9. [Criteris](#M02-9-criteris) · 10. [Tasques](#M02-10-tasques) · 11. [Proves](#M02-11-proves) · 12. [Seguretat](#M02-12-seguretat) · 13. [Riscos](#M02-13-riscos) · 14. [Aprovar](#M02-14-aprovar)
11. [Mòdul 03 — Material](#M03) · [resum](#M03-resum)
   1. [Intenció](#M03-1-intencio) · 2. [Dependències](#M03-2-dependencies) · 3. [Capacitats](#M03-3-capacitats) · 4. [Rols](#M03-4-rols) · 5. [Processos](#M03-5-processos) · 6. [Entitats](#M03-6-entitats) · 7. [Regles](#M03-7-regles)
   8. [Serveis](#M03-8-serveis) · 9. [Criteris](#M03-9-criteris) · 10. [Tasques](#M03-10-tasques) · 11. [Proves](#M03-11-proves) · 12. [Seguretat](#M03-12-seguretat) · 13. [Riscos](#M03-13-riscos) · 14. [Aprovar](#M03-14-aprovar)
12. [Apèndix — Preguntes per propietari](#preguntes): [banc](#preguntes-banc) · [PaynoPain](#preguntes-paynopain) · [tresorer](#preguntes-tresorer) · [junta](#preguntes-junta) · [gestoria](#preguntes-gestoria) · [FECDAS](#preguntes-fecdas) · [secretaria](#preguntes-secretaria) · [informàtica](#preguntes-informatica) · [responsable del projecte](#preguntes-responsable)

<a id="regles"></a>
## 3. Regles generals (valen per a tots els mòduls)

**Ordre i temps**
- Cap data, calendari ni termini. L'ordre es fixa per dependències i per valor ([038](decisions/038-planificar-sense-dates.md)). Les fases són les de la [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md).

**Dades i persones**
- Dades personals només dins la UE ([035](decisions/035-dades-nomes-dins-ue.md), [042](decisions/042-proveidors-substituits-pel-requisit-ue.md)). Tot proveïdor passa pel [registre](proveidors-i-dades-ue.md).
- Cap dada personal real al repositori, a la integració contínua ni a les eines d'IA. Fora de producció, només dades inventades ([010](decisions/010-entorns.md)).
- Cap nom de persona als documents: només rols. Hi ha **un sol tresorer** i cap acció necessita doble aprovació (P-48, opcional i futura).
- Cap dada de salut ([CLAUDE.md](../CLAUDE.md); P-07).

**Pagaments** ([043](decisions/043-proveidor-de-pagaments-dins-la-ue.md))
- El proveïdor de pagaments va darrere d'un **adaptador**: canviar de proveïdor no toca la resta de l'aplicació.
- La targeta s'escriu sempre en un camp o una pàgina segura del proveïdor. L'app no veu ni guarda mai el número.
- Bizum, amb estat «esperant confirmació», caducitat i abandonament (spec 04, annex D).
- Camí de reserva sempre disponible: transferència amb referència única per càrrec i conciliació amb l'extracte.
- IBAN i mandat, només xifrats i només per a la domiciliació ([044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)).
- Tot el que depèn del proveïdor porta [A verificar] fins que el banc o PaynoPain ho confirmin (P-44, P-45).

**Diners, permisos i registre**
- Imports en cèntims (enters). Res s'esborra: s'anul·la amb motiu.
- Permisos comprovats **al servidor**, per rol i per objecte, a cada petició. Amagar un botó no és un permís.
- Registre d'activitat immutable (qui, quan, què, valor anterior).

**Documentació**
- Aquest fitxer és la font única de l'especificació de cada mòdul ([047](decisions/047-planning-font-unica-de-l-especificacio.md)). Cap altre fitxer en copia regles, criteris ni tasques.
- No s'edita cap decisió existent: se'n crea una de nova que la substitueix o l'amplia.
- No s'inventa res: el que falta porta [A verificar] (dada externa) o [A validar] (decisió del club), sempre amb propietari. Propietaris possibles: tresorer, junta, banc, PaynoPain, gestoria, FECDAS, secretaria, informàtica, responsable del projecte.

**Pila i interfície**
- Django i PostgreSQL ([002](decisions/002-pila-tecnologica.md)); cua de tasques sobre PostgreSQL ([012](decisions/012-cua-de-tasques.md)).
- **Interfície:** plantilles de Django i **HTMX** servides des del VPS; l'arxiu d'HTMX es serveix des del servidor propi, **sense CDN** ([046](decisions/046-interficie-django-htmx-servida-des-del-vps.md), que substitueix la part de frontend de la 002).
- Web instal·lable, sense botigues i sense notificacions push ([041](decisions/041-web-installable-i-avisos-sense-push.md)).
- Interfície i documents en català; codi en anglès (V-09 de la spec 00).
- Sistema de disseny de les decisions [030](decisions/030-sistema-de-disseny.md) a [034](decisions/034-patrons-magic-portfolio.md): tokens, dos temes, estats amb símbol, text i color, objectiu WCAG 2.2 AA (checklist B8).

**Metodologia aplicada**
Les skills que es van demanar (spec-driven-development, product-capability, intent-driven-development, planning-and-task-breakdown, blueprint, contract-first, security-and-hardening, django-patterns, django-security, postgres-patterns, documentation-and-adrs, doubt-driven-development i accessibility) **no estan instal·lades**. La plantilla de la secció 5 n'aplica l'estructura a mà: intenció i capacitats (1, 3), contracte primer (8), blueprint de dades (6), tasques per dependències (10), seguretat (12) i revisió de dubtes (13). El mateix val per als mòduls 04, 05a, 05b, 02 i 03.

<a id="glossari"></a>
## 4. Glossari

S'amplia a cada mòdul. Els termes de la spec 00 (persona, compte personal, compte d'administrador, convidat, rol, càrrec, pagament, departament, anonimitzar, bloquejar) tenen el mateix significat aquí.

| Terme | Definició | Font |
|---|---|---|
| Persona | Qualsevol individu de qui el club guarda dades. Un sol perfil per persona | Spec 00, glossari |
| Soci | Persona amb una relació de soci: número, tipus, estat i historial. La relació viu al M01; la persona, a la 00 | Spec 00, RN-01 |
| Tipus de soci | **Simpatitzant** (35 €/any) o **ple dret** (90 €/any). Catàleg editable | F §3; context §3 |
| Estat del soci | Pendent, actiu, impagat o baixa ([M01-7](#M01-7-regles)) | F §3 |
| Sol·licitud | Petició d'alta, de canvi de tipus o de baixa, que la secretaria resol | F §3; mapa v8 |
| Número de soci | Identificador únic del soci al club. No es reutilitza mai ([039](decisions/039-numeros-de-soci-no-es-reutilitzen.md)) | F §3 |
| Quota anual | Càrrec de tipus «quota» (estructura de la spec 00) lligat a un soci i a un període | Spec 00, RN-66; decisió 027 |
| Impagat | Estat d'un soci amb la quota del període vigent sense pagar. De moment el marca el tresorer a mà ([040](decisions/040-impagat-es-marca-a-ma.md)) | F §3 |
| Carnet digital | Document del soci amb número, tipus, validesa, anys de soci i un codi QR | F §3 |
| Testimoni del carnet | Valor aleatori que porta el QR. No conté dades personals; la base de dades en guarda l'empremta | Pla M01 anterior, K2 |
| Verificació pública | Pàgina que s'obre en escanejar el QR: diu «vàlid» o «no vàlid» i el número de soci parcial | Aprovació del pla M01 |
| Data d'alta | Data en què la persona es va fer sòcia. Pot ser **real** o **aproximada** (marca) | F §3 («Corregir l'antiguitat») |
| Anys de soci | Anys sencers des de la data d'alta fins avui | F §3 |
| Registre mínim de llicència | Tipus, data d'alta i data de caducitat de la llicència federativa d'un soci, perquè no es perdin dades en deixar Cluber | [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), punt 4 |
| Importació de prova / final | La de prova valida un fitxer de Cluber sense escriure res. La final escriu les dades i només es fa quan el 05a pot rebre els mandats | Aprovació del pla M01 |
| Avatar de fauna marina | Animal marí generat a partir del nom en l'alta; el soci només en canvia el color. Part futura (Could) | F §3; mapa v8 |
| Moviment | Apunt immutable d'un compte de tresoreria: entrada o sortida, import en cèntims, departament i origen. Es corregeix amb un contramoviment | Spec 04, RN-T05 a RN-T07 |
| Compte de trànsit | Compte de tresoreria on entren els cobraments d'un proveïdor (o d'una remesa) fins que arriben al banc | Spec 04, RN-T01 i RN-T08 |
| Liquidació | Abonament agrupat que un proveïdor (o el banc, per una remesa) fa al compte del club, amb brut, comissions i net | Spec 04, RN-T21 |
| Conciliació | Casar una línia de l'extracte bancari amb el que la plataforma esperava (càrrecs, moviments o una liquidació). La plataforma proposa; el tresorer confirma | Spec 04, RN-T14 a RN-T19 |
| Referència de transferència | Codi únic per càrrec amb dígit de control (per exemple, `CRIS-7K3Q9-4`) que el pagador escriu al concepte | Spec 04, RN-T20 |
| Adaptador de proveïdor | Capa del mòdul 05 que parla amb el proveïdor de pagaments. La resta de l'aplicació només parla amb l'adaptador ([043](decisions/043-proveidor-de-pagaments-dins-la-ue.md)) | 043 |
| Intent de pagament | Cada vegada que algú intenta pagar un càrrec (targeta, Bizum, rebut o transferència anunciada). Un càrrec pot tenir diversos intents; com a molt un acaba «pagat» | [M05b-6](#M05b-6-entitats) |
| Mètode de pagament de la quota | Com vol pagar el soci les quotes: domiciliació (amb mandat), targeta guardada (si el proveïdor ho permet) o pagar cada vegada | [M05a-6](#M05a-6-entitats) |
| Mandat SEPA | Autorització del deutor perquè el club li cobri rebuts domiciliats. Té referència única, data de signatura, tipus recurrent i identificador de creditor | [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md) |
| Identificador de creditor | Codi SEPA que identifica el club com a creditor. El dona el banc [A verificar: banc, P-45 punt 5] | 044 |
| Remesa | Fitxer de rebuts domiciliats (pain.008) que la plataforma genera i el tresorer puja al banc | 043 (e); 044 |
| Avís previ | Missatge al deutor abans de cada rebut domiciliat amb data, import, referència del mandat i identificador de creditor | [017](decisions/017-pagaments-metodes-i-domiciliacions.md) |
| Rebut retornat | Rebut domiciliat que el deutor o el seu banc tornen després del cobrament | 017; arquitectura §4.3 |
| Devolució | Retorn de diners que inicia el club (total o parcial). És un moviment nou; la comissió no es recupera | Spec 04, RN-T11 |
| Rebut (justificant) | Document que rep qui paga, amb referència, concepte, import, departament, data i mètode. No és una factura (P-47) | Spec 04, annex D |
| Nivells de producció | Nivell 1: dades reals només per recollir el mètode de pagament i els mandats, cap cobrament real. Nivell 2: cobraments reals | [025](decisions/025-dos-nivells-de-produccio.md), [042](decisions/042-proveidors-substituits-pel-requisit-ue.md) |
| Activitat | Curs (una convocatòria d'un curs o d'una especialitat) o sortida. Té departament, places, preus i estat ([M02-5](#M02-5-processos)). Les conferències s'hi afegiran amb l'11 | F §4 i §5 |
| Catàleg de cursos / d'especialitats | Dos catàlegs separats de fitxes reutilitzables amb preu de soci i de no soci. Els cursos són formació per nivells; les especialitats, formacions concretes que s'afegeixen a un nivell | F §4 |
| Convocatòria | Cada edició d'un curs o d'una especialitat, amb dates, places, preu i sessions | F §4 |
| Sessió | Classe d'un curs: teoria (aula), piscina o mar, amb lloc, hora i instructors. Se n'hi poden afegir quan calgui | F §4 |
| Classe de reforç | Sessió extra per a un alumne que no assoleix el nivell, sense moure el grup. Té cost i és un ús nou de material | F 9.17; resposta del 22/10/2026 |
| Inscripció | Lligam d'una persona (sòcia o convidada) amb una activitat, amb el seu preu i el seu càrrec. Estats a [M02-5](#M02-5-processos) | F §4 i §5 |
| Llista d'espera i oferta de plaça | Inscripcions sense plaça, per ordre. Quan se n'allibera una, el primer rep una oferta amb un termini per acceptar-la | F §4 |
| Programa del dia | Blocs horaris d'una sortida (trobada, briefing, immersió, dinar, tornada) | F §5 |
| Tipus i subtipus de sortida | Tipus: immersió, medi ambient, Sèniors, jornada oberta. Subtipus (només medi ambient): la mena d'acció, per exemple una neteja; la llista és ampliable | F §5; resposta del 22/10/2026 |
| Projecte de medi ambient | Agrupa sortides, resultats i, amb el 09, factures i ajuts | F §5 |
| Resultats ambientals | Residus (en grams), espècies, observacions i fotos d'una sortida de medi ambient | F §5 |
| Titulació | Nivell de busseig d'una persona (agència, nivell, número), declarat o obtingut en un curs del club. No és una dada de salut | [M02-6](#M02-6-entitats) |
| Certificat del club | PDF amb número que rep l'alumne apte. No substitueix la titulació oficial | RN-M02-16 |
| Duplicar | Crear una activitat nova a partir d'una d'anterior, sense inscrits ni pagaments ([026](decisions/026-duplicar-activitats-al-modul-02.md)) | RN-M02-21 |
| Peça | Cada unitat de material del club, amb codi, tipus, talla o litres i estat | F §6 |
| Tipus de material | Aletes, màscara, tub, neoprè, escarpins, ploms, jaquet, regulador, ordinador, brúixola, boia, llanterna, ganivet de seguretat i ampolla (litres lliures). Llista ampliable | F §6 |
| Stock | Recompte de peces per tipus, talla i estat en una data | F §6 |
| Origen del material | Propi del participant, del club o llogat a un centre de busseig | F §6 |
| Assignació | Material concret d'un participant per a una activitat (o una classe de reforç), amb origen, cost i estat | [M03-6](#M03-6-entitats) |
| Centre de busseig i tarifa | Centre amb què treballa el club; per a cada equip o servei, preu de cost i preu per al soci. La diferència és el marge del lloguer | F §6 |
| Llista de lloguer | Llista per centre del material que s'ha de llogar per a una activitat | F §6 |
| Cost d'ús | Cost per dia del material del club (amortització o tarifa fixa, [A validar]) | F §6 |
| Material típic | Plantilla del material que cal per a un curs, una especialitat o un tipus de sortida | F §6 |
| Revisió | Manteniment o prova periòdica d'una peça; mentre dura, la peça no es pot assignar | F 9.7 |
| Registre d'immersió | Per a cada activitat a què una persona ha assistit, el material que ha fet servir. La bitàcola completa és del 12 | F §5 i §6 |

<a id="plantilla"></a>
## 5. Plantilla de secció de mòdul

Cada mòdul es titula «Mòdul NN — Nom» amb l'ancora `MNN`. Just després de l'estat i les fonts hi ha un **resum d'una pàgina** (àncora `MNN-resum`): intenció, processos que cobreix, quantes tasques té, què el bloqueja i què cal aprovar. Després venen aquestes 14 seccions amb ancores estables `MNN-<número>-<nom>`:

| # | Secció | Ancora | Què hi va |
|---|---|---|---|
| 1 | Intenció, abast i fora d'abast | `MNN-1-intencio` | Per què, resultat esperat, com sabrem que funciona, què entra i què no |
| 2 | Dependències | `MNN-2-dependencies` | De què depèn (i quina part) i què en depèn |
| 3 | Capacitats i històries d'usuari | `MNN-3-capacitats` | Capacitats numerades i històries «Com a… vull… per…» |
| 4 | Rols i permisos | `MNN-4-rols` | Els 13 rols per acció, i permisos per objecte |
| 5 | Processos pas per pas | `MNN-5-processos` | Passos, ordre de pantalles i wireframes que les cobreixen |
| 6 | Entitats i camps | `MNN-6-entitats` | Tipus, restriccions, índexs, relacions, migracions, seguretat de dades |
| 7 | Regles de negoci i càlculs | `MNN-7-regles` | Regles numerades i exemples numèrics |
| 8 | Serveis i interfícies | `MNN-8-serveis` | Contracte del que ofereix i del que consumeix |
| 9 | Criteris d'acceptació i casos límit | `MNN-9-criteris` | Donat… Quan… Llavors…, i casos límit |
| 10 | Tasques | `MNN-10-tasques` | Descripció, esforç (S/M/L), fitxers, depèn de, com es comprova. Sense dates |
| 11 | Pla de proves | `MNN-11-proves` | Unitàries, permisos per rol, integració, accessibilitat; dades inventades |
| 12 | Seguretat i RGPD | `MNN-12-seguretat` | Específics del mòdul |
| 13 | Riscos, supòsits i dubtes | `MNN-13-riscos` | Cadascun amb propietari; revisió de dubtes al final |
| 14 | Què cal aprovar abans de començar | `MNN-14-aprovar` | Llista curta de decisions |

**Esforç:** S = una tasca petita amb proves (poques hores); M = diverses peces o una pantalla completa; L = un flux sencer o una peça amb risc. Sense dates.

---

<a id="M01"></a>
# Mòdul 01 — Socis i carnet digital

**Estat: aprovat** pel responsable del projecte el 27/10/2026, amb les respostes recollides a [M01-14](#M01-14-aprovar).

**Fonts integrades:** el pla M01 del repositori anterior (aprovat amb respostes el 27/10/2026), la [spec 00](../specs/00-base-comuna/spec.md) v2, el document de funcionalitats (F §3 i processos 9.2 a 9.5 i 9.13), el mapa de la plataforma v8 i les decisions 035–047. Per la [047](decisions/047-planning-font-unica-de-l-especificacio.md), aquesta secció **és** l'especificació del M01: no hi ha cap `specs/01-…`.

<a id="M01-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Tenir els socis, les quotes anuals i el carnet digital a la plataforma, perquè la secretaria deixi Excel i correu, cada soci vegi les seves dades i el seu carnet, i Cluber es pugui deixar. Cap altre mòdul no funciona sense aquest. |
| **Processos que cobreix** | P-M01-A Alta de soci · P-M01-B Canvi de tipus · P-M01-C Baixa i readmissió · P-M01-D Renovació anual de quotes · P-M01-E Carnet i verificació pública · P-M01-F RGPD: exportar i esborrar · P-M01-G Importació de Cluber en dues fases (F 9.2 a 9.5 i 9.13) |
| **Tasques** | 29 (T-M01-01 a T-M01-29), incloses les peces de la 00 que el 01 necessita |
| **Què el bloqueja** | Res per començar. La importació final espera el 05a (nivell 1) i la mostra anonimitzada de Cluber [A validar: tresorer, S-M01-16] |
| **Què cal aprovar** | Aprovat el 27/10/2026 ([M01-14](#M01-14-aprovar)). Continua obert sense bloquejar: la matriu dels 13 rols (junta, P-04) i els supòsits de [M01-13](#M01-13-riscos) ([apèndix](#preguntes)) |

<a id="M01-1-intencio"></a>
## M01-1 Intenció, abast i fora d'abast

**Per què.** Avui els socis, les quotes i el carnet són a Cluber, i les altes, les baixes i els canvis es creuen a mà amb Excel i correu. Sense els socis a la plataforma, cap altre mòdul no pot funcionar, i Cluber no es pot deixar ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md)).

**Resultat esperat.**
- La secretaria gestiona en un sol lloc les altes, les baixes, els canvis de tipus i l'antiguitat.
- Cada soci veu les seves dades, les seves quotes i el seu carnet amb QR des de la web instal·lable.
- Qualsevol persona pot comprovar si un carnet és vàlid sense veure'n dades personals.
- Cada any es generen les quotes de tots els socis actius, sense duplicats.
- El fitxer de Cluber es pot validar (importació de prova) abans de fer la migració.

**Com sabrem que funciona.**
- Una alta es fa de principi a fi sense sortir de la plataforma (llevat del pagament, que és del 05b).
- La llista de socis actius coincideix amb la importació de prova de Cluber.
- Un carnet escanejat diu correctament «vàlid» o «no vàlid».
- Tot canvi d'un soci queda al registre d'activitat amb qui, quan, què i el valor anterior.

**Dins de l'abast.**
- Alta (formulari web i presencial), revisió i aprovació, assignació de número.
- Canvi de tipus (simpatitzant ↔ ple dret), baixa, readmissió.
- Fitxa i historial del soci; correcció de la data d'alta (real o aproximada).
- Quotes anuals com a càrrecs (estructura de la spec 00): generació, estat i recordatoris.
- Impagat marcat a mà pel tresorer ([040](decisions/040-impagat-es-marca-a-ma.md)).
- Carnet digital amb QR, PDF i verificació pública.
- Àrea del soci: perfil, carnet, quotes, sol·licituds, consentiments, exportar i esborrar.
- Registre mínim de llicència (tipus, data d'alta i de caducitat) ([024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md)).
- Importació de Cluber en **dues fases**: la de prova (en aquest mòdul) i la final (quan el 05a pugui rebre els mandats).
- La part de la 00 que el M01 necessita ([M01-2](#M01-2-dependencies)).

**Fora d'abast.**
- Cobrar: targeta, Bizum, domiciliació i transferència són del 05b. El **mandat SEPA i l'IBAN** són del 05a ([044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)).
- Moviments de tresoreria, comissions i conciliació (04).
- Llicències completes: preus, renovacions, no socis, tramitació (06, [036](decisions/036-fecdas-alia.md)).
- **Avatars de fauna marina:** part futura (Could). El M01 només en deixa preparada la llavor (vegeu RN-M01-30).
- Bitàcola i insígnies (12; P-38). Missatges (10). Botigues d'apps i notificacions push ([041](decisions/041-web-installable-i-avisos-sense-push.md)).
- Dades de salut, incloent-hi la data del certificat mèdic (P-07).
- Data de naixement i relació amb tutors, fins que es respongui P-33 / Q-09.

<a id="M01-2-dependencies"></a>
## M01-2 Dependències

**De què depèn (de la 00, només la part que el M01 necessita).** Aquestes peces es construeixen dins les tasques del M01 ([M01-10](#M01-10-tasques)) seguint la spec 00; la resta de la 00 s'afegeix quan la necessiti un altre mòdul.

| Peça de la 00 | Què en fa servir el M01 | Referència a la spec 00 |
|---|---|---|
| Persona (perfil únic, duplicats, dades mínimes) | Cada soci és una persona | RN-01 a RN-10; V-03, V-04 |
| Compte personal (correu, verificació, recuperació, TOTP opcional) | Àrea del soci | RN-11 a RN-18; V-01 |
| Compte d'administrador amb TOTP obligatori i rols | Secretaria, tresorer, administrador | RN-11 a RN-27 |
| Rols i permisos per rol i objecte | Tota la matriu de [M01-4](#M01-4-rols) | §2; RN-40 a RN-45 |
| Registre d'activitat | Tots els canvis de socis i quotes | RN-50 a RN-53 |
| Consentiments i textos legals | Formulari d'alta i perfil | HU-17; RN-80 |
| Sol·licituds RGPD, anonimització i bloqueig | Exportar i esborrar | HU-18, HU-19; RN-81 a RN-91 |
| Càrrec i departament (estructura bàsica) | Quotes anuals | HU-15, HU-16; RN-60 a RN-76 |
| Correu (annex A), versió mínima | Confirmacions i recordatoris | Annex A |
| Fitxers privats (annex B) | PDF del carnet i exportacions | Annex B |
| Lot i línia d'importació | Importació de Cluber | HU-20; RN-92 a RN-101 |

**Peces de la 00 que s'afegeixen després (no les necessita el M01):** enllaços de convidat (necessaris al 02 i al 05b), comptes d'emergència complets i codis de recuperació (abans de producció), importació de l'extracte bancari (04), comptador diari de correu i butlletí (07), consulta de dades bloquejades M13 (abans de producció).

**Què depèn del M01.**
| Mòdul | Què necessita del M01 |
|---|---|
| 04 | Quotes com a càrrecs; estat de quota per a la secretaria (spec 04, T11) |
| 05a | Socis actius per signar mandats; **importació final de Cluber** |
| 05b | Quotes per cobrar; carnet que es reactiva en pagar; impagats |
| 06 | Registre mínim de llicència |
| 02 | Saber si una persona és sòcia (preu de soci) |
| 07 | Botó «Fer-se soci» de la web pública |
| 08 | Recomptes de socis per tipus i estat |
| 12 Idees noves | Llavor de l'avatar fixada en l'alta |

<a id="M01-3-capacitats"></a>
## M01-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | Pantalles (mapa v8) |
|---|---|---|---|
| C1 | Entrar: compte personal amb correu; compte d'administrador amb nom d'usuari i TOTP | Tothom amb compte | Inici de sessió, Recuperar contrasenya |
| C2 | Demanar l'alta | Visitant; secretaria (presencial) | Fer-se soci |
| C3 | Revisar i aprovar o rebutjar altes, assignar número | Secretaria | Altes pendents |
| C4 | Consultar i editar socis, amb historial | Secretaria; consulta del tresorer | Llistat de socis, Fitxa del soci |
| C5 | Veure i editar les seves dades i consentiments | Soci | El meu perfil |
| C6 | Demanar el canvi de tipus i la baixa | Soci | Sol·licitar canvi a ple dret, Sol·licitar la baixa |
| C7 | Generar les quotes anuals i veure'n l'estat; marcar i desmarcar impagats | Tresorer; consulta de la secretaria | Quotes, remeses i impagats |
| C8 | Veure les seves quotes i rebuts | Soci | Les meves quotes |
| C9 | Carnet digital amb QR i PDF | Soci | El meu carnet |
| C10 | Verificar un carnet | Qualsevol persona | Verificació del carnet |
| C11 | Exportar i esborrar les seves dades | Soci | El meu perfil, Esborrar el meu compte |
| C12 | Validar el fitxer de Cluber (prova) i, quan toqui, importar-lo (final) | Administrador | Migració des de Cluber |
| C13 | Corregir la data d'alta i marcar-la com a real o aproximada | Secretaria | Fitxa del soci |
| C14 | Registre mínim de llicència | Secretaria | Fitxa del soci |

**Històries d'usuari**
- **HU-M01-01.** Com a visitant, vull demanar l'alta des de la web amb les meves dades, el tipus i els consentiments, per fer-me soci sense anar al local.
- **HU-M01-02.** Com a secretaria, vull donar d'alta presencialment una persona, per atendre qui no fa servir la web.
- **HU-M01-03.** Com a secretaria, vull que la plataforma m'avisi si el document d'identitat ja existeix, per no duplicar persones.
- **HU-M01-04.** Com a secretaria, vull aprovar o rebutjar una sol·licitud i que el número s'assigni sol, per no portar el comptador a mà.
- **HU-M01-05.** Com a secretaria, vull buscar i filtrar socis per tipus i estat i exportar-los, per respondre consultes de la junta.
- **HU-M01-06.** Com a secretaria, vull veure a la fitxa tot l'historial d'estats i tipus, amb data i autor, per saber què ha passat.
- **HU-M01-07.** Com a secretaria, vull corregir la data d'alta quan es recupera (actes, carnets antics), per reconèixer l'antiguitat real.
- **HU-M01-08.** Com a soci, vull veure i corregir el meu correu, telèfon i adreça, per tenir-los al dia.
- **HU-M01-09.** Com a simpatitzant, vull demanar el canvi a ple dret i veure l'import abans de confirmar, per saber què pagaré.
- **HU-M01-10.** Com a soci, vull demanar la baixa amb un motiu, per deixar el club de manera clara.
- **HU-M01-11.** Com a tresorer, vull generar les quotes de l'any de tots els socis actius d'una vegada i sense duplicats, per començar la campanya.
- **HU-M01-12.** Com a tresorer, vull marcar i desmarcar un soci com a impagat amb un motiu, mentre no hi hagi regla automàtica.
- **HU-M01-13.** Com a soci, vull veure les meves quotes per any i el seu estat, i descarregar-ne el rebut quan estigui pagada.
- **HU-M01-14.** Com a soci, vull el meu carnet amb QR al mòbil, també sense cobertura, i en PDF.
- **HU-M01-15.** Com a persona d'un centre de busseig, vull escanejar el QR i saber si el carnet és vàlid, sense veure dades personals.
- **HU-M01-16.** Com a soci, vull descarregar totes les meves dades i poder demanar-ne l'esborrat.
- **HU-M01-17.** Com a administrador, vull validar el fitxer de Cluber sense escriure res, per detectar errors abans de la migració.
- **HU-M01-18.** Com a administrador, vull fer la importació final quan el 05a pugui rebre mandats, i poder-la desfer si no s'ha creat res a partir d'ella.
- **HU-M01-19.** Com a secretaria, vull guardar el tipus i les dates de la llicència d'un soci, per no perdre-les en deixar Cluber.

<a id="M01-4-rols"></a>
## M01-4 Rols i permisos

**Els 13 rols.** Els 8 de la spec 00 més els 5 del mapa v8 que no hi són (Visitant, Participant no soci, Resp. comunicació, Junta, Resp. botiga). Que aquests 5 siguin rols del model és P-04 / Q-01 [A validar: junta]: mentre no es decideixi, Visitant és «sense sessió», Participant no soci és el **convidat** de la [021](decisions/021-persones-no-socies-com-a-convidades.md), i els altres tres no tenen cap permís al M01.

Llegenda: **Sí**; **Propi** (només la seva persona); **Consulta** (només veure); **—** (no); **[A validar]** (junta, Q-01).

| # | Acció | Visitant | Part. no soci | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Resp. comunicació | Dept. Història | Junta | Administrador | Resp. botiga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | Enviar el formulari «Fer-se soci» | Sí | Sí | — | — | — | — | — | — | — | — | — | — | — |
| P2 | Crear una alta presencial | — | — | — | — | Sí | — | — | — | — | — | — | Sí | — |
| P3 | Aprovar o rebutjar altes | — | — | — | — | Sí | — | — | — | — | — | — | Sí | — |
| P4 | Llistat i fitxa de socis | — | — | — | — | Sí | — | — | Consulta (dades mínimes) | — | — | [A validar] | Sí | — |
| P5 | Editar dades d'un soci (inclòs document i número) | — | — | — | — | Sí | — | — | — | — | — | — | Sí | — |
| P6 | Corregir la data d'alta | — | — | — | — | Sí | — | — | — | — | — | — | Sí | — |
| P7 | Resoldre canvis de tipus i baixes | — | — | — | — | Sí | — | — | — | — | — | — | Sí | — |
| P8 | Generar quotes anuals | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| P9 | Marcar i desmarcar impagat | — | — | — | — | — | — | — | Sí | — | — | — | [A validar] | — |
| P10 | Veure l'estat de quotes de tots els socis | — | — | — | — | Consulta | — | — | Sí | — | — | — | Sí | — |
| P11 | Exportar el llistat de socis | — | — | — | — | Sí | — | — | [A validar] | — | — | — | Sí | — |
| P12 | Veure i editar les seves dades i consentiments | — | Propi (compte opcional) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| P13 | Veure el seu carnet i les seves quotes | — | — | Propi | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci |
| P14 | Demanar canvi de tipus o baixa | — | — | Propi | Propi si és soci | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) |
| P15 | Verificar un carnet (pàgina pública) | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí |
| P16 | Demanar l'exportació o l'esborrat de les seves dades | — | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| P17 | Atendre sol·licituds RGPD d'altres | — | — | — | — | [A validar] | — | — | — | — | — | — | [A validar] | — |
| P18 | Importació de Cluber (prova i final) i desfer | — | — | — | — | — | — | — | — | — | — | — | Sí | — |
| P19 | Registre mínim de llicència | — | — | Consulta (propi) | — | Sí | Consulta | — | Consulta | — | — | — | Sí | — |
| P20 | Consultar el registre d'activitat dels socis | — | — | — | — | [A validar] | — | — | — | — | — | — | Sí | — |

**Com es llegeix amb els comptes.** Les files «Propi» es fan amb el **compte personal**; les de gestió, amb el **compte d'administrador** amb el rol corresponent i TOTP ([015](decisions/015-doble-factor-i-comptes-administrador.md), [018](decisions/018-perfil-comptes-i-rols.md)). El compte d'administrador no entra a l'àrea de socis i el compte personal no hereta cap rol (spec 00, §2.6).

**Per objecte.**
- Soci: només la seva persona, el seu soci, les seves quotes, el seu carnet i les seves sol·licituds (RN-42). Intentar obrir un altre soci retorna «no trobat» i queda al registre.
- Tresorer: llistat i fitxa amb **dades mínimes per cobrar**: número, nom, tipus, estat i quotes. No veu document, adreça ni consentiments (spec 00, §2.5; Q-01).
- Secretaria: totes les persones sòcies. No veu imports de tresoreria fora de l'estat de les quotes.
- Conflicte d'interès: un compte d'administrador no pot aprovar la seva pròpia alta, canviar el seu propi estat ni marcar-se impagat (Q-11) [A validar: junta]. Proposta: rebutjar-ho i registrar l'intent.

<a id="M01-5-processos"></a>
## M01-5 Processos pas per pas

**Wireframes existents** (`design/wireframes/`):
- `publica.html`: secció i botó «Fer-se soci» (`#fer-se-soci`).
- `socis.html`: portada del compte personal, **carnet giratori** (`#carnet`, davant i darrere), franja d'estat de pagaments (`#franja-estat`), avisos, llicència (`#llicencia`) i la invitació «Uneix-te al club» per a qui no és soci.
- `admin.html`: barra lateral filtrada per rol (`data-rols`) i el patró de fitxa amb taula, cerca i filtres (es fa servir per a una activitat; el M01 el reutilitza per a la fitxa i el llistat de socis).
- **Falten** wireframes de: formulari «Fer-se soci», altes pendents, llistat i fitxa de soci, quotes i impagats, verificació pública, migració de Cluber, perfil, sol·licituds i esborrar el compte. Tasca T-M01-02 ([M01-10](#M01-10-tasques)).

### P-M01-A Alta de soci (F §9.2)
| Pas | Qui | Què passa | Pantalla (ruta del mapa v8) | Wireframe |
|---|---|---|---|---|
| 1 | Visitant | Obre «Fer-se soci» des de la web pública | `/fer-se-soci` | `publica.html#fer-se-soci` (botó); formulari: falta |
| 2 | Visitant | Omple dades mínimes (V-04: nom, cognoms, document, correu, telèfon; adreça opcional), tria el tipus i accepta els textos legals obligatoris. **Sense mandat SEPA** (és del 05a) | `/fer-se-soci` | Falta |
| 3 | Sistema | Comprova duplicats (RN-M01-03). Desa la sol·licitud «pendent de revisió» i els consentiments. Envia un correu de rebut de la sol·licitud | — | — |
| 3b | Secretaria | (Alta presencial) Omple el mateix formulari des de l'administració; el consentiment es registra com a presencial (canal i compte) | `/gestio/socis/altes/nova` | Falta |
| 4 | Secretaria | Revisa la sol·licitud a «Altes pendents»; veu l'avís de possible duplicat | `/gestio/socis/altes` | Falta |
| 5a | Secretaria | **Aprova:** es crea el soci (estat **pendent**), s'assigna el número (RN-M01-05), es crea la quota del període (RN-M01-12) i s'envia una invitació per activar el compte personal | `/gestio/socis/altes` | Falta |
| 5b | Secretaria | **Rebutja** amb motiu: no es crea cap soci ni es consumeix cap número; s'avisa la persona | `/gestio/socis/altes` | Falta |
| 6 | Soci | Activa el compte personal (verificació de correu) i veu la quota pendent i el botó «Paga ara» (el pagament és del 05b) | `/socis` | `socis.html#franja-estat` |
| 7 | Sistema | Quan la quota passa a «pagat» (05b o conciliació de la 04), el soci passa a **actiu** i es genera el carnet | — | — |
| 8 | Soci | Veu el carnet | `/socis/carnet` | `socis.html#carnet` |

### P-M01-B Canvi de tipus (F §9.3)
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Soci (simpatitzant actiu) | Obre «Sol·licitar canvi a ple dret»; veu l'import calculat (RN-M01-15) i confirma | `/socis/canvi-tipus` | Falta |
| 2 | Sistema | Crea la sol·licitud i un càrrec de quota pel suplement (si l'import és > 0) | — | — |
| 3 | Secretaria | Aprova la sol·licitud. El canvi de tipus és **efectiu quan el suplement està pagat** [A validar: junta] | `/gestio/socis/{id}` | Falta |
| 4 | Sistema | Canvia el tipus amb data efectiva, ho desa a l'historial, **revoca el carnet anterior i n'emet un de nou** | — | — |
Canvi de ple dret a simpatitzant: no consta enlloc [A validar: junta]. Proposta: només s'aplica a la quota del període següent.

### P-M01-C Baixa (F §9.4)
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Soci o junta | El soci la demana amb motiu i confirmació; o la secretaria la crea per decisió de la junta | `/socis/baixa`; `/gestio/socis/{id}` | Falta |
| 2 | Secretaria | La valida i fixa la data efectiva | `/gestio/socis/{id}` | Falta |
| 3 | Sistema | A la data efectiva: estat **baixa**, carnet revocat, correu de confirmació. Quotes pendents: vegeu RN-M01-20 | — | — |
| 4 | Sistema | El compte personal es manté per consultar rebuts (Q-31, proposta) [A validar: junta] | — | — |
El número queda reservat per sempre ([039](decisions/039-numeros-de-soci-no-es-reutilitzen.md)). Si la persona torna, es **readmet** amb el mateix número (P-M01-A des del pas 4).

### P-M01-D Renovació anual de quotes (F §9.5)
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Tresorer | Tria el període i veu una **previsualització**: quants socis actius, quantes quotes de cada tipus i l'import total | `/gestio/quotes` | Falta |
| 2 | Tresorer | Confirma: es crea una quota per soci actiu o impagat (RN-M01-12), departament «General / Quotes de socis» | `/gestio/quotes` | Falta |
| 3 | Sistema | Envia l'avís de quota nova al soci (correu i safata d'avisos de l'app) | — | `socis.html#avisos` |
| 4 | Sistema | Recordatoris abans i després del venciment (RN-M01-14) | — | — |
| 5 | Tresorer | Revisa les quotes pendents i **marca impagat** a mà amb motiu ([040](decisions/040-impagat-es-marca-a-ma.md)) | `/gestio/quotes` | Falta |
| 6 | Sistema | Quan una quota es paga (05b o 04), avisa el tresorer perquè desmarqui l'impagat | — | — |
La remesa de domiciliacions és del 05b; el M01 només crea les quotes.

### P-M01-E Carnet i verificació pública
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Sistema | En passar a actiu (o en un canvi de tipus), genera un carnet amb un testimoni aleatori nou; el QR porta l'URL de verificació amb el testimoni | — | — |
| 2 | Soci | Veu el carnet (davant: nom, número, tipus, vàlid fins a, anys de soci, QR; darrere: [A validar, decisió 032]) i el descarrega en PDF. La web instal·lable el guarda per veure'l sense cobertura | `/socis/carnet` | `socis.html#carnet` |
| 3 | Qualsevol persona | Escaneja el QR i obre la pàgina de verificació | `/carnet/verificar/{testimoni}` | Falta |
| 4 | Sistema | Mostra **«Vàlid»** o **«No vàlid»** i el número de soci parcial (RN-M01-26). Res més. Si el nom de pila s'hi ha de mostrar és [A validar: junta] | — | — |
Sense cobertura, el carnet desat es mostra amb la marca «Comprovat per última vegada: [data]», perquè qui el mira sàpiga que pot no estar al dia.

### P-M01-F RGPD: exportar i esborrar
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Soci | Demana «Descarregar les meves dades» | `/socis/perfil` | Falta |
| 2 | Sistema | Prepara un fitxer JSON amb persona, soci, historial, quotes, carnets (sense testimonis), sol·licituds, consentiments i llicència; URL signada, disponible 7 dies (V-08) | — | — |
| 3 | Soci | Demana «Esborrar el meu compte» amb confirmació | `/socis/perfil/esborrar` | Falta |
| 4 | Responsable RGPD | Aprova la sol·licitud (Q-15) [A validar: junta] | `/gestio/rgpd` | Falta |
| 5 | Sistema | Fa la baixa si és soci actiu, desactiva els comptes, anonimitza les dades personals, **bloqueja** quotes i rebuts fins al termini legal (Q-14), i substitueix la identitat al registre per una referència anònima ([028](decisions/028-esborrat-rgpd-i-registre-d-activitat.md)). El número de soci queda reservat i lligat a la referència anònima | — | — |

### P-M01-G Importació de Cluber, en dues fases (F §9.13; HU-20)
**Fase 1, prova (en aquest mòdul).**
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Administrador | Puja l'exportació de Cluber (fitxer inventat o anonimitzat fora de producció) | `/gestio/importacions/cluber` | Falta |
| 2 | Sistema | Rebutja el fitxer sencer si té una columna d'IBAN (RN-94). Valida cada línia i fa coincidir per document o número de soci (RN-95) | — | — |
| 3 | Administrador | Veu el resum: nous, coincidents, errors per línia, i el que es crearia (socis, tipus, estats, dates d'alta, quotes històriques, llicències). **No s'escriu res** | `/gestio/importacions/cluber` | Falta |
**Fase 2, final (quan el 05a pugui rebre els mandats).**
| Pas | Qui | Què passa |
|---|---|---|
| 4 | Administrador | Torna a pujar l'exportació definitiva i la confirma (excloent explícitament les línies amb error, V-06) |
| 5 | Sistema | Crea persones i socis amb el seu número de Cluber, la data d'alta (marcada aproximada si no és segura), l'estat, el registre mínim de llicència i les **quotes històriques** com a registres informatius (RN-M01-33). Tot porta l'identificador del lot |
| 6 | Sistema | Prepara la campanya de mandats nous del 05a (escenari B, [022](decisions/022-mandats-sepa-escenari-base-b.md)): cap IBAN importat |
| 7 | Administrador | Pot desfer el lot si encara no s'ha creat res a partir d'ell (V-06). Només hi ha una importació final confirmada (RN-93) |

<a id="M01-6-entitats"></a>
## M01-6 Entitats i camps

Noms de codi en anglès (V-09). App Django `members` (nova); les entitats de la 00 viuen a `core` (o les apps que fixi el pla de la 00). Cap camp de salut, cap IBAN, cap data de naixement (fins a Q-09).

### MembershipType (tipus de soci)
| Camp | Tipus | Restriccions |
|---|---|---|
| `code` | `CharField(20)` | Únic. Valors inicials: `supporter` (simpatitzant), `full` (ple dret) |
| `name` | `CharField(60)` | Text en català |
| `annual_fee_cents` | `PositiveIntegerField` | Inicial: 3500 i 9000. Editable només pel tresorer o l'administrador; cada canvi, al registre amb motiu |
| `active` | `BooleanField` | Un tipus amb socis no s'esborra; es desactiva |

### Member (soci)
| Camp | Tipus | Restriccions |
|---|---|---|
| `person` | `OneToOneField(Person, PROTECT)` | Un sol soci per persona (readmissió = mateix registre) |
| `member_number` | `PositiveIntegerField` | Únic per a tota la història; mai es reutilitza ([039](decisions/039-numeros-de-soci-no-es-reutilitzen.md)). Null fins que s'aprova l'alta |
| `type` | `ForeignKey(MembershipType, PROTECT)` | — |
| `status` | `CharField` amb opcions `pending`, `active`, `unpaid`, `left` | Només canvia per serveis (RN-M01-08) |
| `joined_on` | `DateField` | Data d'alta |
| `joined_on_is_approximate` | `BooleanField` | Cert per defecte en importacions sense data segura |
| `left_on` | `DateField` null | Data efectiva de la baixa |
| `cluber_id` | `CharField(40)` null | Únic quan no és null. Només per a la importació |
| `avatar_seed` | `CharField(64)` | Llavor aleatòria fixada en l'alta per a l'avatar futur (RN-M01-30). No canvia mai. Els socis importats de Cluber la reben en la importació final |
| `import_batch` | `ForeignKey(ImportBatch)` null | Lot de Cluber |
| `created_at`, `updated_at` | `DateTimeField` | — |
**Índexs:** únic `member_number` (parcial, no null); únic `cluber_id` (parcial); índex `(status, type)` per als filtres del llistat.

### MemberStatusChange (historial)
`member` (FK), `from_status`, `to_status`, `from_type`, `to_type`, `effective_on` (Date), `reason` (Text, obligatori en baixa, impagat i desmarcar), `actor_account` (FK compte, o null si és el sistema), `created_at`. Només s'hi afegeix: sense UPDATE ni DELETE (com el registre d'activitat). Índex `(member, created_at)`.

### MemberRequest (sol·licitud)
| Camp | Tipus | Restriccions |
|---|---|---|
| `kind` | `join`, `change_type`, `leave` | — |
| `person` | FK Person | Per a `join`, la persona creada o trobada |
| `member` | FK Member null | Null per a `join` fins que s'aprova |
| `requested_type` | FK MembershipType null | `join` i `change_type` |
| `reason` | Text | Obligatori per a `leave` i per rebutjar |
| `channel` | `web`, `in_person` | — |
| `status` | `pending`, `approved`, `rejected`, `cancelled` | Només una `pending` del mateix `kind` per persona |
| `resolved_by`, `resolved_at`, `effective_on` | — | — |
| `duplicate_warning` | JSON | Coincidències trobades (V-03), sense dades sensibles |

### MembershipNumberCounter
Una sola fila amb `last_number`. S'actualitza amb `SELECT … FOR UPDATE` dins la mateixa transacció que aprova l'alta. Després de la importació final, `last_number` = número més alt importat. No es fa servir una seqüència de PostgreSQL perquè una transacció desfeta en consumiria números.

### AnnualFee (quota anual)
| Camp | Tipus | Restriccions |
|---|---|---|
| `member` | FK Member (PROTECT) | — |
| `period` | `PositiveSmallIntegerField` (any) | Únic `(member, period, kind)` |
| `kind` | `annual`, `type_change_supplement` | — |
| `charge` | `OneToOneField(Charge)` (spec 00) | Tipus de càrrec «quota»; departament «General / Quotes de socis» |
| `due_on` | `DateField` | Venciment [A validar: tresorer, P-29] |
L'estat i l'import són els del càrrec (spec 00, RN-60 i RN-67); no es dupliquen.

### HistoricFee (quota històrica importada)
`member`, `period`, `amount_cents`, `status_in_cluber` (text normalitzat), `import_batch`. Només lectura. **No és un càrrec i no genera moviments de tresoreria**: els diners els va cobrar Cluber (RN-M01-33).

### MemberCard (carnet)
| Camp | Tipus | Restriccions |
|---|---|---|
| `member` | FK Member | — |
| `token_hash` | `CharField(64)` | Únic. Empremta (SHA-256) d'un testimoni aleatori de 256 bits; el testimoni sencer no es desa |
| `issued_at` | `DateTimeField` | — |
| `revoked_at`, `revoked_reason` | null | En canvi de tipus, baixa o petició |
**Índex:** únic parcial «un carnet no revocat per soci». El PDF es genera a demanda (annex B de la 00) i no es desa.

### LicenceRecord (registre mínim de llicència)
`member`, `licence_type` (text; llista de la FECDAS [A verificar: FECDAS]), `issued_on`, `expires_on`, `source` (`manual`, `cluber`), `import_batch`. Sense número federatiu fins que la 06 ho defineixi [A validar: secretaria]. Restricció: `expires_on ≥ issued_on`.

### Seguretat de dades i migracions
- Migracions reversibles; dades inicials (tipus, departament, rols) en migracions de dades.
- Les taules d'historial només admeten INSERT per a l'usuari de l'aplicació (permisos de PostgreSQL), com el registre d'activitat.
- El document d'identitat és a `Person` (00), normalitzat; mai es mostra sencer al tresorer.
- Cap camp d'IBAN: una prova revisa el model (CA-15.6 de la 00); el mandat xifrat de la 044 viu al 05a.

<a id="M01-7-regles"></a>
## M01-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M01-01 | Persona i soci són entitats separades; una persona té com a màxim un soci | Spec 00, RN-01 |
| RN-M01-02 | Dades mínimes del soci: nom, cognoms, document, correu i telèfon; adreça opcional | V-04 |
| RN-M01-03 | Mateix document → és la mateixa persona; mateix correu o nom i telèfon → avís; mai es fusiona sol | V-03 |
| RN-M01-04 | El document d'identitat i el número de soci no es repeteixen | F §3 |
| RN-M01-05 | El número s'assigna en **aprovar** l'alta, continuant el llistat actual: `últim número + 1`. Un rebuig no consumeix cap número | F §3; [039](decisions/039-numeros-de-soci-no-es-reutilitzen.md) |
| RN-M01-06 | Un número no es reutilitza mai; qui torna, recupera el seu | 039 |
| RN-M01-07 | Estats: pendent (aprovat, sense la quota pagada) → actiu (quota pagada) → impagat (marcat a mà) → actiu (desmarcat); pendent, actiu o impagat → baixa. Cap altra transició | F §3; 040 |
| RN-M01-08 | Cada canvi d'estat o tipus crea una entrada d'historial amb data efectiva, autor i, si cal, motiu | F §3 |
| RN-M01-09 | L'impagat **no** és automàtic: el tresorer el marca i desmarca amb motiu | 040 |
| RN-M01-10 | Un soci només veu les seves dades | F §3; RN-42 |
| RN-M01-11 | Les quotes són ingrés general: departament «General / Quotes de socis». No entren al marge de cap activitat | F §3; [013](decisions/013-imputacio-comissions.md) |
| RN-M01-12 | Una quota anual per soci i període; generar-les dues vegades no duplica res | Proposta (idempotència) |
| RN-M01-13 | Import de la quota = `annual_fee_cents` del tipus en el moment de generar-la. Un canvi de preu posterior no canvia les quotes ja creades | Proposta |
| RN-M01-14 | Recordatoris: N dies abans i M dies després del venciment [A validar: tresorer]. Proposta: 15 dies abans, 15 i 30 dies després | F §3 |
| RN-M01-15 | Import del canvi a ple dret: **la secretaria l'escriu a mà** en aprovar el canvi, fins que la junta decideixi la regla. La proposta més simple per a la junta és la **diferència** entre quotes (9000 − 3500 = 5500 cèntims, 55 €) [A validar: junta] | F §3, pregunta 1; aprovació del M01, resposta 2 |
| RN-M01-16 | Un soci que s'apunta a mig any paga la quota sencera del període [A validar: junta] | F §9.2 («quota de l'any») |
| RN-M01-17 | Període de la quota = **any natural** (supòsit aprovat); data de venciment pendent del tresorer (P-29) [A validar: tresorer] | Aprovació del M01, resposta 3 |
| RN-M01-18 | Carnet **vàlid** ⇔ soci actiu ∧ quota del període vigent pagada ∧ carnet no revocat | F §3 |
| RN-M01-19 | «Vàlid fins a» = últim dia del període pagat | Proposta |
| RN-M01-20 | En una baixa, les quotes pendents de períodes posteriors a la data efectiva s'anul·len amb motiu; les anteriors es mantenen [A validar: tresorer] | Proposta; RN-61 |
| RN-M01-21 | Anys de soci = anys sencers entre `joined_on` i avui. Si la data és aproximada, el carnet diu «des de ~AAAA» | F §3 |
| RN-M01-22 | La secretaria pot corregir la data d'alta; queda a l'historial amb el valor anterior | F §3 |
| RN-M01-23 | Insígnia de soci clàssic: llindar [A validar: junta]; només si la data no és aproximada | Mapa v8 |
| RN-M01-24 | El QR no conté dades personals: només l'URL amb el testimoni aleatori | Pla M01 anterior, K2 |
| RN-M01-25 | Canvi de tipus, baixa o petició del soci → el carnet es revoca i, si escau, se n'emet un de nou | Pla M01 anterior |
| RN-M01-26 | La verificació pública mostra «Vàlid»/«No vàlid» i els **dos últims dígits** del número (per exemple «··87») [A validar: junta]. El nom de pila, [A validar: junta] | Aprovació del pla M01 |
| RN-M01-27 | Un testimoni desconegut o revocat dona «No vàlid», amb la mateixa resposta i el mateix temps que un de vàlid sense quota | Proposta (no revelar) |
| RN-M01-28 | La pàgina de verificació té limitació de peticions (V-01) | RN-24 |
| RN-M01-29 | Registre mínim de llicència: tipus, data d'alta i de caducitat | 024 |
| RN-M01-30 | L'avatar futur es genera a partir del nom **en l'alta**; corregir el nom després no el canvia. **La llavor es desa en l'alta** (camp `avatar_seed`); el M01 no implementa l'avatar | F §3; mapa v8; aprovació del M01, resposta 5 |
| RN-M01-31 | Importació de Cluber: prova sense escriure res; final quan el 05a pugui rebre mandats; una sola final; sense IBAN | Aprovació del pla M01; RN-93, RN-94 |
| RN-M01-32 | Els números de Cluber es conserven; el comptador continua després del més alt | F §3 («continuant el llistat actual») |
| RN-M01-33 | Les quotes cobrades per Cluber s'importen com a **quotes històriques** informatives, no com a càrrecs ni moviments | Proposta (RN-71: un càrrec només passa a pagat per proveïdor, conciliació o registre manual) |
| RN-M01-34 | Un soci importat com a actiu amb la quota del període vigent pagada a Cluber té el carnet vàlid fins al final del període [A validar: tresorer] | Proposta |

**Exemples numèrics**
- **Quotes:** simpatitzant `3500` cèntims (35,00 €); ple dret `9000` cèntims (90,00 €).
- **Campanya (RN-M01-12):** 150 socis actius (hipòtesi de l'arquitectura §3), 100 simpatitzants i 50 de ple dret → 150 quotes; total = 100 × 3500 + 50 × 9000 = **800.000 cèntims (8.000,00 €)**. Tornar a generar-les → 0 quotes noves.
- **Canvi a ple dret (RN-M01-15), tres opcions:** diferència = 9000 − 3500 = **5500 cèntims (55,00 €)**; complet = **9000**; prorrata amb 6 mesos per acabar el període = 5500 × 6 / 12 = **2750 cèntims (27,50 €)**. Arrodoniment proposat: per avall al cèntim.
- **Número (RN-M01-05):** últim número importat 1286 → la propera alta aprovada rep **1287**; una sol·licitud rebutjada entremig no en consumeix cap.
- **Anys de soci (RN-M01-21):** alta 15/03/1998, avui 27/10/2026 → **28 anys**; alta 15/11/1998 → 27 anys (encara no ha fet l'aniversari).
- **Validesa (RN-M01-19):** quota del període 2027 pagada → «Vàlid fins al 31/12/2027» (amb RN-M01-17).
- **Número parcial (RN-M01-26):** 1287 → «··87».

<a id="M01-8-serveis"></a>
## M01-8 Serveis i interfícies (contracte)

Cap altra app escriu als models del M01: tot passa per aquests serveis (CLAUDE.md). Signatures en Python; errors com a excepcions de domini amb missatge en català.

**Ofereix**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `members.is_member(person, on=date)` | persona, data | `bool` (actiu o impagat a la data) | — | 02, 06, 07 |
| `members.get_member_summary(person)` | persona | número, tipus, estat, vàlid fins a | `NotAMember` | 04, 05a, 05b, 08 |
| `members.on_fee_paid(annual_fee_id)` | quota | passa de pendent a actiu i emet carnet; si és impagat, avisa el tresorer | `InvalidTransition` | 05b, 04 (en conciliar) |
| `members.on_fee_returned(annual_fee_id)` | quota | avisa el tresorer (l'impagat continua sent manual, 040) | — | 05b |
| `members.verify_card(token)` | testimoni | `{valid: bool, partial_number: str}` | — (sempre la mateixa forma) | Pàgina pública |
| `members.active_members_for_mandates()` | — | llista de socis per a la campanya de mandats | — | 05a |
| `members.stats(on=date)` | data | recomptes per tipus i estat, altes i baixes del mes | — | 08 |
| `members.export_personal_data(person)` | persona | diccionari per a l'exportació RGPD | — | 00 (RGPD) |
| `members.anonymise(person)` | persona | anonimitza el que és del M01 i bloqueja quotes | — | 00 (RGPD) |

**Consumeix (de la 00 i d'altres mòduls)**
| Servei | Mòdul | Per a què |
|---|---|---|
| `persons.find_duplicates(data)`, `persons.create_or_get(data)` | 00 | Alta i importació |
| `accounts.invite_personal_account(person)` | 00 | Activar el compte personal en aprovar l'alta |
| `permissions.require(account, action, obj)` | 00 | Cada vista |
| `audit.record(actor, action, obj, field, old, new, reason)` | 00 | Tot canvi |
| `consents.record(person, legal_text, action, channel, by)` | 00 | Alta i perfil |
| `charges.create_charge(person, kind="quota", amount_cents, department, concept, origin)` i `charges.cancel(charge, reason)` | 00 | Quotes i suplements |
| `mail.send(template, to, context)` | 00 (annex A) | Correus |
| `files.render_private_pdf(...)` | 00 (annex B) | PDF del carnet |
| `imports.create_batch(kind="cluber", ...)` | 00 | Importació |
| `treasury.transfer_reference(charge)` | 04 | Mostrar com pagar per transferència (quan existeixi la 04; nom fixat a [M04-8](#M04-8-serveis)) |

**Rutes (interfície)**
- Públiques (declarades a la llista de RN-40): `/fer-se-soci`, `/carnet/verificar/{testimoni}`.
- Compte personal: `/socis`, `/socis/perfil`, `/socis/carnet`, `/socis/quotes`, `/socis/canvi-tipus`, `/socis/baixa`, `/socis/perfil/esborrar`.
- Administració (ruta discreta `ADMIN_URL_PATH`): `/gestio/socis`, `/gestio/socis/{id}`, `/gestio/socis/altes`, `/gestio/quotes`, `/gestio/importacions/cluber`.

<a id="M01-9-criteris"></a>
## M01-9 Criteris d'acceptació i casos límit

**Alta**
- **CA-M01-01** Donat el formulari amb dades vàlides i els textos obligatoris acceptats, quan s'envia, llavors es crea una sol·licitud «pendent», es desen els consentiments amb versió i canal, i no es crea cap soci.
- **CA-M01-02** Donat un document que ja existeix, quan s'envia, llavors no es crea cap persona nova i la sol·licitud queda lligada a la persona existent amb un avís per a la secretaria; el visitant veu un missatge que no revela si el document existia.
- **CA-M01-03** Donat una sol·licitud aprovada, quan es desa, llavors el soci queda «pendent», amb número = últim + 1, una quota del període i una invitació per activar el compte.
- **CA-M01-04** Donat dues aprovacions simultànies, quan es processen, llavors reben números diferents i consecutius (prova de concurrència).
- **CA-M01-05** Donat una sol·licitud rebutjada, quan es desa, llavors cal motiu, no es crea cap soci i el comptador no canvia.
- **CA-M01-06** Donat un soci pendent amb la quota pagada (servei `on_fee_paid`), quan es processa, llavors passa a actiu i té un carnet vàlid.

**Estats i historial**
- **CA-M01-07** Donat qualsevol transició que no és a RN-M01-07, quan es demana, llavors es rebutja i l'estat no canvia.
- **CA-M01-08** Donat un canvi d'estat o de tipus, quan es desa, llavors hi ha una entrada d'historial i una al registre d'activitat amb el valor anterior.
- **CA-M01-09** Donat el tresorer, quan marca un soci com a impagat sense motiu, llavors es rebutja; amb motiu, el carnet passa a «no vàlid».

**Quotes**
- **CA-M01-10** Donat 150 socis actius, quan es generen les quotes d'un període dues vegades, llavors n'hi ha exactament 150, amb departament «General / Quotes de socis».
- **CA-M01-11** Donat un canvi de preu del tipus, quan es generen quotes després, llavors fan servir el preu nou i les anteriors no canvien.
- **CA-M01-12** Donat un soci, quan obre «Les meves quotes», llavors només veu les seves, amb estat i, si està pagada, el rebut.

**Carnet i verificació**
- **CA-M01-13** Donat un carnet vàlid, quan s'escaneja el QR, llavors la pàgina diu «Vàlid» i «··87», i cap altra dada (comprovat a l'HTML).
- **CA-M01-14** Donat un testimoni inventat, revocat o d'un soci impagat, quan es consulta, llavors diu «No vàlid» amb la mateixa estructura de resposta.
- **CA-M01-15** Donat un canvi de tipus aprovat i efectiu, quan es consulta el carnet antic, llavors diu «No vàlid» i el nou diu «Vàlid».
- **CA-M01-16** Donat més peticions de verificació que el límit de V-01 des d'un mateix origen, quan se'n fa una altra, llavors es bloqueja temporalment.
- **CA-M01-17** Donat el compte personal sense connexió, quan s'obre el carnet a la web instal·lable, llavors es mostra el darrer carnet desat amb «Comprovat per última vegada: [data]».

**RGPD**
- **CA-M01-18** Donat un soci que demana l'exportació, quan es resol, llavors el fitxer conté totes les seves dades del M01 i cap dada d'altres persones ni cap testimoni.
- **CA-M01-19** Donat un esborrat aprovat, quan es processa, llavors el soci queda de baixa, la persona anonimitzada, els carnets revocats, les quotes bloquejades, i el número continua reservat.

**Importació**
- **CA-M01-20** Donat un fitxer de Cluber inventat, quan es fa la prova, llavors es veu el resum i la base de dades no canvia (es compara el recompte de taules abans i després).
- **CA-M01-21** Donat un fitxer amb columna d'IBAN, quan es puja, llavors es rebutja sencer.
- **CA-M01-22** Donat una importació final confirmada, quan es dona d'alta un soci nou, llavors rep el número més alt importat + 1.
- **CA-M01-23** Donat que el 05a no està preparat per rebre mandats, quan es vol confirmar la importació final, llavors el botó no està disponible i el servidor ho rebutja (opció de configuració `CLUBER_FINAL_IMPORT_ALLOWED`, fals per defecte).

**Permisos**
- **CA-M01-24** Donat cada cel·la de la matriu de [M01-4](#M01-4-rols), quan el rol prova l'acció, llavors el resultat coincideix amb la matriu (una prova per cel·la).
- **CA-M01-25** Donat un soci que demana la fitxa d'un altre per URL, quan es processa, llavors rep «no trobat» i l'intent queda al registre.

**Casos límit**
| # | Cas | Comportament |
|---|---|---|
| L-M01-01 | Una parella comparteix correu | Totes dues persones poden ser sòcies; només una té compte personal amb aquell correu (V-05) |
| L-M01-02 | Algú torna després d'una baixa | Readmissió amb el mateix número; nova entrada d'historial; la data d'alta original es manté i la nova es registra a l'historial [A validar: junta: si l'antiguitat compta des de la primera alta] |
| L-M01-03 | El soci demana la baixa amb una quota pendent | Vegeu RN-M01-20 |
| L-M01-04 | Canvi a ple dret demanat amb la quota del període pendent | Es rebutja fins que la quota estigui pagada [A validar: junta] |
| L-M01-05 | Una persona de la secretaria vol aprovar la seva pròpia alta | Es rebutja (Q-11) |
| L-M01-06 | El fitxer de Cluber té dos socis amb el mateix document | Les dues línies surten com a error; cal resoldre-ho abans de confirmar |
| L-M01-07 | El fitxer de Cluber no té data d'alta d'un soci | Es fa servir la data més antiga coneguda i es marca com a aproximada [A validar: secretaria] |
| L-M01-08 | No hi ha cap soci (instal·lació nova) | El llistat diu «Encara no hi ha socis. Importa'ls de Cluber o dona'n d'alta un» |
| L-M01-09 | El soci no té cap quota | «Les meves quotes» diu «Encara no tens cap quota» |
| L-M01-10 | Un menor demana l'alta | Bloquejat per P-33: el formulari demana confirmar que és major d'edat [A validar: junta] |

<a id="M01-10-tasques"></a>
## M01-10 Tasques (per dependències, sense dates)

Fitxers orientatius; els fixa el pla tècnic de la 00. «Feta quan» sempre inclou les proves en verd i la revisió d'una persona.

| # | Tasca | Esforç | Fitxers afectats | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M01-01 | Decisions sobre la interfície ([046](decisions/046-interficie-django-htmx-servida-des-del-vps.md)) i sobre la font única de l'especificació ([047](decisions/047-planning-font-unica-de-l-especificacio.md)) | S | `docs/decisions/046-…md`, `047-…md`, `CLAUDE.md` | Aprovació del M01 | **Feta** (27/10/2026) |
| T-M01-02 | Wireframes que falten (formulari d'alta, altes pendents, llistat, fitxa, quotes, verificació, migració, perfil, sol·licituds, esborrar) amb el sistema de disseny | M | `design/wireframes/socis.html`, `admin.html`, `publica.html` | — | Revisats; contrast comprovat |
| T-M01-03 | Esquelet del projecte Django des de `main`, amb l'estructura d'apps de la PR #1 anterior; configuració per entorns; CI amb proves, lint i escaneig de secrets | M | `pyproject.toml`, `config/settings/`, `.github/workflows/` | T-M01-01 | El pipeline passa en buit |
| T-M01-04 | **Model d'usuari propi** abans de la primera migració, i model `Person` (00) | M | `apps/core/models.py`, `migrations/0001_*` | T-M01-03 | Proves de creació i duplicats (V-03) |
| T-M01-05 | Comptes personal i d'administrador, entrada separada, TOTP obligatori a l'administració, bloqueig per intents (V-01) | L | `apps/accounts/` | T-M01-04 | Proves de C2, C3, C4, C5 de la checklist |
| T-M01-06 | Rols (8 de la 00 + els que decideixi P-04) i comprovació de permisos per rol i objecte | M | `apps/core/permissions.py` | T-M01-05 | Prova de la llista de rutes sense sessió (RN-40) |
| T-M01-07 | Registre d'activitat immutable (també a PostgreSQL) | M | `apps/core/audit.py`, migració de permisos | T-M01-04 | Prova que un UPDATE directe falla |
| T-M01-08 | Textos legals i consentiments amb versió i canal | S | `apps/core/consents.py` | T-M01-07 | CA-17.x de la 00 |
| T-M01-09 | Càrrec i departament (estructura bàsica de la 00) | M | `apps/core/charges.py` | T-M01-07 | CA-15.x i CA-16.x de la 00 |
| T-M01-10 | Correu mínim (plantilles, cua) i fitxers privats (PDF) | M | `apps/core/mail.py`, `files.py` | T-M01-03 | Correu a la bústia de proves; URL signada caduca |
| T-M01-11 | Models del M01: tipus, soci, historial, sol·licitud, comptador, carnet, llicència | M | `apps/members/models.py` | T-M01-04, T-M01-09 | Restriccions i índexs comprovats amb proves |
| T-M01-12 | Serveis d'estat i transicions (RN-M01-07 a RN-M01-09) | M | `apps/members/services.py` | T-M01-11, T-M01-07 | CA-M01-07 a 09 |
| T-M01-13 | Formulari «Fer-se soci» i alta presencial | M | `apps/members/views/public.py`, plantilles | T-M01-08, T-M01-12, T-M01-02 | CA-M01-01, 02 |
| T-M01-14 | Altes pendents: aprovar, rebutjar, número amb bloqueig | M | `apps/members/views/admin.py` | T-M01-13 | CA-M01-03 a 05 |
| T-M01-15 | Llistat i fitxa de soci (filtres, historial, exportació) | M | `apps/members/views/admin.py` | T-M01-12 | Proves de permisos per rol |
| T-M01-16 | Àrea del soci: perfil, quotes, sol·licituds | M | `apps/members/views/personal.py` | T-M01-12, T-M01-05 | CA-M01-12, 25 |
| T-M01-17 | Canvi de tipus i baixa (sol·licitud i resolució) | M | `services.py`, vistes | T-M01-16 | Proves de P-M01-B i C |
| T-M01-18 | Generació de quotes, recordatoris i marca d'impagat | M | `apps/members/fees.py`, tasques de la cua | T-M01-09, T-M01-12 | CA-M01-09 a 11 |
| T-M01-19 | Carnet: testimoni, revocació, PDF, pàgina del soci | M | `apps/members/cards.py` | T-M01-12, T-M01-10 | CA-M01-15 |
| T-M01-20 | Verificació pública amb limitació de peticions | S | `apps/members/views/public.py` | T-M01-19 | CA-M01-13, 14, 16 |
| T-M01-21 | Web instal·lable: manifest, service worker amb carnet sense connexió | M | `static/`, plantilla base | T-M01-19 | CA-M01-17 |
| T-M01-22 | RGPD del M01: exportació i anonimització | M | `apps/members/privacy.py` | T-M01-12; HU-18 i HU-19 de la 00 | CA-M01-18, 19 |
| T-M01-23 | Registre mínim de llicència a la fitxa | S | `models.py`, vistes | T-M01-15 | Prova de dates |
| T-M01-24 | Importació de Cluber, **fase de prova** (sense escriure res), feta i provada amb un **fitxer inventat** amb el format de S-M01-16 | L | `apps/members/imports/cluber.py` | T-M01-11 | CA-M01-20, 21. Quan arribi la mostra real anonimitzada (Q-23), es repeteix la prova i s'ajusta el format |
| T-M01-25 | Importació de Cluber, **fase final** preparada però bloquejada per configuració | M | `apps/members/imports/cluber.py` | T-M01-24 | CA-M01-22, 23 |
| T-M01-26 | Serveis oferts a altres mòduls (§8) amb proves de contracte | S | `apps/members/services.py` | T-M01-12, T-M01-19 | Proves de contracte en verd |
| T-M01-27 | Dades de prova inventades (socis, quotes, carnets, fitxer de Cluber) | S | `apps/members/fixtures/`, ordre de gestió | T-M01-11 | Es carreguen amb una ordre; cap dada real |
| T-M01-28 | Revisió d'accessibilitat i de permisos del mòdul | M | — | T-M01-13 a T-M01-21 | Auditoria automàtica sense errors greus; revisió amb teclat i lector de pantalla |
| T-M01-29 | Documentació: guia de la secretaria i del tresorer; actualitzar aquest pla i la spec | S | `docs/` | T-M01-28 | Revisada |

<a id="M01-11-proves"></a>
## M01-11 Pla de proves

- **Unitàries (cobertura completa dels càlculs, checklist B1):** transicions d'estat, comptador de números (inclosa la concurrència), generació idempotent de quotes, imports de canvi de tipus en les tres opcions, anys de soci (aniversari abans i després), validesa del carnet, número parcial.
- **Permisos per rol (B4):** una prova per cel·la de la matriu de [M01-4](#M01-4-rols) amb els 13 rols; proves d'objecte (soci A no veu el soci B; el tresorer no veu el document); llista de rutes sense sessió.
- **Integració:** alta de principi a fi (formulari → aprovació → quota → `on_fee_paid` simulat → carnet → verificació); baixa; canvi de tipus; esborrat RGPD; importació de prova i final amb fitxers inventats (correctes, amb errors, amb IBAN, buits, duplicats; B9).
- **Contracte:** proves dels serveis de §8 amb les formes de sortida exactes.
- **Seguretat:** testimonis endevinats o revocats; limitació de peticions; capçaleres; CSRF als formularis HTMX.
- **Accessibilitat (B8, WCAG 2.2 AA):** eina automàtica [A validar: informàtica, per exemple axe amb Playwright] a totes les pantalles del M01; navegació amb teclat; lector de pantalla al formulari d'alta, al carnet i a la verificació; estats amb símbol, text i color.
- **Dispositius i xarxa (B5, B6):** carnet sense connexió i amb xarxa lenta al mòbil.
- **Dades de prova:** només inventades (noms ficticis, documents amb format vàlid però inexistents); cap exportació real de Cluber fora de producció.

<a id="M01-12-seguretat"></a>
## M01-12 Seguretat i RGPD

- **Minimització:** només V-04; sense data de naixement, sense salut, sense IBAN. El document es mostra emmascarat fora de la secretaria.
- **QR:** testimoni aleatori de 256 bits; només se'n desa l'empremta; revocable; la verificació no revela si un testimoni ha existit.
- **Verificació pública:** limitació de peticions, sense indexació (`noindex`), sense dades personals.
- **Permisos:** al servidor, per rol i objecte; proves per cel·la.
- **Registre:** tot canvi de soci, quota, carnet, sol·licitud i importació; cap secret ni testimoni.
- **Base legal:** relació de soci (estatuts) per a les dades de soci; consentiment per al butlletí i la imatge (Q-16). [A validar: responsable de protecció de dades, Q-15]
- **Conservació:** després de la baixa, el que obliga la llei (quotes i rebuts bloquejats, Q-14) [A validar: gestoria].
- **Esborrat:** decisió 028; el número queda reservat i lligat a una referència anònima.
- **Importació:** el fitxer de Cluber no es desa (RN-101); cap IBAN; la importació real només a producció.
- **Dades dins la UE:** base de dades, còpies i correu dins la UE ([035](decisions/035-dades-nomes-dins-ue.md)); el correu, segons P-46.
- **Fitxers:** PDF del carnet generat a demanda; exportació RGPD amb URL signada de 5 minuts i esborrada als 7 dies (V-08).

<a id="M01-13-riscos"></a>
## M01-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| El format real de l'exportació de Cluber és desconegut (Q-23, P-21) | Alt per a la importació | Fase de prova amb una mostra anonimitzada abans de la final | Tresorer (demanar-la a Cluber) |
| L'ordre 00 → 01 → 04 → 05a: el M01 genera quotes que no es poden cobrar fins al 05b | Mitjà | El M01 no entra sol a producció ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md)); Cluber continua cobrant | Responsable del projecte |
| La matriu de 13 rols no està validada (P-04) | Mitjà | Permisos per configuració; proves per cel·la que es regeneren | Junta |
| Les regles d'impagat i de canvi de tipus no estan fixades | Mitjà | 040 (manual) i import a mà (RN-M01-15) | Junta |
| ~~HTMX contradiu la 002~~ | — | Resolt per la [046](decisions/046-interficie-django-htmx-servida-des-del-vps.md) | — |
| **Mandats SEPA de Cluber.** La importació final no porta IBAN (RN-94; [022](decisions/022-mandats-sepa-escenari-base-b.md)). No se sap si els mandats vigents que gestiona Cluber es poden traspassar al club ni en quines condicions | Alt: decideix si els socis han de signar un mandat nou (05a) o no | Preguntar-ho al **banc** o a la **gestoria** abans de preparar la campanya de mandats del 05a. **No es dona per fet en cap sentit**: ni que es poden traspassar ni que no. Mentre no hi hagi resposta, el 05a es prepara per a tots dos casos ([M05a-13](#M05a-13-riscos)) | Tresorer |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M01-01 | Import del canvi a ple dret (diferència 55 €, complet o prorrata) | **Aprovat:** la secretaria l'escriu a mà fins que la junta decideixi. La diferència (55 €) és la proposta més simple per a la junta | Junta |
| S-M01-02 | Quota sencera per a les altes a mig any | Sí | Junta |
| S-M01-03 | Període = any natural i data de venciment de les quotes | **Aprovat:** any natural com a supòsit; el venciment queda pendent del tresorer (P-29) | Tresorer |
| S-M01-04 | Dies dels recordatoris | 15 abans, 15 i 30 després | Tresorer |
| S-M01-05 | Quotes pendents en una baixa | S'anul·len les posteriors a la data efectiva | Tresorer |
| S-M01-06 | Número parcial a la verificació | Dos últims dígits | Junta |
| S-M01-07 | Nom de pila a la verificació | No es mostra | Junta |
| S-M01-08 | Contingut del darrere del carnet ([032](decisions/032-immersio-socis-i-centre.md)) | Contacte del club i instruccions de verificació | Junta |
| S-M01-09 | Llindar de soci clàssic | Sense insígnia | Junta |
| S-M01-10 | Antiguitat d'una readmissió | Compta des de la primera alta | Junta |
| S-M01-11 | Drets del simpatitzant respecte del ple dret (F §3) | Mateixos al M01; diferències als mòduls 02 i 06 | Junta |
| S-M01-12 | Es manté el compte personal després de la baixa (Q-31) | Sí, per consultar rebuts | Junta |
| S-M01-13 | Socis menors (P-33, Q-09) | Només majors d'edat | Junta |
| S-M01-14 | Qui atén les sol·licituds RGPD (Q-15) | Administrador | Junta |
| S-M01-15 | Terminis de conservació (Q-14) | Bloqueig fins que la gestoria ho digui | Gestoria |
| S-M01-16 | Format i contingut de l'exportació de Cluber (Q-23) | **Aprovat:** es treballa amb un **fitxer inventat** (CSV amb número, document, nom, tipus, estat, data d'alta, quotes i llicència). La mostra real anonimitzada de Cluber és pendent del tresorer (Q-23) | Tresorer |
| S-M01-17 | Tipus de llicència de la FECDAS | Text lliure fins a la 06 | FECDAS |
| S-M01-18 | Data d'alta desconeguda a Cluber | Data més antiga coneguda, aproximada | Secretaria |
| S-M01-19 | Remitent dels correus (Q-26) i proveïdor de correu (P-46) | `no-respon@cris1954.cat`, correu a la bústia de proves | Informàtica |
| S-M01-20 | Eina d'auditoria d'accessibilitat | axe amb Playwright | Informàtica |
| S-M01-21 | Llavor de l'avatar ja al M01 | **Resolt:** es desa en l'alta (RN-M01-30) | — |
| S-M01-22 | Conflicte d'interès (Q-11) | Ningú no aprova ni canvia el seu propi soci | Junta |
| S-M01-23 | Els rols Junta, Resp. comunicació i Resp. botiga existeixen al model (P-04) | Existeixen sense permisos al M01 | Junta |
| S-M01-24 | Quotes de socis importats pagades a Cluber per al període vigent (RN-M01-34) | El carnet és vàlid fins a final del període | Tresorer |
| S-M01-25 | Traspàs al club dels mandats SEPA vigents de Cluber (risc nou) | Cap supòsit: pregunta oberta al banc o a la gestoria | Tresorer |

**Revisió de dubtes (doubt-driven, aplicada a mà)**
1. **El soci «pendent» no té carnet fins que paga, però el pagament no existeix fins al 05b.** En desenvolupament es prova amb `on_fee_paid` simulat; en producció no passa perquè el M01 no hi entra sol. Propietari: responsable del projecte.
2. **El pla M01 anterior deixava que el tresorer marqués quotes com a pagades a mà; ara això és el registre manual bloquejat per P-12 (RN-72).** S'ha tret del M01. Si el club vol cobrar en efectiu abans del 05b, cal resoldre P-12. Propietari: junta i tresorer.
3. **Els diners de Cluber no passen per la tresoreria de la plataforma.** Per això les quotes cobrades per Cluber són «quotes històriques» informatives (RN-M01-33). Si el tresorer necessita que constin com a ingressos, cal una regla a la 04. Propietari: tresorer.
4. **El mapa v8 posava el mandat SEPA al formulari d'alta.** Ara és del 05a ([044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)): el formulari no el demana. Els socis nous aprovats abans del 05a hauran de signar-lo després. Propietari: responsable del projecte.
5. **El mapa v8 parlava de notificacions push i del botó d'esborrar «per a les botigues».** Sense push ([041](decisions/041-web-installable-i-avisos-sense-push.md)); el botó es manté per RGPD. Propietari: cap (resolt).
6. **El pla anterior incloïa la data de naixement; la spec 00 (V-04) no.** Mana la spec 00 fins a P-33. Propietari: junta.
7. **Importació final «quan el 05a pugui rebre els mandats»:** a l'aprovació es deia «M05b» amb la numeració del mapa v8; amb la numeració de la sèrie B és el **05a**. Aprovat amb el pla del M01.
8. **La verificació pública amb només dos dígits** pot ser poc útil si un centre vol comprovar que el carnet és de qui el porta; el nom de pila ho resoldria però exposa més dades. Propietari: junta.
9. **Concurrència del comptador de números:** una fila bloquejada és simple però serialitza les aprovacions; amb el volum del club no és cap problema. Propietari: informàtica.
10. **La spec 00 diu «llista tancada dels 8 rols».** Afegir Junta, Resp. comunicació i Resp. botiga demana una decisió nova i actualitzar la spec 00. Propietari: junta (P-04).

<a id="M01-14-aprovar"></a>
## M01-14 Què cal aprovar abans de començar

**Aprovat el 27/10/2026** pel responsable del projecte, amb aquestes respostes:

| # | Punt | Resposta |
|---|---|---|
| 1 | Aquest pla del M01 | Aprovat. Estat «aprovat» a la [taula d'estat](#estat) |
| 2 | Interfície | Plantilles de Django i HTMX servides des del VPS, HTMX sense CDN: [046](decisions/046-interficie-django-htmx-servida-des-del-vps.md), acceptada |
| 3 | Spec del M01 | Aquest fitxer és la font única ([047](decisions/047-planning-font-unica-de-l-especificacio.md)); CLAUDE.md hi apunta |
| 4 | S-M01-01 | La secretaria escriu l'import a mà fins que la junta decideixi; la diferència (55 €) és la proposta més simple (RN-M01-15) |
| 5 | S-M01-03 | Any natural com a supòsit; el venciment queda pendent del tresorer (P-29) |
| 6 | S-M01-16 | Es treballa amb un fitxer inventat; la mostra real anonimitzada és pendent del tresorer (Q-23) |
| 7 | Llavor de l'avatar | Es desa en l'alta (RN-M01-30) |
| 8 | Mandats SEPA de Cluber | Risc nou a [M01-13](#M01-13-riscos); propietari, el tresorer |
| 9 | Importació final | Depèn del **05a** (dubte 7) |

**Continua obert, sense bloquejar el començament:** la matriu dels 13 rols de [M01-4](#M01-4-rols) (junta, P-04). Mentre no es validi, els permisos són configurables i les proves per cel·la es regeneren (risc de [M01-13](#M01-13-riscos)).

---

<a id="M04"></a>
# Mòdul 04 — Tresoreria, part mínima

**Estat: aprovat** pel responsable del projecte el 27/10/2026 ([M04-14](#M04-14-aprovar)).

**Fonts integrades:** la [spec 04](arxiu/spec-04-tresoreria-v2-2026-10-27.md) v2 (aprovada amb canvis el 27/10/2026), les decisions [013](decisions/013-imputacio-comissions.md), [027](decisions/027-estructura-basica-de-carrec-i-pagament.md), [042](decisions/042-proveidors-substituits-pel-requisit-ue.md) a [045](decisions/045-correccio-transferencia-conciliada-per-error.md), l'arquitectura §4 i §9.1 i la [spec 00](../specs/00-base-comuna/spec.md) (RN-60 a RN-76, HU-21). La spec 04 v2 és a l'arxiu des de l'aprovació d'aquesta secció ([047](decisions/047-planning-font-unica-de-l-especificacio.md)).

**Identificadors.** Es mantenen els de la spec 04 (HU-T, CA-T, RN-T, LT, VT, QT) perquè ja els citen la 045 i `pendents.md`. Els nous continuen la numeració (RN-T24, CA-T16…). Els requisits d'experiència de pagament de l'annex D de la spec 04 passen al [M05b](#M05b-5-processos).

<a id="M04-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Que el tresorer sàpiga en tot moment quant hi ha a cada compte, de quin departament és cada euro, què ha arribat al banc i que cap moviment s'ha modificat ni esborrat. És la base dels pagaments (05a i 05b) i del marge (09). |
| **Processos que cobreix** | P-M04-A Cobrament confirmat → ingrés · P-M04-B Devolució o retorn · P-M04-C Anul·lar un moviment · P-M04-D Traspàs i arqueig · P-M04-E Conciliar l'extracte · P-M04-F Liquidació del proveïdor o de la remesa · P-M04-G Exportar per a la gestoria |
| **Tasques** | 19 (T-M04-01 a T-M04-19) |
| **Què el bloqueja** | T-M04-13 (liquidacions) espera el format de PaynoPain (P-45 punt 9) [A verificar]. La conciliació real espera el format de l'extracte [A verificar: banc]; es construeix amb el supòsit CSV |
| **Què cal aprovar** | Aprovat el 27/10/2026 amb RN-T24 i RN-T25 ([M04-14](#M04-14-aprovar)). Els departaments [A validar: junta] no bloquegen |

<a id="M04-1-intencio"></a>
## M04-1 Intenció, abast i fora d'abast

**Per què.** Avui els diners es porten en diverses eines que es creuen a mà. Cluber cobra les quotes pel seu compte i ingressa al club l'import menys un percentatge. Quan es deixi Cluber, el club cobrarà directament i haurà de quadrar què ha cobrat, què ha pagat de comissions i què ha arribat al banc.

**Resultat esperat.** Que el tresorer sàpiga, en tot moment i sense creuar fulls de càlcul:
1. quant hi ha a cada compte (banc, caixa i trànsit de cada proveïdor o remesa);
2. de quin departament és cada euro que entra o surt;
3. quins cobraments ja han arribat al banc i quins no;
4. que cap moviment s'ha modificat ni esborrat.

**Com sabrem que funciona.**
- El saldo de cada compte surt dels moviments i quadra amb l'extracte després de conciliar.
- Cap moviment es pot modificar ni esborrar, ni des de l'aplicació ni amb una consulta directa.
- Cada cobrament confirmat té exactament un ingrés, al departament del seu càrrec.
- La llista «a revisar» queda buida després de cada conciliació, o cada element hi té motiu.

**Dins de l'abast** (arquitectura §9.1):
- Comptes de tresoreria: bancari, caixa i trànsit (un per proveïdor de cobrament i un per a les remeses SEPA, RN-T24).
- Moviments immutables: ingressos automàtics, comissions, devolucions i retorns com a moviments nous, traspassos, arqueig i contramoviments.
- Departaments i centres de cost.
- Conciliació de l'extracte (importat per la 00, HU-21): transferències amb referència, liquidacions del proveïdor i de les remeses, traspassos; exclusions i llista «a revisar».
- Exportació CSV per a la gestoria.

**Fora d'abast.**
- **09** (fase 2): marge per activitat, despeses amb factura, ajuts i justificació, facturació i Verifactu (P-02, P-47), tancament de període, pressupostos.
- Integració amb el proveïdor, notificacions, mandats, remeses, pantalles de pagament (05a i 05b). La 04 només ofereix els serveis de [M04-8](#M04-8-serveis).
- Registre manual de cobraments: bloquejat per P-12 (RN-72 de la 00).
- Connexió directa amb el banc (PSD2 o agregadors): l'extracte entra en fitxer.
- Despeses que no són comissions: s'exclouen amb motiu fins al 09.
- Monedes que no siguin l'euro.

<a id="M04-2-dependencies"></a>
## M04-2 Dependències

**De què depèn.**
| Mòdul | Què en fa servir la 04 |
|---|---|
| 00 | Càrrec, pagament i departament (estructura bàsica, RN-60 a RN-76; 027); importació de l'extracte bancari (HU-21, RN-92 a RN-101); registre d'activitat; permisos; TOTP |
| 01 | Quotes com a càrrecs; número de soci per al concepte dels moviments (`members.get_member_summary`) |

**Què depèn de la 04.**
| Mòdul | Què necessita |
|---|---|
| 01 | Referència de transferència per mostrar com pagar una quota; estat de la quota (T11) |
| 05a | Crear el compte de trànsit del proveïdor quan es configura (`treasury.create_transit_account`) |
| 05b | Registrar ingressos, comissions, devolucions, retorns i liquidacions; referència de transferència |
| 09 | Moviments, comptes i departaments com a base del marge i de les despeses |
| 08 | Saldos i moviments (només lectura) |

<a id="M04-3-capacitats"></a>
## M04-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | Pantalla (proposta) |
|---|---|---|---|
| C1 | Comptes i saldos calculats | Tresorer | `/gestio/tresoreria` |
| C2 | Moviments automàtics (ingrés, comissió, devolució, retorn) | Sistema, cridat per la 05b o per la conciliació | `/gestio/tresoreria/moviments` |
| C3 | Anul·lar un moviment amb contramoviment | Tresorer | Fitxa del moviment |
| C4 | Traspassos entre comptes propis i arqueig de caixa | Tresorer | `/gestio/tresoreria/traspassos`, `/gestio/tresoreria/arqueig` |
| C5 | Conciliar l'extracte (transferències, liquidacions, traspassos) i desfer-ho | Tresorer | `/gestio/tresoreria/conciliacio` |
| C6 | Excloure línies i resoldre la llista «a revisar» | Tresorer | `/gestio/tresoreria/revisar` |
| C7 | Departaments i centres de cost | Administrador (tresorer [A validar]) | `/gestio/tresoreria/departaments` |
| C8 | Filtrar i exportar moviments en CSV | Tresorer | `/gestio/tresoreria/moviments` |

**Històries d'usuari** (les de la spec 04, amb el mateix número)
- **HU-T01.** Com a tresorer, vull tenir els comptes del club a la plataforma (cada compte bancari, la caixa i un compte de trànsit per a cada proveïdor), per veure el saldo de cadascun.
- **HU-T02.** Com a tresorer, vull que el saldo el calculi la plataforma a partir dels moviments, per no haver-lo de quadrar a mà.
- **HU-T03.** Com a tresorer, vull que cada cobrament confirmat generi sol el seu ingrés al compte i al departament correctes.
- **HU-T04.** Com a tresorer, vull que cada comissió es registri com a despesa del departament que toca (013).
- **HU-T05.** Com a tresorer, vull que una devolució o un rebut retornat generi un moviment nou de signe contrari, sense tocar l'original.
- **HU-T06.** Com a tresorer, vull anul·lar un moviment erroni amb un motiu, de manera que en quedi rastre.
- **HU-T07.** Com a tresorer, vull registrar un traspàs entre comptes propis (per exemple, l'efectiu que ingresso al banc).
- **HU-T08.** Com a tresorer, vull registrar l'arqueig de la caixa i veure la diferència amb el saldo calculat.
- **HU-T09.** Com a tresorer, vull que la plataforma em proposi a quin pagament o liquidació correspon cada línia de l'extracte.
- **HU-T10.** Com a tresorer, vull que en confirmar una transferència amb referència i import correctes el càrrec passi a pagat i es creï l'ingrés.
- **HU-T11.** Com a tresorer, vull casar l'abonament agrupat del proveïdor (o de la remesa) amb els cobraments que conté.
- **HU-T12.** Com a tresorer, vull excloure amb motiu les línies que no són de l'abast mínim.
- **HU-T13.** Com a tresorer, vull una llista dels pagaments i les línies «a revisar».
- **HU-T14.** Com a tresorer, vull que els departaments puguin tenir centres de cost (per exemple, «General / Quotes de socis»).
- **HU-T15.** Com a tresorer, vull filtrar els moviments per compte, departament, centre de cost i període, i exportar-los en CSV per a la gestoria.

<a id="M04-4-rols"></a>
## M04-4 Rols i permisos

Llegenda com a [M01-4](#M01-4-rols). Totes les accions de gestió es fan amb el **compte d'administrador** amb TOTP (015, 018); T12 es fa amb el compte personal o, per a un convidat, amb l'enllaç de convidat.

| # | Acció | Visitant | Part. no soci | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Resp. comunicació | Dept. Història | Junta | Administrador | Resp. botiga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Veure comptes, saldos i moviments | — | — | — | — | — | — | — | Sí | — | — | [A validar] (P-04) | Sí | — |
| T2 | Crear i desactivar comptes | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| T3 | Mantenir departaments i centres de cost | — | — | — | — | — | — | — | [A validar] | — | — | — | Sí | — |
| T4 | Conciliar i desfer una conciliació | — | — | — | — | — | — | — | Sí | — | — | — | [A validar] | — |
| T5 | Anul·lar un moviment amb motiu | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| T6 | Registrar un traspàs | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| T7 | Registrar un arqueig | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| T8 | Excloure una línia de l'extracte | — | — | — | — | — | — | — | Sí | — | — | — | — | — |
| T9 | Exportar moviments en CSV | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| T10 | Veure la llista «a revisar» | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| T11 | Veure l'estat de les quotes sense imports de tresoreria | — | — | — | — | Consulta | — | — | Sí | — | — | — | Sí | — |
| T12 | Veure els seus càrrecs, pagaments i rebuts | — | Propi (enllaç de convidat) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |

**Per objecte.**
- El tresorer veu les dades de les persones que calen per cobrar i conciliar (nom, número de soci, concepte i import), no el perfil sencer (00, §2.5).
- Les línies de l'extracte poden portar noms de persones que no són del club (qui fa una transferència en nom d'un altre): només es veuen a la pantalla de conciliació.
- **Un sol tresorer**, tractat com una sola persona. Cap acció necessita doble aprovació (P-48, opcional i futura).
- Cap endpoint de tresoreria és públic.

<a id="M04-5-processos"></a>
## M04-5 Processos pas per pas

**Wireframes existents:** `admin.html` té l'entrada «Tresoreria» a la barra lateral (rols `admin tresorer`) i el patró de taula amb cerca, filtres i imports alineats (`#participants`, `#resum-economic`). **Falten** wireframes de: comptes i saldos, llistat de moviments, fitxa de moviment amb anul·lació, conciliació (línia ↔ proposta), llista «a revisar», traspàs, arqueig i departaments (tasca T-M04-15).

### P-M04-A Cobrament confirmat → ingrés (HU-T03, HU-T04)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | 05b (notificació verificada) o la conciliació d'una transferència | El càrrec passa a «pagat» (RN-71 de la 00) |
| 2 | Sistema | Crida `treasury.record_income(payment)`: un ingrés al compte de RN-T08, amb el departament i el centre de cost del càrrec. Si ja n'hi ha un, no en crea cap (RN-T09) |
| 3 | Sistema | Si hi ha comissió coneguda, `treasury.record_fee(...)` crea la despesa al departament de la 013 (RN-T10). Si la comissió només arriba amb la liquidació, es registra en conciliar-la (P-M04-F) |
| 4 | Sistema | Tot queda al registre d'activitat (RN-T13) |

### P-M04-B Devolució o retorn (HU-T05)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | 05b | Una devolució (iniciada pel club) o un retorn (rebut retornat o contracàrrec) crida `record_refund` o `record_return` |
| 2 | Sistema | Crea una sortida nova pel mateix compte, departament i centre de cost; l'ingrés original no canvia. Si hi ha comissió de retorn, una despesa més (013). La suma de devolucions no supera l'import cobrat (RN-T11) |
| 3 | Tresorer | Quan arriba la línia de l'extracte, la casa amb aquesta sortida (P-M04-E) |

### P-M04-C Anul·lar un moviment (HU-T06)
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Tresorer | Obre el moviment i tria «Anul·lar», amb motiu obligatori | `/gestio/tresoreria/moviments/{id}` |
| 2 | Sistema | Si és un ingrés de cobrament, ho rebutja: es fa amb una devolució (05b) o desfent la conciliació (CA-T06.2) | — |
| 3 | Sistema | Crea un contramoviment de sentit contrari i mateix import, compte, departament i centre de cost, enllaçat a l'original. L'original es mostra com a anul·lat (RN-T25) | — |

### P-M04-D Traspàs i arqueig (HU-T07, HU-T08)
- **Traspàs:** el tresorer tria compte d'origen, compte de destinació, import, data i concepte. Es creen dues potes enllaçades sense departament (RN-T12). Quan arriba la línia de l'extracte, es casa amb la pota d'entrada al banc.
- **Arqueig:** el tresorer escriu l'import comptat de la caixa. La plataforma mostra el saldo calculat i la diferència. No es crea cap moviment sol; si el tresorer ho decideix, crea un ajust amb motiu a «General / Ajustos de caixa» (VT-06).

### P-M04-E Conciliar l'extracte (HU-T09, HU-T10, HU-T12, HU-T13)
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Tresorer | Importa l'extracte (00, HU-21: previsualització, validació, confirmació) | `/gestio/importacions/extracte` (00) |
| 2 | Sistema | Dona estat a cada línia (RN-T15) i proposa: referència vàlida i import exacte → «proposada»; qualsevol altra coincidència → «a revisar» (RN-T18) | `/gestio/tresoreria/conciliacio` |
| 3 | Tresorer | Confirma la proposta, casa a mà una línia amb un o més càrrecs, moviments o una liquidació (suma exacta, RN-T17), o l'exclou amb motiu | `/gestio/tresoreria/conciliacio` |
| 4 | Sistema | En confirmar una transferència: càrrec «pagat», pagament amb mètode transferència i ingrés al banc (CA-T10.1); `members.on_fee_paid` si és una quota | — |
| 5 | Tresorer | Si s'ha equivocat de càrrec: correcció de la 045 (pagat → pendent, CA-T10.5) | Fitxa de la conciliació |
| 6 | Tresorer | Resol la llista «a revisar» | `/gestio/tresoreria/revisar` |

### P-M04-F Liquidació del proveïdor o de la remesa (HU-T11)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | 05b | Registra la liquidació amb `record_settlement` (notificació o fitxer del proveïdor [A verificar: PaynoPain, P-45 punt 9]) o, per a una remesa SEPA, amb els rebuts que conté (RN-T24) |
| 2 | Sistema | Quan arriba la línia del banc amb l'import net, la proposa |
| 3 | Tresorer | Veu el brut, les comissions i el net. Si el proveïdor no detalla la comissió de cada cobrament, veu el repartiment proporcional (VT-05) abans de confirmar |
| 4 | Sistema | En confirmar: traspàs del compte de trànsit al banc pel net i comissions per departament. Si la liquidació conté cobraments que no són a la plataforma, queda «a revisar» (CA-T11.2) |

### P-M04-G Exportar per a la gestoria (HU-T15)
El tresorer filtra per període, compte, departament o centre de cost i descarrega un CSV amb data, compte, concepte, departament, centre de cost, entrada, sortida i referència, en euros amb dos decimals. Cap dada personal més enllà del concepte (RNF-T4).

<a id="M04-6-entitats"></a>
## M04-6 Entitats i camps

App Django `treasury` (nova). Noms de codi en anglès. Cap camp d'IBAN complet ni de targeta (RN-70 de la 00; l'excepció de la [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md) viu al 05a, mai a la 04).

### TreasuryAccount (compte de tresoreria)
| Camp | Tipus | Restriccions |
|---|---|---|
| `name` | `CharField(80)` | Únic |
| `kind` | `bank`, `cash`, `transit` | — |
| `provider_code` | `CharField(30)` null | Obligatori i únic si `kind = transit` (per exemple `card_provider`, `sepa_remittance`) |
| `last4` | `CharField(4)` null | Només `bank`; mai l'IBAN complet |
| `active` | `BooleanField` | No s'esborra si té moviments (RN-T04) |

### CostCentre (centre de cost)
`department` (FK al departament de la 00, PROTECT), `name` (`CharField(80)`), `active`. Únic `(department, name)`. Dades inicials: «General / Quotes de socis», «General / Llicències» (provisional, VT-04), «General / Ajustos de caixa» (VT-06).

### Movement (moviment)
| Camp | Tipus | Restriccions |
|---|---|---|
| `account` | FK TreasuryAccount (PROTECT) | Compte actiu en crear-lo |
| `direction` | `in`, `out` | — |
| `amount_cents` | `PositiveBigIntegerField` | > 0 (`CHECK`) |
| `value_date` | `DateField` | Data de valor |
| `recorded_at` | `DateTimeField` | Data de registre |
| `kind` | `income`, `fee`, `refund`, `return`, `transfer`, `cash_adjustment`, `reversal` | RN-T06 |
| `concept` | `CharField(140)` | Sense noms de persones; número de soci o referència (RNF-T4) |
| `department` | FK departament (00) null | Obligatori excepte `transfer` (`CHECK`) |
| `cost_centre` | FK CostCentre null | Del mateix departament |
| `payment` | FK pagament (00) null | — |
| `settlement` | FK ProviderSettlement null | — |
| `linked_movement` | FK self null | Altra pota del traspàs |
| `reverses` | `OneToOneField(self)` null | Només per a `reversal`: el moviment que anul·la. Un moviment només s'anul·la una vegada |
| `reason` | `TextField` | Obligatori per a `reversal` i `cash_adjustment` |
| `recorded_by` | FK compte null | Null = sistema |
**Restriccions i índexs:** únic parcial `(payment) WHERE kind = 'income'` (RN-T09); índexs `(account, value_date)` i `(department, cost_centre, value_date)`. **Només INSERT:** activador de PostgreSQL que rebutja UPDATE i DELETE, i permisos de l'usuari de l'aplicació sense UPDATE ni DELETE (RNF-T2).

### ProviderSettlement (liquidació) i SettlementItem
- `ProviderSettlement`: `provider_code`, `external_id` (únic per proveïdor), `settled_on`, `gross_cents`, `fees_cents`, `net_cents` (`CHECK net = gross − fees`), `status` (`received`, `reconciled`, `to_review`), `source` (`notification`, `file`, `manual`, `remittance`).
- `SettlementItem`: `settlement`, `payment` (únic: un pagament només és en una liquidació), `amount_cents`, `fee_cents` null (si el proveïdor el detalla).

### Reconciliation i StatementLineState (conciliació)
- `Reconciliation` (només INSERT): `statement_line` (FK línia d'importació de la 00), `matched_charges`, `matched_movements` (M2M), `settlement` null, `confirmed_by`, `confirmed_at`. Restricció de servei: suma dels objectes = import de la línia.
- `ReconciliationUndo` (només INSERT): `reconciliation` (OneToOne), `reason`, `undone_by`, `undone_at`. Una conciliació és activa si no té desfeta.
- `StatementLineState` (de la 04, mutable amb registre): `statement_line` (OneToOne), `status` (`pending`, `proposed`, `reconciled`, `excluded`), `to_review` (bool) i `review_reason`, `exclusion_reason`, `active_reconciliation` (FK null). La línia de la 00 no es toca mai (RN-T14).

### CashCount (arqueig)
`account` (caixa), `counted_on`, `counted_cents`, `computed_cents`, `difference_cents` (pot ser negatiu: `BigIntegerField`), `recorded_by`, `adjustment` (FK Movement null). Només INSERT.

### TransferReference (referència de transferència)
`charge` (OneToOne), `reference` (`CharField(20)`, únic), `created_at`. No canvia mai.

### Ampliacions de la 00 (sense canviar-ne les regles, 027)
- Al càrrec: `cost_centre` (FK null).
- Al pagament: l'ingrés que ha generat s'obté per la relació inversa de `Movement.payment`; no cal camp nou.

**Migracions:** reversibles; dades inicials (comptes «Caixa» i «Banc principal», centres de cost) en migracions de dades; l'activador i els permisos en una migració pròpia amb prova.

<a id="M04-7-regles"></a>
## M04-7 Regles de negoci i càlculs

Regles de la 00 que la 04 no canvia (027, RN-76): RN-60 a RN-73.

| ID | Regla | Font |
|---|---|---|
| RN-T01 | Tres tipus de compte: bancari, caixa i trànsit (un per proveïdor de cobrament) | ARQ §4.1; 027 |
| RN-T02 | El saldo es calcula sempre a partir dels moviments; no es desa com a camp editable | RN-61 |
| RN-T03 | Cap compte guarda l'IBAN complet. L'IBAN que es mostra per pagar per transferència és configuració (`CLUB_IBAN_TRANSFERENCIES`) | RN-70; ARQ §5 |
| RN-T04 | Un compte amb moviments no s'esborra: es desactiva | RN-61 |
| RN-T05 | Un moviment té compte, sentit, import enter positiu en cèntims, data de valor i de registre, tipus, concepte, departament i centre de cost (excepte traspassos) i origen | RN-60, RN-62 |
| RN-T06 | Tipus: ingrés de cobrament, comissió, devolució, retorn, traspàs (dues potes), ajust d'arqueig i contramoviment | ARQ §4.1 a §4.7 |
| RN-T07 | Els moviments no es modifiquen ni s'esborren; una correcció és un contramoviment amb motiu | CLAUDE.md; RN-61 |
| RN-T08 | Compte de l'ingrés segons el mètode: targeta i Bizum → trànsit del proveïdor; domiciliació → trànsit de les remeses SEPA (RN-T24); transferència → bancari; manual → caixa o bancari (quan es resolgui P-12) | ARQ §4.1, §4.6, §4.7 |
| RN-T09 | Cada pagament genera com a màxim un ingrés de cobrament (unicitat a la base de dades) | ARQ §4.2, punt 5 |
| RN-T10 | L'ingrés porta el departament i el centre de cost del càrrec. Comissió: quotes → «General / Quotes de socis»; inscripcions → activitat i departament de l'activitat; llicències → Q-19 (provisional «General / Llicències») | 013; RN-63 a RN-65 |
| RN-T11 | Devolucions i retorns són sortides noves; la comissió no es recupera; la suma de devolucions no supera l'import cobrat | RN-73; 013 |
| RN-T12 | Els traspassos entre comptes propis no són ingrés ni despesa i no porten departament | Spec 04 |
| RN-T13 | Cada moviment, anul·lació, conciliació, exclusió i arqueig va al registre d'activitat | RN-50 |
| RN-T14 | La 00 importa les línies de l'extracte; la 04 les casa i no n'altera les dades | 00, HU-21 |
| RN-T15 | Estats d'una línia: pendent → proposada → conciliada; pendent → exclosa (amb motiu). «A revisar» és una marca | Spec 04 |
| RN-T16 | Només el tresorer confirma una conciliació; la plataforma mai concilia sola | ARQ §4.6; RN-71 |
| RN-T17 | Una línia es concilia una sola vegada, amb un o més càrrecs, moviments o una liquidació, si la suma coincideix exactament | Spec 04 |
| RN-T17b | Sense saldo a favor ni pagaments parcials: l'excés d'una transferència es retorna pel banc i es registra com a devolució; un pagament de menys queda «a revisar» | QT-05 |
| RN-T18 | Una transferència només posa un càrrec en «pagat» si coincideixen referència i import | ARQ §4.6 |
| RN-T19 | Una conciliació que ha passat un càrrec a «pagat» només es desfà amb la transició «pagat → pendent» de la 045 (només transferències, amb motiu) | 045 |
| RN-T20 | Referència de transferència: una per càrrec, única, prefix `TRANSFER_REFERENCE_PREFIX` i caràcter de control (VT-03). Es genera la primera vegada que es demana i no canvia | ARQ §4.6 |
| RN-T21 | **[A verificar: PaynoPain, P-45 punt 9]** Una liquidació té brut, comissions, net, data i la llista de cobraments. Si el proveïdor no en dona el detall, el tresorer casa la línia del banc amb els cobraments del període | 043; `integracio-paylands.md` §7 |
| RN-T22 | Dos nivells: departament i centre de cost (VT-02) | 013; Q-17 |
| RN-T23 | La llista de departaments i centres de cost la fixa la junta; d'inici només hi ha les de CA-T14.1 | RN-74 |
| **RN-T24** | **Nova, aprovada.** Amb la domiciliació pròpia ([044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)), el «proveïdor» de les domiciliacions és el servei de remeses del banc. Té el seu compte de trànsit («Remeses SEPA») i cada abonament d'una remesa es tracta com una liquidació (RN-T21) amb els rebuts que conté. Si el banc abona rebut a rebut o la remesa sencera és [A verificar: banc, P-45 punt 5] | 043 (e); 044 |
| **RN-T25** | **Nova, aprovada.** «Anul·lat» d'un moviment és un estat **derivat**: un moviment està anul·lat si té un contramoviment que el referencia. Així no cal cap UPDATE a la taula de moviments | RNF-T2; dubte 1 de [M04-13](#M04-13-riscos) |

**Valors proposats (spec 04, §10.1).** VT-01 comptes inicials «Caixa» i «Banc principal»; VT-02 dos nivells; VT-03 referència `PREFIX-XXXXX-C` amb cinc caràcters de l'alfabet sense 0, O, 1 ni I i un caràcter de control (Luhn mod N); VT-04 «General / Llicències» provisional; VT-05 repartiment proporcional i el cèntim que sobra al cobrament més gran; VT-06 ajust d'arqueig a «General / Ajustos de caixa» amb motiu.

**Exemples numèrics**
- **Ingrés i saldo (RN-T02, RN-T08):** dues quotes pagades amb targeta, 9000 i 3500 cèntims → entrades al trànsit del proveïdor; saldo del trànsit = **12.500 cèntims (125,00 €)** fins que arriba la liquidació.
- **Liquidació amb repartiment (VT-05, LT9):** brut 12.500, net 12.380 → comissions 120 cèntims sense detall. Part de la quota de 9000: 120 × 9000 / 12.500 = 86,4 → 86; part de la de 3500: 120 × 3500 / 12.500 = 33,6 → 33. Sumen 119; el cèntim que sobra va al cobrament més gran → **87 i 33**. Les dues comissions van a «General / Quotes de socis». En confirmar: traspàs de 12.380 del trànsit al banc; saldo del trànsit = 12.500 − 12.380 − 120 = **0**.
- **Remesa (RN-T24):** 130 rebuts, 90 × 3500 + 40 × 9000 = **675.000 cèntims (6.750,00 €)** entren al trànsit «Remeses SEPA». L'abonament del banc es casa amb la remesa; la comissió per rebut és [A verificar: banc].
- **Transferència (RN-T17b, RN-T18):** quota de 9000 amb la referència i 9000 → «proposada». Amb 9500 → «a revisar»; el tresorer concilia els 9000 i retorna 500 pel banc (devolució amb motiu). Una família paga 3500 + 9000 amb una línia de 12.500 → una conciliació amb dos càrrecs.
- **Arqueig (VT-06):** saldo calculat 12.000, comptat 11.950 → diferència **−50**; si el tresorer crea l'ajust, sortida de 50 a «General / Ajustos de caixa».
- **Devolucions (RN-T11):** pagament de 12.000; devolució de 4000 i després de 8000 → acceptades (suma 12.000); una tercera de 1 → rebutjada.

<a id="M04-8-serveis"></a>
## M04-8 Serveis i interfícies (contracte)

Cap altra app escriu als models de la 04. Noms de codi en anglès (entre parèntesis, el nom de la spec 04). Tots els serveis que escriuen són idempotents o rebutgen la repetició, i deixen registre.

**Ofereix**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `treasury.record_income(payment)` (`registrar_cobrament`) | pagament amb el càrrec «pagat» | moviment d'ingrés (o l'existent, sense duplicar) | `ChargeNotPaid`, `BrowserOriginRejected` | 05b; la mateixa 04 en conciliar |
| `treasury.record_fee(payment_or_settlement, amount_cents)` (`registrar_comissio`) | pagament o liquidació, import | moviment de comissió | `InvalidAmount` | 05b; 04 |
| `treasury.record_refund(payment, amount_cents, reason)` (`registrar_devolucio`) | pagament, import, motiu | moviment de devolució | `RefundExceedsPaid` | 05b |
| `treasury.record_return(payment, fee_cents=None)` (`registrar_retorn`) | pagament, comissió de retorn opcional | moviment de retorn (i comissió) | `AlreadyReturned` | 05b |
| `treasury.transfer_reference(charge)` (`referencia_transferencia`) | càrrec | referència (es crea si no n'hi ha) | — | 01, 05b |
| `treasury.record_settlement(provider_code, data)` (`registrar_liquidacio`) | proveïdor, identificador extern, brut, comissions, net, llista de pagaments | liquidació | `DuplicateSettlement`, `UnknownPayment` (→ «a revisar») | 05b |
| `treasury.create_transit_account(provider_code, name)` | proveïdor | compte de trànsit (o l'existent) | — | 05a |
| `treasury.balance(account, on=date)`, `treasury.movements(filters)` | — | només lectura | — | 08; 01 (rebuts) |

**Consumeix**
| Servei | Mòdul | Per a què |
|---|---|---|
| `charges.mark_paid(charge, payment, origin="reconciliation")`, `charges.revert_paid_transfer(charge, reason)` (045) | 00 | Conciliar transferències i corregir-les |
| `imports.statement_lines(batch)` | 00 | Llegir les línies de l'extracte |
| `members.get_member_summary(person)`, `members.on_fee_paid(annual_fee_id)` | 01 | Concepte amb número de soci; activar el soci en conciliar una quota |
| `audit.record(...)`, `permissions.require(...)` | 00 | Registre i permisos |

**Rutes (administració, ruta discreta `ADMIN_URL_PATH`):** `/gestio/tresoreria`, `/gestio/tresoreria/moviments`, `/gestio/tresoreria/moviments/{id}`, `/gestio/tresoreria/conciliacio`, `/gestio/tresoreria/revisar`, `/gestio/tresoreria/traspassos`, `/gestio/tresoreria/arqueig`, `/gestio/tresoreria/departaments`. Cap ruta pública.

<a id="M04-9-criteris"></a>
## M04-9 Criteris d'acceptació i casos límit

**Comptes i saldos**
- **CA-T01.1** Instal·lació nova → existeixen «Caixa» i «Banc principal».
- **CA-T01.2** Cap camp de compte guarda un IBAN complet; com a molt, els quatre darrers dígits.
- **CA-T01.3** Un compte amb moviments no es pot esborrar; desactivat, no admet moviments nous.
- **CA-T02.1** El saldo a una data és la suma d'entrades menys sortides amb data de valor fins a aquella data; cap pantalla permet escriure'l.
- **CA-T02.2** Amb totes les liquidacions conciliades, el saldo d'un trànsit és la suma dels cobraments encara no liquidats.

**Ingrés, comissions, devolucions**
- **CA-T03.1** Càrrec «pagat» + `record_income` → un sol ingrés amb l'import del pagament, el departament i el centre de cost del càrrec, al compte de RN-T08.
- **CA-T03.2** Una segona crida per al mateix pagament no crea cap moviment i queda al registre com a repetició.
- **CA-T03.3** Càrrec que no és «pagat» → es rebutja.
- **CA-T03.4** Una petició del navegador no pot crear cap ingrés (RN-71).
- **CA-T04.1** Comissió d'una quota → sortida del trànsit a «General / Quotes de socis».
- **CA-T04.2** Comissió d'una inscripció → departament i activitat del càrrec.
- **CA-T04.3** Comissió d'una llicència → «General / Llicències», marcada provisional (VT-04).
- **CA-T04.4** Liquidació sense detall de comissions **[A verificar: proveïdor]** → repartiment proporcional (VT-05) visible abans de confirmar.
- **CA-T05.1** Devolució total o parcial → sortida nova; l'ingrés original no canvia.
- **CA-T05.2** La comissió original no es retorna.
- **CA-T05.3** Rebut retornat → sortida de l'import i, si n'hi ha, comissió de retorn al mateix departament.
- **CA-T05.4** Suma de devolucions superior a l'import cobrat → es rebutja.

**Anul·lació, traspàs, arqueig**
- **CA-T06.1** Anul·lar amb motiu → contramoviment enllaçat; l'original es mostra anul·lat i no desapareix de cap llistat.
- **CA-T06.2** Anul·lar un ingrés de cobrament des de la tresoreria → es rebutja.
- **CA-T06.3** Modificar o esborrar un moviment, a l'aplicació o amb una consulta directa → es rebutja.
- **CA-T07.1** Traspàs → dues potes enllaçades, mateix import, sense departament.
- **CA-T07.2** La línia de l'ingrés en efectiu es casa amb la pota d'entrada al banc.
- **CA-T08.1** Arqueig amb diferència → es mostra; cap moviment automàtic; ajust opcional amb motiu.

**Conciliació**
- **CA-T09.1** Cada línia d'un extracte confirmat té un estat de RN-T15.
- **CA-T09.2** Referència vàlida i import exacte → «proposada».
- **CA-T09.3** Referència vàlida amb import diferent, o sense referència amb un sol càrrec del mateix import → «a revisar», sense proposta.
- **CA-T10.1** Confirmar una transferència → càrrec «pagat», pagament per transferència, ingrés al banc i registre de qui ho confirma.
- **CA-T10.2** Una línia per a diversos càrrecs només es confirma si la suma és exacta.
- **CA-T10.3** Una línia ja conciliada no es pot fer servir per a un altre càrrec.
- **CA-T10.4** Desfer amb motiu una conciliació que no ha canviat cap càrrec → la línia torna a «pendent».
- **CA-T10.5** Transferència conciliada amb el càrrec equivocat → «pagat → pendent» amb motiu, pagament anul·lat, contramoviment de l'ingrés, línia a «pendent», tot al registre (045).
- **CA-T10.6** «Pagat → pendent» d'un càrrec pagat amb targeta, Bizum o domiciliació → es rebutja.
- **CA-T11.1** Liquidació amb la línia del banc pel net → proposta; en confirmar, traspàs del trànsit al banc i comissions.
- **CA-T11.2** Liquidació amb cobraments desconeguts → «a revisar».
- **CA-T12.1** Excloure una línia → motiu obligatori, estat «exclosa», cap moviment.
- **CA-T13.1** La llista «a revisar» mostra pagaments i línies amb el motiu; buida, diu «No hi ha res a revisar».

**Departaments i exportació**
- **CA-T14.1** Instal·lació nova → departament «General» amb «Quotes de socis», «Llicències» (provisional) i «Ajustos de caixa».
- **CA-T14.2** Un centre de cost desactivat no es pot triar per a càrrecs ni moviments nous.
- **CA-T15.1** El CSV porta data, compte, concepte, departament, centre de cost, entrada, sortida i referència, en euros amb dos decimals, i cap dada personal més enllà del concepte.

**Nous**
- **CA-T16.1** Donat una remesa SEPA registrada amb 130 rebuts, quan arriba l'abonament del banc per l'import de la remesa, llavors es proposa casar-lo amb la liquidació de la remesa i, en confirmar-ho, es crea el traspàs del trànsit «Remeses SEPA» al banc (RN-T24).
- **CA-T17.1** Donat un moviment amb contramoviment, quan es consulta, llavors es mostra com a anul·lat sense que la fila original hagi canviat (RN-T25); un segon intent d'anul·lar-lo es rebutja.

**Casos límit (spec 04, §7)**
| # | Cas | Comportament |
|---|---|---|
| LT1 | Confirmació repetida del proveïdor | Un sol ingrés |
| LT2 | Transferència sense referència | «A revisar»; el tresorer la casa a mà |
| LT3 | Transferència de més | «A revisar»; es concilia el càrrec i l'excés es retorna pel banc |
| LT4 | Transferència de menys | «A revisar»; no es concilia fins que una segona transferència completi l'import exacte, o es retorna |
| LT5 | Una transferència per a dues quotes | Una línia, dos càrrecs |
| LT6 | Transferència d'un càrrec ja pagat amb targeta | «A revisar»; devolució de la transferència pel banc |
| LT7 | Transferència conciliada amb el càrrec equivocat | Correcció de la 045 |
| LT8 | Liquidació amb un cobrament desconegut | «A revisar» |
| LT9 | Comissió que no es reparteix en cèntims exactes | El cèntim que sobra al cobrament més gran |
| LT10 | Departament desactivat amb càrrecs pendents | Els existents el conserven; no es pot triar per a nous |
| LT11 | Línies de despeses amb factura | S'exclouen amb motiu |
| LT12 | Cap extracte importat | «Encara no hi ha cap extracte. Importa'n un des de Tresoreria → Extractes» |
| LT13 | Cap moviment | Saldos a 0,00 € amb un text que explica d'on sortiran |
| LT14 | Esborrat RGPD d'una persona amb moviments | Moviments conservats; persona bloquejada o anonimitzada (028); el concepte no porta el nom |

<a id="M04-10-tasques"></a>
## M04-10 Tasques (per dependències, sense dates)

| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M04-01 | Comptes de tresoreria i dades inicials | S | `apps/treasury/models.py`, migracions | T-M01-09 (càrrec i departament) | CA-T01.x |
| T-M04-02 | Centres de cost i dades inicials «General / …»; centre de cost al càrrec | S | `models.py`, migració de dades | T-M01-09 | CA-T14.x |
| T-M04-03 | Moviment immutable: model, activador i permisos de PostgreSQL, anul·lat derivat | M | `models.py`, migració SQL | T-M04-01, T-M04-02 | CA-T06.3; CA-T17.1; prova de consulta directa |
| T-M04-04 | Saldos i prova de volum amb 50.000 moviments inventats | S | `apps/treasury/balances.py` | T-M04-03 | CA-T02.x; RNF-T7 |
| T-M04-05 | `record_income` idempotent | M | `apps/treasury/services.py` | T-M04-03 | CA-T03.x |
| T-M04-06 | Comissions per tipus de càrrec | S | `services.py` | T-M04-05 | CA-T04.1 a 3 |
| T-M04-07 | Devolucions i retorns | M | `services.py` | T-M04-05, T-M04-06 | CA-T05.x |
| T-M04-08 | Anul·lació amb contramoviment | S | `services.py` | T-M04-03 | CA-T06.1, 2 |
| T-M04-09 | Traspassos i arqueig | M | `services.py`, `models.py` | T-M04-03 | CA-T07.x, CA-T08.1 |
| T-M04-10 | Referència de transferència amb caràcter de control | S | `apps/treasury/references.py` | T-M01-09 | RN-T20; prova de l'algorisme |
| T-M04-11 | Estats de les línies i propostes per referència i import | M | `apps/treasury/reconciliation.py` | T-M04-05, T-M04-10; HU-21 de la 00 | CA-T09.x |
| T-M04-12 | Confirmar i desfer conciliacions (una i diverses) i correcció de la 045 | L | `reconciliation.py` | T-M04-11 | CA-T10.x |
| T-M04-13 | **Obligatòria.** Liquidacions (proveïdor i remeses) i repartiment de comissions | L | `apps/treasury/settlements.py` | T-M04-06, T-M04-11; format de la liquidació [A verificar: P-45 punt 9] | CA-T04.4; CA-T11.x; CA-T16.1 |
| T-M04-14 | Exclusions i llista «a revisar» | S | `reconciliation.py` | T-M04-11 | CA-T12.1; CA-T13.1 |
| T-M04-15 | Wireframes que falten i pantalles de tresoreria amb HTMX (046) | L | `design/wireframes/admin.html`, plantilles | T-M04-04, T-M04-12, T-M04-14 | Proves de permisos (§4) i d'accessibilitat |
| T-M04-16 | Exportació CSV | S | `apps/treasury/exports.py` | T-M04-04 | CA-T15.1 |
| T-M04-17 | Servei `create_transit_account` i contractes de §8 | S | `services.py` | T-M04-05 | Proves de contracte |
| T-M04-18 | Dades de prova inventades (moviments, extractes, liquidacions, remeses) | S | `apps/treasury/fixtures/` | T-M04-13 | Es carreguen amb una ordre |
| T-M04-19 | Guia curta per al tresorer | S | `docs/` | T-M04-15 | Revisada pel tresorer |

T-M04-13 és l'única tasca que depèn del proveïdor; la resta es pot fer abans de saber-lo.

<a id="M04-11-proves"></a>
## M04-11 Pla de proves

- **Unitàries (cobertura completa, CK B1):** saldos; repartiment de comissions amb cèntims que sobren; devolucions totals, parcials i de més; caràcter de control de la referència; càlcul de l'arqueig.
- **Immutabilitat (CK C8):** UPDATE i DELETE directes a moviments, conciliacions i arqueigs fallen; anul·lat derivat.
- **Idempotència (CK C9):** `record_income` repetit, liquidació repetida.
- **Conciliació (CK B9):** referència i import exactes, sense referència, import diferent, diverses línies i càrrecs, línia ja usada, desfer, 045.
- **Permisos (CK B4):** una prova per cel·la de [M04-4](#M04-4-rols) amb els 13 rols; cap ruta pública.
- **Model (CK C9):** revisió automàtica que cap camp de la 04 guarda un IBAN complet ni dades de targeta.
- **Exportació (CK H3):** el CSV no porta dades personals més enllà del concepte.
- **Volum:** 50.000 moviments inventats, saldo en menys d'un segon.
- **Accessibilitat (B8):** imports amb tipografia monoespaiada, alineats a la dreta, amb signe i color; estats amb símbol, text i color.
- **Dades:** només inventades, extractes inclosos (010).

<a id="M04-12-seguretat"></a>
## M04-12 Seguretat i RGPD

- Endpoints només per a comptes d'administrador amb rol tresorer o administrador, amb TOTP.
- Cap IBAN complet ni dades de targeta (l'IBAN del club per a transferències és configuració).
- Immutabilitat a la base de dades, no només a l'aplicació.
- Els fitxers d'extracte no es desen (RN-101 de la 00); les línies normalitzades només es veuen a la conciliació.
- Cap dada de tresoreria al seguiment d'errors (GlitchTip o Bugsink al mateix servidor, 042).
- Concepte dels moviments sense noms (RNF-T4); exportació sense dades personals.
- Esborrat RGPD: moviments conservats i persona bloquejada o anonimitzada segons la 028; terminis [A validar: gestoria, Q-14].
- Dades i còpies dins la UE (035).

<a id="M04-13-riscos"></a>
## M04-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| El format de la liquidació del proveïdor no consta a la documentació pública | Alt per a T-M04-13 | Preguntes P-45 punt 9; mentre tant, casament manual per període (RN-T21) | PaynoPain (via tresorer) |
| Format real de l'extracte desconegut (CSV o Norma 43) | Alt per a la conciliació | Mostra anonimitzada de l'extracte (QT-07, P-45 punt 10) | Banc (via tresorer) |
| El banc abona les remeses rebut a rebut o en total | Mitjà per a RN-T24 | Tots dos casos són liquidacions; es prova amb tots dos | Banc |
| Llista de departaments no fixada (Q-17) | Mitjà | Només «General» d'inici | Junta |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M04-01 | Departaments i centres de cost (QT-03, Q-17) | Dos nivells; només «General» | Junta |
| S-M04-02 | Comptes bancaris del club i banc (QT-06, P-44) | Un compte, «Banc principal» | Tresorer |
| S-M04-03 | Format de l'extracte (QT-07) | CSV amb data, concepte, import i saldo (V-06 de la 00) | Banc |
| S-M04-04 | Caixa en efectiu i periodicitat de l'arqueig (QT-08) | Hi ha caixa; arqueig quan el tresorer vulgui | Tresorer |
| S-M04-05 | El proveïdor detalla la comissió per cobrament | Si no, repartiment proporcional (VT-05) | PaynoPain |
| S-M04-06 | L'ingrés de la quota va a «General / Quotes de socis» (Q-18) | Sí | Junta |
| S-M04-07 | Departament de les comissions de llicències (Q-19) | «General / Llicències», provisional | Junta |
| S-M04-08 | Abonament de remeses per rebut o total | Tots dos admesos | Banc |
| S-M04-09 | Qui pot mantenir departaments i desfer conciliacions (T3, T4) | Administrador; tresorer per a T4 | Junta |

**Revisió de dubtes (aplicada a mà)**
1. **La spec 04 deia que l'original «queda marcat com a anul·lat», però també que la taula de moviments no admet UPDATE.** Les dues coses alhora no són possibles. Es resol amb un estat derivat (RN-T25). Propietari: responsable del projecte (aprovar-ho).
2. **«Conciliacions només s'afegeixen» i «desfer una conciliació»:** es resol amb una fila nova de desfeta (`ReconciliationUndo`) i un estat de línia mutable que és de la 04. Propietari: informàtica.
3. **La spec 04 enviava la domiciliació al trànsit «del proveïdor», però amb la 044 no hi ha proveïdor:** RN-T24 crea el trànsit «Remeses SEPA». Si el banc custodia els mandats o es tria un proveïdor amb domiciliació (alternatives 1 i 2 de la 044), el trànsit és el d'aquell proveïdor i la regla no canvia. Propietari: tresorer.
4. **Noms de codi:** la spec 04 feia servir noms en català (`registrar_cobrament`); V-09 de la 00 diu codi en anglès. Aquí es fixen els noms anglesos i el M01 s'hi alinea (`treasury.transfer_reference`). Propietari: informàtica.
5. **Retorns de domiciliacions:** arriben al banc com a càrrecs separats, després de l'abonament. La 04 només els casa amb la sortida que crea la 05b; la decisió de què passa amb el càrrec és de la 05b ([M05b-7](#M05b-7-regles)). Propietari: tresorer.
6. **Liquidació sense fitxer:** si el proveïdor no envia cap detall, el casament per període pot no quadrar quan hi ha devolucions dins el mateix abonament. Es deixa «a revisar» i es resol a mà. Propietari: tresorer.

<a id="M04-14-aprovar"></a>
## M04-14 Què cal aprovar abans de començar

**Aprovat el 27/10/2026** pel responsable del projecte:
| # | Punt | Resposta |
|---|---|---|
| 1 | Aquesta secció del M04 | Aprovada. La spec 04 v2 passa a l'[arxiu](arxiu/spec-04-tresoreria-v2-2026-10-27.md) (047) |
| 2 | RN-T24 (trànsit «Remeses SEPA») i RN-T25 (anul·lat derivat) | Aprovades |
| 3 | S-M04-01 i S-M04-07 | No bloquegen: es comença només amb «General» |
| 4 | T-M04-13 | Continua esperant P-45 punt 9 [A verificar: PaynoPain] |

---

<a id="M05a"></a>
# Mòdul 05a — Alta del mètode de pagament i mandats

**Estat: aprovat** pel responsable del projecte el 27/10/2026 ([M05a-14](#M05a-14-aprovar)). Els bloquejos que depenen del banc i de PaynoPain es mantenen [A verificar].

**Fonts:** decisions [017](decisions/017-pagaments-metodes-i-domiciliacions.md), [022](decisions/022-mandats-sepa-escenari-base-b.md), [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), [025](decisions/025-dos-nivells-de-produccio.md), [042](decisions/042-proveidors-substituits-pel-requisit-ue.md), [043](decisions/043-proveidor-de-pagaments-dins-la-ue.md), [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md); arquitectura §4.2, §4.3 i §4.9 (on diu Stripe, s'aplica la 042); [`integracio-paylands.md`](integracio-paylands.md); checklist (C9, G3 i els punts «N1»).

**Proveïdor.** Tot el que toca el proveïdor de pagaments passa per l'**adaptador** ([M05a-8](#M05a-8-serveis)). El proveïdor concret no està triat (P-44, P-45): tot el que en depèn porta **[A verificar]**. La domiciliació es planifica amb la **044** (IBAN i mandat xifrats a la plataforma), **acceptada com a camí per defecte**: si el banc custodia els mandats o es tria un proveïdor amb domiciliació (alternatives 1 i 2 de la 044), canvia només la custòdia ([M05a-13](#M05a-13-riscos)).

<a id="M05a-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Que cada soci tingui un mètode per pagar la quota abans de la primera remesa de la plataforma: recollir mandats SEPA nous en producció al nivell 1 (dades reals, cap cobrament), amb l'IBAN xifrat (044) i el proveïdor de targeta darrere de l'adaptador. |
| **Processos que cobreix** | P-M05a-A Triar el mètode de pagament · P-M05a-B Signar el mandat · P-M05a-C Canviar l'IBAN o revocar · P-M05a-D Guardar una targeta (condicional) · P-M05a-E Campanya de mandats · P-M05a-F Pas al nivell 1 · P-M05a-G Rotació de la clau |
| **Tasques** | 21 (T-M05a-01 a T-M05a-21) |
| **Què el bloqueja** | Res de la [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md) (acceptada). Identificador de creditor, remeses i mandats electrònics [A verificar: banc]. Proveïdor (T-M05a-05 i T-M05a-12) [A verificar: PaynoPain]. Traspàs dels mandats de Cluber [A verificar: tresorer amb el banc o la gestoria] |
| **Què cal aprovar** | Aprovat el 27/10/2026 ([M05a-14](#M05a-14-aprovar)). Queden els textos (junta) i l'autorització del nivell 1 (junta). La 044 és acceptada |

<a id="M05a-1-intencio"></a>
## M05a-1 Intenció, abast i fora d'abast

**Per què.** Per deixar Cluber, cada soci ha de tenir un mètode per pagar la quota abans de la primera remesa de la plataforma. Els mandats actuals els gestiona Cluber, i no se sap si es poden traspassar al club ([M01-13](#M01-13-riscos)). El 05a permet recollir mandats nous en producció (**nivell 1**: dades reals, **cap cobrament real**, [025](decisions/025-dos-nivells-de-produccio.md) i 042) mentre es construeixen els cobraments (05b).

**Resultat esperat.**
- Cada soci actiu tria com pagarà les quotes: **domiciliació** (per defecte, 017), **targeta guardada** (només si el proveïdor ho permet) o **pagar cada vegada** (targeta, Bizum o transferència).
- Qui tria domiciliació signa el **mandat SEPA dins l'app** i rep un correu de confirmació (CK G3).
- El tresorer veu quants socis tenen mandat vigent i envia la campanya de mandats i els recordatoris.
- L'IBAN no apareix mai en clar a cap pantalla, registre, exportació ni còpia sense xifrar.

**Com sabrem que funciona.**
- Al nivell 1, una prova demostra que no es pot crear cap cobrament real ni generar cap remesa.
- Cap camp fora del mandat conté un IBAN (prova automàtica de la 044).
- Les portes «N1» de la checklist estan superades (A6, E3, E4, B5, B8, G3) i la junta ho autoritza per escrit.
- El percentatge de socis actius amb mètode triat es veu en una sola pantalla.

**Dins de l'abast.**
- Adaptador de proveïdor: interfície, implementació falsa per a proves i implementació del proveïdor en mode de proves [A verificar: proveïdor].
- Configuració del proveïdor i compte de trànsit (`treasury.create_transit_account`).
- Recepció i registre de notificacions del proveïdor (infraestructura comuna amb el 05b, arquitectura §4.2).
- Preferència de mètode de pagament de la quota.
- Mandat SEPA: signatura dins l'app, IBAN xifrat, confirmació, consulta emmascarada, canvi d'IBAN, revocació, caducitat.
- Targeta guardada amb autenticació inicial, **condicional** al proveïdor [A verificar: P-45 punt 6].
- Campanya de mandats nous (escenari B, 022): invitacions, recordatoris i seguiment.
- Salvaguarda del nivell 1 i desbloqueig de la importació final de Cluber (`CLUBER_FINAL_IMPORT_ALLOWED`, [M01-9](#M01-9-criteris), CA-M01-23).
- Clau de xifratge: custòdia fora de la base de dades, rotació i prova de restauració.

**Fora d'abast.**
- Cobraments, remeses, avís previ, reintents, retornats, devolucions, rebuts (05b).
- **Traspàs dels mandats vigents de Cluber:** no es planifica fins que el banc o la gestoria responguin ([M01-13](#M01-13-riscos)). No es dona per fet ni que es pot ni que no.
- Importar IBAN de Cluber (RN-94 de la 00; 022).
- Socis menors (P-33): el M01 només admet majors d'edat.

<a id="M05a-2-dependencies"></a>
## M05a-2 Dependències

**De què depèn.**
| Mòdul | Què en fa servir |
|---|---|
| 00 | Compte personal (i reautenticació), consentiments i textos legals versionats, correu (annex A) per a G3 i recordatoris, registre d'activitat, permisos, enllaços segurs, cua de tasques |
| 01 | `members.active_members_for_mandates()`, `members.get_member_summary()`; el 05a desbloqueja la importació final de Cluber |
| 04 | `treasury.create_transit_account()` |
| Externes | Banc: identificador de creditor, format de remesa, validesa dels mandats electrònics [A verificar: banc, P-45 punt 5]. Proveïdor: tokenització i entorn de proves [A verificar: PaynoPain, P-45 punts 6 i 8] |

**Què depèn del 05a.**
| Mòdul | Què necessita |
|---|---|
| 05b | Adaptador, notificacions, mandats vigents per a la remesa, targetes guardades, preferència de mètode |
| 01 | Que el 05a pugui rebre mandats per permetre la importació final de Cluber |
| Nivell 1 de producció | El 05a acabat i provat (025) |

<a id="M05a-3-capacitats"></a>
## M05a-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | Pantalla (proposta) | Wireframe |
|---|---|---|---|---|
| C1 | Triar com es paga la quota | Soci | `/socis/pagaments/metode` | Falta (punt d'entrada: `socis.html#franja-estat`) |
| C2 | Signar el mandat SEPA | Soci | `/socis/pagaments/mandat` | Falta |
| C3 | Veure el mandat (IBAN emmascarat), canviar l'IBAN o revocar-lo | Soci | `/socis/pagaments/mandat` | Falta |
| C4 | Guardar una targeta per a les quotes (condicional) | Soci | `/socis/pagaments/targeta` | Falta |
| C5 | Campanya de mandats: enviar, recordar, seguir | Tresorer | `/gestio/pagaments/campanya` | Falta (entrada «Pagaments» a `admin.html`) |
| C6 | Llistat de mètodes i mandats per soci (emmascarat) | Tresorer | `/gestio/pagaments/mandats` | Falta |
| C7 | Configurar el proveïdor i veure l'estat del nivell | Administrador | `/gestio/pagaments/configuracio` | Falta |
| C8 | Revocar un mandat a petició del soci | Tresorer | Fitxa del mandat | Falta |

**Històries d'usuari**
- **HU-M05a-01.** Com a soci, vull triar si pago la quota domiciliada, amb una targeta guardada o cada vegada, per pagar com em vagi millor.
- **HU-M05a-02.** Com a soci, vull signar el mandat SEPA des del mòbil, veient clarament el creditor, el text i què accepto, per no haver d'anar al local.
- **HU-M05a-03.** Com a soci, vull rebre un correu amb la referència del mandat i com revocar-lo, per tenir-ne prova.
- **HU-M05a-04.** Com a soci, vull canviar l'IBAN o revocar el mandat quan vulgui, per mantenir el control.
- **HU-M05a-05.** Com a tresorer, vull enviar a cada soci actiu sense mandat una invitació per signar-lo i recordatoris, per tenir-los abans de la primera remesa.
- **HU-M05a-06.** Com a tresorer, vull veure quants socis tenen mandat, targeta guardada o cap mètode, per saber si es pot fer la remesa.
- **HU-M05a-07.** Com a administrador, vull que al nivell 1 la plataforma no pugui crear cap cobrament real, per complir la 025.
- **HU-M05a-08.** Com a administrador, vull que l'IBAN estigui xifrat amb una clau que no és a la base de dades, i poder rotar-la, per complir la 044.

<a id="M05a-4-rols"></a>
## M05a-4 Rols i permisos

Llegenda com a [M01-4](#M01-4-rols). «Propi» es fa amb el compte personal; la resta, amb el compte d'administrador i TOTP.

| # | Acció | Visitant | Part. no soci | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Resp. comunicació | Dept. Història | Junta | Administrador | Resp. botiga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1 | Triar el mètode de pagament de la quota | — | — | Propi | Propi si és soci | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) |
| A2 | Signar, canviar l'IBAN o revocar el seu mandat | — | — | Propi | Propi si és soci | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) |
| A3 | Guardar o esborrar la seva targeta (condicional) | — | — | Propi | Propi si és soci | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) | (ídem) |
| A4 | Veure mètodes i mandats de tots els socis (IBAN emmascarat) | — | — | — | — | Consulta (només «té mètode: sí/no») [A validar] | — | — | Sí | — | — | — | Sí | — |
| A5 | Enviar la campanya i els recordatoris | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| A6 | Revocar un mandat a petició escrita del soci, amb motiu | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| A7 | Configurar el proveïdor i les claus (per variables d'entorn) | — | — | — | — | — | — | — | — | — | — | — | Sí | — |
| A8 | Rotar la clau de xifratge | — | — | — | — | — | — | — | — | — | — | — | Sí (amb informàtica) | — |
| A9 | Veure l'IBAN complet | — | — | — | — | — | — | — | — | — | — | — | — | — |

**A9:** ningú no el veu a cap pantalla. Només el procés que genera la remesa (05b) el desxifra (044).

**Per objecte.** El soci només veu el seu mandat i la seva targeta. Intentar obrir el mandat d'un altre retorna «no trobat» i queda al registre. Un compte d'administrador no pot revocar el seu propi mandat des de l'administració (ho fa des del compte personal).

<a id="M05a-5-processos"></a>
## M05a-5 Processos pas per pas

**Wireframes existents:** `socis.html#franja-estat` (franja d'estat dels pagaments amb «Paga ara» i un exemple de quota domiciliada), `socis.html#avisos` (exemple d'avís previ), `admin.html` (entrada «Pagaments» per a `admin tresorer`). **Falten** tots els wireframes de [M05a-3](#M05a-3-capacitats) (tasca T-M05a-02).

### P-M05a-A Triar el mètode de pagament de la quota
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Soci | Obre «Com pago la quota» des de la franja de pagaments o des de l'avís de la campanya | `/socis/pagaments/metode` |
| 2 | Sistema | Mostra les opcions disponibles: domiciliació (recomanada), targeta guardada (només si el proveïdor ho permet i està activat) i pagar cada vegada | — |
| 3 | Soci | Tria. Domiciliació → P-M05a-B. Targeta → P-M05a-D. Pagar cada vegada → es desa la preferència i ja està | — |
| 4 | Sistema | Desa la preferència amb data i compte, i la registra | — |

### P-M05a-B Signar el mandat SEPA
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Soci | Escriu el nom del titular del compte i l'IBAN. Si el titular no és el soci, ho declara [A validar: junta i banc] | `/socis/pagaments/mandat` |
| 2 | Sistema | Valida l'IBAN (format i dígits de control, RN-M05a-05) i el país (zona SEPA admesa pel banc [A verificar: banc]) | — |
| 3 | Soci | Llegeix el text del mandat: nom i identificador de creditor del club [A verificar: banc], tipus recurrent, drets de devolució, referència que tindrà; marca «Accepto» | — |
| 4 | Sistema | Demana la contrasenya de nou si la sessió té més de 15 minuts (RN-M05a-12) | — |
| 5 | Sistema | Crea el mandat amb referència única (RN-M05a-03), data i hora, versió del text i compte; xifra l'IBAN; revoca el mandat anterior si n'hi havia (RN-M05a-02) | — |
| 6 | Sistema | Mostra la confirmació amb IBAN emmascarat i envia el correu G3: referència, identificador de creditor, data de signatura i com revocar-lo | — |

### P-M05a-C Canviar l'IBAN o revocar
- **Canviar l'IBAN:** és signar un mandat nou (P-M05a-B); l'anterior es revoca amb el motiu «substituït».
- **Revocar:** el soci tria «Revocar el mandat» i confirma. El mandat passa a «revocat» amb data. Si ja hi ha una remesa enviada al banc amb aquest mandat, s'avisa el tresorer (si el banc permet retirar el rebut és [A verificar: banc]). La preferència passa a «pagar cada vegada» i el soci rep un correu.
- **A petició escrita:** el tresorer revoca amb motiu (A6).

### P-M05a-D Guardar una targeta (condicional) [A verificar: proveïdor, P-45 punt 6]
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Soci | Tria «Targeta guardada» |
| 2 | Sistema | Demana a l'adaptador una operació d'autenticació (per exemple, autorització de 0 € amb 3DS, segons la documentació de Paylands [A verificar]) i obre el camp o la pàgina segura del proveïdor |
| 3 | Soci | Escriu la targeta al camp del proveïdor i s'autentica amb el seu banc. L'app no veu el número |
| 4 | Sistema | Amb la notificació verificada, desa només l'identificador de la targeta del proveïdor, els quatre darrers dígits i la caducitat (si el proveïdor els retorna) |

### P-M05a-E Campanya de mandats (escenari B, 022)
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Tresorer | Obre la campanya: veu els socis actius (`members.active_members_for_mandates`) amb i sense mètode | `/gestio/pagaments/campanya` |
| 2 | Tresorer | Revisa el text de la invitació (aprovat per la junta, comunicació de canvi de creditor, arquitectura §9.3) i l'envia | — |
| 3 | Sistema | Envia a cada soci sense mètode un correu i un avís a l'app amb l'enllaç a P-M05a-A. Sense compte personal activat: l'enllaç porta a activar-lo primer | — |
| 4 | Sistema | Recordatoris als socis que encara no han triat (RN-M05a-14) | — |
| 5 | Tresorer | Segueix el recompte: domiciliació, targeta guardada, pagar cada vegada, sense resposta | `/gestio/pagaments/campanya` |
| 6 | — | Qui no triï res abans de la remesa paga amb targeta, Bizum o transferència (022; 05b) | — |

### P-M05a-F Pas al nivell 1 de producció (025, 042)
1. 05a acabat i provat amb el proveïdor en mode de proves.
2. Portes 0, 1 i 2 superades i, de la porta 3, els punts «N1»: A6 marxa enrere, E3 monitoratge del flux, E4 alertes, B5 flux al mòbil i navegadors habituals, B8 accessibilitat bàsica del flux, G3 correu de confirmació.
3. Autorització **expressa i per escrit** de la junta.
4. `PAYMENTS_LIVE_CHARGES_ALLOWED` continua **fals**: cap cobrament ni remesa (RN-M05a-11).
5. S'obre la campanya (P-M05a-E) i es pot fer la importació final de Cluber (`CLUBER_FINAL_IMPORT_ALLOWED` = cert).

### P-M05a-G Rotació de la clau de xifratge (044)
L'administrador, amb informàtica, afegeix una clau nova a la configuració. Una tasca torna a xifrar cada IBAN amb la clau nova i desa la versió de clau. Quan totes les files tenen la versió nova, la clau vella es retira. Es prova a l'entorn de proves i amb una restauració de còpia.

<a id="M05a-6-entitats"></a>
## M05a-6 Entitats i camps

App Django `payments` (nova), compartida amb el 05b. Noms de codi en anglès.

### ProviderEvent (notificació rebuda, arquitectura §4.2)
| Camp | Tipus | Restriccions |
|---|---|---|
| `provider_code` | `CharField(30)` | — |
| `external_id` | `CharField(100)` | Únic `(provider_code, external_id)`: idempotència. Si el proveïdor no dona identificador d'esdeveniment, es fa servir ordre + estat [A verificar] |
| `event_type` | `CharField(60)` | — |
| `payload_hash` | `CharField(64)` | Empremta del cos; el cos complet es desa xifrat o no es desa [A validar: informàtica] |
| `received_at`, `processed_at` | `DateTimeField` | — |
| `result` | `processed`, `ignored_duplicate`, `rejected_signature`, `to_review`, `error` | — |
Només INSERT, excepte `processed_at` i `result` (s'actualitzen una vegada, amb registre).

### FeePaymentPreference (mètode de pagament de la quota)
`member` (OneToOne), `method` (`direct_debit`, `saved_card`, `pay_each_time`), `since`, `set_by` (compte), `mandate` (FK null), `saved_card` (FK null). `CHECK`: `direct_debit` ⇒ mandat; `saved_card` ⇒ targeta. Per defecte, cap fila = «sense resposta».

### SepaMandate (mandat)
| Camp | Tipus | Restriccions |
|---|---|---|
| `member` | FK Member (PROTECT) | — |
| `reference` | `CharField(35)` | Únic. Format de RN-M05a-03. Caràcters admesos per SEPA |
| `holder_name` | `CharField(70)` | Titular del compte |
| `holder_is_member` | `BooleanField` | — |
| `signed_at` | `DateTimeField` | — |
| `sequence_type` | `recurrent` | Únic valor d'inici |
| `creditor_identifier` | `CharField(35)` | Configuració (`SEPA_CREDITOR_ID`) copiada en signar [A verificar: banc] |
| `legal_text` | FK text legal versionat (00) | Text acceptat i versió |
| `signed_by_account` | FK compte personal | — |
| `evidence` | JSON | Canal, data i hora, versió del text; si cal IP o agent del navegador com a prova és [A validar: banc i gestoria] |
| `status` | `active`, `revoked`, `expired`, `blocked` | Un sol `active` per soci (índex únic parcial) |
| `revoked_at`, `revoked_reason`, `revoked_by` | null | — |
| `last_collection_on` | `DateField` null | L'actualitza el 05b; serveix per a la caducitat (RN-M05a-08) |

### MandateBankAccount (IBAN xifrat, 044)
| Camp | Tipus | Restriccions |
|---|---|---|
| `mandate` | OneToOne SepaMandate (PROTECT) | — |
| `iban_ciphertext` | `BinaryField` | Xifrat autenticat amb una clau fora de la base de dades i del repositori (`MANDATE_ENCRYPTION_KEYS`) |
| `key_version` | `PositiveSmallIntegerField` | Per a la rotació |
| `iban_country` | `CharField(2)` | Per mostrar i validar |
| `iban_last4` | `CharField(4)` | Per mostrar emmascarat |
**És l'únic lloc de la plataforma on hi ha un IBAN** (prova automàtica). El model no té `__str__` ni `repr` que el mostri; l'administrador de Django no el registra.

### SavedCard (targeta guardada, condicional)
`person`, `provider_code`, `provider_card_id` (`CharField(100)`, únic per proveïdor), `last4`, `expiry_month`, `expiry_year` (si el proveïdor els retorna [A verificar]), `status` (`active`, `removed`, `expired`), `created_at`. Mai el número ni el codi de seguretat.

### MandateCampaign i MandateCampaignRecipient
- `MandateCampaign`: `name`, `opened_by`, `opened_at`, `closed_at` null, `invitation_text` (FK text versionat).
- `MandateCampaignRecipient`: `campaign`, `member`, `invited_at`, `reminders_sent` (`PositiveSmallIntegerField`), `last_reminder_at`, `answered_at` null, `answer` (`direct_debit`, `saved_card`, `pay_each_time`) null. Únic `(campaign, member)`.

### ProviderConfig (configuració sense secrets)
`provider_code`, `environment` (`sandbox`, `live`), `card_enabled`, `bizum_enabled`, `tokenization_enabled`, `transit_account` (FK TreasuryAccount). Les claus i els secrets són variables d'entorn ([M05a-12](#M05a-12-seguretat)).

**Migracions:** reversibles; activació de l'extensió o biblioteca de xifratge escollida [A validar: informàtica]; permisos de PostgreSQL perquè la taula `MandateBankAccount` només la llegeixi el procés de remeses si es fan servir rols separats (proposta).

<a id="M05a-7-regles"></a>
## M05a-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M05a-01 | Mètodes de la quota: domiciliació (per defecte recomanat), targeta guardada (si el proveïdor ho permet), pagar cada vegada (targeta, Bizum o transferència). Inscripcions i llicències no es domicilien | 017; RN-69 de la 00 |
| RN-M05a-02 | Un soci té com a molt **un mandat actiu** per a les quotes. Signar-ne un de nou revoca l'anterior amb el motiu «substituït» | Proposta |
| RN-M05a-03 | Referència del mandat: `CRIS` + número de soci de 6 xifres + `M` + ordinal de 2 xifres (per exemple, `CRIS001287M01`). Única, sense dades personals més enllà del número de soci, i no es reutilitza. Que el banc l'admeti és [A verificar: banc] | Proposta; màxim de 35 caràcters del format SEPA |
| RN-M05a-04 | Identificador de creditor = el del club, de configuració. Sense identificador confirmat pel banc, no es pot obrir la campanya en producció | 044; P-45 punt 5 |
| RN-M05a-05 | L'IBAN es valida pel format del país i els dígits de control (mòdul 97, ISO 13616) abans de desar-lo. Un IBAN invàlid no es desa ni es registra | Proposta |
| RN-M05a-06 | L'IBAN es desa **només** xifrat al mandat; a la pantalla, sempre emmascarat (`ES•• •••• •••• •••• •••• 1234`); mai als registres, exportacions, correus ni seguiment d'errors | 044 |
| RN-M05a-07 | El mandat signat queda amb text i versió acceptats, data i hora, compte i canal. El correu de confirmació G3 surt de cris1954.cat amb resposta a cris@cris.es | 044; 019; CK G3 |
| RN-M05a-08 | Un mandat sense cap cobrament en 36 mesos caduca i passa a «caducat» [A verificar: banc, regla del reglament SEPA] | Proposta |
| RN-M05a-09 | La revocació és efectiva per a les remeses que es generin després; si ja n'hi ha una enviada al banc, s'avisa el tresorer [A verificar: banc] | Proposta |
| RN-M05a-10 | Targeta guardada: només amb autenticació inicial del titular al proveïdor; la plataforma desa només l'identificador del proveïdor, els quatre darrers dígits i la caducitat [A verificar: proveïdor] | 043; `integracio-paylands.md` §6 |
| RN-M05a-11 | **Nivell 1:** `PAYMENTS_LIVE_CHARGES_ALLOWED` = fals. L'adaptador rebutja crear cap ordre de cobrament amb claus de producció, i el 05b no pot generar remeses. Només el nivell 2, amb autorització de la junta, ho canvia | 025; 042 |
| RN-M05a-12 | Signar, canviar o revocar un mandat i guardar una targeta demanen una sessió recent: si l'última autenticació té més de 15 minuts, es torna a demanar la contrasenya (i el TOTP si el compte el té) [A validar: informàtica] | Proposta (CK C3) |
| RN-M05a-13 | Menors: el mandat el signa el titular del compte (P-33). Mentre P-33 no es resolgui, només hi ha socis majors d'edat ([M01-13](#M01-13-riscos), S-M01-13) | 044; 025 |
| RN-M05a-14 | Campanya: una invitació per soci actiu sense mètode; recordatoris als 7 i als 14 dies de la invitació, i un d'últim quan el tresorer fixi la remesa [A validar: tresorer]. Cap recordatori a qui ja ha triat | Proposta |
| RN-M05a-15 | Qui no triï cap mètode paga la quota amb targeta, Bizum o transferència quan es generi (022) | 022 |
| RN-M05a-16 | Els mandats vigents de Cluber **no** s'importen ni es donen per traspassables o no traspassables fins que el banc o la gestoria responguin ([M01-13](#M01-13-riscos)) | Aprovació del M01, resposta 7 |
| RN-M05a-17 | Tota notificació del proveïdor es verifica (firma o empremta segons el proveïdor, i llista d'IP si la dona) abans de desar-la com a vàlida; es desa per identificador únic i es processa a la cua | Arquitectura §4.2; `integracio-paylands.md` §3 |

**Exemples numèrics**
- **Referència (RN-M05a-03):** soci 1287, primer mandat → `CRIS001287M01` (13 caràcters); canvia l'IBAN → `CRIS001287M02` i `M01` queda «revocat (substituït)».
- **IBAN emmascarat (RN-M05a-06):** un IBAN espanyol de 24 caràcters acabat en 1234 es mostra `ES•• •••• •••• •••• •••• 1234`. Un IBAN amb un dígit de control canviat es rebutja (RN-M05a-05).
- **Campanya (RN-M05a-14):** 150 socis actius, 20 ja han triat «pagar cada vegada» → **130 invitacions**. Si als 7 dies n'han respost 70, el primer recordatori va a **60**; si als 14 dies en queden 25, el segon va a **25**.
- **Cobertura:** 100 domiciliacions + 10 targetes guardades + 30 «cada vegada» + 10 sense resposta → **110 de 150 (73 %)** amb cobrament automàtic previst a la primera remesa.
- **Caducitat (RN-M05a-08):** mandat amb l'últim cobrament fa 36 mesos sense cap rebut posterior → «caducat»; el soci rep un avís per signar-ne un de nou.

<a id="M05a-8-serveis"></a>
## M05a-8 Serveis i interfícies (contracte)

**Adaptador de proveïdor** (`payments.providers.base.PaymentProvider`). La resta de l'aplicació només crida aquesta interfície. Implementacions: `FakeProvider` (proves, sense xarxa) i la del proveïdor triat [A verificar: P-44, P-45]. Cap mètode rep ni retorna dades de targeta.
| Mètode | Entrada | Sortida | Notes |
|---|---|---|---|
| `create_order(charge, method, urls, idempotency_key)` | càrrec, `card` o `bizum`, URL de notificació i de tornada | `ProviderOrder(external_id, pay_url, expires_at)` | Rebutja si és producció i `PAYMENTS_LIVE_CHARGES_ALLOWED` és fals (RN-M05a-11). Ús: 05b |
| `verify_notification(request)` | petició HTTP | `ProviderNotification(event_id, order_id, status, amount_cents, currency, card_ref?)` o `InvalidSignature` | Firma o empremta i llista d'IP [A verificar] |
| `get_order(external_id)` | — | estat actual | Per a la tasca de xarxa de seguretat [A verificar que l'API ho permet] |
| `refund(payment, amount_cents, idempotency_key)` | — | `ProviderRefund` | Ús: 05b. Bizum [A verificar] |
| `start_card_setup(person, urls)` | — | URL o `iframe` d'autenticació | Condicional (RN-M05a-10) |
| `charge_saved_card(charge, saved_card, idempotency_key)` | — | `ProviderOrder` | Condicional; ús: 05b |
| `capabilities()` | — | `{card, bizum, tokenization, refund_bizum, embedded_field}` | Les pantalles només ofereixen el que el proveïdor declara |

**Ofereix**
| Servei | Sortida | Errors | Qui el fa servir |
|---|---|---|---|
| `payments.fee_payment_method(member)` | `direct_debit`, `saved_card`, `pay_each_time` o `None` | — | 01 (fitxa), 05b |
| `payments.active_mandate(member)` | `MandateSummary(reference, signed_at, masked_iban, creditor_id)` o `None` | — | 01, 05b |
| `payments.mandates_for_remittance(charges)` | iterador de `(charge, reference, signed_at, holder_name, iban)` **desxifrat** | `NoActiveMandate`, `LiveChargesNotAllowed` | **Només** el generador de remeses del 05b |
| `payments.record_collection(mandate, on)` | actualitza `last_collection_on` | — | 05b |
| `payments.campaign_status(campaign)` | recomptes per resposta | — | Tresorer, 08 |
| `payments.provider()` | la implementació configurada de l'adaptador | — | 05b |

**Consumeix**
| Servei | Mòdul | Per a què |
|---|---|---|
| `members.active_members_for_mandates()`, `members.get_member_summary()` | 01 | Campanya i textos |
| `treasury.create_transit_account(provider_code, name)` | 04 | Trànsit del proveïdor i «Remeses SEPA» |
| `consents.record(...)`, `legal_texts.current("sepa_mandate")` | 00 | Text del mandat versionat |
| `accounts.require_recent_auth(account, minutes=15)` | 00 | RN-M05a-12 |
| `mail.send(...)`, `notices.post(...)` | 00 | G3, invitacions i recordatoris |
| `audit.record(...)`, `permissions.require(...)` | 00 | Registre i permisos |

**Rutes.** Compte personal: `/socis/pagaments/metode`, `/socis/pagaments/mandat`, `/socis/pagaments/targeta`. Administració: `/gestio/pagaments/campanya`, `/gestio/pagaments/mandats`, `/gestio/pagaments/configuracio`. Pública declarada (RN-40 de la 00): `/pagaments/notificacions/{proveïdor}` (només POST, verificada).

<a id="M05a-9-criteris"></a>
## M05a-9 Criteris d'acceptació i casos límit

- **CA-M05a-01** Donat un soci actiu, quan obre «Com pago la quota», llavors només veu les opcions que declara `capabilities()`; sense tokenització, no hi ha «targeta guardada».
- **CA-M05a-02** Donat un IBAN amb els dígits de control incorrectes, quan s'envia, llavors es rebutja amb un missatge clar i no es desa ni es registra cap part de l'IBAN.
- **CA-M05a-03** Donat un mandat acceptat, quan es desa, llavors té referència única amb el format de RN-M05a-03, text i versió, data i hora i compte; l'IBAN és només a `MandateBankAccount`, xifrat.
- **CA-M05a-04** Donat un mandat signat, quan s'envia el correu G3, llavors porta la referència, l'identificador de creditor, la data i com revocar-lo, i no porta l'IBAN complet.
- **CA-M05a-05** Donat un soci amb mandat actiu, quan en signa un altre, llavors l'anterior passa a «revocat (substituït)» i només n'hi ha un d'actiu (índex únic parcial).
- **CA-M05a-06** Donat qualsevol pantalla, correu, exportació, registre o error, quan s'hi busca l'IBAN complet d'una dada de prova, llavors no hi és (prova automàtica sobre les sortides).
- **CA-M05a-07** Donat una revisió del model de dades, quan s'executa la prova, llavors l'únic camp que pot contenir un IBAN és `iban_ciphertext` (044).
- **CA-M05a-08** Donat una sessió de més de 15 minuts, quan el soci vol signar o revocar, llavors ha de tornar a escriure la contrasenya.
- **CA-M05a-09** Donat el nivell 1 (`PAYMENTS_LIVE_CHARGES_ALLOWED` = fals) i claus de producció, quan qualsevol codi crida `create_order` o `charge_saved_card`, llavors es rebutja i queda al registre; `mandates_for_remittance` també es rebutja.
- **CA-M05a-10** Donat una notificació amb firma o empremta invàlida, o des d'una IP fora de la llista (si n'hi ha), quan arriba, llavors es respon amb error, no es processa i queda registrada com a rebutjada.
- **CA-M05a-11** Donat una notificació vàlida repetida, quan arriba per segona vegada, llavors es respon correcte i no es torna a processar.
- **CA-M05a-12** Donat una campanya oberta, quan s'envien les invitacions, llavors només en reben els socis actius sense mètode, i cap rep un recordatori després d'haver triat.
- **CA-M05a-13** Donat la rotació de la clau, quan la tasca acaba, llavors tots els IBAN es desxifren amb la clau nova i cap fila té la versió vella; una restauració de còpia amb la clau es prova.
- **CA-M05a-14** Donat un soci que vol veure el mandat d'un altre per URL, quan es processa, llavors rep «no trobat» i l'intent queda al registre.
- **CA-M05a-15** Donat una targeta guardada (condicional), quan es desa, llavors només hi ha l'identificador del proveïdor, els quatre darrers dígits i la caducitat.
- **CA-M05a-16** Donat el 05a acabat i provat, quan l'administrador activa `CLUBER_FINAL_IMPORT_ALLOWED`, llavors la importació final del M01 es pot confirmar (CA-M01-23).
- **CA-M05a-17** Donat cada cel·la de [M05a-4](#M05a-4-rols), quan el rol prova l'acció, llavors el resultat coincideix.

**Casos límit**
| # | Cas | Comportament |
|---|---|---|
| L-M05a-01 | El titular del compte no és el soci (parella, familiar) | Es desa el nom del titular i la declaració; si s'admet és [A validar: junta i banc] |
| L-M05a-02 | Dos socis paguen des del mateix IBAN | Dos mandats, un per soci, amb referències diferents |
| L-M05a-03 | IBAN d'un país de la zona SEPA fora d'Espanya | S'admet si el banc l'accepta [A verificar: banc]; si no, missatge clar |
| L-M05a-04 | El soci revoca el mandat amb una remesa ja enviada | Avís al tresorer (RN-M05a-09) |
| L-M05a-05 | El soci es dona de baixa (M01) | El mandat es revoca amb motiu «baixa»; l'IBAN es conserva xifrat el temps de la 044 i després es destrueix |
| L-M05a-06 | Esborrat RGPD | Mandat i IBAN **bloquejats**, no anonimitzats, fins al final del termini (044; 028) |
| L-M05a-07 | Es perd la clau de xifratge | No es poden generar remeses; els socis han de tornar a signar. Per això la clau té còpia fora del servidor ([M05a-12](#M05a-12-seguretat)) |
| L-M05a-08 | Soci sense compte personal activat rep la invitació | L'enllaç porta a activar el compte primer |
| L-M05a-09 | El proveïdor deixa de permetre la tokenització | L'opció desapareix; les targetes guardades continuen fins que caduquen o el soci les esborra |
| L-M05a-10 | Cap soci ha triat encara | La pantalla de campanya diu «Encara no ha respost ningú» i mostra el recompte de pendents |

<a id="M05a-10-tasques"></a>
## M05a-10 Tasques (per dependències, sense dates)

| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M05a-01 | Text del mandat SEPA, de la invitació i del correu G3, revisats per la junta | S | `docs/`, textos legals (00) | Identificador de creditor (P-45 punt 5) | Textos aprovats |
| T-M05a-02 | Wireframes del mètode, mandat, targeta, campanya i configuració | M | `design/wireframes/socis.html`, `admin.html` | — | Revisats; contrast comprovat |
| T-M05a-03 | Interfície de l'adaptador i `FakeProvider` | M | `apps/payments/providers/` | T-M01-03 | Proves de contracte de l'adaptador |
| T-M05a-04 | `ProviderEvent` i endpoint de notificacions (verificar, desar, respondre, cua) | M | `apps/payments/webhooks.py` | T-M05a-03 | CA-M05a-10, 11 |
| T-M05a-05 | Implementació del proveïdor en mode de proves | L | `apps/payments/providers/<proveïdor>.py` | T-M05a-04; proveïdor triat i entorn de proves (P-44, P-45 punt 8) | Proves contra l'entorn de proves del proveïdor |
| T-M05a-06 | Salvaguarda del nivell 1 | S | `apps/payments/guards.py`, configuració | T-M05a-03 | CA-M05a-09 |
| T-M05a-07 | Xifratge de camp, versions de clau i rotació | M | `apps/payments/crypto.py` | T-M01-03; biblioteca triada [A validar: informàtica] | CA-M05a-13 |
| T-M05a-08 | Models de mandat, IBAN xifrat, preferència i campanya | M | `apps/payments/models.py` | T-M05a-07, T-M01-11 | CA-M05a-03, 05, 07 |
| T-M05a-09 | Signatura del mandat: validació d'IBAN, text versionat, reautenticació, G3 | L | `apps/payments/mandates.py`, vistes | T-M05a-08, T-M05a-01, T-M01-08, T-M01-10 | CA-M05a-02, 03, 04, 08 |
| T-M05a-10 | Canvi d'IBAN i revocació | S | `mandates.py` | T-M05a-09 | P-M05a-C provat |
| T-M05a-11 | Preferència de mètode (pantalla i servei) | S | `apps/payments/preferences.py` | T-M05a-08 | CA-M05a-01 |
| T-M05a-12 | Targeta guardada (condicional) | M | `apps/payments/cards.py` | T-M05a-05; tokenització confirmada (P-45 punt 6) | CA-M05a-15 |
| T-M05a-13 | Campanya: invitacions, recordatoris, recompte | M | `apps/payments/campaigns.py`, tasques de la cua | T-M05a-11 | CA-M05a-12 |
| T-M05a-14 | Llistat de mandats per al tresorer (emmascarat) | S | vistes | T-M05a-08 | Proves de permisos |
| T-M05a-15 | Caducitat de 36 mesos (tasca periòdica) | S | tasques de la cua | T-M05a-08 | Prova amb dates inventades |
| T-M05a-16 | Compte de trànsit en configurar el proveïdor; trànsit «Remeses SEPA» | S | `apps/payments/setup.py` | T-M04-17 | Comptes creats una sola vegada |
| T-M05a-17 | Proves de sortides sense IBAN (pantalles, correus, registres, errors, exportacions) | M | `tests/` | T-M05a-09 | CA-M05a-06, 07 |
| T-M05a-18 | Revisió d'accessibilitat i dispositius del flux de mandat (B5 i B8 «N1») | M | — | T-M05a-09 a T-M05a-13 | Llista de dispositius i auditoria |
| T-M05a-19 | Monitoratge, alertes i marxa enrere del flux (E3, E4, A6 «N1») | M | configuració del servidor | T-M05a-09 | Simulacres fets |
| T-M05a-20 | Desbloqueig de la importació final de Cluber | S | configuració | T-M05a-09, T-M01-25 | CA-M05a-16 |
| T-M05a-21 | Guia per al tresorer i text d'ajuda per als socis | S | `docs/` | T-M05a-13 | Revisada |

<a id="M05a-11-proves"></a>
## M05a-11 Pla de proves

- **Unitàries (B1):** validació d'IBAN (vàlids, dígits de control erronis, països), format de la referència, emmascarament, caducitat, regles de la campanya.
- **Seguretat (C9):** notificacions amb firma falsa, repetides, desordenades; IP fora de llista; nivell 1 sense cap cobrament possible; cap IBAN a cap sortida; xifrat i rotació; restauració amb la clau.
- **Permisos (B4):** una prova per cel·la de [M05a-4](#M05a-4-rols); objecte (un soci no veu el mandat d'un altre).
- **Integració:** de la invitació al correu G3 amb `FakeProvider`; amb l'entorn de proves del proveïdor quan existeixi [A verificar].
- **Contracte:** adaptador i serveis de [M05a-8](#M05a-8-serveis).
- **Accessibilitat i dispositius («N1»):** contrast, teclat, etiquetes i errors clars al formulari del mandat; Android i iOS i navegadors habituals.
- **Dades:** només inventades; IBAN de prova amb format vàlid que no corresponguin a comptes reals.

<a id="M05a-12-seguretat"></a>
## M05a-12 Seguretat i RGPD

- **Xifratge (044):** xifratge autenticat de camp; claus a `MANDATE_ENCRYPTION_KEYS` (variable d'entorn, mai al repositori ni a la base de dades), amb versió; còpia de la clau guardada fora del servidor per les persones que fixi la junta; rotació provada.
- **Còpies:** les còpies de la base de dades porten l'IBAN xifrat; la restauració es prova amb la clau (044).
- **Exposició:** IBAN només emmascarat; cap registre, correu, exportació ni error amb l'IBAN; el seguiment d'errors (GlitchTip o Bugsink) filtra camps sensibles.
- **Targetes:** mai a l'app; camp o pàgina del proveïdor; política de seguretat de continguts que només permet el domini del proveïdor a `frame-src` [A verificar: domini].
- **Notificacions:** endpoint públic declarat, només POST, firma o empremta verificades, llista d'IP si el proveïdor la dona, limitació de peticions.
- **Secrets del proveïdor:** variables d'entorn per entorn; claus de proves i de producció separades.
- **Base legal:** execució del contracte de soci; finalitat única, cobrament de quotes; informació al text del mandat (044) [A validar: responsable de protecció de dades, Q-15].
- **Conservació:** mentre el mandat sigui vigent; després, la prova del mandat el termini de reclamació (13 mesos) més el que digui la gestoria; després es destrueix [A validar: gestoria, Q-14].
- **Dades dins la UE:** proveïdor, servidors i subencarregats dins la UE (035) [A verificar: P-45 punt 3].

<a id="M05a-13-riscos"></a>
## M05a-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| **Mandats vigents de Cluber** (risc de [M01-13](#M01-13-riscos)): no se sap si es poden traspassar al club | Alt: decideix si cal la campanya per a tothom | Preguntar al banc o a la gestoria. El 05a es construeix per a la campanya (022, provisional) i **no** inclou cap importació de mandats fins que hi hagi resposta. Si la resposta és que sí, cal una decisió nova i tasques noves | Tresorer |
| Proveïdor no confirmat (P-44) | Alt per a T-M05a-05 i T-M05a-12 | Adaptador amb `FakeProvider`; la resta del 05a no en depèn | Tresorer (amb el banc) |
| La 044 és el camí per defecte, però revisable | Alt: si el banc custodia els mandats, part del model sobra | Custòdia aïllada a `MandateBankAccount` i `mandates_for_remittance`; canviar-la no toca la resta | Junta i banc |
| Validesa del mandat signat electrònicament | Alt: si el banc no l'admet, cal una altra forma de signatura | Preguntar-ho al banc abans de T-M05a-09 | Banc (via tresorer) |
| Identificador de creditor del club | Bloqueja la producció de la campanya | P-45 punt 5 | Banc |
| Poca resposta a la campanya | Mitjà | Recordatoris, avís a l'app, ajuda presencial de la secretaria; alternativa de pagament (022) | Tresorer |
| Moment de la primera remesa (P-29) | Alt: la campanya ha d'acabar abans | Saber-ho ja; si no hi ha temps, la remesa es fa amb Cluber | Tresorer |
| Pèrdua de la clau | Alt | Còpia de la clau fora del servidor i prova de restauració | Informàtica |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M05a-01 | El banc admet remeses pain.008, dona l'identificador de creditor i admet mandats electrònics (P-45 punt 5) | Sí | Banc |
| S-M05a-02 | Tokenització amb autenticació inicial (P-45 punt 6) | Opció amagada fins que es confirmi | PaynoPain |
| S-M05a-03 | Entorn de proves del proveïdor (P-45 punt 8) | Es treballa amb `FakeProvider` | PaynoPain |
| S-M05a-04 | Format de la referència del mandat (RN-M05a-03) | `CRIS` + número + `M` + ordinal | Banc |
| S-M05a-05 | Titular diferent del soci | Admès amb declaració | Junta i banc |
| S-M05a-06 | IBAN de fora d'Espanya | Admès si el banc l'accepta | Banc |
| S-M05a-07 | Calendari de recordatoris (RN-M05a-14) | 7 i 14 dies, i un d'últim | Tresorer |
| S-M05a-08 | Proves de signatura (IP, agent del navegador) | Només canal, data i versió | Banc i gestoria |
| S-M05a-09 | Qui guarda la còpia de la clau | Dues persones que fixi la junta | Junta |
| S-M05a-10 | Biblioteca de xifratge i rols de PostgreSQL separats | Biblioteca estàndard de Python amb xifratge autenticat | Informàtica |
| S-M05a-11 | Caducitat de 36 mesos (RN-M05a-08) | Sí | Banc |
| S-M05a-12 | Temps per demanar de nou la contrasenya (RN-M05a-12) | 15 minuts | Informàtica |
| S-M05a-13 | La secretaria veu només «té mètode: sí/no» | Sí | Junta |
| S-M05a-14 | Traspàs dels mandats de Cluber | Cap supòsit | Tresorer (banc o gestoria) |

**Revisió de dubtes (aplicada a mà)**
1. **El «mode real només per a mandats» de la 025 pensava en Stripe.** Amb la 044, signar un mandat no necessita el proveïdor: el nivell 1 vol dir «dades reals a producció, cap cobrament ni remesa». La salvaguarda es manté (RN-M05a-11). Propietari: responsable del projecte.
2. **CLAUDE.md deia que la plataforma no guarda mai l'IBAN; la 044 diu que sí, xifrat.** **Resolt:** la 044 és acceptada (27/10/2026) i CLAUDE.md i la checklist (C9) s'hi han alineat. Propietari: cap.
3. **El text del mandat i el correu G3 porten l'identificador de creditor,** que encara no tenim. Bloqueja la producció, no el desenvolupament. Propietari: banc.
4. **La targeta guardada pot fer que alguns socis no domiciliïn.** La 017 diu que la domiciliació és el mètode per defecte, no l'únic; l'opció apareix només si el proveïdor la permet. Propietari: junta.
5. **Socis sense compte personal activat** (molts dels importats de Cluber): la campanya passa primer per activar el compte; pot ser una barrera. Alternativa a valorar: enllaç segur de la 00 per signar sense compte [A validar: junta]. Propietari: junta.
6. **Si el titular no és el soci**, qui accepta el mandat no és qui té el compte personal. Cal saber si el banc ho admet. Propietari: banc.

<a id="M05a-14-aprovar"></a>
## M05a-14 Què cal aprovar abans de començar

**Aprovat el 27/10/2026** pel responsable del projecte. Queda:
1. ~~La 044~~ **Acceptada** el 27/10/2026 «com a camí per defecte, revisable si el banc o el proveïdor ofereixen custòdia de mandats», amb l'ampliació (clau amb rotació i prova de restauració, ningú no veu l'IBAN complet, norma d'esborrat del fitxer de la remesa) i la millora opcional de l'enllaç de descàrrega d'un sol ús. T-M05a-07 a T-M05a-10 ja es poden començar. La conservació continua [A validar: gestoria, Q-14].
2. **Textos** del mandat, la invitació i el correu G3 (junta), quan hi hagi l'identificador de creditor [A verificar: banc].
3. **Format de la referència del mandat** [A verificar: banc] i **titular diferent del soci** [A validar: junta i banc].
4. **Proveïdor** (P-44, P-45) [A verificar: PaynoPain]: només bloqueja T-M05a-05 i T-M05a-12.
5. **Autorització del nivell 1** (junta, 025): quan el 05a estigui acabat i provat.

---

<a id="M05b"></a>
# Mòdul 05b — Cobraments: targeta, Bizum, domiciliació i transferència

**Estat: aprovat** pel responsable del projecte el 27/10/2026 ([M05b-14](#M05b-14-aprovar)). Els bloquejos que depenen del banc i de PaynoPain es mantenen [A verificar].

**Fonts:** decisions [013](decisions/013-imputacio-comissions.md), [017](decisions/017-pagaments-metodes-i-domiciliacions.md), [021](decisions/021-persones-no-socies-com-a-convidades.md), [022](decisions/022-mandats-sepa-escenari-base-b.md), [025](decisions/025-dos-nivells-de-produccio.md), [040](decisions/040-impagat-es-marca-a-ma.md), [042](decisions/042-proveidors-substituits-pel-requisit-ue.md) a [045](decisions/045-correccio-transferencia-conciliada-per-error.md); annex D de la [spec 04](arxiu/spec-04-tresoreria-v2-2026-10-27.md) (experiència de pagament, que passa aquí); arquitectura §4.2 a §4.8; [`integracio-paylands.md`](integracio-paylands.md); spec 00 (RN-30 a RN-33, RN-60 a RN-73).

**Proveïdor.** Targeta i Bizum passen per l'**adaptador** del [05a](#M05a-8-serveis). Tot el que depèn del proveïdor porta **[A verificar]** (P-44, P-45). La domiciliació es fa amb **remeses pain.008** que la plataforma genera i el tresorer puja al banc (043 (e), 044): l'app no mou mai diners sola.

<a id="M05b-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Cobrar dins l'app quotes, inscripcions i llicències amb targeta, Bizum, domiciliació i transferència, sense donar mai res per pagat pel navegador i quadrant-ho tot amb la tresoreria. És el criteri per deixar Cluber (nivell 2). |
| **Processos que cobreix** | P-M05b-A Targeta · P-M05b-B Bizum · P-M05b-C Transferència · P-M05b-D Notificació del proveïdor · P-M05b-E Remesa de quotes · P-M05b-F Retornat, reintent i alternativa · P-M05b-G Devolució · P-M05b-H Liquidació del proveïdor · P-M05b-I Pas al nivell 2 |
| **Tasques** | 20 (T-M05b-01 a T-M05b-20) |
| **Què el bloqueja** | Remeses (T-M05b-10 i T-M05b-11): resposta del banc (P-45 punt 5) [A verificar]. Targeta i Bizum contra un proveïdor real i liquidacions (T-M05b-14): PaynoPain (P-44, P-45) [A verificar]; amb `FakeProvider` es pot avançar |
| **Què cal aprovar** | Aprovat el 27/10/2026 amb RN-M05b-14 ([048](decisions/048-reobrir-carrec-retornat.md)) i RN-M05b-15 ([M05b-14](#M05b-14-aprovar)). Queden RN-M05b-16 i RN-M05b-18 (junta, configurables) i l'autorització del nivell 2 (junta). El 02 proposa una ampliació petita del seu contracte ([M02-14](#M02-14-aprovar)) |

<a id="M05b-1-intencio"></a>
## M05b-1 Intenció, abast i fora d'abast

**Per què.** És el criteri per deixar Cluber ([014](decisions/014-migracio-cluber-i-entrada-en-produccio.md), 025): el club ha de poder cobrar les quotes directament, **dins l'app**, sense errors i quadrant-ho tot amb la tresoreria.

**Resultat esperat.**
- El soci paga un càrrec **sense sortir de l'app**, amb targeta o Bizum al camp o la pàgina segura del proveïdor, o per transferència amb referència; veu sempre l'estat real (pendent, en curs, pagat, fallit) i rep el **rebut de seguida**.
- El tresorer genera la **remesa** de les quotes domiciliades amb avís previ, la puja al banc, i la plataforma gestiona els **retornats**, el **reintent controlat** i l'**alternativa de pagament**.
- Cada cobrament, comissió, devolució i retorn arriba a la tresoreria (04) pels seus serveis.

**Com sabrem que funciona.**
- Cap càrrec passa a «pagat» sense una notificació verificada del proveïdor o una conciliació confirmada pel tresorer.
- Una notificació repetida, desordenada o falsa no crea cap pagament ni ingrés de més.
- Una remesa inventada de 130 rebuts genera un fitxer vàlid contra l'esquema del banc [A verificar: versió] i, conciliada, deixa 130 càrrecs pagats i el trànsit «Remeses SEPA» a zero.
- Portes 0 a 3 completes i autorització de la junta per al **nivell 2** (025).

**Dins de l'abast.**
- Pagar un càrrec (quota ara; inscripció i llicència quan existeixin els mòduls 02 i 06) amb targeta, Bizum o transferència, des del compte personal o amb l'enllaç de convidat de la 00 (021).
- Estats visibles, Bizum amb espera, caducitat i abandonament (annex D de la spec 04).
- Processament de notificacions (sobre la infraestructura del 05a), xarxa de seguretat diària i ordres caducades.
- Cobrament amb targeta guardada (condicional, [M05a-7](#M05a-7-regles) RN-M05a-10).
- Remeses SEPA: selecció, avís previ, fitxer pain.008, marca d'enviament, liquidació a la 04.
- Retornats, reintent controlat, alternativa de pagament i avís al tresorer (l'impagat continua sent manual, 040).
- Devolucions iniciades pel club (totals i parcials).
- Rebut immediat (justificant, no factura, P-47).
- Liquidacions del proveïdor cap a la 04 (T-M04-13).
- Pas al nivell 2.

**Fora d'abast.**
- Registre manual i efectiu (P-12, RN-72 de la 00).
- Facturació i Verifactu (P-02, P-47).
- Pagaments sortints en fitxer pain.001 (P-45 punt 12; 09).
- Iniciació de transferència per PSD2 [A verificar: P-45 punt 14].
- Pagaments parcials i saldo a favor (QT-05). L'operativa `PARTIAL_AUTHORIZATION` de Paylands no es fa servir.

<a id="M05b-2-dependencies"></a>
## M05b-2 Dependències

**De què depèn.**
| Mòdul | Què en fa servir |
|---|---|
| 00 | Càrrec i pagament (RN-66 a RN-73), enllaços de convidat (RN-30 a RN-33), fitxers privats (PDF del rebut), correu, cua de tasques, registre, permisos |
| 01 | Quotes (`AnnualFee`), `members.on_fee_paid`, `members.on_fee_returned`, `members.get_member_summary` |
| 04 | `record_income`, `record_fee`, `record_refund`, `record_return`, `record_settlement`, `transfer_reference`; conciliació de l'extracte |
| 05a | Adaptador, notificacions, `fee_payment_method`, `active_mandate`, `mandates_for_remittance`, `record_collection`, targetes guardades, salvaguarda del nivell |
| Externes | Proveïdor: ordres, notificacions, devolucions, liquidacions [A verificar: P-45]. Banc: format pain.008, terminis de presentació, comissions per rebut i per retornat, fitxer de retornats [A verificar: P-45 punt 5] |

**Què depèn del 05b.** El nivell 2 de producció i la baixa de Cluber (025); els mòduls 02 i 06 (cobrar inscripcions i llicències); el 09 (comissions per activitat); el 08 (cobraments i pendents).

<a id="M05b-3-capacitats"></a>
## M05b-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | Pantalla (proposta) | Wireframe |
|---|---|---|---|---|
| C1 | Pagar un càrrec amb targeta | Soci; convidat | `/socis/pagaments/{càrrec}`; `/convidat/{enllaç}` | `socis.html#franja-estat` (botó «Paga ara»); pantalla de pagament: falta |
| C2 | Pagar amb Bizum | Soci; convidat | ídem | Falta |
| C3 | Pagar per transferència (referència, IBAN, import, copiar) | Soci; convidat | ídem | Falta |
| C4 | Veure l'estat i descarregar el rebut | Soci; convidat | `/socis/quotes`, `/socis/pagaments` | `socis.html#franja-estat` («Historial de pagaments») |
| C5 | Generar la remesa amb avís previ i descarregar el fitxer | Tresorer | `/gestio/pagaments/remeses` | Falta |
| C6 | Registrar retornats i decidir el reintent | Tresorer | `/gestio/pagaments/retornats` | Falta |
| C7 | Fer una devolució | Tresorer | Fitxa del pagament | Falta |
| C8 | Veure pagaments en curs, fallits i «a revisar» | Tresorer | `/gestio/pagaments` (i `/gestio/tresoreria/revisar` de la 04) | Patró de taula d'`admin.html` |
| C9 | Rebre l'avís previ i l'alternativa de pagament | Soci | Correu i `socis.html#avisos` | `socis.html#avisos` |

**Històries d'usuari**
- **HU-M05b-01.** Com a soci, vull pagar la quota amb targeta o Bizum sense sortir de l'app, per acabar en un minut.
- **HU-M05b-02.** Com a soci, vull veure clarament si el pagament està pendent, en curs, pagat o fallit, i què he de fer.
- **HU-M05b-03.** Com a soci, vull pagar per transferència amb les dades i la referència a punt per copiar, si no vull fer servir la targeta.
- **HU-M05b-04.** Com a soci, vull descarregar el rebut tan bon punt el pagament es confirma.
- **HU-M05b-05.** Com a convidat, vull pagar amb l'enllaç segur que he rebut sense crear cap compte (021).
- **HU-M05b-06.** Com a soci domiciliat, vull rebre l'avís previ amb la data, l'import i la referència del mandat abans de cada rebut.
- **HU-M05b-07.** Com a tresorer, vull generar la remesa de les quotes domiciliades i descarregar el fitxer per pujar-lo al banc.
- **HU-M05b-08.** Com a tresorer, vull registrar els rebuts retornats i que la plataforma proposi el reintent o l'alternativa segons el motiu.
- **HU-M05b-09.** Com a soci amb un rebut retornat, vull rebre un enllaç per pagar d'una altra manera.
- **HU-M05b-10.** Com a tresorer, vull fer una devolució total o parcial amb motiu i que la tresoreria ho reflecteixi sola.
- **HU-M05b-11.** Com a tresorer, vull que la plataforma em digui els pagaments que no quadren (import, càrrec o duplicat).

<a id="M05b-4-rols"></a>
## M05b-4 Rols i permisos

Llegenda com a [M01-4](#M01-4-rols).

| # | Acció | Visitant | Part. no soci | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Resp. comunicació | Dept. Història | Junta | Administrador | Resp. botiga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 | Pagar un càrrec seu (targeta, Bizum, transferència) | — | Propi (enllaç de convidat) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| B2 | Veure l'estat i el rebut dels seus pagaments | — | Propi (enllaç) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| B3 | Generar remeses, descarregar el fitxer i marcar-lo com a enviat | — | — | — | — | — | — | — | Sí | — | — | — | — | — |
| B4 | Registrar retornats i decidir el reintent | — | — | — | — | — | — | — | Sí | — | — | — | — | — |
| B5 | Fer devolucions | — | — | — | — | — | — | — | Sí | — | — | — | [A validar] | — |
| B6 | Veure tots els pagaments, en curs, fallits i «a revisar» | — | — | — | — | — | Consulta de les seves activitats (fase 2) [A validar] | — | Sí | — | — | — | Sí | — |
| B7 | Reenviar l'alternativa de pagament o l'enllaç de convidat | — | — | — | — | Sí (quotes) [A validar] | Sí (inscripcions, fase 2) [A validar] | — | Sí | — | — | — | Sí | — |
| B8 | Passar al nivell 2 (configuració) | — | — | — | — | — | — | — | — | — | — | — | Sí, amb l'autorització escrita de la junta | — |

**Per objecte.** Un soci o un convidat només pot pagar i veure els seus càrrecs; un enllaç de convidat només dona accés al càrrec o la inscripció que porta (V-02). **Un sol tresorer**: cap devolució ni remesa necessita una segona aprovació (P-48). El fitxer de la remesa (amb IBAN) només el pot descarregar el tresorer, i cada descàrrega queda al registre.

<a id="M05b-5-processos"></a>
## M05b-5 Processos pas per pas

**Wireframes existents:** `socis.html#franja-estat` (pendents, «Paga ara», «Tot al dia», «Historial de pagaments»), `socis.html#avisos` (avís previ), `publica.html` (convidat: «pagar amb un enllaç segur»), `admin.html` (entrada «Pagaments» i taula amb columnes «Import» i «Mètode», inclòs «Targeta (retornat)»). **Falten:** pantalla de pagament amb els quatre estats, espera de Bizum, transferència, rebut, remeses, retornats, devolució i llistat de pagaments (tasca T-M05b-02).

**Estats visibles (annex D de la spec 04)**
| Estat que veu el soci | Què vol dir | Estat a la 00 |
|---|---|---|
| **Pendent** | Encara no s'ha intentat pagar | Càrrec «pendent», sense intent en curs |
| **En curs** | S'espera la confirmació. Bizum: «Esperant confirmació a l'app del teu banc». Domiciliació: «Es cobrarà el [data] per domiciliació» | Càrrec «pendent», intent «en curs» o «enviat al banc» |
| **Pagat** | Confirmat al servidor | Càrrec «pagat» |
| **Fallit** | L'últim intent no s'ha completat; es pot tornar a provar o pagar d'una altra manera | Càrrec «pendent», intent «fallit» o «caducat» |
Cada estat amb símbol, text i color (030) i un missatge que diu què ha de fer.

### P-M05b-A Pagar amb targeta
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Soci o convidat | Tria «Paga ara» → «Targeta» |
| 2 | Sistema | Comprova que el càrrec és «pendent» i no té cap intent en curs (RN-M05b-04). Crea l'intent i, al servidor, l'ordre amb l'**import del càrrec** (mai del navegador) i una clau d'idempotència (`create_order`) |
| 3 | Soci | Escriu la targeta al **camp incrustat** o a la **pàgina del proveïdor** [A verificar quin dels dos: P-45 punt 4] i fa l'autenticació (3DS) amb el seu banc |
| 4 | Sistema | La tornada del navegador només mostra «Estem confirmant el pagament» (RN-71 de la 00) i consulta l'estat cada pocs segons amb HTMX |
| 5 | Proveïdor | Envia la notificació → P-M05b-D |
| 6 | Soci | Veu «Pagat» i el botó per descarregar el rebut |

### P-M05b-B Pagar amb Bizum
Com la targeta, amb aquestes diferències:
- Flux per **redirecció** (telèfon, clau i codi SMS a la pàgina del proveïdor) o per **sol·licitud a l'app del banc** (RTP) [A verificar: P-45]. L'app no rep el telèfon del pagador si va per redirecció.
- Estat «Esperant confirmació a l'app del teu banc».
- **Caducitat:** el temps el fixa el proveïdor o el banc [A verificar: P-45 punt 13]. A la pantalla, després de 15 minuts sense confirmació es mostra «No s'ha confirmat a temps» i es pot tornar a provar o pagar d'una altra manera (RN-M05b-07). Si després arriba una confirmació vàlida, s'accepta (RN-M05b-08).
- **Abandonament:** si el soci tanca la pantalla, el càrrec continua pendent; en tornar veu l'estat real.

### P-M05b-C Pagar per transferència
1. El soci tria «Transferència». La plataforma mostra l'**IBAN del club** (configuració), l'**import** i la **referència** del càrrec (`treasury.transfer_reference`), cadascun amb un botó per copiar, i el text «Escriu la referència al concepte».
2. L'estat passa a «En curs: esperant la transferència». No hi ha notificació: la prova és l'extracte.
3. El tresorer concilia la línia a la 04 (P-M04-E). En confirmar-la, el càrrec passa a «pagat» i el soci rep el rebut.
4. Si en 30 dies no ha arribat, l'estat torna a «Pendent» i s'envia un recordatori [A validar: tresorer] (arquitectura §4.6, «caducitat»).

### P-M05b-D Notificació del proveïdor (arquitectura §4.2)
| Pas | Què passa |
|---|---|
| 1 | L'endpoint verifica la firma o l'empremta (`verify_notification`) i, si el proveïdor la dona, la IP. Si falla: error, no es processa, registre |
| 2 | Desa l'esdeveniment per identificador únic; si ja existia, respon correcte i no fa res |
| 3 | Respon de seguida; el processament el fa la cua |
| 4 | La tasca comprova import, moneda i càrrec de l'ordre. Si no coincideixen → intent «a revisar» i avís al tresorer |
| 5 | Aplica només transicions vàlides: èxit → intent «pagat», càrrec «pagat» (00), `treasury.record_income`, comissió si es coneix, `members.on_fee_paid` si és una quota, rebut, correu |
| 6 | Fallada o caducitat → intent «fallit» o «caducat»; el càrrec continua «pendent» |
| 7 | **Xarxa de seguretat:** una tasca diària consulta les ordres en curs de més d'una hora (`get_order`) [A verificar que l'API ho permet] |

### P-M05b-E Remesa de quotes domiciliades
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Tresorer | Tria el període i la **data de cobrament**. Veu la previsualització: rebuts (quotes «pendent» amb mandat actiu i sense cap altre intent en curs), import total i socis exclosos amb el motiu | `/gestio/pagaments/remeses` |
| 2 | Sistema | Comprova que la data de cobrament deixa temps per a l'**avís previ** (RN-M05b-11) i que el nivell 2 està actiu (RN-M05a-11) | — |
| 3 | Tresorer | Confirma. Es crea la remesa en esborrany, un rebut per quota (amb identificador d'extrem a extrem únic) i un intent «enviat al banc» per càrrec | — |
| 4 | Sistema | Envia l'**avís previ** a cada deutor: data, import, referència del mandat i identificador de creditor (017) | Correu i `socis.html#avisos` |
| 5 | Tresorer | Quan toca presentar-la [A verificar: termini del banc], **descarrega el fitxer pain.008**. El fitxer es genera en aquell moment amb els IBAN desxifrats (`mandates_for_remittance`), no es desa, i se'n registra l'empremta | `/gestio/pagaments/remeses/{id}` |
| 6 | Tresorer | El puja a la banca en línia del banc, l'esborra del dispositiu (norma de la 044) i marca la remesa com a «enviada al banc», confirmant l'esborrat | — |
| 7 | Sistema | Registra la remesa a la 04 com a liquidació pendent del trànsit «Remeses SEPA» (RN-T24) | — |
| 8 | Tresorer | Quan arriba l'abonament a l'extracte, el concilia (P-M04-F): cada càrrec passa a «pagat», ingrés i comissió per rebut [A verificar: banc], `members.on_fee_paid`, `payments.record_collection`, rebut al soci | `/gestio/tresoreria/conciliacio` |

### P-M05b-F Rebut retornat, reintent i alternativa
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Tresorer | Registra el retorn d'un rebut a partir de la línia de càrrec de l'extracte o del fitxer de retornats del banc [A verificar format: P-45 punt 5], amb el codi de motiu si n'hi ha | `/gestio/pagaments/retornats` |
| 2 | Sistema | Càrrec «pagat → retornat» (RN-67 de la 00), `treasury.record_return` amb la comissió de retorn si n'hi ha, `members.on_fee_returned` (avís al tresorer; l'impagat és manual, 040) | — |
| 3 | Sistema | Segons el motiu (RN-M05b-15): proposa un **reintent** a la remesa següent, o envia l'**alternativa de pagament** (enllaç per pagar amb targeta, Bizum o transferència), o marca el mandat com a invàlid i demana un mandat nou | — |
| 4 | Tresorer | Confirma o canvia la proposta | — |
| 5 | Sistema | En reintentar o enviar l'alternativa, el càrrec passa «retornat → pendent» amb motiu (RN-M05b-14) i el soci rep el correu | — |

### P-M05b-G Devolució iniciada pel club
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Tresorer | Obre el pagament, tria «Devolució», escriu import (total o parcial) i motiu |
| 2 | Sistema | Comprova que la suma de devolucions no supera l'import cobrat (RN-T11) |
| 3 | Sistema | **Targeta:** `refund` per l'adaptador amb clau d'idempotència. **Bizum:** igual si el proveïdor ho admet [A verificar: P-45 punt 7]; si no, transferència des del banc. **Transferència i domiciliació:** el tresorer la fa des del banc i la registra amb justificant |
| 4 | Sistema | `treasury.record_refund`; si és total, càrrec «pagat → anul·lat» (RN-67); si és parcial, el càrrec continua «pagat» (RN-M05b-17); correu al pagador |

### P-M05b-H Liquidació del proveïdor
Quan el proveïdor informa d'un abonament agrupat (notificació o fitxer [A verificar: P-45 punt 9]), el 05b crida `treasury.record_settlement` amb els pagaments que conté. Si no n'informa, el tresorer fa el casament a la 04 per període (RN-T21).

### P-M05b-I Pas al nivell 2 (025)
1. 05b acabat i provat amb el proveïdor en mode de proves i remeses inventades validades contra l'esquema del banc.
2. Portes 0 a 3 completes (B6, E5, E6, F1-F7, H2, H5 i la part «N2» de B5, B8, E3 i E4).
3. Autorització **expressa i per escrit** de la junta.
4. Claus de producció del proveïdor i `PAYMENTS_LIVE_CHARGES_ALLOWED` = cert.
5. Criteri per deixar Cluber (014, 020).

<a id="M05b-6-entitats"></a>
## M05b-6 Entitats i camps

App `payments` (la mateixa del 05a).

### PaymentAttempt (intent de pagament; amplia el «pagament» de la 00)
| Camp | Tipus | Restriccions |
|---|---|---|
| `charge` | FK càrrec (00, PROTECT) | — |
| `method` | `card`, `bizum`, `transfer`, `direct_debit`, `saved_card` | Domiciliació només per a quotes (RN-69) |
| `amount_cents` | `PositiveIntegerField` | = import del càrrec en crear-lo |
| `status` | `created`, `in_progress`, `sent_to_bank`, `paid`, `failed`, `expired`, `abandoned`, `to_review`, `cancelled` | Transicions de RN-M05b-03 |
| `provider_code`, `provider_order_id` | null | Únic `(provider_code, provider_order_id)` |
| `idempotency_key` | `UUIDField` | Únic |
| `expires_at` | null | Bizum i transferència |
| `guest_link` | FK enllaç de convidat (00) null | Si l'ha iniciat un convidat |
| `started_by` | FK compte null | Null per a convidat o sistema |
| `review_reason` | `TextField` | Per a `to_review` |
**Índex únic parcial:** un sol intent `in_progress` o `sent_to_bank` per càrrec (RN-M05b-04). Un sol intent `paid` per càrrec.

### DirectDebitRemittance (remesa)
`period`, `collection_date`, `status` (`draft`, `notified`, `sent_to_bank`, `settled`, `cancelled`), `item_count`, `total_cents`, `file_hash` (empremta de l'últim fitxer generat), `file_format` (`pain.008.001.xx` [A verificar: banc]), `created_by`, `sent_marked_by`, `sent_marked_at`, `settlement` (FK ProviderSettlement de la 04, null).

### DirectDebitItem (rebut domiciliat)
| Camp | Tipus | Restriccions |
|---|---|---|
| `remittance` | FK | — |
| `attempt` | OneToOne PaymentAttempt | — |
| `mandate` | FK SepaMandate (05a) | Actiu en crear la remesa |
| `amount_cents` | `PositiveIntegerField` | — |
| `end_to_end_id` | `CharField(35)` | Únic |
| `attempt_number` | `PositiveSmallIntegerField` | 1 = primer; 2 = reintent (RN-M05b-15) |
| `prenotified_at` | `DateTimeField` null | Avís previ enviat |
| `status` | `included`, `excluded`, `collected`, `returned` | — |
| `return_reason_code` | `CharField(4)` null | Codi del banc [A verificar quins arriben] |
| `returned_on` | null | — |

### Refund (devolució)
`attempt` (FK, el pagament original), `amount_cents`, `reason`, `channel` (`provider`, `bank_transfer`), `provider_refund_id` null, `status` (`requested`, `done`, `failed`), `created_by`, `evidence_file` (FK fitxer privat de la 00, null; justificant de la transferència). La suma de `done` ≤ import pagat (RN-T11).

### Receipt (rebut)
`attempt` (OneToOne, només `paid`), `number` (`CharField(20)`, únic; format `R-AAAA-NNNNNN`), `issued_at`. El PDF es genera a demanda (annex B de la 00) amb referència, concepte, import, departament, data i mètode. Una devolució total anul·la el rebut amb una nota, no l'esborra.

### PaymentSettings (valors configurables, amb registre)
`bizum_ui_timeout_minutes` (15), `transfer_reminder_days` (30), `prenotification_days` (14), `max_direct_debit_attempts` (2), `safety_net_age_minutes` (60). Els valors inicials són propostes de [M05b-7](#M05b-7-regles).

**Migracions:** reversibles; cap camp amb IBAN ni dades de targeta (prova automàtica, excepte `MandateBankAccount` del 05a).

<a id="M05b-7-regles"></a>
## M05b-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M05b-01 | Mètodes per càrrec: quota → domiciliació, targeta, Bizum, transferència; inscripció i llicència → targeta, Bizum, transferència | 017; RN-69 |
| RN-M05b-02 | L'import de l'ordre el fixa el servidor a partir del càrrec. El concepte enviat al proveïdor porta el tipus, el període i el número de soci o la referència, mai el nom; l'identificador de client és intern, mai el DNI ni el correu | RNF-T4; `integracio-paylands.md` §2 |
| RN-M05b-03 | Transicions de l'intent: `created → in_progress → paid / failed / expired / abandoned / to_review`; `created → sent_to_bank → paid / failed`; `paid` no torna enrere (les correccions són devolucions o retorns) | Proposta |
| RN-M05b-04 | Un càrrec té com a molt un intent en curs. Començar-ne un de nou marca l'anterior com a `abandoned` si el proveïdor permet cancel·lar-lo [A verificar]; si no, el nou es bloqueja fins que l'anterior acabi o caduqui | Proposta |
| RN-M05b-05 | Un càrrec només passa a «pagat» per una notificació verificada del proveïdor, una conciliació confirmada pel tresorer (transferència i remesa) o, quan es resolgui P-12, un registre manual. Mai pel navegador | RN-71 de la 00 |
| RN-M05b-06 | Notificacions: verificació, desament per identificador únic, resposta immediata, processament a la cua, comprovació d'import, moneda i càrrec, transicions vàlides, registre (arquitectura §4.2). Les crides sortints porten clau d'idempotència | ARQ §4.2; CLAUDE.md |
| RN-M05b-07 | Bizum: a la pantalla, 15 minuts sense confirmació → «No s'ha confirmat a temps»; la caducitat real la fixa el proveïdor [A verificar: P-45 punt 13] | Annex D; proposta |
| RN-M05b-08 | Una confirmació vàlida que arriba tard s'accepta si el càrrec continua «pendent». Si el càrrec ja s'havia pagat per una altra via, l'intent passa «a revisar» com a **pagament duplicat** i el tresorer en fa la devolució | Proposta (LT6 de la 04) |
| RN-M05b-09 | Transferència: referència única per càrrec (RN-T20); el càrrec passa a «pagat» només en conciliar (RN-T18); sense resposta en 30 dies, recordatori [A validar: tresorer] | ARQ §4.6 |
| RN-M05b-10 | Remesa: només quotes «pendent» amb mandat actiu i sense intent en curs; una quota no pot ser en dues remeses obertes; només amb el nivell 2 actiu | 017; RN-M05a-11 |
| RN-M05b-11 | Avís previ a cada deutor almenys **14 dies naturals** abans de la data de cobrament, si el text del mandat no fixa un termini més curt [A verificar: banc; A validar: tresorer]. Porta data, import, referència del mandat i identificador de creditor | 017; reglament SEPA |
| RN-M05b-12 | El fitxer pain.008 es genera a demanda, no es desa; se'n registra l'empremta i qui l'ha descarregat. La versió de l'esquema i el termini de presentació són del banc [A verificar: P-45 punt 5] | 044 |
| RN-M05b-13 | Una remesa enviada es concilia a la 04 com a liquidació del trànsit «Remeses SEPA» (RN-T24). Els càrrecs passen a «pagat» en confirmar la conciliació | RN-T24; RN-71 |
| RN-M05b-14 | **Després de «retornat»** (Q-22 de la 00): el càrrec passa «retornat → pendent» quan el tresorer confirma un reintent o l'alternativa de pagament, amb motiu i registre. El retorn i la seva comissió ja són a la tresoreria; el nou pagament genera un ingrés nou | **Aprovada:** [048](decisions/048-reobrir-carrec-retornat.md) |
| RN-M05b-15 | Reintent controlat segons el codi de motiu [A verificar: banc, quins codis arriben]: **fons insuficients** (per exemple AM04) → un reintent a la remesa següent; **refús del deutor** (per exemple MS02, MD06) → cap reintent, alternativa de pagament; **compte tancat o sense mandat** (per exemple AC04, MD01) → mandat «bloquejat», alternativa i petició de mandat nou. Màxim 2 intents per domiciliació per càrrec (`max_direct_debit_attempts`). Els codis concrets que arriben, [A verificar: banc] | 017; **aprovada i validada pel tresorer** |
| RN-M05b-16 | Qui assumeix la comissió de retorn: el club, a «General / Quotes de socis» (013), mentre la junta no decideixi una altra cosa [A validar: junta] | 013; 017 punt 4 |
| RN-M05b-17 | Devolució total → càrrec «anul·lat» (RN-67) i rebut anul·lat; devolució parcial → el càrrec continua «pagat» i el rebut porta la devolució anotada. La comissió no es recupera; la suma de devolucions no supera l'import (RN-T11) | RN-67; 013; Q-22 |
| RN-M05b-18 | Conseqüències d'un retorn al soci: avís al tresorer (`members.on_fee_returned`); l'impagat el marca el tresorer a mà (040). Mentre el càrrec no sigui «pagat», el carnet deixa de ser vàlid per RN-M01-18 [A validar: junta] | 040; M01 |
| RN-M05b-19 | Rebut immediat en confirmar-se el pagament: número únic `R-AAAA-NNNNNN`, referència, concepte, import, departament, data i mètode. És un rebut, no una factura (P-47) | Annex D |
| RN-M05b-20 | Targeta guardada: cobrament sense intervenció del soci només si el proveïdor ho admet; si el proveïdor demana autenticació, el soci rep un enllaç i el càrrec continua pendent [A verificar] | `integracio-paylands.md` §6 |
| RN-M05b-21 | Cap pagament parcial ni saldo a favor; no es fa servir `PARTIAL_AUTHORIZATION` | QT-05 |
| RN-M05b-22 | Un càrrec amb un intent en curs o enviat al banc no es pot anul·lar fins que l'intent acabi | Proposta |
| RN-M05b-23 | Nivell 2: `PAYMENTS_LIVE_CHARGES_ALLOWED` = cert només amb l'autorització escrita de la junta i les portes 0 a 3 completes | 025; 042 |

**Exemples numèrics**
- **Comissió de targeta (il·lustrativa):** amb la tarifa pública de l'opció (d) de la 043 (1,80 % + 0,25 €), una quota de **9000** cèntims té una comissió de 162 + 25 = **187** (1,87 €) i una de **3500**, 63 + 25 = **88** (0,88 €). La tarifa real depèn del proveïdor triat [A verificar].
- **Remesa (RN-M05b-10, RN-T24):** 130 rebuts (90 × 3500 + 40 × 9000) = **675.000 cèntims**. Amb una comissió per rebut *c* [A verificar: banc], la comissió total és 130 × *c* a «General / Quotes de socis».
- **Avís previ (RN-M05b-11):** data de cobrament D → l'avís ha de sortir com a molt tard D − 14 dies; si el tresorer tria una data que no ho permet, la plataforma no deixa confirmar la remesa.
- **Retornats (RN-M05b-15):** 2 retorns, un de 3500 per fons insuficients i un de 9000 per refús del deutor → sortides de **12.500** al trànsit, més la comissió de retorn [A verificar: banc]. El primer va a la remesa següent (intent 2 de 2); el segon rep l'alternativa de pagament.
- **Devolucions (RN-M05b-17):** inscripció de 12.000 pagada amb targeta; devolució parcial de 4000 → el càrrec continua «pagat»; devolució de 8000 més → suma 12.000, càrrec «anul·lat»; una tercera devolució → rebutjada.
- **Duplicat (RN-M05b-08):** quota de 9000 pagada per transferència i, més tard, confirmació vàlida d'un Bizum de 9000 → intent «a revisar» i devolució de 9000 del Bizum; la comissió del Bizum es queda com a despesa (013).

<a id="M05b-8-serveis"></a>
## M05b-8 Serveis i interfícies (contracte)

**Ofereix**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `payments.start_payment(charge, method, actor)` | càrrec, mètode, compte o enllaç de convidat | `PaymentStart(attempt_id, kind: redirect / iframe / transfer_details, url?, reference?, iban?, amount_cents)` | `ChargeNotPayable`, `AttemptInProgress`, `MethodNotAllowed`, `LiveChargesNotAllowed` | Pantalles de pagament; 02 i 06 (fase 2) |
| `payments.payment_status(charge)` | càrrec | estat visible (pendent, en curs, pagat, fallit) i missatge | — | Pantalles; 01 |
| `payments.process_notification(event_id)` | esdeveniment desat | resultat | — | Cua (cridat per l'endpoint del 05a) |
| `payments.build_remittance(period, collection_date, actor)` | — | remesa en esborrany amb previsualització | `PrenotificationTooLate`, `LiveChargesNotAllowed` | Tresorer |
| `payments.remittance_file(remittance, actor)` | — | contingut pain.008 (en memòria) | `NotAllowed` | Tresorer |
| `payments.mark_remittance_sent(remittance, actor)` | — | — | — | Tresorer |
| `payments.register_return(item, reason_code, statement_line=None)` | — | proposta de reintent o alternativa | `NotCollected` | Tresorer |
| `payments.refund(attempt, amount_cents, reason, actor)` | — | `Refund` | `RefundExceedsPaid` | Tresorer |
| `payments.receipt_pdf(attempt)` | — | PDF a demanda | `NotPaid` | Soci, convidat, tresorer |

**Consumeix**
| Servei | Mòdul | Per a què |
|---|---|---|
| `charges.mark_paid`, `charges.mark_returned`, `charges.reopen_returned(charge, reason)`, `charges.cancel` | 00 | Transicions del càrrec (la tercera és RN-M05b-14) |
| `guest_links.resolve(token)` | 00 | Pagaments de convidats |
| `treasury.record_income`, `record_fee`, `record_refund`, `record_return`, `record_settlement`, `transfer_reference` | 04 | Tresoreria |
| `members.on_fee_paid`, `members.on_fee_returned` | 01 | Estat del soci i avís de retorn |
| `payments.provider()`, `fee_payment_method`, `active_mandate`, `mandates_for_remittance`, `record_collection` | 05a | Adaptador i mandats |
| `files.render_private_pdf`, `mail.send`, `notices.post`, `audit.record`, `permissions.require` | 00 | Rebut, avisos, registre, permisos |

**Rutes.** Compte personal: `/socis/pagaments`, `/socis/pagaments/{càrrec}`, `/socis/pagaments/{intent}/estat` (HTMX), `/socis/pagaments/{intent}/rebut`. Convidat (públic declarat, amb enllaç): `/convidat/{enllaç}`. Administració: `/gestio/pagaments`, `/gestio/pagaments/remeses`, `/gestio/pagaments/remeses/{id}`, `/gestio/pagaments/retornats`. Notificacions: l'endpoint del 05a.

<a id="M05b-9-criteris"></a>
## M05b-9 Criteris d'acceptació i casos límit

**Targeta i Bizum**
- **CA-M05b-01** Donat un càrrec pendent, quan el soci tria targeta, llavors l'ordre es crea al servidor amb l'import del càrrec i la pantalla mostra el camp o la pàgina del proveïdor; cap camp de targeta és un formulari propi.
- **CA-M05b-02** Donat la tornada del navegador amb «ok», quan es mostra, llavors diu «Estem confirmant el pagament» i el càrrec no canvia.
- **CA-M05b-03** Donat una notificació vàlida d'èxit, quan es processa, llavors l'intent i el càrrec passen a «pagat», hi ha un ingrés (CA-T03.1), el rebut es pot descarregar i el soci rep el correu.
- **CA-M05b-04** Donat la mateixa notificació repetida o desordenada, quan es processa, llavors no hi ha cap segon pagament, ingrés ni correu.
- **CA-M05b-05** Donat una notificació amb un import o un càrrec que no coincideixen, quan es processa, llavors l'intent queda «a revisar» i s'avisa el tresorer.
- **CA-M05b-06** Donat un Bizum sense confirmar durant 15 minuts, quan el soci mira la pantalla, llavors veu «No s'ha confirmat a temps» i pot tornar a provar; el càrrec continua pendent.
- **CA-M05b-07** Donat una confirmació tardana d'un càrrec ja pagat per una altra via, quan es processa, llavors l'intent queda «a revisar» com a duplicat.
- **CA-M05b-08** Donat un intent en curs, quan se'n vol començar un altre, llavors s'aplica RN-M05b-04.
- **CA-M05b-09** Donat un enllaç de convidat vàlid, quan el convidat paga, llavors el pagament segueix les mateixes regles i el càrrec queda lligat al seu perfil (RN-33 de la 00); un càrrec pagat només mostra l'estat i el rebut (CA-02.4 de la 00).

**Transferència**
- **CA-M05b-10** Donat «Transferència», quan es mostra, llavors hi ha l'IBAN del club, l'import i la referència, cadascun copiable, i l'estat «esperant la transferència».
- **CA-M05b-11** Donat la conciliació confirmada (CA-T10.1), quan acaba, llavors el soci veu «Pagat» i el rebut.

**Remeses**
- **CA-M05b-12** Donat 130 quotes pendents amb mandat actiu i 20 sense, quan es previsualitza la remesa, llavors té 130 rebuts, 675.000 cèntims (amb les quotes de l'exemple) i la llista dels 20 exclosos amb motiu.
- **CA-M05b-13** Donat una data de cobrament a menys de 14 dies, quan es confirma, llavors es rebutja (RN-M05b-11).
- **CA-M05b-14** Donat una remesa confirmada, quan s'envien els avisos previs, llavors cada deutor en rep un amb data, import, referència del mandat i identificador de creditor, i cap correu porta l'IBAN complet.
- **CA-M05b-15** Donat la descàrrega del fitxer, quan es genera, llavors valida contra l'esquema pain.008 del banc [A verificar versió], no es desa al disc ni a l'emmagatzematge, i la descàrrega queda al registre amb l'empremta.
- **CA-M05b-16** Donat el nivell 1, quan es vol generar una remesa, llavors es rebutja.
- **CA-M05b-17** Donat l'abonament conciliat (CA-T16.1), quan acaba, llavors els 130 càrrecs són «pagat», cada mandat té `last_collection_on` i els socis reben el rebut.

**Retornats i devolucions**
- **CA-M05b-18** Donat un rebut retornat per fons insuficients, quan es registra, llavors el càrrec és «retornat», hi ha la sortida i la comissió de retorn, el tresorer rep l'avís i es proposa un reintent; en confirmar-lo, el càrrec torna a «pendent» amb motiu.
- **CA-M05b-19** Donat un segon retorn del mateix càrrec, quan es registra, llavors no es proposa cap altre reintent (màxim 2) i s'envia l'alternativa de pagament.
- **CA-M05b-20** Donat un retorn per compte tancat o sense mandat, quan es registra, llavors el mandat passa a «bloquejat» i el soci rep l'alternativa i la petició de mandat nou.
- **CA-M05b-21** Donat un pagament de 12.000, quan es fan devolucions de 4000 i de 8000, llavors el càrrec passa a «anul·lat» a la segona i una tercera es rebutja.
- **CA-M05b-22** Donat una devolució amb targeta, quan es crida l'adaptador dues vegades amb la mateixa clau, llavors només hi ha una devolució.

**Nivell, permisos i dades**
- **CA-M05b-23** Donat cada cel·la de [M05b-4](#M05b-4-rols), quan el rol prova l'acció, llavors el resultat coincideix.
- **CA-M05b-24** Donat qualsevol petició del navegador, quan intenta posar un càrrec en «pagat», llavors es rebutja (CA-15.7 de la 00).
- **CA-M05b-25** Donat una revisió del model, quan s'executa, llavors cap camp del 05b guarda dades de targeta ni IBAN.

**Casos límit**
| # | Cas | Comportament |
|---|---|---|
| L-M05b-01 | El proveïdor no envia la notificació | La xarxa de seguretat consulta l'ordre ([A verificar]); si no es pot, «a revisar» |
| L-M05b-02 | El soci paga amb targeta una quota que ja era a una remesa enviada | Bloquejat per RN-M05b-04 (intent «enviat al banc»); si passa igualment, duplicat i devolució |
| L-M05b-03 | El soci revoca el mandat després de l'avís previ | Avís al tresorer (RN-M05a-09); si el banc ho permet, s'exclou el rebut [A verificar] |
| L-M05b-04 | Una remesa sencera la rebutja el banc | Remesa «cancel·lada», intents «fallit», càrrecs pendents; es pot tornar a generar |
| L-M05b-05 | El banc abona la remesa menys els retornats immediats | La liquidació «a revisar»; el tresorer registra els retornats i la concilia |
| L-M05b-06 | Contracàrrec d'una targeta | Com un retorn: càrrec «retornat», sortida i avís (arquitectura §4.4) [A verificar com ho notifica el proveïdor] |
| L-M05b-07 | Soci donat de baixa amb un rebut a la remesa | El rebut es manté si ja s'ha enviat; la quota segueix RN-M01-20 |
| L-M05b-08 | Esborrat RGPD amb pagaments | Pagaments i rebuts bloquejats fins al termini legal (028) |
| L-M05b-09 | Cap càrrec pendent | «Tot al dia» (`socis.html#franja-estat`) |
| L-M05b-10 | Cap remesa encara | «Encara no has generat cap remesa» i el nombre de socis domiciliats |

<a id="M05b-10-tasques"></a>
## M05b-10 Tasques (per dependències, sense dates)

| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M05b-01 | Transicions de càrrec que falten a la 00 (`mark_returned`, `reopen_returned` de RN-M05b-14) | S | `apps/core/charges.py` | T-M01-09; aprovació de RN-M05b-14 | CA-M05b-18 |
| T-M05b-02 | Wireframes: pantalla de pagament amb els quatre estats, Bizum, transferència, rebut, remeses, retornats, devolució | M | `design/wireframes/` | — | Revisats; contrast i estats amb símbol |
| T-M05b-03 | Model `PaymentAttempt` i transicions | M | `apps/payments/models.py` | T-M05a-08 | RN-M05b-03, 04 |
| T-M05b-04 | `start_payment` amb targeta i Bizum sobre l'adaptador; tornada i consulta d'estat amb HTMX | L | `apps/payments/checkout.py`, vistes | T-M05b-03, T-M05a-03 | CA-M05b-01, 02, 08 |
| T-M05b-05 | Processament de notificacions i xarxa de seguretat | L | `apps/payments/processing.py`, tasques | T-M05b-04, T-M05a-04, T-M04-05 | CA-M05b-03 a 07 |
| T-M05b-06 | Transferència: pantalla i enllaç amb la conciliació de la 04 | S | vistes | T-M04-10, T-M04-12 | CA-M05b-10, 11 |
| T-M05b-07 | Rebut amb número i PDF | M | `apps/payments/receipts.py` | T-M05b-05, T-M01-10 | RN-M05b-19 |
| T-M05b-08 | Pagaments de convidats amb l'enllaç de la 00 | M | vistes | T-M05b-04; enllaços de convidat de la 00 | CA-M05b-09 |
| T-M05b-09 | Remesa: selecció, previsualització, avís previ | M | `apps/payments/remittances.py` | T-M05a-08, T-M05b-03 | CA-M05b-12, 13, 14, 16 |
| T-M05b-10 | Fitxer pain.008 i validació contra l'esquema | L | `apps/payments/sepa_xml.py` | T-M05b-09; versió i mostra del banc (P-45 punt 5) | CA-M05b-15 |
| T-M05b-11 | Remesa com a liquidació a la 04 i conciliació | M | `remittances.py` | T-M05b-10, T-M04-13 | CA-M05b-17; CA-T16.1 |
| T-M05b-12 | Retornats, codis de motiu, reintent i alternativa | L | `apps/payments/returns.py` | T-M05b-11, T-M05b-01 | CA-M05b-18, 19, 20 |
| T-M05b-13 | Devolucions (proveïdor i banc) | M | `apps/payments/refunds.py` | T-M05b-05, T-M04-07 | CA-M05b-21, 22 |
| T-M05b-14 | Liquidacions del proveïdor cap a la 04 | M | `apps/payments/settlements.py` | T-M04-13; format (P-45 punt 9) | CA-T11.x |
| T-M05b-15 | Cobrament amb targeta guardada (condicional) | M | `checkout.py` | T-M05a-12 | RN-M05b-20 |
| T-M05b-16 | Llistat de pagaments i «a revisar» per al tresorer | M | vistes | T-M05b-05 | Proves de permisos |
| T-M05b-17 | Dades de prova inventades: càrrecs, notificacions, remeses, retornats | S | `apps/payments/fixtures/` | T-M05b-12 | Es carreguen amb una ordre |
| T-M05b-18 | Proves de principi a fi amb `FakeProvider` i, quan n'hi hagi, amb l'entorn de proves del proveïdor | L | `tests/` | T-M05b-05 a T-M05b-14 | Totes en verd |
| T-M05b-19 | Portes del nivell 2 (B5, B6, B8, E3 a E6, F1-F7, H2, H5) | L | — | T-M05b-18 | Checklist revisada |
| T-M05b-20 | Guia del tresorer (remeses, retornats, devolucions) i ajuda per als socis | S | `docs/` | T-M05b-16 | Revisades |

<a id="M05b-11-proves"></a>
## M05b-11 Pla de proves

- **Unitàries (B1):** transicions de l'intent i del càrrec; comprovació d'import i càrrec; regles de reintent per codi; límit de devolucions; termini de l'avís previ; numeració de rebuts.
- **Notificacions (C9):** falses, repetides, desordenades, tardanes, d'un càrrec ja pagat, amb import diferent; xarxa de seguretat.
- **Remeses:** fitxer contra l'esquema del banc [A verificar]; 0, 1 i 130 rebuts; caràcters especials en noms de titulars; cap IBAN fora del fitxer; nivell 1 sense remeses.
- **Integració:** de «Paga ara» al rebut amb `FakeProvider`; remesa → conciliació → retorn → reintent → pagament amb targeta; convidat.
- **Permisos (B4):** una prova per cel·la de [M05b-4](#M05b-4-rols); un convidat no veu altres càrrecs.
- **Contracte:** serveis de [M05b-8](#M05b-8-serveis) i crides a la 04.
- **Accessibilitat i dispositius (B5, B8 completes):** els quatre estats amb símbol, text i color; anuncis d'estat amb `role="status"`; pagament al mòbil amb xarxa lenta (B6).
- **Dades:** només inventades; targetes i telèfons de prova del proveïdor (per exemple, els de Bizum de la documentació de Paylands [A verificar]).

<a id="M05b-12-seguretat"></a>
## M05b-12 Seguretat i RGPD

- **Targetes:** mai a l'app; camp o pàgina del proveïdor; CSP que només permet el domini del proveïdor.
- **Confirmació al servidor:** firma o empremta, IP, idempotència, comprovació d'import; mai pel navegador.
- **Fitxer de remesa:** conté IBAN; generat a demanda, no desat, descàrrega amb sessió d'administració i TOTP, empremta i registre. Norma d'esborrat del dispositiu del tresorer: [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md), ampliació (el mateix dia, sense correu ni carpetes sincronitzades); en marcar la remesa com a enviada, el tresorer confirma que l'ha esborrat. **Millora opcional (044):** l'enllaç de descàrrega és d'un sol ús i caduca [A validar: tresorer, quant de temps].
- **Secrets:** claus del proveïdor per entorn en variables d'entorn; claus de producció només al nivell 2.
- **Enllaços de convidat:** caducitat, limitació d'intents i testimoni que no apareix als registres (00).
- **Mínim de dades:** el proveïdor no rep noms ni DNI; els conceptes porten el número de soci o la referència.
- **Conservació i esborrat:** pagaments, rebuts i remeses bloquejats fins al termini legal (028) [A validar: gestoria, Q-14].
- **Bizum i Hisenda:** els bancs informen l'Agència Tributària dels cobraments per Bizum (arquitectura §4.5); a comentar amb la gestoria [A verificar: gestoria].
- **Dades dins la UE:** proveïdor i subencarregats (035) [A verificar: P-45 punt 3].

<a id="M05b-13-riscos"></a>
## M05b-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| Proveïdor no confirmat (P-44) | Alt per a targeta i Bizum | Adaptador i `FakeProvider`; transferència sempre disponible | Tresorer (amb el banc) |
| El banc no admet remeses pain.008 o demana un altre format | Alt per a la domiciliació | P-45 punt 5; si no, alternativa 2 de la 044 | Banc |
| Liquidacions sense detall | Mitjà | Casament per període (RN-T21) | PaynoPain |
| Primera remesa abans d'acabar el 05b (P-29) | Alt | Aquella remesa la fa Cluber; la de la plataforma, la següent | Tresorer |
| Reintents i conseqüències dels retornats no fixats | Mitjà | Propostes RN-M05b-14 a 18, configurables | Tresorer i junta |
| El carnet deixa de ser vàlid amb un retorn | Mitjà (queixes de socis) | RN-M05b-18 a validar; alternativa de pagament ràpida | Junta |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M05b-01 | Camp incrustat o redirecció (P-45 punt 4) | Tots dos suportats per l'adaptador | PaynoPain |
| S-M05b-02 | Bizum per redirecció o RTP; caducitat (P-45 punt 13) | Redirecció; 15 minuts a la pantalla | PaynoPain |
| S-M05b-03 | Consulta d'ordres per a la xarxa de seguretat | Hi és | PaynoPain |
| S-M05b-04 | Devolucions de Bizum per API (P-45 punt 7) | No; transferència des del banc | PaynoPain |
| S-M05b-05 | Versió pain.008, terminis de presentació, comissions per rebut i per retornat, fitxer de retornats (P-45 punt 5) | pain.008 estàndard; retornats a l'extracte | Banc |
| S-M05b-06 | Termini de l'avís previ (RN-M05b-11) | 14 dies naturals | Banc i tresorer |
| S-M05b-07 | Regles de reintent per codi i màxim d'intents (RN-M05b-15) | **Resolt:** validades pel tresorer | — |
| S-M05b-08 | Comissió de retorn (RN-M05b-16) | La paga el club | Junta |
| S-M05b-09 | Carnet amb una quota retornada (RN-M05b-18) | No vàlid fins que es pagui | Junta |
| S-M05b-10 | Recordatori de transferència (30 dies) | Sí | Tresorer |
| S-M05b-11 | Format del número de rebut | `R-AAAA-NNNNNN` | Tresorer i gestoria |
| S-M05b-12 | Què s'ha de facturar (P-47) | Rebut, no factura | Gestoria |
| S-M05b-13 | Qui pot reenviar l'alternativa (B7) | Tresorer i secretaria (quotes) | Junta |

**Revisió de dubtes (aplicada a mà)**
1. **«Retornat» no tenia sortida a la 00 (Q-22).** La proposta RN-M05b-14 afegeix «retornat → pendent» amb motiu. La 00 delega aquesta part a la 05b, però és un canvi d'estat de diners: s'ha d'aprovar explícitament. Propietari: responsable del projecte i tresorer.
2. **Amb la remesa pròpia no hi ha notificació del proveïdor:** el «pagat» d'una domiciliació depèn de la conciliació de l'abonament (RN-M05b-13). Si el tresorer triga a conciliar, el soci veu «en curs» uns dies més. Propietari: tresorer.
3. **Retorns després del «pagat»:** és el cas normal amb remeses (el banc abona i després carrega els retornats). Per això el retorn és «pagat → retornat», com preveu RN-67. Propietari: cap (coherent).
4. **El carnet depèn de la quota pagada (RN-M01-18) però l'impagat és manual (040):** un retorn fa el carnet no vàlid abans que el tresorer marqui res. Pot ser el que vol el club o no. Propietari: junta.
5. **Pagament duplicat** (transferència i Bizum alhora): l'app no ho pot evitar del tot perquè la transferència no té notificació. Es detecta i es retorna (RN-M05b-08). Propietari: tresorer.
6. **El fitxer de remesa surt de la plataforma amb IBAN en clar** cap al dispositiu del tresorer. És inevitable si el banc no té API; la norma d'esborrat és a l'ampliació de la 044. Propietari: tresorer.
7. **Comissió il·lustrativa** feta amb les tarifes públiques de l'opció (d); no s'ha de llegir com la tarifa del club. Propietari: tresorer.

<a id="M05b-14-aprovar"></a>
## M05b-14 Què cal aprovar abans de començar

**Aprovat el 27/10/2026** pel responsable del projecte, amb RN-M05b-14 ([048](decisions/048-reobrir-carrec-retornat.md)) i RN-M05b-15 (validada pel tresorer). Queda:
1. **RN-M05b-16** (qui paga la comissió de retorn) i **RN-M05b-18** (carnet amb una quota retornada) [A validar: junta]. No bloquegen el codi: són valors configurables.
2. **Resposta del banc** sobre remeses (P-45 punt 5) [A verificar: banc]: bloqueja T-M05b-10 i T-M05b-11.
3. **Proveïdor** (P-44, P-45) [A verificar: PaynoPain]: bloqueja T-M05b-04 contra un proveïdor real; amb `FakeProvider` es pot avançar.
4. **Autorització del nivell 2** (junta, 025): quan el 05b estigui acabat i provat.

---

<a id="M02"></a>
# Mòdul 02 — Activitats (cursos i sortides)

**Estat: escrit**, per aprovar pel responsable del projecte.

**Fonts:** document de funcionalitats (F §4 Cursos, §5 Sortides, processos 9.1, 9.17 i 9.18), mapa de la plataforma v8 (M02 Cursos i M03 Sortides), respostes del responsable del projecte del 20/10/2026 i del 22/10/2026 (catàlegs separats i editables, classes de reforç amb cost, subtipus de medi ambient ampliables, preus configurables amb nota obligatòria en canviar-los, duplicar com a plantilla), decisions [013](decisions/013-imputacio-comissions.md), [017](decisions/017-pagaments-metodes-i-domiciliacions.md), [021](decisions/021-persones-no-socies-com-a-convidades.md), [026](decisions/026-duplicar-activitats-al-modul-02.md), [027](decisions/027-estructura-basica-de-carrec-i-pagament.md), [035](decisions/035-dades-nomes-dins-ue.md), [041](decisions/041-web-installable-i-avisos-sense-push.md), [043](decisions/043-proveidor-de-pagaments-dins-la-ue.md) i [046](decisions/046-interficie-django-htmx-servida-des-del-vps.md); [spec 00](../specs/00-base-comuna/spec.md) (RN-30 a RN-33, RN-43, RN-60 a RN-73, V-02); seccions aprovades [M01](#M01), [M04](#M04) i [M05b](#M05b).

**Proveïdor de pagaments.** El 02 no parla mai amb el proveïdor: crea el càrrec d'inscripció (00) i el cobra amb els serveis del [05b](#M05b-8-serveis), que hi parla a través de l'adaptador. Inscripcions: targeta, Bizum o transferència, mai domiciliació (017; RN-69 de la 00).

<a id="M02-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Organitzar cursos i sortides de principi a fi en un sol lloc: catàlegs i preus, convocatòries i sortides (o duplicar-ne una d'anterior), inscripció i pagament dins l'app, places i llista d'espera, llista des del mòbil, avaluació, classes de reforç i certificat als cursos, i resultats ambientals i projectes a les sortides de medi ambient. Deixa cada activitat a punt perquè el 09 en calculi i en congeli el marge. |
| **Processos que cobreix** | P-M02-A Catàlegs i preus · P-M02-B Crear o duplicar una activitat · P-M02-C Publicar i inscriure's (soci, convidat i presencial) · P-M02-D Places, llista d'espera i cancel·lacions · P-M02-E El dia de l'activitat: llista i incidències · P-M02-F Avaluació, reforç i certificat · P-M02-G Resultats ambientals i projectes · P-M02-H Fi de l'activitat i comprovacions de tancament (F 9.1, 9.17 i 9.18) |
| **Tasques** | 27 (T-M02-01 a T-M02-27) |
| **Què el bloqueja** | Per construir: el 05b (cobrar inscripcions) i dues peces petites de mòduls aprovats ([M02-14](#M02-14-aprovar), punts 2 i 3). Per entrar en producció: el catàleg amb preus i la política de cancel·lació [A validar: junta]. La resta són supòsits configurables ([M02-13](#M02-13-riscos)) |
| **Què cal aprovar** | Aquesta secció; les dues ampliacions de contracte de mòduls aprovats; els supòsits S-M02-01 a S-M02-06, que fixen el comportament per defecte ([M02-14](#M02-14-aprovar)) |

<a id="M02-1-intencio"></a>
## M02-1 Intenció, abast i fora d'abast

**Per què.** Avui els cursos i les sortides es munten amb Excel, correu i WhatsApp: les places, els pagaments, la llista del dia i qui necessita reforç es creuen a mà. Cap programa comercial cobreix el reforç individual sense moure el grup, ni les sortides de medi ambient amb subtipus, projectes i resultats (F §4 i §5).

**Resultat esperat.**
- El responsable de cursos i sortides crea una convocatòria o una sortida, o en duplica una d'anterior, i la publica en pocs minuts.
- Socis i no socis s'inscriuen i paguen dins l'app; ningú no supera les places i l'excedent va a la llista d'espera.
- L'instructor passa llista i avalua cada alumne des del mòbil; els alumnes que ho necessiten tenen classes de reforç sense moure l'horari de la resta.
- Les sortides de medi ambient acumulen els seus resultats al seu projecte.
- Cada activitat acaba «realitzada» amb tot el que el 09 necessita per al marge.

**Com sabrem que funciona.**
- Una sortida es fa de principi a fi (crear, inscriure, pagar, passar llista, resultats) sense cap full de càlcul.
- Mai hi ha més inscripcions vàlides que places, tampoc amb dues inscripcions alhora (prova de concurrència).
- Cada inscripció pagada té exactament un càrrec «pagat» i el seu ingrés a l'activitat i al departament correctes (RN-T10).
- Un instructor no veu cap dada d'una sessió on no fa classe.

**Dins de l'abast.**
- Catàleg de cursos i catàleg d'especialitats, separats, amb preus de soci i de no soci editables.
- Tipus de sortida, subtipus de medi ambient (ampliables) i projectes de medi ambient.
- Activitats de dos tipus: **curs** (una convocatòria d'un curs o d'una especialitat, amb sessions) i **sortida** (amb programa del dia).
- Duplicar una activitat ([026](decisions/026-duplicar-activitats-al-modul-02.md)); el servei queda a punt perquè l'11 el faci servir per a les conferències.
- Inscripció del soci (compte personal), del no soci (convidat amb enllaç segur, [021](decisions/021-persones-no-socies-com-a-convidades.md)) i presencial; càrrec d'inscripció i pagament amb el 05b.
- Places, termini de pagament, llista d'espera i ofertes de plaça; cancel·lacions i proposta de devolució al tresorer.
- Requisits: titulació mínima i llicència vigent (avís o bloqueig, [A validar: junta, S-M02-01]).
- Assistència per sessió o per dia, incidències operatives, avaluació per pràctica, classes de reforç amb cost, resultat apte o no apte i certificat del club en PDF.
- Resultats ambientals (residus, espècies, observacions i fotos) i fitxa de projecte amb els acumulats.
- Avisos per correu i a l'app (sense push, [041](decisions/041-web-installable-i-avisos-sense-push.md)): confirmació, recordatoris, canvi de programa i missatge als inscrits; horari descarregable al calendari del mòbil.
- «Les meves activitats»: inscripcions, horari, progrés, certificats i historial.
- Informes operatius: participants, horari imprimible, ocupació.

**Fora d'abast.**
- **Material** (necessitats, assignació, lloguer, cost): mòdul [03](#M03). El 02 només ofereix els punts d'extensió perquè el 03 s'hi enganxi.
- **Marge, despeses amb factura (embarcació, aire, lloguer), ajuts i tancament econòmic:** mòdul 09. El 02 deixa l'activitat «realitzada» i diu què impedeix tancar-la.
- **Xat per activitat i grups:** mòdul 10. El 02 només envia missatges d'un sentit (correu i avís).
- **Conferències:** mòdul 11 (fa servir el servei de duplicar del 02).
- **Llicències** (tramitar-ne, llicència d'un dia per a no socis): mòdul 06. El 02 només llegeix si la llicència és vigent.
- **Bitàcola, hores d'immersió i insígnies:** mòdul 12 (P-38). El 02 en guarda l'assistència, que n'és la base.
- **Web pública** (portada, pàgines de projectes): mòdul 07. El 02 ofereix el llistat i el detall de les activitats publicades.
- Pujar observacions a Minka (F §5) i incrustar la previsió marítima d'un tercer: fora d'abast ara (vegeu RN-M02-24 i [M02-12](#M02-12-seguretat)).
- Qualsevol dada de salut, incloent-hi certificats mèdics i aptituds (P-07).
- Edat mínima: no hi ha data de naixement fins que es respongui P-33.

<a id="M02-2-dependencies"></a>
## M02-2 Dependències

**De què depèn.**
| Mòdul | Què en fa servir el 02 |
|---|---|
| 00 | Persona i dades mínimes del convidat; enllaços de convidat (V-02, RN-30 a RN-33); càrrec de tipus «inscripció» amb activitat i departament (RN-60 a RN-73); departaments; permisos per rol i per objecte (RN-43: l'instructor només veu les seves sessions); registre d'activitat; correu (annex A) i avisos; fitxers privats (annex B) |
| 01 | `members.is_member(person, on=date)` per al preu de soci; **registre mínim de llicència** per comprovar si és vigent (cal un servei de lectura nou, [M02-14](#M02-14-aprovar)) |
| 04 | Res directament: l'ingrés i les comissions de cada inscripció els crea el 05b amb l'activitat i el departament del càrrec (RN-T10) |
| 05b | `payments.start_payment`, `payments.payment_status`, rebut; devolucions fetes pel tresorer (`payments.refund`, B5); avís al 02 quan un càrrec d'inscripció es paga, es retorna o es torna (cal ampliar-ho, [M02-14](#M02-14-aprovar)) |

**Peces de mòduls aprovats que el 02 necessita i no hi són** (no s'editen les seccions aprovades fins que s'aprovin aquests punts):
1. **01:** `members.licence_record(person)` (només lectura): tipus i data de caducitat del registre mínim de llicència.
2. **00 i 05b:** quan un càrrec canvia a «pagat», «retornat» o «anul·lat», el 05b avisa el **mòdul d'origen** del càrrec (camp «mòdul d'origen» de la 00). Avui el 05b crida directament `members.on_fee_paid` (01). Proposta: un registre de la 00, `charges.register_handler(origin, handler)`, que el 05b crida per a qualsevol origen; el 01 hi passa a ser un origen més. No canvia cap regla del 05b.

**Què depèn del 02.**
| Mòdul | Què necessita |
|---|---|
| 03 | Activitats, dates, inscripcions i participants; senyals d'inscripció, de duplicat i de fi; punts d'extensió del formulari i del tancament |
| 09 | Activitat, departament, estat «realitzada», comprovacions de tancament; ingressos per activitat (via 04); projectes de medi ambient per justificar ajuts |
| 06 | Avís de llicència no vigent i enllaç per tramitar-la |
| 07 | Llistat i detall de les activitats publicades; projectes i resultats ambientals (només els que es publiquin) |
| 08 | Ocupació, inscripcions i assistència |
| 10 | Inscrits d'una activitat per al xat |
| 11 | Servei de duplicar i, si s'hi decideix, el mateix model d'inscripció |
| 12 | Assistència de cada persona per a la bitàcola |

**Dependència circular 02 ↔ 03.** El 03 necessita les activitats; el 02 necessita saber si hi ha material pendent per tancar. Es resol sense que el 02 importi el 03: el 02 emet senyals i ofereix punts d'extensió on el 03 es registra ([M02-8](#M02-8-serveis)).

<a id="M02-3-capacitats"></a>
## M02-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | Pantalles (mapa v8 i proposta) | Wireframe |
|---|---|---|---|---|
| C1 | Mantenir els catàlegs de cursos i d'especialitats, amb preus | Resp. cursos i sortides | Gestió de cursos | Falta |
| C2 | Mantenir tipus de sortida, subtipus de medi ambient i projectes | Resp. cursos i sortides | Gestió de sortides; Projectes | Falta |
| C3 | Crear, editar, publicar, cancel·lar i duplicar activitats | Resp. cursos i sortides | Convocatòria; Gestió de sortides | `admin.html#fitxa` (fitxa d'activitat) |
| C4 | Sessions dels cursos i programa del dia de les sortides | Resp. cursos i sortides | Convocatòria; Programa del dia | `admin.html#programa-i-notes` |
| C5 | Veure activitats publicades i el seu detall | Tothom | Cursos; Sortides; Detall | `publica.html#properes-activitats`; `socis.html#proximes-activitats` |
| C6 | Inscriure's i pagar | Soci; convidat | Inscriure'm | Falta |
| C7 | Inscripció presencial | Resp. cursos i sortides; secretaria [A validar: junta, S-M02-16] | Participants | `admin.html#participants` |
| C8 | Places, llista d'espera i ofertes | Sistema; Resp. cursos i sortides | Participants | `admin.html#participants` |
| C9 | Cancel·lar una inscripció o una activitat | Participant; Resp. cursos i sortides | Les meves inscripcions; Fitxa | Falta |
| C10 | Passar llista i registrar incidències des del mòbil | Instructor; Resp. cursos i sortides | Passar llista | Falta |
| C11 | Avaluar cada pràctica i veure el progrés | Instructor; alumne (el seu) | Avaluació; El meu progrés | Falta |
| C12 | Proposar i confirmar classes de reforç | Instructor; Resp. cursos i sortides | Classes de reforç | Falta |
| C13 | Resultat i certificat | Instructor; Resp. cursos i sortides | Certificats | Falta |
| C14 | Resultats ambientals i projectes | Resp. cursos i sortides | Resultats ambientals; Projecte | Falta |
| C15 | Avisos i missatge als inscrits; horari al calendari | Sistema; Resp. cursos i sortides | — | `socis.html#avisos` |
| C16 | Les meves activitats: inscripcions, horari, progrés, certificats i historial | Soci; convidat (el seu) | Les meves inscripcions; Horari | `socis.html#proximes-activitats` |
| C17 | Informes operatius | Resp. cursos i sortides | Informes | Falta |

**Històries d'usuari**
- **HU-M02-01.** Com a responsable de cursos i sortides, vull afegir un curs o una especialitat al seu catàleg i canviar-ne els preus sense tocar res més.
- **HU-M02-02.** Com a responsable, vull afegir un subtipus de medi ambient nou quan calgui, per poder agrupar despeses i buscar ajuts per subtipus.
- **HU-M02-03.** Com a responsable, vull crear una convocatòria a partir del catàleg, amb sessions de teoria, piscina i mar, i afegir-hi sessions quan calgui.
- **HU-M02-04.** Com a responsable, vull duplicar una sortida de l'any passat i canviar-ne només la data, per no tornar-la a escriure.
- **HU-M02-05.** Com a responsable, si canvio el preu que ve del catàleg, vull escriure el motiu i que el tresorer ho sàpiga.
- **HU-M02-06.** Com a soci, vull veure les places lliures, el preu que pagaré i els requisits, i inscriure'm i pagar al moment.
- **HU-M02-07.** Com a persona no sòcia, vull inscriure'm amb un enllaç segur sense haver de crear un compte.
- **HU-M02-08.** Com a soci en llista d'espera, vull rebre un avís quan s'alliberi una plaça i poder-la acceptar.
- **HU-M02-09.** Com a participant, vull cancel·lar la meva inscripció i saber què em tornaran.
- **HU-M02-10.** Com a responsable, vull cancel·lar una sortida per mal temps i que tots els inscrits ho sàpiguen i el tresorer en tingui les devolucions preparades.
- **HU-M02-11.** Com a instructor, vull passar llista des del mòbil al costat de la piscina, amb botons grans i encara que la cobertura sigui dolenta.
- **HU-M02-12.** Com a instructor, vull marcar a cada pràctica si l'alumne ho ha assolit, no ho ha assolit o necessita reforç, amb una observació.
- **HU-M02-13.** Com a instructor, vull proposar classes de reforç per a un alumne sense moure l'horari del grup.
- **HU-M02-14.** Com a alumne, vull veure el meu progrés, les classes de reforç i el seu preu, i descarregar el certificat quan sigui apte.
- **HU-M02-15.** Com a responsable de medi ambient, vull registrar els quilos de residus, les espècies i les fotos d'una neteja i veure'n l'acumulat al projecte.
- **HU-M02-16.** Com a inscrit, vull rebre el programa i un recordatori, i saber-ho si el programa canvia.
- **HU-M02-17.** Com a responsable, vull saber per què una activitat encara no es pot tancar (pagaments o material pendents).

<a id="M02-4-rols"></a>
## M02-4 Rols i permisos

Llegenda com a [M01-4](#M01-4-rols). A les taules, «[A validar]» sense propietari vol dir **junta** (Q-01, P-04). «Les seves» vol dir les sessions on l'instructor fa classe (RN-43 de la 00).

| # | Acció | Visitant | Part. no soci | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Resp. comunicació | Dept. Història | Junta | Administrador | Resp. botiga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AC1 | Veure les activitats publicades i el seu detall | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí |
| AC2 | Inscriure's i pagar | — | Propi (enllaç de convidat) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| AC3 | Veure les seves inscripcions, horari, progrés i certificats | — | Propi (enllaç o compte opcional) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| AC4 | Cancel·lar la seva inscripció | — | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| AC5 | Inscriure presencialment una altra persona | — | — | — | — | [A validar] | Sí | — | — | — | — | — | Sí | — |
| AC6 | Mantenir catàlegs, tipus, subtipus, projectes i preus | — | — | — | — | — | Sí | — | Consulta | — | — | [A validar] | Sí | — |
| AC7 | Crear, editar, publicar, cancel·lar i duplicar activitats | — | — | — | — | — | Sí | — | — | — | — | — | Sí | — |
| AC8 | Llista de participants amb requisits | — | — | — | Les seves | — | Sí | Consulta | Consulta (estat de pagament) | — | — | — | Sí | — |
| AC9 | Passar llista i registrar incidències | — | — | — | Les seves | — | Sí | — | — | — | — | — | Sí | — |
| AC10 | Avaluar pràctiques i proposar reforç | — | — | — | Les seves | — | [A validar] | — | — | — | — | — | — | — |
| AC11 | Confirmar o rebutjar reforç | — | — | — | — | — | Sí | — | — | — | — | — | Sí | — |
| AC12 | Registrar apte o no apte | — | — | — | Les seves | — | — | — | — | — | — | — | — | — |
| AC13 | Emetre el certificat | — | — | — | [A validar] | — | Sí | — | — | — | — | — | Sí | — |
| AC14 | Resultats ambientals i fitxa de projecte | — | — | — | — | — | Sí | — | — | Consulta [A validar] | — | Consulta | Sí | — |
| AC15 | Missatge als inscrits (correu i avís) | — | — | — | Les seves [A validar] | — | Sí | — | — | [A validar] | — | — | Sí | — |
| AC16 | Gestionar la llista d'espera a mà (ordre, oferir) | — | — | — | — | — | Sí | — | — | — | — | — | Sí | — |
| AC17 | Proposar una devolució per cancel·lació | — | — | — | — | — | Sí | — | — | — | — | — | Sí | — |
| AC18 | Fer la devolució | — | — | — | — | — | — | — | Sí (B5 del 05b) | — | — | — | [A validar] | — |
| AC19 | Veure els imports cobrats d'una activitat | — | — | — | — | — | Consulta [A validar: Q-01] | — | Sí | — | — | [A validar] | Sí | — |
| AC20 | Informes operatius | — | — | — | Les seves | — | Sí | Consulta | Consulta | — | — | Consulta | Sí | — |

**Com es llegeix amb els comptes.** Com al [M01-4](#M01-4-rols): les files «Propi» amb el compte personal (o amb l'enllaç de convidat); les de gestió amb el compte d'administrador, el rol i TOTP. Un instructor sempre entra per l'administració per passar llista (RN-20 de la 00).

**Per objecte.**
- **Instructor:** només les sessions on fa classe i els alumnes inscrits a aquestes sessions. Dels alumnes veu nom i cognoms, titulació, si la llicència és vigent (sí o no, no la data), l'assistència i les avaluacions. **No veu** document, adreça, correu, telèfon ni pagaments [A validar: junta, Q-01]. Fora de les seves sessions, «no trobat» i registre.
- **Responsable de material:** participants i necessitats de material (03), sense pagaments.
- **Tresorer:** estat de pagament de les inscripcions, sense avaluacions ni incidències.
- **Participant:** només les seves inscripcions; mai la llista d'altres inscrits (tampoc noms a la web pública).
- **Un sol tresorer:** cap acció del 02 necessita doble aprovació (P-48). El responsable proposa la devolució i el tresorer la fa.
- **Conflicte d'interès:** un instructor no pot registrar-se apte a ell mateix si és alumne d'una activitat; es rebutja i es registra.

<a id="M02-5-processos"></a>
## M02-5 Processos pas per pas

**Wireframes existents:** `admin.html#fitxa` (fitxa d'una sortida amb resum econòmic, participants amb cerca i filtres, material assignat, activitat recent i programa i notes), `publica.html#properes-activitats` i `socis.html#proximes-activitats` (targetes d'activitat). **Falten** (T-M02-01): catàlegs, formulari d'activitat i de sessions, inscripció en quatre estats, llista d'espera, «Les meves inscripcions», passar llista al mòbil, avaluació i progrés, reforç, certificat, resultats ambientals i projecte.

**Estats d'una activitat**
| Estat | Curs (F §4) | Sortida (F §5) | Qui hi passa |
|---|---|---|---|
| `draft` | esborrany | esborrany | Responsable |
| `open` | obert | oberta | Responsable (publicar) |
| `registration_closed` | tancat a inscripcions | tancada a inscripcions | Sistema (places plenes o data límit) o responsable |
| `in_progress` | en curs | — (no s'usa) | Sistema (primera sessió) |
| `done` | finalitzat | realitzada | Responsable |
| `closed` | tancat econòmicament | tancada econòmicament | **Només el 09** (`margins.close_activity`). Fins que existeixi el 09, cap activitat hi arriba |
| `cancelled` | cancel·lat | cancel·lada | Responsable, amb motiu |

**Estats d'una inscripció**
| Estat | Què vol dir | Ocupa plaça |
|---|---|---|
| `pending_payment` | Inscrit, càrrec creat, dins el termini de pagament | Sí |
| `confirmed` | Càrrec pagat (o activitat gratuïta) | Sí |
| `waitlisted` | A la llista d'espera, amb ordre | No |
| `offered` | Se li ha ofert una plaça i té un termini per acceptar-la | Sí |
| `cancelled` | Cancel·lada pel participant o pel club, amb motiu | No |
| `expired` | No ha pagat a temps o no ha acceptat l'oferta | No |

### P-M02-A Catàlegs i preus
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Responsable | Obre «Catàleg de cursos» o «Catàleg d'especialitats» (dues pantalles separades) i afegeix o edita una fitxa: nom, nivell, descripció, requisits, places per defecte, preu de soci, preu de no soci, departament |
| 2 | Sistema | Desa i registra el valor anterior. Els canvis de preu s'apliquen a les activitats noves, no a les que ja tenen inscripcions (RN-M02-05) |
| 3 | Responsable | A «Tipus de sortida» i «Subtipus de medi ambient» afegeix o desactiva valors; a «Projectes», crea un projecte amb nom i objectiu |

### P-M02-B Crear o duplicar una activitat (F 9.1 passos 1-2; 9.18)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Responsable | **Curs:** tria la fitxa del catàleg; es copien places, preus i requisits. **Sortida:** tria tipus i, si és de medi ambient, subtipus i projecte. Omple títol, objectiu, dates, lloc, departament, places, data límit d'inscripció i responsable |
| 2 | Responsable | **Curs:** afegeix sessions (teoria, piscina o mar) amb data, hora, lloc i instructors; se'n poden afegir més tard. **Sortida:** afegeix el programa del dia per blocs (trobada, briefing, immersió, dinar, tornada) |
| 3 | Responsable | Si canvia un preu respecte del catàleg, escriu el motiu (obligatori). El sistema avisa el tresorer (RN-M02-06) |
| 4 | Responsable | **Duplicar:** obre una activitat anterior, tria «Duplicar» i una data d'inici nova. El sistema copia el que diu RN-M02-21, desplaça sessions i dates i en deixa la còpia en esborrany |
| 5 | Responsable | Publica: l'activitat passa a `open`, surt al llistat públic i, si ho tria, s'envia l'anunci als socis (correu i avís, RN-M02-19) |

### P-M02-C Publicar i inscriure's (F 9.1 pas 4)
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Participant | Obre el detall: descripció, programa o sessions, lloc, preu que li correspon, places lliures (només el número), requisits i, a les sortides, l'enllaç a la previsió marítima | Detall |
| 2 | Participant | **Soci:** «Inscriure'm» amb el compte personal. **No soci:** «Inscriure'm sense compte» → dades mínimes i consentiment (00) → rep un enllaç de convidat al correu (V-02). **Presencial:** el responsable ho fa per ell | Inscriure'm |
| 3 | Participant | Respon les preguntes que hi afegeixin altres mòduls (el 03 hi posa el material que porta i el que necessita) | Inscriure'm |
| 4 | Sistema | Comprova requisits (RN-M02-10). Si no els compleix: avís (supòsit) o bloqueig [A validar: junta, S-M02-01] | — |
| 5 | Sistema | Bloqueja la fila de l'activitat i compta les places (RN-M02-07). Si n'hi ha: inscripció `pending_payment` i càrrec «inscripció» amb l'import que toca, l'activitat i el departament. Si no: `waitlisted` | — |
| 6 | Participant | Paga amb targeta, Bizum o transferència (P-M05b-A a C). Activitat gratuïta: `confirmed` sense càrrec | Pantalla de pagament (05b) |
| 7 | Sistema | Quan el 05b avisa que el càrrec és «pagat», la inscripció passa a `confirmed` i el participant rep la confirmació amb l'horari i el fitxer per al calendari | — |

### P-M02-D Places, llista d'espera i cancel·lacions
1. **Termini de pagament.** Una inscripció `pending_payment` que no s'ha pagat dins el termini (RN-M02-08) passa a `expired`, el càrrec s'anul·la amb motiu i la plaça s'ofereix.
2. **Oferta de plaça.** Quan s'allibera una plaça, el primer de la llista passa a `offered` i rep un correu i un avís amb un termini per acceptar-la (RN-M02-09). Si l'accepta, es crea el càrrec com al pas 5 de P-M02-C. Si no, `expired` i es passa al següent.
3. **Cancel·lació del participant.** Abans de la data límit (RN-M02-12). La inscripció passa a `cancelled` amb motiu. Si estava pagada, el sistema crea una **proposta de devolució** amb l'import que diu la política [A validar: junta] i l'envia a la llista del tresorer, que la fa amb el 05b.
4. **Cancel·lació de l'activitat** (per exemple, per meteorologia). El responsable tria «Cancel·lar» i el motiu. L'activitat passa a `cancelled`, totes les inscripcions a `cancelled`, els càrrecs pendents s'anul·len, es creen propostes de devolució per als pagats (RN-M02-13) i s'avisa tots els inscrits i la llista d'espera.
5. **Tancar inscripcions.** Automàtic quan s'arriba a la data límit; amb les places plenes, l'activitat continua `open` amb llista d'espera fins a la data límit.

### P-M02-E El dia de l'activitat: llista i incidències (F 9.1 pas 8)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Instructor o responsable | Obre «Passar llista» al mòbil: llista dels inscrits `confirmed` de la sessió (curs) o del dia (sortida), amb titulació i llicència vigent sí o no |
| 2 | Instructor | Marca present o absent amb un toc. Cada canvi s'envia sol (HTMX) i, si no hi ha cobertura, es reintenta i es mostra «pendent d'enviar» |
| 3 | Instructor | Registra incidències **operatives** (retard, embarcació, material, meteorologia). Mai dades de salut (RN-M02-17) |
| 4 | Sistema | Un participant `pending_payment` el dia de l'activitat surt marcat perquè el responsable ho resolgui |

### P-M02-F Avaluació, reforç i certificat (F 9.17)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Instructor | A cada sessió pràctica, avalua cada alumne: **assolit**, **no assolit** o **necessita reforç**, amb una observació curta (sense dades de salut) |
| 2 | Instructor | Si un alumne no assoleix el nivell o no se sent preparat, proposa una o més classes de reforç |
| 3 | Responsable | Confirma o rebutja la proposta. En confirmar-la, crea les sessions de reforç d'aquell alumne (data, lloc i instructor) sense moure el grup |
| 4 | Sistema | Crea un càrrec «inscripció» per al reforç amb el preu del catàleg (RN-M02-15), lligat a la mateixa activitat; l'alumne rep l'avís amb data i preu i paga com al pas 6 de P-M02-C |
| 5 | Instructor | Quan l'alumne està preparat, registra **apte** (o **no apte** al final, amb motiu) |
| 6 | Responsable | Emet el certificat del club en PDF amb número (RN-M02-16). L'alumne el descarrega des de «Les meves activitats». Si cal llicència, l'avís enllaça amb el 06 |

### P-M02-G Resultats ambientals i projectes (F 9.1 pas 9)
1. Després d'una sortida de medi ambient, el responsable obre «Resultats»: quilos de residus (amb decimals, es desen en grams), espècies observades, observacions i fotos.
2. Les fotos van als fitxers privats de la 00 amb autor i permís d'ús; cap foto no es publica sense això (P-41).
3. La fitxa del projecte mostra les seves sortides, la suma de residus, les espècies i les fotos. Les factures i l'ajut del projecte hi apareixen quan existeixi el 09.

### P-M02-H Fi de l'activitat i comprovacions de tancament (F 9.1 passos 10-11)
1. El responsable marca l'activitat com a `done` quan s'ha fet (cursos: quan totes les sessions del grup s'han fet; el reforç individual pot continuar, RN-M02-14).
2. «Què falta per tancar» mostra la llista de `closing_blockers`: inscripcions sense pagar, propostes de devolució sense fer (05b) i material pendent (03, quan existeixi).
3. El tancament econòmic i el marge són del 09.

<a id="M02-6-entitats"></a>
## M02-6 Entitats i camps

App Django `activities` (nova). Noms de codi en anglès. Imports en cèntims (`PositiveIntegerField`). Cap camp de dades de salut, de targeta ni d'IBAN. Les persones són de la 00 (FK `Person`, PROTECT).

### TrainingCatalogueEntry (fitxa de curs o d'especialitat)
| Camp | Tipus | Restriccions |
|---|---|---|
| `kind` | `course`, `speciality` | Dos catàlegs separats a la interfície (dues pantalles i dos llistats) |
| `name` | `CharField(120)` | Únic per `kind` |
| `level` | `CharField(60)` | Nivell que dona o requereix [A verificar: FECDAS, llista de nivells] |
| `description`, `requirements` | `TextField` | — |
| `default_places` | `PositiveSmallIntegerField` | > 0 |
| `price_member_cents`, `price_non_member_cents` | `PositiveIntegerField` | ≥ 0 |
| `reinforcement_price_cents` | `PositiveIntegerField` null | Preu d'una classe de reforç [A validar: junta] |
| `open_to_non_members` | `BooleanField` | [A validar: junta] |
| `department` | FK departament (00) | Obligatori |
| `active` | `BooleanField` | No s'esborra si té activitats |

### OutingType, EnvironmentalSubtype, EnvironmentalProject
- `OutingType`: `name` (únic), `is_environmental` (bool), `default_department` (FK), `active`. Dades inicials: «Immersió», «Medi ambient» (`is_environmental`), «Sèniors» i «Jornada oberta» [A validar: junta, si són tipus propis].
- `EnvironmentalSubtype`: `name` (únic), `active`. Dades inicials: «Neteja» (F §5); la resta, la llista del responsable del projecte [A validar: responsable del projecte, S-M02-13].
- `EnvironmentalProject`: `name` (únic), `objective` (`TextField`), `status` (`active`, `finished`), `department` (FK). No s'esborra si té sortides.

### Activity (activitat)
| Camp | Tipus | Restriccions |
|---|---|---|
| `kind` | `course`, `outing` | `conference` s'hi afegirà amb l'11 |
| `title` | `CharField(140)` | — |
| `description` | `TextField` | Objectiu (sortides) o descripció (cursos) |
| `catalogue_entry` | FK TrainingCatalogueEntry null | Obligatori si `kind = course` (`CHECK`) |
| `outing_type` | FK OutingType null | Obligatori si `kind = outing` (`CHECK`) |
| `subtype`, `project` | FK null | Només si el tipus és de medi ambient (validació de servei) |
| `department` | FK departament (00) | Obligatori (RN-62 de la 00) |
| `cost_centre` | FK CostCentre (04) null | Del mateix departament |
| `status` | estats de [M02-5](#M02-5-processos) | Transicions de RN-M02-02 |
| `starts_on`, `ends_on` | `DateField` | `ends_on ≥ starts_on` |
| `location`, `meeting_point` | `CharField(140)` | — |
| `max_places` | `PositiveSmallIntegerField` | > 0 |
| `registration_closes_at` | `DateTimeField` | ≤ inici |
| `payment_window_hours` | `PositiveSmallIntegerField` | RN-M02-08 |
| `price_member_cents`, `price_non_member_cents` | `PositiveIntegerField` | Còpia del catàleg en crear-la |
| `price_override_note` | `TextField` | Obligatori si algun preu difereix del catàleg (validació de servei) |
| `open_to_non_members` | `BooleanField` | — |
| `required_level` | `CharField(60)` | Opcional |
| `licence_required` | `BooleanField` | — |
| `requirements_mode` | `warn`, `block` | RN-M02-10 |
| `responsible` | FK Person | Persona responsable de l'activitat |
| `forecast_url` | `URLField` | Enllaç a la previsió marítima (RN-M02-24) |
| `duplicated_from` | FK self null | RN-M02-21 |
| `cancellation_reason` | `TextField` | Obligatori si `cancelled` |
| `published_at`, `done_at` | `DateTimeField` null | — |
**Índexs:** `(status, starts_on)`, `(kind, starts_on)`, `(project)`.

### Session (sessió d'un curs) i ProgrammeBlock (bloc del programa d'una sortida)
- `Session`: `activity` (FK), `kind` (`theory`, `pool`, `sea`), `starts_at`, `ends_at` (`CHECK ends_at > starts_at`), `location`, `instructors` (M2M a Person, amb el rol instructor), `is_practice` (bool), `reinforcement_for` (FK Enrolment null: si no és null, és una classe de reforç d'aquell alumne), `cancelled` (bool) i `cancellation_reason`.
- `ProgrammeBlock`: `activity` (FK), `order`, `starts_at` (`TimeField`), `ends_at` null, `label` (`CharField(80)`), `location`, `responsible_label` (`CharField(80)`, rol o funció, mai dades de contacte).

### Enrolment (inscripció)
| Camp | Tipus | Restriccions |
|---|---|---|
| `activity` | FK Activity (PROTECT) | — |
| `person` | FK Person (00) | — |
| `status` | estats de [M02-5](#M02-5-processos) | Transicions de RN-M02-03 |
| `channel` | `account`, `guest`, `desk` | — |
| `price_kind` | `member`, `non_member` | Fixat en inscriure's (RN-M02-04) |
| `price_cents` | `PositiveIntegerField` | Còpia del preu en inscriure's |
| `charge` | FK càrrec (00) null | Null si és gratuïta o en llista d'espera |
| `waitlist_position` | `PositiveIntegerField` null | Només `waitlisted` |
| `payment_due_at`, `offer_expires_at` | `DateTimeField` null | — |
| `requirements_warning` | `TextField` | Què no complia en inscriure's |
| `cancelled_reason`, `cancelled_by` | text, FK compte null | Obligatori si `cancelled` |
| `created_by` | FK compte null | Null = el mateix participant o el seu enllaç |
**Restriccions:** únic parcial `(activity, person) WHERE status NOT IN ('cancelled','expired')` (una inscripció viva per persona i activitat). Índex `(activity, status)`.

### Attendance, Incident, PracticeAssessment, ReinforcementRequest, CourseOutcome
- `Attendance`: `enrolment` (FK), `session` (FK null: null = el dia de la sortida), `present` (bool), `recorded_by`, `recorded_at`. Únic `(enrolment, session)`. Es pot corregir; cada canvi va al registre d'activitat.
- `Incident`: `activity`, `session` null, `kind` (`delay`, `boat`, `equipment`, `weather`, `other`), `description` (`TextField`, màx. 1000), `recorded_by`, `recorded_at`. Només s'hi afegeix. Text d'ajuda: «Sense dades de salut».
- `PracticeAssessment`: `session` (pràctica), `enrolment`, `result` (`achieved`, `not_achieved`, `needs_reinforcement`), `notes` (màx. 500, sense dades de salut), `recorded_by`. Únic `(session, enrolment)`.
- `ReinforcementRequest`: `enrolment`, `proposed_by`, `reason` (pedagògic, màx. 500), `status` (`proposed`, `confirmed`, `rejected`), `decided_by`, `price_cents`, `charge` (FK null).
- `RefundProposal`: `enrolment`, `charge`, `amount_cents` (≤ pagat), `reason`, `proposed_by` (null = sistema), `status` (`proposed`, `done`, `rejected`), `refund` (FK a la devolució del 05b, null), `decided_by`, `decision_reason`. El tresorer les veu a la seva llista; només ell les fa o les rebutja amb motiu.
- `CourseOutcome`: `enrolment` (OneToOne), `result` (`pass`, `fail`), `decided_by` (instructor), `decided_at`, `reason` (obligatori si `fail`), `certificate_number` (únic, null), `certificate_issued_by`, `certificate_issued_at`. El PDF es genera a demanda (annex B de la 00).

### DiverCertification (titulació)
`person` (FK), `agency` (`CharField(60)`) [A verificar: FECDAS, llista d'agències], `level` (`CharField(60)`), `number` (`CharField(40)`, opcional), `issued_on` (null), `source` (`club_course`, `declared`, `imported`), `verified_by` (FK compte null), `verified_at`. Cap foto ni escaneig del carnet de titulació.

### EnvironmentalResult i EnvironmentalPhoto
- `EnvironmentalResult`: `activity` (OneToOne, només sortides de medi ambient), `waste_grams` (`PositiveIntegerField` null), `species` (`TextField`: una espècie per línia) [A validar: junta, quines dades], `observations` (`TextField`), `recorded_by`, `recorded_at`.
- `EnvironmentalPhoto`: `result` (FK), `file` (fitxer privat de la 00), `author` (`CharField(120)`), `usage_permission` (bool), `shows_people` (bool), `people_consent` (bool). Si `shows_people` i no hi ha consentiment, no es pot marcar com a publicable (P-41).

### Ampliacions de la 00 (sense canviar-ne les regles)
- El càrrec ja té `activity` (opcional, «quan existeixi la 02»): el 02 l'omple.
- Registre de gestors per mòdul d'origen (`charges.register_handler`), si s'aprova ([M02-14](#M02-14-aprovar)).

**Migracions:** reversibles; dades inicials (tipus de sortida, subtipus «Neteja») en una migració de dades; cap dada personal a les migracions.

<a id="M02-7-regles"></a>
## M02-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M02-01 | Cursos i especialitats són dos catàlegs separats; cadascun amb preus de soci i de no soci editables pel responsable sense tocar res més | F §4; resposta del 22/10/2026 |
| RN-M02-02 | Transicions de l'activitat: `draft → open → registration_closed → in_progress → done → closed`; `open → done` i `registration_closed → done` (sortides); qualsevol estat abans de `done` → `cancelled` amb motiu. `closed` només el fa el 09. Cap transició enrere excepte `registration_closed → open` (el responsable reobre inscripcions abans de l'inici) | F §4 i §5 |
| RN-M02-03 | Transicions de la inscripció: `pending_payment → confirmed / expired / cancelled`; `waitlisted → offered / cancelled / expired`; `offered → pending_payment / expired`; `confirmed → cancelled`. Una inscripció `confirmed` no torna a `pending_payment` | Proposta |
| RN-M02-04 | Preu: soci si `members.is_member(person, on=data d'inscripció)`; si no, el de no soci. Es copia a la inscripció i no canvia encara que canviï el catàleg o l'estat de soci. Simpatitzants i ple dret paguen el preu de soci [A validar: junta, S-M01-11] | F §4; S-M02-04 |
| RN-M02-05 | Canviar un preu del catàleg no canvia les activitats ja creades | Proposta |
| RN-M02-06 | Si el preu d'una activitat difereix del catàleg, la nota del motiu és obligatòria i s'avisa el tresorer (correu i avís a l'app). El canvi i el valor anterior van al registre | Resposta del 22/10/2026 |
| RN-M02-07 | Places ocupades = inscripcions `pending_payment` + `confirmed` + `offered`. Mai més que `max_places`: el recompte i la inscripció es fan dins una transacció amb la fila de l'activitat bloquejada (`SELECT … FOR UPDATE`) | F §4 i §5 |
| RN-M02-08 | Termini de pagament: `payment_window_hours` des de la inscripció (o des d'acceptar l'oferta), amb un valor per defecte de 72 hores [A validar: responsable de cursos i sortides i tresorer, S-M02-02]. Un pagament en curs (intent del 05b «en curs») allarga el termini fins que acaba. Una transferència anunciada no l'allarga | Proposta |
| RN-M02-09 | Llista d'espera per ordre d'arribada; el responsable pot reordenar-la amb motiu. Oferta de plaça amb 48 hores per acceptar-la [A validar, S-M02-03]. Si queden menys de 48 hores per a la data límit, el termini acaba a la data límit | F §4 i §5 |
| RN-M02-10 | Requisits: titulació mínima (`required_level`, contra les titulacions de la persona) i llicència vigent (registre mínim del 01) a la data de l'activitat. `requirements_mode = warn` (supòsit per defecte): es pot inscriure, veu l'avís i el responsable ho veu marcat. `block`: no es pot inscriure [A validar: junta, S-M02-01] | F §5 |
| RN-M02-11 | Un no soci només es pot inscriure si l'activitat té `open_to_non_members`; s'inscriu com a convidat amb dades mínimes i consentiment i paga amb l'enllaç (021; RN-30 de la 00) | F §4; 021 |
| RN-M02-12 | Cancel·lació del participant: només abans de la data límit d'inscripció. L'import a tornar el fixa la política del club [A validar: junta, S-M02-05]; mentre no hi sigui, la proposta de devolució és de l'import pagat i el tresorer decideix | F §4 |
| RN-M02-13 | Cancel·lació de l'activitat pel club (també per meteorologia): proposta de devolució del **100 %** de l'import pagat a cada inscrit [A validar: junta, S-M02-05]. La comissió del proveïdor no es recupera i queda com a despesa de l'activitat (RN-T11, 013) | F §5 |
| RN-M02-14 | Un curs pot passar a `done` amb alumnes en reforç: les seves sessions de reforç continuen lligades a la mateixa activitat (resposta del 22/10/2026: lligades al curs actiu de l'alumne) | Resposta del 22/10/2026 |
| RN-M02-15 | Les classes de reforç tenen cost per a l'alumne (resposta del 22/10/2026). Preu: `reinforcement_price_cents` del catàleg, per proposta confirmada [A validar: junta, import i si és per classe o per proposta]. Càrrec «inscripció» a la mateixa activitat i departament | F 9.17; resposta del 22/10/2026 |
| RN-M02-16 | Un alumne no rep el certificat fins que l'instructor el registra apte. El certificat és del club, en PDF, amb número únic `C-AAAA-NNNN` [A validar: junta]; la titulació oficial de la federació o l'agència es tramita fora de la plataforma [A verificar: FECDAS]. En emetre'l es crea la titulació de la persona amb `source = club_course` | F §4 |
| RN-M02-17 | Ni incidències, ni observacions, ni avaluacions no poden contenir dades de salut. Un accident segueix el protocol del club fora de la plataforma [A validar: junta] | CLAUDE.md; P-07 |
| RN-M02-18 | Qualsevol canvi del programa del dia, de les sessions, del lloc o de l'hora d'una activitat `open` o posterior avisa automàticament els inscrits `confirmed`, `pending_payment` i `offered` | F §5 |
| RN-M02-19 | Avisos per correu i a la safata de l'app, mai push (041): confirmació, recordatori (supòsit: 2 dies abans de cada sessió o sortida [A validar: secretaria, S-M02-15]), canvi de programa, oferta de plaça, termini de pagament, cancel·lació i missatge del responsable | F §4 i §5; 041 |
| RN-M02-20 | Una activitat no es pot marcar `done` abans de la data de l'última sessió (curs) o de la sortida | Proposta |
| RN-M02-21 | **Duplicar** (026): copia títol, descripció, tipus, subtipus, projecte, catàleg, departament, centre de cost, places, preus (i la nota), requisits, termini de pagament, programa del dia, sessions del grup (no les de reforç) amb instructors, i el material típic (via senyal, 03). Desplaça totes les dates i hores per la diferència entre la data d'inici nova i l'antiga. **No copia:** inscripcions, llista d'espera, pagaments, assistència, avaluacions, resultats, incidències ni fotos. La còpia és `draft` i guarda `duplicated_from` | F 9.18; 026 |
| RN-M02-22 | Comprovacions de tancament (`closing_blockers`): inscripcions `pending_payment` o `offered`, càrrecs de reforç sense pagar, propostes de devolució sense fer i les que registrin altres mòduls (material pendent, 03) | F §5 («no es pot tancar amb cobraments o material pendents») |
| RN-M02-23 | Les fotos i els resultats ambientals no es publiquen enlloc des del 02. La publicació és del 07 i només amb autor, permís i consentiment de les persones que hi surtin (P-41) | P-41 |
| RN-M02-24 | Previsió marítima: només un **enllaç** a la pàgina pública del servei (per exemple, Meteocat), sense incrustar-ne cap giny ni carregar-ne cap script (046) | F §5; 046 |
| RN-M02-25 | L'horari descarregable (fitxer de calendari) només conté les sessions o la sortida de qui el descarrega, sense dades d'altres persones | Proposta |

**Exemples numèrics (imports inventats)**
- **Places (RN-M02-07):** sortida amb 12 places i preu de soci de **4500** cèntims. 10 `confirmed` + 2 `pending_payment` → plena; la 13a inscripció va a la llista d'espera (posició 1). Una de les dues pendents no paga en 72 hores → `expired`, el seu càrrec s'anul·la, la posició 1 passa a `offered` amb 48 hores.
- **Cancel·lació per meteorologia (RN-M02-13):** 10 inscrits pagats amb targeta → 10 propostes de devolució de 4500 = **45.000** cèntims. Si la comissió de targeta fos de 1,80 % + 25 cèntims (tarifa pública il·lustrativa, M05b-7), cada pagament n'hauria costat 81 + 25 = 106, i les **1060** cèntims de comissions queden com a despesa de l'activitat.
- **Reforç (RN-M02-15):** curs amb `reinforcement_price_cents = 3000` (inventat). L'instructor proposa 2 classes per a un alumne; el responsable confirma la proposta → un càrrec de **3000** (si el preu és per proposta) o de **6000** (si és per classe) [A validar: junta].
- **Duplicar (RN-M02-21):** original del 14 al 15 de juny amb sessions el 14 a les 9:00 i el 15 a les 10:00; data d'inici nova, 13 de juny de l'any següent → sessions el 13 a les 9:00 i el 14 a les 10:00, data límit d'inscripció desplaçada el mateix.

<a id="M02-8-serveis"></a>
## M02-8 Serveis i interfícies (contracte)

Cap altra app escriu als models del 02. Errors com a excepcions de domini amb missatge en català.

**Ofereix**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `activities.get_activity(id)`, `activities.public_list(filters)` | — | dades públiques (sense noms d'inscrits) | `NotFound` | 07, 03, 09 |
| `activities.enrol(activity, person, channel, actor, answers)` | activitat, persona, canal, respostes del formulari | `Enrolment` (amb càrrec o en llista d'espera) | `ActivityNotOpen`, `AlreadyEnrolled`, `NonMembersNotAllowed`, `RequirementsNotMet` (si `block`) | Vistes |
| `activities.cancel_enrolment(enrolment, reason, actor)` | — | proposta de devolució si estava pagada | `CancellationClosed` | Vistes |
| `activities.cancel_activity(activity, reason, actor)` | — | — | `InvalidTransition` | Vistes |
| `activities.duplicate(activity, new_start, actor)` | — | activitat nova en `draft` | `NotAllowed` | Vistes; 11 (conferències) |
| `activities.enrolments(activity, statuses)` | — | inscripcions i persona (dades mínimes) | — | 03, 10 |
| `activities.attendance_for(person)` | persona | activitats a què ha assistit, amb dates | — | 12 (bitàcola); «Les meves activitats» |
| `activities.closing_blockers(activity)` | — | llista de motius | — | 09; fitxa de l'activitat |
| `activities.mark_closed(activity, actor)` | — | — | `ClosingBlocked` | Només 09 |
| `activities.on_charge_event(charge, event)` | càrrec, `paid` / `returned` / `cancelled` | actualitza la inscripció o el reforç | — | 05b, a través del registre de la 00 ([M02-14](#M02-14-aprovar)) |
| `activities.export_personal_data(person)`, `activities.anonymise(person)` | persona | — | — | 00 (RGPD) |

**Punts d'extensió i senyals** (perquè el 03 i altres mòduls s'hi enganxin sense que el 02 els importi)
| Nom | Tipus | Per a què |
|---|---|---|
| `activities.register_enrolment_section(section)` | registre | Afegir preguntes al formulari d'inscripció (el 03 hi posa el material) |
| `activities.register_closing_check(check)` | registre | Afegir motius que impedeixen tancar (el 03 hi posa «material pendent») |
| `activities.register_detail_section(section)` | registre | Afegir un bloc a «Les meves activitats» i a la fitxa d'administració (el 03 hi posa el material assignat) |
| `enrolment_confirmed`, `enrolment_cancelled`, `activity_duplicated(original, copy)`, `activity_done`, `activity_cancelled` | senyals | Avisar el 03 (assignacions, material típic) i, més endavant, el 10 i el 12 |

**Consumeix**
| Servei | Mòdul | Per a què |
|---|---|---|
| `persons.create_or_get(data)`, `guest_links.create(person, obj, purpose)`, `guest_links.resolve(token)` | 00 | No socis i enllaços (V-02) |
| `charges.create_charge(person, kind="inscripció", amount_cents, department, concept, origin="activities", activity)`, `charges.cancel(charge, reason)` | 00 | Inscripcions i reforç |
| `charges.register_handler("activities", activities.on_charge_event)` | 00 (nou, [M02-14](#M02-14-aprovar)) | Saber quan es paga |
| `members.is_member(person, on)` | 01 | Preu |
| `members.licence_record(person)` | 01 (nou, [M02-14](#M02-14-aprovar)) | Requisit de llicència |
| `payments.start_payment`, `payments.payment_status`, `payments.receipt_pdf` | 05b | Pagar i rebut |
| `payments.refund(attempt, amount_cents, reason, actor)` | 05b | El tresorer fa la devolució des de la proposta del 02 (B5 del 05b); el 02 no la crida mai sol |
| `files.render_private_pdf`, `files.store_private`, `mail.send`, `notices.post`, `audit.record`, `permissions.require` | 00 | Certificat, fotos, avisos, registre, permisos |

**Rutes.** Públiques (declarades): `/activitats`, `/activitats/{id}`, `/activitats/{id}/inscripcio` (inici del convidat). Compte personal: `/socis/activitats`, `/socis/activitats/{inscripcio}`, `/socis/activitats/{inscripcio}/calendari.ics`, `/socis/activitats/{inscripcio}/certificat`. Convidat: `/convidat/{enllaç}` (de la 00). Administració: `/gestio/activitats`, `/gestio/activitats/{id}`, `/gestio/activitats/{id}/participants`, `/gestio/activitats/{id}/llista` (mòbil), `/gestio/activitats/{id}/avaluacio`, `/gestio/activitats/{id}/resultats`, `/gestio/cataleg/cursos`, `/gestio/cataleg/especialitats`, `/gestio/sortides/tipus`, `/gestio/projectes`, `/gestio/projectes/{id}`.

<a id="M02-9-criteris"></a>
## M02-9 Criteris d'acceptació i casos límit

**Catàleg i activitats**
- **CA-M02-01** Donat un curs al catàleg, quan el responsable en canvia el preu de soci, llavors les activitats ja creades conserven el preu anterior i el canvi queda al registre amb el valor anterior.
- **CA-M02-02** Donat una activitat amb el preu diferent del catàleg, quan es desa sense nota, llavors es rebutja; amb nota, es desa i el tresorer rep l'avís.
- **CA-M02-03** Donat una sortida de medi ambient, quan es desa sense subtipus, llavors es rebutja; donat una d'immersió, quan es desa amb subtipus, llavors es rebutja.
- **CA-M02-04** Donat una activitat amb 2 sessions i 3 blocs de programa, quan es duplica amb una data d'inici 364 dies després, llavors la còpia és `draft`, té les mateixes sessions i blocs desplaçats 364 dies, cap inscripció ni pagament, i `duplicated_from` apunta a l'original.
- **CA-M02-05** Donat una activitat `draft`, quan un visitant demana el detall, llavors rep «no trobat».

**Inscripció i places**
- **CA-M02-06** Donat un soci actiu i una activitat oberta amb places, quan s'inscriu, llavors la inscripció és `pending_payment`, el càrrec és «inscripció» amb el preu de soci, l'activitat i el departament de l'activitat, i veu la pantalla de pagament.
- **CA-M02-07** Donat el càrrec pagat (notificació verificada al 05b), quan el 05b avisa el 02, llavors la inscripció és `confirmed`, el participant rep la confirmació amb el calendari i l'ingrés és a l'activitat (CA-T03.1, RN-T10).
- **CA-M02-08** Donat una activitat amb 1 plaça lliure, quan dues persones s'inscriuen alhora, llavors una queda `pending_payment` i l'altra `waitlisted` (prova de concurrència).
- **CA-M02-09** Donat una inscripció `pending_payment` sense pagar en el termini, quan passa el termini, llavors queda `expired`, el càrrec s'anul·la amb motiu i el primer de la llista d'espera rep l'oferta.
- **CA-M02-10** Donat una persona no sòcia i una activitat no oberta a no socis, quan s'hi vol inscriure, llavors es rebutja amb un missatge que diu com fer-se soci.
- **CA-M02-11** Donat una persona no sòcia i una activitat oberta a no socis, quan s'inscriu, llavors paga el preu de no soci amb un enllaç de convidat i cap pantalla no li mostra dades d'altres persones (CA-02.2 de la 00).
- **CA-M02-12** Donat `requirements_mode = warn` i un participant sense llicència vigent, quan s'inscriu, llavors pot fer-ho, veu l'avís i el responsable el veu marcat; amb `block`, es rebutja.
- **CA-M02-13** Donat un participant ja inscrit, quan s'hi torna a inscriure, llavors es rebutja (`AlreadyEnrolled`).

**Cancel·lacions**
- **CA-M02-14** Donat una inscripció pagada, quan el participant la cancel·la abans de la data límit, llavors queda `cancelled` i el tresorer té una proposta de devolució; cap devolució no es fa sense el tresorer.
- **CA-M02-15** Donat una sortida amb 10 inscrits pagats i 2 pendents, quan el responsable la cancel·la per meteorologia, llavors l'activitat és `cancelled`, hi ha 10 propostes de devolució del 100 %, els 2 càrrecs pendents s'anul·len i els 12 i la llista d'espera reben l'avís.

**El dia, avaluació i certificat**
- **CA-M02-16** Donat un instructor I1 de la sessió S1, quan obre la llista de S2 (d'un altre instructor), llavors rep «no trobat» i l'intent queda al registre (CA-12.1 de la 00).
- **CA-M02-17** Donat la llista al mòbil sense cobertura, quan l'instructor marca un alumne, llavors la marca es mostra «pendent d'enviar» i s'envia sola en tornar la connexió, sense duplicar-se.
- **CA-M02-18** Donat un alumne avaluat «necessita reforç», quan l'instructor proposa 2 classes i el responsable les confirma, llavors l'alumne té 2 sessions noves només seves, l'horari del grup no canvia i hi ha un càrrec de reforç a la mateixa activitat.
- **CA-M02-19** Donat un alumne sense resultat apte, quan es vol emetre el certificat, llavors es rebutja; quan és apte, el certificat té un número únic i l'alumne el pot descarregar.
- **CA-M02-20** Donat un canvi d'hora d'una sessió d'una activitat oberta, quan es desa, llavors tots els inscrits vius reben l'avís (RN-M02-18).

**Medi ambient, tancament i permisos**
- **CA-M02-21** Donat 3 sortides d'un projecte amb 12,5 kg, 8 kg i 4,25 kg de residus, quan s'obre la fitxa del projecte, llavors el total és **24,75 kg** (24.750 grams).
- **CA-M02-22** Donat una foto marcada «hi surten persones» sense consentiment, quan es vol marcar com a publicable, llavors es rebutja.
- **CA-M02-23** Donat una activitat amb una inscripció `pending_payment`, quan es demana `closing_blockers`, llavors la llista la conté; quan el 09 crida `mark_closed`, es rebutja.
- **CA-M02-24** Donat cada cel·la de [M02-4](#M02-4-rols), quan el rol prova l'acció, llavors el resultat coincideix.
- **CA-M02-25** Donat una revisió del model, quan s'executa, llavors cap camp del 02 guarda dades de salut, de targeta ni d'IBAN.

**Casos límit**
| # | Cas | Comportament |
|---|---|---|
| L-M02-01 | El participant paga just quan la inscripció caduca | Si el pagament es confirma després de `expired`, el càrrec ja és anul·lat: el 05b el marca «a revisar» com a duplicat (RN-M05b-08) i es fa la devolució; si encara hi ha plaça, el responsable el pot reinscriure |
| L-M02-02 | El soci es dona de baixa amb una inscripció de soci | Manté el preu de soci (RN-M02-04) |
| L-M02-03 | Es redueixen les places per sota de les ocupades | Es rebutja; primer s'han de cancel·lar inscripcions |
| L-M02-04 | Es canvia la data d'una activitat amb inscripcions pagades | S'avisa (RN-M02-18); qui no pugui venir pot cancel·lar amb la regla de RN-M02-13 [A validar: junta] |
| L-M02-05 | Un instructor deixa de tenir el rol | Les seves sessions futures queden sense instructor i surten marcades al responsable |
| L-M02-06 | Activitat gratuïta | Sense càrrec; `confirmed` directament; la llista d'espera funciona igual |
| L-M02-07 | Esborrat RGPD d'un participant | Inscripcions i assistència anonimitzades; càrrecs i pagaments bloquejats fins al termini legal (028); els recomptes de places i de residus no canvien |
| L-M02-08 | Un menor vol inscriure's | No hi ha data de naixement (P-33): el responsable ho resol fora de la plataforma fins que es decideixi |
| L-M02-09 | Cap activitat publicada | «Ara no hi ha cap activitat oberta» i enllaç per rebre el butlletí (07) |
| L-M02-10 | Duplicar una activitat cancel·lada | Permès: la còpia és `draft` i neta |

<a id="M02-10-tasques"></a>
## M02-10 Tasques (per dependències, sense dates)

| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M02-01 | Wireframes que falten (vegeu [M02-5](#M02-5-processos)) | M | `design/wireframes/` | — | Revisats; contrast, estats amb símbol i botons grans al mòbil |
| T-M02-02 | Models de catàleg, tipus, subtipus i projectes; dades inicials | M | `apps/activities/models.py`, migracions | T-M01-09 (càrrec i departament de la 00) | RN-M02-01; CA-M02-03 |
| T-M02-03 | Model `Activity`, `Session`, `ProgrammeBlock` i transicions | L | `models.py`, `apps/activities/states.py` | T-M02-02 | RN-M02-02, 20 |
| T-M02-04 | Permisos del 02 per rol i per objecte (instructor → les seves sessions) | M | `apps/activities/permissions.py` | T-M02-03; permisos de la 00 | CA-M02-16, 24 |
| T-M02-05 | Catàlegs a l'administració i avís de canvi de preu | M | vistes, plantilles | T-M02-02 | CA-M02-01, 02 |
| T-M02-06 | Crear, editar, publicar i cancel·lar activitats; sessions i programa | M | vistes | T-M02-03, T-M02-04 | CA-M02-03, 05 |
| T-M02-07 | Duplicar (026) | M | `apps/activities/duplicate.py` | T-M02-06 | CA-M02-04; L-M02-10 |
| T-M02-08 | Llistat i detall públics; enllaç de previsió; calendari descarregable | M | vistes públiques | T-M02-06 | RN-M02-24, 25 |
| T-M02-09 | Punts d'extensió i senyals (formulari, tancament, blocs de pantalla) | S | `apps/activities/extensions.py` | T-M02-03 | Prova amb un mòdul fals |
| T-M02-10 | Gestor del càrrec pagat (`on_charge_event`) i registre de la 00 | S | `apps/activities/charges.py`, `apps/core/charges.py` | Aprovació de [M02-14](#M02-14-aprovar) punt 3; T-M05b-05 | CA-M02-07 |
| T-M02-11 | Inscripció del soci amb preu, requisits i càrrec | L | `apps/activities/enrolment.py` | T-M02-09, T-M02-10, T-M02-23 | CA-M02-06, 12, 13 |
| T-M02-12 | Control de places amb bloqueig i llista d'espera | L | `enrolment.py` | T-M02-11 | CA-M02-08 |
| T-M02-13 | Terminis de pagament, ofertes i caducitat (tasques a la cua) | M | `apps/activities/tasks.py` | T-M02-12 | CA-M02-09; L-M02-01 |
| T-M02-14 | Inscripció de convidat i inscripció presencial | M | vistes | T-M02-11; enllaços de convidat de la 00 | CA-M02-10, 11 |
| T-M02-15 | Cancel·lacions i propostes de devolució | M | `apps/activities/cancellation.py` | T-M02-12; T-M05b-13 | CA-M02-14, 15 |
| T-M02-16 | Passar llista des del mòbil (HTMX, reintent sense cobertura) i incidències | M | vistes, plantilles | T-M02-04 | CA-M02-17 |
| T-M02-17 | Avaluació per pràctica i «El meu progrés» | M | `apps/activities/assessment.py` | T-M02-16 | HU-M02-12, 14 |
| T-M02-18 | Classes de reforç: proposta, confirmació, sessions i càrrec | L | `apps/activities/reinforcement.py` | T-M02-17, T-M02-10 | CA-M02-18 |
| T-M02-19 | Resultat, certificat en PDF i titulació del club | M | `apps/activities/certificates.py` | T-M02-17 | CA-M02-19 |
| T-M02-20 | Resultats ambientals, fotos amb permís i fitxa de projecte | M | `apps/activities/environment.py` | T-M02-06 | CA-M02-21, 22 |
| T-M02-21 | Avisos: confirmació, recordatoris, canvi de programa, missatge als inscrits | M | `apps/activities/notifications.py` | T-M02-11 | CA-M02-20; RN-M02-19 |
| T-M02-22 | «Les meves activitats», `attendance_for` i comprovacions de tancament | M | vistes, `services.py` | T-M02-16, T-M02-09 | CA-M02-23 |
| T-M02-23 | Titulacions de la persona (declarades i del club) i servei de llicència del 01 | M | `models.py`; `apps/members/services.py` | Aprovació de [M02-14](#M02-14-aprovar) punt 2 | RN-M02-10 |
| T-M02-24 | Informes operatius: participants, horari imprimible, ocupació (CSV i impressió) | S | vistes | T-M02-12 | Proves de permisos |
| T-M02-25 | Dades de prova inventades: catàlegs, activitats, inscrits, avaluacions | S | `apps/activities/fixtures/` | T-M02-20 | Es carreguen amb una ordre |
| T-M02-26 | Proves de principi a fi amb `FakeProvider` | L | `tests/` | T-M02-11 a T-M02-22 | Totes en verd |
| T-M02-27 | Guia del responsable i de l'instructor; ajuda per inscriure's | S | `docs/` | T-M02-26 | Revisades |

<a id="M02-11-proves"></a>
## M02-11 Pla de proves

- **Unitàries (B1):** transicions d'activitat i d'inscripció; preu de soci o no soci; desplaçament de dates en duplicar; places ocupades; terminis i ofertes; requisits en mode avís i bloqueig; suma de residus en grams.
- **Concurrència:** dues i deu inscripcions alhora a l'última plaça; oferta i nova inscripció alhora.
- **Integració:** inscripció → pagament amb `FakeProvider` → `on_charge_event` → `confirmed` → ingrés a l'activitat (04); cancel·lació per meteorologia → propostes → devolució pel tresorer (05b); reforç → càrrec → pagament.
- **Permisos (B4):** una prova per cel·la de [M02-4](#M02-4-rols); instructor fora de les seves sessions; convidat només la seva inscripció.
- **Contracte:** serveis i senyals de [M02-8](#M02-8-serveis) amb un mòdul fals que s'hi registra.
- **Accessibilitat i dispositius (B5, B6, B8):** passar llista al mòbil amb xarxa lenta i sense connexió; botons d'almenys 44 × 44 px; estats amb símbol, text i color; anuncis amb `role="status"`.
- **Dades:** només inventades; cap nom real ni foto real.

<a id="M02-12-seguretat"></a>
## M02-12 Seguretat i RGPD

- **Mínim de dades:** el públic veu només el nombre de places lliures; l'instructor, el que diu [M02-4](#M02-4-rols); ningú no veu els altres inscrits des de l'àrea de socis.
- **Sense dades de salut** (P-07): ni certificats mèdics, ni aptituds, ni accidents. Text d'ajuda als camps lliures i revisió a les proves; risc a [M02-13](#M02-13-riscos).
- **Convidats:** enllaç de la 00 (V-02): caducitat, límit d'intents, testimoni fora dels registres.
- **Fotos:** fitxers privats (annex B de la 00) a la UE; autor, permís i consentiment abans de publicar (P-41). Les metadades de geolocalització de les fotos s'eliminen en pujar-les.
- **Tercers:** cap giny ni script de la previsió marítima ni de Minka (046); només enllaços. Cap dada personal no surt cap a aquests serveis (035).
- **Pagaments:** el 02 no veu mai targetes ni IBAN; el càrrec el cobra el 05b.
- **Registre:** inscripcions, cancel·lacions, canvis de preu, assistència, avaluacions, resultats i certificats queden al registre d'activitat amb el valor anterior.
- **Conservació:** inscripcions i assistència es conserven mentre la persona no en demani l'esborrat; els càrrecs i pagaments, fins al termini legal (028) [A validar: gestoria, Q-14].

<a id="M02-13-riscos"></a>
## M02-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| Catàleg, preus i política de cancel·lació no fixats | Alt per entrar en producció | Tot és configurable; els supòsits de sota fan funcionar el codi | Junta |
| Notes lliures (incidències, avaluacions) amb dades de salut | Alt (RGPD, P-07) | Text d'ajuda, límits de llargada, formació a la guia, revisió periòdica pel responsable | Junta |
| Termini de pagament curt per a qui paga per transferència | Mitjà (inscripcions que caduquen) | RN-M02-08 configurable per activitat; avís abans que caduqui | Tresorer |
| Les dues ampliacions de contracte de mòduls aprovats no s'aproven | Alt: sense la del 05b, el 02 no sap quan es paga | Alternativa: el 02 consulta l'estat del càrrec a la cua cada pocs minuts (pitjor: retard i més càrrega) | Responsable del projecte |
| Concurrència a l'última plaça | Mitjà | Bloqueig de fila i prova de concurrència (CA-M02-08) | Informàtica |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M02-01 | Llicència no vigent o titulació insuficient: avís o bloqueig (RN-M02-10) | Avís | Junta |
| S-M02-02 | Termini de pagament d'una inscripció (RN-M02-08) | 72 hores | Tresorer |
| S-M02-03 | Termini per acceptar una oferta de plaça (RN-M02-09) | 48 hores | Junta |
| S-M02-04 | Simpatitzants i ple dret paguen el mateix preu de soci (RN-M02-04) | Sí | Junta |
| S-M02-05 | Política de cancel·lació i devolució, també per meteorologia (RN-M02-12, 13) | El tresorer decideix cas per cas; 100 % si cancel·la el club | Junta |
| S-M02-06 | Els no socis es poden apuntar i a quin preu (F §4) | Sí, si l'activitat ho permet, al preu de no soci | Junta |
| S-M02-07 | Llista de cursos i d'especialitats amb preus de soci i de no soci | Catàleg buit; dades inventades a les proves | Junta |
| S-M02-08 | Preu de les classes de reforç: per classe o per proposta (RN-M02-15) | Per proposta confirmada | Junta |
| S-M02-09 | Qui emet el certificat i en quin format; numeració `C-AAAA-NNNN` (RN-M02-16) | Certificat del club signat pel responsable | Junta |
| S-M02-10 | Relació entre el certificat del club i la titulació oficial (federació o agència) | Es tramita fora de la plataforma | FECDAS |
| S-M02-11 | Llista de nivells i d'agències de titulació | Text lliure | FECDAS |
| S-M02-12 | Tipus de sortida: Sèniors i jornades obertes són tipus propis (F §5) | Sí, com a dades inicials desactivables | Junta |
| S-M02-13 | Llista de subtipus de medi ambient i projectes actuals | Només «Neteja»; cap projecte | Responsable del projecte |
| S-M02-14 | Dades ambientals que s'han de registrar (F §5) | Residus en kg, espècies, observacions i fotos | Junta |
| S-M02-15 | Dies del recordatori (RN-M02-19) | 2 dies abans | Secretaria |
| S-M02-16 | La secretaria pot fer inscripcions presencials (AC5) | No; només el responsable i l'administrador | Junta |
| S-M02-17 | Dades dels alumnes que veu l'instructor ([M02-4](#M02-4-rols); Q-01) | Nom, titulació, llicència sí o no, assistència i avaluacions | Junta |
| S-M02-18 | El responsable veu els imports cobrats de totes les activitats o només de les seves (AC19; Q-01) | Totes | Junta |
| S-M02-19 | Requisits d'edat i socis menors (P-33) | No es comproven | Junta |
| S-M02-20 | Protocol d'accidents i contacte d'emergència dels participants | Fora de la plataforma | Junta |
| S-M02-21 | Servei de previsió marítima enllaçat (RN-M02-24) | Meteocat, només enllaç | Responsable del projecte |
| S-M02-22 | Pujar observacions a Minka | Fora d'abast; caldrà saber si les dades queden dins la UE | Responsable del projecte |
| S-M02-23 | Les propostes de devolució viuen al 02 (`RefundProposal`) i el tresorer les fa amb el 05b | Sí; si més endavant el 05b en té una llista general, s'hi mouen | Informàtica |

**Revisió de dubtes (aplicada a mà)**
1. **El 05b (aprovat) només avisa el 01 quan es paga un càrrec.** Sense un registre per mòdul d'origen, el 02 no sap quan una inscripció és pagada. És la peça que més bloqueja. Propietari: responsable del projecte (aprovar-la).
2. **El 01 (aprovat) guarda la llicència però no ofereix cap servei per llegir-la.** És una lectura petita, però canvia el contracte d'un mòdul aprovat. Propietari: responsable del projecte.
3. **«Tancada econòmicament» és un estat del 02, però el tancament és del 09, que es construeix després.** Fins que existeixi el 09, les activitats queden `done`. Si el club vol tancar-les abans, caldria avançar una part del 09. Propietari: tresorer.
4. **Reforç després del tancament econòmic:** si un alumne necessita reforç quan el 09 ja ha congelat el marge del curs, el càrrec nou no hi entraria. Proposta per al 09: no tancar un curs amb reforç en curs, o imputar-lo al període següent. Propietari: tresorer.
5. **F §4 deia que el responsable de cursos confirma el reforç i F §5 parla d'un «responsable de sortides i medi ambient»;** la spec 00 té un sol rol «responsable de cursos i sortides». Si són persones diferents amb permisos diferents, cal un rol nou (P-04). Propietari: junta.
6. **«Grup de comunicació» de F §5 vs. el xat del 10:** el 02 només envia missatges d'un sentit; si el club vol substituir el grup de WhatsApp des del primer dia, el 10 s'ha d'avançar. Propietari: junta.
7. **Pagar amb Bizum una inscripció que caduca mentre s'espera la confirmació:** RN-M02-08 allarga el termini mentre l'intent és «en curs»; si el proveïdor no informa mai, la caducitat del 05b ho acaba resolent. Propietari: informàtica.
8. **El material llogat el paga el participant** (F §6) però el 02 cobra la inscripció abans de saber si es lloga. Es resol al 03 amb un càrrec a part ([M03-7](#M03-7-regles)). Propietari: junta i tresorer.

<a id="M02-14-aprovar"></a>
## M02-14 Què cal aprovar abans de començar

1. **Aquesta secció del 02**, amb els estats, la plantilla de duplicar (RN-M02-21) i la separació 02 ↔ 03 per senyals i punts d'extensió.
2. **Ampliació del contracte del 01** (aprovat): servei de només lectura `members.licence_record(person)` (tipus i data de caducitat). Bloqueja T-M02-23.
3. **Ampliació del contracte de la 00 i del 05b** (aprovats): registre `charges.register_handler(origin, handler)` i que el 05b avisi el mòdul d'origen de cada càrrec pagat, retornat o anul·lat (el 01 hi passa a ser un origen més). No canvia cap regla del 05b. Bloqueja T-M02-10 i, per tant, la inscripció.
4. **Supòsits per defecte** S-M02-01 (avís), S-M02-02 (72 hores), S-M02-04 (mateix preu de soci), S-M02-05 (devolució decidida pel tresorer; 100 % si cancel·la el club) i S-M02-06 (no socis si l'activitat ho permet) [A validar: junta i tresorer]. No bloquegen el codi: són valors configurables.
5. **Per entrar en producció** (no per començar): catàleg amb preus (S-M02-07) i política de cancel·lació (S-M02-05) [A validar: junta].

---

<a id="M03"></a>
# Mòdul 03 — Material

**Estat: escrit**, per aprovar pel responsable del projecte.

**Fonts:** document de funcionalitats (F §6 Material i cost per participant, processos 9.6 i 9.7), mapa de la plataforma v8 (M04 Material), respostes del responsable del projecte del 20/10/2026 (llista de tipus, ampolla amb litres lliures, stock de tot el material, material al registre d'immersió, tarifes per centre amb marge propi) i del 22/10/2026 (les classes de reforç són un ús nou de material), decisions [013](decisions/013-imputacio-comissions.md), [026](decisions/026-duplicar-activitats-al-modul-02.md), [035](decisions/035-dades-nomes-dins-ue.md) i [046](decisions/046-interficie-django-htmx-servida-des-del-vps.md); [spec 00](../specs/00-base-comuna/spec.md) (càrrec, importacions, fitxers); secció [M02](#M02).

**Proveïdor de pagaments.** El 03 no cobra res directament. Si s'aprova que el participant paga el lloguer a part (RN-M03-11), el 03 crea un càrrec de la 00 i el cobra el [05b](#M05b-8-serveis) a través de l'adaptador.

<a id="M03-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Respondre per a cada activitat què fa servir cada participant, d'on surt (propi, del club o llogat a un centre de busseig) i quant costa; portar l'inventari de tot el material del club peça per peça, amb stock i revisions; i donar al 09 el cost de material i el marge dels lloguers. |
| **Processos que cobreix** | P-M03-A Inventari, tipus i stock · P-M03-B Centres de busseig i tarifes · P-M03-C Necessitats a la inscripció · P-M03-D Assignar, llogar, lliurar i retornar (F 9.6) · P-M03-E Quantitats reals, registre d'immersió i cost per participant · P-M03-F Revisions (F 9.7) · P-M03-G Càrrega inicial de l'inventari |
| **Tasques** | 21 (T-M03-01 a T-M03-21) |
| **Què el bloqueja** | Per construir: el 02 (activitats, inscripcions i punts d'extensió). Per entrar en producció: centres i tarifes, peces actuals del club i regla del cost d'ús [A validar: junta]; qui paga el material llogat [A validar: junta i tresorer] |
| **Què cal aprovar** | Aquesta secció; la regla que evita comptar dues vegades el lloguer al marge (RN-M03-10); els supòsits S-M03-01 a S-M03-04 ([M03-14](#M03-14-aprovar)) |

<a id="M03-1-intencio"></a>
## M03-1 Intenció, abast i fora d'abast

**Per què.** Avui el material es porta amb Excel: qui porta què, què es lloga i a quin centre, i quant costa. És una de les peces que cap programa comercial cobreix (F §6), i sense ella el marge de cada activitat no és real.

**Resultat esperat.**
- El responsable de material sap en tot moment quantes peces hi ha de cada tipus i talla, i quantes estan disponibles, assignades, en ús o en revisió.
- Per a cada activitat, sap què necessita cada participant, què li assigna el club i què s'ha de llogar a cada centre, amb la llista per enviar.
- Cap peça no s'assigna a dues activitats el mateix dia, ni si està en revisió.
- Cada participant veu al seu historial el material que ha fet servir a cada activitat.
- El 09 rep el cost de material de cada activitat i el marge de cada lloguer sense tornar a escriure res.

**Com sabrem que funciona.**
- L'stock surt de l'inventari i quadra amb un recompte físic.
- Una assignació que solapa dies amb una altra de la mateixa peça es rebutja, també des de la base de dades.
- El cost per participant d'una activitat de prova coincideix amb el càlcul a mà de l'exemple de [M03-7](#M03-7-regles).
- Cap revisió no passa de data sense que el responsable n'hagi rebut l'avís.

**Dins de l'abast.**
- Tipus de material i inventari peça per peça (codi, tipus, talla o litres, estat, compra, propera revisió, historial).
- Stock per tipus, talla i estat a una data.
- Centres de busseig i tarifes (preu de cost i preu per al soci) amb versions.
- Material típic per curs, especialitat o tipus de sortida, que s'aplica a l'activitat i es copia en duplicar.
- Necessitats del participant al formulari d'inscripció del 02 («porto el meu» o «necessito», amb talla).
- Assignació per participant: propi, del club o llogat; lliurament, retorn i peces a revisió.
- Llista de lloguer per centre, exportable i imprimible.
- Càrrec del lloguer al participant, si s'aprova (RN-M03-11).
- Quantitats reals després de l'activitat, material al registre d'immersió i cost per participant i per activitat.
- Revisions: calendari, avisos, registre i cost.
- Càrrega inicial de l'inventari amb la importació de la 00.

**Fora d'abast.**
- **Factures dels centres i despeses de revisió:** són despeses amb factura del 09. El 03 en dona les dades per casar-les.
- **Marge de l'activitat:** el calcula i el congela el 09 amb el cost que li dona el 03.
- **Bitàcola** (hores, profunditat, insígnies): mòdul 12. El 03 dona el material de cada activitat.
- **Botiga i venda de material:** mòdul 13, fora d'abast.
- Lectura de codis de barres o QR de les peces: idea per a més endavant (el codi de la peça ja hi és).
- Dades del cos (pes, alçada) per triar ploms o talles: no es guarden; la persona tria la talla.

<a id="M03-2-dependencies"></a>
## M03-2 Dependències

**De què depèn.**
| Mòdul | Què en fa servir el 03 |
|---|---|
| 00 | Càrrec (lloguer al participant, si s'aprova); importacions (càrrega inicial); permisos; registre d'activitat; correu i avisos |
| 02 | Activitats, dates i sessions de reforç; inscripcions; senyals `enrolment_confirmed`, `enrolment_cancelled`, `activity_duplicated`, `activity_done`, `activity_cancelled`; punts d'extensió del formulari d'inscripció, del tancament i de les pantalles ([M02-8](#M02-8-serveis)) |
| 05b | Cobrar el càrrec de lloguer (si s'aprova RN-M03-11), com qualsevol càrrec d'inscripció |

**Què depèn del 03.**
| Mòdul | Què necessita |
|---|---|
| 02 | Motiu «material pendent» per no tancar; material típic a la còpia; bloc de material a «Les meves activitats» i a la fitxa |
| 09 | Cost de material per activitat i per participant; lloguers per centre per casar la factura; marge dels lloguers; cost de les revisions |
| 08 | Stock, material més usat, revisions properes |
| 12 | Material fet servir a cada activitat (bitàcola) |

<a id="M03-3-capacitats"></a>
## M03-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | Pantalla (proposta) | Wireframe |
|---|---|---|---|---|
| C1 | Mantenir tipus de material i inventari | Resp. material | Inventari; Fitxa de la peça | Falta |
| C2 | Veure l'stock per tipus, talla i estat | Resp. material | Stock | Falta |
| C3 | Mantenir centres de busseig i tarifes | Resp. material | Centres i tarifes | Falta |
| C4 | Material típic per curs, especialitat o tipus de sortida | Resp. cursos i sortides; Resp. material | Material típic | Falta |
| C5 | Indicar què porta i què necessita | Participant | Inscriure'm (bloc del 03 dins el formulari del 02) | Falta |
| C6 | Assignar, marcar llogat, lliurar i retornar | Resp. material | Material de l'activitat | `admin.html#material-assignat` |
| C7 | Llista de lloguer per centre | Resp. material | Llista de lloguer | Falta |
| C8 | Quantitats reals i cost per participant | Resp. material | Material de l'activitat; Cost per participant | Falta |
| C9 | Revisions i avisos | Resp. material | Revisions | Falta |
| C10 | Veure el seu material per activitat | Participant | Les meves activitats (bloc del 03) | Falta |
| C11 | Càrrega inicial de l'inventari | Resp. material; Administrador | Importar inventari | Falta |

**Històries d'usuari**
- **HU-M03-01.** Com a responsable de material, vull donar d'alta cada peça amb un codi, el tipus, la talla (o els litres, a les ampolles) i la propera revisió, per saber què tenim.
- **HU-M03-02.** Com a responsable de material, vull veure quants jaquets de talla M hi ha disponibles el dia d'una sortida.
- **HU-M03-03.** Com a responsable de material, vull guardar per a cada centre el preu de cost i el preu per al soci de cada equip, i que el marge surti sol.
- **HU-M03-04.** Com a participant, vull marcar peça per peça si porto el meu material o el necessito, amb la talla, quan m'inscric.
- **HU-M03-05.** Com a responsable de material, vull assignar peces de l'inventari i que la plataforma no em deixi posar la mateixa peça a dues activitats el mateix dia.
- **HU-M03-06.** Com a responsable de material, vull marcar el que s'ha de llogar i treure la llista per a cada centre, per enviar-la abans de la sortida.
- **HU-M03-07.** Com a responsable de material, vull registrar què ha tornat i què ha d'anar a revisió.
- **HU-M03-08.** Com a responsable de material, vull rebre un avís abans de cada revisió i que una peça en revisió no es pugui assignar.
- **HU-M03-09.** Com a responsable de cursos i sortides, vull que cada tipus de sortida porti el seu material típic, i que es copiï quan dupliqui una activitat.
- **HU-M03-10.** Com a tresorer, vull veure el cost de material de cada participant i de cada activitat, i el marge dels lloguers.
- **HU-M03-11.** Com a soci, vull veure el material que vaig fer servir a cada immersió.

<a id="M03-4-rols"></a>
## M03-4 Rols i permisos

Llegenda com a [M01-4](#M01-4-rols). A les taules, «[A validar]» sense propietari vol dir **junta** (Q-01, P-04).

| # | Acció | Visitant | Part. no soci | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Resp. comunicació | Dept. Història | Junta | Administrador | Resp. botiga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MT1 | Indicar què porta i què necessita (inscripció) | — | Propi (enllaç) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| MT2 | Veure el seu material per activitat | — | Propi (enllaç) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| MT3 | Mantenir tipus i inventari; donar de baixa una peça | — | — | — | — | — | — | Sí | — | — | — | — | Sí | — |
| MT4 | Veure l'stock | — | — | — | — | — | Consulta | Sí | Consulta | — | — | Consulta | Sí | — |
| MT5 | Material típic | — | — | — | — | — | Sí | Sí | — | — | — | — | Sí | — |
| MT6 | Assignar, marcar llogat, lliurar i retornar | — | — | — | — | — | [A validar] | Sí | — | — | — | — | Sí | — |
| MT7 | Veure el material dels participants d'una activitat | — | — | — | Les seves | — | Sí | Sí | — | — | — | — | Sí | — |
| MT8 | Centres de busseig i tarifes | — | — | — | — | — | Consulta | Sí | Consulta | — | — | [A validar] | Sí | — |
| MT9 | Llista de lloguer: generar, exportar i marcar enviada | — | — | — | — | — | Sí | Sí | — | — | — | — | Sí | — |
| MT10 | Quantitats reals després de l'activitat | — | — | — | [A validar] | — | — | Sí | — | — | — | — | Sí | — |
| MT11 | Revisions | — | — | — | — | — | — | Sí | — | — | — | — | Sí | — |
| MT12 | Cost per participant i per activitat; marge dels lloguers | — | — | — | — | — | Consulta [A validar: Q-01] | Sí | Sí | — | — | Consulta | Sí | — |
| MT13 | Càrrega inicial de l'inventari | — | — | — | — | — | — | Sí | — | — | — | — | Sí | — |

**Per objecte.**
- **Participant:** només les seves necessitats i el seu material; ni el material ni les talles d'altres persones.
- **Instructor:** el material assignat als alumnes de les seves sessions (per comprovar-lo abans d'entrar a l'aigua), sense costos.
- **Responsable de material:** tot l'inventari i totes les assignacions; dels participants veu nom, talles i necessitats, no pagaments ni dades de contacte.
- **Tresorer:** costos, tarifes i marges; no les talles.

<a id="M03-5-processos"></a>
## M03-5 Processos pas per pas

**Wireframes existents:** `admin.html#material-assignat` (llista de peces assignades a una activitat amb codi, participant, import i estat «Lliurat» o «Per recollir»). **Falten** (T-M03-01): inventari i fitxa de la peça, stock, centres i tarifes, material típic, bloc del formulari d'inscripció, material de l'activitat amb els tres orígens, llista de lloguer, cost per participant, revisions i càrrega inicial.

**Estat d'una peça del club.** F §6 parla de «disponible → assignada → en ús → retornada, i en revisió». Com que una mateixa peça pot estar assignada a activitats de dies diferents, la peça només guarda l'estat operatiu i la resta surt de les assignacions:
| Estat que es veu | D'on surt |
|---|---|
| **Disponible** (en una data) | Peça `available` sense cap assignació viva que inclogui aquella data |
| **Assignada** | Assignació `planned` que inclou la data |
| **En ús** | Assignació `delivered` (lliurada i no retornada) |
| **Retornada** | Esdeveniment de l'assignació (`returned`); la peça torna a `available` o passa a `in_review` |
| **En revisió** | Peça `in_review` |
| **De baixa** | Peça `retired`, amb motiu (perduda, trencada, revisió fallida) |

### P-M03-A Inventari, tipus i stock
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Resp. material | Revisa els tipus (aletes, màscara, tub, neoprè, escarpins, ploms, jaquet, regulador, ordinador, brúixola, boia, llanterna, ganivet de seguretat, ampolla) i n'afegeix si cal |
| 2 | Resp. material | Dona d'alta una peça: codi (proposat pel sistema, `MAT-NNNN`), tipus, talla o litres, data i cost de compra (opcionals), propera revisió |
| 3 | Sistema | La fitxa de la peça mostra l'historial: assignacions, revisions, canvis d'estat |
| 4 | Resp. material | Obre «Stock» per a una data: recompte per tipus i talla (o litres) i per estat |

### P-M03-B Centres de busseig i tarifes
1. El responsable crea el centre (nom, adreça, contacte del centre) i, per a cada equip o servei, el **preu de cost** i el **preu per al soci** (i, si cal, el de no soci) [A validar: junta, S-M03-01].
2. El sistema mostra el marge de cada línia. Canviar una tarifa crea una versió nova amb data d'inici; les assignacions anteriors conserven la tarifa que tenien (RN-M03-06).

### P-M03-C Necessitats a la inscripció (F 9.6 pas 1)
1. El formulari d'inscripció del 02 mostra el bloc del 03 amb el **material típic** de l'activitat: per a cada peça, «porto el meu» o «necessito», i la talla.
2. Les respostes es desen com a necessitats de la inscripció. Una inscripció a la llista d'espera també les guarda.

### P-M03-D Assignar, llogar, lliurar i retornar (F 9.6 passos 2-5)
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Resp. material | Obre «Material de l'activitat»: per a cada participant `confirmed`, el que porta, el que necessita i el que ja té assignat | Material de l'activitat |
| 2 | Resp. material | **Del club:** tria una peça disponible de la talla; el sistema només n'ofereix de disponibles aquells dies i rebutja el solapament (RN-M03-02, 03) | ídem |
| 3 | Resp. material | **Llogat:** tria el centre i la línia de tarifa; es copien el preu de cost i el preu per al participant (RN-M03-06) | ídem |
| 4 | Sistema | Si s'aprova RN-M03-11, crea el càrrec del lloguer al participant i l'avisa | — |
| 5 | Resp. material | Genera la **llista de lloguer** de cada centre (agrupada per tipus i talla, amb una referència per participant), l'exporta o l'imprimeix, l'envia pel canal del club i la marca «enviada» | Llista de lloguer |
| 6 | Resp. material | El dia de l'activitat marca cada peça del club com a **lliurada** | ídem |
| 7 | Resp. material | En tornar, marca cada peça com a **retornada** i tria «disponible» o «a revisió» | ídem |

### P-M03-E Quantitats reals, registre d'immersió i cost (F 9.6 passos 4 i 6)
1. Després de l'activitat, el responsable confirma què s'ha fet servir de veritat: una assignació pot quedar «no s'ha fet servir» (per exemple, un participant que no ha vingut).
2. El material fet servir passa al registre de la persona per a aquella activitat (`equipment.used_by`).
3. El sistema calcula el cost per participant i per activitat (RN-M03-08 a 10) i el deixa a punt per al 09.

### P-M03-F Revisions (F 9.7)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Sistema | Cada dia, avisa el responsable (correu i avís a l'app) de les peces amb la revisió a menys de 30 dies [A validar: junta, S-M03-06] i de les vençudes |
| 2 | Resp. material | Envia la peça a revisió: passa a `in_review` i no es pot assignar. Si tenia assignacions futures, surten marcades per canviar-les |
| 3 | Resp. material | En tornar, registra la data, el resultat, el proveïdor, el cost i la propera revisió. Si és correcta, `available`; si no, `retired` amb motiu |
| 4 | Sistema | El cost queda a la revisió perquè el 09 el casi amb la factura (despesa amb factura) |

### P-M03-G Càrrega inicial de l'inventari
1. El responsable puja un CSV (codi, tipus, talla o litres, data de compra, propera revisió) amb la importació de la 00: lot, validació sense escriure res, confirmació i opció de desfer.
2. En desenvolupament i proves, només amb dades inventades.

<a id="M03-6-entitats"></a>
## M03-6 Entitats i camps

App Django `equipment` (nova). Noms de codi en anglès. Imports en cèntims. Les FK cap a models del 02 són només de lectura: el 03 no hi escriu mai.

### EquipmentType (tipus de material)
`name` (`CharField(60)`, únic), `sizing` (`size`, `litres`, `none`), `requires_review` (bool), `active`. Dades inicials: els 14 tipus de F §6. Ampolla: `sizing = litres`.

### EquipmentItem (peça)
| Camp | Tipus | Restriccions |
|---|---|---|
| `code` | `CharField(20)` | Únic. Proposta `MAT-NNNN` |
| `type` | FK EquipmentType (PROTECT) | — |
| `size` | `CharField(10)` | Obligatori si `sizing = size` |
| `litres` | `DecimalField(4,1)` | Obligatori i > 0 si `sizing = litres`; nul altrament (`CHECK`) |
| `status` | `available`, `in_review`, `retired` | RN-M03-04 |
| `purchased_on` | `DateField` null | — |
| `purchase_cost_cents` | `PositiveIntegerField` null | Per a l'amortització, si s'aprova (RN-M03-08) |
| `next_review_on` | `DateField` null | Obligatori si `requires_review` |
| `retired_reason` | `TextField` | Obligatori si `retired` |
| `notes` | `TextField` | — |
**Índexs:** `(type, size, litres, status)`. Una peça amb assignacions no s'esborra; es dona de baixa.

### DiveCentre i CentreRate (centre i tarifa)
- `DiveCentre`: `name` (únic), `address`, `contact_email`, `contact_phone` (del centre, no de persones), `active`.
- `CentreRate`: `centre` (FK), `label` (`CharField(80)`, equip o servei), `equipment_type` (FK null), `cost_cents`, `member_price_cents`, `non_member_price_cents` (null) [A validar: junta, S-M03-01], `valid_from` (`DateField`), `superseded_by` (FK self null). Una tarifa usada en una assignació no es modifica: es crea una versió nova.

### ActivityTypicalEquipment i TypicalEquipmentTemplate (material típic)
- `TypicalEquipmentTemplate`: `catalogue_entry` (FK 02 null) o `outing_type` (FK 02 null) (exactament un, `CHECK`), `equipment_type`, `quantity_per_participant` (`PositiveSmallIntegerField`).
- `ActivityTypicalEquipment`: `activity` (FK 02), `equipment_type`, `quantity_per_participant`. Es crea en crear l'activitat a partir de la plantilla i es copia en duplicar.

### EquipmentNeed (necessitat del participant)
`enrolment` (FK 02), `equipment_type`, `brings_own` (bool), `size` (`CharField(10)`), `litres` (null). Únic `(enrolment, equipment_type)`.

### EquipmentAssignment (assignació)
| Camp | Tipus | Restriccions |
|---|---|---|
| `activity` | FK Activity (02) | — |
| `enrolment` | FK Enrolment (02) | Participant |
| `session` | FK Session (02) null | Només per a classes de reforç (ús nou de material) |
| `equipment_type` | FK EquipmentType | — |
| `origin` | `own`, `club`, `rented` | — |
| `item` | FK EquipmentItem null | Obligatori si `origin = club`; nul altrament (`CHECK`) |
| `centre`, `rate` | FK null | Obligatoris si `origin = rented` (`CHECK`) |
| `period` | `DateRangeField` | Dies de l'activitat (o de la sessió de reforç) |
| `cost_cents` | `PositiveIntegerField` | Còpia: 0 si propi; cost d'ús si del club; preu de cost si llogat |
| `participant_price_cents` | `PositiveIntegerField` | Còpia: preu per al participant (lloguer) o 0 |
| `status` | `planned`, `delivered`, `returned`, `not_used`, `cancelled` | RN-M03-12 |
| `delivered_at`, `returned_at` | `DateTimeField` null | — |
| `charge` | FK càrrec (00) null | Si s'aprova RN-M03-11 |
**Restricció d'exclusió (PostgreSQL, `btree_gist`):** `EXCLUDE USING gist (item WITH =, period WITH &&) WHERE (item IS NOT NULL AND status IN ('planned','delivered'))`. És la garantia de RN-M03-02 encara que dues persones assignin alhora.

### RentalList (llista de lloguer)
`activity`, `centre`, `generated_by`, `generated_at`, `fingerprint` (empremta del contingut), `sent_at` null, `sent_by` null. El contingut es genera a demanda a partir de les assignacions i no es desa (com el fitxer de la remesa del 05b).

### EquipmentReview (revisió)
`item` (FK), `kind` (`hydrostatic_test`, `visual_inspection`, `regulator_service`, `other`), `due_on`, `sent_on` null, `done_on` null, `provider` (`CharField(120)`), `result` (`ok`, `failed`, null), `cost_cents` null, `next_review_on` null, `notes`, `recorded_by`. Només s'hi afegeix un cop tancada.

### UsageRate (cost d'ús del material del club)
`equipment_type`, `cost_per_day_cents`, `valid_from`. Sense cap fila, el cost d'ús és 0 (RN-M03-08).

**Migracions:** reversibles; extensió `btree_gist` i restricció d'exclusió en una migració pròpia amb prova; tipus inicials en una migració de dades; cap dada personal.

<a id="M03-7-regles"></a>
## M03-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M03-01 | Tres orígens del material: **propi** (cost 0 per al club), **del club** (cost d'ús) i **llogat** a un centre (preu de cost de la tarifa) | F §6 |
| RN-M03-02 | Una peça del club no es pot assignar a dues activitats amb dies que es toquin. Ho garanteix la restricció d'exclusió de la base de dades, no només la pantalla | F §6 i 9.6 |
| RN-M03-03 | No es pot assignar una peça `in_review` o `retired`, ni una que tingui la revisió vençuda abans de l'últim dia de l'activitat | F 9.7; proposta |
| RN-M03-04 | Estats de la peça: `available ⇄ in_review`; `available → retired`; `in_review → retired`. «Assignada», «en ús» i «retornada» surten de les assignacions ([M03-5](#M03-5-processos)) | F §6 |
| RN-M03-05 | Ampolla: capacitat en litres com a número lliure positiu amb un decimal com a màxim (10, 12, 15 o el que sigui). La resta de tipus, talla en text curt o res | F §6; resposta del 20/10/2026 |
| RN-M03-06 | Tarifes per centre amb versions: un canvi crea una versió nova amb data d'inici. En assignar un lloguer, es copien el preu de cost i el preu per al participant de la versió vigent el primer dia de l'activitat | F §6 |
| RN-M03-07 | Marge d'un lloguer = preu per al participant − preu de cost. Si és negatiu, es pot desar però surt marcat al tresorer | F §6; resposta del 20/10/2026 |
| RN-M03-08 | Cost d'ús d'una peça del club = dies de l'assignació × `cost_per_day_cents` del seu tipus vigent. Sense tarifa, 0. La fórmula (amortització o tarifa fixa per tipus) la fixa la junta [A validar: junta i tresorer, S-M03-02] | F §6 |
| RN-M03-09 | Cost de material d'un participant = suma del `cost_cents` de les seves assignacions fetes servir (`returned` o `delivered`); `not_used` i `cancelled` no compten | F §6 |
| RN-M03-10 | **Per al marge del 09:** el «cost de material» de la fórmula de CLAUDE.md és el cost d'ús del material del club (RN-M03-08). El lloguer entra al marge com a **despesa** quan es registra la factura del centre (09); mentre no hi és, el 09 fa servir el cost estimat de les tarifes. Mai totes dues coses alhora, per no comptar el lloguer dues vegades | CLAUDE.md; F §6 i §7 |
| RN-M03-11 | El participant paga el material llogat al preu per al participant de la tarifa (F §6). Supòsit: quan el responsable confirma un lloguer, es crea un **càrrec a part** de tipus «inscripció» amb aquest preu, l'activitat i el departament de l'activitat, i es cobra amb el 05b [A validar: junta i tresorer, S-M03-03]. El material del club no es cobra al participant mentre la junta no en fixi un preu | F §6; [M02-13](#M02-13-riscos), dubte 8 |
| RN-M03-12 | Transicions de l'assignació: `planned → delivered → returned`; `planned → not_used / cancelled`; `delivered → not_used` (no s'ha fet servir). En retornar, la peça passa a `available` o `in_review` | F 9.6 |
| RN-M03-13 | «Material pendent» (motiu per no tancar l'activitat, registrat al 02): assignacions `planned` o `delivered` després de l'activitat, necessitats «necessito» sense assignació, lloguers sense quantitat real confirmada i llistes de lloguer no marcades «enviades» | F §5 i §6 |
| RN-M03-14 | Una peça lliurada que no s'ha retornat 7 dies després de l'activitat [A validar: junta, S-M03-06] surt a l'avís diari del responsable | Proposta |
| RN-M03-15 | Avís de revisió 30 dies abans de `next_review_on` [A validar: junta, S-M03-06] i cada dia mentre estigui vençuda. La plataforma no calcula terminis legals: la data la posa el responsable segons la normativa o el fabricant [A verificar: normativa d'equips a pressió per a les ampolles; fabricant per als reguladors] | F 9.7 |
| RN-M03-16 | Stock en una data: per tipus i talla (o litres), recompte de peces disponibles, assignades, en ús i en revisió. Les peces `retired` no hi compten | F §6 |
| RN-M03-17 | Material típic: en crear una activitat, es copia la plantilla del curs, de l'especialitat o del tipus de sortida; en duplicar-la, es copia el de l'original (026, RN-M02-21) | F §6; 026 |
| RN-M03-18 | Llista de lloguer: agrupada per tipus i talla, amb una referència per participant (número d'inscripció i inicials), no el nom complet ni el contacte [A validar: junta, S-M03-04]. Es genera a demanda, no es desa, i queda al registre amb l'empremta | Proposta; RGPD |
| RN-M03-19 | Una classe de reforç és un ús nou de material: té les seves assignacions, amb el període de la sessió (resposta del 22/10/2026) | Resposta del 22/10/2026 |
| RN-M03-20 | Si s'esborra una inscripció (cancel·lació), les seves assignacions `planned` passen a `cancelled` i les peces queden lliures; si hi havia un càrrec de lloguer pendent, s'anul·la; si estava pagat, es proposa la devolució amb la mateixa regla del 02 | RN-M02-12, 13 |

**Exemples numèrics (imports inventats)**
- **Solapament (RN-M03-02):** l'ampolla `MAT-0007` està assignada a una sortida del 14 al 15 de juny. Assignar-la a un curs el 15 de juny → rebutjat per la base de dades; el 16 de juny → acceptat.
- **Lloguer i marge (RN-M03-06, 07):** al centre A, «equip complet» té preu de cost **2500** i preu per al soci **3000** → marge **500** per lloguer. Quatre lloguers: ingrés 12.000, cost 10.000, marge **2000**.
- **Cost d'ús (RN-M03-08):** si la junta fixa 200 cèntims per dia per a les ampolles, sis ampolles en una sortida d'un dia → **1200**. Sense tarifa → 0.
- **Cost per participant (RN-M03-09):** P1 porta tot el seu material → **0**. P2 fa servir una ampolla del club (200) i un equip llogat al centre A (2500) → **2700**. P3 tenia una ampolla assignada però no ha vingut (`not_used`) → **0**.
- **Sense duplicar el lloguer (RN-M03-10):** amb els quatre lloguers de l'exemple, abans de la factura el 09 resta 10.000 d'estimat; quan es registra la factura del centre (per exemple, 10.000), resta la factura i deixa de restar l'estimat. Si la factura diu 10.400, la diferència de 400 es veu com a desviació.

<a id="M03-8-serveis"></a>
## M03-8 Serveis i interfícies (contracte)

Cap altra app escriu als models del 03.

**Ofereix**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| Bloc del formulari d'inscripció (registrat amb `activities.register_enrolment_section`) | activitat, inscripció | preguntes i desament de les necessitats | `InvalidSize` | 02 |
| Comprovació de tancament (registrada amb `activities.register_closing_check`) | activitat | motius de RN-M03-13 | — | 02 → 09 |
| Bloc de material a «Les meves activitats» i a la fitxa (registrat amb `activities.register_detail_section`) | inscripció o activitat | fragment HTML | — | 02 |
| `equipment.activity_material_cost(activity)` | activitat | `{club_use_cents, rental_cost_estimated_cents, rental_participant_cents, rental_margin_cents, per_participant: […]}` | — | 09 |
| `equipment.rentals_for(activity, centre)` | — | línies de lloguer per casar la factura | — | 09 |
| `equipment.reviews_with_cost(period)` | — | revisions amb cost, per casar factures | — | 09 |
| `equipment.used_by(person)` | persona | per activitat, el material fet servir (tipus, talla o litres, origen) | — | 02 (bloc), 12 |
| `equipment.stock(on=date, filters)` | — | recomptes | — | 08 |
| `equipment.export_personal_data(person)`, `equipment.anonymise(person)` | persona | — | — | 00 (RGPD) |

**Consumeix**
| Servei o senyal | Mòdul | Per a què |
|---|---|---|
| `activities.get_activity`, `activities.enrolments(activity, statuses)` | 02 | Participants i dates |
| `enrolment_confirmed`, `enrolment_cancelled`, `activity_duplicated`, `activity_done`, `activity_cancelled` | 02 (senyals) | Preparar l'assignació, alliberar peces, copiar el material típic, demanar quantitats reals |
| `activities.register_enrolment_section`, `register_closing_check`, `register_detail_section` | 02 | Punts d'extensió |
| `charges.create_charge(person, kind="inscripció", …, origin="equipment", activity)`, `charges.cancel` | 00 | Càrrec del lloguer (si s'aprova RN-M03-11) |
| `imports.create_batch(kind="equipment", …)` | 00 | Càrrega inicial |
| `mail.send`, `notices.post`, `audit.record`, `permissions.require` | 00 | Avisos, registre, permisos |

**Rutes (administració):** `/gestio/material`, `/gestio/material/peces/{codi}`, `/gestio/material/stock`, `/gestio/material/centres`, `/gestio/material/centres/{id}`, `/gestio/material/tipic`, `/gestio/material/revisions`, `/gestio/material/importar`, `/gestio/activitats/{id}/material`, `/gestio/activitats/{id}/material/lloguer/{centre}`. Compte personal: el bloc dins `/socis/activitats/{inscripcio}`. Cap ruta pública.

<a id="M03-9-criteris"></a>
## M03-9 Criteris d'acceptació i casos límit

- **CA-M03-01** Donat el tipus «Ampolla», quan es dona d'alta una peça sense litres o amb 0, llavors es rebutja; amb 12, s'accepta; amb 11,5, s'accepta.
- **CA-M03-02** Donat la peça `MAT-0007` assignada del 14 al 15 de juny, quan s'assigna a una altra activitat el 15 de juny (també des de dues sessions alhora), llavors es rebutja; el 16 de juny, s'accepta.
- **CA-M03-03** Donat una peça `in_review`, quan es vol assignar, llavors no surt a la llista i, si es força la petició, es rebutja.
- **CA-M03-04** Donat una peça amb la revisió vençuda abans de l'últim dia de l'activitat, quan es vol assignar, llavors es rebutja amb el motiu.
- **CA-M03-05** Donat una tarifa usada en una assignació, quan el responsable en canvia el preu, llavors es crea una versió nova i l'assignació conserva els imports anteriors.
- **CA-M03-06** Donat una inscripció amb «necessito jaquet, talla M», quan el responsable obre el material de l'activitat, llavors la necessitat hi surt i només s'hi ofereixen jaquets M disponibles aquells dies.
- **CA-M03-07** Donat quatre lloguers al centre A, quan es genera la llista, llavors agrupa per tipus i talla, porta referències i no noms complets ni contactes, no es desa i queda al registre amb l'empremta.
- **CA-M03-08** Donat els exemples de [M03-7](#M03-7-regles), quan es demana `activity_material_cost`, llavors el cost de P1, P2 i P3 és 0, 2700 i 0; i, a l'activitat amb quatre lloguers al centre A, el marge dels lloguers és 2000.
- **CA-M03-09** Donat una activitat amb una peça lliurada i no retornada, quan el 02 demana les comprovacions de tancament, llavors hi surt «material pendent».
- **CA-M03-10** Donat una activitat duplicada, quan es crea la còpia, llavors té el mateix material típic i cap assignació.
- **CA-M03-11** Donat una peça amb revisió d'aquí a 30 dies, quan s'executa l'avís diari, llavors el responsable rep un correu i un avís a l'app (sense push).
- **CA-M03-12** Donat una revisió fallida, quan es registra, llavors la peça passa a `retired` amb el motiu i les seves assignacions futures surten marcades.
- **CA-M03-13** Donat un lloguer confirmat i RN-M03-11 aprovada, quan es confirma, llavors el participant té un càrrec del preu per al participant a la mateixa activitat i departament, i el pot pagar amb el 05b.
- **CA-M03-14** Donat una inscripció cancel·lada amb una peça `planned`, quan es cancel·la, llavors l'assignació passa a `cancelled` i la peça torna a estar disponible aquells dies.
- **CA-M03-15** Donat el stock d'una data, quan es compara amb les peces, llavors disponibles + assignades + en ús + en revisió = total de peces no `retired`.
- **CA-M03-16** Donat cada cel·la de [M03-4](#M03-4-rols), quan el rol prova l'acció, llavors el resultat coincideix.
- **CA-M03-17** Donat un CSV d'inventari amb una fila sense tipus, quan es valida, llavors la fila surt amb l'error i no s'escriu res fins a confirmar.

**Casos límit**
| # | Cas | Comportament |
|---|---|---|
| L-M03-01 | No hi ha prou peces de la talla | Es pot marcar «llogat» o assignar una altra talla amb nota |
| L-M03-02 | El centre canvia la tarifa després d'enviar la llista | L'assignació manté la tarifa copiada; la diferència apareixerà en registrar la factura (09) |
| L-M03-03 | Una peça es perd durant l'activitat | Assignació `returned` amb nota i peça `retired` amb motiu «perduda»; qui en paga el cost: [A validar: junta] |
| L-M03-04 | Un participant porta el seu material però el dia en necessita | Assignació nova el mateix dia; si és llogat, càrrec nou (si s'aprova RN-M03-11) |
| L-M03-05 | L'activitat es cancel·la | Totes les assignacions `cancelled`; les llistes de lloguer ja enviades surten marcades per avisar el centre |
| L-M03-06 | Una ampolla de 2 × 7 litres (bibotella) | Es desa com a 14 litres amb nota [A validar: junta] |
| L-M03-07 | Esborrat RGPD d'un participant | Necessitats i assignacions anonimitzades; els costos de l'activitat no canvien |
| L-M03-08 | Cap peça a l'inventari | «Encara no hi ha cap peça» i enllaç a la càrrega inicial |

<a id="M03-10-tasques"></a>
## M03-10 Tasques (per dependències, sense dates)

| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M03-01 | Wireframes que falten (vegeu [M03-5](#M03-5-processos)) | M | `design/wireframes/` | — | Revisats; contrast i estats amb símbol |
| T-M03-02 | Tipus de material i dades inicials | S | `apps/equipment/models.py`, migracions | T-M02-02 | RN-M03-05; CA-M03-01 |
| T-M03-03 | Inventari de peces, estats, baixa i historial | M | `models.py`, vistes | T-M03-02 | RN-M03-04 |
| T-M03-04 | Stock en una data | S | `apps/equipment/stock.py` | T-M03-08 | CA-M03-15 |
| T-M03-05 | Centres de busseig i tarifes amb versions | M | `models.py`, vistes | T-M03-02 | CA-M03-05 |
| T-M03-06 | Material típic: plantilles, còpia a l'activitat i en duplicar | S | `apps/equipment/typical.py` | T-M02-07, T-M02-09 | CA-M03-10 |
| T-M03-07 | Bloc del formulari d'inscripció i necessitats | M | `apps/equipment/enrolment.py` | T-M02-09, T-M02-11 | HU-M03-04 |
| T-M03-08 | Assignació amb la restricció d'exclusió (`btree_gist`) | L | `models.py`, migració, `assignments.py` | T-M03-03, T-M03-07 | CA-M03-02, 03, 04, 06 |
| T-M03-09 | Lliurament, retorn i pas a revisió | S | `assignments.py`, vistes | T-M03-08 | RN-M03-12 |
| T-M03-10 | Llista de lloguer per centre (CSV i impressió, sense desar-la) | M | `apps/equipment/rentals.py` | T-M03-05, T-M03-08 | CA-M03-07 |
| T-M03-11 | Càrrec del lloguer al participant (condicional) | M | `rentals.py` | T-M03-10; aprovació de RN-M03-11; T-M02-10 | CA-M03-13 |
| T-M03-12 | Quantitats reals i servei `used_by` | S | `assignments.py` | T-M03-09 | HU-M03-11 |
| T-M03-13 | Cost per participant i per activitat; servei per al 09 | M | `apps/equipment/costs.py` | T-M03-12 | CA-M03-08; RN-M03-10 |
| T-M03-14 | Revisions: registre, avisos diaris a la cua, peces vençudes | M | `apps/equipment/reviews.py`, tasques | T-M03-03 | CA-M03-11, 12 |
| T-M03-15 | Comprovació de tancament i bloc de «Les meves activitats» | S | `apps/equipment/extensions.py` | T-M03-12, T-M02-22 | CA-M03-09 |
| T-M03-16 | Cancel·lacions: alliberar peces i anul·lar càrrecs de lloguer | S | `assignments.py` | T-M03-08, T-M03-11 | CA-M03-14 |
| T-M03-17 | Càrrega inicial de l'inventari amb la importació de la 00 | M | `apps/equipment/imports.py` | T-M03-03 | CA-M03-17 |
| T-M03-18 | Permisos per rol i per objecte | S | `apps/equipment/permissions.py` | T-M03-03 | CA-M03-16 |
| T-M03-19 | Informes: cost per participant i activitat, material més usat, revisions properes | S | vistes | T-M03-13, T-M03-14 | Proves de permisos |
| T-M03-20 | Dades inventades i proves de principi a fi (inscripció → necessitat → assignació → lliurament → retorn → cost) | L | `apps/equipment/fixtures/`, `tests/` | T-M03-08 a T-M03-17 | Totes en verd |
| T-M03-21 | Guia del responsable de material | S | `docs/` | T-M03-20 | Revisada |

<a id="M03-11-proves"></a>
## M03-11 Pla de proves

- **Unitàries (B1):** litres i talles; transicions de peça i d'assignació; versions de tarifa; marge del lloguer; cost d'ús per dies; cost per participant; avís de revisió; stock en una data.
- **Base de dades:** la restricció d'exclusió amb assignacions simultànies i dies que es toquen (el darrer dia d'una i el primer de l'altra).
- **Integració amb el 02:** inscripció amb necessitats; cancel·lació que allibera peces; duplicat amb material típic; tancament bloquejat per material pendent.
- **Integració amb el 05b:** càrrec del lloguer pagat amb `FakeProvider` (si s'aprova RN-M03-11).
- **Contracte per al 09:** `activity_material_cost` amb l'exemple de [M03-7](#M03-7-regles), inclòs el cas sense factura i amb factura (RN-M03-10).
- **Permisos (B4):** una prova per cel·la de [M03-4](#M03-4-rols); el participant no veu el material d'altres.
- **Accessibilitat i dispositius (B5, B8):** pantalla de lliurament i retorn usable al mòbil; estats amb símbol, text i color.
- **Dades:** només inventades.

<a id="M03-12-seguretat"></a>
## M03-12 Seguretat i RGPD

- **Mínim de dades:** el 03 només guarda talles i necessitats lligades a la inscripció; cap dada del cos (pes, alçada) ni de salut.
- **Llista de lloguer:** surt cap a un tercer (el centre). Només referències i talles; si el centre necessita noms (per exemple, per a la seva assegurança), cal decidir-ho i informar-ne els participants [A validar: junta, S-M03-04]. Es genera a demanda i no es desa.
- **Centres:** si un centre rep dades personals, ha de ser dins la UE ([035](decisions/035-dades-nomes-dins-ue.md)) i cal un acord de tractament [A validar: gestoria].
- **Registre:** altes, baixes, assignacions, lliuraments, retorns, tarifes i revisions queden al registre amb el valor anterior.
- **Imports:** cap dada de pagament; el càrrec del lloguer el cobra el 05b.

<a id="M03-13-riscos"></a>
## M03-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| Inventari inicial desconegut | Alt per a l'stock i les assignacions | Càrrega en CSV; recompte físic abans de producció | Junta |
| Centres i tarifes no recollits | Alt per al marge dels lloguers | Tarifes configurables; el marge surt quan s'hi posen | Junta |
| Comptar el lloguer dues vegades al marge (tarifa i factura) | Alt per al marge | RN-M03-10 i prova de contracte amb el 09 | Tresorer |
| Assignacions fetes fora de la plataforma el dia de l'activitat | Mitjà (stock incorrecte) | Pantalla mòbil de lliurament; avís de peces no retornades | Junta |
| Cost d'ús sense fórmula | Mitjà (marge incomplet) | Cost 0 fins que la junta decideixi | Junta i tresorer |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M03-01 | Centres de busseig amb què treballa el club, preu de cost i preu per al soci de cadascun; si hi ha preu de no soci | Cap centre; tarifes inventades a les proves | Junta |
| S-M03-02 | S'imputa un cost d'ús al material del club; amortització o tarifa fixa per tipus (RN-M03-08) | Cost 0 | Junta i tresorer |
| S-M03-03 | El material llogat es cobra en un càrrec a part o inclòs al preu de la inscripció (RN-M03-11) | Càrrec a part en confirmar el lloguer | Junta i tresorer |
| S-M03-04 | Dades que rep el centre a la llista de lloguer (RN-M03-18) | Referència i inicials, sense nom complet | Junta |
| S-M03-05 | Peces de cada tipus i talla que té avui el club | Inventari buit; càrrega en CSV | Junta |
| S-M03-06 | Dies d'antelació de l'avís de revisió i de peces no retornades (RN-M03-14, 15) | 30 i 7 dies | Junta |
| S-M03-07 | Periodicitat legal de les revisions (ampolles i reguladors) | La data la posa el responsable | Informàtica (consultar la normativa i els fabricants) |
| S-M03-08 | Qui paga una peça perduda o trencada per un participant (L-M03-03) | Ningú automàticament; el responsable ho anota | Junta |
| S-M03-09 | Bibotelles i equips compostos (L-M03-06) | Una peça amb els litres totals | Junta |
| S-M03-10 | El responsable de cursos i sortides també assigna material (MT6) | No | Junta |
| S-M03-11 | Format dels codis de les peces | `MAT-NNNN`; si ja tenen etiquetes, es respecten | Junta |

**Revisió de dubtes (aplicada a mà)**
1. **F §6 diu que el participant paga el lloguer, però el 02 cobra la inscripció abans de saber si es lloga.** El càrrec a part (RN-M03-11) ho resol, però dona dos pagaments per activitat. L'alternativa és cobrar un preu de material fix a la inscripció. Propietari: junta i tresorer.
2. **«Retornada» com a estat de la peça** (F §6) no funciona si la peça té assignacions a dies diferents. Es tracta com un esdeveniment de l'assignació. Propietari: cap (coherent amb F 9.6 pas 4).
3. **El marge de CLAUDE.md** (ingressos − despeses − cost de material) no diu si el lloguer és despesa o cost de material. RN-M03-10 el fa despesa (factura) i deixa el cost de material per al del club. El 09 ho ha de respectar. Propietari: tresorer.
4. **Dades del centre:** si el centre necessita el nom i el document de cada persona per a la seva assegurança, la plataforma passaria dades a un tercer; cal base legal i informar-ne. Propietari: junta.
5. **Revisions amb terminis legals:** les ampolles tenen proves periòdiques obligatòries; la plataforma no les calcula perquè no les tenim confirmades. Si el club vol que les calculi, cal la norma exacta. Propietari: informàtica.
6. **Ploms:** es compten per peces (cinturons o blocs) i no per quilos. Si el club els porta per quilos, el tipus necessita una unitat diferent. Propietari: junta.

<a id="M03-14-aprovar"></a>
## M03-14 Què cal aprovar abans de començar

1. **Aquesta secció del 03**, amb l'estat de la peça derivat de les assignacions ([M03-5](#M03-5-processos)) i la restricció d'exclusió.
2. **RN-M03-10** (el lloguer entra al marge com a despesa amb factura; el cost de material és el del club), perquè el 09 hi quedi lligat.
3. **Supòsits per defecte** S-M03-02 (cost d'ús 0), S-M03-03 (càrrec a part del lloguer) i S-M03-04 (referència i inicials a la llista) [A validar: junta i tresorer]. No bloquegen el codi.
4. **Per entrar en producció** (no per començar): centres i tarifes (S-M03-01) i inventari inicial (S-M03-05) [A validar: junta].

---

<a id="preguntes"></a>
# Apèndix — Preguntes per propietari

Recull de totes les preguntes obertes ([A verificar] i [A validar]) dels mòduls d'aquest pla, agrupades per qui les ha de respondre. La pregunta completa i el supòsit vigent són a la secció de l'ID. **«Bloqueja»** diu quin mòdul o quina tasca no es pot acabar sense la resposta; «—» vol dir que hi ha un supòsit i el codi no s'atura. Quan es respon una pregunta, s'actualitza la secció del mòdul i se'n treu la fila d'aquí.

<a id="preguntes-banc"></a>
**Banc**
| ID | Pregunta | Bloqueja |
|---|---|---|
| P-44 | Quin és el banc del club i si ofereix TPV virtual (amb PaynoPain) a una associació | 05a i 05b: proveïdor real (amb `FakeProvider` es pot avançar) |
| P-45 punt 5; S-M05a-01 | Admet remeses pain.008? Quin és l'identificador de creditor del club? Admet mandats signats electrònicament? Pot custodiar els mandats (044)? | 05a: producció de la campanya; 05b: T-M05b-10 i T-M05b-11 |
| S-M05b-05 | Versió de pain.008, terminis de presentació, comissió per rebut i per retornat, fitxer de retornats | 05b: T-M05b-10 |
| S-M04-03; P-45 punt 10 | Format de l'extracte (CSV o Norma 43) i una mostra anonimitzada | — (supòsit CSV); conciliació real del 04 |
| S-M04-08 | Abona les remeses rebut a rebut o en total? | — |
| S-M05a-04 | Format de la referència del mandat | — |
| S-M05a-05 | Admet un titular del compte diferent del soci? (també junta) | — |
| S-M05a-06 | Admet IBAN de fora d'Espanya? | — |
| S-M05a-11 | Caducitat d'un mandat sense cobraments (36 mesos) | — |
| S-M05b-06 | Termini de l'avís previ (14 dies) segons el text del mandat (també tresorer) | — |
| S-M01-25; S-M05a-14 | Es poden traspassar al club els mandats vigents de Cluber? (pregunta del tresorer, al banc o a la gestoria) | — (decideix l'abast de la campanya del 05a) |

<a id="preguntes-paynopain"></a>
**PaynoPain**
| ID | Pregunta | Bloqueja |
|---|---|---|
| P-45 punts 1 i 2 | Qui contracta el TPV i amb quines comissions (targeta, Bizum, devolucions, contracàrrecs) | 05b: producció |
| P-45 punt 3 | On són els servidors, quins subencarregats hi ha i si signen contracte d'encarregat; cap transferència fora de la UE (035) | 05b: producció |
| S-M05b-01; P-45 punt 4 | Camp de targeta incrustat o redirecció | — (l'adaptador admet tots dos) |
| S-M05b-02; P-45 punt 13 | Bizum per redirecció o sol·licitud a l'app; caducitat i reintents de les notificacions | — |
| S-M05b-03 | Es poden consultar les ordres (xarxa de seguretat)? | — |
| S-M05b-04; P-45 punt 7 | Devolucions per API, també de Bizum | — (supòsit: transferència des del banc) |
| S-M05a-02; P-45 punt 6 | Tokenització per a renovacions | 05a: T-M05a-12 |
| S-M05a-03; P-45 punt 8 | Entorn de proves i com es demana | — (`FakeProvider`) |
| S-M04-05 | La liquidació detalla la comissió de cada cobrament? | — (repartiment proporcional) |
| P-45 punt 9 | Format de les liquidacions (agrupades o per operació, brutes o netes) | 04: T-M04-13; 05b: T-M05b-14 |

<a id="preguntes-tresorer"></a>
**Tresorer**
| ID | Pregunta | Bloqueja |
|---|---|---|
| P-29; S-M01-03 | En quin moment de l'any es cobren les quotes i quan és la propera remesa | 05a: calendari de la campanya |
| S-M01-16 (Q-23) | Mostra anonimitzada de l'exportació de Cluber | 01: importació final real |
| P-28 | Què fa avui Cluber amb les llicències | — |
| P-12 | Registre manual de cobraments (efectiu): qui el pot fer i quin justificant cal (també junta) | Registre manual (RN-72 de la 00) |
| S-M01-04 | Dies dels recordatoris de quota | — |
| S-M01-05 | Quotes pendents en una baixa | — |
| S-M01-24 | Validesa del carnet dels socis importats amb la quota pagada a Cluber | — |
| S-M04-02 | Comptes bancaris del club | — |
| S-M04-04 | Caixa en efectiu i arqueig | — |
| S-M05a-07 | Calendari de recordatoris de la campanya | — |
| S-M05b-10 | Recordatori de transferència als 30 dies | — |
| S-M05b-11 | Format del número de rebut (també gestoria) | — |
| 044 | Norma d'esborrat del fitxer de la remesa al seu dispositiu; caducitat de l'enllaç de descàrrega d'un sol ús (millora opcional) | — |
| S-M02-02 | Termini de pagament d'una inscripció (72 hores) | — |

<a id="preguntes-junta"></a>
**Junta**
| ID | Pregunta | Bloqueja |
|---|---|---|
| P-04; S-M01-23 | Matriu dels 13 rols i rols nous (Junta, Resp. comunicació, Resp. botiga) | — (permisos configurables) |
| S-M01-01, 02 | Import del canvi a ple dret; quota sencera a mig any | — |
| S-M01-06, 07, 08 | Verificació pública del carnet (dígits, nom) i darrere del carnet | — |
| S-M01-09, 10, 11 | Soci clàssic, antiguitat en una readmissió, drets del simpatitzant | — |
| S-M01-12, 13, 14, 22 | Compte després de la baixa, socis menors (P-33), qui atén l'RGPD, conflicte d'interès | — |
| S-M04-01, 06, 07, 09 | Departaments i centres de cost (Q-17), ingrés de quotes, comissions de llicències, qui desfà conciliacions | — |
| S-M05a-09, 13 | Qui guarda la còpia de la clau; què veu la secretaria del mètode de pagament | 05a: nivell 1 (còpia de la clau) |
| M05a-14 punt 2 | Textos del mandat, la invitació i el correu G3 | 05a: producció |
| 025 | Autoritzacions del nivell 1 i del nivell 2 | Producció del 05a i del 05b |
| S-M05b-08, 09, 13 | Comissió de retorn, carnet amb una quota retornada, qui reenvia l'alternativa | — |
| P-48 | Doble aprovació (opcional i futura) | — |
| S-M02-01, 03, 04, 06 | Avís o bloqueig per requisits, termini de l'oferta, preu dels simpatitzants, no socis | — |
| S-M02-05 | Política de cancel·lació i devolució, també per meteorologia | 02: producció |
| S-M02-07 | Catàleg de cursos i d'especialitats amb preus | 02: producció |
| S-M02-08, 09 | Preu del reforç (per classe o per proposta); qui emet el certificat i com es numera | — |
| S-M02-12, 14 | Tipus de sortida propis (Sèniors, jornades obertes); dades ambientals | — |
| S-M02-16, 17, 18 | Inscripció presencial de la secretaria; dades que veu l'instructor; imports que veu el responsable (Q-01) | — |
| S-M02-19, 20 | Requisits d'edat; protocol d'accidents i contacte d'emergència | — |
| S-M03-01 | Centres de busseig i tarifes | 03: producció |
| S-M03-02, 03 | Cost d'ús del material del club; lloguer en càrrec a part (també tresorer) | — |
| S-M03-04 | Dades que rep el centre a la llista de lloguer | — |
| S-M03-05 | Inventari actual per tipus i talla | 03: producció |
| S-M03-06, 08, 09, 10, 11 | Dies dels avisos, peces perdudes, bibotelles, qui assigna, codis de les peces | — |

<a id="preguntes-gestoria"></a>
**Gestoria**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-15 (Q-14) | Terminis de conservació de quotes, rebuts i pagaments | — (es bloquegen fins que es digui) |
| S-M05b-12; P-47; P-02 | Què s'ha de facturar, IVA i obligació de Verifactu | 09 |
| M05b-12 | Informació a Hisenda dels cobraments per Bizum | — |
| S-M05a-08 | Proves de la signatura electrònica del mandat (també banc) | — |
| M03-12 | Acord de tractament amb els centres de busseig si reben dades personals | 03: llista de lloguer amb noms |

<a id="preguntes-fecdas"></a>
**FECDAS**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-17 | Tipus de llicència | 06 |
| S-M02-10 | Relació entre el certificat del club i la titulació oficial | — |
| S-M02-11 | Llista de nivells i d'agències de titulació | — |

<a id="preguntes-secretaria"></a>
**Secretaria**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-18 | Data d'alta dels socis que Cluber no té | — |
| S-M02-15 | Dies del recordatori d'una activitat | — |

<a id="preguntes-informatica"></a>
**Informàtica**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-19; P-46 | Remitent dels correus i proveïdor de correu (subencarregats de Brevo dins la UE) | 00: correu en producció |
| S-M01-20 | Eina d'auditoria d'accessibilitat | — |
| S-M05a-10 | Biblioteca de xifratge i rols de PostgreSQL separats | — |
| S-M05a-12 | Temps per tornar a demanar la contrasenya | — |
| S-M02-23 | On viuen les propostes de devolució | — |
| S-M03-07 | Periodicitat legal de les revisions d'ampolles i reguladors | — |

<a id="preguntes-responsable"></a>
**Responsable del projecte**
| ID | Pregunta | Bloqueja |
|---|---|---|
| M02-14 punt 2 | Servei `members.licence_record` al 01 (aprovat) | 02: T-M02-23 |
| M02-14 punt 3 | Avís del 05b al mòdul d'origen de cada càrrec (00 i 05b aprovats) | 02: T-M02-10 i la inscripció |
| RN-M03-10 | El lloguer entra al marge com a despesa amb factura | 09 |
| S-M02-13 | Llista de subtipus de medi ambient i projectes actuals | — |
| S-M02-21, 22 | Servei de previsió marítima enllaçat; pujar observacions a Minka | — |
| M02, M03 | Aprovar les seccions dels mòduls 02 i 03 | 02 i 03 |
