# Pla de la plataforma C.R.I.S., mòdul a mòdul

- **Què és:** l'únic fitxer del pla de tots els mòduls. S'hi afegeix un mòdul cada vegada, amb la mateixa estructura de 14 seccions.
- **Data de la versió:** 27/10/2026 (la data només identifica la versió; el pla no té calendari, [038](decisions/038-planificar-sense-dates.md)).
- **Com s'aprova:** cada secció de mòdul passa d'«escrit» a «aprovat» quan el responsable del projecte l'aprova. Cap mòdul nou s'afegeix fins que l'anterior està aprovat.

<a id="estat"></a>
## 1. Estat dels mòduls

Numeració de la sèrie B (CLAUDE.md). Ordre de fases segons la [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md). «Estat» és l'estat de la secció d'aquest pla, no del codi.

| Fase | Mòdul | Depèn de | Spec | Estat al pla |
|---|---|---|---|---|
| 1 | **00** Base comuna | — | [spec 00](../specs/00-base-comuna/spec.md) v2 | pendent (el M01 en defineix la part que necessita) |
| 1 | **01** Socis i carnet digital | 00 | No n'hi ha cap `spec.md`: aquest pla en fa de base (vegeu [M01-14](#M01-14-aprovar)) | **escrit** |
| 1 | **04** Tresoreria, part mínima | 00, 01 | [spec 04](../specs/04-tresoreria/spec.md) v2 | pendent |
| 1 | **05a** Alta del mètode de pagament i mandats | 01, 04 | — | pendent |
| 1 | **05b** Cobraments (targeta, Bizum, domiciliació, transferència) | 05a | — | pendent |
| 2 | **02** Activitats (cursos i sortides) | 01, 04 | — | pendent |
| 2 | **03** Material | 02 | — | pendent |
| 2 | **04** Resta (marge, despeses, ajuts, facturació) | 02, 03, 05b | — | pendent |
| 2 | **06** Llicències | 01, 05b | — | pendent |
| 2 | **07** Web pública | 01, 02 | — | pendent |
| 2 | **08** Dashboard | 02, 04 | — | pendent |
| Sense número | Missatges i xat per activitat | 01, 02 | — | pendent [A validar número] |
| Sense número | Departament d'Història i conferències | 01, 07 | — | pendent [A validar si va dins el 02] |
| Sense número | Idees noves (avatars de fauna marina, bitàcola) | 01, 03 | — | pendent |
| — | Botiga en línia | — | Fora d'abast ara | — |

La web instal·lable ([041](decisions/041-web-installable-i-avisos-sense-push.md)) no és un mòdul: va amb la interfície des del M01. Detall de la correspondència amb el mapa v8: [mapa-de-moduls.md](mapa-de-moduls.md).

<a id="index"></a>
## 2. Índex
1. [Estat dels mòduls](#estat)
2. [Índex](#index)
3. [Regles generals](#regles)
4. [Glossari](#glossari)
5. [Plantilla de secció de mòdul](#plantilla)
6. [Mòdul 01 — Socis i carnet digital](#M01)
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
- No s'edita cap decisió existent: se'n crea una de nova que la substitueix o l'amplia.
- No s'inventa res: el que falta porta [A verificar] (dada externa) o [A validar] (decisió del club), sempre amb propietari. Propietaris possibles: tresorer, junta, banc, PaynoPain, gestoria, FECDAS, secretaria, informàtica, responsable del projecte.

**Pila i interfície**
- Django i PostgreSQL ([002](decisions/002-pila-tecnologica.md)); cua de tasques sobre PostgreSQL ([012](decisions/012-cua-de-tasques.md)).
- **HTMX:** interfície amb plantilles de Django i HTMX servida des del mateix servidor. [A validar: responsable del projecte] La 002 diu «Django amb API REST» i web i PWA a Cloudflare Pages, i la 030 deixa la pila del frontend [A validar]. Cal una **decisió nova** (proposta 046) abans de programar la interfície (vegeu [M01-14](#M01-14-aprovar)).
- Web instal·lable, sense botigues i sense notificacions push ([041](decisions/041-web-installable-i-avisos-sense-push.md)).
- Interfície i documents en català; codi en anglès (V-09 de la spec 00).
- Sistema de disseny de les decisions [030](decisions/030-sistema-de-disseny.md) a [034](decisions/034-patrons-magic-portfolio.md): tokens, dos temes, estats amb símbol, text i color, objectiu WCAG 2.2 AA (checklist B8).

**Metodologia aplicada**
Les skills que es van demanar (spec-driven-development, product-capability, intent-driven-development, planning-and-task-breakdown, blueprint, contract-first, security-and-hardening, django-patterns, django-security, postgres-patterns, documentation-and-adrs, doubt-driven-development i accessibility) **no estan instal·lades**. La plantilla de la secció 5 n'aplica l'estructura a mà: intenció i capacitats (1, 3), contracte primer (8), blueprint de dades (6), tasques per dependències (10), seguretat (12) i revisió de dubtes (13).

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

<a id="plantilla"></a>
## 5. Plantilla de secció de mòdul

Cada mòdul es titula «Mòdul NN — Nom» amb l'ancora `MNN`, i té aquestes 14 seccions amb ancores estables `MNN-<número>-<nom>`:

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

**Fonts integrades:** el pla M01 del repositori anterior (aprovat amb respostes el 27/10/2026), la [spec 00](../specs/00-base-comuna/spec.md) v2, el document de funcionalitats (F §3 i processos 9.2 a 9.5 i 9.13), el mapa de la plataforma v8 i les decisions 035–045. **No hi ha cap `specs/01-…/spec.md` al repositori**: aquest pla en recull el contingut (vegeu [M01-14](#M01-14-aprovar)).

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
- Bitàcola i insígnies (P-38). Missatges. Botigues d'apps i notificacions push ([041](decisions/041-web-installable-i-avisos-sense-push.md)).
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
| Idees noves | Llavor de l'avatar fixada en l'alta |

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
| `avatar_seed` | `CharField(64)` null | Llavor aleatòria fixada en l'alta per a l'avatar futur (RN-M01-30) [A validar: responsable del projecte] |
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
| RN-M01-15 | Import del canvi a ple dret: diferència, complet o prorrata [A validar: junta]. Mentre no es decideixi, la secretaria l'introdueix a mà en aprovar (pla M01 anterior, R1) | F §3, pregunta 1 |
| RN-M01-16 | Un soci que s'apunta a mig any paga la quota sencera del període [A validar: junta] | F §9.2 («quota de l'any») |
| RN-M01-17 | Període de la quota = any natural; venciment [A validar: tresorer, P-29] | Proposta |
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
| RN-M01-30 | L'avatar futur es genera a partir del nom **en l'alta**; corregir el nom després no el canvia. El M01 desa una llavor aleatòria en l'alta i no implementa l'avatar | F §3; mapa v8 |
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
| `treasury.referencia_transferencia(càrrec)` | 04 | Mostrar com pagar per transferència (quan existeixi la 04) |

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
| T-M01-01 | Decisió nova sobre la interfície (Django + HTMX servit des del VPS) i sobre l'existència de la spec 01 | S | `docs/decisions/046-…md` | Aprovació ([M01-14](#M01-14-aprovar)) | Decisió acceptada |
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
| T-M01-24 | Importació de Cluber, **fase de prova** (sense escriure res) | L | `apps/members/imports/cluber.py` | T-M01-11; mostra anonimitzada (Q-23) | CA-M01-20, 21 |
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
| HTMX contradiu la 002 | Alt si no es decideix | Decisió nova abans de programar (T-M01-01) | Responsable del projecte |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M01-01 | Import del canvi a ple dret (diferència 55 €, complet o prorrata) | La secretaria l'escriu a mà | Junta |
| S-M01-02 | Quota sencera per a les altes a mig any | Sí | Junta |
| S-M01-03 | Període = any natural i data de venciment de les quotes | Any natural; venciment pendent (P-29) | Tresorer |
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
| S-M01-16 | Format i contingut de l'exportació de Cluber (Q-23) | CSV amb número, document, nom, tipus, estat, data d'alta, quotes i llicència | Tresorer |
| S-M01-17 | Tipus de llicència de la FECDAS | Text lliure fins a la 06 | FECDAS |
| S-M01-18 | Data d'alta desconeguda a Cluber | Data més antiga coneguda, aproximada | Secretaria |
| S-M01-19 | Remitent dels correus (Q-26) i proveïdor de correu (P-46) | `no-respon@cris1954.cat`, correu a la bústia de proves | Informàtica |
| S-M01-20 | Eina d'auditoria d'accessibilitat | axe amb Playwright | Informàtica |
| S-M01-21 | Llavor de l'avatar ja al M01 | Sí, un camp aleatori sense ús | Responsable del projecte |
| S-M01-22 | Conflicte d'interès (Q-11) | Ningú no aprova ni canvia el seu propi soci | Junta |
| S-M01-23 | Els rols Junta, Resp. comunicació i Resp. botiga existeixen al model (P-04) | Existeixen sense permisos al M01 | Junta |
| S-M01-24 | Quotes de socis importats pagades a Cluber per al període vigent (RN-M01-34) | El carnet és vàlid fins a final del període | Tresorer |

**Revisió de dubtes (doubt-driven, aplicada a mà)**
1. **El soci «pendent» no té carnet fins que paga, però el pagament no existeix fins al 05b.** En desenvolupament es prova amb `on_fee_paid` simulat; en producció no passa perquè el M01 no hi entra sol. Propietari: responsable del projecte.
2. **El pla M01 anterior deixava que el tresorer marqués quotes com a pagades a mà; ara això és el registre manual bloquejat per P-12 (RN-72).** S'ha tret del M01. Si el club vol cobrar en efectiu abans del 05b, cal resoldre P-12. Propietari: junta i tresorer.
3. **Els diners de Cluber no passen per la tresoreria de la plataforma.** Per això les quotes cobrades per Cluber són «quotes històriques» informatives (RN-M01-33). Si el tresorer necessita que constin com a ingressos, cal una regla a la 04. Propietari: tresorer.
4. **El mapa v8 posava el mandat SEPA al formulari d'alta.** Ara és del 05a ([044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)): el formulari no el demana. Els socis nous aprovats abans del 05a hauran de signar-lo després. Propietari: responsable del projecte.
5. **El mapa v8 parlava de notificacions push i del botó d'esborrar «per a les botigues».** Sense push ([041](decisions/041-web-installable-i-avisos-sense-push.md)); el botó es manté per RGPD. Propietari: cap (resolt).
6. **El pla anterior incloïa la data de naixement; la spec 00 (V-04) no.** Mana la spec 00 fins a P-33. Propietari: junta.
7. **Importació final «quan el 05a pugui rebre els mandats»:** a l'aprovació es deia «M05b» amb la numeració del mapa v8; amb la numeració de la sèrie B és el **05a**. Propietari: responsable del projecte (confirmar).
8. **La verificació pública amb només dos dígits** pot ser poc útil si un centre vol comprovar que el carnet és de qui el porta; el nom de pila ho resoldria però exposa més dades. Propietari: junta.
9. **Concurrència del comptador de números:** una fila bloquejada és simple però serialitza les aprovacions; amb el volum del club no és cap problema. Propietari: informàtica.
10. **La spec 00 diu «llista tancada dels 8 rols».** Afegir Junta, Resp. comunicació i Resp. botiga demana una decisió nova i actualitzar la spec 00. Propietari: junta (P-04).

<a id="M01-14-aprovar"></a>
## M01-14 Què cal aprovar abans de començar

1. **Aquest pla del M01** (responsable del projecte).
2. **Interfície amb plantilles de Django i HTMX** servida des del VPS: decisió nova 046, perquè la 002 parla d'API REST i de Cloudflare Pages (responsable del projecte).
3. **Spec del M01:** o aquest pla fa de `spec.md` (i CLAUDE.md, punt 1, s'hi refereix), o se n'extreu `specs/01-socis-i-carnet/spec.md` abans de programar (responsable del projecte).
4. **Matriu de rols** de [M01-4](#M01-4-rols), amb els 13 rols (junta, P-04).
5. Els supòsits marcats a [M01-13](#M01-13-riscos) que bloquegen tasques: S-M01-01 (canvi de tipus, només per a T-M01-17), S-M01-03 (període i venciment, per a T-M01-18), S-M01-16 (mostra de Cluber, per a T-M01-24).
6. Confirmar que la importació final depèn del **05a** (dubte 7).
