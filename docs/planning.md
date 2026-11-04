# Pla de la plataforma C.R.I.S., mòdul a mòdul

- **Què és:** l'únic fitxer del pla de tots els mòduls i la **font única de la seva especificació** ([047](decisions/047-planning-font-unica-de-l-especificacio.md)). S'hi afegeixen mòduls amb la mateixa estructura de 14 seccions. Cap altre fitxer en copia el contingut: s'hi enllaça per l'àncora.
- **Data de la versió:** 31/10/2026, amb els ajustos de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md) (la data només identifica la versió; el pla no té calendari, [038](decisions/038-planificar-sense-dates.md)).
- **Com s'aprova:** cada secció de mòdul passa d'«escrit» a «aprovat» quan el responsable del projecte l'aprova. Cap mòdul nou s'afegeix fins que l'anterior està aprovat, excepte quan el responsable del projecte en demana diversos alhora perquè depenen entre ells (04, 05a i 05b; 02 i 03; 09 i 06, que depenen tots dos del 05b).

<a id="estat"></a>
## 1. Estat i numeració dels mòduls

«Estat» és l'estat de la secció d'aquest pla, no del codi: **pendent** (no escrita), **escrit** (per aprovar), **aprovat**. Aprovats: 01, 04, 05a i 05b (27/10/2026); 02, 03, 06 i 09 amb l'apartat d'ajuts (28/10/2026). Ordre de construcció segons la [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md) i la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): fase 1, 00 → 01 → 04 → 05a → 05b; fase 2, 06 → 02 → 03 → 09 → 07 → 08 (el 06 entra en producció quan existeix el nucli de despeses del 09, T-M09-02 a T-M09-05); després, 10, 11 i 12. **El número identifica el mòdul, no l'ordre de construcció.**

| Núm. | Mòdul | Fase | Depèn de | Font de l'especificació | Estat al pla |
|---|---|---|---|---|---|
| **00** | Base comuna | 1 | — | [spec 00](../specs/00-base-comuna/spec.md) v2 (fins que el 00 tingui secció aquí) | pendent (el 01 en defineix la part que necessita) |
| **01** | [Socis i carnet digital](#M01) | 1 | 00 | Aquest pla ([047](decisions/047-planning-font-unica-de-l-especificacio.md)) | **aprovat** (addendes de la 049 i la 052) |
| **02** | [Activitats (cursos i sortides)](#M02) | 2 | 00, 01, 04, 05b, 06 (060) | Aquest pla | **aprovat** (28/10/2026) |
| **03** | [Material](#M03) | 2 | 00, 02 | Aquest pla | **aprovat** (28/10/2026) |
| **04** | [Tresoreria, part mínima](#M04) | 1 | 00, 01 | Aquest pla (la spec 04 v2 és a l'[arxiu](arxiu/spec-04-tresoreria-v2-2026-10-27.md)) | **aprovat** (addenda de la 050) |
| **05a** | [Alta del mètode de pagament i mandats](#M05a) | 1 | 01, 04 | Aquest pla | **aprovat** |
| **05b** | [Cobraments](#M05b) | 1 | 05a | Aquest pla | **aprovat** (ampliat per la 049) |
| **06** | [Llicències](#M06) | 2 | 01, 05b | Aquest pla | **aprovat** (28/10/2026) |
| **07** | Web pública | 2 | 01, 02 | — | pendent |
| **08** | Dashboard | 2 | 01, 02, 04, 09 | — | pendent |
| **09** | [Marge, despeses, ajuts i facturació](#M09) (abans «resta de la 04»; amb l'[apartat d'ajuts](#M09-ajuts)) | 2 | 02, 03, 04, 05b | Aquest pla | **aprovat** (28/10/2026) |
| **10** | Missatges i xat per activitat | després de la 2 | 01, 02 | — | pendent |
| **11** | Departament d'Història i conferències | després de la 2 | 01, 02, 07 | — | pendent |
| **12** | Idees noves (avatars de fauna marina i bitàcola; [idees registrades](#M12-idees)) | després de la 2 | 01, 02, 03 | — | pendent |
| **13** | Botiga en línia | — | — | Fora d'abast ara | — |

<a id="primer-modul"></a>
**Primer mòdul que es pot començar a construir: el 01 (Socis i carnet digital), amb les peces de la 00 que necessita**, a partir de T-M01-01 i T-M01-03 (esquelet del projecte). La 00 no té secció pròpia: el 01 en construeix la part que necessita, seguint la [spec 00](../specs/00-base-comuna/spec.md). Després, per dependències: 04 → 05a → 05b (fase 1) i 06 → 02 → 03 → 09 (fase 2, [060](decisions/060-ajustos-de-l-auditoria-del-pla.md)). Les peces de la 00 que el pla esmentava sense tasca tenen identificador propi (T-M00-01 a T-M00-04, [apèndix de la 060](#ajustos-060-peces-00); la T-M00-05, de la [063](decisions/063-validacions-de-la-revisio-de-la-t-m01-02.md), és al mateix apèndix); la T-RP-01 i la T-RP-04 es fan just després de la T-M01-06. Tots aquests mòduls estan aprovats i es poden construir en aquest ordre; entrar en producció depèn dels [A verificar] externs i de les decisions de la junta ([ordre del dia](#ordre-del-dia-junta)).

**Regles de la numeració** (fixada el 27/10/2026 pel responsable del projecte)
- Cap mòdul no canvia de número. Un mòdul nou s'afegeix al final (14, 15…).
- La web instal·lable ([041](decisions/041-web-installable-i-avisos-sense-push.md)) no és un mòdul: va amb la interfície des del 01.
- **Dependències sense cicles entre el 01, el 02, el 05b i el 06** (revisat el 27/10/2026, [052](decisions/052-llicencia-font-unica-al-06.md)). Una fletxa vol dir «crida serveis de»:
  - 02 → 01, 05b i 06 (quan existeixi); 06 → 01 i 05b; 05b → 01; el 01 no crida cap d'aquests tres.
  - El 05b avisa el 02 i el 06 amb l'esdeveniment `charge.paid`, i el 06 avisa el 01 amb els esdeveniments de llicència. Els esdeveniments passen pel mecanisme de la 00 ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)): qui emet no importa el codi de qui els rep, per tant no fan cicle.
  - Fora d'aquest grup, el 01 i la 04 ja es criden en tots dos sentits (`treasury.transfer_reference` i `members.on_fee_paid`), tal com es van aprovar; no s'ha tocat.
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
   - [Addenda de la 052: còpia de lectura de la llicència](#M01-addenda-052)
   - [Addenda de la 054: versió dels esdeveniments i comprovació diària](#M01-addenda-054)
   - [Addenda de la 055: pantalla d'ajustos](#M01-addenda-055)
   - [Addenda de la 058: data de naixement (00), caducitat desconeguda i conservació](#M01-addenda-058)
   - [Addenda de la 059: permisos editables i configuració inicial](#M01-addenda-059)
   - [Addenda de la 060: ajustos de l'auditoria](#M01-addenda-060)
   - [Addenda de la 063: contrasenya abans d'esborrar el compte](#M01-addenda-063)
   - [Addenda de la 064: baixa rebutjada i motius de la sol·licitud](#M01-addenda-064)
7. [Mòdul 04 — Tresoreria, part mínima](#M04) · [resum](#M04-resum)
   1. [Intenció](#M04-1-intencio) · 2. [Dependències](#M04-2-dependencies) · 3. [Capacitats](#M04-3-capacitats) · 4. [Rols](#M04-4-rols) · 5. [Processos](#M04-5-processos) · 6. [Entitats](#M04-6-entitats) · 7. [Regles](#M04-7-regles)
   8. [Serveis](#M04-8-serveis) · 9. [Criteris](#M04-9-criteris) · 10. [Tasques](#M04-10-tasques) · 11. [Proves](#M04-11-proves) · 12. [Seguretat](#M04-12-seguretat) · 13. [Riscos](#M04-13-riscos) · 14. [Aprovar](#M04-14-aprovar)
   - [Addenda de la 050: despeses, altres ingressos, anul·lació i període tancat](#M04-addenda-050)
   - [Addenda de la 053: moviments d'origen extern i període tancat](#M04-addenda-053)
   - [Addenda de la 059: permisos editables i configuració inicial](#M04-addenda-059)
   - [Addenda de la 060: ajustos de l'auditoria](#M04-addenda-060)
8. [Mòdul 05a — Alta del mètode de pagament i mandats](#M05a) · [resum](#M05a-resum)
   1. [Intenció](#M05a-1-intencio) · 2. [Dependències](#M05a-2-dependencies) · 3. [Capacitats](#M05a-3-capacitats) · 4. [Rols](#M05a-4-rols) · 5. [Processos](#M05a-5-processos) · 6. [Entitats](#M05a-6-entitats) · 7. [Regles](#M05a-7-regles)
   8. [Serveis](#M05a-8-serveis) · 9. [Criteris](#M05a-9-criteris) · 10. [Tasques](#M05a-10-tasques) · 11. [Proves](#M05a-11-proves) · 12. [Seguretat](#M05a-12-seguretat) · 13. [Riscos](#M05a-13-riscos) · 14. [Aprovar](#M05a-14-aprovar)
   - [Addenda de la 055: pantalla d'ajustos](#M05a-addenda-055)
   - [Addenda de la 058: targeta guardada recomanada i renovació de la quota](#M05a-addenda-058)
   - [Addenda de la 059: permisos editables i configuració inicial](#M05a-addenda-059)
   - [Addenda de la 060: ajustos de l'auditoria](#M05a-addenda-060)
9. [Mòdul 05b — Cobraments](#M05b) · [resum](#M05b-resum)
   1. [Intenció](#M05b-1-intencio) · 2. [Dependències](#M05b-2-dependencies) · 3. [Capacitats](#M05b-3-capacitats) · 4. [Rols](#M05b-4-rols) · 5. [Processos](#M05b-5-processos) · 6. [Entitats](#M05b-6-entitats) · 7. [Regles](#M05b-7-regles)
   8. [Serveis](#M05b-8-serveis) · 9. [Criteris](#M05b-9-criteris) · 10. [Tasques](#M05b-10-tasques) · 11. [Proves](#M05b-11-proves) · 12. [Seguretat](#M05b-12-seguretat) · 13. [Riscos](#M05b-13-riscos) · 14. [Aprovar](#M05b-14-aprovar)
   - [Addenda de la 055: pantalla d'ajustos](#M05b-addenda-055)
   - [Addenda de la 058: import extra del retorn i reintent de la targeta](#M05b-addenda-058)
   - [Addenda de la 059: permisos editables i configuració inicial](#M05b-addenda-059)
   - [Addenda de la 060: ajustos de l'auditoria](#M05b-addenda-060)
10. [Mòdul 02 — Activitats (cursos i sortides)](#M02) · [resum](#M02-resum) · **aprovat** (28/10/2026)
   1. [Intenció](#M02-1-intencio) · 2. [Dependències](#M02-2-dependencies) · 3. [Capacitats](#M02-3-capacitats) · 4. [Rols](#M02-4-rols) · 5. [Processos](#M02-5-processos) · 6. [Entitats](#M02-6-entitats) · 7. [Regles](#M02-7-regles)
   8. [Serveis](#M02-8-serveis) · 9. [Criteris](#M02-9-criteris) · 10. [Tasques](#M02-10-tasques) · 11. [Proves](#M02-11-proves) · 12. [Seguretat](#M02-12-seguretat) · 13. [Riscos](#M02-13-riscos) · 14. [Aprovar](#M02-14-aprovar)
   - [Addenda de la 058: instructors, nivells, especialitats, titulacions i edat mínima](#M02-addenda-058)
   - [Addenda de la 059: permisos editables i configuració inicial](#M02-addenda-059)
   - [Addenda de la 060: ajustos de l'auditoria](#M02-addenda-060)
11. [Mòdul 03 — Material](#M03) · [resum](#M03-resum) · **aprovat** (28/10/2026)
   1. [Intenció](#M03-1-intencio) · 2. [Dependències](#M03-2-dependencies) · 3. [Capacitats](#M03-3-capacitats) · 4. [Rols](#M03-4-rols) · 5. [Processos](#M03-5-processos) · 6. [Entitats](#M03-6-entitats) · 7. [Regles](#M03-7-regles)
   8. [Serveis](#M03-8-serveis) · 9. [Criteris](#M03-9-criteris) · 10. [Tasques](#M03-10-tasques) · 11. [Proves](#M03-11-proves) · 12. [Seguretat](#M03-12-seguretat) · 13. [Riscos](#M03-13-riscos) · 14. [Aprovar](#M03-14-aprovar)
   - [Addenda de la 059: permisos editables i configuració inicial](#M03-addenda-059)
   - [Addenda de la 060: ajustos de l'auditoria](#M03-addenda-060)
12. [Mòdul 09 — Marge, despeses, ajuts i facturació](#M09) · [resum](#M09-resum) · **aprovat** (28/10/2026)
   1. [Intenció](#M09-1-intencio) · 2. [Dependències](#M09-2-dependencies) · 3. [Capacitats](#M09-3-capacitats) · 4. [Rols](#M09-4-rols) · 5. [Processos](#M09-5-processos) · 6. [Entitats](#M09-6-entitats) · 7. [Regles](#M09-7-regles)
   8. [Serveis](#M09-8-serveis) · 9. [Criteris](#M09-9-criteris) · 10. [Tasques](#M09-10-tasques) · 11. [Proves](#M09-11-proves) · 12. [Seguretat](#M09-12-seguretat) · 13. [Riscos](#M09-13-riscos) · 14. [Aprovar](#M09-14-aprovar)
   - [Apartat: Ajuts: calendari, sol·licituds i justificació](#M09-ajuts) · [resum](#M09-ajuts-resum) · **aprovat** (28/10/2026): 1. [Intenció](#M09-ajuts-1-intencio) · 2. [Dependències](#M09-ajuts-2-dependencies) · 3. [Capacitats](#M09-ajuts-3-capacitats) · 4. [Rols](#M09-ajuts-4-rols) · 5. [Processos](#M09-ajuts-5-processos) · 6. [Entitats](#M09-ajuts-6-entitats) · 7. [Regles](#M09-ajuts-7-regles) · 8. [Serveis](#M09-ajuts-8-serveis) · 9. [Criteris](#M09-ajuts-9-criteris) · 10. [Tasques](#M09-ajuts-10-tasques) · 11. [Proves](#M09-ajuts-11-proves) · 12. [Seguretat](#M09-ajuts-12-seguretat) · 13. [Riscos](#M09-ajuts-13-riscos) · 14. [Aprovar](#M09-ajuts-14-aprovar)
   - [Addenda de la 058: IVA per tipus de càrrec, donatius, termini d'esmena i conservació](#M09-addenda-058)
   - [Addenda de la 059: permisos editables i configuració inicial](#M09-addenda-059)
   - [Addenda de la 060: ajustos de l'auditoria](#M09-addenda-060)
13. [Mòdul 06 — Llicències](#M06) · [resum](#M06-resum) · **aprovat** (28/10/2026)
   1. [Intenció](#M06-1-intencio) · 2. [Dependències](#M06-2-dependencies) · 3. [Capacitats](#M06-3-capacitats) · 4. [Rols](#M06-4-rols) · 5. [Processos](#M06-5-processos) · 6. [Entitats](#M06-6-entitats) · 7. [Regles](#M06-7-regles)
   8. [Serveis](#M06-8-serveis) · 9. [Criteris](#M06-9-criteris) · 10. [Tasques](#M06-10-tasques) · 11. [Proves](#M06-11-proves) · 12. [Seguretat](#M06-12-seguretat) · 13. [Riscos](#M06-13-riscos) · 14. [Aprovar](#M06-14-aprovar)
   - [Addenda de la 058: tipus, durades, llicència d'un dia, recàrrec, renovació, format del carnet i caducitat desconeguda](#M06-addenda-058)
   - [Addenda de la 059: permisos editables i configuració inicial](#M06-addenda-059)
   - [Addenda de la 060: ajustos de l'auditoria](#M06-addenda-060)
14. [Mòdul 12 — Idees noves (idees registrades)](#M12-idees), amb l'assistent d'ajuts
15. [Apèndix — Preguntes per propietari](#preguntes): [banc](#preguntes-banc) · [PaynoPain](#preguntes-paynopain) · [tresorer](#preguntes-tresorer) · [junta](#preguntes-junta) · [gestoria](#preguntes-gestoria) · [FECDAS](#preguntes-fecdas) · [secretaria](#preguntes-secretaria) · [informàtica](#preguntes-informatica) · [responsable del projecte](#preguntes-responsable) · [responsable de cursos i sortides](#preguntes-cursos-sortides)
16. [Apèndix — Ordre del dia per a la junta](#ordre-del-dia-junta): [decisions de debò](#ordre-del-dia-decisions) · [valors inicials](#ordre-del-dia-valors)
17. [Apèndix — Valors configurables](#valors-configurables) · [peça comuna d'ajustos (055)](#valors-configurables-055)
18. [Apèndix — Rols i permisos editables (059)](#rols-i-permisos-059) · [configuració inicial de la matriu](#rols-i-permisos-059-matriu)
19. [Apèndix — Ajustos de l'auditoria (060)](#ajustos-060) · [peces de la 00](#ajustos-060-peces-00) · [rols i permisos](#ajustos-060-rols) · [lectura de les tasques substituïdes](#ajustos-060-lectura)

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
- **Els permisos de cada rol són dades** que només l'administrador canvia des de l'app, amb TOTP, nota, resum dels afectats i registre; també assigna i retira rols als comptes d'administrador. Les regles de seguretat i d'integritat (IBAN, documents de justificació, data de naixement, dades bloquejades, gestionar usuaris i rols…) queden al codi i no s'editen ([059](decisions/059-rols-i-permisos-editables.md), [apèndix](#rols-i-permisos-059)).
- Registre d'activitat immutable (qui, quan, què, valor anterior).

**Valors de negoci (configurables)** (28/10/2026)
- **Els valors de negoci són dades editables des de l'app, no codi ni configuració tècnica.** Un preu, el nom d'un curs o d'un departament, un llindar, els dies d'un avís, un text d'ajuda i els supòsits que són només un valor es canvien des de la pantalla d'**«Ajustos»** del mòdul, per l'administrador o pel responsable del departament que correspongui.
- Cada valor editable té: **valor inicial**, **rang vàlid**, **rol que el canvia**, **registre de canvis** (qui, quan, valor anterior) i, si afecta diners, **data d'entrada en vigor** (el canvi no toca el que ja s'ha demanat o cobrat).
- **Queden al codi** i no s'editen des de l'app: les regles i la seguretat (per exemple, preu de soci igual al de la federació, període tancat que no es toca, documents amb IBAN només per al tresorer i la junta, quantes xifres es mostren en una verificació pública) i els formats que garanteixen la integritat (numeracions, referències). **Els secrets** viuen en variables d'entorn.
- La llista de valors, on viu cadascun i què canvia és a l'[apèndix de valors configurables](#valors-configurables). En els mòduls aprovats (01, 04, 05a i 05b) aquesta regla no edita cap regla aprovada: s'hi aplica amb la decisió [055](decisions/055-ajustos-configurables-i-addendes.md), amb una addenda a cada mòdul. La peça comuna d'ajustos (00) és a l'[apèndix](#valors-configurables-055). Tot canvi d'un valor que afecta diners avisa per correu el tresorer i la junta (RN-AJ-04).

**Documentació**
- Aquest fitxer és la font única de l'especificació de cada mòdul ([047](decisions/047-planning-font-unica-de-l-especificacio.md)). Cap altre fitxer en copia regles, criteris ni tasques.
- No s'edita cap decisió existent: se'n crea una de nova que la substitueix o l'amplia.
- No s'inventa res: el que falta porta [A verificar] (dada externa) o [A validar] (decisió del club), sempre amb propietari. Propietaris possibles: tresorer, junta, banc, PaynoPain, gestoria, FECDAS, secretaria, informàtica, responsable del projecte, responsable de cursos i sortides.

**Pila i interfície**
- Django i PostgreSQL ([002](decisions/002-pila-tecnologica.md)); cua de tasques sobre PostgreSQL ([012](decisions/012-cua-de-tasques.md)).
- **Interfície:** plantilles de Django i **HTMX** servides des del VPS; l'arxiu d'HTMX es serveix des del servidor propi, **sense CDN** ([046](decisions/046-interficie-django-htmx-servida-des-del-vps.md), que substitueix la part de frontend de la 002).
- Web instal·lable, sense botigues i sense notificacions push ([041](decisions/041-web-installable-i-avisos-sense-push.md)).
- Interfície i documents en català; codi en anglès (V-09 de la spec 00).
- <a id="idiomes"></a>**Idiomes ([061](decisions/061-plataforma-preparada-per-traduir.md)):** el català és l'única llengua activa i la de reserva; la plataforma queda preparada per traduir-se sense activar-ne cap més (quines i qui les tradueix: [P-49](decisions/pendents.md)).
  - Tota cadena que veu l'usuari es marca com a traduïble, amb el text català com a original: `gettext_lazy` a nivell de mòdul o de classe, `gettext` dins de les funcions, `{% translate %}` i `{% blocktranslate %}` a les plantilles. Sense f-strings ni `.format()` dins de `_()` (regla `INT` de ruff); amb un comptador, `ngettext` o `{% blocktranslate count %}`. No es marquen els noms de codi ni les dades que escriuen els usuaris.
  - La persona té una llengua preferida (`Person.preferred_language`, per defecte `"ca"`); `persons.language_for(person)` la retorna si és activa i, si no, el català. Els correus es generen en aquesta llengua i, si no hi ha la plantilla, en català.
  - Els textos legals tenen llengua; una traducció és una fila més de la mateixa versió, no una versió nova. El consentiment apunta a la fila exacta (versió i llengua). El servei de traduccions queda per a la primera traducció real.
  - El nom d'un rol a la interfície surt de `get_code_display()`; `Role.name` és una dada interna.
- Sistema de disseny de les decisions [030](decisions/030-sistema-de-disseny.md) a [034](decisions/034-patrons-magic-portfolio.md): tokens, dos temes, estats amb símbol, text i color, objectiu WCAG 2.2 AA (checklist B8).

**Metodologia aplicada**
Les skills que es van demanar (spec-driven-development, product-capability, intent-driven-development, planning-and-task-breakdown, blueprint, contract-first, security-and-hardening, django-patterns, django-security, postgres-patterns, documentation-and-adrs, doubt-driven-development i accessibility) **no estan instal·lades**. La plantilla de la secció 5 n'aplica l'estructura a mà: intenció i capacitats (1, 3), contracte primer (8), blueprint de dades (6), tasques per dependències (10), seguretat (12) i revisió de dubtes (13). El mateix val per als mòduls 04, 05a, 05b, 02, 03, 09 (i el seu apartat d'ajuts) i 06.

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
| Despesa | Sortida de diners amb factura, categoria i departament; es pot repartir entre activitats. Quan es paga, és un moviment de la 04 | F §7; [M09-6](#M09-6-entitats) |
| Marge previst / marge real | Marge d'una activitat mentre és oberta (amb costos previstos) / calculat en tancar-la i congelat | F §7; RN-M09-06 i 07 |
| Tancament econòmic | Pas del 09 que congela el marge d'una activitat i la deixa `closed` | RN-M09-12 |
| Període tancat | Període (mensual, [A validar]) que no admet canvis del 09. El que arriba tard entra al període obert («ajust posterior», «moviment tardà»). Només l'administrador el reobre, amb motiu i avís per correu al tresorer i a la junta, i només per corregir errors de la feina del propi període | RN-M09-07, 15, 16 i 24 |
| Factura / rectificativa | Document fet per un servei homologat per Verifactu quan la facturació està activada / la que anul·la o redueix una factura per una devolució. No és el rebut | F §7; RN-M09-17 a 19 |
| Convocatòria d'ajut | Crida d'un organisme per demanar un ajut. No s'ha de confondre amb la convocatòria d'un curs | [M09-ajuts-6](#M09-ajuts-6-entitats) |
| Sol·licitud d'ajut | Petició del club a una convocatòria d'ajut, amb estat, responsable i import | RN-M09A-01 |
| Paquet de justificació | Resum, llistat de factures i ZIP amb factures i comprovants de les despeses lligades a un ajut | F 9.10; RN-M09A-11 |
| Llicència federativa | Llicència de la federació per a un soci o una persona de fora. Cada tipus té una categoria (aficionat, tècnic o altres) i una regla de validesa: any natural (fins al 31/12), 365 dies o, només si s'activa l'opció, un dia | F §8.1; [M06](#M06); RN-M06-01 |
| Recàrrec de no soci | Diferència entre el preu de la llicència per a un no soci i el preu de la federació (el del soci) | RN-M06-06 |
| Rol de gestió | Conjunt de permisos que s'assigna a un compte d'administrador: instructor, secretaria, responsable de cursos i sortides, responsable de material, tresorer, Departament d'Història, administrador, President, junta, responsable de comunicació i responsable de botiga. Un compte en pot tenir diversos (unió) | [059](decisions/059-rols-i-permisos-editables.md) |
| President | Rol de gestió nou (30/10/2026). Pot fer només el que li dona la matriu inicial; no gestiona usuaris, rols ni permisos | [059](decisions/059-rols-i-permisos-editables.md) |
| Permís | Acció concreta d'un mòdul (per exemple, registrar una despesa). Autoritzar-ne una no n'autoritza cap altra | [Apèndix](#rols-i-permisos-059) |
| Abast | Sobre quins objectes s'aplica un permís (tots, les seves activitats, les seves sessions, propi), d'una llista tancada que fixa el codi | RN-RP-04 |
| Camp sensible | Camp que només veu qui en té el permís de lectura (data de naixement, document, número federatiu, marge…) | [Apèndix](#rols-i-permisos-059) |
| Regla protegida | Regla de seguretat o d'integritat que l'editor mostra però no deixa canviar | RN-RP-05 |
| Configuració inicial de la matriu | Permisos amb què arrenca la plataforma; l'administrador els pot canviar des de l'editor, amb versions | [Matriu](#rols-i-permisos-059-matriu) |
| Administrador operatiu | Compte actiu amb el rol administrador, TOTP donat d'alta, no bloquejat i que no és d'emergència. N'hi ha d'haver sempre almenys un | RN-RP-13 |

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

**Estat: aprovat** pel responsable del projecte el 27/10/2026, amb les respostes recollides a [M01-14](#M01-14-aprovar). Ampliat per la [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md) amb un servei de lectura de la llicència (T-M01-30) i per la [052](decisions/052-llicencia-font-unica-al-06.md) amb una [addenda](#M01-addenda-052) (T-M01-31), completada per la [054](decisions/054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md) ([addenda](#M01-addenda-054)), i per la [055](decisions/055-ajustos-configurables-i-addendes.md) amb una [addenda](#M01-addenda-055) de pantalla d'ajustos (T-M01-32), sense canviar cap regla. Ampliat també per la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) amb una [addenda](#M01-addenda-058) (data de naixement de la 00, caducitat desconeguda i conservació; T-M01-33 i T-M01-34), amb la precisió del 29/10/2026 (data de naixement obligatòria per als socis i socis existents; T-M01-35 i T-M01-36), sense canviar cap regla. Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M01-addenda-059)).

**Fonts integrades:** el pla M01 del repositori anterior (aprovat amb respostes el 27/10/2026), la [spec 00](../specs/00-base-comuna/spec.md) v2, el document de funcionalitats (F §3 i processos 9.2 a 9.5 i 9.13), el mapa de la plataforma v8 i les decisions 035–047. Per la [047](decisions/047-planning-font-unica-de-l-especificacio.md), aquesta secció **és** l'especificació del M01: no hi ha cap `specs/01-…`.

<a id="M01-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Tenir els socis, les quotes anuals i el carnet digital a la plataforma, perquè la secretaria deixi Excel i correu, cada soci vegi les seves dades i el seu carnet, i Cluber es pugui deixar. Cap altre mòdul no funciona sense aquest. |
| **Processos que cobreix** | P-M01-A Alta de soci · P-M01-B Canvi de tipus · P-M01-C Baixa i readmissió · P-M01-D Renovació anual de quotes · P-M01-E Carnet i verificació pública · P-M01-F RGPD: exportar i esborrar · P-M01-G Importació de Cluber en dues fases (F 9.2 a 9.5 i 9.13) |
| **Tasques** | 37 (T-M01-01 a T-M01-37), incloses les peces de la 00 que el 01 necessita; la T-M01-30 l'afegeix la 049, la T-M01-31, la 052 (amb la 054) i la T-M01-32, la 055, de la T-M01-33 a la T-M01-36, la 058 (amb la precisió del 29/10/2026), i la T-M01-37, la 059. La T-M01-07b (consulta del registre) s'afegeix el 02/11/2026. La peça comuna de rols i permisos (T-RP-01 a T-RP-04; la T-RP-05, retirada per la 060) és a l'[apèndix](#rols-i-permisos-059). La peça comuna d'ajustos (T-AJ-01 i T-AJ-02) és a l'[apèndix](#valors-configurables-055). Les peces de la 00 que no tenien tasca (T-M00-01 a T-M00-04) són a l'[apèndix de la 060](#ajustos-060-peces-00) |
| **Què el bloqueja** | Res per començar. La importació final espera el 05a (nivell 1) i la mostra anonimitzada de Cluber [A validar: tresorer, S-M01-16] |
| **Què cal aprovar** | Aprovat el 27/10/2026 ([M01-14](#M01-14-aprovar)). La matriu de rols (P-04) queda resolta per la [059](decisions/059-rols-i-permisos-editables.md) (30/10/2026). Continuen oberts sense bloquejar els supòsits de [M01-13](#M01-13-riscos) ([apèndix](#preguntes)) |

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
| 06 | Registre mínim de llicència (`members.licence_records`, [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) |
| 02 | Saber si una persona és sòcia (preu de soci) i si la llicència és vigent (`members.licence_record`, 049) |
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

**Wireframes** (`design/wireframes/`; inventari actualitzat per la T-M01-02, 03/11/2026). Les pantalles noves s'obren amb l'adreça (per exemple, `admin.html#vista-socis-llistat&rol=tresorer`); com provar-les és a [`design-system.md`](design-system.md) §13.
- **Existents, conservades sense canvis:**
  - `publica.html`: secció i botons «Fer-se soci» (`#fer-se-soci`; ara porten al formulari).
  - `socis.html`: portada del compte personal, **carnet giratori** (`#carnet`), franja d'estat (`#franja-estat`), avisos, pagaments amb justificant (`#historial-pagaments`, que fa de «Les meves quotes»), llicència (`#llicencia`) i la invitació per a qui no és soci.
  - `admin.html`: barra lateral filtrada per rol (`data-rols`) i el patró de fitxa amb taula, cerca i filtres.
- **Esbós completat:** `admin.html#vista-socis-sollicituds` (abans «Altes pendents»), ara amb altes, canvis de tipus i baixes, i els permisos de la [059](#M01-addenda-059).
- **Noves (T-M01-02):** formulari «Fer-se soci» (`publica.html#alta`) i verificació del carnet (`publica.html#verificar`); alta presencial (`#vista-socis-alta`), llistat (`#vista-socis-llistat`), fitxa (`#vista-socis-fitxa`), quotes i impagats (`#vista-socis-quotes`) i importació de Cluber (`#vista-socis-cluber`) a `admin.html`; perfil (`socis.html#perfil`), canvi a ple dret (`#canvi-tipus`), baixa (`#baixa`), esborrar el compte (`#esborrar`) i «no trobat» (`#no-trobat`).
- **Encara sense wireframe (fora de la T-M01-02):** l'aprovació de l'esborrat per l'administració (`/gestio/rgpd`, peça de la 00, M11) i la marca «Comprovat per última vegada» del carnet sense connexió (T-M01-21).

### P-M01-A Alta de soci (F §9.2)
| Pas | Qui | Què passa | Pantalla (ruta del mapa v8) | Wireframe |
|---|---|---|---|---|
| 1 | Visitant | Obre «Fer-se soci» des de la web pública | `/fer-se-soci` | `publica.html#fer-se-soci` (botó) i `publica.html#alta` (formulari) |
| 2 | Visitant | Omple dades mínimes (V-04: nom, cognoms, document, correu, telèfon; adreça opcional), tria el tipus i accepta els textos legals obligatoris. **Sense mandat SEPA** (és del 05a) | `/fer-se-soci` | `publica.html#alta` |
| 3 | Sistema | Comprova duplicats (RN-M01-03). Desa la sol·licitud «pendent de revisió» i els consentiments. Envia un correu de rebut de la sol·licitud | — | — |
| 3b | Secretaria | (Alta presencial) Omple el mateix formulari des de l'administració; el consentiment es registra com a presencial (canal i compte) | `/gestio/socis/altes/nova` | `admin.html#vista-socis-alta` |
| 4 | Secretaria | Revisa la sol·licitud a «Altes pendents»; veu l'avís de possible duplicat | `/gestio/socis/altes` | `admin.html#vista-socis-sollicituds` |
| 5a | Secretaria | **Aprova:** es crea el soci (estat **pendent**), s'assigna el número (RN-M01-05), es crea la quota del període (RN-M01-12) i s'envia una invitació per activar el compte personal | `/gestio/socis/altes` | `admin.html#vista-socis-sollicituds` |
| 5b | Secretaria | **Rebutja** amb motiu: no es crea cap soci ni es consumeix cap número; s'avisa la persona | `/gestio/socis/altes` | `admin.html#vista-socis-sollicituds` |
| 6 | Soci | Activa el compte personal (verificació de correu) i veu la quota pendent i el botó «Paga ara» (el pagament és del 05b) | `/socis` | `socis.html#franja-estat` |
| 7 | Sistema | Quan la quota passa a «pagat» (05b o conciliació de la 04), el soci passa a **actiu** i es genera el carnet | — | — |
| 8 | Soci | Veu el carnet | `/socis/carnet` | `socis.html#carnet` |

### P-M01-B Canvi de tipus (F §9.3)
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Soci (simpatitzant actiu) | Obre «Sol·licitar canvi a ple dret»; veu l'import calculat (RN-M01-15) i confirma | `/socis/canvi-tipus` | `socis.html#canvi-tipus` (amb l'import «pendent de determinar per la secretaria»; vegeu la nota) |
| 2 | Sistema | Crea la sol·licitud i un càrrec de quota pel suplement (si l'import és > 0) | — | — |
| 3 | Secretaria | Aprova la sol·licitud. El canvi de tipus és **efectiu quan el suplement està pagat** [A validar: junta] | `/gestio/socis/{id}` | `admin.html#vista-socis-sollicituds` (pestanya «Canvis de tipus») |
| 4 | Sistema | Canvia el tipus amb data efectiva, ho desa a l'historial, **revoca el carnet anterior i n'emet un de nou** | — | — |
Canvi de ple dret a simpatitzant: no consta enlloc [A validar: junta]. Proposta: només s'aplica a la quota del període següent.

**Nota de la T-M01-02 (wireframes, 03/11/2026).** HU-M01-09 i el pas 1 demanen que el soci vegi l'import abans de confirmar, però RN-M01-15 (aprovada) diu que la secretaria l'escriu en aprovar el canvi. El wireframe segueix RN-M01-15 (estat «Import pendent de determinar per la secretaria» i camp per escriure'l a la resolució) i **no resol la contradicció** [A validar: junta]. A més, la configuració inicial de la [059](#M01-addenda-059) dona P7 al President sense P4 (fitxa): per això el wireframe resol els canvis de tipus i les baixes des de la vista de sol·licituds, i no només des de `/gestio/socis/{id}` [A validar: ruta definitiva, T-M01-17].

### P-M01-C Baixa (F §9.4)
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Soci o junta | El soci la demana amb motiu i confirmació; o la secretaria la crea per decisió de la junta | `/socis/baixa`; `/gestio/socis/{id}` | `socis.html#baixa`; `admin.html#vista-socis-fitxa` («Crea una baixa») |
| 2 | Secretaria | La valida i fixa la data efectiva, o la rebutja amb motiu obligatori (`MemberRequest` passa a `rejected`) | `/gestio/socis/{id}` | `admin.html#vista-socis-sollicituds` (pestanya «Baixes») |
| 3 | Sistema | A la data efectiva: estat **baixa**, carnet revocat, correu de confirmació. Quotes pendents: vegeu RN-M01-20 | — | — |
| 4 | Sistema | El compte personal es manté per consultar rebuts (Q-31, proposta) [A validar: junta] | — | — |
**Rebutjar una baixa (03/11/2026, [064](decisions/064-una-baixa-es-pot-rebutjar-amb-motiu.md)).** El responsable del projecte ha comunicat que la junta ha validat que una baixa es pot rebutjar, amb motiu. Continuen pendents, i no s'han d'implementar fins que es decideixin ([P-50](decisions/pendents.md)): qui la pot rebutjar i per quins motius; què passa si hi ha quotes impagades; qui pot perdonar o anul·lar una quota anterior i amb quin permís; i què es diu al soci abans d'enviar la sol·licitud. El motiu de la baixa i el de rebuig es guarden en camps separats ([addenda de la 064](#M01-addenda-064)).

El número queda reservat per sempre ([039](decisions/039-numeros-de-soci-no-es-reutilitzen.md)). Si la persona torna, es **readmet** amb el mateix número (P-M01-A des del pas 4).

### P-M01-D Renovació anual de quotes (F §9.5)
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Tresorer | Tria el període i veu una **previsualització**: quants socis actius, quantes quotes de cada tipus i l'import total | `/gestio/quotes` | `admin.html#vista-socis-quotes` |
| 2 | Tresorer | Confirma: es crea una quota per soci actiu o impagat (RN-M01-12), departament «General / Quotes de socis» | `/gestio/quotes` | `admin.html#vista-socis-quotes` |
| 3 | Sistema | Envia l'avís de quota nova al soci (correu i safata d'avisos de l'app) | — | `socis.html#avisos` |
| 4 | Sistema | Recordatoris abans i després del venciment (RN-M01-14) | — | — |
| 5 | Tresorer | Revisa les quotes pendents i **marca impagat** a mà amb motiu ([040](decisions/040-impagat-es-marca-a-ma.md)) | `/gestio/quotes` | `admin.html#vista-socis-quotes` |
| 6 | Sistema | Quan una quota es paga (05b o 04), avisa el tresorer perquè desmarqui l'impagat | — | — |
La remesa de domiciliacions és del 05b; el M01 només crea les quotes.

### P-M01-E Carnet i verificació pública
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Sistema | En passar a actiu (o en un canvi de tipus), genera un carnet amb un testimoni aleatori nou; el QR porta l'URL de verificació amb el testimoni | — | — |
| 2 | Soci | Veu el carnet (davant: nom, número, tipus, vàlid fins a, anys de soci, QR; darrere: [A validar, decisió 032]) i el descarrega en PDF. La web instal·lable el guarda per veure'l sense cobertura | `/socis/carnet` | `socis.html#carnet` |
| 3 | Qualsevol persona | Escaneja el QR i obre la pàgina de verificació | `/carnet/verificar/{testimoni}` | `publica.html#verificar` |
| 4 | Sistema | Mostra **«Vàlid»** o **«No vàlid»** i el número de soci parcial (RN-M01-26). Res més. Si el nom de pila s'hi ha de mostrar és [A validar: junta] | — | — |
Sense cobertura, el carnet desat es mostra amb la marca «Comprovat per última vegada: [data]», perquè qui el mira sàpiga que pot no estar al dia.

### P-M01-F RGPD: exportar i esborrar
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Soci | Demana «Descarregar les meves dades» | `/socis/perfil` | `socis.html#perfil` |
| 2 | Sistema | Prepara un fitxer JSON amb persona, soci, historial, quotes, carnets (sense testimonis), sol·licituds, consentiments i llicència; URL signada, disponible 7 dies (V-08) | — | — |
| 3 | Soci | Demana «Esborrar el meu compte»: marca la confirmació i torna a escriure la contrasenya (i el codi TOTP si el compte en té). Sense això no s'envia la sol·licitud ([RN-M01-57](#M01-addenda-063)) | `/socis/perfil/esborrar` | `socis.html#esborrar` |
| 4 | Responsable RGPD | Aprova la sol·licitud (Q-15) [A validar: junta] | `/gestio/rgpd` | Falta (fora de la T-M01-02: peça de la 00; l'atén l'administrador, M11 de la [059](#rols-i-permisos-059-matriu)) |
| 5 | Sistema | Fa la baixa si és soci actiu, desactiva els comptes, anonimitza les dades personals, **bloqueja** quotes i rebuts fins al termini legal (Q-14), i substitueix la identitat al registre per una referència anònima ([028](decisions/028-esborrat-rgpd-i-registre-d-activitat.md)). El número de soci queda reservat i lligat a la referència anònima | — | — |

### P-M01-G Importació de Cluber, en dues fases (F §9.13; HU-20)
**Fase 1, prova (en aquest mòdul).**
| Pas | Qui | Què passa | Pantalla | Wireframe |
|---|---|---|---|---|
| 1 | Administrador | Puja l'exportació de Cluber (fitxer inventat o anonimitzat fora de producció) | `/gestio/importacions/cluber` | `admin.html#vista-socis-cluber` |
| 2 | Sistema | Rebutja el fitxer sencer si té una columna d'IBAN (RN-94). Valida cada línia i fa coincidir per document o número de soci (RN-95) | — | — |
| 3 | Administrador | Veu el resum: nous, coincidents, errors per línia, i el que es crearia (socis, tipus, estats, dates d'alta, quotes històriques, llicències). **No s'escriu res** | `/gestio/importacions/cluber` | `admin.html#vista-socis-cluber` |
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

El camp `reason` el substitueixen `request_reason` i `resolution_reason` ([addenda de la 064](#M01-addenda-064)).

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
| RN-M01-07 | Estats: pendent (aprovat, sense la quota pagada) → actiu (quota pagada) → impagat (marcat a mà) → actiu (desmarcat); pendent, actiu o impagat → baixa. Cap altra transició. **Precisió d'abast (04/11/2026, [P-55](decisions/pendents.md)):** readmissió: baixa → pendent, només en aprovar una sol·licitud d'alta d'una persona que ja va ser sòcia (P-M01-C), amb el mateix registre i el mateix número ([039](decisions/039-numeros-de-soci-no-es-reutilitzen.md)) i una entrada d'historial. Cap altra transició | F §3; 040; P-55 (aprovat pel responsable del projecte el 04/11/2026) |
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
| `members.licence_record(person)` | persona | tipus, data d'alta i data de caducitat del registre mínim de llicència, o res. **Només lectura** ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) | — | 02 |
| `members.licence_records()` | — | el mateix per a tots els socis. **Només lectura** (049) | — | 06 |
| `members.export_personal_data(person)` | persona | diccionari per a l'exportació RGPD | — | 00 (RGPD) |
| `members.anonymise(person)` | persona | anonimitza el que és del M01 i bloqueja quotes | — | 00 (RGPD) |

**Consumeix (de la 00 i d'altres mòduls)**
| Servei | Mòdul | Per a què |
|---|---|---|
| `persons.find_duplicates(data)`, `persons.create_or_get(data)` | 00 | Alta i importació |
| `accounts.invite_personal_account(person)` | 00 | Activar el compte personal en aprovar l'alta |
| `permissions.require(account, action, obj)` | 00 | Cada vista |
| `audit.record(actor, action, obj, field, old, new, reason)` | 00 | Tot canvi |
| `consents.grant(person, kind, channel, by)` i `consents.withdraw(...)` (T-M01-08; abans `consents.record`) | 00 | Alta i perfil |
| `charges.create_charge(person, kind="fee", amount_cents, department, concept, origin)` i `charges.cancel(charge, reason)` | 00 | Quotes i suplements |
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
| T-M01-02 | Wireframes que falten (formulari d'alta, altes pendents, llistat, fitxa, quotes, verificació, migració, perfil, sol·licituds, esborrar) amb el sistema de disseny | M | `design/wireframes/socis.html`, `admin.html`, `publica.html` | — | Revisats; contrast comprovat. **Feta** (03/11/2026; revisió del responsable del projecte aprovada el 03/11/2026): onze pantalles noves i l'esbós d'«Altes pendents» completat, amb els permisos inicials de la 059 ([inventari a M01-5](#M01-5-processos)); contrast comprovat amb els valors de `tokens.css` als dos temes; teclat i focus provats amb tecles reals a Chrome sense finestra; CI verd a la PR #4 (dues execucions: proves, captures i secrets), també després de la revisió (47d9b84); CI de referència verd a aca95cc (sis feines). **No tanca** el que continua pendent: la paleta revisada el 31/10, les dues excepcions de contrast i el focus del selector de data natiu ([design-system](design-system.md), pendents de la 1.5; T-M01-28); la contradicció de l'import del canvi de tipus i la ruta definitiva de resolució del President ([nota de P-M01-B](#M01-5-processos); T-M01-17); i què passa amb la sessió oberta quan el compte queda bloquejat (nota de `socis.html#esborrar`; RN-M01-57, T-M00-05) [A validar: informàtica] |
| T-M01-03 | Esquelet del projecte Django des de `main`, amb l'estructura d'apps de la PR #1 anterior; configuració per entorns; CI amb proves, lint i escaneig de secrets | M | `pyproject.toml`, `config/settings/`, `.github/workflows/` | T-M01-01 | **Feta** (01/11/2026): apps `core`, `accounts` i `members` segons aquest pla (sense la PR #1); Python 3.12 i Django 5.2 LTS |
| T-M01-04 | **Model d'usuari propi** abans de la primera migració, i model `Person` (00) | M | `apps/core/models.py`, `migrations/0001_*` | T-M01-03 | **Feta** (01/11/2026): `Person` a `apps/core`; el model d'usuari és `Account` a `apps/accounts` (un compte = una fila, personal o d'administrador, lligada a la persona); RN-13 estricte mentre Q-02 sigui oberta |
| T-M01-05 | Comptes personal i d'administrador, entrada separada, TOTP obligatori a l'administració, bloqueig per intents (V-01) | L | `apps/accounts/` | T-M01-04 | Proves de C2, C3, C4, C5 de la checklist. **Feta en part** (01/11/2026): entrades separades, TOTP obligatori a l'administració (secret xifrat, QR, sense reutilitzar codis), codis de recuperació, bloqueig per compte i per origen, caducitat de les sessions i sortida. **Queda:** verificació i recuperació per correu del compte personal (C4, C5; depèn de la T-M01-10), restabliment per un altre administrador (HU-08; depèn de la T-M01-06), alta i baixa del TOTP del compte personal (HU-05; baixa amb registre, T-M01-07) i prova de càrrega de C3. **Segona tanda, encara en part** (03/11/2026, CI [A comprovar]): verificació del correu (C5, CA-04.2); contrasenya nova amb l'enllaç de recuperació (CA-04.4), amb testimonis separats per finalitat, d'un sol ús i provats amb peticions simultànies; alta i baixa del TOTP personal (CA-05.1, CA-05.2), sense codis de recuperació; preparació de l'HU-08 (servei amb M4, credencial temporal de 24 hores amb canvi obligatori en entrar, avís de CA-08.4 i llista de comptes amb M4); prova de càrrega de C3, que va trobar més intents dels de V-01 amb peticions simultànies (corregit). **Queda:** la pantalla per demanar l'enllaç de recuperació i el reenviament de la verificació (CA-04.3; límits per origen i per destinatari i regla dels comptes pendents, per aprovar), la part de C3 d'aquests dos formularis, l'acció de restabliment de l'HU-08 (revalidació del TOTP de qui la fa, per aprovar; canal de Q-03 obert) i el procediment quan un soci perd el mòbil ([P-52](decisions/pendents.md), abans de producció). CI de la segona tanda: verd a la PR #4 (sis feines, dues execucions), segons el responsable del projecte. **Tercera tanda, implementada** (03/11/2026, amb la [065](decisions/065-enllacos-del-correu-i-restabliment-per-un-altre-administrador.md)): «He oblidat la contrasenya» i reenviament de la verificació amb els límits de RN-M01-58 (`apps/accounts/limits.py`), comptes pendents de RN-M01-59, acció de restabliment de l'HU-08 amb codi TOTP nou i motiu (RN-M01-60) i avís separat al registre (RN-M01-61); CA-M01-48 a CA-M01-55 amb proves, també amb peticions simultànies. CI d'aquesta tanda (0bfcee8): verd, segons el responsable del projecte. **Revisió al navegador** (03/11/2026, Chrome): a 50324e9 la confirmació del correu i la contrasenya nova des de l'enllaç fallaven amb un 403 de CSRF («Origin: null» per «no-referrer» a les pàgines netes); corregit a ad5d53d, amb proves amb CSRF activat, i comprovat al mateix navegador sense manipular cap capçalera; CI: verd a 942b80a (PR #4, sis feines, dues execucions), segons el responsable del projecte. **Ajustos de la [066](decisions/066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md)** (04/11/2026): reenviament sense el límit d'un sol ús i prova que el límit d'origen avança igual amb compte i sense; captures de la revisió afegides al diari; proves del reenviament amb el mateix estat, el límit d'origen i peticions simultànies, i comprovació a Chrome del reenviament múltiple (4e62231; els reenviaments repetits es van fer enviant el formulari des de la pàgina, no tots amb botons visibles); CI de referència: verd a e316e40 (proves, secrets i captures, dues execucions), segons el responsable del projecte. **Feta** (04/11/2026; aprovada pel responsable del projecte el 04/11/2026 dins de l'abast funcional actual, a partir dels informes, els resultats i les limitacions documentades al [diari](diari-de-construccio/T-M01-05.md); no aprova el disseny final de les pantalles). **No tanca:** la T-M01-38 (disseny i usabilitat de les pantalles, inclòs el recorregut després de reenviar); la T-M00-06 (reserva i prioritat dels correus); la T-M01-39 i [P-53](decisions/pendents.md) (proposta no aprovada); Q-03, [P-52](decisions/pendents.md) (abans de producció del TOTP personal) i Q-26; les comprovacions de desplegament (HTTPS real, proxy i registres d'accés amb rutes amb testimoni, arquitectura §7); i les limitacions de la revisió: només Chrome, sense lector de pantalla i sense escanejar el QR del TOTP amb un mòbil real |
| T-M01-06 | Rols (8 de la 00 + els que decideixi P-04) i comprovació de permisos per rol i objecte | M | `apps/core/permissions.py` | T-M01-05 | Prova de la llista de rutes sense sessió (RN-40). **Feta** (01/11/2026) amb la T-RP-01, segons la [lectura de la 060](#ajustos-060-lectura) |
| T-M01-07 | Registre d'activitat immutable (també a PostgreSQL) | M | `apps/core/audit.py`, migració de permisos | T-M01-04 | Prova que un UPDATE directe falla. **Feta** (02/11/2026): `AuditEntry` (hora en UTC, actor compte, convidat, sistema o sense identificar; persona, rols actius de RN-RP-15, IP, acció, objecte, camp, valors anterior i nou, motiu i detalls), bloquejat a l'ORM i amb disparadors de PostgreSQL contra UPDATE, DELETE i TRUNCATE (`core/0004`); servei `audit.record` i `audit.record_changes`, que rebutja els noms de camp que semblen secrets (RN-52); entrades d'entrada, sortida, intents fallits, bloquejos, TOTP, codis de recuperació i rols. **Queda:** l'excepció acotada de RN-89, que afegirà amb una migració pròpia la tasca de l'esborrat RGPD (T-M01-22), i la pantalla de consulta (T-M01-07b) |
| T-M01-07b | Llistat i filtratge del registre d'activitat (HU-14): M6 hi veu totes les entrades i P20, només les de dades de socis; filtres per data, compte, acció i objecte; només lectura. Afegida el 02/11/2026 | S | `apps/core/views/audit.py`, plantilles | T-M01-07, T-RP-01 | Prova per cel·la de M6 i P20 (sense permís, «no trobat»); prova que la pantalla no ofereix cap manera de modificar ni esborrar (CA-14.3); checklist C8. Abans del nivell 1 |
| T-M01-08 | Textos legals i consentiments amb versió i canal | S | `apps/core/consents.py` | T-M01-07 | CA-17.x de la 00. **Feta** (02/11/2026): `LegalText` i `Consent`, als quals només s'afegeixen files (`core/0005`); publicar (M12) crea la versió següent; atorgar i retirar afegeixen una fila amb la versió, el canal i, si és presencial, el compte que el registra; tot queda al registre d'activitat. Amb Q-16 oberta, no hi ha llista fixa de tipus i una versió nova no obliga a tornar a donar el consentiment |
| T-M01-09 | Càrrec i departament (estructura bàsica de la 00) | M | `apps/core/charges.py` | T-M01-07 | CA-15.x i CA-16.x de la 00. **Feta** (02/11/2026): `Department` (amb «General» des de la migració `core/0006`), `Charge` i `Payment` bàsics, sense esborrar mai; imports en cèntims comprovats al codi i a la base de dades; transicions de RN-67 amb registre; «pagat» només des del proveïdor o la conciliació (manual bloquejat per P-12); domiciliació només per a quotes; quotes sempre a «General»; serveis de departament amb M7. Segons la [lectura de la 060](#ajustos-060-lectura) |
| T-M01-09b | Preparació per traduir ([061](decisions/061-plataforma-preparada-per-traduir.md)), en dos commits: (a) configuració (`LANGUAGES` només amb el català, `LOCALE_PATHS`, `LocaleMiddleware`, processador `i18n`, `<html lang>` dinàmic, regla `INT` de ruff), `Person.preferred_language`, `LegalText.language` amb la restricció `(kind, version, language)`, `current_text` amb reserva al català i `persons.language_for`, i la migració `core/0007`; (b) marcatge de les cadenes existents segons la [regla d'idiomes](#idiomes) i nom dels rols amb `get_code_display()`. Afegida el 02/11/2026 | M | `config/settings/base.py`, `apps/core/models.py`, `consents.py`, `persons.py`, `migrations/0007_*`, plantilles, formularis i vistes | T-M01-08 | A cada commit, `makemigrations --check` net i la suite completa en verd; prova que `Accept-Language: es` dona català; proves de la reserva de `language_for` i de `current_text` i de la restricció única. **Feta** (02/11/2026): (a) configuració, camps i migració `core/0007`; (b) unes 200 cadenes marcades (models, catàleg de permisos, formularis, vistes, serveis i plantilles), `Role.__str__` amb `get_code_display()`. Sense cap `.po`: arriben amb la primera llengua nova (P-49) |
| T-M01-10 | Correu mínim (plantilles, cua) i fitxers privats (PDF) | M | `apps/core/mail.py`, `files.py` | T-M01-03, T-M01-09b | Correu a la bústia de proves; URL signada caduca; plantilla per llengua (`emails/<nom>.<llengua>.…`) triada amb `persons.language_for` i, si no n'hi ha, la catalana; generada dins de `translation.override` en posar-la a la cua, i el missatge guarda la llengua (061, punt 7). **Feta** (03/11/2026): cua de tasques sobre PostgreSQL amb procrastinate; `mail.queue_email` amb plantilla per llengua i reserva al català, generada dins de `translation.override`. El registre d'enviaments (`OutgoingEmail`, `core/0008`) guarda la llengua i esborra el cos quan s'envia bé o quan s'esgoten els intents. Transport SMTP configurable: Brevo o Scaleway sense tocar el codi. Remitent `no-respon@cris1954.cat` amb resposta a cris@cris.es. Fitxers privats (`PrivateFile`, `core/0009`) amb clau aleatòria i URL signada de 5 minuts després de comprovar compte i objecte; tipus comprovat pel contingut, mida de 10 MB (V-08) i exportació RGPD esborrada als 7 dies. Fora de producció, un emmagatzematge local que imita Scaleway. Correu comprovat a la bústia de proves. **Queda:** comptador diari, reserva, tandes i avís del 80 % (RN-A3 a RN-A6), butlletí i avisos de Brevo (RN-A9, RN-A10), i bloqueig de fitxers en un esborrat RGPD (RN-B8) |
| T-M01-11 | Models del M01: tipus, soci, historial, sol·licitud, comptador, carnet, llicència | M | `apps/members/models.py` | T-M01-04, T-M01-09 | Restriccions i índexs comprovats amb proves. **Feta** (04/11/2026; aprovada pel responsable del projecte dins l'abast actual, sense haver executat les proves ni revisat el codi personalment; CI verd de referència a a446ece; el commit del tancament, documental: CI [A comprovar]). **No tanca:** [P-54](decisions/pendents.md) abans de la T-M01-14; la persona i el tipus del càrrec d'`AnnualFee` (T-M01-14, T-M01-17, T-M01-18); transicions, estats, dates i readmissió ([067](decisions/067-readmissio-d-un-antic-soci.md); T-M01-12, T-M01-14, T-M01-17); la llavor de la importació (T-M01-24); les excepcions d'anonimització (T-M01-22) ([diari](diari-de-construccio/T-M01-11.md)). Abans: **Feta en part** (04/11/2026, a501793, CI verd a d3d1064 confirmat pel responsable; segona tanda a ba89284 i tercera a a34f5a1, CI verd a 28cd481 confirmat pel responsable; quarta tanda, només documentació, a 48d9ed6, CI verd a 7b2c586 confirmat pel responsable; cinquena, només documentació, a 1c87847, CI [A comprovar]): els vuit models (també `AnnualFee`, amb les precisions de la [lectura](#ajustos-060-lectura)), migracions `members/0001` a `0005` i 69 proves contra la base de dades, amb CA-M01-47 i `avatar_seed` aleatòria, immutable i amb format comprovat ([diari](diari-de-construccio/T-M01-11.md)). Readmissió: [decisió 067](decisions/067-readmissio-d-un-antic-soci.md), sense implementar (T-M01-12 i T-M01-14). Decisió pendent: [P-54](decisions/pendents.md), abans de la T-M01-14. **Queda:** la revisió del responsable |
| T-M01-12 | Serveis d'estat i transicions (RN-M01-07 a RN-M01-09) | M | `apps/members/services.py` | T-M01-11, T-M01-07 | CA-M01-07 a 09. **Feta en part** (04/11/2026, 8653602; decisions abans del codi a f4624d0; CI [A comprovar]): serveis autoritzats `mark_unpaid` i `unmark_unpaid` (P9) i primitives internes `_change_status`, `_change_type` i `_readmit` (067), amb historial i registre a la mateixa transacció, dates i `left_on` validats i conflicte d'interès, segons la [lectura](#ajustos-060-lectura); 77 proves noves ([diari](diari-de-construccio/T-M01-12.md)). CA-M01-07 i 08 coberts; de CA-M01-09, el motiu i P9, però no la part del carnet «no vàlid» (T-M01-19 i T-M01-20). CI de 1647d72 (fins al diari): verd (proves, secrets i captures, dues execucions), segons el responsable del projecte. **Segona tanda** (revisió del responsable, 04/11/2026; 812517f a 289277d; CI [A comprovar]): readmissió no anterior a la baixa actual, compte no actiu rebutjat també a les primitives (amb la fila del compte bloquejada dins la transacció), prova executada que el bloqueig no agafa el tipus, i la prova del conflicte d'interès assignada als punts d'entrada; 88 proves al fitxer. **Queda:** la revisió del responsable. **Feta** (04/11/2026; aprovada pel responsable del projecte dins l'abast actual, a partir dels informes, els resultats de les proves i el CI, sense haver executat les proves ni revisat el codi personalment; CI de referència verd a 081868b, segons el responsable; el commit del tancament, documental: CI [A comprovar]). Característica actual: cada canvi bloqueja la fila del compte que actua fins al final de la transacció, de manera que dos canvis simultanis d'un mateix compte van un darrere l'altre (impacte de rendiment no mesurat). **No tanca:** la validesa del carnet de CA-M01-09 (T-M01-19 i T-M01-20); l'historial dels socis importats de baixa (T-M01-24); les proves dels punts d'entrada que demostrin que l'intent rebutjat per conflicte d'interès queda registrat (T-M01-14, T-M01-17, T-M01-18, T-M01-22); els comportaments del canvi de tipus pendents (soci de baixa, tipus inactiu, motiu d'un impagat; T-M01-17); i [P-54](decisions/pendents.md) i les decisions de quotes, que no són d'aquesta tasca ([diari](diari-de-construccio/T-M01-12.md)) |
| T-M01-13 | Formulari «Fer-se soci» i alta presencial | M | `apps/members/views/public.py`, plantilles | T-M01-08, T-M01-12, T-M01-02 | CA-M01-01, 02 |
| T-M01-14 | Altes pendents: aprovar, rebutjar, número amb bloqueig | M | `apps/members/views/admin.py` | T-M01-13 | CA-M01-03 a 05 |
| T-M01-15 | Llistat i fitxa de soci (filtres, historial, exportació) | M | `apps/members/views/admin.py` | T-M01-12 | Proves de permisos per rol |
| T-M01-16 | Àrea del soci: perfil, quotes, sol·licituds | M | `apps/members/views/personal.py` | T-M01-12, T-M01-05 | CA-M01-12, 25. El perfil valida `preferred_language` contra les llengües actives i només mostra el selector si n'hi ha més d'una (061) |
| T-M01-17 | Canvi de tipus i baixa (sol·licitud i resolució) | M | `services.py`, vistes | T-M01-16 | Proves de P-M01-B i C |
| T-M01-18 | Generació de quotes, recordatoris i marca d'impagat | M | `apps/members/fees.py`, tasques de la cua | T-M01-09, T-M01-12 | CA-M01-09 a 11 |
| T-M01-19 | Carnet: testimoni, revocació, PDF, pàgina del soci | M | `apps/members/cards.py` | T-M01-12, T-M01-10 | CA-M01-15 |
| T-M01-20 | Verificació pública amb limitació de peticions | S | `apps/members/views/public.py` | T-M01-19 | CA-M01-13, 14, 16 |
| T-M01-21 | Web instal·lable: manifest, service worker amb carnet sense connexió | M | `static/`, plantilla base | T-M01-19 | CA-M01-17 |
| T-M01-22 | RGPD del M01: exportació i anonimització | M | `apps/members/privacy.py` | T-M01-12; HU-18 i HU-19 de la 00 | CA-M01-18, 19. En anonimitzar, `preferred_language` torna a `"ca"` (061). Dos riscos anotats a la T-M01-10: (1) el registre d'enviaments (`OutgoingEmail`) guarda l'adreça del destinatari, que s'ha d'anonimitzar quan s'anonimitza la persona; (2) si una operació es desfà just després de desar un fitxer privat, el fitxer pot quedar a l'emmagatzematge sense registre (risc petit amb el volum del club; es pot afegir una neteja més endavant) |
| T-M01-23 | Registre mínim de llicència a la fitxa | S | `models.py`, vistes | T-M01-15 | Prova de dates |
| T-M01-24 | Importació de Cluber, **fase de prova** (sense escriure res), feta i provada amb un **fitxer inventat** amb el format de S-M01-16 | L | `apps/members/imports/cluber.py` | T-M01-11 | CA-M01-20, 21. Quan arribi la mostra real anonimitzada (Q-23), es repeteix la prova i s'ajusta el format. **Feta en part** (04/11/2026, 0389010; precisions abans del codi a f7465a6; CI [A comprovar]): lector CSV i `preview()` sense escriptures, amb el perfil CSV inicial, el rebuig per la columna d'IBAN abans de llegir cap fila, el número de soci, els duplicats dins del fitxer i les coincidències sense tipus de document, segons la [lectura](#ajustos-060-lectura); 75 proves noves ([diari](diari-de-construccio/T-M01-24.md)). CA-M01-21 cobert; de CA-M01-20, l'absència d'escriptures de `preview()`, però no que l'administrador vegi el resum. **Queda:** `ImportBatch` i els camps `import_batch` (esperen el contracte del lot) i la comprovació de CA-20.8; la presentació del resum (T-M01-38 i criteris vigents); les equivalències del tipus, l'estat i la data d'alta; i Q-23: la mostra parcial rebuda el 04/11/2026 no està anonimitzada i no serveix per repetir la prova. **Revisió del responsable** (04/11/2026; precisions a f879b95, codi a 3cd9662; CI [A comprovar]): el resultat intern només conserva el document normalitzat i el número; `summary()` és el resum sense valors del fitxer, i `repr` no mostra dades; el detall del catàleg, omès explícitament per sobre de 50 valors; límit de camp provat també per sobre del límit intern del mòdul `csv`; un número de més de 4.300 xifres ja no fa fallar la previsualització; antigues sòcies no anonimitzades detectades sigui quin sigui el compte. 87 proves al fitxer; deu mutacions del codi, totes detectades. Continua feta en part, amb les mateixes peces pendents |
| T-M01-25 | Importació de Cluber, **fase final** preparada però bloquejada per configuració | M | `apps/members/imports/cluber.py` | T-M01-24 | CA-M01-22, 23 |
| T-M01-26 | Serveis oferts a altres mòduls (§8) amb proves de contracte | S | `apps/members/services.py` | T-M01-12, T-M01-19 | Proves de contracte en verd |
| T-M01-27 | Dades de prova inventades (socis, quotes, carnets, fitxer de Cluber) | S | `apps/members/fixtures/`, ordre de gestió | T-M01-11 | Es carreguen amb una ordre; cap dada real |
| T-M01-28 | Revisió d'accessibilitat i de permisos del mòdul | M | — | T-M01-13 a T-M01-21 | Auditoria automàtica sense errors greus; revisió amb teclat i lector de pantalla |
| T-M01-29 | Documentació: guia de la secretaria i del tresorer; actualitzar aquest pla i la spec | S | `docs/` | T-M01-28 | Revisada |
| T-M01-30 | Servei de lectura de la llicència (`licence_record`, `licence_records`), sense cap escriptura (049) | S | `apps/members/services.py` | T-M01-23 (registre mínim de llicència) | Prova que el servei no escriu res i que retorna res si no hi ha registre |

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
- **Dades dins la UE:** base de dades, còpies i correu dins la UE ([035](decisions/035-dades-nomes-dins-ue.md)); el correu, amb Brevo ([062](decisions/062-brevo-es-mante-com-a-proveidor-de-correu.md)).
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
| S-M01-19 | Remitent dels correus (Q-26); el proveïdor és Brevo ([062](decisions/062-brevo-es-mante-com-a-proveidor-de-correu.md)) | `no-respon@cris1954.cat`, correu a la bústia de proves | Informàtica |
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


<a id="M01-addenda-052"></a>
## M01 — Addenda de la [052](decisions/052-llicencia-font-unica-al-06.md): còpia de lectura de la llicència

Aprovada el 27/10/2026. **No canvia cap regla del M01** ni cap fila aprovada de les seccions anteriors: les completa per al moment en què el 06 entri en producció.

**Què passa.** El 06 és l'únic propietari de les llicències i emet els esdeveniments `licence.issued`, `licence.renewed`, `licence.expired` i `licence.cancelled` (mecanisme de la [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)). El M01 s'hi subscriu i manté el seu registre mínim (`LicenceRecord`) com a **còpia de lectura**. El M01 no importa cap codi del 06: no hi ha cicle de dependències.

| | Quan el 06 entra en producció |
|---|---|
| **Deixa d'existir al M01** | El formulari per crear o editar a mà el registre mínim (a la fila P19, la secretaria passa de «Sí» a «Consulta»); l'origen `manual` per a registres nous |
| **Es conserva al M01** | El model `LicenceRecord` i RN-M01-29; els registres importats de Cluber i els fets a mà abans del 06; la lectura a la fitxa i al carnet; `members.licence_record` i `members.licence_records` (049), que llegeixen la còpia; l'exportació i l'anonimització RGPD |
| **S'afegeix al M01** | Camps `licence_ref` (identificador de la llicència del 06, únic, null) i `cancelled_on` (null) a `LicenceRecord`, i l'origen `licences`; el subscriptor dels quatre esdeveniments |

**Regles de la còpia** (noves, no en substitueixen cap)
| ID | Regla |
|---|---|
| RN-M01-35 | Cada esdeveniment de llicència d'un soci crea o actualitza la fila amb el mateix `licence_ref`; si la llicència ve del pas únic del 01 al 06, actualitza la fila d'origen en lloc de crear-ne una de nova ([052](decisions/052-llicencia-font-unica-al-06.md), punt 8) |
| RN-M01-36 | `licence.cancelled` omple `cancelled_on`; `licence.expired` no canvia res (la caducitat ja surt de la data). Res s'esborra |
| RN-M01-37 | Un esdeveniment repetit o més antic que la dada que ja hi ha no fa res (idempotent, amb el registre de lliuraments de la 049) |
| RN-M01-38 | `members.licence_record(person)` torna la fila no cancel·lada amb la data de caducitat més tardana |
| RN-M01-39 | Les persones que no són sòcies no tenen còpia al M01: la seva llicència només és al 06 |

**Criteris d'acceptació**
- **CA-M01-26** Donat un soci sense registre, quan arriba `licence.issued`, llavors es crea una fila amb origen `licences` i `members.licence_record` la torna.
- **CA-M01-27** Donat el mateix esdeveniment repetit, quan arriba de nou, llavors no es crea cap fila ni cap canvi.
- **CA-M01-28** Donat una llicència cancel·lada, quan arriba `licence.cancelled`, llavors la fila té `cancelled_on` i `members.licence_record` ja no la torna.
- **CA-M01-29** Donat el 06 en producció, quan la secretaria vol crear o editar a mà un registre mínim, llavors no hi ha formulari i una petició forçada es rebutja.

**Tasca**
| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M01-31 | Còpia de lectura de la llicència: camps nous (també `source_version`), subscriptor dels esdeveniments del 06 que ignora els més vells, comprovació diària amb registre i fi de l'edició manual quan el 06 estigui actiu ([052](decisions/052-llicencia-font-unica-al-06.md), [054](decisions/054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md)) | M | `apps/members/licences.py`, `apps/members/tasks.py`, migració | T-M01-30, T-M05b-21 (mecanisme d'esdeveniments), T-M06-15 | CA-M01-26 a 34; proves del M01 en verd |

<a id="M01-addenda-054"></a>
## M01 — Addenda de la [054](decisions/054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md): versió dels esdeveniments i comprovació diària

Aprovada el 27/10/2026. Completa l'[addenda de la 052](#M01-addenda-052) **sense canviar cap regla** del M01 ni de l'addenda. La feina és a la mateixa tasca T-M01-31.

**Entitats.** Camp nou `source_version` (enter, null) a `LicenceRecord`: la versió de la llicència del 06 que reflecteix la fila.

**Regles noves** (no en substitueixen cap)
| ID | Regla |
|---|---|
| RN-M01-40 | Cada esdeveniment de llicència porta `version` (comptador de la llicència al 06) i `occurred_at` (RN-M06-17). El 01 aplica un esdeveniment només si la seva `version` és més gran que `source_version`; si és igual o més petita, no fa res. Compara la versió, mai l'hora |
| RN-M01-41 | **Comprovació diària:** un cop al dia, el 01 llegeix l'estat actual de les llicències dels socis amb la font que el 06 li ha registrat (`members.register_licence_source`) i el compara amb la còpia (tipus, durada, dates, `cancelled_on`, `source_version`). Si troba una diferència, la corregeix: el 06 sempre té raó. Si no hi ha cap font registrada, no fa res |
| RN-M01-42 | La comprovació no esborra res. Una fila amb `licence_ref` que el 06 no té no es toca: surt a la llista per revisar de la secretaria. Les files d'origen `cluber` o `manual` sense `licence_ref` no es comparen |
| RN-M01-43 | Cada correcció queda al registre d'activitat amb el valor anterior i l'actor «comprovació diària». La tasca guarda quantes files ha revisat i quantes ha corregit. Qui rep un avís quan hi ha correccions: [A validar: informàtica] |

**Servei nou**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `members.register_licence_source(source)` | funció `source() → llicències dels socis amb {licence_ref, person, type, duration, starts_on, expires_on, cancelled_on, version}` | — | — | 06, en arrencar (el 06 ja depèn del 01; el 01 no importa res del 06) |

**Criteris d'acceptació**
- **CA-M01-30** Donat una còpia amb `source_version` 3, quan arriba un esdeveniment amb `version` 2 (o 3), llavors no canvia res; amb `version` 4, s'aplica.
- **CA-M01-31** Donat `licence.renewed` (versió 2) lliurat abans que `licence.issued` (versió 1), quan arriben tots dos, llavors la còpia queda amb les dades de la renovació.
- **CA-M01-32** Donat una còpia amb una data de caducitat diferent de la del 06, quan corre la comprovació diària, llavors la fila queda igual que al 06 i el registre d'activitat guarda el valor anterior i l'actor «comprovació diària»; si corre una altra vegada, no corregeix res.
- **CA-M01-33** Donat cap font registrada, quan corre la comprovació diària, llavors no fa cap canvi; donat una fila amb un `licence_ref` que el 06 no té, llavors no s'esborra i surt a la llista per revisar.

**Precisió** (addenda mínima, aprovada el 27/10/2026; no canvia cap regla anterior)
| ID | Regla |
|---|---|
| RN-M01-44 | Si la font del 06 falla, no respon o torna una llista buida mentre el 01 té còpies amb `licence_ref`, la comprovació **se salta sencera**: no corregeix, no cancel·la ni esborra res, ho anota al registre de la tasca i avisa (destinatari [A validar: informàtica], com RN-M01-43). Una llicència només es marca cancel·lada si el 06 la torna cancel·lada, mai perquè falti a la llista |

- **CA-M01-34** Donat una còpia amb llicències vigents, quan la font del 06 dona error o torna una llista buida, llavors cap fila canvia, el registre de la tasca diu «comprovació saltada» i s'envia l'avís.

<a id="M01-addenda-055"></a>
## M01 — Addenda de la [055](decisions/055-ajustos-configurables-i-addendes.md): pantalla d'ajustos

Aprovada el 28/10/2026. **No canvia cap regla** del M01: els valors que el text deixava oberts passen a la [peça comuna d'ajustos](#valors-configurables-055), amb valor inicial, rang, rol i registre. Els valors inicials són les propostes que ja hi havia; les preguntes obertes (RN-M01-14, S-M01-08, S-M01-09) continuen obertes. La feina és a la tasca T-M01-32.

**Valors** (de l'[apèndix](#valors-configurables))
| VC | Clau | Valor inicial | Rang | Qui el canvia | Data d'entrada en vigor |
|---|---|---|---|---|---|
| VC-01 | Preu del tipus de soci (`annual_fee_cents`), que continua al tipus | 3500 i 9000 cèntims (validats pel responsable del projecte el 03/11/2026) | > 0 | Tresorer o administrador, amb motiu | Sí (nova) |
| VC-02 | `members.fee_reminder_days_before`; `members.fee_reminder_days_after` | 15; 15 i 30 | 1 a 90 | Tresorer | — |
| VC-03 | `members.card_back_text` | Contacte del club i com verificar-lo; el text final [A validar: junta, S-M01-08] | Fins a 300 caràcters | Secretaria o administrador | — |
| VC-04 | `members.classic_member_years` (0 = sense insígnia) | 0 | 0 a 60 | Administrador, per decisió de la junta | — |

**Regles noves** (no en substitueixen cap)
| ID | Regla |
|---|---|
| RN-M01-45 | El preu de cada tipus de soci guarda versions amb data d'entrada en vigor (igual que `SettingVersion`, RN-AJ-03). La quota es genera amb el preu vigent a la data en què es genera, que és el que ja diu RN-M01-13; un canvi no toca les quotes creades. Cada canvi avisa el tresorer i la junta (RN-AJ-04) |
| RN-M01-46 | Els recordatoris de quota, el darrere del carnet i la insígnia de soci clàssic llegeixen el valor dels ajustos en el moment d'enviar o de generar; no hi ha cap valor escrit al codi |

**Criteris d'acceptació**
- **CA-M01-35** Donat el preu d'un tipus a 3500 i un canvi a 4000 amb data d'entrada en vigor d'aquí a un mes, quan es genera una quota avui, llavors és de 3500; quan es genera després d'aquella data, és de 4000; les quotes ja creades no canvien, i el tresorer i la junta reben un correu amb 3500 i 4000.
- **CA-M01-36** Donat els dies de recordatori canviats a 10 abans, quan corre la tasca de recordatoris, llavors fa servir 10; un valor de 0 o de 91 es rebutja.
- **CA-M01-37** Donat `members.classic_member_years` a 0, quan es genera un carnet, llavors no hi ha insígnia; a 25, la té qui té 25 anys o més d'antiguitat.

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M01-32 | Pantalla d'ajustos del 01 (VC-01 a VC-04), versions del preu del tipus amb data d'entrada en vigor i lectura dels valors des de les tasques i el carnet ([055](decisions/055-ajustos-configurables-i-addendes.md)) | S | `apps/members/settings.py`, vistes, migració | T-AJ-02, T-M01-18, T-M01-19 | CA-M01-35 a 37; proves del M01 en verd |


<a id="M01-addenda-058"></a>
## M01 — Addenda de la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md): data de naixement (00), caducitat desconeguda i conservació

Aprovada el 29/10/2026. **No canvia cap regla** del M01 ni edita la spec 00: hi afegeix el que diuen els punts 1, 7 i 10 de la 058. La part de la 00 es construeix aquí, com la resta de peces de la 00 que el 01 necessita. El fora d'abast de [M01-1](#M01-1-intencio) («data de naixement») queda substituït per aquesta addenda; la relació amb tutors continua fora d'abast mentre P-33 sigui obert.

**Entitats**
- `Person` (00): camp nou `birth_date` (`DateField`, null). Substitueix la V-04 de la spec 00 només en aquest punt.
- `LicenceRecord`: `expires_on` passa a admetre buit (caducitat desconeguda). La restricció `expires_on ≥ issued_on` només s'aplica quan hi ha data.

**Regles noves** (no en substitueixen cap)
| ID | Regla |
|---|---|
| RN-M01-47 | **Data de naixement.** Finalitat: tramitar llicències i comprovar l'edat mínima dels cursos. Es demana a l'alta i a la fitxa; si és obligatòria a l'alta o només en demanar una llicència: [A validar: secretaria] (supòsit: obligatòria en demanar una llicència, opcional a la resta) |
| RN-M01-48 | Només la secretaria i l'administrador veuen la data. La resta de rols que poden veure la persona veuen només «major d'edat», «menor d'edat» o «edat desconeguda», que calcula el servei de la 00 `persons.age_band(person, on)`. Cap llistat, exportació (excepte l'RGPD i el llistat de tramitació del 06) ni registre no porta la data |
| RN-M01-49 | La data de naixement s'inclou a l'exportació RGPD de la persona i s'anonimitza amb la resta de dades. P-33 (menors) continua obert: aquesta addenda no admet socis menors |
| RN-M01-50 | **Caducitat desconeguda.** Un registre mínim pot no tenir `expires_on` (Cluber no la guarda). La fitxa i el carnet hi diuen «caducitat desconeguda». `members.licence_record(person)` torna primer la fila amb la caducitat coneguda més tardana; només si no n'hi ha cap, la fila sense data, marcada com a desconeguda. Per al 02, una llicència amb caducitat desconeguda és «pendent de confirmar», no vigent (com «en tràmit», RN-M02-10) [A validar: secretaria] |
| RN-M01-51 | **Conservació** ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) punt 7): les quotes, els càrrecs i els pagaments no s'eliminen mai. Quan s'esborren les dades d'una persona (RGPD), les seves dades personals en aquests registres s'anonimitzen passat el termini legal [A verificar: gestoria, Q-14], en lloc de destruir els registres |

**Criteris d'acceptació**
- **CA-M01-38** Donat un soci amb data de naixement, quan l'obre l'instructor o el tresorer, llavors veuen «major d'edat» i no la data; quan l'obre la secretaria, veu la data; una petició forçada de la data per un altre rol es rebutja.
- **CA-M01-39** Donat un soci que demana l'esborrat RGPD, quan s'executa, llavors l'exportació prèvia porta la data de naixement i, després, la data queda anonimitzada amb la resta de dades.
- **CA-M01-40** Donat un registre importat de Cluber sense caducitat, quan es desa, llavors s'accepta; la fitxa diu «caducitat desconeguda» i `members.licence_record` el torna marcat com a desconegut si no n'hi ha cap altre amb data.

**Tasques**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M01-33 | `Person.birth_date` (00), servei `persons.age_band`, visibilitat per rol i exportació i anonimització RGPD ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md)) | S | `apps/core/models.py`, `apps/core/persons.py`, migració | T-M01-04, T-M01-06 | CA-M01-38, 39 |
| T-M01-34 | Caducitat desconeguda al registre mínim i a `members.licence_record` ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md)) | S | `apps/members/models.py`, `services.py`, migració | T-M01-30 | CA-M01-40 |

**Precisió del 29/10/2026** (addenda mínima aprovada pel responsable del projecte; aplica la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) i **substitueix el supòsit de RN-M01-47**; no canvia cap altra regla). Tota la precisió és [A validar: junta], perquè és una dada personal més: finalitat, abast i obligatorietat segons el principi de minimització (punt 0 de l'[ordre del dia](#ordre-del-dia-decisions)).

| ID | Regla |
|---|---|
| RN-M01-52 | **Socis:** la data de naixement és **obligatòria a l'alta de tot soci**, al formulari «Fer-se soci» i a l'alta presencial. Una alta sense data no es pot aprovar. Finalitat: tramitar llicències i comprovar l'edat mínima dels cursos i de les activitats |
| RN-M01-53 | **No socis (convidats):** la data és obligatòria només si la persona demana una llicència o s'inscriu a una activitat amb edat mínima (RN-M02-33); a la resta, és opcional |
| RN-M01-54 | **Menors:** si la data indica que la persona és menor d'edat, l'alta es bloqueja mentre P-33 sigui obert (L-M01-10). La visibilitat continua sent la de RN-M01-48 |
| RN-M01-55 | **Socis existents sense data** (els importats de Cluber): la importació de Cluber accepta una **columna opcional** de data de naixement; si no hi és, el soci queda «sense data de naixement». El soci la pot completar al seu perfil i rep un avís al compte personal i per correu. La secretaria té la llista dels socis sense data i també la pot completar. Mentre no hi sigui, el soci surt com a «edat desconeguda» i **no es bloqueja cap acció que ja tingui**; només la demana una acció nova que l'exigeixi (RN-M01-53) |
| RN-M01-56 | **Llicències d'any natural amb caducitat desconeguda** (abans que existeixi el 06): la secretaria les pot confirmar **en bloc** (selecciona els registres d'any natural pendents i en fixa la caducitat al 31/12 de l'any que tria) i el soci pot **declarar** la caducitat de la seva llicència al perfil. Una caducitat declarada queda marcada «declarada pel soci» fins que la secretaria la confirma. Cada canvi va al registre d'activitat amb el valor anterior |

- **CA-M01-41** Donat el formulari «Fer-se soci» sense data de naixement, quan s'envia, llavors es rebutja; donat una alta pendent sense data (alta presencial antiga o dada esborrada), quan la secretaria la vol aprovar, llavors es rebutja.
- **CA-M01-42** Donat una alta amb una data que fa la persona menor d'edat, quan s'envia, llavors queda bloquejada amb el missatge de P-33.
- **CA-M01-43** Donat un soci importat de Cluber sense data, quan entra al compte personal, llavors veu l'avís i el camp per completar-la; surt a la llista de la secretaria; i pot continuar pagant la quota i fent el que ja feia.
- **CA-M01-44** Donat deu registres d'any natural sense caducitat, quan la secretaria en confirma vuit en bloc per a l'any 2026, llavors aquests vuit caduquen el 31/12/2026, els altres dos no canvien i el registre d'activitat guarda els valors anteriors; donat un soci que declara la caducitat, llavors el registre queda «declarada pel soci» fins que la secretaria la confirma.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M01-35 | Data de naixement obligatòria a l'alta dels socis i condicional per als convidats; bloqueig de menors; columna opcional a la importació de Cluber; avís, camp al perfil i llista de la secretaria | M | `apps/members/views/`, `imports/cluber.py`, `apps/core/persons.py` | T-M01-13, T-M01-14, T-M01-25, T-M01-33 | CA-M01-41 a 43 |
| T-M01-36 | Confirmació en bloc de les caducitats d'any natural pendents i declaració del soci | S | `apps/members/licences.py`, vistes | T-M01-34 | CA-M01-44 |

<a id="M01-addenda-059"></a>
## M01 — Addenda de la [059](decisions/059-rols-i-permisos-editables.md): permisos editables i configuració inicial

Aprovada el 30/10/2026. **No canvia cap regla** del M01. La taula de [M01-4](#M01-4-rols) passa a ser la **configuració inicial** dels permisos del mòdul, que l'administrador pot canviar des de l'app ([peça comuna](#rols-i-permisos-059)). Els canvis respecte de la taula, cel·la per cel·la, són a la [matriu inicial](#rols-i-permisos-059-matriu). Les cel·les [A validar] prenen el supòsit per defecte del mòdul; si no n'hi ha, «—»; si l'acció es quedaria sense ningú, l'administrador.

**Què canvia**
- El **tresorer** i el **President** aproven o rebutgen altes (P3) i resolen canvis de tipus i baixes (P7), amb el permís nou de consultar sol·licituds (P3a). El tresorer no crea altes ni edita dades del soci.
- Ni el tresorer ni el President veuen la data de naixement ni el document. La data de naixement continua com a la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) (regla protegida).
- Queden resolts:
  - S-M01-14: l'administrador atén les sol·licituds RGPD;
  - S-M01-22: el conflicte d'interès és una regla protegida;
  - S-M01-23: Junta, Resp. comunicació i Resp. botiga existeixen, sense permisos al 01;
  - el punt 10 de [M01-13](#M01-13-riscos): la decisió nova que amplia la llista de rols és la 059.
- La T-M01-06 la completa la T-RP-01 (motor, rols i catàleg).

**Criteri d'acceptació**
- **CA-M01-45** Donat un compte amb el rol tresorer, quan obre una sol·licitud d'alta, llavors la pot aprovar o rebutjar i hi veu «major d'edat» o «menor d'edat» en lloc de la data de naixement, sense el document. Quan la sol·licitud és seva, es rebutja i queda al registre.

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M01-37 | Declarar els permisos del 01 al catàleg (P2 a P20, P3a, C1 i C2) i comprovar-los a totes les vistes i serveis del 01 | S | `apps/members/permissions.py` | T-RP-01 | CA-M01-45; proves per cel·la del 01 (CA-RP-13) |

<a id="M01-addenda-060"></a>
## M01 — Addenda de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): ordre de les tasques

Aprovada el 31/10/2026. **No canvia cap regla** del M01; només fixa l'ordre de les tasques.
- La T-RP-01 i la T-RP-04 es fan just després de la T-M01-06. **De la T-M01-13 a la T-M01-22, i també la T-M01-33, depenen també de la T-RP-01**: cada vista declara i comprova el seu permís quan es fa. La T-M01-37 queda com a revisió final de la cobertura per cel·la.
- La **T-M01-31** (còpia de lectura de la llicència) es fa en construir el 06, al començament de la fase 2. No bloqueja que el 01 es doni per acabat.
- La **T-M01-36** (confirmació en bloc) és requisit previ per obrir les inscripcions del 02 ([RN-M02-34](#M02-addenda-060)).
- RN-M01-47 és un supòsit substituït per RN-M01-52: es construeix RN-M01-52.

<a id="M01-addenda-063"></a>
## M01 — Addenda de la [063](decisions/063-validacions-de-la-revisio-de-la-t-m01-02.md): contrasenya abans d'esborrar el compte

Aprovada el 03/11/2026. Afegeix una regla i un criteri i no en canvia cap altra. El pas 3 de [P-M01-F](#M01-5-processos) ja ho recull.

**Regla nova**
| ID | Regla |
|---|---|
| RN-M01-57 | **Contrasenya abans d'esborrar el compte.** Per enviar la sol·licitud «Esborrar el meu compte», el soci torna a escriure la contrasenya **sempre**, encara que acabi d'entrar, i el codi TOTP si el compte en té. Es fa servir el servei de reautenticació de la 00 (`accounts.require_recent_auth`, el de RN-M05a-12; tasca [T-M00-05](#ajustos-060-peces-00)), però **sense la finestra de 15 minuts**: la comprovació es fa a la mateixa petició que envia la sol·licitud. Si falla, no s'envia res i l'intent compta per al bloqueig per intents del compte (V-01). El missatge és «Contrasenya incorrecta» (o «Codi incorrecte») i no diu quants intents queden. L'intent fallit i la sol·licitud enviada queden al registre d'activitat |

**Criteri d'acceptació**
- **CA-M01-46** Donat un soci amb la sessió iniciada fa menys d'un minut, quan envia «Esborrar el meu compte» sense la contrasenya o amb una contrasenya incorrecta, llavors no es crea cap sol·licitud, veu «Contrasenya incorrecta» al costat del camp i l'intent compta per al bloqueig de V-01. Amb la contrasenya correcta, i el codi TOTP si el compte en té, es crea la sol·licitud.

**Contracte de serveis** (precisa [M05a-8](#M05a-8-serveis) sense editar-lo): `accounts.require_recent_auth(account, minutes)` admet `minutes=0`, que vol dir que s'ha de tornar a escriure a la mateixa petició. El 05a continua fent servir `minutes=15`.

**Tasques.** La prova de CA-M01-46 és a la T-M01-22, que també depèn de la T-M00-05. Les files aprovades no s'editen: ho diu la [lectura de les tasques substituïdes](#ajustos-060-lectura).

<a id="M01-addenda-064"></a>
## M01 — Addenda de la [064](decisions/064-una-baixa-es-pot-rebutjar-amb-motiu.md): baixa rebutjada i motius de la sol·licitud

Aprovada el 03/11/2026. Una baixa es pot rebutjar amb motiu obligatori (pas 2 de [P-M01-C](#M01-5-processos)). Els altres punts de [P-50](decisions/pendents.md) continuen oberts i no s'implementen. No canvia cap regla de negoci: només com es guarda el motiu.

**Entitats.** A [`MemberRequest`](#M01-6-entitats), aquests dos camps substitueixen el camp `reason`. La taula aprovada no s'edita.
| Camp | Tipus | Restriccions |
|---|---|---|
| `request_reason` | Text | Motiu de qui fa la sol·licitud. Obligatori per a `leave`; opcional per a la resta |
| `resolution_reason` | Text | Motiu de qui la resol. Obligatori quan `status` = `rejected`; opcional quan s'aprova o es cancel·la |

- Dues restriccions a la base de dades: si `kind` = `leave`, `request_reason` no pot ser buit; si `status` = `rejected`, `resolution_reason` no pot ser buit.
- CA-M01-05 («cal motiu» en rebutjar) es comprova amb `resolution_reason`.
- RGPD: tots dos camps són text lliure i poden contenir dades personals. S'anonimitzen a la T-M01-22, amb la resta de dades de la persona.

**Criteri d'acceptació**
- **CA-M01-47** Donat una baixa rebutjada, quan es consulta, llavors es conserven el motiu de la baixa i el de rebuig, i cap no substitueix l'altre.

**Tasques.** La T-M01-11 construeix els dos camps i les restriccions (CA-M01-47). La T-M01-22 també anonimitza `request_reason` i `resolution_reason` ([lectura de les tasques substituïdes](#ajustos-060-lectura)).

<a id="M01-addenda-065"></a>
## M01 — Addenda de la [065](decisions/065-enllacos-del-correu-i-restabliment-per-un-altre-administrador.md): enllaços del correu i restabliment per un altre administrador

Aprovada el 03/11/2026. Precisa la recuperació per correu, el reenviament de la verificació i el restabliment per un altre administrador de la spec 00 (HU-04, HU-08, RN-24, V-01), sense editar-la. No resol Q-03 ni [P-52](decisions/pendents.md). Els textos de RN-M01-58, RN-M01-59, CA-M01-50 i CA-M01-51 els canvia la [066](#M01-addenda-066) (04/11/2026).

**Regles noves**
| ID | Regla |
|---|---|
| RN-M01-58 | **Límits dels enllaços del correu.** Per destinatari (adreça normalitzada) i finalitat (recuperació o verificació): com a màxim 3 correus per hora i 6 cada 24 hores. Per origen: quan arriba a 10 peticions acceptades en 15 minuts, queda limitat 15 minuts comptats des de la desena; el límit és **conjunt** per a la recuperació i el reenviament. Una petició limitada per origen no envia res, no compta i no allarga cap finestra. Una petició limitada per destinatari no envia res ni compta per al límit del destinatari, però **compta per al límit d'origen**, perquè aquest avanci igual tant si l'adreça té compte com si no (text canviat per la [066](decisions/066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md)). No bloquegen l'entrada ni compten per a V-01. La resposta pública no canvia. Valors de seguretat al codi, en un sol lloc (`apps/accounts/limits.py`); canviar-los demana una decisió nova |
| RN-M01-59 | **Comptes pendents i reenviament.** Un compte personal pendent de verificar no rep cap enllaç de recuperació. El reenviament de la verificació només s'ofereix després de la contrasenya correcta d'un compte pendent (amb «Encara has de confirmar el correu»). Aquest estat dura com a màxim 10 minuts a la sessió; mentre dura, permet demanar reenviaments amb els límits de RN-M01-58 (sense el límit d'un sol ús que hi havia: [066](decisions/066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md)). No és cap sessió autenticada i no dona accés a res més. Abans d'enviar es torna a comprovar que el compte és pendent; el destinatari el decideix el servidor |
| RN-M01-60 | **Restabliment per un altre administrador.** Qui el fa escriu a la mateixa petició un codi TOTP nou del seu compte (cap codi ja acceptat abans, tampoc el de l'entrada), també en l'excepció de RN-RP-18, i un motiu obligatori, tant per a la contrasenya com per al TOTP. Un codi incorrecte no restableix res i compta per a V-01. Restablir la contrasenya no desbloqueja el compte ni li treu el TOTP ni els codis de recuperació; tanca les sessions i les entrades a mig fer i anul·la la credencial temporal anterior |
| RN-M01-61 | **Avís del restabliment (CA-08.4).** El registre separa el restabliment i l'avís, sense secrets; un avís a la cua no es presenta mai com a lliurat. Sense correu de notificació, el restabliment es pot fer: la pantalla ho adverteix abans («Aquest compte no té correu de notificació. El restabliment es pot fer, però no se li podrà enviar l'avís.») i ho diu després («Restabliment completat. No s'ha pogut enviar l'avís perquè el compte no té correu de notificació. Avisa la persona afectada per una altra via.»); el registre guarda l'avís com a no enviat, «sense adreça», i no s'avisa ningú més. No resol Q-03 ni permet enviar la credencial per correu (RN-17) |

**Criteris d'acceptació**
- **CA-M01-48** Donat qualsevol adreça (compte personal actiu, pendent, desactivat, d'administrador, inexistent o limitada), quan es demana recuperar la contrasenya, llavors la resposta és la mateixa i només un compte personal actiu rep l'enllaç.
- **CA-M01-49** Donat 3 correus enviats en una hora a una adreça per a una finalitat, quan se'n demana un altre, llavors no s'envia res i la resposta no canvia; amb peticions simultànies tampoc no se n'envien més de 3. El mateix amb 6 en 24 hores.
- **CA-M01-50** Donat 10 peticions acceptades d'un origen en 15 minuts, barrejant recuperació i reenviament, quan en fa una altra, llavors no s'envia res; les limitades per origen no allarguen el límit, que s'acaba 15 minuts després de la desena; les limitades per destinatari compten per a l'origen, de manera que deu peticions per a una adreça amb compte actiu limiten l'origen igual que deu per a una adreça sense compte ([066](decisions/066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md)); amb peticions simultànies no se n'accepten més de 10; i l'entrada des d'aquest origen i el comptador de V-01 no canvien.
- **CA-M01-51** Donat un compte pendent, quan s'escriu la contrasenya correcta, llavors s'ofereix el reenviament; quan han passat 10 minuts o el compte ja no és pendent, no s'envia res; dins dels 10 minuts, cada reenviament passa pels límits de RN-M01-58 ([066](decisions/066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md)); i aquest estat no obre cap pàgina que demani sessió.
- **CA-M01-52** Donat dos enllaços vigents de la mateixa operació, quan se'n fa servir un, llavors l'altre ja no serveix; si se'n fan servir dos alhora, només un completa l'operació.
- **CA-M01-53** Donat un restabliment per un altre administrador, quan el codi TOTP de qui el fa falta, és incorrecte o ja s'ha acceptat abans, llavors no es restableix res, l'intent compta per a V-01 i queda al registre; amb un codi nou i el motiu, es restableix.
- **CA-M01-54** Donat un restabliment de la contrasenya o del TOTP sense motiu, quan es confirma, llavors es rebutja.
- **CA-M01-55** Donat un compte sense correu de notificació, quan es restableix, llavors la pantalla mostra l'advertiment abans i el missatge després, el registre té el restabliment i l'avís «no enviat, sense adreça», i no surt cap correu; amb correu, el registre diu «a la cua» i la pantalla no diu que s'hagi lliurat.

**Tasques.** La feina és de la T-M01-05 ([lectura de les tasques substituïdes](#ajustos-060-lectura)).

---

<a id="M01-addenda-066"></a>
## M01 — Addenda de la [066](decisions/066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md): revisió de la T-M01-05

Aprovada el 04/11/2026, excepte la T-M01-39, que és una **proposta**. Canvia el text de RN-M01-58, RN-M01-59, CA-M01-50 i CA-M01-51 (a l'[addenda de la 065](#M01-addenda-065)): el reenviament de la verificació ja no és d'un sol ús, i una petició limitada per destinatari compta per al límit d'origen. Quines parts de les decisions de disseny 030 a 034 valen després de la 046 per a la T-M01-38 és a la [066](decisions/066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md).

**Tasques**
| # | Tasca | Esforç | Fitxers afectats | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M01-38 | Plantilla base, fulls d'estil i wireframes de les pantalles de comptes: entrades personal i d'administració, codi TOTP, alta del TOTP i codis de recuperació, contrasenya oblidada, contrasenya nova, verificació i reenviament, seguretat del compte, canvi de la credencial temporal, llista de comptes i restabliment (amb correu i sense). `tokens.css` passa a `static/css/` (una sola còpia), les fonts s'allotgen al servidor i el JavaScript del selector de tema va en un fitxer propi | M | `templates/base.html`, `static/css/`, `static/fonts/`, `static/js/`, `design/wireframes/` | T-M01-02, T-M01-05 | Wireframes revisats, amb els requisits de seguretat i privacitat de cada flux; contrast comprovat als dos temes; teclat i focus; amplada de 320 px; camps amb lletra de 16 px com a mínim; prova que cap plantilla carrega recursos externs; B8 bàsica. No tanca les pendents de la T-M01-02, que continuen a la T-M01-28 |
| T-M01-39 | **Proposta, no aprovada** ([P-53](decisions/pendents.md)). Igualar la feina de la petició de «He oblidat la contrasenya» amb una cua, en tres parts: (a) mesura abans i després; (b) implementació; (c) decisió de si és condició del nivell 1. Detall a sota | M | `apps/accounts/email_links.py`, `limits.py`, `models.py`, `tasks.py`, migració; programa de mesura fora del CI | Aprovació de la proposta pel responsable del projecte; T-M01-05 | (a) mesures documentades; (b) proves de sota en verd i mesura després; (c) decisió registrada |

**Ordre.** La T-M01-38 es fa abans de qualsevol pantalla nova del 01: la T-M01-07b i de la T-M01-13 a la T-M01-22 en depenen ([lectura de les tasques substituïdes](#ajustos-060-lectura)). Com que depèn de la T-M01-05, primer s'ha de tancar aquesta.

### T-M01-39 en detall (proposta)

**Estat:** proposta. Cap valor d'aquesta secció no és una regla vigent (tampoc el retard màxim de 5 minuts): tots són [A validar]. No es pot començar cap part, tampoc la (a), sense l'aprovació del responsable del projecte ([P-53](decisions/pendents.md)). El codi actual no fa servir cap cua per a «He oblidat la contrasenya»: la petició fa tota la feina en el moment.

**(a) Mesura abans i després.** No depèn de cap canvi de codi.
- Un programa de mesura fora del CI, contra una base de dades de proves (mai la de desenvolupament), a la mateixa màquina connectada a la corrent. Es documenten el commit, les versions de Python i PostgreSQL, les files de les taules implicades, l'estat del worker, els altres processos i la data i l'hora.
- Casos: dues adreces inexistents (la diferència entre totes dues dona el soroll), compte personal actiu, actiu limitat per destinatari, pendent, desactivat i d'administrador.
- Intercalats: blocs amb un cas de cada en ordre aleatori, amb la llavor documentada; 50 blocs d'escalfament descartats i 500 de mesurats. Cada petició amb una IP diferent i un compte actiu nou a cada bloc, perquè els límits no interfereixin.
- Dues execucions: amb el worker aturat i en marxa.
- Resultat per cas: n, mediana, p10, p90, p99 i mitjana, i diferència de medianes respecte a la primera adreça inexistent amb interval de confiança del 95 % (bootstrap).
- **Abans del canvi, el programa ha de reproduir la diferència actual.** Referència: 03/11/2026, en local, 500 per cas, amb condicions no documentades del tot; mediana de 3,9 ms per a una adreça inexistent i de 10,5 ms per a un compte actiu amb correu enviat. Si no la reprodueix, no serveix per avaluar el canvi.
- Després del canvi, cada diferència hauria de quedar dins del soroll entre les dues adreces inexistents, amb p10–p90 solapats. És evidència útil, no prova absoluta: amb més mostres es poden detectar diferències més petites.
- Es repeteix a l'entorn de proves, darrere del proxy amb HTTPS, abans de la decisió (c).

**(b) Implementació** (només si s'aprova). Abast: només «He oblidat la contrasenya», que és pública. El reenviament no hi entra: s'hi arriba amb la contrasenya correcta.
- **A la petició, la mateixa feina per a qualsevol adreça:**
  - validar el format;
  - bloqueig i límit per origen (si està limitat: la mateixa resposta, cap fila i cap tasca);
  - una fila amb l'hora, la IP, la finalitat, l'estat «pendent» i l'**empremta** de l'adreça escrita (`limits.recipient_key`, la mateixa d'ara);
  - una tasca a la cua amb **només l'identificador de la fila**;
  - la mateixa resposta.

  No es busca el compte.
- **Què es desa, amb compte o sense:** la mateixa fila.
  - No es desa cap adreça, ni en clar ni xifrada. La tasca troba el compte per l'empremta, amb una columna indexada nova al compte personal: l'empremta del `login`, que es recalcula quan canvia.
  - No hi intervé la clau global de xifratge.
  - L'empremta depèn de `SECRET_KEY`. Si es canvia, cal una ordre que recalculi la columna, i es perden els límits per destinatari de les últimes 24 hores, com avui.
- **La tasca:**
  - Bloqueja la fila sense esperar si ja la té un altre procés (`skip_locked`). Si no és «pendent», no fa res.
  - Si té més del retard màxim, la marca «caducada», buida l'empremta i no envia res.
  - Si no:
    - busca el compte personal per l'empremta;
    - bloqueja el destinatari i la fila del compte;
    - torna a comprovar que és actiu;
    - aplica el límit per destinatari.
  - Si queda limitada, ho registra, i **la fila es queda i compta per a l'origen** (RN-M01-58, 066).
  - Si no, posa el correu a la cua, desa l'empremta com a destinatari i marca la fila «enviada», tot en una sola transacció.
  - Si no s'envia, l'empremta es buida.
- **El comptatge no depèn de l'existència del compte.** La fila es crea a la petició per a tota petició acceptada i la tasca no l'esborra mai. Prova obligatòria: la de CA-M01-50 amb compte actiu i sense, abans i després d'executar la tasca.
- **Reintents i concurrència:**
  - Un error desfà la transacció i la cua ho reintenta: 3 intents, en menys d'un minut. Mai no hi ha dos correus per una fila.
  - Es mantenen els bloquejos per origen (a la petició) i per destinatari (a la tasca).
  - L'enllaç es genera en executar-se la tasca, i la seva hora de validesa compta des de l'enviament.
- **Retard màxim: 5 minuts** [A validar].
  - Per què no més: l'enllaç caduca en una hora, el worker normalment respon en segons i els reintents acaben en menys d'un minut. Passats 5 minuts, la persona probablement ja l'ha tornat a demanar o ha marxat, i un correu tardà es pot creuar amb el següent.
  - Per què no menys: un redesplegament normal atura el worker un o dos minuts [A verificar a l'entorn de proves]; amb 1 o 2 minuts es perdrien correus legítims.
- **Què veu l'usuari:** sempre el mateix missatge, perquè no pot dir res més sense revelar si el compte existeix. S'hi afegeix una frase [A validar]: «Si d'aquí a 5 minuts no t'ha arribat, mira el correu brossa i torna-ho a demanar.» Si la cua s'atura, la pantalla no canvia i no arriba res; tornar-ho a demanar compta per als límits.
- **Monitoratge:**
  - Una adreça de comprovació, declarada pública i sense cap dada, que respon amb error si la petició pendent més antiga, o el correu pendent més antic, té més de 2 minuts, o si el worker no dona senyals de vida.
  - UptimeRobot la vigila i avisa per correu ([011](decisions/011-monitoratge-i-errors.md)). Qui rep l'avís és Q-26 [A validar].
  - Les files caducades es compten als registres de l'aplicació, sense dades personals (E1).
- **Minimització i retenció:**
  - La IP només cal per al límit per origen (15 minuts més 15 de bloqueig), i es buida als 30 minuts.
  - L'empremta de les peticions no enviades es buida en processar-les o en caducar. La de les enviades es queda 24 hores per als límits per destinatari, com ara.
  - La purga passa de diària a cada 5 minuts.
  - No canvien la IP del registre d'activitat ni la de la línia de registre de les limitades, que tenen la seva pròpia retenció.
  - Una còpia de seguretat ([006](decisions/006-copies-de-seguretat.md)) pot contenir aquestes files dins d'aquestes finestres.

**(c) Decisió del nivell 1.** No és condició del nivell 1 mentre no es vegi la mesura. Amb la part (a) feta abans i després, i repetida darrere del proxy, el responsable del projecte decideix si cal per al nivell 1 ([P-53](decisions/pendents.md)).

---

<a id="M04"></a>
# Mòdul 04 — Tresoreria, part mínima

**Estat: aprovat** pel responsable del projecte el 27/10/2026 ([M04-14](#M04-14-aprovar)). Ampliat per la [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md) amb una [addenda](#M04-addenda-050) (T-M04-20), precisada per la [053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md) ([addenda](#M04-addenda-053)), sense canviar cap altra regla. Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M04-addenda-059)).

**Fonts integrades:** la [spec 04](arxiu/spec-04-tresoreria-v2-2026-10-27.md) v2 (aprovada amb canvis el 27/10/2026), les decisions [013](decisions/013-imputacio-comissions.md), [027](decisions/027-estructura-basica-de-carrec-i-pagament.md), [042](decisions/042-proveidors-substituits-pel-requisit-ue.md) a [045](decisions/045-correccio-transferencia-conciliada-per-error.md), l'arquitectura §4 i §9.1 i la [spec 00](../specs/00-base-comuna/spec.md) (RN-60 a RN-76, HU-21). La spec 04 v2 és a l'arxiu des de l'aprovació d'aquesta secció ([047](decisions/047-planning-font-unica-de-l-especificacio.md)).

**Identificadors.** Es mantenen els de la spec 04 (HU-T, CA-T, RN-T, LT, VT, QT) perquè ja els citen la 045 i `pendents.md`. Els nous continuen la numeració (RN-T24, CA-T16…). Els requisits d'experiència de pagament de l'annex D de la spec 04 passen al [M05b](#M05b-5-processos).

<a id="M04-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Que el tresorer sàpiga en tot moment quant hi ha a cada compte, de quin departament és cada euro, què ha arribat al banc i que cap moviment s'ha modificat ni esborrat. És la base dels pagaments (05a i 05b) i del marge (09). |
| **Processos que cobreix** | P-M04-A Cobrament confirmat → ingrés · P-M04-B Devolució o retorn · P-M04-C Anul·lar un moviment · P-M04-D Traspàs i arqueig · P-M04-E Conciliar l'extracte · P-M04-F Liquidació del proveïdor o de la remesa · P-M04-G Exportar per a la gestoria |
| **Tasques** | 21 (T-M04-01 a T-M04-21); la T-M04-20 l'afegeix la 050 (amb la 053) i la T-M04-21, la 059 |
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


<a id="M04-addenda-050"></a>
## M04 — Addenda de la [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md): despeses, altres ingressos, anul·lació i període tancat

Aprovada el 27/10/2026 perquè el [09](#M09) pugui registrar els seus moviments sense escriure als models de la 04. **No canvia cap regla existent del M04** ni cap fila aprovada de les seccions anteriors.

**Entitats.** `Movement.kind` admet dos valors nous: `expense` (sortida amb factura, la crea el 09) i `other_income` (entrada que no és un càrrec: ajuts, patrocinis, donatius). Tots dos porten departament obligatori (com RN-T05) i, opcionalment, centre de cost. L'activador «només INSERT» no canvia.

**Regles noves** (no en substitueixen cap)
| ID | Regla |
|---|---|
| RN-T26 | Moviments `expense` i `other_income`: els crea només el 09 amb els serveis d'aquesta addenda; són immutables, amb departament, conciliables i al registre d'activitat com la resta (RN-T05, RN-T07, RN-T13) |
| RN-T27 | `treasury.reverse` crea el contramoviment de RN-T07; motiu i usuari obligatoris; queda al registre d'activitat. Un moviment només s'anul·la una vegada (la restricció de `reverses` ja ho garanteix) |
| RN-T28 | **Bloqueig de període tancat, només per als moviments nous:** abans de crear qualsevol moviment (també un contramoviment), la 04 consulta els bloquejos registrats i rebutja la data de valor dins un període tancat (`PeriodClosed`). Els moviments que ja existeixen no canvien mai |
| RN-T29 | **Corregir un període tancat** = anul·lació i moviment nou, tots dos amb data de valor dins el període obert. El moviment original es queda al període tancat |

**Serveis nous**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `treasury.record_expense(account, amount_cents, value_date, department, cost_centre, concept, actor)` | — | moviment `expense` | `PeriodClosed`, `InvalidDepartment` | 09 |
| `treasury.record_other_income(account, amount_cents, value_date, department, cost_centre, concept, actor)` | — | moviment `other_income` | `PeriodClosed`, `InvalidDepartment` | 09 |
| `treasury.reverse(movement, reason, actor)` | moviment, motiu, usuari | contramoviment | `AlreadyReversed`, `PeriodClosed` (si la data de valor de l'anul·lació és en un període tancat) | 09; la pantalla de P-M04-C |
| `treasury.register_movement_guard(guard)` | funció `guard(value_date) → None o error` | — | — | 09 (bloqueig de període tancat) |

**Criteris d'acceptació**
- **CA-T18** Donat un moviment `expense` creat, quan s'intenta modificar o esborrar (també amb una consulta directa), llavors es rebutja.
- **CA-T19** Donat un període tancat fins al dia 31 i un moviment d'aquell període, quan el 09 en fa l'anul·lació amb data de valor del dia 31, llavors es rebutja; amb data del dia 1 del període obert, s'accepta i el moviment original no canvia.
- **CA-T20** Donat una anul·lació sense motiu, quan es demana, llavors es rebutja; amb motiu, el registre guarda el motiu i l'usuari.
- **CA-T21** Donat cap bloqueig registrat, quan es crea un moviment, llavors la 04 funciona exactament com abans (les proves del M04 continuen en verd).

**Tasca**
| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M04-20 | Addenda [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md) i [053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md): tipus `expense` i `other_income`, `record_expense`, `record_other_income`, `reverse`, `register_movement_guard`; camp `original_value_date` i bloqueig només per als moviments del 09 (els d'origen extern entren al període obert) | M | `apps/treasury/`, migració | T-M04-19 | CA-T18 a CA-T25; proves del M04 en verd |

<a id="M04-addenda-053"></a>
## M04 — Addenda de la [053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md): moviments d'origen extern i període tancat

Aprovada el 27/10/2026. Precisa l'abast de RN-T28 de l'[addenda de la 050](#M04-addenda-050); **no canvia cap altra regla** del M04. La feina és a la mateixa tasca T-M04-20.

**Entitats.** Camp nou `original_value_date` (data, null) a `Movement`: la data de valor real d'un moviment d'origen extern que ha entrat al període obert. Buit en tots els altres. Com la resta del moviment, no es modifica mai.

**Regles noves** (no en substitueixen cap altra)
| ID | Regla |
|---|---|
| RN-T30 | **Abast del bloqueig (precisa RN-T28):** el rebuig per període tancat (`PeriodClosed`) s'aplica només als moviments que crea el 09 (`expense` i `other_income`) i a les **anul·lacions manuals** (les que demana una persona amb `treasury.reverse`, des del 09 o des de la pantalla de P-M04-C) |
| RN-T31 | **Moviments d'origen extern:** tots els altres (els de `record_income`, `record_fee`, `record_refund`, `record_return` i `record_settlement`, els de la conciliació, els traspassos i els arqueigs) **no es rebutgen mai**. Si la data de valor és dins un període tancat, la data de valor passa a ser el primer dia del període obert i la real es guarda a `original_value_date`. Queda al registre d'activitat |
| RN-T32 | La conciliació de l'extracte compara la data de la línia amb `original_value_date` quan és plena; si no, amb la data de valor |
| RN-T33 | **Precisió del punt d'extensió:** la funció registrada amb `treasury.register_movement_guard` torna la data fins a la qual el període és tancat (o res). La 04 aplica RN-T30 o RN-T31 segons l'origen. La 04 continua sense dependre del 09 |

**Criteris d'acceptació**
- **CA-T22** Donat un període tancat fins al dia 31, quan arriba un pagament confirmat del 05b amb data del dia 30, llavors no es rebutja: es crea l'ingrés amb data de valor del dia 1 del període obert i `original_value_date` del dia 30, i el 05b el dona per registrat.
- **CA-T23** Donat el mateix període tancat, quan es registren una comissió del banc, un retorn i una liquidació amb data dins el període, llavors cap no es rebutja i tots tres porten `original_value_date`; quan el 09 registra una despesa amb aquella data, es rebutja (`PeriodClosed`).
- **CA-T24** Donat un ingrés que ha entrat al període obert amb `original_value_date` del dia 30, quan s'importa la línia de l'extracte del dia 30, llavors la conciliació els casa.
- **CA-T25** Donat cap període tancat, quan es crea qualsevol moviment, llavors `original_value_date` queda buit i la data de valor no canvia.

<a id="M04-addenda-059"></a>
## M04 — Addenda de la [059](decisions/059-rols-i-permisos-editables.md): permisos editables i configuració inicial

Aprovada el 30/10/2026. **No canvia cap regla** del M04. La taula de [M04-4](#M04-4-rols) passa a ser la **configuració inicial** dels permisos del mòdul, que l'administrador pot canviar des de l'app ([peça comuna](#rols-i-permisos-059)). Els canvis respecte de la taula, cel·la per cel·la, són a la [matriu inicial](#rols-i-permisos-059-matriu). Les cel·les [A validar] prenen el supòsit per defecte del mòdul; si no n'hi ha, «—»; si l'acció es quedaria sense ningú, l'administrador.

**Què canvia:** res per al tresorer i l'administrador. La Junta no veu comptes ni saldos a l'inici, perquè T1 era [A validar]. Queda resolt S-M04-09: l'administrador manté els departaments i el tresorer concilia i desfà conciliacions.

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M04-21 | Declarar els permisos de la 04 al catàleg (T1 a T11) i comprovar-los a totes les vistes i serveis | XS | `apps/treasury/permissions.py` | T-RP-01 | Proves per cel·la de la 04 (CA-RP-13) |

<a id="M04-addenda-060"></a>
## M04 — Addenda de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): importació de l'extracte

Aprovada el 31/10/2026. **No canvia cap regla** del M04. La importació de l'extracte bancari (HU-21 de la 00), de la qual depèn la conciliació, té tasca pròpia: **T-M00-01** ([apèndix](#ajustos-060-peces-00)). La **T-M04-11** en depèn, a més del que ja deia. La T-M04-21 queda com a revisió final de la cobertura per cel·la.

---

<a id="M05a"></a>
# Mòdul 05a — Alta del mètode de pagament i mandats

**Estat: aprovat** pel responsable del projecte el 27/10/2026 ([M05a-14](#M05a-14-aprovar)). Els bloquejos que depenen del banc i de PaynoPain es mantenen [A verificar]. Ampliat per la [055](decisions/055-ajustos-configurables-i-addendes.md) amb una [addenda](#M05a-addenda-055) de pantalla d'ajustos (T-M05a-22), sense canviar cap regla. Ampliat també per la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) amb una [addenda](#M05a-addenda-058) (T-M05a-23 i T-M05a-24), sense canviar cap regla. Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M05a-addenda-059)).

**Fonts:** decisions [017](decisions/017-pagaments-metodes-i-domiciliacions.md), [022](decisions/022-mandats-sepa-escenari-base-b.md), [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), [025](decisions/025-dos-nivells-de-produccio.md), [042](decisions/042-proveidors-substituits-pel-requisit-ue.md), [043](decisions/043-proveidor-de-pagaments-dins-la-ue.md), [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md); arquitectura §4.2, §4.3 i §4.9 (on diu Stripe, s'aplica la 042); [`integracio-paylands.md`](integracio-paylands.md); checklist (C9, G3 i els punts «N1»).

**Proveïdor.** Tot el que toca el proveïdor de pagaments passa per l'**adaptador** ([M05a-8](#M05a-8-serveis)). El proveïdor concret no està triat (P-44, P-45): tot el que en depèn porta **[A verificar]**. La domiciliació es planifica amb la **044** (IBAN i mandat xifrats a la plataforma), **acceptada com a camí per defecte**: si el banc custodia els mandats o es tria un proveïdor amb domiciliació (alternatives 1 i 2 de la 044), canvia només la custòdia ([M05a-13](#M05a-13-riscos)).

<a id="M05a-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Que cada soci tingui un mètode per pagar la quota abans de la primera remesa de la plataforma: recollir mandats SEPA nous en producció al nivell 1 (dades reals, cap cobrament), amb l'IBAN xifrat (044) i el proveïdor de targeta darrere de l'adaptador. |
| **Processos que cobreix** | P-M05a-A Triar el mètode de pagament · P-M05a-B Signar el mandat · P-M05a-C Canviar l'IBAN o revocar · P-M05a-D Guardar una targeta (condicional) · P-M05a-E Campanya de mandats · P-M05a-F Pas al nivell 1 · P-M05a-G Rotació de la clau |
| **Tasques** | 26 (T-M05a-01 a T-M05a-26); la T-M05a-22 l'afegeix la 055, la T-M05a-23 i la T-M05a-24, la 058, la T-M05a-25, la 059, i la T-M05a-26, la 060 |
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

<a id="M05a-addenda-055"></a>
## M05a — Addenda de la [055](decisions/055-ajustos-configurables-i-addendes.md): pantalla d'ajustos

Aprovada el 28/10/2026. **No canvia cap regla** del M05a. La feina és a la tasca T-M05a-22.

| VC | Clau | Valor inicial | Rang | Qui el canvia |
|---|---|---|---|---|
| VC-11 | `payments.mandate_campaign_reminder_days` | 7 i 14 dies [A validar: tresorer, RN-M05a-14] | 1 a 60 | Tresorer |

| ID | Regla |
|---|---|
| RN-M05a-18 | Els recordatoris de la campanya de mandats (RN-M05a-14) llegeixen els dies dels ajustos en el moment d'enviar. El darrer recordatori, quan el tresorer fixa la remesa, no canvia. Cap recordatori a qui ja ha triat |

- **CA-M05a-18** Donat els dies canviats a 5 i 10, quan corre la campanya, llavors els recordatoris surten als 5 i als 10 dies de la invitació; el canvi queda al registre amb el valor anterior; un valor de 0 o de 61 es rebutja.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M05a-22 | Pantalla d'ajustos del 05a (VC-11) i lectura des de la campanya ([055](decisions/055-ajustos-configurables-i-addendes.md)) | S | `apps/payments/settings.py`, vistes | T-AJ-02, T-M05a-13 | CA-M05a-18 |


<a id="M05a-addenda-058"></a>
## M05a — Addenda de la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md): targeta guardada recomanada i renovació de la quota

Aprovada el 29/10/2026. **No canvia cap regla** del M05a: canvia només quin mètode es **recomana** per defecte als socis nous (punt 15 de la 058, que substitueix la 017 en aquest punt). Els mètodes disponibles de RN-M05a-01 no canvien.

| ID | Regla |
|---|---|
| RN-M05a-19 | **Mètode recomanat als socis nous:** la targeta guardada, si el proveïdor permet guardar-la (`tokenization_enabled`, VC-14) [A verificar: PaynoPain, P-45 punt 6]. Si no ho permet, es continua recomanant la domiciliació. La domiciliació continua disponible i la transferència es permet sense obligar-hi. Els socis que ja tenen un mètode no reben cap canvi |
| RN-M05a-20 | **Caducitat de la targeta guardada:** el soci rep un avís abans que caduqui la targeta, per correu i a l'app (sense push), amb l'enllaç per guardar-ne una de nova. Quants dies abans: ajust `payments.card_expiry_notice_days`, valor inicial [A validar: tresorer] |
| RN-M05a-21 | **Renovació de la quota:** la quota es renova cada any. La baixa s'ha de demanar abans d'una data límit i el soci rep un avís previ del cobrament, sigui quin sigui el mètode. La data límit i el termini de l'avís: [A validar: junta i gestoria]. Mentre no es fixin, no s'activa cap renovació automàtica en producció |
| RN-M05a-22 | **Invitació a pagar de manera automàtica:** el tresorer pot enviar als socis que paguen per transferència una invitació opcional a passar a targeta guardada o domiciliació, amb la campanya (RN-M05a-14). No és obligatori respondre-hi i no canvia el mètode de ningú |

- **CA-M05a-19** Donat `tokenization_enabled` actiu, quan un soci nou tria mètode, llavors la targeta guardada surt com a recomanada i la domiciliació i la transferència es poden triar; amb `tokenization_enabled` desactivat, surt recomanada la domiciliació.
- **CA-M05a-20** Donat una targeta guardada que caduca d'aquí a menys dies que `payments.card_expiry_notice_days`, quan corre la tasca diària, llavors el soci rep un sol avís.
- **CA-M05a-21** Donat un soci que paga per transferència, quan el tresorer envia la invitació, llavors la rep una sola vegada i el seu mètode no canvia fins que ell en triï un altre.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M05a-23 | Mètode recomanat segons el proveïdor, avís de caducitat de la targeta i invitació als qui paguen per transferència ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md)) | S | `apps/payments/preferences.py`, `campaigns.py`, tasques de la cua | T-M05a-11, T-M05a-12, T-M05a-13 | CA-M05a-19 a 21 |
| T-M05a-24 | Renovació anual de la quota, data límit de baixa i avís previ del cobrament (bloquejada fins que es fixin la data i el termini) | M | `apps/payments/renewals.py` | T-M01-18, T-M05a-23; RN-M05a-21 validada | Proves amb dates inventades |

<a id="M05a-addenda-059"></a>
## M05a — Addenda de la [059](decisions/059-rols-i-permisos-editables.md): permisos editables i configuració inicial

Aprovada el 30/10/2026. **No canvia cap regla** del M05a. La taula de [M05a-4](#M05a-4-rols) passa a ser la **configuració inicial** dels permisos del mòdul, que l'administrador pot canviar des de l'app ([peça comuna](#rols-i-permisos-059)). Els canvis respecte de la taula, cel·la per cel·la, són a la [matriu inicial](#rols-i-permisos-059-matriu). Les cel·les [A validar] prenen el supòsit per defecte del mòdul; si no n'hi ha, «—»; si l'acció es quedaria sense ningú, l'administrador.

**Què canvia:** res per al tresorer i l'administrador. La secretaria veu només «té mètode: sí o no» (A4), perquè queda resolt S-M05a-13. A9 (IBAN complet, ningú) és una regla protegida ([044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)).

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M05a-25 | Declarar els permisos del 05a al catàleg (A4 a A8; A9 protegit) i comprovar-los a totes les vistes i serveis | XS | `apps/payments/permissions.py` | T-RP-01 | Proves per cel·la del 05a (CA-RP-13) |

<a id="M05a-addenda-060"></a>
## M05a — Addenda de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): estat de la targeta guardada

Aprovada el 31/10/2026. **No canvia cap regla** del M05a: completa RN-M05a-20 per als casos en què la targeta ja no es pot fer servir.

**Entitats.** `SavedCard.status` admet un valor nou, `declined` (denegada de manera definitiva, [RN-M05b-28](#M05b-addenda-060)). Valor inicial de `payments.card_expiry_notice_days` (VC-48): **30 dies** [A validar: tresorer].

| ID | Regla |
|---|---|
| RN-M05a-23 | Si la caducitat coneguda de la targeta (`expiry_month`, `expiry_year`) és anterior al dia d'un cobrament, la targeta passa a `expired` i no es fa servir. Si el proveïdor no retorna la caducitat, no hi ha avís previ (RN-M05a-20 no s'aplica) i és la denegació del cobrament ([RN-M05b-28](#M05b-addenda-060)) la que ho detecta. Una targeta `expired` o `declined` no torna a ser activa: el soci n'ha de guardar una de nova |

- **CA-M05a-22** Donat una targeta guardada que caduca el 31/03 i una quota que es cobra el 15/04, quan corre la tasca diària, llavors la targeta és `expired`, no es fa cap intent amb ella i el soci té l'enllaç per guardar-ne una de nova.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M05a-26 | Estats `expired` per caducitat coneguda i `declined`; valor inicial de VC-48 | S | `apps/payments/cards.py`, migració | T-M05a-12, T-M05a-23 | CA-M05a-22 |

---

<a id="M05b"></a>
# Mòdul 05b — Cobraments: targeta, Bizum, domiciliació i transferència

**Estat: aprovat** pel responsable del projecte el 27/10/2026 ([M05b-14](#M05b-14-aprovar)). Els bloquejos que depenen del banc i de PaynoPain es mantenen [A verificar]. Ampliat per la [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md) amb l'esdeveniment general «càrrec pagat» (T-M05b-21), i per la [055](decisions/055-ajustos-configurables-i-addendes.md) amb una [addenda](#M05b-addenda-055) de pantalla d'ajustos (T-M05b-22), sense canviar cap regla. Ampliat també per la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) amb una [addenda](#M05b-addenda-058) (T-M05b-23 i T-M05b-24), sense canviar cap regla. Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M05b-addenda-059)).

**Fonts:** decisions [013](decisions/013-imputacio-comissions.md), [017](decisions/017-pagaments-metodes-i-domiciliacions.md), [021](decisions/021-persones-no-socies-com-a-convidades.md), [022](decisions/022-mandats-sepa-escenari-base-b.md), [025](decisions/025-dos-nivells-de-produccio.md), [040](decisions/040-impagat-es-marca-a-ma.md), [042](decisions/042-proveidors-substituits-pel-requisit-ue.md) a [045](decisions/045-correccio-transferencia-conciliada-per-error.md); annex D de la [spec 04](arxiu/spec-04-tresoreria-v2-2026-10-27.md) (experiència de pagament, que passa aquí); arquitectura §4.2 a §4.8; [`integracio-paylands.md`](integracio-paylands.md); spec 00 (RN-30 a RN-33, RN-60 a RN-73).

**Proveïdor.** Targeta i Bizum passen per l'**adaptador** del [05a](#M05a-8-serveis). Tot el que depèn del proveïdor porta **[A verificar]** (P-44, P-45). La domiciliació es fa amb **remeses pain.008** que la plataforma genera i el tresorer puja al banc (043 (e), 044): l'app no mou mai diners sola.

<a id="M05b-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Cobrar dins l'app quotes, inscripcions i llicències amb targeta, Bizum, domiciliació i transferència, sense donar mai res per pagat pel navegador i quadrant-ho tot amb la tresoreria. És el criteri per deixar Cluber (nivell 2). |
| **Processos que cobreix** | P-M05b-A Targeta · P-M05b-B Bizum · P-M05b-C Transferència · P-M05b-D Notificació del proveïdor · P-M05b-E Remesa de quotes · P-M05b-F Retornat, reintent i alternativa · P-M05b-G Devolució · P-M05b-H Liquidació del proveïdor · P-M05b-I Pas al nivell 2 |
| **Tasques** | 27 (T-M05b-01 a T-M05b-27); la T-M05b-21 l'afegeix la 049, la T-M05b-22, la 055, la T-M05b-23 i la T-M05b-24, la 058, la T-M05b-25, la 059, i la T-M05b-26 i la T-M05b-27, la 060 (la T-M05b-23 queda congelada) |
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
| Esdeveniment `charge.paid` ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) | s'emet dins la mateixa transacció en què el càrrec passa a «pagat», per qualsevol camí (notificació, conciliació de transferència o de remesa): càrrec, tipus, mòdul d'origen, activitat, import | lliurament a la cua, com a mínim una vegada; idempotent per (esdeveniment, subscriptor); emissió i lliuraments al registre | — | Qualsevol mòdul que s'hi subscrigui amb `events.subscribe` (02; més endavant 03, 06 i 09). La crida directa a `members.on_fee_paid` es manté |

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
| T-M05b-21 | Esdeveniment `charge.paid`: taula d'esdeveniments pendents a la mateixa transacció, subscripcions, lliurament a la cua i registre de lliuraments únic per subscriptor (049) | M | `apps/core/events.py`, `apps/core/charges.py` | T-M05b-05, T-M04-12 | Prova que un esdeveniment repetit no torna a executar el subscriptor i que la conciliació també l'emet |

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

<a id="M05b-addenda-055"></a>
## M05b — Addenda de la [055](decisions/055-ajustos-configurables-i-addendes.md): pantalla d'ajustos

Aprovada el 28/10/2026. **No canvia cap valor inicial ni cap regla** del M05b: dona pantalla als `PaymentSettings` que ja existeixen i als dos valors configurables de RN-M05b-16 i RN-M05b-18. La feina és a la tasca T-M05b-22.

| VC | Valor | Valor inicial | Rang | Qui el canvia | Data d'entrada en vigor |
|---|---|---|---|---|---|
| VC-16 | `transfer_reminder_days`; `prenotification_days`; `max_direct_debit_attempts` | 30; 14; 2 | 7 a 60; 14 a 30 (segons el text del mandat [A verificar: banc]); 1 a 3 | Tresorer | — |
| VC-17 | `bizum_ui_timeout_minutes`; `safety_net_age_minutes` | 15; 60 | 5 a 30; 30 a 240 | Administrador | — |
| VC-18 | `payments.return_fee_payer` (club o soci, RN-M05b-16); `members.card_valid_with_returned_fee` (RN-M05b-18) | El club; no vàlid | — | Administrador, per decisió de la junta | Sí, el de la comissió |

| ID | Regla |
|---|---|
| RN-M05b-24 | La pantalla edita els `PaymentSettings` amb els rangs de VC-16 i VC-17 i les mateixes comprovacions de la peça comuna (rol al servidor, rang, registre amb el valor anterior). Els valors que ja s'estan fent servir (una remesa amb l'avís previ enviat, un pagament de Bizum en curs) no canvien |
| RN-M05b-25 | Els dos valors de VC-18 viuen a la peça comuna d'ajustos. Canviar qui paga la comissió de retorn afecta diners: porta data d'entrada en vigor, s'aplica als retornats que arriben a partir d'aquella data i avisa el tresorer i la junta (RN-AJ-04) |

- **CA-M05b-26** Donat `prenotification_days` a 14, quan el tresorer el posa a 13 o a 31, llavors es rebutja; a 20, s'accepta, queda al registre i les remeses noves fan servir 20, però una remesa amb l'avís ja enviat no canvia.
- **CA-M05b-27** Donat un canvi de `payments.return_fee_payer` a «soci» amb data d'entrada en vigor, quan arriba un retornat abans d'aquella data, llavors la comissió la paga el club; quan arriba després, la paga el soci; el tresorer i la junta reben el correu amb el valor anterior i el nou.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M05b-22 | Pantalla d'ajustos del 05b (VC-16 a VC-18) sobre els `PaymentSettings` i la peça comuna ([055](decisions/055-ajustos-configurables-i-addendes.md)) | S | `apps/payments/views/settings.py` | T-AJ-02, T-M05b-05, T-M05b-12 | CA-M05b-26, 27 |


<a id="M05b-addenda-058"></a>
## M05b — Addenda de la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md): import extra del retorn i reintent de la targeta

Aprovada el 29/10/2026. **No canvia cap regla** del M05b. El valor de `payments.return_fee_payer` (VC-18, RN-M05b-25) continua sent «el club» fins que es validi el punt 11 de la 058.

| ID | Regla |
|---|---|
| RN-M05b-26 | **Import extra del retorn:** quan `payments.return_fee_payer` és «soci», al **segon intent** d'una quota retornada (RN-M05b-15) el soci paga, a més de la quota, un càrrec a part que cobreix la comissió de retorn de CaixaGuissona, departament «General / Quotes de socis». L'import és el que cobra el banc [A verificar: banc, S-M05b-05]. Canviar el valor a «soci» necessita la validació de la junta i del banc i cobertura als estatuts [A validar: junta i banc]; fins llavors no es cobra cap import extra |
| RN-M05b-27 | **Reintent de la targeta guardada:** si el cobrament d'una quota amb la targeta guardada falla, es reintenta; quants reintents i amb quin interval: [A validar: tresorer]. Si tots fallen, el soci rep l'alternativa de pagament (targeta nova, Bizum o transferència) |

- **CA-M05b-28** Donat `payments.return_fee_payer` a «club», quan es reintenta una quota retornada, llavors no es crea cap càrrec extra; amb «soci», es crea un càrrec a part amb l'import de la comissió, lligat a la quota.
- **CA-M05b-29** Donat un cobrament amb targeta guardada que falla, quan s'esgoten els reintents, llavors el soci rep l'alternativa de pagament i el càrrec continua pendent.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M05b-23 | Càrrec extra de la comissió de retorn al segon intent, condicionat a l'ajust ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md)) | S | `apps/payments/returns.py` | T-M05b-12, T-M05b-22 | CA-M05b-28 |
| T-M05b-24 | Reintent i alternativa del cobrament amb targeta guardada | S | `checkout.py`, tasques de la cua | T-M05b-15 | CA-M05b-29 |

<a id="M05b-addenda-059"></a>
## M05b — Addenda de la [059](decisions/059-rols-i-permisos-editables.md): permisos editables i configuració inicial

Aprovada el 30/10/2026. **No canvia cap regla** del M05b. La taula de [M05b-4](#M05b-4-rols) passa a ser la **configuració inicial** dels permisos del mòdul, que l'administrador pot canviar des de l'app ([peça comuna](#rols-i-permisos-059)). Els canvis respecte de la taula, cel·la per cel·la, són a la [matriu inicial](#rols-i-permisos-059-matriu). Les cel·les [A validar] prenen el supòsit per defecte del mòdul; si no n'hi ha, «—»; si l'acció es quedaria sense ningú, l'administrador.

**Què canvia:** les devolucions (B5) les fa només el tresorer (l'administrador era [A validar]). La secretaria reenvia l'alternativa de les quotes (B7), perquè queda resolt S-M05b-13. B3, pel fitxer amb IBAN, i B8, per l'autorització de la junta, són regles protegides.

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M05b-25 | Declarar els permisos del 05b al catàleg (B3 a B8; B3 i B8 protegits) i comprovar-los a totes les vistes i serveis | XS | `apps/payments/permissions.py` | T-RP-01 | Proves per cel·la del 05b (CA-RP-13) |

<a id="M05b-addenda-060"></a>
## M05b — Addenda de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): denegacions definitives, segon retorn i T-M05b-23 congelada

Aprovada el 31/10/2026. **No canvia cap regla** del M05b: limita el reintent de RN-M05b-27 i completa RN-M05b-15 per a l'últim intent.

| ID | Regla |
|---|---|
| RN-M05b-28 | **Denegació definitiva de la targeta guardada.** Els codis de denegació del proveïdor es classifiquen en **definitius** (caducada, perduda o robada, compte tancat, targeta no vàlida; codis concrets [A verificar: PaynoPain]) i **temporals** (la resta). Una denegació definitiva **no es reintenta mai** (RN-M05b-27 no s'hi aplica): la targeta passa a `expired` si el motiu és la caducitat, i a `declined` en els altres casos (RN-M05a-23). El soci rep de seguida l'alternativa de pagament i el càrrec continua pendent. Un codi desconegut es tracta com a temporal i surt a la llista «a revisar» del tresorer |
| RN-M05b-29 | **Caducitat coneguda abans del cobrament:** amb una targeta `expired` no es fa cap intent. El soci rep directament l'alternativa (RN-M05a-23) |
| RN-M05b-30 | **Segon retorn.** Quan torna el rebut de l'últim intent permès (`max_direct_debit_attempts`, RN-M05b-15), **la quota no entra en cap remesa més**: la selecció de la remesa l'exclou amb el motiu «intents esgotats». El sistema només proposa l'alternativa de pagament (pas 3 de P-M05b-F) i el tresorer en rep l'avís. L'impagat continua sent manual (040). Aquest motiu sol no canvia l'estat del mandat; el mandat només canvia per RN-M05b-15 |

**T-M05b-23 congelada.** No es construeix fins que la junta i el banc validin el punt 11 de la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md). En validar-lo, abans de construir-la, cal fixar:
- de quin tipus és el càrrec extra i com es cobra, perquè no és una quota i no pot anar a la remesa (RN-M05b-10);
- si porta IVA (09);
- si es cobra també quan el soci paga per l'alternativa en lloc del reintent.

Mentre no es validi, `payments.return_fee_payer` és «club» i no es crea cap càrrec extra (CA-M05b-28).

**Dependències.** La T-M05b-08 (pagaments de convidats) depèn de la **T-M00-02** ([apèndix](#ajustos-060-peces-00)).

- **CA-M05b-30** Donat un cobrament amb targeta guardada denegat amb un codi definitiu, quan arriba la notificació, llavors no es programa cap reintent, la targeta és `declined` (o `expired` si el motiu és la caducitat), el soci rep l'alternativa una sola vegada i el càrrec continua pendent.
- **CA-M05b-31** Donat una targeta `expired`, quan arriba el dia del cobrament, llavors no es crea cap intent amb la targeta i el soci rep l'alternativa.
- **CA-M05b-32** Donat una quota amb un retorn per fons insuficients que ja s'ha reintentat (intent 2 de 2), quan el segon rebut també torna, llavors la previsualització de la remesa següent l'exclou amb el motiu «intents esgotats», el tresorer veu la proposta d'alternativa i no es genera cap tercer rebut.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M05b-26 | Classificació de les denegacions (definitiva o temporal), cap reintent de les definitives i cap intent amb una targeta `expired` | S | `apps/payments/checkout.py`, `apps/payments/cards.py` | T-M05b-24, T-M05a-26 | CA-M05b-30, 31 |
| T-M05b-27 | Exclusió de la remesa quan s'esgoten els intents i proposta d'alternativa | S | `apps/payments/returns.py`, `remittances.py` | T-M05b-12 | CA-M05b-32 |

---

<a id="M02"></a>
# Mòdul 02 — Activitats (cursos i sortides)

**Estat: aprovat** pel responsable del projecte el 28/10/2026 ([M02-14](#M02-14-aprovar)), alhora que els 02, 03, 06 i 09. Ampliat per la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) amb una [addenda](#M02-addenda-058) (T-M02-29 a T-M02-32), sense canviar cap regla. Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M02-addenda-059)).

**Fonts:** document de funcionalitats (F §4 Cursos, §5 Sortides, processos 9.1, 9.17 i 9.18), mapa de la plataforma v8 (M02 Cursos i M03 Sortides), respostes del responsable del projecte del 20/10/2026 i del 22/10/2026 (catàlegs separats i editables, classes de reforç amb cost, subtipus de medi ambient ampliables, preus configurables amb nota obligatòria en canviar-los, duplicar com a plantilla), decisions [013](decisions/013-imputacio-comissions.md), [017](decisions/017-pagaments-metodes-i-domiciliacions.md), [021](decisions/021-persones-no-socies-com-a-convidades.md), [026](decisions/026-duplicar-activitats-al-modul-02.md), [027](decisions/027-estructura-basica-de-carrec-i-pagament.md), [035](decisions/035-dades-nomes-dins-ue.md), [041](decisions/041-web-installable-i-avisos-sense-push.md), [043](decisions/043-proveidor-de-pagaments-dins-la-ue.md) i [046](decisions/046-interficie-django-htmx-servida-des-del-vps.md); [spec 00](../specs/00-base-comuna/spec.md) (RN-30 a RN-33, RN-43, RN-60 a RN-73, V-02); seccions aprovades [M01](#M01), [M04](#M04) i [M05b](#M05b).

**Proveïdor de pagaments.** El 02 no parla mai amb el proveïdor: crea el càrrec d'inscripció (00) i el cobra amb els serveis del [05b](#M05b-8-serveis), que hi parla a través de l'adaptador. Inscripcions: targeta, Bizum o transferència, mai domiciliació (017; RN-69 de la 00).

<a id="M02-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Organitzar cursos i sortides de principi a fi en un sol lloc: catàlegs i preus, convocatòries i sortides (o duplicar-ne una d'anterior), inscripció i pagament dins l'app, places i llista d'espera, llista des del mòbil, avaluació, classes de reforç i certificat als cursos, i resultats ambientals i projectes a les sortides de medi ambient. Deixa cada activitat a punt perquè el 09 en calculi i en congeli el marge. |
| **Processos que cobreix** | P-M02-A Catàlegs i preus · P-M02-B Crear o duplicar una activitat · P-M02-C Publicar i inscriure's (soci, convidat i presencial) · P-M02-D Places, llista d'espera i cancel·lacions · P-M02-E El dia de l'activitat: llista i incidències · P-M02-F Avaluació, reforç i certificat · P-M02-G Resultats ambientals i projectes · P-M02-H Fi de l'activitat i comprovacions de tancament (F 9.1, 9.17 i 9.18) |
| **Tasques** | 36 (T-M02-01 a T-M02-36); de la T-M02-29 a la T-M02-32 les afegeix la 058, la T-M02-33, la 059, i de la T-M02-34 a la T-M02-36, la 060 |
| **Què el bloqueja** | Per construir: el 05b (cobrar inscripcions) i les dues peces de mòduls aprovats que aprova la [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md) (T-M01-30 i T-M05b-21). Per entrar en producció: el catàleg amb preus i la política de cancel·lació [A validar: junta]. La resta són supòsits configurables ([M02-13](#M02-13-riscos)) |
| **Què cal aprovar** | Aquesta secció i els supòsits S-M02-01 a S-M02-06, que fixen el comportament per defecte ([M02-14](#M02-14-aprovar)). Les dues peces de mòduls aprovats ja són aprovades (049) |

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
| 01 | `members.is_member(person, on=date)` per al preu de soci; **registre mínim de llicència** per comprovar si és vigent (`members.licence_record`, només lectura, [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) |
| 06 (quan existeixi) | `licences.current(person, on)` ([M06-8](#M06-8-serveis)), amb la categoria, la font única de la llicència ([052](decisions/052-llicencia-font-unica-al-06.md)); llicència d'un dia (RP-M02-01, condicional); categoria exigida (RP-M02-02) |
| 04 | Res directament: l'ingrés i les comissions de cada inscripció els crea el 05b amb l'activitat i el departament del càrrec (RN-T10) |
| 05b | `payments.start_payment`, `payments.payment_status`, rebut; devolucions fetes pel tresorer (`payments.refund`, B5); esdeveniment general `charge.paid` al qual el 02 se subscriu ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) |

**Peces de mòduls aprovats que el 02 necessita** (aprovades per la [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md), sense canviar cap regla d'aquells mòduls):
1. **01:** `members.licence_record(person)`, només lectura (T-M01-30).
2. **05b:** esdeveniment general `charge.paid`, emès dins la mateixa transacció que el canvi a «pagat» i lliurat a la cua, idempotent i amb registre (T-M05b-21). El 02 s'hi subscriu; el 05b no crida mai el 02.

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
- **Instructor:** només les sessions on fa classe i els alumnes inscrits a aquestes sessions. Dels alumnes veu nom i cognoms, titulació, si la llicència és vigent per a la data de la sessió (només sí o no: ni la data de venciment, ni el número federatiu, ni la categoria; igual que el [M06-4](#M06-4-rols)), l'assistència i les avaluacions. **No veu** document, adreça, correu, telèfon ni pagaments [A validar: junta, Q-01]. Fora de les seves sessions, «no trobat» i registre.
- **Responsable de cursos i sortides:** de la llicència dels participants de les seves activitats, només «vigent», «en tràmit» o «no» per a la data de l'activitat, sense dates ni categoria (RN-M06-22). L'instructor continua veient només «vigent sí o no».
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
- Subscripció a l'esdeveniment `charge.paid` (049); cap camp nou a la 00.

**Migracions:** reversibles; dades inicials (tipus de sortida, subtipus «Neteja») en una migració de dades; cap dada personal a les migracions.

### Valors configurables (pantalla d'ajustos, T-M02-28)
Valors de la [regla general](#regles), a la pantalla d'ajustos del mòdul sobre la [peça comuna](#valors-configurables-055) de la [055](decisions/055-ajustos-configurables-i-addendes.md): cada canvi es comprova al servidor (rol i rang), queda al registre amb el valor anterior i, si afecta diners, porta data d'entrada en vigor i avisa per correu el tresorer i la junta (RN-AJ-03 i RN-AJ-04). Els valors inicials són els supòsits que ja hi havia; les preguntes obertes continuen obertes.

| Clau de l'ajust | VC | Valor inicial | Rang vàlid | Qui el canvia | Data d'entrada en vigor |
|---|---|---|---|---|---|
| Preus del catàleg (`price_member_cents`, `price_non_member_cents`, `reinforcement_price_cents`): versions a `TrainingCataloguePrice` (`entry`, preus, `valid_from`, `changed_by`, `note`) | VC-20 | Els de la fitxa | ≥ 0 | Responsable de cursos i sortides (RN-M02-01) | Sí |
| Tipus i subtipus de sortida, projectes | VC-20 | «Neteja»; Sèniors i jornades obertes, desactivables | Noms únics | Responsable de cursos i sortides | — |
| `activities.default_payment_window_hours` | VC-21 | 72 | 24 a 240 | Tresorer | — |
| `activities.offer_accept_hours` | VC-22 | 48 | 12 a 168 | Responsable de cursos i sortides | — |
| `activities.reminder_days_before` | VC-23 | 2 | 0 a 14 (0 = el mateix dia) | Secretaria | — |
| `activities.default_requirements_mode` | VC-24 | `warn` (avís) | `warn`, `block` | Responsable de cursos i sortides, per decisió de la junta | — |
| `activities.marine_forecast_url` | VC-25 | La pàgina pública de previsió marítima del Meteocat | URL `https` | Administrador | — |

Es queda al codi: la numeració del certificat (VC-26).

<a id="M02-7-regles"></a>
## M02-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M02-01 | Cursos i especialitats són dos catàlegs separats; cadascun amb preus de soci i de no soci editables pel responsable sense tocar res més | F §4; resposta del 22/10/2026 |
| RN-M02-02 | Transicions de l'activitat: `draft → open → registration_closed → in_progress → done → closed`; `open → done` i `registration_closed → done` (sortides); qualsevol estat abans de `done` → `cancelled` amb motiu. `closed` només el fa el 09. Cap transició enrere excepte `registration_closed → open` (el responsable reobre inscripcions abans de l'inici) | F §4 i §5 |
| RN-M02-03 | Transicions de la inscripció: `pending_payment → confirmed / expired / cancelled`; `waitlisted → offered / cancelled / expired`; `offered → pending_payment / expired`; `confirmed → cancelled`. Una inscripció `confirmed` no torna a `pending_payment` | Proposta |
| RN-M02-04 | Preu: soci si `members.is_member(person, on=data d'inscripció)`; si no, el de no soci. Es copia a la inscripció i no canvia encara que canviï el catàleg o l'estat de soci. Simpatitzants i ple dret paguen el preu de soci [A validar: junta, S-M01-11] | F §4; S-M02-04 |
| RN-M02-05 | Canviar un preu del catàleg no canvia les activitats ja creades. El preu del catàleg té versions amb data d'entrada en vigor (`TrainingCataloguePrice`): una activitat nova copia el preu vigent el dia que es crea | Proposta |
| RN-M02-06 | Si el preu d'una activitat difereix del catàleg, la nota del motiu és obligatòria i s'avisa el tresorer (correu i avís a l'app). El canvi i el valor anterior van al registre | Resposta del 22/10/2026 |
| RN-M02-07 | Places ocupades = inscripcions `pending_payment` + `confirmed` + `offered`. Mai més que `max_places`: el recompte i la inscripció es fan dins una transacció amb la fila de l'activitat bloquejada (`SELECT … FOR UPDATE`) | F §4 i §5 |
| RN-M02-08 | Termini de pagament: `payment_window_hours` des de la inscripció (o des d'acceptar l'oferta), amb un valor per defecte de 72 hores (ajust `activities.default_payment_window_hours`) [A validar: responsable de cursos i sortides i tresorer, S-M02-02]. Un pagament en curs (intent del 05b «en curs») allarga el termini fins que acaba. Una transferència anunciada no l'allarga | Proposta |
| RN-M02-09 | Llista d'espera per ordre d'arribada; el responsable pot reordenar-la amb motiu. Oferta de plaça amb 48 hores per acceptar-la (ajust `activities.offer_accept_hours`) [A validar, S-M02-03]. Si queda menys d'aquest termini per a la data límit, el termini acaba a la data límit | F §4 i §5 |
| RN-M02-10 | Requisits: titulació mínima (`required_level`, contra les titulacions de la persona) i llicència vigent (registre mínim del 01; quan existeixi el 06, `licences.current`) a la data de l'activitat. Quan existeixi el 06, una llicència **en tràmit** (`status = in_progress`, RN-M06-13) compta com a «no vigent, en tràmit»: en mode `warn` es pot inscriure i el responsable la veu marcada «en tràmit»; en mode `block` no es pot inscriure. **Titulació:** cada titulació es classifica com a **verificada** (`verified_by` informat) o **del club** (`source = club_course`). Mentre S-M02-10 no es respongui, una titulació del club compta com a «sense verificar»: si arriba al nivell exigit, el responsable veu el requisit marcat «titulació del club, sense verificar»; si en mode `block` això ha d'impedir inscriure's [A validar: responsable de cursos i sortides, S-M02-10] (supòsit: no ho impedeix, només es marca). `requirements_mode = warn` (supòsit per defecte, ajust `activities.default_requirements_mode`; cada activitat el pot canviar): es pot inscriure, veu l'avís i el responsable ho veu marcat. `block`: no es pot inscriure [A validar: junta, S-M02-01] | F §5 |
| RN-M02-11 | Un no soci només es pot inscriure si l'activitat té `open_to_non_members`; s'inscriu com a convidat amb dades mínimes i consentiment i paga amb l'enllaç (021; RN-30 de la 00) | F §4; 021 |
| RN-M02-12 | Cancel·lació del participant: només abans de la data límit d'inscripció. L'import a tornar el fixa la política del club [A validar: junta, S-M02-05]; mentre no hi sigui, la proposta de devolució és de l'import pagat i el tresorer decideix | F §4 |
| RN-M02-13 | Cancel·lació de l'activitat pel club (també per meteorologia): proposta de devolució del **100 %** de l'import pagat a cada inscrit [A validar: junta, S-M02-05]. La comissió del proveïdor no es recupera i queda com a despesa de l'activitat (RN-T11, 013) | F §5 |
| RN-M02-14 | Un curs pot passar a `done` amb alumnes en reforç: les seves sessions de reforç continuen lligades a la mateixa activitat (resposta del 22/10/2026: lligades al curs actiu de l'alumne) | Resposta del 22/10/2026 |
| RN-M02-15 | Les classes de reforç tenen cost per a l'alumne (resposta del 22/10/2026). Preu: `reinforcement_price_cents` del catàleg, per proposta confirmada [A validar: junta, import i si és per classe o per proposta]. Càrrec «inscripció» a la mateixa activitat i departament | F 9.17; resposta del 22/10/2026 |
| RN-M02-16 | Un alumne no rep el certificat fins que l'instructor el registra apte. El certificat és del club, en PDF, amb número únic `C-AAAA-NNNN` [A validar: junta]; la titulació oficial de la federació o l'agència es tramita fora de la plataforma [A verificar: FECDAS]. En emetre'l es crea la titulació de la persona amb `source = club_course` | F §4 |
| RN-M02-17 | Ni incidències, ni observacions, ni avaluacions no poden contenir dades de salut. Un accident segueix el protocol del club fora de la plataforma [A validar: junta] | CLAUDE.md; P-07 |
| RN-M02-18 | Qualsevol canvi del programa del dia, de les sessions, del lloc o de l'hora d'una activitat `open` o posterior avisa automàticament els inscrits `confirmed`, `pending_payment` i `offered` | F §5 |
| RN-M02-19 | Avisos per correu i a la safata de l'app, mai push (041): confirmació, recordatori (ajust `activities.reminder_days_before`; supòsit: 2 dies abans de cada sessió o sortida [A validar: secretaria, S-M02-15]), canvi de programa, oferta de plaça, termini de pagament, cancel·lació i missatge del responsable | F §4 i §5; 041 |
| RN-M02-20 | Una activitat no es pot marcar `done` abans de la data de l'última sessió (curs) o de la sortida | Proposta |
| RN-M02-21 | **Duplicar** (026): copia títol, descripció, tipus, subtipus, projecte, catàleg, departament, centre de cost, places, preus (i la nota), requisits, termini de pagament, programa del dia, sessions del grup (no les de reforç) amb instructors, i el material típic (via senyal, 03). Desplaça totes les dates i hores per la diferència entre la data d'inici nova i l'antiga. **No copia:** inscripcions, llista d'espera, pagaments, assistència, avaluacions, resultats, incidències ni fotos. La còpia és `draft` i guarda `duplicated_from` | F 9.18; 026 |
| RN-M02-22 | Comprovacions de tancament (`closing_blockers`): inscripcions `pending_payment` o `offered`, càrrecs de reforç sense pagar, propostes de devolució sense fer i les que registrin altres mòduls (material pendent i càrrecs de lloguer sense pagar, 03) | F §5 («no es pot tancar amb cobraments o material pendents») |
| RN-M02-23 | Les fotos i els resultats ambientals no es publiquen enlloc des del 02. La publicació és del 07 i només amb autor, permís i consentiment de les persones que hi surtin (P-41) | P-41 |
| RN-M02-24 | Previsió marítima: només un **enllaç** a la pàgina pública del servei (ajust `activities.marine_forecast_url`; inicial, Meteocat), sense incrustar-ne cap giny ni carregar-ne cap script (046) | F §5; 046 |
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
| `activities.on_charge_paid(event)` | esdeveniment `charge.paid` d'un càrrec amb origen `activities` | inscripció a `confirmed` o reforç pagat; si ja ho estava, no fa res (idempotent) | — | Subscriptor de l'esdeveniment del 05b (049) |
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
| `events.subscribe("charge.paid", activities.on_charge_paid)` | 05b i 00 ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) | Saber quan es paga |
| `members.is_member(person, on)` | 01 | Preu |
| `members.licence_record(person)` | 01 (049) | Requisit de llicència fins que existeixi el 06; després, `licences.current(person)` (06) |
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
- **CA-M02-26** Donat un preu de catàleg de 4500 i un canvi a 5000 amb data d'entrada en vigor l'1 del mes vinent, quan es crea una activitat avui, llavors copia 4500; quan es crea a partir d'aquella data, copia 5000; les activitats ja creades no canvien, i el tresorer i la junta reben el correu amb 4500 i 5000.
- **CA-M02-27** Donat `activities.offer_accept_hours` a 24, quan s'ofereix una plaça, llavors el termini és de 24 hores (o la data límit, si és abans); un valor d'11 o de 169 es rebutja.
- **CA-M02-28** Donat el 06 actiu i un participant amb la llicència en tràmit (`licences.current` torna `in_progress`), quan s'inscriu a una activitat en mode `warn`, llavors s'accepta i el responsable el veu marcat «en tràmit» (l'instructor veu «no»); en mode `block`, es rebutja.
- **CA-M02-29** Donat una activitat que exigeix un nivell i un participant que només el té amb una titulació `source = club_course`, quan s'inscriu, llavors el requisit surt marcat «titulació del club, sense verificar» per al responsable; amb una titulació del mateix nivell amb `verified_by` informat, surt com a complert sense marca.

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
| T-M02-10 | Subscriptor de `charge.paid` (`on_charge_paid`), idempotent | S | `apps/activities/charges.py` | T-M05b-21 | CA-M02-07; prova d'esdeveniment repetit |
| T-M02-11 | Inscripció del soci amb preu, requisits i càrrec | L | `apps/activities/enrolment.py` | T-M02-09, T-M02-10, T-M02-23 | CA-M02-06, 12, 13, 28, 29 |
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
| T-M02-23 | Titulacions de la persona (declarades i del club) i lectura de la llicència | M | `models.py` | T-M01-30 | RN-M02-10 |
| T-M02-24 | Informes operatius: participants, horari imprimible, ocupació (CSV i impressió) | S | vistes | T-M02-12 | Proves de permisos |
| T-M02-25 | Dades de prova inventades: catàlegs, activitats, inscrits, avaluacions | S | `apps/activities/fixtures/` | T-M02-20 | Es carreguen amb una ordre |
| T-M02-26 | Proves de principi a fi amb `FakeProvider` | L | `tests/` | T-M02-11 a T-M02-22 | Totes en verd |
| T-M02-27 | Guia del responsable i de l'instructor; ajuda per inscriure's | S | `docs/` | T-M02-26 | Revisades |
| T-M02-28 | Pantalla d'**ajustos** del mòdul: els seus valors (bloc «Valors configurables» de la secció 6), amb valor inicial, rang vàlid, rol que el canvia, registre (qui, quan, valor anterior) i data d'entrada en vigor si afecta diners; només per als rols amb permís | S | `apps/activities/settings.py`, vistes | T-M02-04; T-AJ-02 (peça comuna d'ajustos, [055](#valors-configurables-055)) | Per valor: fora de rang es rebutja; el canvi queda al registre; un rol sense permís rep «no trobat»; un canvi de diners no toca el que ja s'ha demanat; CA-M02-26, 27 |

<a id="M02-11-proves"></a>
## M02-11 Pla de proves

- **Unitàries (B1):** transicions d'activitat i d'inscripció; preu de soci o no soci; desplaçament de dates en duplicar; places ocupades; terminis i ofertes; requisits en mode avís i bloqueig; suma de residus en grams.
- **Concurrència:** dues i deu inscripcions alhora a l'última plaça; oferta i nova inscripció alhora.
- **Integració:** inscripció → pagament amb `FakeProvider` → `charge.paid` → `on_charge_paid` → `confirmed` → ingrés a l'activitat (04); cancel·lació per meteorologia → propostes → devolució pel tresorer (05b); reforç → càrrec → pagament.
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
| Un subscriptor de `charge.paid` falla o rep l'esdeveniment dues vegades | Mitjà: una inscripció pagada que no es confirma | Lliurament a la cua amb reintents i registre únic per (esdeveniment, subscriptor) ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)); alerta a l'administrador si un lliurament falla repetidament | Informàtica |
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
1. ~~El 05b (aprovat) només avisa el 01 quan es paga un càrrec.~~ Resolt per la [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md): esdeveniment general `charge.paid`.
2. ~~El 01 (aprovat) guarda la llicència però no ofereix cap servei per llegir-la.~~ Resolt per la 049: `members.licence_record`, només lectura.
3. **«Tancada econòmicament» és un estat del 02, però el tancament és del 09, que es construeix després.** Fins que existeixi el 09, les activitats queden `done`. Si el club vol tancar-les abans, caldria avançar una part del 09. Propietari: tresorer.
4. **Reforç després del tancament econòmic:** si un alumne necessita reforç quan el 09 ja ha congelat el marge del curs, el càrrec nou no hi entraria. Proposta per al 09: no tancar un curs amb reforç en curs, o imputar-lo al període següent. Propietari: tresorer.
5. **F §4 deia que el responsable de cursos confirma el reforç i F §5 parla d'un «responsable de sortides i medi ambient»;** la spec 00 té un sol rol «responsable de cursos i sortides». Si són persones diferents amb permisos diferents, cal un rol nou (P-04). Propietari: junta.
6. **«Grup de comunicació» de F §5 vs. el xat del 10:** el 02 només envia missatges d'un sentit; si el club vol substituir el grup de WhatsApp des del primer dia, el 10 s'ha d'avançar. Propietari: junta.
7. **Pagar amb Bizum una inscripció que caduca mentre s'espera la confirmació:** RN-M02-08 allarga el termini mentre l'intent és «en curs»; si el proveïdor no informa mai, la caducitat del 05b ho acaba resolent. Propietari: informàtica.
8. **El material llogat el paga el participant** (F §6) però el 02 cobra la inscripció abans de saber si es lloga. Es resol al 03 amb un càrrec a part ([M03-7](#M03-7-regles)). Propietari: junta i tresorer.

**Requisits pendents** (s'han de resoldre quan es revisi aquesta secció)
| ID | Requisit | Origen | Propietari |
|---|---|---|---|
| RP-M02-01 | **Condicional a `licences.day_enabled`** (desactivada per defecte, RN-M06-01). **Llicència d'un dia:** quan existeixi el 06 i l'opció sigui activada, el 02 li demanarà si una activitat (per a un participant i una data) necessita llicència d'un dia, i oferirà demanar-la. El 06 no depèn del 02: la pregunta va del 02 al 06 (`licences.current` i, si cal, un servei nou de lectura del 06). Fins llavors, el 02 només avisa (RN-M02-10) | [052](decisions/052-llicencia-font-unica-al-06.md) | Responsable del projecte |
| RP-M02-02 | **Categoria de llicència exigida:** una activitat o un rol podrà exigir una categoria concreta (per exemple, tècnic per a un instructor). `licences.current` ja torna la categoria (RN-M06-13); el 02 hi afegirà el requisit, amb el mateix avís o bloqueig de RN-M02-10. Si cal la tècnica per als instructors [A validar: responsable de cursos i sortides] | Revisió del 06, 28/10/2026 | Responsable de cursos i sortides |
| RP-M02-03 | **Sortides a l'estranger:** avís al responsable i als participants, 7 dies abans, que cal la cobertura internacional de la llicència, excepte per a Portugal i França [A verificar: FECDAS, condicions i països] | Revisió del 06, 28/10/2026 | Responsable de cursos i sortides |

<a id="M02-14-aprovar"></a>
## M02-14 Què cal aprovar abans de començar

**Aprovat el 28/10/2026** pel responsable del projecte, alhora que els 02, 03, 06 i 09 (amb l'apartat d'ajuts), sense canviar cap regla ni cap criteri. Respostes d'aquesta aprovació:
- Els **supòsits per defecte** s'accepten per començar i **no bloquegen el codi**.
- **Per entrar en producció** cal respondre els [A verificar] externs i les decisions de la junta ([ordre del dia](#ordre-del-dia-junta)).
- Tots els [A validar] i [A verificar] continuen oberts amb el seu propietari: aquesta aprovació no els resol.

Punts que es van presentar per aprovar:

1. **Aquesta secció del 02**, amb els estats, la plantilla de duplicar (RN-M02-21) i la separació 02 ↔ 03 per senyals i punts d'extensió.
2. ~~Ampliació del contracte del 01~~ **Aprovada per la [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)**: `members.licence_record(person)`, només lectura (T-M01-30).
3. ~~Ampliació del contracte de la 00 i del 05b~~ **Aprovada per la 049** com a esdeveniment general `charge.paid` (T-M05b-21), no com a crida directa al 02. Si el 02 ha de reaccionar a un càrrec retornat o anul·lat, caldrà aprovar aquell esdeveniment a part (049, conseqüències).
4. **Supòsits per defecte** S-M02-01 (avís), S-M02-02 (72 hores), S-M02-04 (mateix preu de soci), S-M02-05 (devolució decidida pel tresorer; 100 % si cancel·la el club) i S-M02-06 (no socis si l'activitat ho permet) [A validar: junta i tresorer]. No bloquegen el codi: són valors configurables.
5. **Per entrar en producció** (no per començar): catàleg amb preus (S-M02-07) i política de cancel·lació (S-M02-05) [A validar: junta].


<a id="M02-addenda-058"></a>
## M02 — Addenda de la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md): instructors, nivells, especialitats, titulacions i edat mínima

Aprovada el 29/10/2026. **No canvia cap regla aprovada** del M02: hi afegeix els punts 3, 13 i 14 de la 058 i la comprovació de l'edat mínima del punt 1. Quan un punt d'aquesta addenda i el text anterior diuen coses diferents sobre el mateix, val l'addenda (com amb la 052).

**Entitats**
- `CertificationLevel` (nou): `name` (únic), `rank` (enter únic, ordre: un número més alt és un nivell més alt), `agency` (`CharField(60)`, opcional), `active`. L'edita el responsable de cursos i sortides. Dades inicials: les que doni el responsable (per exemple, B1 < B2 i els nivells d'1 i 2 estrelles de la FECDAS) [A verificar: FECDAS, S-M02-11].
- `Activity`: camp nou `min_level` (FK `CertificationLevel`, null), que fa la funció del camp de text `required_level` per als requisits nous; camps nous `required_specialities` (M2M a fitxes del catàleg de tipus `speciality`) i `specialities_rule` (`all` totes, `any` alguna).
- `OutingType` i `TrainingCatalogueEntry`: camp nou `default_requirements_mode` (`warn`, `block`, null). Si és buit, val l'ajust general `activities.default_requirements_mode` (VC-24).
- `TrainingCatalogueEntry`: camp nou `min_age` (enter, null), que es copia a l'activitat. Valors: [A validar: responsable de cursos i sortides].
- `DiverCertification`: camps nous `level` (FK `CertificationLevel`, null), `speciality` (FK a una fitxa de tipus `speciality`, null; una de les dues és obligatòria), `issuer` (`CharField(120)`; «C.R.I.S.» en una titulació del club), `instructor` (FK Person, null), `certificate_number` (null) i `course_outcome` (FK, null).
- Ajust nou: `activities.instructor_requirements_mode` (`block` o `warn`), valor inicial `block` [A validar: junta].

**Regles noves**
| ID | Regla |
|---|---|
| RN-M02-26 | **Instructors:** per assignar una persona com a instructor d'una sessió cal que sigui **soci actiu** (`members.is_member`) i que tingui **llicència tècnica vigent** (`licences.current` amb `status = active` i categoria tècnic) a la data de la sessió. «Adherit al C.R.I.S.» = soci actiu [A validar: junta]. Amb `instructor_requirements_mode = block` no es pot assignar; amb `warn`, s'assigna i el responsable ho veu marcat. Mentre no existeixi el 06, la categoria no es pot comprovar: la condició de llicència es comprova només com a avís [A validar: responsable del projecte]. Si deixa de complir-se per a una sessió futura, la sessió surt marcada al responsable |
| RN-M02-27 | **Nivell mínim:** una persona compleix `min_level` si té una titulació amb `level.rank` igual o més alt. Un «B1/B2» és «mínim B1»; si els grups fan coses diferents, es fan dues activitats (duplicar, RN-M02-21) |
| RN-M02-28 | **Especialitats:** amb `specialities_rule = all`, cal tenir totes les de `required_specialities`; amb `any`, n'hi ha prou amb una |
| RN-M02-29 | **Mode per activitat:** cada activitat té el seu `requirements_mode`, modificable; en crear-la, es copia el `default_requirements_mode` del tipus de sortida o de la fitxa del catàleg i, si és buit, l'ajust general |
| RN-M02-30 | **Quines titulacions compten:** en mode `block` només compten les titulacions **verificades** (`verified_by` informat) o d'un **curs del club** (`source = club_course`); les declarades o importades sense verificar només donen avís [A validar: junta]. En mode `warn` compten totes, i el responsable veu de quin origen és cadascuna. Substitueix, per al mode `block`, la marca «titulació del club, sense verificar» de RN-M02-10 |
| RN-M02-31 | **Titulació del club:** en emetre el certificat (RN-M02-16) es crea la titulació amb `issuer` «C.R.I.S.», data, instructor, nivell o especialitat i número de certificat, lligada al resultat del curs |
| RN-M02-32 | **Titulacions inicials:** la secretaria o el responsable les carreguen a mà (origen `declared` o `imported`) i les poden verificar (queda qui i quan). Si el fitxer de Cluber porta titulacions, s'importen amb origen `imported` [A verificar: tresorer, mostra Q-23] |
| RN-M02-33 | **Edat mínima:** si l'activitat té `min_age`, es comprova amb `persons.age_band` o la data de naixement a la data d'inici. Sense data de naixement, el responsable veu «edat desconeguda». Avís o bloqueig segons el `requirements_mode` de l'activitat. Cap rol fora de la secretaria i l'administrador no veu la data (RN-M01-48) |

**Criteris d'acceptació**
- **CA-M02-30** Donat `instructor_requirements_mode = block` i una persona sòcia amb una llicència d'aficionat vigent, quan se l'assigna a una sessió, llavors es rebutja; amb una llicència tècnica vigent, s'accepta; amb `warn`, s'accepta i surt marcada.
- **CA-M02-31** Donat una activitat amb `min_level` B1 i un participant amb una titulació B2 verificada, quan s'inscriu en mode `block`, llavors s'accepta; amb una titulació B2 declarada sense verificar, es rebutja en `block` i s'accepta amb avís en `warn`.
- **CA-M02-32** Donat una activitat que demana les especialitats A i B amb `any`, quan s'inscriu una persona que només té A, llavors compleix; amb `all`, no compleix.
- **CA-M02-33** Donat un curs del club acabat, quan s'emet el certificat d'un alumne apte, llavors la titulació té `issuer` «C.R.I.S.», l'instructor, el nivell i el número del certificat, i compta en mode `block`.
- **CA-M02-34** Donat un tipus de sortida amb `default_requirements_mode = block`, quan es crea una sortida d'aquest tipus, llavors l'activitat neix en `block` i el responsable la pot canviar a `warn`.

**Tasques**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M02-29 | Llista de nivells, `min_level`, especialitats exigides, mode per defecte per tipus i càlcul del requisit ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md)) | M | `apps/activities/requirements.py`, models, migració | T-M02-02, T-M02-23 | CA-M02-31, 32, 34 |
| T-M02-30 | Requisits per assignar instructors i ajust del mode | S | `apps/activities/sessions.py` | T-M02-06, T-M06-13 (quan existeixi) | CA-M02-30 |
| T-M02-31 | Titulació del club en emetre el certificat; càrrega manual, verificació i importació de titulacions | M | `certificates.py`, vistes | T-M02-19, T-M02-29 | CA-M02-33 |
| T-M02-32 | Edat mínima per fitxa i activitat amb `persons.age_band` | S | `requirements.py` | T-M02-29, T-M01-33 | Prova amb dates inventades: major, menor i sense data |

<a id="M02-addenda-059"></a>
## M02 — Addenda de la [059](decisions/059-rols-i-permisos-editables.md): permisos editables i configuració inicial

Aprovada el 30/10/2026. **No canvia cap regla** del M02. La taula de [M02-4](#M02-4-rols) passa a ser la **configuració inicial** dels permisos del mòdul, que l'administrador pot canviar des de l'app ([peça comuna](#rols-i-permisos-059)). Els canvis respecte de la taula, cel·la per cel·la, són a la [matriu inicial](#rols-i-permisos-059-matriu). Les cel·les [A validar] prenen el supòsit per defecte del mòdul; si no n'hi ha, «—»; si l'acció es quedaria sense ningú, l'administrador.

**Què canvia**
- El **tresorer** i el **President** gestionen activitats completes: AC5 a AC8, AC15 a AC17 i AC20. No passen llista ni avaluen; el President sí que passa llista (AC9).
- El tresorer i el President mantenen el catàleg i els preus (AC6). El President confirma reforços (AC11) i emet certificats (AC13).
- **Avaluar, proposar reforç i posar apte** (AC10 i AC12) només ho fa qui fa classe a la sessió (RN-RP-04).
- El responsable de material conserva la consulta de participants (AC8) per assignar material.
- Queden resolts:
  - S-M02-16: la secretaria no fa inscripcions presencials;
  - S-M02-17: dades dels alumnes per a l'instructor;
  - S-M02-18: el responsable veu els imports cobrats de totes les activitats i el marge de les seves.
- Les **conferències** (mòdul 11) tenen la configuració inicial a CF1 i CF2.

**Criteri d'acceptació**
- **CA-M02-35** Donat un compte amb el rol tresorer, quan crea, publica i duplica una activitat, llavors pot. Quan vol passar llista o avaluar un alumne, rep «no trobat», tret que faci classe a la sessió.

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M02-33 | Declarar els permisos del 02 al catàleg (AC5 a AC20, C3; CF1 i CF2 reservats per a l'11) i comprovar-los a totes les vistes i serveis | S | `apps/activities/permissions.py` | T-RP-01 | CA-M02-35; proves per cel·la del 02 (CA-RP-13) |

<a id="M02-addenda-060"></a>
## M02 — Addenda de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): ordre, obertura, convidats menors i cancel·lacions

Aprovada el 31/10/2026. **No canvia cap regla aprovada** del M02: hi afegeix el requisit d'obertura, la declaració d'edat dels convidats i com es propaguen les cancel·lacions.

**Ordre.** El 06 es construeix abans del 02. La dependència «06 (quan existeixi)» de [M02-2](#M02-2-dependencies) passa a ser una dependència normal: la T-M02-30 troba la T-M06-13 feta i el mode provisional de RN-M02-26 (llicència només com a avís mentre no existeixi el 06) no s'aplica. La T-M02-14 depèn de la **T-M00-02** (enllaços de convidat, [apèndix](#ajustos-060-peces-00)).

**Entitats.** `Enrolment`: camp nou `void_pending_since` (data i hora, null), «anul·lar el càrrec quan acabi l'intent». La declaració «Soc major d'edat» es guarda com un consentiment de la 00 (text amb versió, data i canal; T-M01-08), mai com una data de naixement.

| ID | Regla |
|---|---|
| RN-M02-34 | **Obertura del 02.** No s'obren inscripcions a producció fins que la secretaria ha fet la confirmació en bloc de les llicències d'any natural pendents de confirmar: amb la T-M01-36 abans del pas únic al 06, o amb la T-M06-24 amb el 06 actiu. A més, s'ha d'haver revisat la llista de «pendents de confirmar». És una condició d'entrada en producció, que es comprova a la checklist, no al codi |
| RN-M02-35 | **Convidats i menors.** Mentre P-33 sigui oberta, tota inscripció d'un convidat que no demana la data de naixement (RN-M01-53) porta la casella obligatòria **«Soc major d'edat»**; sense marcar-la, no es pot enviar. A la inscripció presencial la marca qui la fa, després de preguntar-ho. Si la persona diu que no és major d'edat, el formulari explica que de moment el club no admet inscripcions de menors (P-33) |
| RN-M02-36 | **Cancel·lacions per esdeveniments.** La cancel·lació d'una inscripció i la d'una activitat s'emeten com a esdeveniments de la [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md) (`enrolment.cancelled` i `activity.cancelled`): dins la mateixa transacció, lliurats a la cua i amb un registre de lliuraments únic per subscriptor. Substitueixen els senyals `enrolment_cancelled` i `activity_cancelled` de [M02-8](#M02-8-serveis). La resta de senyals no canvia |
| RN-M02-37 | **Cancel·lar amb un intent en curs.** Si en cancel·lar una inscripció o una activitat el càrrec té un intent en curs o enviat al banc (RN-M05b-22), la inscripció passa igualment a `cancelled` i s'omple `void_pending_since`. Una tasca de la cua torna a provar d'anul·lar el càrrec quan l'intent acaba. Si l'intent acaba **pagat**, `activities.on_charge_paid` no confirma la inscripció: crea una `RefundProposal` de l'import pagat, amb la regla de RN-M02-12 o de RN-M02-13 segons qui ha cancel·lat. Si acaba **fallat o caducat**, el càrrec s'anul·la |

- **CA-M02-36** Donat registres d'any natural pendents de confirmar, quan es revisa la checklist d'entrada en producció del 02, llavors el punt d'obertura no es pot marcar fins que la confirmació en bloc s'ha fet.
- **CA-M02-37** Donat un convidat a una activitat sense edat mínima, quan envia la inscripció sense marcar «Soc major d'edat», llavors es rebutja; quan la marca, s'accepta i queda la declaració amb la versió del text i sense cap data de naixement.
- **CA-M02-38** Donat `activity.cancelled` lliurat dues vegades, quan el rep cada subscriptor, llavors cada efecte s'aplica una sola vegada.
- **CA-M02-39** Donat una sortida amb un inscrit que té un Bizum esperant confirmació, quan el responsable la cancel·la, llavors la inscripció és `cancelled` amb `void_pending_since`. Si el Bizum es confirma després, hi ha una proposta de devolució del 100 % i la inscripció no es confirma; si caduca, el càrrec s'anul·la.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M02-34 | Casella «Soc major d'edat» a les inscripcions de convidats i presencials | S | `apps/activities/enrolment.py`, plantilles | T-M02-14, T-M01-08 | CA-M02-37 |
| T-M02-35 | `enrolment.cancelled` i `activity.cancelled` com a esdeveniments de la 049 | S | `apps/activities/cancellation.py`, `apps/core/events.py` | T-M02-15, T-M05b-21 | CA-M02-38 |
| T-M02-36 | Cancel·lació amb un intent en curs: `void_pending_since`, reintent d'anul·lació i proposta de devolució si s'acaba pagant | S | `apps/activities/cancellation.py`, `charges.py`, tasques de la cua | T-M02-15, T-M02-10 | CA-M02-39 |

---

<a id="M03"></a>
# Mòdul 03 — Material

**Estat: aprovat** pel responsable del projecte el 28/10/2026 ([M03-14](#M03-14-aprovar)), alhora que els 02, 03, 06 i 09. Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M03-addenda-059)).

**Fonts:** document de funcionalitats (F §6 Material i cost per participant, processos 9.6 i 9.7), mapa de la plataforma v8 (M04 Material), respostes del responsable del projecte del 20/10/2026 (llista de tipus, ampolla amb litres lliures, stock de tot el material, material al registre d'immersió, tarifes per centre amb marge propi) i del 22/10/2026 (les classes de reforç són un ús nou de material), decisions [013](decisions/013-imputacio-comissions.md), [026](decisions/026-duplicar-activitats-al-modul-02.md), [035](decisions/035-dades-nomes-dins-ue.md) i [046](decisions/046-interficie-django-htmx-servida-des-del-vps.md); [spec 00](../specs/00-base-comuna/spec.md) (càrrec, importacions, fitxers); secció [M02](#M02).

**Proveïdor de pagaments.** El 03 no cobra res directament. Si s'aprova que el participant paga el lloguer a part (RN-M03-11), el 03 crea un càrrec de la 00 i el cobra el [05b](#M05b-8-serveis) a través de l'adaptador.

<a id="M03-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Respondre per a cada activitat què fa servir cada participant, d'on surt (propi, del club o llogat a un centre de busseig) i quant costa; portar l'inventari de tot el material del club peça per peça, amb stock i revisions; i donar al 09 el cost de material i el marge dels lloguers. |
| **Processos que cobreix** | P-M03-A Inventari, tipus i stock · P-M03-B Centres de busseig i tarifes · P-M03-C Necessitats a la inscripció · P-M03-D Assignar, llogar, lliurar i retornar (F 9.6) · P-M03-E Quantitats reals, registre d'immersió i cost per participant · P-M03-F Revisions (F 9.7) · P-M03-G Càrrega inicial de l'inventari |
| **Tasques** | 24 (T-M03-01 a T-M03-24); la T-M03-23 l'afegeix la 059 i la T-M03-24, la 060 |
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

### Valors configurables (pantalla d'ajustos, T-M03-22)
Valors de la [regla general](#regles), a la pantalla d'ajustos del mòdul sobre la [peça comuna](#valors-configurables-055) de la [055](decisions/055-ajustos-configurables-i-addendes.md): cada canvi es comprova al servidor (rol i rang), queda al registre amb el valor anterior i, si afecta diners, porta data d'entrada en vigor i avisa per correu el tresorer i la junta (RN-AJ-03 i RN-AJ-04). Els valors inicials són els supòsits que ja hi havia; les preguntes obertes continuen obertes.

| Clau de l'ajust | VC | Valor inicial | Rang vàlid | Qui el canvia | Data d'entrada en vigor |
|---|---|---|---|---|---|
| Cost d'ús per tipus (`UsageRate.cost_per_day_cents`) | VC-28 | 0 (sense cap fila) | ≥ 0 | Tresorer | Sí (`valid_from`) |
| `equipment.review_notice_days` | VC-29 | 30 | 1 a 90 | Responsable de material | — |
| `equipment.unreturned_after_days` | VC-29 | 7 | 1 a 90 | Responsable de material | — |

Tipus de material, centres i tarifes (VC-27) ja són dades del mòdul, i les tarifes ja tenen versions amb data d'inici (RN-M03-06); un canvi de tarifa també avisa el tresorer i la junta (RN-AJ-04). Es queda al codi: el format dels codis de les peces (VC-30).

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
| RN-M03-08 | Cost d'ús d'una peça del club = dies de l'assignació × `cost_per_day_cents` del seu tipus vigent (`UsageRate`, que canvia el tresorer a la pantalla d'ajustos amb data d'entrada en vigor). Sense tarifa, 0. La fórmula (amortització o tarifa fixa per tipus) la fixa la junta [A validar: junta i tresorer, S-M03-02] | F §6 |
| RN-M03-09 | Cost de material d'un participant = suma del `cost_cents` de les seves assignacions fetes servir (`returned` o `delivered`); `not_used` i `cancelled` no compten | F §6 |
| RN-M03-10 | **Per al marge del 09:** el «cost de material» de la fórmula de CLAUDE.md és el cost d'ús del material del club (RN-M03-08). El lloguer entra al marge com a **despesa** quan es registra la factura del centre (09); mentre no hi és, el 09 fa servir el cost estimat de les tarifes. Mai totes dues coses alhora, per no comptar el lloguer dues vegades | CLAUDE.md; F §6 i §7 |
| RN-M03-11 | El participant paga el material llogat al preu per al participant de la tarifa (F §6). Supòsit: quan el responsable confirma un lloguer, es crea un **càrrec a part** de tipus «inscripció» amb aquest preu, l'activitat i el departament de l'activitat, i es cobra amb el 05b [A validar: junta i tresorer, S-M03-03]. Si el càrrec de lloguer no és pagat quan es vol tancar l'activitat, és un motiu per no tancar-la (RN-M03-13). El material del club no es cobra al participant mentre la junta no en fixi un preu | F §6; [M02-13](#M02-13-riscos), dubte 8 |
| RN-M03-12 | Transicions de l'assignació: `planned → delivered → returned`; `planned → not_used / cancelled`; `delivered → not_used` (no s'ha fet servir). En retornar, la peça passa a `available` o `in_review` | F 9.6 |
| RN-M03-13 | «Material pendent» (motiu per no tancar l'activitat, registrat al 02): assignacions `planned` o `delivered` després de l'activitat, necessitats «necessito» sense assignació, lloguers sense quantitat real confirmada llistes de lloguer no marcades «enviades» i, si s'aprova el càrrec a part (RN-M03-11), càrrecs de lloguer sense pagar | F §5 i §6 |
| RN-M03-14 | Una peça lliurada que no s'ha retornat 7 dies (ajust `equipment.unreturned_after_days`) després de l'activitat [A validar: junta, S-M03-06] surt a l'avís diari del responsable | Proposta |
| RN-M03-15 | Avís de revisió 30 dies (ajust `equipment.review_notice_days`) abans de `next_review_on` [A validar: junta, S-M03-06] i cada dia mentre estigui vençuda. La plataforma no calcula terminis legals: la data la posa el responsable segons la normativa o el fabricant [A verificar: normativa d'equips a pressió per a les ampolles; fabricant per als reguladors] | F 9.7 |
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
- **CA-M03-18** Donat un cost d'ús de les ampolles canviat de 0 a 200 cèntims per dia amb data d'entrada en vigor l'1 del mes vinent, quan es calcula el cost d'una assignació d'abans d'aquella data, llavors és 0; d'una de després, 200 per dia; un rol que no és el tresorer ni l'administrador no el pot canviar.
- **CA-M03-19** Donat una activitat acabada amb un càrrec de lloguer (RN-M03-11) sense pagar, quan es demana `closing_blockers`, llavors la llista conté «càrrec de lloguer sense pagar» i el 09 no la pot tancar; quan el càrrec és pagat, el motiu desapareix.

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
| T-M03-15 | Comprovació de tancament i bloc de «Les meves activitats» | S | `apps/equipment/extensions.py` | T-M03-12, T-M02-22 | CA-M03-09; CA-M03-19 (si s'aprova RN-M03-11) |
| T-M03-16 | Cancel·lacions: alliberar peces i anul·lar càrrecs de lloguer | S | `assignments.py` | T-M03-08, T-M03-11 | CA-M03-14 |
| T-M03-17 | Càrrega inicial de l'inventari amb la importació de la 00 | M | `apps/equipment/imports.py` | T-M03-03 | CA-M03-17 |
| T-M03-18 | Permisos per rol i per objecte | S | `apps/equipment/permissions.py` | T-M03-03 | CA-M03-16 |
| T-M03-19 | Informes: cost per participant i activitat, material més usat, revisions properes | S | vistes | T-M03-13, T-M03-14 | Proves de permisos |
| T-M03-20 | Dades inventades i proves de principi a fi (inscripció → necessitat → assignació → lliurament → retorn → cost) | L | `apps/equipment/fixtures/`, `tests/` | T-M03-08 a T-M03-17 | Totes en verd |
| T-M03-21 | Guia del responsable de material | S | `docs/` | T-M03-20 | Revisada |
| T-M03-22 | Pantalla d'**ajustos** del mòdul: els seus valors (bloc «Valors configurables» de la secció 6), amb valor inicial, rang vàlid, rol que el canvia, registre (qui, quan, valor anterior) i data d'entrada en vigor si afecta diners; només per als rols amb permís | S | `apps/equipment/settings.py`, vistes | T-M03-02; T-AJ-02 (peça comuna d'ajustos, [055](#valors-configurables-055)) | Per valor: fora de rang es rebutja; el canvi queda al registre; un rol sense permís rep «no trobat»; un canvi de diners no toca el que ja s'ha demanat; CA-M03-18 |

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

**Aprovat el 28/10/2026** pel responsable del projecte, alhora que els 02, 03, 06 i 09 (amb l'apartat d'ajuts), sense canviar cap regla ni cap criteri. Respostes d'aquesta aprovació:
- Els **supòsits per defecte** s'accepten per començar i **no bloquegen el codi**.
- **Per entrar en producció** cal respondre els [A verificar] externs i les decisions de la junta ([ordre del dia](#ordre-del-dia-junta)).
- Tots els [A validar] i [A verificar] continuen oberts amb el seu propietari: aquesta aprovació no els resol.

Punts que es van presentar per aprovar:

1. **Aquesta secció del 03**, amb l'estat de la peça derivat de les assignacions ([M03-5](#M03-5-processos)) i la restricció d'exclusió.
2. **RN-M03-10** (el lloguer entra al marge com a despesa amb factura; el cost de material és el del club), perquè el 09 hi quedi lligat.
3. **Supòsits per defecte** S-M03-02 (cost d'ús 0), S-M03-03 (càrrec a part del lloguer) i S-M03-04 (referència i inicials a la llista) [A validar: junta i tresorer]. No bloquegen el codi.
4. **Per entrar en producció** (no per començar): centres i tarifes (S-M03-01) i inventari inicial (S-M03-05) [A validar: junta].

<a id="M03-addenda-059"></a>
## M03 — Addenda de la [059](decisions/059-rols-i-permisos-editables.md): permisos editables i configuració inicial

Aprovada el 30/10/2026. **No canvia cap regla** del M03. La taula de [M03-4](#M03-4-rols) passa a ser la **configuració inicial** dels permisos del mòdul, que l'administrador pot canviar des de l'app ([peça comuna](#rols-i-permisos-059)). Els canvis respecte de la taula, cel·la per cel·la, són a la [matriu inicial](#rols-i-permisos-059-matriu). Les cel·les [A validar] prenen el supòsit per defecte del mòdul; si no n'hi ha, «—»; si l'acció es quedaria sense ningú, l'administrador.

**Què canvia**
- «Gestionar inventari i assignar material» és de l'instructor (només les seves sessions), el responsable de cursos i sortides, el responsable de material, el tresorer, l'administrador i el President. Queda resolt S-M03-10 al revés del supòsit: el responsable de cursos i sortides **sí** que assigna material.
- **Lloguer puntual a un centre** (MT6b, nou):
  - qui el registra tria qui ha agafat què i escriu el **cost del centre**;
  - el preu per a l'alumne és el de la tarifa (MT8), que mantenen el responsable de material, el tresorer, l'administrador i el President;
  - l'instructor veu el preu per a l'alumne (C4), però no el marge dels lloguers (MT12);
  - si el centre no té tarifa per a aquell equip, el lloguer queda «sense preu per a l'alumne» fins que el responsable de material la posa [A validar: responsable de material].
- El responsable de cursos i sortides veu el marge dels lloguers de les seves activitats (MT12).
- **Punt feble:** l'instructor pot calcular el marge amb el cost que escriu i el preu de l'alumne. Es pot canviar des de l'editor.

**Criteri d'acceptació**
- **CA-M03-20** Donat un instructor d'una sessió amb un lloguer puntual, quan registra que un alumne ha agafat un jaquet al centre i n'escriu el cost, llavors l'assignació queda amb el cost del centre i el preu per a l'alumne de la tarifa. L'instructor veu el preu per a l'alumne i no el marge. En una sessió on no fa classe, rep «no trobat».

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M03-23 | Declarar els permisos del 03 al catàleg (MT3 a MT13, MT6b, C4) i el lloguer puntual amb el cost del centre | S | `apps/equipment/permissions.py`, `apps/equipment/rentals.py` | T-RP-01, T-M03-10, T-M03-18 | CA-M03-20; proves per cel·la del 03 (CA-RP-13) |

<a id="M03-addenda-060"></a>
## M03 — Addenda de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): cancel·lacions per esdeveniments i lloguers ja enviats

Aprovada el 31/10/2026. **No canvia cap regla** del M03: RN-M03-20 i L-M03-05 s'apliquen igual, però des d'un subscriptor dels esdeveniments de la 049 ([RN-M02-36](#M02-addenda-060)).

| ID | Regla |
|---|---|
| RN-M03-21 | El 03 se subscriu a `enrolment.cancelled` i `activity.cancelled` en lloc dels senyals. El subscriptor és idempotent: un esdeveniment repetit no torna a anul·lar cap assignació ni cap càrrec de lloguer, i no crea cap proposta de devolució nova |
| RN-M03-22 | Si l'activitat es cancel·la amb una `RentalList` ja enviada (`sent_at` informat), la llista surt a «avisar el centre» (L-M03-05). El que el centre cobri per la cancel·lació **no es cobra als participants**: és una despesa de l'activitat al 09 ([RN-M09-32](#M09-addenda-060)). El 03 no crea cap càrrec ni cap despesa |

- **CA-M03-21** Donat `activity.cancelled` lliurat dues vegades, quan el rep el 03, llavors les assignacions queden `cancelled` una sola vegada i hi ha com a molt una proposta de devolució per càrrec de lloguer pagat.
- **CA-M03-22** Donat una activitat amb una llista de lloguer enviada, quan es cancel·la, llavors la llista surt a «avisar el centre» i cap participant rep cap càrrec nou.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M03-24 | Subscriptor de `enrolment.cancelled` i `activity.cancelled` en lloc dels senyals; llistes enviades a «avisar el centre» | S | `apps/equipment/assignments.py`, `rentals.py` | T-M03-16, T-M02-35 | CA-M03-21, 22 |

---

<a id="M09"></a>
# Mòdul 09 — Marge, despeses, ajuts i facturació

**Estat: aprovat** pel responsable del projecte el 28/10/2026 ([M09-14](#M09-14-aprovar)), amb l'apartat d'ajuts i alhora que els 02, 03 i 06. Abans s'anomenava «resta de la 04» ([numeració](#numeracio)). Té dues parts, cadascuna amb la plantilla de 14 seccions: la **principal** (despeses amb factura, altres ingressos, marge per activitat, informes per departament, facturació i tancament de període) i l'apartat **[Ajuts: calendari, sol·licituds i justificació](#M09-ajuts)**. Ampliat per la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) amb una [addenda](#M09-addenda-058) (T-M09-27 a T-M09-29 i T-M09A-16), sense canviar cap regla. Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M09-addenda-059)).

**Fonts:** document de funcionalitats (F §7 Tresoreria, marge per activitat, factures i ajuts; F §5 tancament econòmic de les sortides; processos 9.8, 9.10 i 9.11), mapa de la plataforma v8 (M05c Marge, factures i ajuts), respostes del responsable del projecte del 20/10/2026 (totes les factures per justificar ajuts; els ajuts es compten per departament i no per activitat; centres de busseig amb marge propi) i del 22/10/2026 (factures de tot quan la junta ho activi; subtipus de medi ambient ampliables; preus configurables), instruccions del 27/10/2026 per a l'apartat d'ajuts, decisions [013](decisions/013-imputacio-comissions.md), [027](decisions/027-estructura-basica-de-carrec-i-pagament.md), [028](decisions/028-esborrat-rgpd-i-registre-d-activitat.md), [035](decisions/035-dades-nomes-dins-ue.md), [043](decisions/043-proveidor-de-pagaments-dins-la-ue.md), [046](decisions/046-interficie-django-htmx-servida-des-del-vps.md) i [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md); seccions [M02](#M02) (`closing_blockers`, `mark_closed`), [M03](#M03) (RN-M03-10 i `activity_material_cost`), [M04](#M04) (moviments i conciliació) i [M05b](#M05b) (rebuts i esdeveniment `charge.paid`).

**Proveïdor de pagaments.** El 09 no cobra res i no parla mai amb el proveïdor de pagaments. Llegeix els ingressos, les comissions i les devolucions que han creat el 05b i la 04. Les despeses i els ingressos que no són càrrecs (ajuts, patrocinis) es registren com a moviments de la 04 amb l'[addenda](#M04-addenda-050) de la [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md).

**Proveïdor de facturació.** La factura no la fa la plataforma: la demana per API a un servei homologat per Verifactu, darrere d'un adaptador propi (`InvoicingProvider`), igual que el de pagaments. Quin servei, si el club ha de facturar i amb quin IVA és [A verificar: gestoria, P-02 i P-47]. Mentre no es respongui, la facturació queda desactivada i el justificant de cada pagament és el rebut del 05b.

<a id="M09-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Que el tresorer sàpiga quant guanya o perd cada curs i cada sortida (marge previst mentre és oberta, marge real congelat en tancar-la), que cap despesa quedi sense factura, que els ingressos i les despeses es puguin veure per departament, subtipus i projecte per demanar i justificar ajuts, que es puguin emetre factures amb un servei homologat i que cada període es tanqui i no es toqui més. |
| **Processos que cobreix** | P-M09-A Registrar una despesa (F 9.8) · P-M09-B Repartir una despesa entre activitats · P-M09-C Registrar un ingrés que no és un càrrec (ajut, patrocini, donatiu) · P-M09-D Marge previst i tancament econòmic d'una activitat · P-M09-E Informes per departament, subtipus i projecte · P-M09-F Factures i rectificatives · P-M09-G Tancament de període (F 9.11). La justificació d'ajuts (F 9.10) és a l'[apartat d'ajuts](#M09-ajuts) |
| **Tasques** | 31 (T-M09-01 a T-M09-31), més les 16 de l'apartat d'ajuts (T-M09A-01 a T-M09A-16); de la T-M09-27 a la T-M09-29 i la T-M09A-16 les afegeix la 058, i la T-M09-30 (que també cobreix l'apartat d'ajuts), la 059, i la T-M09-31, la 060 |
| **Què el bloqueja** | Per construir: el 02, el 03, el 05b i l'addenda de la 04 ([050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md), T-M04-20). Facturació: què s'ha de facturar, IVA i Verifactu [A verificar: gestoria, P-02, P-47]. La resta són supòsits configurables ([M09-13](#M09-13-riscos)) |
| **Què cal aprovar** | Aquesta secció i els supòsits S-M09-01 a S-M09-05 ([M09-14](#M09-14-aprovar)). Les peces de la 04 ([050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md)) i els documents amb IBAN ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) ja són aprovats |

<a id="M09-1-intencio"></a>
## M09-1 Intenció, abast i fora d'abast

**Per què.** Avui el marge de cada activitat es calcula a mà, si es calcula, i les factures de despesa es busquen quan es demana un ajut. Sense totes les factures, el club no pot justificar els ajuts de cada tipus d'acció de medi ambient (F §7). La 04 ja sap quins diners entren i surten de cada compte, però no sap a quina activitat corresponen les despeses ni quant val el material.

**Resultat esperat.**
- Cada despesa té la seva factura, categoria, departament i, si toca, l'activitat o activitats o el projecte de medi ambient.
- Cada curs i cada sortida té un marge previst mentre és oberta i un marge real que es congela en tancar-la.
- El tresorer veu els ingressos i les despeses per departament, subtipus i projecte de qualsevol període, amb els ajuts al departament i mai a l'activitat.
- Quan la junta ho activi i la gestoria ho confirmi, cada cobrament té la seva factura feta per un servei homologat, i cada devolució la seva rectificativa.
- Un període tancat no es modifica sense que un administrador el reobri amb motiu.

**Com sabrem que funciona.**
- El marge de la sortida d'exemple ([M09-7](#M09-7-regles)) surt de 130,50 € (21,8 %) amb les dades inventades de la prova.
- El lloguer de material no es compta mai dues vegades (RN-M03-10).
- No es pot tancar un període amb despeses sense factura, línies de l'extracte sense conciliar o activitats fetes sense tancar.
- La numeració de les factures no té salts ni duplicats.

**Dins de l'abast.**
- Categories de despesa (F §7: embarcació, aire, lloguer, instructor, taxa, instal·lacions, altres), ampliables pel tresorer.
- Proveïdors de les despeses (empreses i professionals), amb les dades mínimes per identificar la factura.
- Despeses amb factura adjunta (foto o PDF des del mòbil), pagament, comprovant i conciliació amb la 04.
- Repartiment d'una despesa entre activitats per participants, a parts iguals o a mà.
- Ingressos que no són càrrecs: ajuts, patrocinis, donatius i altres, amb departament (i activitat només per als patrocinis d'una activitat).
- Costos previstos per activitat, marge previst, avís de marge baix i marge real congelat.
- Informes per departament, centre de cost, subtipus i projecte, i llistat de despeses sense factura.
- Factures emeses i rectificatives a través del servei homologat (quan s'activi).
- Tancament i reobertura de període.
- Hores de voluntariat (opcional, per als informes d'ajuts).

**Fora d'abast.**
- **Calendari, sol·licituds i justificació d'ajuts:** són a l'[apartat d'ajuts](#M09-ajuts), dins d'aquest mateix mòdul.
- Cobraments, devolucions i retorns: 05b. Comptes, moviments i conciliació: 04 (amb l'[addenda](#M04-addenda-050) de la [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md)).
- Pressupost anual del club i comptes anuals: [A validar: junta]; el 09 només fa la previsió per activitat.
- Comptabilitat oficial (llibres, impostos, model 182 de donatius): la porta la gestoria amb l'exportació de la 04 i del 09 [A verificar: gestoria].
- Llegir les factures automàticament (OCR): no es fa; el tresorer escriu l'import.
- Factures de compra rebudes per un canal electrònic del proveïdor: es pugen a mà.

<a id="M09-2-dependencies"></a>
## M09-2 Dependències

**De què depèn.**
| Mòdul | Què en fa servir el 09 |
|---|---|
| 00 | Departaments; càrrecs de lectura (activitat i origen de cada càrrec); persona (dades mínimes per a una factura); fitxers privats (factures i comprovants); correu i avisos; cua de tasques; permisos; registre d'activitat |
| 02 | Activitats, estats, participants i projectes i subtipus de medi ambient (lectura); `activities.closing_blockers` i `activities.mark_closed` ([M02-8](#M02-8-serveis)) |
| 03 | `equipment.activity_material_cost`, `equipment.rentals_for` i `equipment.reviews_with_cost` ([M03-8](#M03-8-serveis)); regla RN-M03-10 |
| 04 | Moviments (ingressos, comissions, devolucions) i conciliació; [addenda](#M04-addenda-050) de la [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md) |
| 05b | Esdeveniment `charge.paid` ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) per fer la factura d'un cobrament; devolucions fetes |

**Què depèn del 09.**
| Mòdul | Què necessita |
|---|---|
| 02 | El tancament econòmic de l'activitat (estat `closed`, que només fa el 09) |
| 06 | El pagament a la federació es registra com a despesa del 09 (RN-M09-20) |
| 08 | Marges, ingressos i despeses per departament, despeses sense factura, períodes |
| Apartat d'ajuts | Despeses amb factura i comprovant, ingressos de tipus «ajut» i informes per departament i projecte |

**Peces de mòduls aprovats que el 09 necessita** (aprovades com a addenda per la [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md), sense canviar cap regla de la 04; detall a [M04-addenda-050](#M04-addenda-050)):
1. **Tipus de moviment nous** `expense` i `other_income`, amb `treasury.record_expense` i `treasury.record_other_income`.
2. **Servei d'anul·lació** `treasury.reverse(movement, reason, actor)`, amb motiu i usuari al registre.
3. **Bloqueig de període tancat** amb `treasury.register_movement_guard(guard)`, **només per als moviments nous**. Corregir un període tancat = anul·lació i moviment nou al període obert (RN-T28 i RN-T29). Precisió de la [053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md): el bloqueig només afecta els moviments del 09 i les anul·lacions manuals; els d'origen extern entren al període obert amb la data original guardada (RN-T30 a RN-T33).

<a id="M09-3-capacitats"></a>
## M09-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | On |
|---|---|---|---|
| C1 | Categories de despesa i proveïdors | Tresorer | Configuració |
| C2 | Registrar una despesa amb factura, també des del mòbil | Tresorer; responsable de l'activitat [A validar: junta, S-M09-01] | Despeses |
| C3 | Pagar una despesa i adjuntar-ne el comprovant | Tresorer | Fitxa de la despesa |
| C4 | Repartir una despesa entre activitats | Tresorer | Fitxa de la despesa |
| C5 | Registrar ajuts, patrocinis i donatius | Tresorer | Ingressos |
| C6 | Costos previstos i marge previst | Resp. cursos i sortides, tresorer | Fitxa de l'activitat |
| C7 | Tancar econòmicament una activitat | Tresorer | Fitxa de l'activitat |
| C8 | Informes per departament, subtipus i projecte | Tresorer, junta | Informes |
| C9 | Factures i rectificatives (quan s'activi) | Tresorer | Factures |
| C10 | Veure i descarregar les seves factures | Soci, convidat | Compte personal o enllaç |
| C11 | Tancar i reobrir un període | Tresorer (tancar), administrador (reobrir) | Períodes |
| C12 | Hores de voluntariat | Tresorer | Voluntariat |

**Històries d'usuari**
- **HU-M09-01.** Com a tresorer, vull registrar una despesa amb la foto de la factura des del mòbil, per no perdre cap factura.
- **HU-M09-02.** Com a tresorer, vull veure quines despeses no tenen factura, per reclamar-les abans de tancar el període.
- **HU-M09-03.** Com a tresorer, vull repartir la factura d'una embarcació entre dues sortides segons els participants, perquè el marge de cada una sigui real.
- **HU-M09-04.** Com a responsable de cursos i sortides, vull posar els costos previstos d'una sortida i veure'n el marge previst, per saber si el preu cobreix els costos.
- **HU-M09-05.** Com a tresorer, vull tancar una sortida i que el marge quedi congelat, perquè l'informe no canviï després.
- **HU-M09-06.** Com a tresorer, vull registrar un ajut cobrat al departament de medi ambient i al seu projecte, sense repartir-lo entre sortides.
- **HU-M09-07.** Com a junta, vull veure ingressos i despeses del departament de medi ambient per subtipus i projecte, per decidir quins ajuts demanar.
- **HU-M09-08.** Com a soci, vull descarregar la factura de la meva inscripció quan el club factura.
- **HU-M09-09.** Com a tresorer, vull tancar el mes quan tot quadra, perquè ningú no hi pugui fer canvis.
- **HU-M09-10.** Com a administrador, vull reobrir un període amb motiu quan hi ha un error, i que quedi al registre.

<a id="M09-4-rols"></a>
## M09-4 Rols i permisos

Llegenda com a [M01-4](#M01-4-rols). A les taules, «[A validar]» sense propietari vol dir **junta** (Q-01, P-04).

| # | Acció | Visitant | Part. no soci | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Resp. comunicació | Dept. Història | Junta | Administrador | Resp. botiga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MG1 | Registrar una despesa amb factura | — | — | — | — | — | Les seves activitats [A validar] | Revisions i material [A validar] | Sí | — | — | — | Sí | — |
| MG2 | Pagar una despesa, adjuntar-ne el comprovant i anul·lar-la | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| MG3 | Repartir una despesa entre activitats | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| MG4 | Registrar ajuts, patrocinis i donatius | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| MG5 | Costos previstos d'una activitat | — | — | — | — | — | Les seves | — | Sí | — | — | — | Sí | — |
| MG6 | Veure el marge d'una activitat | — | — | — | — | — | Consulta [A validar: Q-01, S-M02-18] | — | Sí | — | — | Consulta | Sí | — |
| MG7 | Tancar econòmicament una activitat | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| MG8 | Informes per departament, subtipus i projecte | — | — | — | — | — | — | — | Sí | — | Consulta del seu departament [A validar] | Consulta | Sí | — |
| MG9 | Emetre factures i rectificatives | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| MG10 | Veure i descarregar les seves factures | — | Propi (enllaç) | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi |
| MG11 | Tancar un període | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |
| MG12 | Reobrir un període | — | — | — | — | — | — | — | — | — | — | — | Sí | — |
| MG13 | Hores de voluntariat | — | — | — | — | — | — | — | Sí | — | — | [A validar] | Sí | — |
| MG14 | Categories, proveïdors i llindar de marge baix | — | — | — | — | — | — | — | Sí | — | — | — | Sí | — |

**Per objecte.**
- **Responsable de cursos i sortides:** només les activitats de què és responsable; veu els seus costos i el seu marge si la junta ho aprova (S-M02-18), mai els informes de departament.
- **Responsable de material:** només pot registrar despeses de categoria «lloguer» o de revisions, sense activitat d'una altra persona [A validar: junta, S-M09-01].
- **Junta:** consulta, sense poder registrar ni anul·lar res.
- **Documents de justificació** (factures de despesa, comprovants i paquets): només els obren el **tresorer** i la **junta** ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)). L'administrador i qui registra una despesa poden gestionar-la, però no obrir-ne els fitxers.
- **Soci i convidat:** només les factures on és el client.
- **Un sol tresorer** i cap doble aprovació (P-48).

<a id="M09-5-processos"></a>
## M09-5 Processos pas per pas

**Wireframes existents:** cap del 09 (el mapa v8 en té la llista de pantalles de M05c). **Falten** (T-M09-01): llistat i fitxa de despesa (amb el formulari mòbil), despeses sense factura, ingressos, marge d'una activitat (previst i real), taula de marges, informe per departament, factures, períodes i llista de control.

### P-M09-A Registrar una despesa (F 9.8)
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Tresorer (o responsable, des del mòbil) | Escriu import, data de la factura, proveïdor, número de factura i categoria | `/gestio/despeses/nova` |
| 2 | Tresorer | Hi posa departament i, si toca, l'activitat o activitats o el projecte de medi ambient | Ídem |
| 3 | Tresorer | Adjunta la factura (foto o PDF). Sense factura, la despesa queda **sense factura** i surt a la llista | Ídem |
| 4 | Sistema | Desa la despesa en estat **per pagar** i ho registra | — |
| 5 | Tresorer | Quan la paga, hi posa el compte, la data de valor i, si en té, el comprovant del banc. El sistema crea el moviment `expense` a la 04 i la despesa passa a **pagada** | Fitxa |
| 6 | Tresorer | En conciliar l'extracte (04), casa la línia del banc amb aquest moviment | `/gestio/tresoreria/conciliacio` |

### P-M09-B Repartir una despesa entre activitats
1. El tresorer tria les activitats i el criteri: per participants, a parts iguals o a mà.
2. El sistema proposa els imports (RN-M09-10) i el tresorer els confirma o els corregeix; la suma no pot passar de l'import.
3. El que no es reparteix queda al departament de la despesa, sense activitat.

### P-M09-C Registrar un ingrés que no és un càrrec
1. El tresorer tria el tipus (ajut, patrocini, donatiu, altres), qui el paga (organisme o empresa), l'import, el compte, la data de valor, el departament i, si cal, el projecte.
2. Si és un ajut, el lliga a la sol·licitud concedida ([apartat d'ajuts](#M09-ajuts-5-processos)) i hi adjunta la resolució. Un ajut **no** pot portar activitat (RN-M09-08).
3. El sistema crea el moviment `other_income` a la 04; el tresorer el concilia amb l'extracte.

### P-M09-D Marge previst i tancament econòmic d'una activitat
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Resp. cursos i sortides o tresorer | Posa els costos previstos per categoria (embarcació, aire…) |
| 2 | Sistema | Mostra el marge previst (RN-M09-06) i avisa si és per sota del llindar (RN-M09-14) |
| 3 | Sistema | Quan el 02 marca l'activitat com a feta (`done`), l'afegeix a «per tancar» |
| 4 | Tresorer | Obre el marge de l'activitat: veu les despeses reals, el lloguer (factura o estimació) i el cost de material, i el que encara impedeix tancar-la (`closing_blockers` del 02, despeses sense factura) |
| 5 | Tresorer | Tanca l'activitat: el sistema calcula el marge real, el congela (RN-M09-07) i crida `activities.mark_closed` |

### P-M09-E Informes per departament, subtipus i projecte
1. El tresorer o la junta tria el període i el departament (o el subtipus o el projecte de medi ambient).
2. El sistema mostra: marges de les activitats tancades, ingressos i despeses sense activitat, ajuts i patrocinis del departament i el total. Els ajuts surten en una línia pròpia, mai dins el marge de cap activitat.
3. Es pot exportar en CSV.

### P-M09-F Factures i rectificatives (quan s'activi)
1. Quan un càrrec es paga, el 09 rep l'esdeveniment `charge.paid` (049) i, si la facturació està activada per a aquell tipus de càrrec, demana la factura al servei homologat amb les dades del client i de les línies.
2. El servei en torna el número, el PDF i el QR; el 09 la desa i la mostra al client a «Les meves factures».
3. Per a una factura manual (per exemple, un patrocini a una empresa), el tresorer escriu el client i les línies.
4. Per a cada devolució d'un cobrament facturat, el tresorer emet la rectificativa des de la llista «devolucions sense rectificativa».
5. Si el servei falla, la factura queda **fallida** i es reintenta des de la cua; surt a la llista de control del període.

### P-M09-G Tancament de període (F 9.11)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Sistema | Mostra la llista de control del període: línies de l'extracte sense conciliar, activitats fetes sense tancar, despeses sense factura, despeses pagades sense conciliar i factures fallides |
| 2 | Tresorer | Resol cada element |
| 3 | Tresorer | Tanca el període quan la llista és buida. A partir d'aquí no s'hi pot fer cap canvi |
| 4 | Administrador | Si cal, el reobre amb motiu; el registre guarda qui, quan i per què |

<a id="M09-6-entitats"></a>
## M09-6 Entitats i camps

Apps Django noves: `expenses` (despeses, proveïdors, altres ingressos i voluntariat), `margins` (costos previstos, marges i períodes) i `invoicing` (factures). Noms de codi en anglès. Imports en cèntims; els marges, amb signe (`BigIntegerField`). Cap camp d'IBAN, de targeta ni de salut.

### ExpenseCategory i Supplier
- `ExpenseCategory`: `name` (únic), `active`. Dades inicials (F §7): embarcació, aire, lloguer, instructor, taxa, instal·lacions, altres.
- `Supplier`: `name` (`CharField(140)`), `tax_id` (`CharField(20)`, opcional, NIF o CIF tal com surt a la factura), `active`. Sense adreça, telèfon ni compte bancari.

### Expense (despesa)
| Camp | Tipus | Restriccions |
|---|---|---|
| `supplier` | FK Supplier (PROTECT) | — |
| `invoice_number` | `CharField(40)` | Únic per proveïdor (si n'hi ha) |
| `invoice_date` | `DateField` | — |
| `category` | FK ExpenseCategory | — |
| `description` | `CharField(200)` | Sense dades de persones |
| `amount_cents` | `PositiveBigIntegerField` | > 0. Total de la factura |
| `tax_cents` | `PositiveBigIntegerField` null | IVA de la factura, si la gestoria el necessita [A verificar: gestoria] |
| `department` | FK departament (00) | Obligatori (RN-62 de la 00) |
| `cost_centre` | FK CostCentre (04) null | Del mateix departament |
| `project` | FK EnvironmentalProject (02) null | Només per a medi ambient |
| `invoice_file` | document de justificació null | PDF, JPG o PNG, xifrat ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)). Sense ell, la despesa és «sense factura» |
| `status` | `to_pay`, `paid`, `annulled` | `annulled` només amb `ExpenseAnnulment` |
| `paid_movement` | FK Movement (04) null | El posa el servei en pagar-la |
| `payment_proof_file` | document de justificació null | Comprovant del banc. Original xifrat; només l'obren el tresorer i la junta ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) |
| `invoice_masked_file`, `payment_proof_masked_file` | document de justificació null | Còpies amb l'IBAN emmascarat (quatre últims dígits), generades per la plataforma ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) |
| `masking_status` | `masked`, `no_iban`, `not_detected` | `not_detected`: el tresorer en puja la còpia emmascarada a mà |
| `recorded_by`, `recorded_at` | — | — |
**Restriccions:** una despesa `paid` no canvia d'import, departament ni proveïdor (es comprova al servei i amb una prova); qualsevol canvi d'una `to_pay` va al registre amb el valor anterior.

### ExpenseAllocation (repartiment) i ExpenseAnnulment (anul·lació)
- `ExpenseAllocation`: `expense`, `activity` (FK Activity del 02), `amount_cents` (> 0), `method` (`participants`, `equal`, `manual`), `created_by`. Únic `(expense, activity)`. Suma ≤ import de la despesa (servei).
- `ExpenseAnnulment` (només INSERT): `expense` (OneToOne), `reason`, `reversal_movement` (FK Movement null, si estava pagada), `annulled_by`, `annulled_at`.

### DocumentIllegibleMark (document il·legible)
No es modifica ni s'esborra: l'únic camp que s'escriu després de crear-la és `replaced_at`, una sola vegada. `expense`, `document` (`invoice`, `payment_proof`), `reason`, `marked_by` (tresorer), `marked_at`, `notified_person` (qui havia pujat el document), `replaced_at` (null; el posa el servei quan arriba el document nou). El document il·legible no s'esborra: es conserva xifrat i deixa de ser el vigent. **Restricció única parcial** `(expense, document)` quan `replaced_at` és buit: com a màxim una marca oberta per document. **Font única de l'estat:** un document és «il·legible», una despesa amb la factura il·legible és «sense factura» i una despesa amb el comprovant de pagament il·legible és **«sense comprovant»**, només mentre hi ha una marca sense `replaced_at`. És un estat derivat: `Expense` no té cap camp per a això i la fila de la despesa no s'escriu mai en marcar un document (RN-M09-11).

### OtherIncome (ingrés que no és un càrrec)
`kind` (`grant`, `sponsorship`, `donation`, `other`), `payer` (`CharField(140)`, organisme o empresa; un donatiu d'una persona: vegeu S-M09-03), `amount_cents`, `department`, `cost_centre` null, `project` null, `activity` (FK null; **prohibit** si `kind = grant`, `CHECK`), `grant_application` (FK de l'apartat d'ajuts, null), `document_file` (resolució o contracte; obligatori si `kind = grant`), `movement` (FK Movement, el posa el servei), `recorded_by`. Només s'anul·la amb motiu, com la despesa.

### PlannedCost (cost previst)
`activity`, `category`, `amount_cents`, `note`, `created_by`. Es pot canviar mentre l'activitat no està tancada; cada canvi va al registre.

### MarginSnapshot (marge congelat)
Només INSERT. `activity`, `income_enrolments_cents`, `other_direct_income_cents`, `direct_costs_cents`, `material_cost_cents`, `margin_cents` (amb signe), `margin_pct_tenths` (enter, dècimes de punt; null si no hi ha ingressos), `participants`, `breakdown` (JSON amb el detall per categoria, comissions, lloguer facturat o estimat), `closed_by`, `closed_at`, `supersedes` (FK self null) i `reopen_reason` (si en substitueix un altre). Vigent = el que no és substituït.

### Period (període) i PeriodEvent
- `Period`: `starts_on`, `ends_on` (sense solapaments, restricció d'exclusió), `status` (`open`, `closed`).
- `PeriodEvent` (només INSERT): `period`, `action` (`close`, `reopen`), `reason` (obligatori per a `reopen`), `actor`, `at`, `checklist` (JSON de la llista de control en aquell moment), `exceptions` (JSON: elements portats al període següent, cadascun amb el seu motiu; buit si es tanca amb la llista buida, RN-M09-26).

### VolunteerHours (hores de voluntariat)
`date`, `hours` (`DecimalField(5,2)`, > 0), `role_label` (`CharField(80)`, funció o rol, **mai el nom**), `department`, `activity` null, `project` null, `description`, `recorded_by`.

### Invoice i InvoiceLine (factura)
- `Invoice`: `series` (`F` ordinària, `R` rectificativa), `number` (del servei), `issued_on`, `customer_person` (FK Person null) o `customer_name` i `customer_tax_id` (empresa), `base_cents`, `tax_cents`, `total_cents`, `charge` (FK càrrec null, únic per sèrie `F`), `rectifies` (FK self null), `refund_movement` (FK Movement null), `provider_ref`, `pdf_file`, `qr_payload`, `status` (`requested`, `issued`, `failed`), `attempts`. Únic `(series, number)`. Mai s'edita ni s'esborra una factura `issued`.
- `InvoiceLine`: `invoice`, `description`, `quantity`, `unit_cents`, `tax_rate` [A verificar: gestoria], `total_cents`.

**Migracions:** reversibles; categories inicials en migració de dades; la restricció d'exclusió dels períodes en una migració pròpia.

### Valors configurables (pantalla d'ajustos, T-M09-26)
Valors de la [regla general](#regles), a la pantalla d'ajustos del mòdul sobre la [peça comuna](#valors-configurables-055) de la [055](decisions/055-ajustos-configurables-i-addendes.md): cada canvi es comprova al servidor (rol i rang), queda al registre amb el valor anterior i, si afecta diners, porta data d'entrada en vigor i avisa per correu el tresorer i la junta (RN-AJ-03 i RN-AJ-04). Els valors inicials són els supòsits que ja hi havia; les preguntes obertes continuen obertes.

| Clau de l'ajust | VC | Valor inicial | Rang vàlid | Qui el canvia | Data d'entrada en vigor |
|---|---|---|---|---|---|
| `margin.low_margin_threshold_cents` | VC-31 | 0 | Qualsevol import (també negatiu) | Tresorer | — |
| `margin.period_length` | VC-32 | `monthly` (mensual) | `monthly`, `quarterly` (trimestral) | Tresorer | Només als períodes nous (RN-M09-28) |
| `billing.enabled_charge_kinds` | VC-34 | Cap (facturació desactivada) | Quota, inscripció, llicència, material | Administrador, per decisió de la junta (RN-M09-19) | Sí |

Categories de despesa i proveïdors (VC-33) ja són dades. **No s'aplica** VC-35 (text d'ajuda de la pujada de documents): és la mitigació d'un risc de dades fora de la UE (RN-M09-25 i [051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) i es queda al codi, com la seguretat.

<a id="M09-7-regles"></a>
## M09-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M09-01 | **Marge operatiu = Inscripcions + Altres ingressos directes − Costos directes − Cost de material** | CLAUDE.md; F §7 |
| RN-M09-02 | **Inscripcions** = ingressos de la 04 dels càrrecs pagats de l'activitat amb origen `activities`, menys les devolucions d'aquests cobraments. Un moviment anul·lat no compta (RN-T25) | F §7; RN-T10 |
| RN-M09-03 | **Altres ingressos directes** = càrrecs pagats de l'activitat amb un altre origen (per exemple, el lloguer cobrat al participant, RN-M03-11) i patrocinis amb activitat, menys les seves devolucions. Mai ajuts | F §7 |
| RN-M09-04 | **Costos directes** = repartiments de despeses a l'activitat + comissions dels cobraments de l'activitat (013, RN-64) + lloguer de material: la factura del centre si s'ha registrat i, si no, l'estimació del 03; **mai totes dues** | F §7; RN-M03-10 |
| RN-M09-05 | **Cost de material** = cost d'ús del material del club que dona `equipment.activity_material_cost` (`club_use_cents`) | RN-M03-10 |
| RN-M09-06 | **Marge previst** (activitat no tancada): inscripcions = preus de les inscripcions vives (pendents de pagament i pagades); costos = per a cada categoria, els reals si n'hi ha i, si no, els previstos; comissions, només les reals | F §7 |
| RN-M09-07 | **Marge real**: es calcula en tancar l'activitat i es **congela** (`MarginSnapshot`). Un moviment posterior lligat a l'activitat (per exemple, una devolució tardana) no el canvia: surt com a **«ajust posterior»** al costat del marge congelat i compta al període on entra. Això inclou una factura que arriba tard (L-M09-02) i els moviments d'origen extern de la 053, que a més es marquen com a «moviments tardans» (RN-M09-24). Només reobrint el període (administrador, amb motiu, per un error de la feina del propi període) es fa un marge nou que substitueix l'anterior; aquest marge no inclou els moviments tardans (RN-M09-24) | F §7 i §9.11 |
| RN-M09-08 | Els ajuts **no s'imputen a cap activitat**: compten al departament i, si cal, al subtipus o projecte (com a molt, al total de medi ambient) | F §5 i §7; 20/10/2026 |
| RN-M09-09 | Tota despesa té categoria, departament i factura adjunta. Sense factura és «sense factura», surt a la llista, avisa el tresorer i **bloqueja el tancament del període** | F §7 |
| RN-M09-10 | Repartiment: la suma dels repartiments no passa de l'import. **Per participants:** proporcional als assistents de cada activitat (si no hi ha llista, a les inscripcions confirmades) [A validar: tresorer, S-M09-02]. **A parts iguals** o **a mà**. Arrodoniment com VT-05: cada part a la baixa i els cèntims que sobren, un a un, a les activitats amb més participants (empat: la més antiga) | F §7; VT-05 |
| RN-M09-11 | Una despesa pagada no es modifica: s'anul·la amb motiu i usuari (contramoviment a la 04, anul·lació manual) i se'n registra una de nova. Si la despesa és d'un període tancat, l'anul·lació i la despesa nova porten data del període obert (RN-T29); amb data del període tancat, la 04 les rebutja (RN-T30). Una despesa per pagar es pot corregir; cada canvi va al registre | CLAUDE.md; RN-T07; [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md); [053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md) |
| RN-M09-12 | Una activitat només es tanca econòmicament si `activities.closing_blockers` és buit (inclou el material pendent del 03) i no té cap despesa sense factura. Ho fa el tresorer | F §5 i §7; [M02-7](#M02-7-regles) |
| RN-M09-13 | **Percentatge** = marge ÷ (inscripcions + altres ingressos directes), amb una xifra decimal i arrodoniment a la meitat cap amunt; sense ingressos, no es mostra. **Per participant** = marge ÷ assistents (si no n'hi ha llista, confirmats), arrodonit al cèntim | F §7 |
| RN-M09-14 | **Avís de marge baix:** quan el marge previst és per sota del llindar, avís al responsable de l'activitat i al tresorer (correu i app, sense push), un sol cop per cada canvi de previsió. Llindar (ajust `margin.low_margin_threshold_cents`) per defecte: 0 € (l'activitat no cobreix costos) [A validar: junta, S-M09-04] | F §7 |
| RN-M09-15 | **Període:** mensual (ajust `margin.period_length`, mensual o trimestral; RN-M09-28) [A validar: tresorer, S-M09-05]. Es tanca només amb la llista de control buida: línies de l'extracte sense conciliar amb data dins el període, activitats acabades dins el període sense tancar, despeses sense factura, despeses pagades sense conciliar i factures fallides. També es pot tancar amb **excepcions documentades** (RN-M09-26) | F §7 i §9.11 |
| RN-M09-16 | Un període tancat no admet cap registre nou del 09 (despesa, altre ingrés o anul·lació manual) amb data dins el període: la 04 el rebutja (RN-T30); el que ja hi ha no canvia. Una correcció es fa amb una anul·lació i un registre nou al període obert. **Els moviments d'origen extern** (pagaments del 05b, devolucions, retorns, comissions del banc, remeses i liquidacions) **no es rebutgen mai**: entren al període obert i guarden la data de valor original a `original_value_date` (RN-T31); al marge compten al període on entren, com un ajust posterior (RN-M09-07). Només l'administrador reobre un període, amb motiu, i queda al registre; en reobrir-lo, s'avisa per correu el tresorer i la junta [A validar: junta, S-M09-13]. Reobrir és només per als errors de la feina del propi període (per exemple, un repartiment o un tancament mal fet), no per al que arriba tard | F §7; [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md); [053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md) |
| RN-M09-17 | **Facturació:** el 09 no numera. Demana la factura al servei homologat a través de l'adaptador i en desa el número, el PDF i el QR. Comprova que cada sèrie no té salts ni duplicats i, si en troba, avisa el tresorer. Idempotent per càrrec: un càrrec té com a màxim una factura ordinària | F §7 |
| RN-M09-18 | Cada devolució d'un cobrament facturat té la seva rectificativa (total o parcial) lligada a la factura original. Cap factura emesa s'edita ni s'esborra | F §7 |
| RN-M09-19 | Què es factura, amb quin IVA i si el club és dins de Verifactu [A verificar: gestoria, P-02, P-47]. Mentre no es respongui, la facturació està **desactivada** i el justificant és el rebut del 05b. Quan la junta l'activi, s'activa per tipus de càrrec (ajust `billing.enabled_charge_kinds`, amb data d'entrada en vigor) (quota, inscripció, llicència, material) | 22/10/2026; P-47 |
| RN-M09-20 | Llicències: el pagament a la federació és una despesa de categoria «taxa» al departament de les llicències («General / Llicències», provisional, S-M04-07) [A validar: tresorer]. El marge de la llicència d'un soci és 0 abans de comissions | 20/10/2026; [M06-7](#M06-7-regles) |
| RN-M09-21 | Hores de voluntariat: opcionals, per funció i mai per persona; no es valoren en euros dins el marge [A validar: junta] | F §7 |
| RN-M09-22 | Tots els imports en cèntims (enters); els marges amb signe. Cap càlcul amb coma flotant | CLAUDE.md |
| RN-M09-23 | **Documents de justificació** (factures de despesa, comprovants del banc, paquets): xifrats a l'emmagatzematge de la UE; només els obren el tresorer i la junta; cap eina d'IA els rep; la plataforma en fa una còpia amb l'IBAN emmascarat i conserva l'original. Qui puja una factura des del mòbil no la pot tornar a obrir [A validar: junta] | [051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md) |
| RN-M09-24 | **Reobrir no mou mai els moviments de la 053.** Els moviments d'origen extern que van entrar al període obert amb una `original_value_date` dins el període reobert s'hi queden, amb aquesta data. El marge recalculat del període reobert (RN-M09-07) no els inclou i els mostra a part com a «moviments tardans» | [053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md); RN-T31 |
| RN-M09-25 | **Vista prèvia i document il·legible.** En pujar una factura o un comprovant (també des del mòbil), el formulari en mostra una vista prèvia abans de desar-lo. La vista prèvia passa **només al navegador**: el fitxer no s'envia al servidor fins que la persona prem «Desa» i no es guarda enlloc (ni al servidor, ni a la memòria cau, ni a l'emmagatzematge del navegador). La pantalla de pujada mostra un **text d'ajuda**: «Si fas la foto amb la càmera, queda a la galeria del telèfon i es pot copiar a un núvol fora de la UE. Esborra-la de la galeria (i de la paperera) després de pujar-la.» La plataforma no pot esborrar res del telèfon (risc a [M09-13](#M09-13-riscos)) [A validar: junta i informàtica]. Un cop desat, el tresorer pot marcar el document com a **«il·legible»**, amb motiu: la persona que l'havia pujat rep un avís (correu i app, sense push) per tornar-lo a pujar, i l'avís no porta ni el document ni cap enllaç per obrir-lo. Mentre no arriba el nou, la despesa compta com a «sense factura» (RN-M09-09) si el document il·legible és la factura, i com a «sense comprovant» si és el comprovant de pagament: el paquet d'ajuts l'exclou amb el motiu «comprovant il·legible» i en dona l'avís (RN-M09A-11). Només hi pot haver una marca oberta per document. «Il·legible», «sense factura» i «sense comprovant» es deriven només de `DocumentIllegibleMark` sense `replaced_at`: marcar un document no escriu mai a la fila d'`Expense`, tampoc si és pagada (RN-M09-11). Cap rol fora del tresorer i la junta obre mai un document ja desat (RN-M09-23) | [051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md); 27/10/2026 |
| RN-M09-26 | **Tancar amb excepcions documentades** [A validar: tresorer, S-M09-15]. Si la llista de control no és buida, el tresorer pot tancar el període indicant, element per element, quins es porten al període següent, cadascun amb motiu obligatori. Les excepcions queden a `PeriodEvent.exceptions` i al registre d'activitat, i cada element portat surt a la llista de control del període següent fins que es resol: aquell període no es pot tancar sense resoldre'l o tornar-lo a portar amb un motiu nou. Un element sense excepció continua bloquejant el tancament | 27/10/2026 |
| RN-M09-27 | **Registre i escriptura única de la marca d'il·legible** (addenda mínima, 28/10/2026). Marcar un document i substituir-lo creen cadascun una entrada al registre d'activitat **de la `DocumentIllegibleMark`** (mai de la fila d'`Expense`), amb qui, quan, quin document (`expense`, `document`) i el motiu o el document nou. `replaced_at` només passa de buit a una data una vegada i no es canvia ni s'esborra mai: ho fa complir un **activador de PostgreSQL** (com l'activador «només INSERT» dels moviments de la 04), que rebutja qualsevol altre UPDATE i qualsevol DELETE, i també el servei | CLAUDE.md; RN-M09-25 |
| RN-M09-28 | **Canvi de la durada del període** ([055](decisions/055-ajustos-configurables-i-addendes.md), condició b). Un canvi de `margin.period_length` només s'aplica als períodes que es creen després: els que ja existeixen, oberts o tancats, no canvien. El període nou comença **l'endemà** del darrer període existent i dura un mes o tres a partir d'aquell dia, sense forats ni solapaments (restricció d'exclusió de `Period`) | 28/10/2026 |

**Exemples numèrics** (dades inventades)
- **Sortida d'un dia a les Medes, 10 participants a 60 € (F §7):** inscripcions 10 × 6000 = **60.000**; embarcació −25.000; aire 20 × 600 = −12.000; material llogat 3 × 2500 = −7500; material del club 7 × 350 = −2450; instructor voluntari 0. Marge = 60.000 − 25.000 − 12.000 − 7500 − 2450 = **13.050 cèntims (130,50 €)**. Percentatge 13.050 ÷ 60.000 = 21,75 % → **21,8 %**. Per participant 13.050 ÷ 10 = **1305 (13,05 €)**. Els ajuts no hi surten.
- **Amb comissions:** si els 10 cobraments tinguessin una comissió inventada de 30 cèntims cadascun (la real és [A verificar: PaynoPain]), els costos directes pujarien 300 i el marge seria **12.750**.
- **Lloguer sense duplicar (RN-M03-10):** abans de la factura del centre, el 09 resta l'estimació de 7500; quan es registra la factura de 7800, resta 7800 i deixa de restar l'estimació. Marge real 13.050 − 300 = **12.750**; la desviació de 300 surt al detall.
- **Repartiment per participants:** factura d'embarcació de 50.000 per a dues sortides amb 10 i 15 assistents → **20.000 i 30.000**.
- **Arrodoniment:** 10.000 entre tres sortides de 7 assistents cadascuna → 3333 + 3333 + 3333 = 9999; el cèntim que sobra va a la més antiga → **3334, 3333 i 3333**.
- **Marge previst amb avís:** preu 4500 × 8 inscripcions = 36.000; embarcació prevista 25.000, aire previst 12.000 → marge previst **−1000**, per sota de 0 → avís.
- **Departament de medi ambient (informe):** marges de sortides tancades 13.050 + 8200 = 21.250; despeses del departament sense activitat −4000; ajut cobrat +300.000 en una línia pròpia. Total del departament = 21.250 − 4000 + 300.000 = **317.250**; el marge de cada sortida no canvia.

<a id="M09-8-serveis"></a>
## M09-8 Serveis i interfícies (contracte)

Cap altra app escriu als models del 09. Tots els serveis que escriuen deixen registre i rebutgen les dates dins un període tancat (`PeriodClosed`).

**Ofereix**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `expenses.record_expense(data, actor)` | despesa | `Expense` | `PeriodClosed`, `InvalidDepartment` | Vistes |
| `expenses.pay(expense, account, value_date, proof, actor)` | — | despesa `paid` i moviment `expense` (04) | `AlreadyPaid`, `PeriodClosed` | Vistes |
| `expenses.annul(expense, reason, actor)` | — | anul·lació i, si estava pagada, contramoviment (04) | `PeriodClosed` | Vistes |
| `expenses.allocate(expense, activities, method, actor)` | — | repartiments | `AllocationExceedsAmount` | Vistes |
| `expenses.record_other_income(data, actor)` | tipus, pagador, import, compte, data, departament, projecte, sol·licitud d'ajut | `OtherIncome` i moviment `other_income` (04) | `GrantWithActivity`, `PeriodClosed` | Vistes; apartat d'ajuts |
| `expenses.expenses_for(filters)` | departament, projecte, període, categoria | despeses amb estat de factura i comprovant (lectura) | — | Apartat d'ajuts; 08 |
| `margins.activity_margin(activity, kind)` | activitat, `forecast` o `real` | detall de RN-M09-01 | — | Fitxa de l'activitat (02), 08 |
| `margins.close_activity(activity, actor)` | — | `MarginSnapshot` i `activities.mark_closed` | `ClosingBlocked`, `MissingInvoices` | Vistes |
| `margins.department_report(period, department, group_by)` | — | ingressos, despeses, marges i ajuts (lectura) | — | 08; apartat d'ajuts |
| `margins.is_period_closed(date)` | data | sí o no | — | Guarda de la 04 (si s'aprova); el mateix 09 |
| `invoicing.on_charge_paid(event)` | esdeveniment `charge.paid` | factura `requested` i petició a la cua (si la facturació està activada per aquell tipus) | — | Subscriptor ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) |
| `invoicing.issue_manual(customer, lines, actor)`, `invoicing.issue_rectification(invoice, refund_movement, reason, actor)` | — | factura | `InvoicingDisabled`, `AlreadyRectified` | Vistes |
| `invoicing.invoices_for(person)` | persona | factures (lectura) | — | Compte personal; enllaç del convidat |
| `expenses.export_personal_data(person)`, `invoicing.export_personal_data(person)`, `invoicing.block(person)` | persona | — | — | 00 (RGPD): les factures es bloquegen, no s'anonimitzen (028) |

**Adaptador de facturació** (`InvoicingProvider`): `issue(invoice_data) → {number, pdf, qr, provider_ref}`, `rectify(...)`, `status(provider_ref)`. Implementacions: `FakeInvoicingProvider` (proves i desenvolupament) i la del servei homologat que triï la gestoria [A verificar: gestoria]. El servei ha de tractar les dades dins la UE ([035](decisions/035-dades-nomes-dins-ue.md)) i entrar al [registre de proveïdors](proveidors-i-dades-ue.md).

**Consumeix**
| Servei | Mòdul | Per a què |
|---|---|---|
| `treasury.record_expense`, `treasury.record_other_income`, `treasury.reverse`, `treasury.register_movement_guard` | 04 ([addenda](#M04-addenda-050), [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md)) | Moviments de despesa i d'altres ingressos, anul·lacions, guarda de període |
| `treasury.movements(filters)`, `treasury.balance` | 04 | Ingressos, comissions i devolucions de cada activitat; llista de control |
| Lectura de càrrecs per activitat i origen | 00 | Inscripcions i altres ingressos directes |
| `activities.get_activity`, `activities.enrolments`, `activities.attendance_for`, `activities.closing_blockers`, `activities.mark_closed`; senyal `activity_done` | 02 | Participants, tancament |
| `equipment.activity_material_cost`, `equipment.rentals_for`, `equipment.reviews_with_cost` | 03 | Cost de material, lloguers i revisions |
| `events.subscribe("charge.paid", invoicing.on_charge_paid)` | 05b ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) | Factura d'un cobrament |
| `files.store_private`, `mail.send`, `notices.post`, `audit.record`, `permissions.require`, cua de tasques | 00 | Fitxers, avisos, registre, permisos, reintents |

**Rutes (administració).** `/gestio/despeses`, `/gestio/despeses/nova`, `/gestio/despeses/{id}`, `/gestio/despeses/sense-factura`, `/gestio/ingressos`, `/gestio/marges`, `/gestio/marges/{activitat}`, `/gestio/informes/departaments`, `/gestio/factures`, `/gestio/factures/{id}`, `/gestio/periodes`, `/gestio/voluntariat`, `/gestio/despeses/categories`, `/gestio/despeses/proveidors`. Compte personal: `/socis/factures`. Convidat: dins l'enllaç de la 00. Cap ruta pública.

<a id="M09-9-criteris"></a>
## M09-9 Criteris d'acceptació i casos límit

- **CA-M09-01** Donat una despesa sense factura, quan es desa, llavors queda «sense factura», surt a `/gestio/despeses/sense-factura` i el tresorer en rep l'avís.
- **CA-M09-02** Donat una despesa per pagar, quan el tresorer la paga, llavors es crea exactament un moviment `expense` a la 04 amb el mateix import i departament, i la despesa passa a `paid`.
- **CA-M09-03** Donat una despesa pagada, quan es vol canviar l'import, llavors es rebutja; quan s'anul·la amb motiu, es crea el contramoviment i la despesa passa a `annulled`.
- **CA-M09-04** Donat una factura de 50.000 i dues sortides amb 10 i 15 assistents, quan es reparteix per participants, llavors queden 20.000 i 30.000.
- **CA-M09-05** Donat 10.000 entre tres sortides de 7 assistents, quan es reparteix, llavors queden 3334, 3333 i 3333 i la suma és 10.000.
- **CA-M09-06** Donat un repartiment que suma més que l'import, quan es desa, llavors es rebutja.
- **CA-M09-07** Donat la sortida de l'exemple de [M09-7](#M09-7-regles), quan es calcula el marge real, llavors surt 13.050, 21,8 % i 1305 per participant.
- **CA-M09-08** Donat un lloguer estimat de 7500 i una factura del centre de 7800, quan es calcula el marge, llavors només resta 7800 i mostra la desviació de 300.
- **CA-M09-09** Donat un ajut, quan s'hi vol posar una activitat, llavors es rebutja (també a la base de dades).
- **CA-M09-10** Donat una activitat amb una inscripció pendent de pagament o amb material pendent, quan el tresorer la vol tancar, llavors es rebutja amb els motius.
- **CA-M09-11** Donat una activitat tancada, quan arriba una devolució posterior, llavors el marge congelat no canvia i la devolució surt com a ajust posterior al període on entra.
- **CA-M09-12** Donat un marge previst de −1000 i el llindar de 0, quan es desa la previsió, llavors el responsable i el tresorer reben un sol avís; si la previsió no canvia, no se'n repeteix cap.
- **CA-M09-13** Donat un període amb una despesa sense factura, quan es vol tancar sense cap excepció, llavors es rebutja i la llista de control la mostra.
- **CA-M09-29** Donat un període amb dues línies de l'extracte sense conciliar, quan el tresorer el tanca portant-ne una al període següent amb motiu i l'altra sense, llavors es rebutja; quan les porta totes dues amb motiu, es tanca, `PeriodEvent.exceptions` i el registre guarden els dos elements amb el seu motiu i tots dos surten a la llista de control del període següent, que no es pot tancar fins que es resolen o es tornen a portar.
- **CA-M09-14** Donat un període tancat, quan algú registra una despesa amb data dins el període, llavors es rebutja (`PeriodClosed`); quan l'administrador el reobre amb motiu, s'accepta i el registre guarda la reobertura, i el tresorer i la junta reben un correu.
- **CA-M09-22** Donat una despesa pagada d'un període tancat, quan el tresorer l'anul·la, llavors el contramoviment i la despesa nova porten data del període obert i el moviment original no canvia.
- **CA-M09-25** Donat un període tancat, quan arriba una comissió del banc amb data dins el període, llavors no es rebutja, entra al període obert amb `original_value_date` i surt a l'informe del període obert com a ajust posterior.
- **CA-M09-26** Donat un període reobert per l'administrador amb una comissió del banc que hi té `original_value_date` però que va entrar al període obert, quan es recalcula el marge del període reobert, llavors la comissió no s'hi inclou, surt a la llista de «moviments tardans» i continua al període obert amb la mateixa data de valor.
- **CA-M09-23** Donat un comprovant en PDF amb un IBAN, quan es puja, llavors l'original es desa xifrat, es genera una còpia amb només els quatre últims dígits i cap pantalla mostra l'IBAN; un administrador o un responsable que vol obrir l'original rep «no trobat».
- **CA-M09-24** Donat una foto d'un comprovant on no es detecta cap IBAN, quan es puja, llavors queda `not_detected` i surt a la llista del tresorer per pujar-ne la còpia emmascarada.
- **CA-M09-27** Donat un responsable que tria la foto d'una factura al mòbil, quan veu la vista prèvia i surt sense prémer «Desa», llavors el servidor no ha rebut cap fitxer i no queda res desat; quan prem «Desa», el document es desa xifrat i, si després vol tornar a obrir-lo, rep «no trobat».
- **CA-M09-28** Donat una factura desada, quan el tresorer la marca «il·legible» amb motiu, llavors la persona que l'havia pujat rep un avís sense enllaç al document, la despesa surt a «sense factura» perquè hi ha una `DocumentIllegibleMark` sense `replaced_at`, i la marca queda al registre; quan puja el document nou, la marca rep `replaced_at`, la despesa en surt i l'il·legible es conserva xifrat.
- **CA-M09-30** Donat una despesa pagada amb la factura desada, quan el tresorer marca la factura «il·legible», llavors la fila d'`Expense` no canvia (mateixos valors i mateixa data de modificació) i el registre d'activitat no té cap entrada nova per a aquesta fila; només n'hi ha una per a la `DocumentIllegibleMark` creada.
- **CA-M09-31** Donat un document marcat il·legible i després substituït, quan es consulta el registre d'activitat, llavors hi ha dues entrades de la `DocumentIllegibleMark` (marca i substitució) amb qui, quan, la despesa, el document i el motiu, i cap de la fila d'`Expense`.
- **CA-M09-33** Donat una factura amb una marca d'il·legible oberta, quan el tresorer la vol tornar a marcar (també amb una consulta SQL directa), llavors es rebutja; quan el document s'ha substituït (`replaced_at` ple), el nou es pot marcar.
- **CA-M09-34** Donat una despesa pagada lligada a un ajut, quan el tresorer marca il·legible el comprovant de pagament, llavors la despesa surt com a «sense comprovant», la fila d'`Expense` no canvia, i el paquet de justificació l'exclou amb el motiu «comprovant il·legible» i el tresorer en rep l'avís; quan es puja el comprovant nou, el paquet següent la torna a incloure.
- **CA-M09-35** (CA-AJ-06) Donat períodes mensuals fins al darrer, que acaba el 31/03, quan el tresorer canvia la durada a trimestral, llavors el període nou va de l'1/04 al 30/06; cap dia queda fora de cap període ni dins de dos, i els períodes existents no canvien.
- **CA-M09-32** Donat una marca amb `replaced_at` ple, quan una consulta SQL directa intenta canviar-lo, buidar-lo, canviar un altre camp o esborrar la fila, llavors PostgreSQL ho rebutja; donat `replaced_at` buit, passar-lo a una data s'accepta una sola vegada.
- **CA-M09-15** Donat un tresorer, quan vol reobrir un període, llavors es rebutja.
- **CA-M09-16** Donat la facturació activada per a inscripcions i un esdeveniment `charge.paid` repetit, quan arriba dues vegades, llavors hi ha una sola factura.
- **CA-M09-17** Donat el `FakeInvoicingProvider` que torna un número que salta un valor, quan es desa, llavors el tresorer rep l'avís de salt a la sèrie.
- **CA-M09-18** Donat una devolució parcial d'un cobrament facturat, quan el tresorer emet la rectificativa, llavors queda lligada a la factura original per l'import de la devolució.
- **CA-M09-19** Donat la facturació desactivada, quan es paga un càrrec, llavors no es crea cap factura i el rebut del 05b continua sent el justificant.
- **CA-M09-20** Donat l'informe de medi ambient de l'exemple, quan es genera, llavors l'ajut surt en una línia pròpia i el total és 317.250.
- **CA-M09-21** Donat cada cel·la de [M09-4](#M09-4-rols), quan el rol prova l'acció, llavors el resultat coincideix.

**Casos límit**
| # | Cas | Comportament |
|---|---|---|
| L-M09-01 | Una factura serveix per a una activitat i per a despeses generals | Es reparteix una part i la resta queda al departament |
| L-M09-02 | Una factura arriba quan el període ja és tancat | No es reobre el període. La despesa (`expense`) entra al període obert, lligada a l'activitat, i es mostra com a «ajust posterior» al costat del marge congelat (RN-M09-07). Reobrir queda per als errors de la feina del propi període (RN-M09-16) |
| L-M09-03 | Una activitat sense cap ingrés (sortida gratuïta) | Marge negatiu, sense percentatge |
| L-M09-04 | Una activitat cancel·lada amb despeses ja fetes | Es pot tancar econòmicament; el marge mostra la pèrdua |
| L-M09-05 | Un ajut que cobreix dos departaments | Dos ingressos, un per departament, lligats a la mateixa sol·licitud |
| L-M09-06 | El servei de facturació no respon | Factura `failed`, reintents a la cua, avís i element a la llista de control |
| L-M09-07 | Esborrat RGPD d'un client amb factures | Les factures es bloquegen fins al final del termini legal (028; Q-14) |
| L-M09-08 | Una devolució sense factura original (facturació activada després del cobrament) | No es fa rectificativa; surt a la llista amb el motiu |

<a id="M09-10-tasques"></a>
## M09-10 Tasques (per dependències, sense dates)

| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M09-01 | Wireframes que falten (vegeu [M09-5](#M09-5-processos)) | M | `design/wireframes/` | — | Revisats; contrast i estats amb símbol |
| T-M09-02 | Registrar el bloqueig de període tancat a la 04 i fer servir els serveis de l'addenda ([050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md)) | S | `apps/margins/periods.py` | T-M04-20 | CA-T19; CA-T22; CA-M09-22; CA-M09-25 |
| T-M09-03 | Categories de despesa i proveïdors | S | `apps/expenses/models.py`, migracions | T-M09-02 | Dades inicials de F §7 |
| T-M09-04 | Despesa: model, factura adjunta, estats i registre de canvis | M | `apps/expenses/` | T-M09-03 | CA-M09-01 |
| T-M09-05 | Pagar i anul·lar una despesa amb moviments de la 04 | M | `apps/expenses/services.py` | T-M09-04 | CA-M09-02, 03 |
| T-M09-06 | Formulari mòbil de despesa amb foto i vista prèvia només al navegador (RN-M09-25) | S | vistes, plantilles | T-M09-04 | Prova al mòbil (B5); CA-M09-27 |
| T-M09-07 | Repartiment entre activitats amb arrodoniment | M | `apps/expenses/allocation.py` | T-M09-04, T-M02-16 | CA-M09-04, 05, 06 |
| T-M09-08 | Altres ingressos (ajut, patrocini, donatiu) | S | `apps/expenses/income.py` | T-M09-02 | CA-M09-09 |
| T-M09-09 | Costos previstos per activitat | S | `apps/margins/models.py` | T-M09-03 | Registre de canvis |
| T-M09-10 | Càlcul del marge (funció pura, sense base de dades) | M | `apps/margins/calc.py` | — | Exemples de [M09-7](#M09-7-regles) amb cobertura completa |
| T-M09-11 | Marge previst i real d'una activitat amb dades de 02, 03, 04 i 09 | M | `apps/margins/services.py` | T-M09-07, T-M09-09, T-M09-10, T-M03-13 | CA-M09-07, 08 |
| T-M09-12 | Tancament econòmic i `MarginSnapshot` | M | `apps/margins/closing.py` | T-M09-11, T-M02-22 | CA-M09-10, 11 |
| T-M09-13 | Avís de marge baix | S | `apps/margins/alerts.py` | T-M09-11 | CA-M09-12 |
| T-M09-14 | Informes per departament, subtipus i projecte, i CSV | M | `apps/margins/reports.py` | T-M09-11, T-M09-08 | CA-M09-20 |
| T-M09-15 | Llista de despeses sense factura i avisos | S | vistes | T-M09-04 | CA-M09-01 |
| T-M09-16 | Períodes: llista de control, tancament (també amb excepcions documentades), reobertura i guarda | M | `apps/margins/periods.py` | T-M09-05, T-M09-12, T-M09-02 | CA-M09-13, 14, 15, 29 |
| T-M09-17 | Hores de voluntariat | S | `apps/expenses/volunteering.py` | T-M09-03 | Sense noms |
| T-M09-18 | Adaptador `InvoicingProvider` i `FakeInvoicingProvider` | M | `apps/invoicing/providers/` | — | Proves de contracte |
| T-M09-19 | Factura d'un cobrament (subscriptor de `charge.paid`) i factura manual; control de salts | M | `apps/invoicing/` | T-M09-18, T-M05b-21 | CA-M09-16, 17, 19 |
| T-M09-20 | Rectificatives des de la llista de devolucions | S | `apps/invoicing/` | T-M09-19 | CA-M09-18 |
| T-M09-21 | «Les meves factures» (soci i convidat) | S | vistes | T-M09-19 | Permisos per objecte |
| T-M09-22 | Permisos per rol i per objecte | S | `apps/*/permissions.py` | T-M09-04 | CA-M09-21 |
| T-M09-23 | Dades inventades i proves de principi a fi (inscripció → pagament → despesa → repartiment → tancament → informe → període) | L | `fixtures/`, `tests/` | T-M09-05 a T-M09-16 | Totes en verd |
| T-M09-24 | Guia del tresorer (despeses, marge, tancament, factures) | S | `docs/` | T-M09-23 | Revisada |
| T-M09-25 | Magatzem de documents de justificació: xifratge, accés només del tresorer i la junta, còpia amb l'IBAN emmascarat i marca «il·legible» amb avís, derivada de `DocumentIllegibleMark` sense escriure a la despesa ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) | M | `apps/expenses/documents.py` | T-M09-04 | CA-M09-23, 24, 28, 30, 31, 32, 33, 34 (activador de `replaced_at` i restricció única parcial en una migració pròpia, RN-M09-27) |
| T-M09-26 | Pantalla d'**ajustos** del mòdul: els seus valors (bloc «Valors configurables» de la secció 6), amb valor inicial, rang vàlid, rol que el canvia, registre (qui, quan, valor anterior) i data d'entrada en vigor si afecta diners; només per als rols amb permís, també els de l'apartat d'ajuts | S | `apps/margins/settings.py`, `apps/grants/settings.py`, vistes | T-M09-22, T-M09A-12; T-AJ-02 (peça comuna d'ajustos, [055](#valors-configurables-055)) | Per valor: fora de rang es rebutja; el canvi queda al registre; un rol sense permís rep «no trobat»; un canvi de diners no toca el que ja s'ha demanat; CA-M09-35 (prova de la durada del període, condició b de la 055) |

La facturació real (servei homologat) espera la resposta de la gestoria: T-M09-18 a T-M09-21 es poden fer amb el `FakeInvoicingProvider`, però la facturació no s'activa en producció fins que es respongui P-02 i P-47.

<a id="M09-11-proves"></a>
## M09-11 Pla de proves

- **Unitàries (B1), cobertura completa dels càlculs econòmics:** fórmula del marge, previst i real, percentatge i per participant, arrodoniment del repartiment, lloguer sense duplicar, ajust posterior, moviments tardans en reobrir, avís de marge baix.
- **Base de dades:** `CHECK` de l'ajut sense activitat; restricció d'exclusió dels períodes; unicitat de la factura per càrrec i per número de sèrie; activador «només INSERT» de la 04 amb els tipus nous.
- **Integració:** inscripció pagada amb `FakeProvider` → ingrés (04) → despesa repartida → tancament → `MarginSnapshot` → informe de departament; esdeveniment `charge.paid` repetit → una sola factura amb `FakeInvoicingProvider`.
- **Contracte amb el 03:** `activity_material_cost` amb l'exemple de [M03-7](#M03-7-regles), amb factura i sense.
- **Període:** cada servei que escriu rebutja una data dins un període tancat.
- **Permisos (B4):** una prova per cel·la de [M09-4](#M09-4-rols); un soci només descarrega les seves factures.
- **Accessibilitat i dispositius (B5, B8):** formulari de despesa amb foto al mòbil; marges negatius amb símbol i text, no només color.
- **Dades:** només inventades.

<a id="M09-12-seguretat"></a>
## M09-12 Seguretat i RGPD

- **Factures emeses:** porten nom i document del client; el servei de facturació ha de ser dins la UE amb contracte d'encarregat [A verificar: gestoria i informàtica]. Les factures no s'anonimitzen: es bloquegen fins al final del termini legal (028; Q-14 [A validar: gestoria]).
- **Factures de despesa i comprovants:** fitxers privats (00), servits amb enllaç signat i caducitat curta; mai públics.
- **Documents de justificació amb IBAN** ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)): la [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md) cobreix els IBAN i mandats dels socis. Factures, comprovants i paquets es guarden xifrats a la UE, només els obren el tresorer i la junta, cap eina d'IA els rep i la plataforma en fa una còpia amb l'IBAN emmascarat (RN-M09-23). Cap camp, pantalla ni exportació del 09 mostra un IBAN com a text.
- **Proveïdors:** només nom i NIF de la factura. Un professional autònom és una persona: mateix tractament mínim.
- **Voluntariat:** per funció, mai per nom.
- **Registre:** despeses, repartiments, anul·lacions, ingressos, previsions, tancaments, reobertures i factures, amb el valor anterior.
- **Permisos:** comprovats al servidor per rol i per objecte; el tancament i la reobertura de període amb TOTP (administració).

<a id="M09-13-riscos"></a>
## M09-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| No es detecta l'IBAN en una foto d'un comprovant | Mitjà: còpia no emmascarada | Estat `not_detected` i còpia emmascarada a mà (CA-M09-24) | Tresorer |
| Factures que no arriben o es perden | Alt per justificar ajuts | Avís de «sense factura», bloqueig del tancament, foto des del mòbil | Tresorer |
| No se sap si el club ha de facturar ni amb quin servei | Mitjà: la facturació no es pot activar | Adaptador i `FakeInvoicingProvider`; rebuts del 05b mentrestant | Gestoria |
| Comptar el lloguer dues vegades | Alt per al marge | RN-M09-04 i prova de contracte amb el 03 | Tresorer |
| Períodes tancats que s'han de tocar sovint | Mitjà | Reobertura per l'administrador amb motiu; períodes mensuals | Tresorer |
| Una foto d'una factura o d'un comprovant feta amb la càmera queda a la galeria del telèfon i es pot copiar a un núvol fora de la UE (comprovants amb IBAN, 051; requisit UE, 035) [A validar: junta i informàtica] | Mitjà: dades fora de la UE i fora del control del club | Text d'ajuda a la pujada que demana esborrar la foto (RN-M09-25); informàtica comprova si la càmera oberta des del navegador desa la foto a la galeria en cada sistema; la junta decideix si n'hi ha prou o cal una norma per als responsables | Junta i informàtica |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M09-01 | El responsable de l'activitat i el de material poden registrar despeses (MG1) | Sí, només de les seves activitats o del material | Junta |
| S-M09-02 | Criteri «per participants»: assistents o confirmats (RN-M09-10) | Assistents; si no hi ha llista, confirmats | Tresorer |
| S-M09-03 | Donatius de persones: es registren amb el nom del donant i cal certificat (model 182) | Només donatius anònims o d'empreses fins que es respongui | Gestoria |
| S-M09-04 | Llindar de marge baix (RN-M09-14) | 0 € | Junta |
| S-M09-05 | Durada del període (RN-M09-15) | Mensual | Tresorer |
| S-M09-06 | El marge per departament inclou els costos generals o només la suma dels marges (F §7) | Es mostren les dues coses per separat | Junta |
| S-M09-07 | Departaments a efectes d'ajuts i centres de cost (Q-17) | Els de la 04 | Junta |
| S-M09-08 | Què s'ha de facturar, IVA i Verifactu; quin servei homologat (P-02, P-47) | Facturació desactivada; només rebuts | Gestoria |
| S-M09-09 | El pagament a la federació és «taxa» al departament de llicències (RN-M09-20) | Sí | Tresorer |
| S-M09-10 | Informes que necessita l'assemblea (F §7) | Els de P-M09-E en CSV | Junta |
| S-M09-11 | Les hores de voluntariat no es valoren en euros (RN-M09-21) | No es valoren | Junta |
| S-M09-12 | Calen pressupostos anuals per departament | Fora d'abast | Junta |
| S-M09-13 | Qui reobre un període tancat i si el tresorer ho pot demanar (RN-M09-16) | Només l'administrador, amb motiu; avís per correu al tresorer i a la junta; el tresorer no ho demana a la plataforma | Junta |
| S-M09-15 | Tancar un període amb excepcions documentades (RN-M09-26): si es permet i quins elements de la llista de control es poden portar al període següent | Sí, tots, cadascun amb motiu; el tresorer decideix | Tresorer |
| S-M09-14 | Com es comptabilitza la llicència que el club cobra i paga a la FECDAS (RN-M09-20) [A verificar: gestoria] | Ingrés i despesa del club, amb marge 0, com diu el [M06-2](#M06-2-dependencies). No bloqueja el codi; bloqueja la producció | Gestoria |

**Revisió de dubtes (aplicada a mà)**
1. ~~Peces de la 04 (aprovada).~~ Resolt per la [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md) (addenda del M04).
2. ~~Moviments tardans en un període tancat.~~ Resolt per la 050: el bloqueig rebutja tot moviment nou amb data dins un període tancat i la correcció va al període obert.
3. **Reforç després del tancament** (dubte 4 de [M02-13](#M02-13-riscos)). Proposta: la comprovació de tancament del 02 ja bloqueja el tancament mentre hi hagi un reforç pendent de pagament; un reforç confirmat després del tancament és un ajust posterior (RN-M09-07). Propietari: tresorer.
4. ~~IBAN als comprovants del banc.~~ Resolt per la [051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md): la 044 cobreix els socis; els documents de justificació tenen les seves regles i una còpia emmascarada.
5. **Comissions del cobrament de la llicència d'un soci:** amb preu igual al de la federació, el club perd la comissió de cada cobrament amb targeta o Bizum. Alternatives: assumir-la o sumar-la al preu. Propietari: junta.
6. **Pressupostos:** la 04 posava «pressupostos» dins el 09, però F §7 no en diu res. Es deixen fora d'abast fins que la junta ho demani (S-M09-12). Propietari: junta.

<a id="M09-14-aprovar"></a>
## M09-14 Què cal aprovar abans de començar

**Aprovat el 28/10/2026** pel responsable del projecte, alhora que els 02, 03, 06 i 09 (amb l'apartat d'ajuts), sense canviar cap regla ni cap criteri. Respostes d'aquesta aprovació:
- Els **supòsits per defecte** s'accepten per començar i **no bloquegen el codi**.
- **Per entrar en producció** cal respondre els [A verificar] externs i les decisions de la junta ([ordre del dia](#ordre-del-dia-junta)).
- Tots els [A validar] i [A verificar] continuen oberts amb el seu propietari: aquesta aprovació no els resol.

Punts que es van presentar per aprovar:

1. **Aquesta secció del 09** (part principal), amb la fórmula del marge, la congelació en tancar i el tancament de període.
2. ~~Peces noves a la 04~~ **Aprovades** com a addenda per la [050](decisions/050-addenda-tresoreria-despeses-ingressos-i-periodes.md) ([M04-addenda-050](#M04-addenda-050)).
3. ~~IBAN als comprovants del banc~~ **Aprovat** per la [051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md).
4. **Supòsits per defecte** S-M09-01 a S-M09-05 [A validar: junta i tresorer]. No bloquegen el codi: són configurables.
5. **Per activar la facturació** (no per començar): resposta de la gestoria a P-02 i P-47 (S-M09-08) i decisió de la junta d'activar-la.

---

<a id="M09-ajuts"></a>
# Mòdul 09 — Apartat: Ajuts: calendari, sol·licituds i justificació

**Estat: aprovat** pel responsable del projecte el 28/10/2026 ([M09-ajuts-14](#M09-ajuts-14-aprovar)), amb la resta del 09. Ampliat per la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) (termini d'esmena, T-M09A-16, a l'[addenda del 09](#M09-addenda-058)). Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M09-addenda-059)).

**Fonts:** instruccions del responsable del projecte del 27/10/2026; F §7 (ajuts i justificació, procés 9.10); respostes del 20/10/2026 (totes les factures per justificar ajuts; ajuts per departament i per tipus d'acció de medi ambient) i del 22/10/2026 (subtipus i projectes per trobar ajuts); part principal del [09](#M09).

**Cap integració externa.** Les convocatòries les introdueix el club. La plataforma no busca convocatòries, no es connecta amb cap sede electrònica i no presenta res. La cerca automàtica és una idea futura del [mòdul 12](#M12-idees).

<a id="M09-ajuts-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Que el club no perdi cap termini d'un ajut i que cada ajut tingui una història completa: la convocatòria amb tots els requisits, la sol·licitud amb el seu estat i el seu responsable, les despeses i factures que el justifiquen i, si es denega, què cal millorar per tornar-ho a intentar. |
| **Processos que cobreix** | P-M09A-A Donar d'alta una convocatòria · P-M09A-B Revisar l'elegibilitat · P-M09A-C Preparar i presentar · P-M09A-D Avisos del calendari · P-M09A-E Resolució: concedida o denegada · P-M09A-F Justificar (F 9.10) · P-M09A-G Tornar-ho a intentar |
| **Tasques** | 16 (T-M09A-01 a T-M09A-16); la T-M09A-16 l'afegeix la 058 |
| **Què el bloqueja** | Per construir: les despeses i els ingressos de la part principal del 09 (T-M09-05 i T-M09-08) i el correu de la 00 (Brevo, [062](decisions/062-brevo-es-mante-com-a-proveidor-de-correu.md)). Per fer-lo servir: qui és el responsable dels ajuts i quines convocatòries s'han de vigilar [A validar: junta] |
| **Què cal aprovar** | Aquest apartat i els supòsits S-M09A-01 a S-M09A-04 ([M09-ajuts-14](#M09-ajuts-14-aprovar)) |

<a id="M09-ajuts-1-intencio"></a>
## M09-ajuts-1 Intenció, abast i fora d'abast

**Per què.** Els ajuts són una font d'ingressos important per al departament de medi ambient, però avui les convocatòries se segueixen a mà: els terminis es perden, els documents es busquen a l'últim moment i no queda memòria de per què se'n va denegar un. Justificar-ne un demana totes les factures de les despeses (F §7).

**Resultat esperat.**
- Totes les convocatòries que el club vigila són en un calendari, amb els requisits i els documents que demanen.
- El responsable i el tresorer reben un correu 30, 14 i 7 dies abans de cada tancament i el dia previst de resposta.
- Cada sol·licitud té estat, responsable, departament o projecte i import demanat.
- Un ajut concedit té les seves despeses i factures lligades, i el paquet de justificació surt amb un botó.
- Un ajut denegat guarda el motiu i què cal millorar, i es copia per a la convocatòria següent.

**Com sabrem que funciona.**
- Cap convocatòria vigilada tanca sense que el responsable n'hagi rebut els tres avisos.
- El paquet de justificació d'un ajut de prova conté totes les factures i comprovants de les despeses lligades i avisa de les que no en tenen.
- Una sol·licitud denegada es pot copiar a una convocatòria nova amb les observacions visibles.

**Dins de l'abast.**
- Convocatòries: organisme, nom, obertura, tancament, import màxim, enllaç a les bases, documents requerits, requisits d'elegibilitat (revisats per una persona), termini màxim de resolució si l'organisme el publica (opcional), data i format de justificació.
- Calendari amb avisos per correu 30, 14 i 7 dies abans del tancament i a la data prevista de resposta, amb el correu de la 00 (proveïdor dins la UE).
- Sol·licituds amb estats (detectada, en preparació, presentada, concedida, denegada, justificada, tancada), responsable, departament o projecte i import demanat.
- Concedides: despeses i factures lligades a l'ajut i paquet de justificació consolidat.
- Denegades: observacions amb motiu, data i què millorar, i còpia de la sol·licitud per a la convocatòria següent.
- Rols tresorer, junta i administrador, i registre d'activitat.

**Fora d'abast.**
- Buscar convocatòries a fonts públiques o rebre'n alertes: idea futura del [mòdul 12](#M12-idees).
- Connectar-se amb cap sede electrònica, presentar o signar una sol·licitud: es fa fora de la plataforma.
- Dades personals de socis o participants dins les sol·licituds: no s'hi posen (RN-M09A-15).
- Comptabilitat de l'ajut més enllà de l'ingrés i les despeses lligades (per exemple, periodificacions): gestoria.

<a id="M09-ajuts-2-dependencies"></a>
## M09-ajuts-2 Dependències

**De què depèn.**
| Mòdul | Què en fa servir l'apartat |
|---|---|
| 00 | Departaments; fitxers privats (bases, documents, resolucions, paquet); correu (Brevo, [062](decisions/062-brevo-es-mante-com-a-proveidor-de-correu.md)) i avisos a l'app; cua de tasques; permisos; registre d'activitat |
| 02 | Projectes i subtipus de medi ambient (lectura, clau forana) |
| 09 (part principal) | `expenses.expenses_for` (despeses amb factura i comprovant), `expenses.record_other_income(kind="grant")` (ingrés de l'ajut), `margins.department_report` |

**Què depèn de l'apartat.**
| Mòdul | Què necessita |
|---|---|
| 08 | Properes dates del calendari d'ajuts i import concedit per departament |
| 12 | L'assistent d'ajuts (idea futura) hi proposaria convocatòries com a «detectades» |

<a id="M09-ajuts-3-capacitats"></a>
## M09-ajuts-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | On |
|---|---|---|---|
| CA1 | Convocatòries amb tots els camps, i còpia a l'edició següent | Tresorer, junta | Ajuts |
| CA2 | Revisió de l'elegibilitat per una persona | Tresorer, junta | Fitxa de la convocatòria |
| CA3 | Calendari i avisos per correu | Tresorer, junta | Calendari |
| CA4 | Sol·licituds amb estats, responsable, departament o projecte i import | Tresorer, junta | Sol·licituds |
| CA5 | Documents requerits per sol·licitud | Responsable | Fitxa de la sol·licitud |
| CA6 | Concedida: ingrés, despeses lligades i paquet de justificació | Tresorer | Justificació |
| CA7 | Denegada: observacions i còpia | Tresorer, junta | Fitxa de la sol·licitud |

**Històries d'usuari**
- **HU-M09A-01.** Com a tresorer, vull donar d'alta una convocatòria amb l'enllaç a les bases i els documents que demana, per tenir-ho tot en un lloc.
- **HU-M09A-02.** Com a responsable d'una sol·licitud, vull rebre un correu 30, 14 i 7 dies abans del tancament, per no perdre el termini.
- **HU-M09A-03.** Com a junta, vull veure el calendari de totes les convocatòries vigilades i l'estat de cada sol·licitud.
- **HU-M09A-04.** Com a tresorer, vull lligar les despeses amb factura a un ajut concedit i descarregar-ne el paquet de justificació.
- **HU-M09A-05.** Com a junta, vull guardar per què ens han denegat un ajut i copiar la sol·licitud a la convocatòria de l'any següent amb el que cal millorar.

<a id="M09-ajuts-4-rols"></a>
## M09-ajuts-4 Rols i permisos

Només tres rols hi tenen accés; **la resta de rols no hi veuen res**. Tot es fa amb el compte d'administrador i TOTP. «[A validar]» sense propietari vol dir **junta** (S-M09A-01).

| # | Acció | Tresorer | Junta | Administrador |
|---|---|---|---|---|
| AJ1 | Crear, editar i copiar convocatòries | Sí | Sí | Sí |
| AJ2 | Revisar l'elegibilitat | Sí | Sí | Sí |
| AJ3 | Veure el calendari, les convocatòries i les sol·licituds | Sí | Sí | Sí |
| AJ4 | Crear una sol·licitud i moure-la fins a «presentada» | Sí | Sí, si n'és responsable [A validar] | Sí |
| AJ5 | Marcar-la concedida o denegada i escriure les observacions | Sí | Sí, si n'és responsable [A validar] | Sí |
| AJ13 | Registrar un requeriment d'esmena i la seva resposta; editar la pròrroga de justificació | Sí | Sí, si n'és responsable [A validar] | Sí |
| AJ6 | Registrar l'ingrés de l'ajut (part principal, MG4) | Sí | — | Sí |
| AJ7 | Lligar despeses i generar el paquet de justificació | Sí | Consulta | Lligar despeses, sense obrir els documents ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) |
| AJ8 | Marcar-la justificada o tancada | Sí | — | Sí |
| AJ9 | Desfer l'últim canvi d'estat, amb motiu | — | — | Sí |
| AJ10 | Configurar els dies dels avisos | Sí | — | Sí |
| AJ11 | Consultar el registre d'activitat dels ajuts | Consulta | — | Sí |
| AJ12 | Obrir i descarregar els documents de justificació i el paquet | Sí | Sí | — ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) |

**Per objecte.** El **responsable** d'una sol·licitud és una persona amb compte d'administrador i un d'aquests tres rols [A validar: junta, S-M09A-01]. Rep els avisos de les seves sol·licituds. Que la junta existeixi com a rol és P-04 (S-M01-23).

<a id="M09-ajuts-5-processos"></a>
## M09-ajuts-5 Processos pas per pas

**Wireframes:** cap. **Falten** (T-M09A-01): calendari, llistat i fitxa de convocatòria, fitxa de sol·licitud amb estats i documents, justificació (despeses lligades i paquet), observacions de denegació.

**Estats de la sol·licitud**
| Estat | Què vol dir | Hi arriba |
|---|---|---|
| **Detectada** | El club ha vist la convocatòria i la vigila | En crear la sol·licitud |
| **En preparació** | S'ha decidit presentar-s'hi i es preparen els documents | Des de «detectada», amb l'elegibilitat revisada |
| **Presentada** | S'ha presentat a l'organisme | Des d'«en preparació», amb data, import demanat i documents a punt |
| **Concedida** | L'organisme l'ha concedit | Des de «presentada», amb import concedit i resolució |
| **Denegada** | L'organisme l'ha denegat | Des de «presentada», amb observacions |
| **Justificada** | S'ha enviat la justificació | Des de «concedida», amb la data d'enviament |
| **Tancada** | No hi ha res més a fer | Des de «justificada» o «denegada»; o des de «detectada» o «en preparació» amb el motiu «no es presenta» |

### P-M09A-A Donar d'alta una convocatòria
1. El tresorer o la junta escriu l'organisme, el nom, l'obertura, el tancament, l'import màxim, l'enllaç a les bases, els documents requerits (un per línia), els requisits d'elegibilitat, el termini màxim de resolució si l'organisme el publica, el període de despeses subvencionables, la data i el format de justificació.
2. Crea la sol·licitud en estat **detectada** amb el responsable, el departament o projecte i l'import previst.
3. El sistema programa els avisos del tancament (RN-M09A-04).

### P-M09A-B Revisar l'elegibilitat
1. El responsable llegeix les bases i marca cada requisit com a complert, no complert o dubtós, amb nota.
2. Marca la convocatòria com a **elegible** o **no elegible**. El sistema no ho decideix mai sol (RN-M09A-03).
3. Si no és elegible, la sol·licitud passa a **tancada** amb el motiu.

### P-M09A-C Preparar i presentar
1. La sol·licitud passa a **en preparació**: surt la llista de documents requerits per marcar-los i pujar-los.
2. Quan es presenta (fora de la plataforma), el responsable hi posa la data, el número de registre d'entrada, l'import demanat i la còpia del que s'ha presentat.
3. Passa a **presentada**. Si l'organisme publica el termini de resolució, el sistema calcula la data prevista de resposta; si no, el responsable la pot escriure.

### P-M09A-D Avisos del calendari
| Quan | A qui | Què diu |
|---|---|---|
| 30, 14 i 7 dies abans del tancament (sol·licituds detectades o en preparació) | Responsable i tresorer [A validar: junta] | Convocatòria, data de tancament, documents que falten i enllaç a la fitxa |
| La data prevista de resposta (sol·licituds presentades) | Responsable i tresorer | Que toca comprovar la resolució |
| [Proposta] 30, 14 i 7 dies abans de la data de justificació, o de la pròrroga si n'hi ha (sol·licituds concedides) | Responsable i tresorer | Despeses sense factura o sense comprovant [A validar: junta, S-M09A-04] |
| En registrar un requeriment d'esmena (immediat) i, [Proposta], 7 i 2 dies abans de la data límit, fins que es respon | Responsable del requeriment i tresorer | Sol·licitud, descripció del requeriment, data límit i enllaç a la fitxa [A validar: junta, S-M09A-09] |

### P-M09A-E Resolució
- **Concedida:** el responsable hi posa l'import concedit, la data i la resolució. El tresorer registra l'ingrés quan arriba (part principal, P-M09-C), un o més cops (bestreta i saldo).
- **Denegada:** el responsable escriu el motiu, la data de la resolució i què caldria millorar; adjunta la resolució.

### P-M09A-F Justificar (F 9.10)
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Tresorer | Obre la justificació de l'ajut: el sistema filtra les despeses del departament o projecte dins el període subvencionable |
| 2 | Tresorer | Lliga les despeses a l'ajut, amb l'import imputat de cadascuna |
| 3 | Sistema | Avisa de les que no tenen factura o comprovant, i mostra l'import justificat davant del concedit |
| 4 | Tresorer | Genera el paquet: resum d'ingressos i despeses, llistat de factures i un ZIP amb totes les factures i els comprovants |
| 5 | Tresorer | Registra la data d'enviament a l'organisme: la sol·licitud passa a **justificada** |
| 6 | Tresorer | Quan l'organisme l'accepta (o es fa un reintegrament), la passa a **tancada** |

### P-M09A-G Tornar-ho a intentar
1. Des d'una sol·licitud denegada, el responsable tria «Copiar a una convocatòria nova» i tria la convocatòria (o copia la convocatòria a l'edició següent, sense dates).
2. El sistema crea una sol·licitud nova en estat **detectada** amb el mateix departament o projecte, l'import i la llista de documents, i hi mostra les observacions de la denegació anterior.

<a id="M09-ajuts-6-entitats"></a>
## M09-ajuts-6 Entitats i camps

App Django `grants` (nova). Cap camp de dades personals més enllà del responsable (FK a la persona amb rol) i de qui fa cada acció.

### GrantCall (convocatòria)
| Camp | Tipus | Restriccions |
|---|---|---|
| `body` | `CharField(140)` | Organisme |
| `name` | `CharField(200)` | — |
| `edition_label` | `CharField(20)` | Per distingir edicions (text lliure) |
| `opens_on`, `closes_on` | `DateField` null | `closes_on ≥ opens_on`. Sense tancament = convocatòria oberta tot l'any, sense avisos de tancament |
| `max_amount_cents` | `PositiveBigIntegerField` null | — |
| `rules_url` | `URLField` | Enllaç a les bases; la plataforma no el visita |
| `rules_file` | fitxer privat null | Còpia de les bases (opcional) |
| `eligibility_requirements` | `TextField` | — |
| `eligibility_status` | `pending`, `eligible`, `not_eligible` | Només el canvia una persona (RN-M09A-03) |
| `eligibility_reviewed_by`, `eligibility_reviewed_at`, `eligibility_notes` | — | Obligatoris si no és `pending` |
| `max_resolution_days` | `PositiveSmallIntegerField` null | Opcional, si l'organisme el publica |
| `eligible_expenses_from`, `eligible_expenses_to` | `DateField` null | Període de despeses subvencionables |
| `justification_due_on` | `DateField` null | — |
| `justification_format` | `TextField` | — |
| `accepts_masked_proofs` | `yes`, `no`, `unknown` | Si l'organisme accepta comprovants amb l'IBAN emmascarat; per defecte `unknown` [A verificar: tresorer, per a cada convocatòria] ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) |
| `previous_edition` | FK self null | Còpia de l'edició anterior |
| `created_by` | FK compte | — |
- `GrantCallDocument`: `call`, `name`, `order`. Documents requerits.

### GrantApplication (sol·licitud)
| Camp | Tipus | Restriccions |
|---|---|---|
| `call` | FK GrantCall (PROTECT) | — |
| `status` | estats de [M09-ajuts-5](#M09-ajuts-5-processos) | Transicions de RN-M09A-01 |
| `responsible` | FK Person | Amb rol tresorer, junta o administrador (servei) |
| `department` | FK departament (00) | Obligatori |
| `cost_centre` | FK CostCentre (04) null | — |
| `project`, `subtype` | FK (02) null | Medi ambient |
| `amount_requested_cents` | `PositiveBigIntegerField` | Obligatori per presentar-la |
| `submitted_on`, `submission_ref` | data, `CharField(60)` | Obligatoris per presentar-la |
| `submission_file` | fitxer privat null | Còpia del que s'ha presentat |
| `expected_response_on` | `DateField` null | Calculada (RN-M09A-05) o escrita |
| `amount_granted_cents`, `resolved_on`, `resolution_file` | — | Obligatoris en concedir-la o denegar-la |
| `justified_on` | `DateField` null | Obligatori en passar a justificada |
| `submitted_package` | FK JustificationPackage null (PROTECT) | Obligatori en passar a justificada: el primer paquet enviat (versió 1), que queda congelat (RN-M09A-18). Les versions següents són a `PackageSubmission` |
| `justification_extended_to` | `DateField` null | **Pròrroga de justificació**, editable; cada canvi amb motiu al registre. Si hi és, substitueix `justification_due_on` de la convocatòria per a aquesta sol·licitud (RN-M09A-20) |
| `closed_reason` | `TextField` | Obligatori si es tanca sense presentar-la |
| `copied_from` | FK self null | RN-M09A-14 |
- `ApplicationDocument`: `application`, `name` (copiat de la convocatòria o afegit), `file` null, `ready` (bool), `uploaded_by`.
- `ApplicationTransition` (només INSERT): `application`, `from_status`, `to_status`, `reason`, `actor`, `at`. Un desfer és una transició nova (AJ9).
- `DenialNote` (només INSERT): `application`, `reason` (motiu), `resolved_on` (data), `improvements` (què millorar), `recorded_by`.
- `GrantExpenseLink`: `application`, `expense` (FK Expense del 09), `amount_cents` (> 0), `created_by`, `requirement` (FK GrantRequirement null: el requeriment amb què s'ha afegit, si la sol·licitud ja era justificada), `removed_at`, `removed_by`, `removed_requirement` (null; un enllaç no s'esborra mai, es dona de baixa). **Únic parcial** `(application, expense)` quan `removed_at` és buit. La suma imputada d'una despesa entre tots els ajuts (enllaços actius) no passa del seu import (servei). En una sol·licitud justificada, només es pot afegir o donar de baixa un enllaç amb un requeriment obert (RN-M09A-21).
- `GrantRequirement` (requeriment d'esmena): `application`, `origin` (`body`: el demana l'organisme; `club`: iniciativa del club), `origin_reason` (obligatori si `origin = club`), `received_on` (data de rebuda o, si és del club, data en què s'obre), `due_on`, `description`, `responsible` (FK Person, amb rol tresorer, junta o administrador), `answered_on` (null), `created_by`. **No és un estat**: la sol·licitud manté el seu estat (RN-M09A-19). Cada canvi va al registre; canviar `due_on` demana motiu (RN-M09A-22).
- `JustificationPackage` (només INSERT): `application`, `generated_by`, `generated_at`, `file` (ZIP, document de justificació xifrat, [051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)), `masked` (bool: si porta les còpies emmascarades), `sha256`, `totals` (JSON), `excluded` (JSON amb les despeses excloses i el motiu), `items` (JSON: cada despesa inclosa amb l'import imputat i el `sha256` de cada document).
- `PackageSubmission` (enviament d'una versió, només INSERT): `application`, `package` (FK JustificationPackage, PROTECT), `version` (1, 2, 3…), `requirement` (FK GrantRequirement; buit només a la versió 1), `sent_on`, `sent_by`. Únic `(application, version)` i únic `package`. La versió 1 es crea en passar a «justificada» i coincideix amb `submitted_package`. La versió vigent és la més alta.
- `GrantReminder` (només INSERT): `application`, `requirement` (FK GrantRequirement null), `kind` (`close_30`, `close_14`, `close_7`, `response`, `justify_30`, `justify_14`, `justify_7`, `requirement_now`, `requirement_7`, `requirement_2`), `due_on`, `sent_at`. Dues restriccions úniques parcials: per als avisos de requeriment (`requirement_now`, `requirement_7`, `requirement_2`), **únic `(application, requirement, kind)`, sense `due_on`**, perquè un canvi de data límit no permeti tornar a enviar un avís ja enviat (RN-M09A-22); per a la resta, únic `(application, kind, due_on)`. Un avís no s'envia dues vegades.

### Valors configurables de l'apartat (pantalla d'ajustos del 09, T-M09-26)
| Clau de l'ajust | VC | Valor inicial | Rang vàlid | Qui el canvia | Data d'entrada en vigor |
|---|---|---|---|---|---|
| `grants.deadline_reminder_days` | VC-36 | 30, 14 i 7 | 1 a 90 | Tresorer | — |
| `grants.requirement_reminder_days` | VC-37 | 7 i 2 (el primer avís, immediat, és fix) | 1 a 30 | Tresorer | — |

<a id="M09-ajuts-7-regles"></a>
## M09-ajuts-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M09A-01 | Transicions: detectada → en preparació → presentada → concedida → justificada → tancada; presentada → denegada → tancada; detectada o en preparació → tancada (amb motiu «no es presenta»). Cap altra. L'administrador pot desfer l'última transició amb motiu (queda com a transició nova) | Instruccions del 27/10/2026 |
| RN-M09A-02 | Per passar a «presentada» calen data, número de registre, import demanat i tots els documents requerits marcats a punt | Proposta |
| RN-M09A-03 | L'elegibilitat la revisa **sempre una persona**. Sense revisió, la sol·licitud no passa a «en preparació». El sistema no decideix mai l'elegibilitat | Instruccions del 27/10/2026 |
| RN-M09A-04 | Avisos de tancament: 30, 14 i 7 dies abans de `closes_on`, per a les sol·licituds detectades o en preparació, al responsable i al tresorer, per correu i a l'app (sense push, [041](decisions/041-web-installable-i-avisos-sense-push.md)). Una tasca diària de la cua els envia; si `closes_on` canvia, es recalculen; si la data ja ha passat, no s'envia | Instruccions del 27/10/2026 |
| RN-M09A-05 | Data prevista de resposta = `submitted_on` + `max_resolution_days` si l'organisme el publica; si no, la que escrigui el responsable; si no n'hi ha, cap avís. El dia de la data, avís si encara és «presentada» | Instruccions del 27/10/2026 |
| RN-M09A-06 | Els dies dels avisos (30, 14 i 7) són configurables (ajust `grants.deadline_reminder_days`). Cada avís s'envia una sola vegada (unicitat de `GrantReminder`), també si la tasca es repeteix | Proposta |
| RN-M09A-07 | El correu surt pel servei de la 00, amb Brevo ([062](decisions/062-brevo-es-mante-com-a-proveidor-de-correu.md)). Només porta el nom de la convocatòria, les dates, el que falta i l'enllaç a la fitxa | 035; 042; 062 |
| RN-M09A-08 | Concedida: import concedit i resolució obligatoris. Si l'import concedit supera el demanat, avís (no bloqueja) | Proposta |
| RN-M09A-09 | L'ingrés de l'ajut es registra a la part principal com a `OtherIncome` de tipus `grant`, lligat a la sol·licitud i al seu departament, **mai a una activitat** (RN-M09-08). Pot tenir diversos ingressos (bestreta i saldo) | F §7; RN-M09-08 |
| RN-M09A-10 | Només es poden lligar despeses del departament o projecte de la sol·licitud, dins el període subvencionable si n'hi ha, que no estiguin anul·lades. La suma imputada d'una despesa entre tots els ajuts no passa del seu import | F 9.10 |
| RN-M09A-11 | Paquet de justificació: resum d'ingressos i despeses, llistat de factures i ZIP amb factures i comprovants. Les despeses sense factura o sense comprovant (també quan la factura o el comprovant tenen una marca d'il·legible oberta, RN-M09-25) **no hi entren**: surten a «excloses» amb el motiu, i el tresorer en rep l'avís. El paquet porta les **còpies amb l'IBAN emmascarat**, excepte si la convocatòria diu que no les accepta (`accepts_masked_proofs = no`); llavors el tresorer el genera amb els originals | F 9.10; [051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md) |
| RN-M09A-12 | Justificada: cal la data d'enviament. Tancada: quan l'organisme l'accepta o s'ha registrat el reintegrament (vegeu el dubte 2) | F 9.10 |
| RN-M09A-13 | Denegada: cal almenys una observació amb motiu, data i què millorar | Instruccions del 27/10/2026 |
| RN-M09A-14 | Copiar una sol·licitud: la nova és «detectada», amb el mateix departament o projecte, import i documents (sense els fitxers, excepte si el responsable els tria), i amb les observacions de la denegació anterior visibles. Copiar una convocatòria a l'edició següent en copia tot excepte les dates | Instruccions del 27/10/2026 |
| RN-M09A-15 | Cap dada personal de socis ni participants a les convocatòries, sol·licituds ni documents. Si un organisme demana un llistat de participants, es dona fora de la plataforma; aquí només hi ha recomptes | Instruccions del 27/10/2026; 035 |
| RN-M09A-16 | Tot canvi (convocatòries, estats, documents, despeses lligades, paquets i avisos enviats) va al registre d'activitat amb el valor anterior | CLAUDE.md |
| RN-M09A-17 | Imports en cèntims | CLAUDE.md |
| RN-M09A-18 | **Paquet congelat.** En passar a «justificada», la sol·licitud queda lligada al paquet enviat (`submitted_package`): llista de despeses, imports, documents (amb el seu `sha256`) i data d'enviament (`justified_on`). Aquest paquet no canvia mai. Si després s'anul·la una despesa que hi és inclosa (RN-M09-11), el tresorer rep un avís (correu i app) amb la sol·licitud, la despesa i l'import, i el paquet **no canvia sol**: el tresorer decideix què fer (per exemple, el reintegrament, dubte 2). Les despeses lligades d'una sol·licitud justificada no es poden treure ni afegir, excepte amb un requeriment obert (RN-M09A-21). L'avís per anul·lació val per a les despeses de qualsevol versió enviada. Igualment, si es marca il·legible (RN-M09-25) una factura o un comprovant inclòs en una versió enviada, el tresorer rep un avís amb la sol·licitud, la versió i la despesa; el paquet no canvia sol i el tresorer pot obrir un requeriment d'iniciativa del club (RN-M09A-19) | 27/10/2026 |
| RN-M09A-19 | **Requeriment d'esmena:** és un esdeveniment de la sol·licitud, no un estat. Porta origen, data de rebuda, data límit, descripció i responsable. L'origen és «organisme» (el demana l'organisme) o «iniciativa del club»: el tresorer en pot obrir un per enviar una versió nova del paquet sense esperar que l'organisme la demani, amb motiu obligatori. Surt al calendari i té avisos propis al responsable i al tresorer: el primer **immediat** en registrar-lo; després, [Proposta] 7 i 2 dies abans de la data límit, configurables (ajust `grants.requirement_reminder_days`) [A validar: junta, S-M09A-09]. Quan es registra la resposta (`answered_on`), no s'envia cap més avís. La data límit l'escriu la persona a partir del requeriment (o la fixa el tresorer, si és del club); el termini legal de resposta és [A verificar: gestoria, S-M09A-08] i la plataforma no el calcula | 27/10/2026 |
| RN-M09A-20 | **Pròrroga de justificació:** data editable de la sol·licitud (`justification_extended_to`), amb motiu al registre. Si hi és, els avisos de justificació (RN-M09A-04 i S-M09A-04) i el calendari fan servir aquesta data; els avisos ja enviats no es repeteixen | 27/10/2026 |
| RN-M09A-21 | **Versions del paquet.** El primer paquet enviat (versió 1) queda congelat (RN-M09A-18). Si l'organisme demana esmenar la justificació, o el tresorer ho decideix per iniciativa del club (per exemple, perquè un document enviat s'ha marcat il·legible), amb un requeriment obert de qualsevol origen (RN-M09A-19) (sense `answered_on`) el tresorer pot afegir o donar de baixa despeses lligades (cada canvi porta el requeriment), generar un paquet nou i enviar-lo com a **versió 2** (i així successivament), lligada a aquell requeriment. Les versions anteriors i els seus fitxers no canvien mai. Enviar una versió registra la resposta del requeriment (`answered_on` = data d'enviament). La sol·licitud continua «justificada» | 28/10/2026 |
| RN-M09A-22 | **Canviar la data límit d'un requeriment:** amb motiu obligatori, al registre amb el valor anterior. Els avisos que falten es recalculen sobre la data nova; els ja enviats no es repeteixen, ni l'immediat (mateixa lògica que la pròrroga, RN-M09A-20, CA-M09A-19). Ho garanteix també la base de dades: un avís de requeriment és únic per sol·licitud, requeriment i tipus, sigui quina sigui la data límit | 28/10/2026 |

**Exemples** (dades inventades; «dia D» és el tancament de la convocatòria)
- **Avisos:** tancament el dia D → correus els dies D−30, D−14 i D−7. Si el dia D−20 el tancament es mou a D+10, els avisos que falten passen a D−4 (el de 14 dies respecte del nou tancament) i D+3; el de 30 ja enviat no es repeteix.
- **Resposta:** presentada el dia P, termini de resolució publicat de 90 dies → avís el dia P+90 si encara és «presentada». Sense termini publicat → cap avís si el responsable no escriu una data.
- **Justificació:** demanat 300.000 (3000 €), concedit 240.000. Despeses lligades: embarcació 50.000 (amb factura i comprovant), aire 24.000 (amb factura i comprovant), bosses 6500 (sense factura). Justificat al paquet: 50.000 + 24.000 = **74.000**; exclosa la de 6500 amb el motiu «sense factura». El sistema mostra 74.000 de 240.000 (30,8 %).

<a id="M09-ajuts-8-serveis"></a>
## M09-ajuts-8 Serveis i interfícies (contracte)

Cap altra app escriu als models de `grants`.

**Ofereix**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `grants.calendar(from, to)` | dates | tancaments, respostes previstes, justificacions (amb la pròrroga si n'hi ha) i requeriments oberts (lectura) | — | Calendari; 08 |
| `grants.transition(application, to_status, data, actor)` | — | sol·licitud | `InvalidTransition`, `MissingDocuments`, `EligibilityNotReviewed` | Vistes |
| `grants.link_expense(application, expense, amount_cents, actor, requirement=None)`, `grants.unlink_expense(link, actor, requirement=None)` | — | `GrantExpenseLink` (alta o baixa) | `ExpenseOutOfScope`, `OverImputed`; `AlreadyJustified` si la sol·licitud és justificada sense requeriment obert | Vistes |
| `grants.build_package(application, actor, requirement=None)` | — | `JustificationPackage` (esborrany d'una versió nova si la sol·licitud ja és justificada) | `NotGranted`; `AlreadyJustified` si la sol·licitud és justificada i no s'indica cap requeriment obert; `RequirementNotOpen` | Vistes |
| `grants.submit_package_version(application, package, requirement, sent_on, actor)` | — | `PackageSubmission` amb la versió següent; resposta del requeriment | `RequirementNotOpen`, `PackageAlreadySent` | Vistes |
| `grants.on_expense_annulled(expense)` | senyal intern del 09 quan s'anul·la una despesa | avís al tresorer si la despesa és en un paquet congelat (RN-M09A-18); no canvia res | — | Subscriptor (`expenses` emet el senyal; `grants` no escriu als models de `expenses`) |
| `grants.on_document_marked_illegible(expense, document)` | senyal intern del 09 quan es crea una `DocumentIllegibleMark` | avís al tresorer si el document és en una versió enviada (RN-M09A-18); no canvia res | — | Subscriptor (`expenses` emet el senyal) |
| `grants.copy_application(application, call, actor)`, `grants.copy_call(call, actor)` | — | sol·licitud o convocatòria nova | — | Vistes |
| `grants.record_requirement(application, origin, received_on, due_on, description, responsible, actor, origin_reason=None)`, `grants.answer_requirement(requirement, answered_on, actor)` | — | `GrantRequirement`; el primer avís surt a la cua en desar-lo | `InvalidDates`, `MissingReason` (origen club sense motiu) | Vistes |
| `grants.set_justification_extension(application, date, reason, actor)` | — | sol·licitud | — | Vistes |
| `grants.change_requirement_due_on(requirement, due_on, reason, actor)` | — | requeriment; avisos que falten recalculats | `MissingReason`, `RequirementNotOpen` | Vistes |
| `grants.send_due_reminders(today)` | data | avisos enviats (idempotent) | — | Tasca diària de la cua |
| `grants.granted_by_department(period)` | — | imports concedits i cobrats (lectura) | — | 08 |

**Consumeix**
| Servei | Mòdul | Per a què |
|---|---|---|
| `expenses.expenses_for(filters)`, `expenses.record_other_income(kind="grant", …)` | 09 | Despeses per justificar i ingrés de l'ajut |
| `margins.department_report` | 09 | Resum del paquet |
| `files.store_private`, `mail.send`, `notices.post`, `audit.record`, `permissions.require`, cua de tasques | 00 | Fitxers, avisos, registre, permisos |

**Rutes (administració).** `/gestio/ajuts`, `/gestio/ajuts/calendari`, `/gestio/ajuts/convocatories/{id}`, `/gestio/ajuts/sollicituds/{id}`, `/gestio/ajuts/sollicituds/{id}/justificacio`. Cap ruta pública ni del compte personal.

<a id="M09-ajuts-9-criteris"></a>
## M09-ajuts-9 Criteris d'acceptació i casos límit

- **CA-M09A-01** Donat una sol·licitud detectada amb tancament el dia D, quan la tasca s'executa els dies D−30, D−14 i D−7, llavors el responsable i el tresorer reben un correu cada dia; si la tasca s'executa dues vegades el mateix dia, no s'envia cap correu repetit.
- **CA-M09A-02** Donat una sol·licitud presentada, quan s'executa la tasca un dia d'avís de tancament, llavors no s'envia cap avís de tancament.
- **CA-M09A-03** Donat un termini de resolució de 90 dies i la data de presentació P, quan es presenta, llavors la data prevista és P+90 i aquell dia s'envia l'avís si encara és presentada.
- **CA-M09A-04** Donat una convocatòria amb l'elegibilitat pendent, quan es vol passar la sol·licitud a «en preparació», llavors es rebutja.
- **CA-M09A-05** Donat un document requerit sense marcar, quan es vol presentar, llavors es rebutja amb la llista del que falta.
- **CA-M09A-06** Donat una sol·licitud presentada, quan es vol passar a «justificada», llavors es rebutja (transició no permesa).
- **CA-M09A-07** Donat una sol·licitud denegada sense observació, quan es desa, llavors es rebutja.
- **CA-M09A-08** Donat l'exemple de justificació, quan es genera el paquet, llavors el ZIP conté les factures i comprovants de 50.000 i 24.000, el resum diu 74.000 i la despesa de 6500 surt a «excloses».
- **CA-M09A-09** Donat una despesa d'un altre departament, quan es vol lligar a l'ajut, llavors es rebutja.
- **CA-M09A-10** Donat una despesa de 10.000 ja lligada per 8000 a un altre ajut, quan se'n lliguen 3000 més, llavors es rebutja.
- **CA-M09A-11** Donat una sol·licitud denegada, quan es copia a la convocatòria següent, llavors la nova és «detectada», té els mateixos documents sense fitxers i mostra les observacions.
- **CA-M09A-12** Donat un ingrés de tipus ajut lligat a la sol·licitud, quan es vol posar a una activitat, llavors es rebutja (CA-M09-09).
- **CA-M09A-13** Donat un soci o un responsable de material, quan obre `/gestio/ajuts`, llavors rep «no trobat» i queda al registre.
- **CA-M09A-14** Donat cada cel·la de [M09-ajuts-4](#M09-ajuts-4-rols), quan el rol prova l'acció, llavors el resultat coincideix.
- **CA-M09A-16** Donat una sol·licitud justificada amb un paquet de dues despeses (50.000 i 24.000), quan el tresorer anul·la la de 24.000, llavors el paquet enviat continua amb les dues despeses, els imports, el `sha256` dels documents i la data d'enviament; el tresorer rep un avís, i, sense cap requeriment obert, lligar-hi o treure'n despeses i `build_package` es rebutgen (`AlreadyJustified`).
- **CA-M09A-20** Donat una sol·licitud justificada amb la versió 1 (despeses de 50.000 i 24.000) i un requeriment obert, quan el tresorer dona de baixa la de 24.000, n'afegeix una de 10.000, genera el paquet i l'envia, llavors hi ha una versió 2 lligada al requeriment amb 50.000 i 10.000, la versió 1 continua amb 50.000 i 24.000, el seu `sha256` i la seva data d'enviament, el requeriment queda respost i la sol·licitud continua «justificada».
- **CA-M09A-21** Donat un requeriment ja respost, quan es vol generar o enviar una versió nova amb aquest requeriment, llavors es rebutja (`RequirementNotOpen`); quan es vol tornar a donar d'alta una despesa donada de baixa, s'accepta només amb un requeriment obert i l'enllaç anterior es conserva.
- **CA-M09A-17** Donat una sol·licitud concedida, quan el responsable registra un requeriment amb data límit D, llavors la sol·licitud continua «concedida», el requeriment surt al calendari i el responsable i el tresorer reben el primer avís en aquell moment.
- **CA-M09A-18** Donat un requeriment amb data límit D, quan la tasca s'executa els dies D−7 i D−2 (dues vegades cadascun), llavors s'envia un sol avís cada dia; si s'ha registrat la resposta abans de D−2, aquell dia no s'envia res.
- **CA-M09A-19** Donat una justificació amb data J i l'avís de 30 dies ja enviat, quan s'hi posa una pròrroga fins a J+60 amb motiu, llavors el calendari mostra J+60, els avisos que falten es calculen sobre J+60, el de 30 dies no es repeteix fins a la nova data i el canvi queda al registre amb el motiu.
- **CA-M09A-22** Donat un requeriment amb data límit D i l'avís de 7 dies ja enviat, quan el responsable canvia la data límit a D+10 amb motiu, llavors el calendari mostra D+10, l'avís de 2 dies es calcula sobre D+10, ni l'immediat ni el de 7 dies no es tornen a enviar, i el registre guarda D, D+10, el motiu i qui ho ha fet; sense motiu, el canvi es rebutja.
- **CA-M09A-23** Donat un requeriment amb l'avís `requirement_7` ja enviat per a la data límit D, quan la data passa a D+10 i es vol inserir un altre `requirement_7` per a aquell requeriment (també amb una consulta SQL directa), llavors la base de dades ho rebutja.
- **CA-M09A-24** Donat una sol·licitud justificada amb la versió 1 enviada, quan el tresorer marca il·legible el comprovant d'una despesa inclosa, llavors rep un avís amb la sol·licitud, la versió i la despesa, i la versió 1 no canvia.
- **CA-M09A-25** Donat el cas anterior, quan el tresorer obre un requeriment d'origen «iniciativa del club» sense motiu, llavors es rebutja; amb motiu, s'obre, surt al calendari amb el seu origen i permet generar i enviar la versió 2 (RN-M09A-21).
- **CA-M09A-15** Donat una convocatòria amb `accepts_masked_proofs = unknown`, quan es genera el paquet, llavors porta les còpies emmascarades; amb `no`, el tresorer el pot generar amb els originals i la descàrrega queda al registre.

**Casos límit**
| # | Cas | Comportament |
|---|---|---|
| L-M09A-01 | Convocatòria sense data de tancament | Sense avisos de tancament; surt al calendari com a «oberta» |
| L-M09A-02 | Es crea la sol·licitud quan falten menys de 7 dies | Només s'envien els avisos que encara no han passat |
| L-M09A-03 | Ajut concedit per menys del que s'ha demanat | Es desa l'import concedit; la justificació es compara amb el concedit |
| L-M09A-04 | Ajut concedit i després renunciat | Transició a «tancada» des de «concedida» no és permesa: es fa amb el desfer de l'administrador i el motiu (vegeu el dubte 3) |
| L-M09A-05 | El responsable deixa de tenir el rol | La sol·licitud surt a «sense responsable» al calendari i els avisos van al tresorer |
| L-M09A-06 | La mateixa convocatòria es demana per a dos projectes | Dues sol·licituds a la mateixa convocatòria |

<a id="M09-ajuts-10-tasques"></a>
## M09-ajuts-10 Tasques (per dependències, sense dates)

| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M09A-01 | Wireframes que falten (vegeu [M09-ajuts-5](#M09-ajuts-5-processos)) | S | `design/wireframes/` | — | Revisats |
| T-M09A-02 | Models de convocatòria, documents requerits i sol·licitud | M | `apps/grants/models.py`, migracions | T-M09-03 | Restriccions provades |
| T-M09A-03 | Elegibilitat revisada per una persona | S | `apps/grants/services.py` | T-M09A-02 | CA-M09A-04 |
| T-M09A-04 | Transicions d'estat, documents i desfer de l'administrador | M | `services.py` | T-M09A-02 | CA-M09A-05, 06 |
| T-M09A-05 | Calendari (llista i mes) | S | vistes | T-M09A-02 | HU-M09A-03 |
| T-M09A-06 | Avisos de la cua (tancament, resposta i, si s'aprova, justificació), idempotents | M | `apps/grants/reminders.py` | T-M09A-02 | CA-M09A-01, 02, 03 |
| T-M09A-07 | Resolució: concedida i denegada amb observacions | S | `services.py` | T-M09A-04 | CA-M09A-07 |
| T-M09A-08 | Ingrés de l'ajut des de la sol·licitud | S | vistes | T-M09A-07, T-M09-08 | CA-M09A-12 |
| T-M09A-09 | Lligar despeses amb els límits; alta i baixa amb un requeriment obert (RN-M09A-21) | M | `apps/grants/justification.py` | T-M09A-07, T-M09-05 | CA-M09A-09, 10, 21 |
| T-M09A-10 | Paquet de justificació (resum, llistat i ZIP xifrat, amb còpies emmascarades o originals segons la convocatòria); paquet congelat en justificar, versions noves lligades a un requeriment (`PackageSubmission`) i avís si s'anul·la una despesa inclosa o se'n marca il·legible un document | M | `justification.py` | T-M09A-09, T-M09-25 | CA-M09A-08, 15, 16, 20, 24 |
| T-M09A-11 | Còpia de sol·licitud i de convocatòria | S | `services.py` | T-M09A-07 | CA-M09A-11 |
| T-M09A-12 | Permisos (tres rols, cap accés per a la resta) | S | `apps/grants/permissions.py` | T-M09A-02 | CA-M09A-13, 14 |
| T-M09A-13 | Dades inventades i proves de principi a fi (convocatòria → avisos → presentada → concedida → ingrés → despeses → paquet → tancada) | M | `fixtures/`, `tests/` | T-M09A-03 a T-M09A-11 | Totes en verd |
| T-M09A-14 | Guia d'ajuts per al tresorer i la junta | S | `docs/` | T-M09A-13 | Revisada |
| T-M09A-15 | Requeriments d'esmena (origen organisme o club, esdeveniment, calendari i avisos propis amb el primer immediat) i pròrroga de justificació; canvi de data límit amb motiu i avisos recalculats | M | `apps/grants/requirements.py`, `reminders.py` | T-M09A-06 | CA-M09A-17, 18, 19, 22, 23, 25 |

<a id="M09-ajuts-11-proves"></a>
## M09-ajuts-11 Pla de proves

- **Unitàries (B1):** transicions i requisits de cada estat; càlcul de les dates dels avisos (amb canvis de data i dates passades); data prevista de resposta; límits d'imputació; contingut del paquet i despeses excloses.
- **Cua:** la tasca diària executada dues vegades no envia avisos repetits; amb una data de prova fixa, sense dependre del dia real.
- **Correu:** bústia de proves; el text no porta cap dada personal més enllà del destinatari.
- **Integració amb la part principal:** despesa pagada amb factura → lligada → paquet; ingrés de l'ajut → informe del departament.
- **Permisos (B4):** una prova per cel·la de [M09-ajuts-4](#M09-ajuts-4-rols) i «no trobat» per a la resta de rols.
- **Accessibilitat (B8):** estats amb símbol, text i color; calendari usable amb teclat.
- **Dades:** només inventades.

<a id="M09-ajuts-12-seguretat"></a>
## M09-ajuts-12 Seguretat i RGPD

- **Cap dada personal** de socis ni participants (RN-M09A-15). Text d'ajuda als camps lliures i a la pujada de documents.
- **Correu dins la UE** (035, 042; Brevo, 062).
- **Cap integració externa:** la plataforma no visita els enllaços de les bases ni es connecta amb cap organisme.
- **Fitxers privats** (bases, documents, resolucions), amb enllaç signat i caducitat curta.
- **Documents de justificació i paquets** ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)): xifrats a la UE, només els obren el tresorer i la junta, cap eina d'IA, còpia amb l'IBAN emmascarat i original conservat. Si l'organisme accepta la còpia emmascarada és [A verificar: tresorer] per a cada convocatòria.
- **Permisos** al servidor per a tres rols; la resta, «no trobat» i registre de l'intent.
- **Registre** de tot canvi (RN-M09A-16). Conservació dels paquets i resolucions [A validar: gestoria, Q-14].

<a id="M09-ajuts-13-riscos"></a>
## M09-ajuts-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| Ningú no dona d'alta les convocatòries | Alt: el calendari queda buit | Responsable designat per la junta; idea de l'assistent d'ajuts (12) | Junta |
| Avisos que no arriben (correu brossa, proveïdor) | Alt: termini perdut | Avís també a l'app; el calendari mostra els tancaments propers | Informàtica |
| Factures o comprovants que falten en justificar | Alt: reintegrament | Avís de «sense factura» des del registre de la despesa (part principal) | Tresorer |
| Documents amb dades personals pujats per error | Mitjà (RGPD) | Text d'ajuda, revisió del responsable, anul·lació del fitxer | Junta |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M09A-01 | Qui és el responsable dels ajuts i de cada sol·licitud | El tresorer, si no se'n designa cap altre | Junta |
| S-M09A-02 | Quines convocatòries s'han de vigilar (organismes i línies) | Cap; les dona d'alta el responsable | Junta |
| S-M09A-03 | Qui rep els avisos | Responsable i tresorer | Junta |
| S-M09A-04 | Avisos també abans de la data de justificació (30, 14 i 7 dies) | Sí | Junta |
| S-M09A-05 | Format de justificació que demana cada organisme (F §7) | Paquet genèric (resum, llistat i ZIP) | Junta |
| S-M09A-06 | Conservació de sol·licituds, resolucions i paquets | Fins que la gestoria ho digui (Q-14) | Gestoria |
| S-M09A-07 | L'organisme de cada convocatòria accepta comprovants amb l'IBAN emmascarat ([A verificar], 051) | `unknown`: el paquet porta la còpia emmascarada i l'original es dona a part si el demanen | Tresorer |
| S-M09A-08 | Termini legal per respondre un requeriment d'esmena (RN-M09A-19) [A verificar] | La data límit l'escriu la persona a partir del requeriment; la plataforma no la calcula | Gestoria |
| S-M09A-09 | Dies dels avisos d'un requeriment (RN-M09A-19) | Immediat, i 7 i 2 dies abans de la data límit | Junta |

**Revisió de dubtes (aplicada a mà)**
1. **«Tancada» té dos sentits:** final normal (justificada i acceptada) i «no es presenta». Es distingeixen pel motiu, sense estat nou, per mantenir la llista d'estats demanada. Propietari: cap (coherent amb les instruccions).
2. **Reintegrament:** si l'organisme accepta menys del concedit, el club ha de retornar diners. No hi ha cap estat ni tipus de moviment per a això. Proposta: es registra com a despesa del 09 amb la resolució com a document (en lloc de la factura) i la sol·licitud passa a «tancada». Propietari: tresorer.
3. **Renúncia a un ajut concedit:** la llista d'estats no hi té camí directe. Proposta: l'administrador desfà l'última transició amb motiu i la tanca. Si passa sovint, caldrà un camí «concedida → tancada». Propietari: junta.
4. **Rol de junta:** els permisos d'aquest apartat donen accions a la junta, que encara no és un rol aprovat (P-04, S-M01-23). Propietari: junta.

<a id="M09-ajuts-14-aprovar"></a>
## M09-ajuts-14 Què cal aprovar abans de començar

**Aprovat el 28/10/2026** pel responsable del projecte, alhora que els 02, 03, 06 i 09 (amb l'apartat d'ajuts), sense canviar cap regla ni cap criteri. Respostes d'aquesta aprovació:
- Els **supòsits per defecte** s'accepten per començar i **no bloquegen el codi**.
- **Per entrar en producció** cal respondre els [A verificar] externs i les decisions de la junta ([ordre del dia](#ordre-del-dia-junta)).
- Tots els [A validar] i [A verificar] continuen oberts amb el seu propietari: aquesta aprovació no els resol.

Punts que es van presentar per aprovar:

1. **Aquest apartat**, amb la llista d'estats i les transicions de RN-M09A-01.
2. **Supòsits per defecte** S-M09A-01 (responsable: el tresorer), S-M09A-03 (responsable i tresorer reben els avisos) i S-M09A-04 (avisos també abans de justificar) [A validar: junta].
3. **Per fer-lo servir** (no per començar): les convocatòries que s'han de vigilar (S-M09A-02) [A validar: junta].


<a id="M09-addenda-058"></a>
## M09 — Addenda de la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md): IVA per tipus de càrrec, donatius, termini d'esmena i conservació

Aprovada el 29/10/2026. **No canvia cap regla aprovada** del 09 ni de l'apartat d'ajuts. La facturació continua desactivada fins que es resolguin P-02 i P-47 (RN-M09-19).

**Respostes que confirmen el que ja diu el 09:** la llicència és sempre ingrés del soci i despesa a la federació, amb marge 0 per als socis i +20 € per als no socis (S-M09-14 i S-M06-11; RN-M09-20). Els moviments que arriben després del tancament entren al període obert amb la data original (RN-T31 de la [053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md); RN-M09-16).

**Ajustos nous**
| Clau de l'ajust | Valor inicial | Qui el canvia | Data d'entrada en vigor |
|---|---|---|---|
| `billing.vat_rate_by_charge_kind` (per tipus de càrrec) | Inscripció (cursos, sortides i material llogat): amb IVA, tipus [A verificar: gestoria]. Quota i llicència: exemptes | Tresorer, amb avís (RN-AJ-04) | Sí |
| `billing.vat_exemption_text` | [A verificar: gestoria] | Tresorer | Sí |

**Regles noves**
| ID | Regla |
|---|---|
| RN-M09-29 | **Es factura tot cobrament** quan s'activi la facturació (RN-M09-19): quota, inscripció, llicència i material. Les línies de quota i de llicència porten el text d'exempció; la resta, el tipus d'IVA de l'ajust. La botiga en línia continua fora d'abast. El servei homologat i Verifactu continuen oberts (P-02, P-47) |
| RN-M09-30 | **Donatius de persones** (substitueix el supòsit S-M09-03): un `OtherIncome` de tipus `donation` pot tenir com a donant una persona (`donor_person`, FK Person), amb el nom i el NIF del seu document (00). Cada any, el tresorer genera el certificat de donatiu de cada donant i el fitxer per al model 182. Que el club pugui emetre certificats deduïbles: [A verificar: gestoria]; fins llavors, el certificat no es lliura |
| RN-M09-31 | **Conservació** (punt 7 de la 058): els registres econòmics (despeses, altres ingressos, factures, moviments) **no s'eliminen mai**. Les dades personals que hi surten s'anonimitzen passat el termini legal [A verificar: gestoria, Q-14]; el que identifica la persona se substitueix per la referència anònima, com al registre d'activitat (028) |
| RN-M09A-23 | **Termini d'esmena:** la convocatòria pot tenir un termini d'esmena opcional (`amendment_term_days`, null). Si hi és, en registrar un requeriment es proposa la data límit; la persona la pot canviar (RN-M09A-19). Sense prioritat |

**Criteris d'acceptació**
- **CA-M09-36** Donat la facturació activada per a tots els tipus, quan es factura una quota, llavors la línia porta el text d'exempció i cap IVA; quan es factura una inscripció a un curs, porta el tipus d'IVA de l'ajust vigent a la data del cobrament.
- **CA-M09-37** Donat dos donatius d'una mateixa persona en un any, quan el tresorer genera els certificats, llavors n'hi ha un sol per a aquella persona amb la suma, i el fitxer del model 182 en porta una sola línia.
- **CA-M09-38** Donat una persona esborrada (RGPD) amb una despesa i un donatiu de fa més del termini legal, quan corre l'anonimització, llavors els registres continuen existint amb els imports i les dates, i el nom i el NIF s'han substituït per la referència anònima.
- **CA-M09A-26** Donat una convocatòria amb `amendment_term_days` 10, quan es registra un requeriment rebut l'1/3, llavors la data límit proposada és l'11/3 i es pot canviar.

**Tasques**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M09-27 | IVA per tipus de càrrec i text d'exempció a les factures ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md)) | S | `apps/invoicing/`, ajustos | T-M09-19, T-M09-26 | CA-M09-36 |
| T-M09-28 | Donant persona, certificat anual de donatius i fitxer del model 182 (lliurament bloquejat fins a la resposta de la gestoria) | M | `apps/expenses/donations.py` | T-M09-08 | CA-M09-37 |
| T-M09-29 | Anonimització dels registres econòmics passat el termini legal (bloquejada fins a Q-14) | M | `apps/expenses/retention.py`, tasques de la cua | T-M09-04, T-M09-08 | CA-M09-38 |
| T-M09A-16 | Termini d'esmena opcional per convocatòria (sense prioritat) | S | `apps/grants/models.py`, migració | T-M09A-02 | CA-M09A-26 |

<a id="M09-addenda-059"></a>
## M09 — Addenda de la [059](decisions/059-rols-i-permisos-editables.md): permisos editables i configuració inicial

Aprovada el 30/10/2026. **No canvia cap regla** del M09. Les taules de [M09-4](#M09-4-rols) i [M09-ajuts-4](#M09-ajuts-4-rols) passen a ser la **configuració inicial** dels permisos del mòdul, que l'administrador pot canviar des de l'app ([peça comuna](#rols-i-permisos-059)). Els canvis, cel·la per cel·la, són a la [matriu inicial](#rols-i-permisos-059-matriu).

**Què canvia**
- El **President** registra despeses amb factura (MG1) i veu el marge (MG6).
- El **responsable de cursos i sortides** registra despeses de les seves activitats i en veu el marge.
- El **responsable de material no registra despeses**, a diferència del supòsit S-M09-01, que queda resolt així.
- Pagar despeses, repartir-les, emetre factures, tancar i fer devolucions es queden com al pla.
- Obrir els documents de justificació (RN-M09-23, [051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) i reobrir un període (MG12) són regles protegides.
- L'apartat d'ajuts no canvia. La Junta hi actua sobre les sol·licituds de què és responsable.

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M09-30 | Declarar els permisos del 09 i de l'apartat d'ajuts al catàleg (MG1 a MG14, AJ1 a AJ13; C5, MG12 i AJ12 protegits) i comprovar-los a totes les vistes i serveis | S | `apps/expenses/permissions.py`, `apps/grants/permissions.py` | T-RP-01 | Proves per cel·la del 09 (CA-RP-13) |

<a id="M09-addenda-060"></a>
## M09 — Addenda de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): nucli de despeses abans i cost de cancel·lació d'un centre

Aprovada el 31/10/2026. **No canvia cap regla** del M09.

**Ordre.** El 09 es construeix després del 03. Però el **nucli de despeses (T-M09-02 a T-M09-05)**, que no depèn ni del 02 ni del 03, es construeix just després del 06: és condició perquè el 06 entri en producció ([RN-M06-27](#M06-addenda-060)), perquè el pagament a la federació és una despesa del 09 (RN-M09-20).

| ID | Regla |
|---|---|
| RN-M09-32 | **Cost de cancel·lació d'un centre.** La factura que un centre de busseig emet per una activitat cancel·lada es registra com una despesa normal, de categoria «lloguer», lligada a l'activitat cancel·lada, a la seva llista de lloguer i al departament de l'activitat. Compta com a «factura del centre» per a RN-M09-04; l'estimació del 03 ja és 0, perquè les assignacions estan anul·lades. El marge mostra la pèrdua (L-M09-04). Mai genera cap càrrec als participants |

- **CA-M09-39** Donat una sortida cancel·lada amb una llista de lloguer enviada i una factura de cancel·lació del centre de 3000, quan el tresorer la registra lligada a l'activitat, llavors el marge real de l'activitat resta 3000 (i res de l'estimació del 03), es pot fer el tancament econòmic amb pèrdua i cap participant té cap càrrec nou.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M09-31 | Despesa de cancel·lació d'un centre lligada a una activitat cancel·lada i a la seva llista de lloguer | S | `apps/expenses/`, `apps/margins/services.py` | T-M09-05, T-M09-11, T-M03-24 | CA-M09-39 |

---

<a id="M06"></a>
# Mòdul 06 — Llicències

**Estat: aprovat** pel responsable del projecte el 28/10/2026 ([M06-14](#M06-14-aprovar)), alhora que els 02, 03, 06 i 09. Ampliat per la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) amb una [addenda](#M06-addenda-058) (T-M06-21 a T-M06-24, amb la precisió del 29/10/2026), sense canviar cap regla. Els permisos de la taula de rols són la configuració inicial, editable des de l'app per l'administrador ([059](decisions/059-rols-i-permisos-editables.md), [addenda](#M06-addenda-059)).

**Fonts:** document de funcionalitats (F §8.1 Llicències federatives, processos 9.12 i 9.16), mapa de la plataforma v8 (M06 Llicències), respostes del responsable del projecte del 20/10/2026 (tres durades; marge 0 per a la llicència d'un soci) i del 22/10/2026 (opció de llicència sense ser soci, amb un recàrrec que faci que fer-se soci surti gairebé sempre a compte; preus configurables amb nota obligatòria en canviar-los), decisions [036](decisions/036-fecdas-alia.md) (la FECDAS és un aliat, sense cap acord d'integració), [013](decisions/013-imputacio-comissions.md), [017](decisions/017-pagaments-metodes-i-domiciliacions.md), [021](decisions/021-persones-no-socies-com-a-convidades.md), [024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), [035](decisions/035-dades-nomes-dins-ue.md), [041](decisions/041-web-installable-i-avisos-sense-push.md) i [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md); seccions [M01](#M01) (registre mínim de llicència), [M05b](#M05b) i [M09](#M09) (despesa de la federació).

**Proveïdor de pagaments.** El 06 no parla mai amb el proveïdor: crea el càrrec de tipus «llicència» (00) i el cobra amb els serveis del [05b](#M05b-8-serveis). Llicències: targeta, Bizum o transferència, mai domiciliació (017; RN-69 de la 00).

**FECDAS.** És la font dels tipus de llicència, dels preus de cada durada, del format per tramitar-les i de les dades que demana [A verificar: FECDAS]. No hi ha cap integració: la secretaria tramita amb el llistat exportat.

**Informació nova (28/10/2026) [A verificar: FECDAS i responsable de cursos i sortides].** La FECDAS distingeix la llicència d'**aficionat** (1 a 3 estrelles) de la de **tècnic** (titulacions superiors i instructors). Pot ser que ja no hi hagi llicència d'un dia: avui només s'hi veuen l'**any natural** (fins al 31/12; si s'obté a mig any dura menys i pot tenir un preu per trams) i els **365 dies**. La FECDAS demana la **data de naixement** en tramitar, i la llicència **no és vigent fins al correu de confirmació de la FECDAS** (pas 4 de P-M06-E).

<a id="M06-resum"></a>
**Resum d'una pàgina**
| | |
|---|---|
| **Intenció** | Portar totes les llicències federatives dels socis (i, quan la junta ho activi, de persones de fora) en un sol lloc: tipus amb categoria (aficionat, tècnic, altres) i regla de validesa (any natural, 365 dies i, només si s'activa, un dia), preu de soci igual al de la federació, preu de no soci amb recàrrec i l'estalvi de fer-se soci a la vista, pagament dins l'app, avisos abans que caduquin, llistat per tramitar-les a la federació, i saber a l'instant si la llicència d'una persona és vigent. |
| **Processos que cobreix** | P-M06-A Preus i tipus · P-M06-B Demanar i pagar una llicència (soci) · P-M06-C Llicència per a una persona de fora (F 9.16) · P-M06-D «Ja en tinc una» · P-M06-E Tramitar a la federació · P-M06-F Avisos i renovació (F 9.12) · P-M06-G Cancel·lar · P-M06-H Passar els registres del 01 al 06 |
| **Tasques** | 25 (T-M06-01 a T-M06-25; de la T-M06-21 a la T-M06-24 les afegeix la 058 i la T-M06-25, la 059); la còpia de lectura del 01 és la T-M01-31 |
| **Què el bloqueja** | Per construir: el 05b (cobrar), el mecanisme d'esdeveniments (T-M05b-21) i el servei de lectura del 01 (T-M01-30, 049). La font única de la llicència ja és aprovada ([052](decisions/052-llicencia-font-unica-al-06.md)). Per entrar en producció: tipus, categories, preus, trams i format de tramitació [A verificar: FECDAS] i recàrrec dels no socis [A validar: junta]; data de naixement (punt prioritari 0 de l'[ordre del dia](#ordre-del-dia-junta)) |
| **Què cal aprovar** | Aquesta secció i els supòsits S-M06-04, 05, 07 i 09 ([M06-14](#M06-14-aprovar)) |

<a id="M06-1-intencio"></a>
## M06-1 Intenció, abast i fora d'abast

**Per què.** Avui les llicències es porten entre Cluber i la federació (P-28). El 01 només en guarda un registre mínim perquè no es perdi en deixar Cluber (024). Falta cobrar-les dins l'app, avisar abans que caduquin, preparar la tramitació i, més endavant, oferir-les a persones que no són sòcies.

**Resultat esperat.**
- Cada soci veu «La meva llicència»: estat, venciment i botó per renovar.
- La secretaria veu totes les llicències amb filtres per tipus, categoria i estat, els venciments a 60, 30 i 7 dies i un llistat per enviar a la federació.
- Un soci paga la llicència al preu de la federació; una persona de fora, quan la junta ho activi, paga el preu de no soci i veu quant s'estalviaria fent-se sòcia.
- Els cursos i les sortides saben si la llicència d'una persona és vigent amb una sola crida.

**Com sabrem que funciona.**
- Cap llicència anual caduca sense que el titular hagi rebut els tres avisos.
- El preu de soci és sempre igual al preu de la federació (marge 0) i el de no soci el supera en el recàrrec.
- `licences.current` dona el mateix resultat que el càlcul a mà de les dates de l'exemple de [M06-7](#M06-7-regles).
- Hi ha una sola font de la llicència d'una persona (sense dades duplicades entre el 01 i el 06).

**Dins de l'abast.**
- Tipus de llicència amb categoria i regla de validesa, i preus amb versions i trams per dates, amb nota obligatòria en canviar-los.
- Regles de validesa: any natural (fins al 31/12), 365 dies i, **només si s'activa l'opció** `licences.day_enabled`, un dia [A validar: responsable de cursos i sortides].
- Llicència de soci, i de no soci com a **opció que activa la junta** (avui ser soci és obligatori).
- «Ja en tinc una»: número i venciment, sense tramitar-ne cap.
- Pagament amb el 05b, també com a convidat ([021](decisions/021-persones-no-socies-com-a-convidades.md)).
- Estats, venciments, avisos a 60, 30 i 7 dies (agrupats per a la secretaria), renovació i sol·licitud anticipada de l'any següent.
- Llistat exportable per tramitar a la federació; marcar tramitada i vigent.
- Cancel·lació, amb proposta de devolució al tresorer.
- Pas únic dels registres mínims del 01 al 06.

**Fora d'abast.**
- Connexió amb cap sistema de la federació (alta automàtica, consulta de llicències): la FECDAS és un aliat, sense cap acord d'integració ([036](decisions/036-fecdas-alia.md)). Es fa amb el llistat.
- Assegurança de la llicència, sinistres i accidents: fora de la plataforma.
- Certificat mèdic o qualsevol dada de salut (P-07).
- Titulacions de busseig: són del 02 (S-M02-10, S-M02-11).
- La despesa del pagament a la federació: és una despesa del [09](#M09-7-regles) (RN-M09-20).

<a id="M06-2-dependencies"></a>
## M06-2 Dependències

**De què depèn.**
| Mòdul | Què en fa servir el 06 |
|---|---|
| 00 | Persona i dades mínimes (V-04: per a una llicència, també el document); enllaços de convidat (V-02); càrrec de tipus «llicència» amb departament (RN-60 a RN-73); departaments; correu i avisos; cua de tasques; permisos; registre d'activitat |
| 01 | `members.is_member(person, on)` per al preu; `members.licence_records()` per passar els registres mínims al 06 (només lectura, [049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) |
| 05b | `payments.start_payment`, `payments.payment_status`, rebut; esdeveniment `charge.paid` (049); devolucions fetes pel tresorer (`payments.refund`) |

La taula d'estat diu que el 06 depèn del 01 i del 05b; això no canvia. **El 06 no depèn del 02** ([052](decisions/052-llicencia-font-unica-al-06.md)): la llicència d'un dia no es lliga a cap activitat. Si cal, és el 02 qui demana al 06 si una activitat necessita llicència d'un dia (requisit pendent RP-M02-01 de [M02-13](#M02-13-riscos), condicional a `licences.day_enabled`) o una categoria concreta (RP-M02-02).

**Què depèn del 06.**
| Mòdul | Què necessita |
|---|---|
| 02 | `licences.current(person, on)` per al requisit de llicència vigent, amb la categoria (substitueix `members.licence_record`) |
| 01 | Esdeveniments `licence.issued`, `licence.renewed`, `licence.expired` i `licence.cancelled` per mantenir la seva còpia de lectura ([052](decisions/052-llicencia-font-unica-al-06.md), [addenda del M01](#M01-addenda-052)). El 01 no crida cap servei del 06 |
| 08 | Llicències per caducar i per tramitar |
| 09 | Ingressos de les llicències (amb el 04) i despesa de la federació |

<a id="M06-3-capacitats"></a>
## M06-3 Capacitats i històries d'usuari

| # | Capacitat | Qui | On |
|---|---|---|---|
| C1 | Tipus (categoria i regla de validesa) i preus | Tresorer [A validar: junta, S-M06-05] | Configuració |
| C2 | «La meva llicència» i renovar | Soci, persona de fora | Compte personal o enllaç |
| C3 | Demanar una llicència des de la web (no socis, quan s'activi) | Visitant | Web |
| C4 | «Ja en tinc una» | Persona de fora, soci | Formulari |
| C5 | Llistat, filtres i venciments | Secretaria | Llicències |
| C6 | Exportar per a la federació i marcar tramitada o vigent | Secretaria | Llicències |
| C7 | Avisos de venciment | Sistema | Correu i app |
| C8 | Cancel·lar | Secretaria (i tresorer per a la devolució) | Fitxa |
| C9 | Vigència per a cursos i sortides | Sistema | Servei per al 02 |

**Històries d'usuari**
- **HU-M06-01.** Com a soci, vull veure l'estat i el venciment de la meva llicència i renovar-la pagant dins l'app.
- **HU-M06-02.** Com a persona de fora, vull demanar una llicència (d'un dia, només si l'opció és activada), veure el preu de soci al costat del meu i pagar sense crear cap compte.
- **HU-M06-03.** Com a persona de fora que ja té llicència, vull indicar-ne el número i el venciment perquè no me'n tramitin cap altra.
- **HU-M06-04.** Com a secretaria, vull el llistat de llicències pagades per tramitar i un fitxer per enviar a la federació.
- **HU-M06-05.** Com a secretaria, vull veure les llicències que caduquen d'aquí a 60, 30 i 7 dies.
- **HU-M06-06.** Com a responsable de cursos i sortides, vull saber si la llicència d'un participant serà vigent el dia de l'activitat (només sí o no).

<a id="M06-4-rols"></a>
## M06-4 Rols i permisos

Llegenda com a [M01-4](#M01-4-rols). A les taules, «[A validar]» sense propietari vol dir **junta** (Q-01, P-04).

| # | Acció | Visitant | Part. no soci | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Resp. comunicació | Dept. Història | Junta | Administrador | Resp. botiga |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LC1 | Veure «La meva llicència» i renovar-la | — | Propi (enllaç) | Propi | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci | Propi si és soci |
| LC2 | Demanar una llicència des de la web (si l'opció de no socis està activada) | Sí | Sí | — | — | — | — | — | — | — | — | — | — | — |
| LC3 | «Ja en tinc una» | — | Propi (enllaç) | Propi [A validar: secretaria] | — | Sí | — | — | — | — | — | — | Sí | — |
| LC4 | Llistat, filtres i venciments | — | — | — | — | Sí | — | — | Consulta | — | — | Consulta [A validar] | Sí | — |
| LC5 | Exportar per a la federació; marcar tramitada i vigent | — | — | — | — | Sí | — | — | — | — | — | — | Sí | — |
| LC6 | Cancel·lar una llicència | — | — | — | — | Sí | — | — | — | — | — | — | Sí | — |
| LC7 | Fer la devolució d'una llicència cancel·lada (05b) | — | — | — | — | — | — | — | Sí | — | — | — | — | — |
| LC8 | Tipus, preus i recàrrec | — | — | — | — | — | — | — | Sí [A validar] | — | — | Consulta | Sí | — |
| LC9 | Activar l'opció de llicència per a no socis (per decisió de la junta) | — | — | — | — | — | — | — | — | — | — | — | Sí | — |
| LC10 | Veure si la llicència d'un participant és vigent | — | — | — | Les seves sessions (només «vigent sí o no» per a la data de la sessió) | Sí | Les seves activitats (només «vigent sí o no» per a la data de l'activitat) | — | — | — | — | — | Sí | — |
| LC11 | Passar els registres del 01 al 06 | — | — | — | — | — | — | — | — | — | — | — | Sí | — |

**Per objecte.**
- **Titular:** només les seves llicències.
- **Instructor i responsable de cursos i sortides:** només «vigent sí o no» **per a la data de la sessió o de l'activitat** dels participants de les seves sessions o activitats; mai la data de venciment, el número federatiu ni el document. És la mateixa regla que al [M02-4](#M02-4-rols).
- **Tresorer:** imports i estats per cobrar i fer devolucions; no el document.
- **Secretaria:** totes les llicències i les dades que demana la federació.

<a id="M06-5-processos"></a>
## M06-5 Processos pas per pas

**Wireframes existents:** `socis.html#llicencia` (bloc de llicència al compte personal). **Falten** (T-M06-01): «La meva llicència» amb renovació, pantalla pública de llicència per a no socis amb la comparació de preus, «Ja en tinc una», llistat de la secretaria amb filtres i venciments, tramitació, preus.

**Estats d'una llicència.** El cicle de F §8.1 (sol·licitada, pagada, tramitada; vigent → per renovar → caducada, o cancel·lada) es desa i es deriva així:
| Estat que es veu | D'on surt |
|---|---|
| **Sol·licitada** | `requested`: s'ha demanat i el càrrec és pendent |
| **Pagada** | `paid`: el càrrec és pagat i falta tramitar-la |
| **Tramitada** | `filed`: la secretaria l'ha enviada a la federació i espera la confirmació |
| **Vigent** | `active` i avui és entre `starts_on` i `expires_on` |
| **Per renovar** | `active` i caduca d'aquí a 60 dies o menys (ajust `licences.to_renew_days`) (no per a les d'un dia) |
| **No tramitada a temps** | `lapsed`: llicència d'un dia pagada (o tramitada) que no ha arribat a `active` abans d'acabar el dia de la llicència (RN-M06-20; només si l'opció d'un dia és activada) |
| **Caducada** | `active` i `expires_on` és anterior a avui |
| **Cancel·lada** | `cancelled`, amb motiu |

### P-M06-A Preus i tipus
1. El tresorer dona d'alta els tipus de llicència de la federació [A verificar: FECDAS], cadascun amb la seva **categoria** (aficionat, tècnic, altres) i la seva **regla de validesa** (any natural, 365 dies i, si l'opció és activada, un dia). Per a cada tipus, hi posa el **preu de la federació** i el **recàrrec de no soci** [A validar: junta]; si la federació té preus per trams de l'any (any natural obtingut a mig any), cada tram és una versió de preu amb les seves dates (RN-M06-18).
2. El sistema fixa el preu de soci = preu de la federació (RN-M06-05) i calcula el de no soci. Cada canvi crea una versió nova amb nota obligatòria i avisa la secretaria i la junta (respostes del 22/10/2026).

### P-M06-B Demanar i pagar una llicència (soci)
| Pas | Qui | Què passa | Pantalla |
|---|---|---|---|
| 1 | Soci | Obre «La meva llicència» i tria el tipus (que ja porta la seva regla de validesa); des de la data d'obertura de l'any següent, també pot triar l'any següent amb inici l'1/1 (RN-M06-21) | `/socis/llicencia` |
| 2 | Sistema | Mostra el preu de soci, les dates de validesa i les dades que s'enviaran a la federació | Ídem |
| 3 | Soci | Confirma: es crea la llicència `requested` i el càrrec «llicència» | — |
| 4 | Soci | Paga amb targeta, Bizum o transferència (05b) | Pantalla de pagament |
| 5 | Sistema | En rebre `charge.paid`, passa la llicència a `paid` i avisa la secretaria | — |

### P-M06-C Llicència per a una persona de fora (F 9.16)
1. Només si l'opció de no socis està activada (RN-M06-03). La persona entra a la pàgina pública i tria el tipus. Els tipus d'un dia només surten si també és activada l'opció `licences.day_enabled` (RN-M06-01); si no, no es poden triar ni demanar.
2. El sistema mostra el preu de no soci al costat del de soci, l'estalvi en la llicència i la quota anual de soci, per comparar (RN-M06-07).
3. La persona escriu les dades mínimes (V-04 de la 00) i accepta la informació de privacitat; es crea com a convidada amb l'enllaç segur (021).
4. Paga dins l'app; la resta és com a P-M06-B des del pas 5.

### P-M06-D «Ja en tinc una»
1. La persona (o la secretaria) escriu el número, el tipus i la data de venciment de la llicència que ja té.
2. Es desa com a llicència `active` amb origen `external`, sense càrrec ni tramitació. La secretaria la pot comprovar [A validar: secretaria, S-M06-04].

### P-M06-E Tramitar a la federació
| Pas | Qui | Què passa |
|---|---|---|
| 1 | Secretaria | Obre «Per tramitar»: llicències `paid` |
| 2 | Secretaria | Exporta el llistat amb les dades que demana la federació (RN-M06-11). No es desa; queda al registre amb l'empremta |
| 3 | Secretaria | Les tramita a la federació (fora de la plataforma) i les marca `filed` |
| 4 | Secretaria | Quan la federació les confirma per correu (la llicència no és vigent fins llavors), hi posa el número federatiu i les marca `active` (si no hi ha espera, del pas 1 es pot passar directament a `active`) |

### P-M06-F Avisos i renovació (F 9.12)
1. Cada dia, la cua mira les llicències d'any natural i de 365 dies que caduquen d'aquí a 60, 30 i 7 dies i avisa el titular (correu i app, sense push; el convidat, per correu amb l'enllaç), en lots perquè no se n'enviïn centenars de cop. La secretaria **no** rep un avís per llicència: rep un sol resum per dia, agrupat per data de venciment i categoria, i ordenat per data i nom (RN-M06-12). Les d'un dia no s'avisen.
2. El titular confirma que vol renovar i tria el tipus; paga al preu que li toqui (soci o no soci).
3. Es crea una llicència nova lligada a l'anterior (`renewal_of`) que comença l'endemà del venciment (o avui, si ja ha caducat); la secretaria la tramita com a P-M06-E. Per a l'any natural, des de la data d'obertura de l'any següent, la renovació es pot demanar abans de l'1/1 amb inici l'1/1 (RN-M06-21).

### P-M06-G Cancel·lar
1. La secretaria cancel·la una llicència amb motiu. Si encara no és pagada, el càrrec s'anul·la.
2. Si és pagada i no tramitada, es crea una proposta de devolució per al tresorer, que la fa amb el 05b.
3. Si ja és tramitada, la devolució depèn de la federació [A verificar: FECDAS]; el supòsit és que no se'n fa (S-M06-06).

### P-M06-H Passar els registres del 01 al 06
1. Quan el 06 entra en producció, l'administrador llança el pas únic: llegeix `members.licence_records()` i crea una llicència `active` amb origen `imported_m01` per a cada registre (sense càrrec).
2. Mostra el resum (creats, ja existents, errors) i no escriu res fins a confirmar. Es pot desfer per lot.
3. Cada llicència creada recorda de quin registre del 01 surt; el seu `licence.issued` actualitza aquell registre i no en crea cap de nou ([052](decisions/052-llicencia-font-unica-al-06.md)). A partir d'aquí, la secretaria ja no edita el registre del 01: tot es fa al 06.

<a id="M06-6-entitats"></a>
## M06-6 Entitats i camps

App Django `licences` (nova). Noms de codi en anglès. Imports en cèntims. Cap dada de salut ni de pagament.

### LicenceType (tipus) i LicencePrice (preu)
- `LicenceType`: `name` (únic; llista de la federació [A verificar: FECDAS]), `description`, `category` (`amateur` aficionat, `technical` tècnic, `other` altres), `validity_rule` (`calendar_year` any natural, `days_365` 365 dies, `single_day` un dia; configurable), `active`. Un tipus `single_day` no es pot crear ni activar mentre `licences.day_enabled` és desactivada.
- `LicencePrice` (només INSERT; una versió nova per canvi): `licence_type`, `federation_cost_cents`, `non_member_surcharge_cents`, `valid_from`, `valid_to` (null), `note` (obligatòria), `created_by`. `valid_from` i `valid_to` són les dates d'inici de la llicència a què s'aplica el preu: així es fan els **trams de l'any** (per exemple, un preu de gener a juny i un altre de juliol a desembre) (RN-M06-18). El preu de soci és `federation_cost_cents` i el de no soci, `federation_cost_cents + non_member_surcharge_cents`.

### Licence (llicència)
| Camp | Tipus | Restriccions |
|---|---|---|
| `person` | FK Person (00, PROTECT) | — |
| `licence_type` | FK LicenceType | — |
| `validity_rule` | `calendar_year`, `days_365`, `single_day` | Còpia de la regla del tipus en demanar-la |
| `status` | `requested`, `paid`, `filed`, `active`, `cancelled`, `lapsed` | Transicions de RN-M06-09; `lapsed` només per a les d'un dia (RN-M06-20) |
| `origin` | `club`, `external`, `imported_m01` | `external` i `imported_m01` no tenen càrrec |
| `starts_on`, `expires_on` | `DateField` | `expires_on ≥ starts_on` (`CHECK`); calculades (RN-M06-02) excepte `external` |
| `federation_number` | `CharField(30)` | Opcional; obligatori en passar a `active` si `origin = club` [A validar: secretaria] |
| `price_kind` | `member`, `non_member` null | Fixat en demanar-la |
| `price_cents` | `PositiveIntegerField` null | Còpia del preu en demanar-la |
| `charge` | FK càrrec (00) null | Únic |
| `renewal_of` | FK self null | — |
| `m01_record_ref` | identificador del registre del 01 null | Només `imported_m01` (052, punt 8) |
| `filed_by`, `filed_at`, `activated_by`, `activated_at` | — | — |
| `cancellation_reason`, `cancelled_by` | — | Obligatori si `cancelled` |
| `import_batch` | FK lot d'importació (00) null | Només `imported_m01` |
**Restriccions:** únic parcial `(person, licence_type) WHERE status IN ('requested','paid','filed') AND validity_rule <> 'single_day'` (una sola llicència anual en curs per tipus); si s'activa la llicència d'un dia, únic parcial `(person, licence_type, starts_on) WHERE status IN ('requested','paid','filed') AND validity_rule = 'single_day'`, per poder-ne tenir diverses per a dates diferents (RN-M06-19); índexs `(status, expires_on)` i `(person, expires_on)`.

### LicenceReminder i RefundProposal
- `LicenceReminder` (només INSERT): `licence`, `days_before` (60, 30, 7), `sent_at`. Únic `(licence, days_before)`.
- `LicenceReminderDigest` (només INSERT): `day`, `days_before`, `count`, `sent_to` (secretaria), `sent_at`. Únic `(day, days_before)`: un sol resum per dia i tram per a la secretaria (RN-M06-12).
- `LicenceRefundProposal`: `licence`, `amount_cents`, `reason`, `status` (`proposed`, `done`, `rejected`), `decided_by`. Com la `RefundProposal` del 02: el tresorer la fa amb `payments.refund`.

### Valors configurables (pantalla d'ajustos, T-M06-20)
Valors de la [regla general](#regles), a la pantalla d'ajustos del mòdul sobre la [peça comuna](#valors-configurables-055) de la [055](decisions/055-ajustos-configurables-i-addendes.md): cada canvi es comprova al servidor (rol i rang), queda al registre amb el valor anterior i, si afecta diners, porta data d'entrada en vigor i avisa per correu el tresorer i la junta (RN-AJ-03 i RN-AJ-04). Els valors inicials són els supòsits que ja hi havia; les preguntes obertes continuen obertes.

| Clau de l'ajust | VC | Valor inicial | Rang vàlid | Qui el canvia | Data d'entrada en vigor |
|---|---|---|---|---|---|
| `licences.non_members_enabled` | VC-39 | Desactivada | Sí o no | Administrador, per decisió de la junta | — |
| `licences.day_enabled` | VC-40 | Desactivada | Sí o no | Administrador, quan es confirmi que la llicència d'un dia existeix [A validar: responsable de cursos i sortides; A verificar: FECDAS]. Si es confirma que no existeix, la retirarà la decisió 056 | — |
| `licences.reminder_days` | VC-41 | 60, 30 i 7 | 1 a 120 | Secretaria | — |
| `licences.to_renew_days` | VC-41 | 60 | 1 a 120 | Secretaria | — |
| `licences.next_year_opens_on` (dia i mes, RN-M06-21) | VC-42 | 1/12 [A verificar: FECDAS] | 1/10 a 31/12 | Secretaria | — |

Tipus, categories, regles de validesa i preus (VC-38) ja són dades amb versions (`valid_from`); un canvi de preu també avisa el tresorer i la junta (RN-AJ-04). Es queden: `LICENCE_REMINDER_BATCH_SIZE`, variable d'entorn d'informàtica (VC-43), i preu de soci igual al de la federació (VC-44, regla).

<a id="M06-7-regles"></a>
## M06-7 Regles de negoci i càlculs

| ID | Regla | Font |
|---|---|---|
| RN-M06-01 | **Regles de validesa** (una per tipus, configurable): **any natural** (des del dia d'inici fins al 31 de desembre d'aquell any), **365 dies** (RN-M06-02) i **un dia** (només aquell dia). La d'un dia queda **darrere de l'opció `licences.day_enabled`, desactivada per defecte**: mentre ho estigui, cap tipus d'un dia no es pot crear, triar ni demanar, i RP-M02-01 i S-M06-07 són condicionals [A validar: responsable de cursos i sortides; A verificar: FECDAS, si avui existeix]. Cada tipus té també una **categoria**: aficionat (1 a 3 estrelles), tècnic (titulacions superiors i instructors) o altres [A verificar: FECDAS] | F §8.1; 28/10/2026 |
| RN-M06-02 | Dates: **any natural** → `expires_on` = 31 de desembre de l'any de `starts_on`. **365 dies** → `expires_on = starts_on + 364 dies`: la llicència cobreix 365 dies naturals **comptant el dia d'inici**; si hi ha un 29 de febrer pel mig, acaba dos dies abans del mateix dia de l'any següent (del 15/3/2026 al 14/3/2027; del 15/3/2027 al 13/3/2028; del 29/2/2028 al 27/2/2029) [A verificar: FECDAS, S-M06-02]. **Un dia** (només si l'opció és activada) → `expires_on = starts_on`. `starts_on` = el dia que es tramita, el que tria la persona (llicència d'un dia) o l'1/1 en una sol·licitud anticipada de l'any següent (RN-M06-21) | F §8.1; 28/10/2026 |
| RN-M06-03 | La llicència per a no socis és una **opció que activa la junta** (`licences.non_members_enabled`). Desactivada: la pàgina pública no existeix i només els socis en poden demanar | 22/10/2026 |
| RN-M06-04 | Preu de soci o de no soci segons `members.is_member(person, on=data en què es demana)`; queda copiat a la llicència. També en una sol·licitud anticipada de l'any següent (RN-M06-21), perquè l'estat de soci a l'1/1 encara no se sap [A validar: tresorer, S-M06-14] | F §8.1; 28/10/2026 |
| RN-M06-05 | **Preu de soci = preu de la federació** (marge 0). El sistema no admet cap preu de soci diferent | 20/10/2026; F §8.1 |
| RN-M06-06 | **Preu de no soci = preu de la federació + recàrrec** [A validar: junta, S-M06-01]. El recàrrec no pot ser negatiu | F §8.1; 22/10/2026 |
| RN-M06-07 | La pantalla del no soci mostra el preu de soci al costat, l'estalvi en la llicència (= recàrrec) i la quota anual de soci, sense dir que surt a compte si no és així | F §8.1 |
| RN-M06-08 | Un canvi de preu crea una versió nova amb nota obligatòria i avisa la secretaria i la junta; les llicències ja demanades conserven el seu preu | 22/10/2026 |
| RN-M06-09 | Transicions: `requested → paid` (només per `charge.paid`); `paid → filed → active`; `paid → active`; `requested`, `paid` o `filed` → `cancelled` amb motiu; `paid` o `filed` → `lapsed` (només la tasca diària i només les d'un dia, RN-M06-20). «Per renovar» i «caducada» es deriven de les dates. Una llicència `active` no es cancel·la: es deixa caducar [A validar: secretaria] | F §8.1 |
| RN-M06-10 | Càrrec de tipus «llicència», departament «General / Llicències» (provisional, S-M04-07, Q-19) i mètodes targeta, Bizum o transferència | 013; 017; RN-69 de la 00 |
| RN-M06-11 | El llistat per a la federació només porta les dades que la federació demana [A verificar: FECDAS] i que la plataforma ja té (V-04 de la 00). Es genera a demanda, no es desa i queda al registre amb l'empremta | 035; F §8.1 |
| RN-M06-12 | Avisos al titular a 60, 30 i 7 dies del venciment (ajust `licences.reminder_days`), per correu i a l'app (sense push), un sol cop per llicència i dia, enviats per la cua en lots (`LICENCE_REMINDER_BATCH_SIZE`). Com que gairebé totes les d'any natural caduquen el 31/12, **la secretaria no rep un avís per llicència**: rep un sol resum per dia i tram (60, 30 o 7), agrupat per data de venciment i categoria, i ordenat per data i nom, amb l'enllaç al llistat filtrat. Si ja hi ha una renovació en curs, no s'avisa. Les d'un dia (només si l'opció és activada) no s'avisen | F §8.1 i 9.12; 28/10/2026 |
| RN-M06-13 | `licences.current(person, on)` torna la llicència `active` que cobreix aquella data (si n'hi ha diverses, la que caduca més tard), amb la seva **categoria** i `status = active`. Si no n'hi ha cap però n'hi ha una `requested`, `paid` o `filed` que cobriria aquella data, torna `status = in_progress` (**en tràmit**) amb la categoria; si no, res. Les `cancelled` i les `lapsed` no compten | F §8.1 |
| RN-M06-14 | «Ja en tinc una»: es desa el número, el tipus i el venciment; no es crea càrrec ni tramitació | F §8.1 i 9.16 |
| RN-M06-15 | Cap dada de salut: ni certificat mèdic ni data de validesa (P-07). Si la federació en demana, es comprova fora de la plataforma | CLAUDE.md; P-07 |
| RN-M06-16 | Imports en cèntims; tot canvi d'estat, de preu i tota exportació, al registre d'activitat | CLAUDE.md |
| RN-M06-17 | **El 06 és l'únic propietari de les llicències** i emet, dins la mateixa transacció i amb el mecanisme de la 049: `licence.issued` (passa a `active`), `licence.renewed` (la renovació passa a `active`), `licence.expired` (la tasca diària, l'endemà de `expires_on`, una sola vegada) i `licence.cancelled`. Porten persona, tipus, durada (la regla de validesa, `validity_rule`), dates, origen i, si escau, `m01_record_ref`. Cada llicència té un comptador `version` que puja en 1 a cada canvi, dins la mateixa transacció, i cada esdeveniment porta `version` i `occurred_at` ([054](decisions/054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md)). En arrencar, el 06 registra al 01 la seva font de lectura per a la comprovació diària (`members.register_licence_source`, RN-M01-41) | [052](decisions/052-llicencia-font-unica-al-06.md) |
| RN-M06-18 | **Preu aplicat:** la versió de `LicencePrice` del tipus creada més recentment amb `valid_from ≤ starts_on` i `valid_to` buit o `≥ starts_on`. Els trams de l'any natural (preu més baix si s'obté a mig any) són versions amb dates [A verificar: FECDAS, quins trams hi ha] | 28/10/2026 |
| RN-M06-19 | **Condicional a `licences.day_enabled`:** una persona pot tenir diverses llicències d'un dia en curs per a dates diferents, però no dues per al mateix tipus i data. La unicitat «una llicència en curs per tipus» només val per a les d'any natural i de 365 dies | 28/10/2026 |
| RN-M06-20 | **Condicional a `licences.day_enabled`:** si una llicència d'un dia pagada (o tramitada) no ha arribat a `active` en acabar el seu dia, la tasca diària la marca **«no tramitada a temps»** (`lapsed`), avisa la secretaria i el tresorer i crea una proposta de devolució (`LicenceRefundProposal`). Cap devolució automàtica: la fa el tresorer amb el 05b | 28/10/2026 |
| RN-M06-21 | **Sol·licitud anticipada de l'any següent:** des de `licences.next_year_opens_on` (supòsit: 1/12 [A verificar: FECDAS, quan s'obre cada any]), es pot demanar una llicència d'any natural de l'any següent amb `starts_on` l'1/1, al preu de la versió que cobreix l'1/1 i, per a soci o no soci, segons `members.is_member(person, on=data en què es demana)` (RN-M06-04). Si la persona es dona de baixa abans de l'1/1, la secretaria cancel·la la llicència amb proposta de devolució (P-M06-G) [A validar: tresorer, S-M06-14]. Es paga quan es demana; la secretaria la tramita quan la federació obri el període. Abans d'aquella data, es rebutja (`NextYearNotOpen`) | 28/10/2026 |
| RN-M06-22 | **Visibilitat per a l'instructor i el responsable de l'activitat** (igual al [M02-4](#M02-4-rols)): l'**instructor** només veu «vigent sí o no» per a la data de la sessió (una llicència en tràmit és «no»); el **responsable de l'activitat** veu «vigent», «en tràmit» o «no» per a la data de l'activitat. Cap dels dos veu mai la data de venciment, el número federatiu, la categoria ni el document | 28/10/2026 |

**Exemples** (preus inventats; els reals són [A verificar: FECDAS])
- **Dates:** inici el 15/3/2027: any natural → 15/3/2027 a 31/12/2027; 365 dies → 15/3/2027 a 13/3/2028 (el 29/2/2028 és pel mig); inici el 15/3/2026 amb 365 dies → 14/3/2027; un dia (només amb l'opció) → 15/3/2027 a 15/3/2027.
- **Trams (preus inventats):** any natural amb inici entre l'1/1 i el 30/6 → 9000; entre l'1/7 i el 31/12 → 5000. Inici el 10/9 → 5000.
- **Final d'any:** 300 llicències d'any natural caduquen el 31/12 → el 2/11, el 1/12 i el 24/12 cada titular rep el seu avís i la secretaria en rep un sol resum cada dia; des de l'1/12 (supòsit) es poden demanar les de l'any següent amb inici l'1/1.
- **Preus:** preu de la federació de la llicència anual 9000; recàrrec 2500 → soci **9000**, no soci **11.500**; estalvi en la llicència **2500**. La pantalla mostra al costat la quota anual de soci, sense restar-la.
- **Estat derivat:** caduca el 31/12; el 2/11 surt «per renovar» (60 dies o menys); l'1/1 surt «caducada».
- **Avisos:** caduca el dia V → avisos els dies V−60, V−30 i V−7; si el titular renova el dia V−40, no s'envien els de V−30 i V−7.
- **Marge (09):** soci amb llicència de 9000 → ingrés 9000 i despesa a la federació 9000 → marge **0** abans de comissions (RN-M09-20).

<a id="M06-8-serveis"></a>
## M06-8 Serveis i interfícies (contracte)

Cap altra app escriu als models del 06.

**Ofereix**
| Servei | Entrada | Sortida | Errors | Qui el fa servir |
|---|---|---|---|---|
| `licences.current(person, on=date)` | persona, data | `{status (active o in_progress), type, category, validity_rule, expires_on, origin}` o res (RN-M06-13). **Només lectura**. Al 02, la pantalla de l'instructor i del responsable només en mostra «vigent sí o no» (instructor) o «vigent, en tràmit o no» (responsable) (RN-M06-22) | — | 02 (requisit de llicència i, quan es resolgui RP-M02-02, de categoria) |
| `licences.request(person, licence_type, starts_on, actor)` | — | llicència `requested` i càrrec | `NonMembersDisabled`, `DayLicencesDisabled`, `AlreadyInProgress`, `NextYearNotOpen`, `DateInPast` | Vistes |
| `licences.declare_existing(person, data, actor)` | número, tipus, venciment | llicència `active` amb origen `external` | — | Vistes |
| `licences.on_charge_paid(event)` | esdeveniment `charge.paid` d'un càrrec amb origen `licences` | llicència `paid` (si ja ho era, no fa res) | — | Subscriptor ([049](decisions/049-peces-noves-a-moduls-aprovats-per-al-02.md)) |
| `licences.expiring(days)` | — | llicències per caducar (lectura) | — | 08; llistat de la secretaria |
| Esdeveniments `licence.issued`, `licence.renewed`, `licence.expired`, `licence.cancelled` | — | emesos a la cua, amb `version` i `occurred_at` (RN-M06-17) | — | 01 (còpia de lectura); qualsevol mòdul que s'hi subscrigui ([052](decisions/052-llicencia-font-unica-al-06.md)) |
| Font de lectura registrada amb `members.register_licence_source` | — | llicències dels socis amb `version` (només lectura) | — | 01 (comprovació diària, [054](decisions/054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md)) |
| `licences.export_personal_data(person)`, `licences.anonymise(person)` | persona | — | — | 00 (RGPD) |

**Consumeix**
| Servei | Mòdul | Per a què |
|---|---|---|
| `persons.create_or_get(data)`, `guest_links.create`, `guest_links.resolve` | 00 | Persones de fora (021) |
| `charges.create_charge(person, kind="llicència", amount_cents, department, concept, origin="licences")`, `charges.cancel` | 00 | Càrrec |
| `events.subscribe("charge.paid", licences.on_charge_paid)` | 05b i 00 (049) | Saber quan es paga |
| `payments.start_payment`, `payments.payment_status`, `payments.receipt_pdf`, `payments.refund` | 05b | Pagar, rebut i devolució pel tresorer |
| `members.is_member(person, on)`, `members.licence_records()` | 01 | Preu; pas únic dels registres (049) |
| `imports.create_batch(kind="licences", …)` | 00 | Lot del pas únic, per poder-lo desfer |
| `mail.send`, `notices.post`, `audit.record`, `permissions.require`, cua de tasques | 00 | Avisos, registre, permisos |

**Rutes.** Pública (declarada, només si l'opció està activada): `/llicencies`, `/llicencies/demanar`. Compte personal: `/socis/llicencia`. Convidat: dins l'enllaç de la 00. Administració: `/gestio/llicencies`, `/gestio/llicencies/{id}`, `/gestio/llicencies/per-tramitar`, `/gestio/llicencies/exportar`, `/gestio/llicencies/preus`, `/gestio/llicencies/importar-01`.

<a id="M06-9-criteris"></a>
## M06-9 Criteris d'acceptació i casos límit

- **CA-M06-01** Donat un tipus de 365 dies, quan es calcula, llavors: inici 15/3/2026 → caduca 14/3/2027; inici 15/3/2027 → 13/3/2028; inici 29/2/2028 → 27/2/2029; inici 1/3/2027 → 28/2/2028; inici 1/1/2028 → 30/12/2028; i en tots els casos hi ha exactament 365 dies comptant el d'inici.
- **CA-M06-02** Donat un tipus d'any natural, quan es calcula amb inici el 15/3, l'1/1 i el 31/12, llavors caduca el 31/12 del mateix any.
- **CA-M06-03** Donat un preu de la federació de 9000 i un recàrrec de 2500, quan un soci i un no soci demanen la llicència, llavors el soci paga 9000 i el no soci 11.500.
- **CA-M06-04** Donat un intent de posar un preu de soci diferent del de la federació, quan es desa, llavors es rebutja.
- **CA-M06-05** Donat un canvi de preu sense nota, quan es desa, llavors es rebutja; amb nota, crea una versió nova, avisa la secretaria i la junta i les llicències ja demanades conserven el preu.
- **CA-M06-06** Donat l'opció de no socis desactivada, quan un visitant obre `/llicencies`, llavors rep «no trobat»; activada, veu la comparació de preus.
- **CA-M06-07** Donat una llicència `requested`, quan arriba `charge.paid` dues vegades, llavors passa a `paid` una sola vegada i la secretaria rep un sol avís.
- **CA-M06-08** Donat una llicència anual `active` que caduca el dia V, quan s'executa la tasca diària els dies V−60, V−30 i V−7, llavors el titular rep un avís cada dia i cap de repetit; per a una d'un dia (només amb l'opció activada), cap.
- **CA-M06-09** Donat una renovació pagada el dia V−40, quan arriba V−30, llavors no s'envia cap avís.
- **CA-M06-10** Donat dues llicències `paid`, quan la secretaria exporta el llistat, llavors el fitxer només porta els camps de RN-M06-11, no es desa i el registre en guarda l'empremta.
- **CA-M06-11** Donat una persona amb una llicència de 365 dies `active` del 15/3/2026 al 14/3/2027 i de categoria tècnic, quan el 02 demana `licences.current` per al 14/3/2027 i per al 15/3/2027, llavors torna la llicència amb la categoria i res.
- **CA-M06-12** Donat «Ja en tinc una» amb venciment el 31/12, quan es desa, llavors la llicència és `active`, origen `external`, sense càrrec.
- **CA-M06-13** Donat una llicència pagada i no tramitada, quan la secretaria la cancel·la, llavors es crea una proposta de devolució per al tresorer i cap devolució automàtica.
- **CA-M06-14** Donat tres registres mínims al 01, quan l'administrador fa el pas únic en prova, llavors no s'escriu res; en confirmar, es creen tres llicències `imported_m01` i el lot es pot desfer.
- **CA-M06-15** Donat un instructor o un responsable d'activitat, quan consulta un participant de la seva sessió o activitat, llavors l'instructor només veu «vigent sí o no» i el responsable «vigent», «en tràmit» o «no» per a la data de la sessió o de l'activitat, i no la data de venciment, el número federatiu, la categoria ni el document; una petició forçada d'aquestes dades es rebutja.
- **CA-M06-16** Donat cada cel·la de [M06-4](#M06-4-rols), quan el rol prova l'acció, llavors el resultat coincideix.
- **CA-M06-17** Donat una llicència d'un soci que passa a `active`, quan es desa, llavors s'emet un sol `licence.issued` i la còpia del 01 la mostra (CA-M01-26); quan la tasca diària passa per una llicència caducada dues vegades, s'emet un sol `licence.expired`.
- **CA-M06-18** Donat una llicència importada del registre del 01, quan s'emet `licence.issued`, llavors el 01 actualitza el registre d'origen i no en crea cap de nou.
- **CA-M06-19** Donat una llicència amb `version` 1, quan es renova i després es cancel·la, llavors els esdeveniments porten `version` 2 i 3, i la font registrada al 01 torna `version` 3.
- **CA-M06-20** Donat un tipus d'any natural amb un tram de 9000 (inici de l'1/1 al 30/6) i un de 5000 (de l'1/7 al 31/12), quan un soci en demana una amb inici el 10/9, llavors paga 5000; si després es crea una versió nova del tram de juliol, les llicències ja demanades conserven el preu.
- **CA-M06-21** Donat `licences.day_enabled` desactivada, quan es vol crear un tipus d'un dia o demanar-ne una (també amb una petició forçada), llavors es rebutja (`DayLicencesDisabled`) i la pàgina no l'ofereix.
- **CA-M06-22** *(Condicional a `licences.day_enabled`.)* Donat una persona amb una llicència d'un dia en curs per al 10/5, quan en demana una altra del mateix tipus per al 17/5, llavors s'accepta; per al 10/5, es rebutja; i dues d'any natural en curs del mateix tipus continuen rebutjades.
- **CA-M06-23** *(Condicional a `licences.day_enabled`.)* Donat una llicència d'un dia `paid` per al 10/5 que el 10/5 a la nit encara no és `active`, quan corre la tasca diària, llavors passa a `lapsed` una sola vegada, la secretaria i el tresorer reben l'avís i es crea una proposta de devolució, sense cap devolució automàtica.
- **CA-M06-24** Donat 300 llicències d'any natural que caduquen el 31/12, quan corre la tasca el 2/11, llavors cada titular rep un sol avís (enviats en lots), la secretaria rep un sol resum agrupat per data i categoria, i si la tasca es repeteix aquell dia no s'envia res més.
- **CA-M06-25** Donat `licences.next_year_opens_on` l'1/12, quan un soci demana el 30/11 la llicència d'any natural de l'any següent, llavors es rebutja (`NextYearNotOpen`); l'1/12, es crea amb inici l'1/1 i caducitat el 31/12 de l'any següent, al preu de la versió que cobreix l'1/1 i al preu de soci perquè és soci l'1/12 (data en què la demana), lligada a l'anterior (`renewal_of`), i els avisos de l'anterior s'aturen; si es dona de baixa el 20/12, la secretaria la cancel·la i es crea una proposta de devolució, sense devolució automàtica.
- **CA-M06-26** Donat `licences.reminder_days` canviat a 45, 15 i 3, quan corre la tasca d'avisos, llavors els titulars i el resum de la secretaria surten a 45, 15 i 3 dies; un valor de 0 o de 121 es rebutja i el canvi vàlid queda al registre.
- **CA-M06-27** Donat una persona sense llicència `active` i amb una d'any natural `paid` (o `requested` o `filed`) que cobriria el 10/5, quan el 02 demana `licences.current` per al 10/5, llavors torna `status = in_progress` amb la categoria; el responsable de l'activitat veu «en tràmit» i l'instructor, «no»; si la llicència és `cancelled`, torna res.

**Casos límit**
| # | Cas | Comportament |
|---|---|---|
| L-M06-01 | Un soci es dona de baixa amb la llicència vigent | La llicència continua vigent fins al venciment; la renovació serà al preu de no soci (si l'opció és activada) |
| L-M06-02 | Una persona de fora es fa sòcia amb una llicència de no soci vigent | No es retorna cap diferència [A validar: junta] |
| L-M06-03 | El càrrec caduca sense pagar | La llicència queda `requested` i la secretaria la pot cancel·lar |
| L-M06-04 | Dues persones amb el mateix document | Les uneix la 00 (perfil únic); el 06 no crea persones duplicades |
| L-M06-05 | La federació canvia el preu a mig any | Versió nova del preu; les demanades conserven l'anterior |
| L-M06-06 | Esborrat RGPD del titular | Llicència anonimitzada; el càrrec i el cobrament es bloquegen (028) |
| L-M06-07 | *(Condicional a `licences.day_enabled`.)* La llicència d'un dia es demana per a una data passada | Es rebutja (`DateInPast`); amb l'opció desactivada, ni tan sols es pot triar |
| L-M06-08 | Un soci demana l'any següent el 15/12 però es dona de baixa abans de l'1/1 | El preu de soci es va fixar amb `is_member` a la data en què la va demanar (el 15/12, RN-M06-04); la secretaria cancel·la la llicència amb proposta de devolució (P-M06-G) [A validar: tresorer, S-M06-14] |

<a id="M06-10-tasques"></a>
## M06-10 Tasques (per dependències, sense dates)

| # | Tasca | Esforç | Fitxers | Depèn de | Feta quan |
|---|---|---|---|---|---|
| T-M06-01 | Wireframes que falten (vegeu [M06-5](#M06-5-processos)) | M | `design/wireframes/` | — | Revisats; contrast i estats amb símbol |
| T-M06-02 | Tipus amb categoria i regla de validesa; preus amb versions, trams per dates, nota i avís | M | `apps/licences/models.py`, vistes | T-M01-11 | CA-M06-03, 04, 05, 20 |
| T-M06-03 | Model de llicència, estats derivats i càlcul de dates (funció pura: any natural, 365 dies comptant el dia d'inici i any de traspàs) | M | `models.py`, `apps/licences/dates.py` | T-M06-02 | CA-M06-01, 02 |
| T-M06-04 | Demanar i pagar (soci) amb el càrrec i el 05b; sol·licitud anticipada de l'any següent | M | `apps/licences/services.py` | T-M06-03, T-M05b-04 | P-M06-B; CA-M06-25 |
| T-M06-05 | Subscriptor de `charge.paid`, idempotent | S | `services.py` | T-M05b-21 | CA-M06-07 |
| T-M06-06 | «La meva llicència» i renovació | M | vistes, plantilles | T-M06-04 | HU-M06-01 |
| T-M06-07 | Pàgina pública per a no socis, desactivada per defecte, amb comparació de preus | M | vistes, plantilles | T-M06-04; enllaços de convidat de la 00 | CA-M06-06 |
| T-M06-08 | «Ja en tinc una» | S | `services.py` | T-M06-03 | CA-M06-12 |
| T-M06-09 | Llistat de la secretaria, filtres i venciments | S | vistes | T-M06-03 | HU-M06-05 |
| T-M06-10 | Exportació per a la federació i marcar tramitada o vigent | M | `apps/licences/filing.py` | T-M06-09 | CA-M06-10; format [A verificar: FECDAS] |
| T-M06-11 | Avisos diaris a la cua, idempotents, en lots, i resum diari agrupat per a la secretaria | S | `apps/licences/tasks.py` | T-M06-03 | CA-M06-08, 09, 24 |
| T-M06-12 | Cancel·lació i proposta de devolució | S | `services.py` | T-M06-04, T-M05b-13 | CA-M06-13 |
| T-M06-13 | Servei `licences.current` (amb la categoria i l'estat «en tràmit») i visibilitat («sí o no» per a l'instructor; «vigent, en tràmit o no» per al responsable) amb proves de contracte per al 02 | S | `services.py` | T-M06-03 | CA-M06-11, 15, 27 |
| T-M06-14 | Pas únic dels registres del 01, amb prova, confirmació i desfer | M | `apps/licences/imports.py` | T-M01-30, T-M06-03 | CA-M06-14 |
| T-M06-15 | Emetre els esdeveniments de llicència (RN-M06-17) dins la mateixa transacció, també des de la tasca diària i del pas únic, amb `version` i `occurred_at`, i registrar la font de lectura al 01 ([052](decisions/052-llicencia-font-unica-al-06.md), [054](decisions/054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md)) | S | `apps/licences/events.py`, `apps/licences/apps.py` | T-M06-03, T-M06-11, T-M05b-21 | CA-M06-17, 18, 19 |
| T-M06-16 | Permisos per rol i per objecte | S | `apps/licences/permissions.py` | T-M06-03 | CA-M06-16 |
| T-M06-17 | Dades inventades i proves de principi a fi (demanar → pagar → tramitar → vigent → avís → renovar) | M | `fixtures/`, `tests/` | T-M06-04 a T-M06-14 | Totes en verd |
| T-M06-18 | Guia de la secretaria (tramitació i venciments) | S | `docs/` | T-M06-17 | Revisada |
| T-M06-19 | Opció `licences.day_enabled` (desactivada per defecte) i, darrere d'ella, llicència d'un dia: unicitat per data, estat `lapsed`, avís i proposta de devolució | M | `apps/licences/day.py`, migració | T-M06-03, T-M06-12 | CA-M06-21 sempre; CA-M06-22, 23 amb l'opció activada a la prova |
| T-M06-20 | Pantalla d'**ajustos** del mòdul: els seus valors (bloc «Valors configurables» de la secció 6), amb valor inicial, rang vàlid, rol que el canvia, registre (qui, quan, valor anterior) i data d'entrada en vigor si afecta diners; només per als rols amb permís | S | `apps/licences/settings.py`, vistes | T-M06-16; T-AJ-02 (peça comuna d'ajustos, [055](#valors-configurables-055)) | Per valor: fora de rang es rebutja; el canvi queda al registre; un rol sense permís rep «no trobat»; un canvi de diners no toca el que ja s'ha demanat; CA-M06-26 |

<a id="M06-11-proves"></a>
## M06-11 Pla de proves

- **Unitàries (B1):** càlcul de dates (any natural i 365 dies comptant el dia d'inici, inclosos el 29 de febrer, l'any de traspàs i el canvi d'any), preu per trams, estats derivats, preu de soci i de no soci, versions de preu, dies dels avisos.
- **Base de dades:** `CHECK` de dates; unicitat d'una llicència anual en curs per tipus i, amb l'opció d'un dia, per tipus i data; unicitat dels avisos i dels resums.
- **Integració:** demanar → pagar amb `FakeProvider` → `charge.paid` → `paid` → tramitar → `active`; renovació; cancel·lació amb proposta de devolució.
- **Contracte amb el 02:** `licences.current` amb els casos de CA-M06-11.
- **Pas únic del 01:** prova sense escriure, confirmació i desfer amb registres inventats.
- **Permisos (B4):** una prova per cel·la de [M06-4](#M06-4-rols); la pàgina pública només amb l'opció activada.
- **Accessibilitat (B8):** estats amb símbol, text i color; comparació de preus llegible amb lector de pantalla.
- **Dades:** només inventades.

<a id="M06-12-seguretat"></a>
## M06-12 Seguretat i RGPD

- **Mínim de dades:** les que demana la federació i ja són a la 00 (V-04: per a una llicència, també el document). La data de naixement no es demana fins que es respongui Q-09 i P-33; si la federació la demana, és el dubte 2 de [M06-13](#M06-13-riscos).
- **Cap dada de salut** (RN-M06-15).
- **Llistat per a la federació:** surt cap a un tercer dins la UE; es genera a demanda i no es desa. Base legal i informació a la persona [A validar: junta]; la federació hi és com a destinatària, no com a encarregada.
- **Pàgina pública:** declarada de manera explícita, desactivada per defecte, amb limitació de peticions i protecció contra robots, i dades mínimes.
- **Permisos:** comprovats al servidor; l'instructor i el responsable de l'activitat només veuen «vigent sí o no» per a la data de l'activitat, sense venciment ni número federatiu.
- **Registre:** canvis d'estat, preus, exportacions, cancel·lacions i el pas únic, amb el valor anterior.

<a id="M06-13-riscos"></a>
## M06-13 Riscos, supòsits i dubtes

**Riscos**
| Risc | Impacte | Mitigació | Propietari |
|---|---|---|---|
| Esdeveniments de llicència que no arriben al 01 | Mitjà: la fitxa del soci mostraria una dada antiga | Lliurament a la cua amb reintents i registre de lliuraments (049); `members.licence_record` i `licences.current` es comparen a les proves ([052](decisions/052-llicencia-font-unica-al-06.md)) | Informàtica |
| Tipus, preus i format de tramitació desconeguts | Alt per entrar en producció | Configurables; dades inventades a les proves | FECDAS |
| La federació demana dades que la plataforma no té (data de naixement) | Mitjà | La secretaria les completa fora; dubte 2 | Secretaria |
| Recàrrec massa baix i no socis que no es fan socis | Mitjà per al club | La junta el fixa; la pantalla mostra la comparació | Junta |
| Gairebé totes les llicències d'any natural caduquen el 31/12 | Alt per a la secretaria al desembre | Resum diari agrupat en lloc d'un avís per llicència; avisos als titulars en lots; sol·licitud anticipada de l'any següent (RN-M06-12 i 21) | Secretaria |
| La llicència d'un dia potser ja no existeix | Mitjà: funcions que no es farien servir | Darrere de `licences.day_enabled`, desactivada per defecte | Responsable de cursos i sortides |

**Supòsits [A validar] i dades [A verificar]**
| ID | Què | Supòsit mentre tant | Propietari |
|---|---|---|---|
| S-M06-01 | Recàrrec per als no socis (RN-M06-06) | Cap preu; l'opció de no socis queda desactivada | Junta |
| S-M06-02 | Tipus de llicència, categoria (aficionat, tècnic, altres), preu i trams, i càlcul exacte de les dates de 365 dies (S-M01-17) | Tipus en text; preus inventats; 365 dies comptant el dia d'inici (RN-M06-02) | FECDAS |
| S-M06-03 | Format i dades del llistat per tramitar; si la federació té un sistema per importar-lo | CSV amb nom, cognoms, document, correu, tipus i durada | FECDAS |
| S-M06-04 | «Ja en tinc una» per a socis i qui la comprova | Sí, i la secretaria la comprova | Secretaria |
| S-M06-05 | Qui manté els preus de les llicències | El tresorer | Junta |
| S-M06-06 | Devolució d'una llicència ja tramitada | No se'n fa | FECDAS |
| S-M06-07 | *(Condicional a `licences.day_enabled`.)* La llicència d'un dia es pot demanar sense estar inscrit a cap activitat | Sí | Junta |
| S-M06-08 | Una persona de fora que es fa sòcia amb una llicència vigent (L-M06-02) | Cap retorn | Junta |
| S-M06-09 | Número federatiu obligatori per marcar una llicència vigent | Sí, per a les tramitades pel club | Secretaria |
| S-M06-10 | Departament de les llicències (Q-19, S-M04-07) | «General / Llicències», provisional | Junta |
| S-M06-11 | Com es comptabilitza la llicència que el club cobra i paga a la FECDAS (RN-M06-05, RN-M06-10) [A verificar: gestoria] | Ingrés i despesa del club, amb marge 0, com diu el [M06-2](#M06-2-dependencies). No bloqueja el codi; bloqueja la producció | Gestoria |
| S-M06-12 | Si existeix avui la llicència d'un dia (RN-M06-01) [A validar; A verificar: FECDAS] | No: `licences.day_enabled` desactivada | Responsable de cursos i sortides |
| S-M06-13 | Quan obre la FECDAS el període de sol·licitud de l'any següent (RN-M06-21) [A verificar] | 1/12 (configurable) | FECDAS |
| S-M06-14 | Preu d'una sol·licitud anticipada de l'any següent (RN-M06-04, RN-M06-21): l'estat de soci a l'1/1 encara no se sap | `is_member` a la data en què es demana; si es dona de baixa abans de l'1/1, cancel·lació amb proposta de devolució. Alternativa: exigir la quota de l'any següent pagada | Tresorer |

**Revisió de dubtes (aplicada a mà)**
1. ~~Font única de la llicència.~~ Resolt per la [052](decisions/052-llicencia-font-unica-al-06.md): el 06 és l'únic propietari i el 01 en guarda una còpia de lectura amb esdeveniments.
2. **Data de naixement.** La FECDAS la demana en tramitar (informació del 28/10/2026); falta saber si el formulari de club també la demana [A verificar: FECDAS]. Cal decidir si la plataforma la guarda (Q-09, P-33). Supòsit, que es manté: no es guarda i la secretaria la completa fora. És el **punt prioritari 0** de l'[ordre del dia de la junta](#ordre-del-dia-junta). Propietari: junta.
3. ~~Llicència d'un dia i activitat.~~ Resolt per la [052](decisions/052-llicencia-font-unica-al-06.md): el 06 no depèn del 02; el 02 hi demanarà si una activitat necessita llicència d'un dia (RP-M02-01, condicional a `licences.day_enabled`).
4. **Comissió del cobrament de la llicència d'un soci** (dubte 5 de [M09-13](#M09-13-riscos)). Amb preu igual al de la federació, la comissió la paga el club. Propietari: junta.
5. **«Pagada» abans de «tramitada»:** si la federació demana tramitar abans de cobrar, l'ordre s'inverteix. Supòsit: es cobra abans. Propietari: FECDAS.
6. **Què fa avui Cluber amb les llicències (P-28):** si les tramita Cluber, cal saber-ho abans de deixar-lo. Propietari: tresorer.

<a id="M06-14-aprovar"></a>
## M06-14 Què cal aprovar abans de començar

**Aprovat el 28/10/2026** pel responsable del projecte, alhora que els 02, 03, 06 i 09 (amb l'apartat d'ajuts), sense canviar cap regla ni cap criteri. Respostes d'aquesta aprovació:
- Els **supòsits per defecte** s'accepten per començar i **no bloquegen el codi**.
- **Per entrar en producció** cal respondre els [A verificar] externs i les decisions de la junta ([ordre del dia](#ordre-del-dia-junta)).
- Tots els [A validar] i [A verificar] continuen oberts amb el seu propietari: aquesta aprovació no els resol.

Punts que es van presentar per aprovar:

1. **Aquesta secció del 06**, amb els estats derivats i el càlcul de dates.
2. ~~Font única de la llicència al 06 i canvi al 01~~ **Aprovada** per la [052](decisions/052-llicencia-font-unica-al-06.md), amb l'[addenda del M01](#M01-addenda-052).
3. ~~Dependència opcional del 02~~ **No s'afegeix** (052). Queda com a requisit pendent del 02 (RP-M02-01).
4. **Supòsits per defecte** S-M06-04, S-M06-05, S-M06-07 (condicional) i S-M06-09 [A validar: junta i secretaria], i S-M06-12 (llicència d'un dia desactivada) [A validar: responsable de cursos i sortides]. No bloquegen el codi.
5. **Per entrar en producció** (no per començar): tipus, categories, preus i trams, càlcul de dates, obertura de l'any següent i format de tramitació [A verificar: FECDAS, S-M06-02, S-M06-03 i S-M06-13]; data de naixement (punt 0 de la junta); recàrrec i activació de l'opció de no socis [A validar: junta, S-M06-01].


<a id="M06-addenda-058"></a>
## M06 — Addenda de la [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md): tipus, durades, llicència d'un dia, recàrrec, renovació, format del carnet i caducitat desconeguda

Aprovada el 29/10/2026. **No canvia cap regla aprovada** del 06, excepte el càlcul dels 365 dies, que aquesta addenda substitueix (RN-M06-23 en lloc de la part de 365 dies de RN-M06-02, i CA-M06-28 en lloc de CA-M06-01). L'any natural no canvia. El número 056 no es fa servir: la llicència d'un dia existeix.

**Dades i valors inicials**
- **Tipus inicials:** Aficionat (categoria `amateur`) i Tècnic (categoria `technical`), cadascun amb les tres durades (un dia, any natural i 365 dies): sis `LicenceType`. Que els dos tipus tinguin les tres durades: [A verificar: FECDAS].
- **Preus:** un preu per tipus i durada mentre no se sàpiga si la FECDAS varia el preu segons el mes de compra; si el varia, es fan servir els trams que ja preveu RN-M06-18 [A verificar: FECDAS]. Els imports de la federació: [A verificar: FECDAS].
- **Recàrrec de no soci:** valor inicial **2000 cèntims** a `non_member_surcharge_cents` (RN-M06-06). El preu de soci continua sent el de la federació (RN-M06-05). Activar l'opció de no socis continua sent decisió de la junta (RN-M06-03).
- **Llicència d'un dia:** existeix; `licences.day_enabled` (VC-40) passa a **activada** amb una migració de dades. RP-M02-01 i S-M06-07 deixen de ser condicionals.
- **Obertura de la renovació de l'any natural:** `licences.next_year_opens_on` (VC-42), valor inicial l'**1/12**, decidit pel club. Els avisos als 60, 30 i 7 dies continuen.
- **Format del carnet:** camp nou `card_format` a la llicència (`physical` físic, `digital`, null) [A validar: secretaria, qui el tria i si és obligatori].
- **Llistat per a la FECDAS:** en el format que triï el club, amb les dades de RN-M06-11; ara hi pot anar la data de naixement (RN-M01-47). S-M06-03 queda resolt.
- **Cap cànon de club:** el 06 no crea cap càrrec anual del club a la federació.

**Regles noves**
| ID | Regla |
|---|---|
| RN-M06-23 | **365 dies:** `expires_on` = el mateix dia de l'any següent menys un dia (del 15/03 al 14/03). Els anys de traspàs no compten. Si comença el 29/02, caduca el 28/02 de l'any següent [A verificar: FECDAS] |
| RN-M06-24 | **Caducitat desconeguda:** el pas únic (P-M06-H) importa els registres del 01 sense `expires_on` com a llicències `active` amb `expiry_confirmed = false` («pendent de confirmar»). No reben avisos ni emeten `licence.expired` fins que la secretaria hi posa la data. `licences.current` les torna amb `status = unconfirmed`; el responsable de l'activitat veu «pendent de confirmar» i l'instructor, «no». Posar-hi la data puja la `version` i la comprovació diària (054) la porta al 01 |
| RN-M06-25 | **Comptabilitat:** la llicència és sempre ingrés del soci i despesa a la federació; marge 0 per als socis i el recàrrec per als no socis (S-M06-11 resolt; RN-M09-20) |

**Criteris d'acceptació**
- **CA-M06-28** (substitueix CA-M06-01) Donat un tipus de 365 dies, quan es calcula, llavors: inici 15/3/2026 → caduca 14/3/2027; inici 15/3/2027 → 14/3/2028; inici 1/3/2027 → 29/2/2028; inici 1/1/2028 → 31/12/2028; inici 29/2/2028 → 28/2/2029.
- **CA-M06-29** Donat un registre del 01 sense caducitat, quan corre el pas únic, llavors es crea una llicència «pendent de confirmar» sense cap avís; quan la secretaria hi posa la data, passa a ser una llicència normal, rep avisos i el 01 en té la data l'endemà com a molt tard.
- **CA-M06-30** Donat un no soci que demana una llicència d'any natural amb un preu de federació de X, quan es calcula el preu, llavors és X + 2000 cèntims, i el d'un soci és X.
- **CA-M06-31** Donat la base de dades nova, quan s'apliquen les migracions, llavors hi ha els sis tipus inicials i `licences.day_enabled` és activada.

**Tasques**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M06-21 | Dades inicials: sis tipus, recàrrec de 2000 cèntims, llicència d'un dia activada, obertura l'1/12 i camp `card_format` ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md)) | S | migracions de dades, `models.py` | T-M06-02, T-M06-19 | CA-M06-30, 31 |
| T-M06-22 | Càlcul dels 365 dies segons RN-M06-23 | S | `apps/licences/dates.py` | T-M06-03 | CA-M06-28 |
| T-M06-23 | Llicències «pendents de confirmar» al pas únic i a `licences.current` | S | `imports.py`, `services.py` | T-M06-14, T-M06-13, T-M01-34 | CA-M06-29 |

**Precisió del 29/10/2026** (addenda mínima aprovada pel responsable del projecte; no canvia cap regla).

| ID | Regla |
|---|---|
| RN-M06-26 | **Confirmació de les llicències «pendents de confirmar»** (RN-M06-24): la secretaria pot confirmar **en bloc** les d'any natural (selecciona les pendents i en fixa la caducitat al 31/12 de l'any que tria), i el soci pot **declarar** la caducitat de la seva al perfil; la declaració queda pendent fins que la secretaria la confirma. Cada confirmació puja la `version` i la comprovació diària (054) la porta al 01. Mentre no es confirma, cap avís |

- **CA-M06-32** Donat vint llicències d'any natural «pendents de confirmar», quan la secretaria en confirma quinze en bloc per a l'any 2026, llavors aquestes quinze caduquen el 31/12/2026, comencen a rebre els avisos i el 01 en té la data l'endemà com a molt tard; les altres cinc no canvien.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M06-24 | Confirmació en bloc de les llicències d'any natural pendents i declaració del soci | S | `apps/licences/imports.py`, vistes | T-M06-23 | CA-M06-32 |

<a id="M06-addenda-059"></a>
## M06 — Addenda de la [059](decisions/059-rols-i-permisos-editables.md): permisos editables i configuració inicial

Aprovada el 30/10/2026. **No canvia cap regla** del M06. La taula de [M06-4](#M06-4-rols) passa a ser la **configuració inicial** dels permisos del mòdul, que l'administrador pot canviar des de l'app ([peça comuna](#rols-i-permisos-059)). Els canvis respecte de la taula, cel·la per cel·la, són a la [matriu inicial](#rols-i-permisos-059-matriu). Les cel·les [A validar] prenen el supòsit per defecte del mòdul; si no n'hi ha, «—»; si l'acció es quedaria sense ningú, l'administrador.

**Què canvia**
- El **responsable de cursos i sortides** i el **tresorer** veuen el llistat i els venciments (LC4), amb el número federatiu i la categoria (C6), i registren «ja en tinc una» (LC3).
- Exportar a la federació i cancel·lar (LC5, LC6) ho fan la secretaria, l'administrador i el President.
- El President també canvia tipus i preus (LC8).
- L'instructor continua veient només «vigent sí o no» (RN-M06-22). La data de naixement continua com a la 058 (regla protegida).
- Queda resolt S-M06-05: mantenen els preus el tresorer, l'administrador i el President.

**Criteri d'acceptació**
- **CA-M06-33** Donat un compte amb el rol responsable de cursos i sortides, quan obre el llistat de llicències, llavors en veu els venciments, el número federatiu i la categoria, però no la data de naixement. Quan vol exportar a la federació o cancel·lar, rep «no trobat».

**Tasca**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-M06-25 | Declarar els permisos del 06 al catàleg (LC3 a LC11, C6) i comprovar-los a totes les vistes i serveis | XS | `apps/licences/permissions.py` | T-RP-01 | CA-M06-33; proves per cel·la del 06 (CA-RP-13) |

<a id="M06-addenda-060"></a>
## M06 — Addenda de la [060](decisions/060-ajustos-de-l-auditoria-del-pla.md): el 06 primer a la fase 2

Aprovada el 31/10/2026. **No canvia cap regla** del 06 ni les seves dependències (01 i 05b).
- **Ordre.** El 06 és el primer mòdul de la fase 2. La T-M01-31 (còpia de lectura al 01) es fa amb ell.
- **Dependències.** La T-M06-07 depèn de la **T-M00-02** (enllaços de convidat, [apèndix](#ajustos-060-peces-00)).
- **Tasques substituïdes.** La T-M06-03 es dona per feta amb CA-M06-28 i CA-M06-02, no amb CA-M06-01. La T-M06-22 es fa dins la T-M06-03 i es tanca amb ella.
- La **T-M06-24** és la confirmació en bloc que, amb el 06 actiu, fa de requisit previ per obrir el 02 ([RN-M02-34](#M02-addenda-060)).

| ID | Regla |
|---|---|
| RN-M06-27 | **Entrada en producció.** El 06 no entra en producció fins que existeix el nucli de despeses del 09 (T-M09-02 a T-M09-05), perquè el pagament a la federació és una despesa del 09 (RN-M09-20). Es comprova a la checklist |

---

<a id="M12-idees"></a>
# Mòdul 12 — Idees noves (idees registrades)

**Estat: pendent.** El 12 encara no té secció ([estat](#estat)); aquí només s'hi apunten les idees perquè no es perdin. Cap idea d'aquesta llista no es construeix fins que el 12 tingui la seva secció aprovada.

| Idea | Què faria | Condicions | Propietari |
|---|---|---|---|
| Avatars de fauna marina | Ja recollida al mapa v8 (M11 Idees) | — | Responsable del projecte |
| Bitàcola, hores i insígnies | Ja recollida (P-38); la base és l'assistència del 02 i el material del 03 | — | Responsable del projecte |
| **Assistent d'ajuts** (idea futura, 27/10/2026) | Cercar convocatòries a fonts públiques (BDNS, Generalitat, Diputació, CIDO) i avisar de les noves que encaixin; les proposaria com a «detectades» a l'[apartat d'ajuts del 09](#M09-ajuts), amb un filtre d'elegibilitat que sempre revisa una persona | Fonts i condicions d'ús de cada font [A verificar: informàtica]. Cap dada personal a cap eina d'IA ([035](decisions/035-dades-nomes-dins-ue.md)): només dades públiques de les convocatòries i el perfil del club. La plataforma no decideix mai l'elegibilitat (RN-M09A-03) | Responsable del projecte |
| **Lectura automàtica de moviments del compte (API de CaixaGuissona)** (idea futura, 28/10/2026) | Llegir cada dia els moviments del compte per proposar la conciliació sense importar l'extracte a mà. S'afegiria a través de l'adaptador bancari, sense canviar les regles de la 04; la importació de l'extracte en fitxer continua sent la base i el camí de reserva | El banc confirma l'accés de producció per a un client sense certificat QSealC i el cost [A verificar: banc]; durada i renovació del consentiment del titular; on s'executa la plataforma de l'API (dades dins la UE, [035](decisions/035-dades-nomes-dins-ue.md)); [decisió 057](decisions/057-tarifes-paynopain-i-api-caixaguissona.md). No es planifica fins que el banc ho confirmi | Responsable del projecte |

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
| S-M09-02, 05, 09 | Criteri «per participants»; durada del període; pagament a la federació com a «taxa» | — |
| S-M09-15 | Tancar un període amb excepcions documentades i quins elements es poden portar al període següent | — (es construeix permès) |
| S-M06-14 | Preu de la llicència de l'any següent demanada abans de l'1/1: soci segons la data en què es demana (i cancel·lació si es dona de baixa) o exigir la quota de l'any següent pagada | — |
| M09-13 dubte 3 | Reforç confirmat després del tancament econòmic | — |
| M09-ajuts-13 dubte 2 | Com es registra el reintegrament d'un ajut | — |
| S-M09A-07 | Per a cada convocatòria, si l'organisme accepta comprovants amb l'IBAN emmascarat ([051](decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) | — (es fa servir la còpia emmascarada) |

<a id="preguntes-junta"></a>
**Junta**
Els punts de la junta, agrupats per tema i amb la proposta de Claude, són a l'[ordre del dia](#ordre-del-dia-junta).

| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-01, 02 | Import del canvi a ple dret; quota sencera a mig any | — |
| S-M01-06, 07, 08 | Verificació pública del carnet (dígits, nom) i darrere del carnet | — |
| S-M01-09, 10, 11 | Soci clàssic, antiguitat en una readmissió, drets del simpatitzant | — |
| S-M01-12, 13 | Compte després de la baixa, socis menors (P-33) | — |
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
| S-M02-19, 20 | Requisits d'edat; protocol d'accidents i contacte d'emergència | — |
| S-M03-01 | Centres de busseig i tarifes | 03: producció |
| S-M03-02, 03 | Cost d'ús del material del club; lloguer en càrrec a part (també tresorer) | — |
| S-M03-04 | Dades que rep el centre a la llista de lloguer | — |
| S-M03-05 | Inventari actual per tipus i talla | 03: producció |
| S-M03-06, 08, 09, 10, 11 | Dies dels avisos, peces perdudes, bibotelles, qui assigna, codis de les peces | — |
| S-M09-04, 06, 07 | Llindar de marge baix; costos generals al marge per departament; departaments per a ajuts | — |
| RN-M09-23 | Qui puja una factura des del mòbil la pot tornar a obrir (documents de justificació, 051) | — |
| RN-M09-25 (risc de [M09-13](#M09-13-riscos)) | Fotos de factures i comprovants que queden a la galeria del telèfon: si n'hi ha prou amb el text d'ajuda o cal una norma per als responsables | — |
| S-M09-10, 11, 12 | Informes de l'assemblea; hores de voluntariat; pressupostos | — |
| S-M09A-01, 02, 03 | Responsable dels ajuts, convocatòries que s'han de vigilar, qui rep els avisos | Fer servir l'apartat d'ajuts |
| S-M09A-04, 05; M09-ajuts-13 dubte 3 | Avisos abans de justificar; format de cada organisme; renúncia a un ajut concedit | — |
| S-M09A-09 | Dies dels avisos d'un requeriment d'esmena | — |
| S-M06-01 | Recàrrec dels no socis i activació de l'opció | 06: llicències per a no socis |
| S-M06-07, 08, 10 | Llicència d'un dia sense inscripció (condicional); no soci que es fa soci; departament de les llicències (Q-19) | — |
| M06-13 dubte 2 | Data de naixement: la FECDAS la demana en tramitar (Q-09, P-33); **punt prioritari 0** | — |
| M06-13 dubte 4; M09-13 dubte 5 | Comissió del cobrament de la llicència d'un soci | — |
| S-AJ-01, 02 ([055](#valors-configurables-055)) | Si algun import només es pot canviar amb ratificació; qui rep l'avís dels canvis de diners com a «junta» | — (el canvi s'aplica i s'avisa) |

<a id="preguntes-gestoria"></a>
**Gestoria**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-15 (Q-14); S-M09A-06 | Terminis de conservació de quotes, rebuts, pagaments, factures i documents d'ajuts | — (es bloquegen fins que es digui) |
| S-M05b-12; S-M09-08; P-47; P-02 | Què s'ha de facturar, IVA, obligació de Verifactu i quin servei homologat | 09: activar la facturació (es construeix amb `FakeInvoicingProvider`) |
| S-M09-03 | Donatius de persones i certificat de donatius | — |
| M09-12 | Contracte d'encarregat amb el servei de facturació (també informàtica) | 09: activar la facturació |
| M05b-12 | Informació a Hisenda dels cobraments per Bizum | — |
| S-M05a-08 | Proves de la signatura electrònica del mandat (també banc) | — |
| M03-12 | Acord de tractament amb els centres de busseig si reben dades personals | 03: llista de lloguer amb noms |
| S-M09A-08 | Termini legal per respondre un requeriment d'esmena d'un ajut i si es compta en dies hàbils | — (la data límit l'escriu la persona) |
| RN-M06-05, RN-M06-10; S-M06-11; S-M09-14 | Com es comptabilitzen els diners d'una llicència que el club cobra i després paga a la FECDAS: ingrés i despesa del club (el que suposa ara el 09) o diners de tercers (cobrament per compte de la federació, fora d'ingressos i despeses) | 06 i 09: producció (es construeix amb el supòsit) |
| RN-T31 ([053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md)) | Si és correcte comptabilitzar al període obert un moviment d'origen extern que arriba després del tancament (pagament, devolució, retorn, comissió, remesa, liquidació), amb la data de valor original guardada a part; si els traspassos i els arqueigs han de seguir la mateixa regla; si l'exportació per a la gestoria (P-M04-G) ha de portar les dues dates | — (es construeix així; l'exportació porta les dues dates) |

<a id="preguntes-fecdas"></a>
**FECDAS**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-17; S-M06-02 | Tipus de llicència, categories (aficionat, tècnic), preus i trams de l'any natural, i càlcul exacte dels 365 dies (dia d'inici, any de traspàs) | 06: producció |
| S-M06-12, 13 | Si encara existeix la llicència d'un dia; quan s'obre cada any el període per demanar la de l'any següent | 06: activar l'opció d'un dia; sol·licitud anticipada |
| M06-13 dubte 2 | Si el formulari de club també demana la data de naixement | 06: producció (punt 0 de la junta) |
| RP-M02-03 | Condicions de la cobertura internacional de la llicència (avís 7 dies abans; excepte Portugal i França) | — |
| S-M06-03 | Format i dades del llistat per tramitar; si la federació el pot importar | 06: producció (T-M06-10) |
| S-M06-06; M06-13 dubte 5 | Devolució d'una llicència ja tramitada; si es cobra abans o després de tramitar | — |
| S-M02-10 | Relació entre el certificat del club i la titulació oficial | — |
| S-M02-11 | Llista de nivells i d'agències de titulació | — |

<a id="preguntes-secretaria"></a>
**Secretaria**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-18 | Data d'alta dels socis que Cluber no té | — |
| S-M02-15 | Dies del recordatori d'una activitat | — |
| S-M06-04, 09 | «Ja en tinc una» per a socis i qui la comprova; número federatiu obligatori | — |
| RN-M06-09 | Una llicència vigent no es cancel·la, es deixa caducar | — |

<a id="preguntes-informatica"></a>
**Informàtica**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M01-19 | Remitent dels correus (el proveïdor, Brevo, és a la [062](decisions/062-brevo-es-mante-com-a-proveidor-de-correu.md)); també per als avisos d'ajuts | 00: correu en producció |
| S-M01-20 | Eina d'auditoria d'accessibilitat | — |
| S-M05a-10 | Biblioteca de xifratge i rols de PostgreSQL separats; també per als documents de justificació (051) | — |
| S-M05a-12 | Temps per tornar a demanar la contrasenya | — |
| S-M02-23 | On viuen les propostes de devolució | — |
| S-M03-07 | Periodicitat legal de les revisions d'ampolles i reguladors | — |
| RN-T31, RN-T32 ([053](decisions/053-addenda-050-moviments-d-origen-extern-en-periode-tancat.md)) | Cada quan s'importa l'extracte i es processen les liquidacions (com més tard, més moviments entren al període obert) | — |
| RN-M01-41, RN-M01-43 ([054](decisions/054-addenda-052-versio-dels-esdeveniments-i-comprovacio-diaria.md)) | A quina hora corre la comprovació diària de la llicència (després de la tasca diària del 06), qui rep l'avís si fa correccions i on es veu el resum | — |
| RN-M09-25 (risc de [M09-13](#M09-13-riscos)) | Si la càmera oberta des del navegador (Android i iPhone) desa la foto a la galeria o al núvol del telèfon, i si hi ha una manera de pujar-la sense que s'hi guardi | — |
| M12-idees | Fonts i condicions d'ús per a l'assistent d'ajuts (BDNS, Generalitat, Diputació, CIDO) | — (idea futura) |

<a id="preguntes-cursos-sortides"></a>
**Responsable de cursos i sortides**
| ID | Pregunta | Bloqueja |
|---|---|---|
| S-M06-12 | ~~Si existeix avui la llicència d'un dia~~ **Respost** ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md)): existeix i `licences.day_enabled` és activada | — |
| S-M06-02 | Quins tipus de llicència tramita el club i a quins preus (aficionat, tècnic, altres) | 06: producció |
| RP-M02-02 | Si cal la llicència tècnica per als instructors | — |
| RP-M02-03 | Quines sortides són a l'estranger i necessiten l'avís de cobertura internacional | — |

<a id="preguntes-responsable"></a>
**Responsable del projecte**
| ID | Pregunta | Bloqueja |
|---|---|---|
| RN-M03-10 | El lloguer entra al marge com a despesa amb factura | 09 |
| S-M02-13 | Llista de subtipus de medi ambient i projectes actuals | — |
| S-M02-21, 22 | Servei de previsió marítima enllaçat; pujar observacions a Minka | — |
| RP-M02-01 | Com el 02 demanarà al 06 si una activitat necessita llicència d'un dia (en revisar el 02; condicional a `licences.day_enabled`) | — |
| M02, M03, M09, M06 | Aprovar les seccions dels mòduls 02, 03, 09 (amb l'apartat d'ajuts) i 06 | 02, 03, 09 i 06 |

<a id="ordre-del-dia-junta"></a>
# Apèndix — Ordre del dia per a la junta

Tots els pendents de la junta dels mòduls 01, 02, 03, 04, 05a, 05b, 06 i 09, en **dues parts** (28/10/2026). Cada punt diu la decisió que cal prendre, la **proposta de Claude** (el supòsit amb què ja funciona el codi, si no es diu el contrari) i on és el detall. Quan la junta decideix un punt, s'actualitza la secció del mòdul i se'n treu la fila d'aquí i de l'[apèndix de preguntes](#preguntes).
- **Part A, decisions de debò** (política, rols, qui paga). El **punt 0 és prioritari**. Cap punt no bloqueja començar a construir: bloquegen entrar en producció.
- **Part B, valors inicials que es poden canviar quan calgui** (preus, dies d'avís, llindars, llistes). **No bloqueja res** i es pot tractar més endavant: cada valor es canvia després des de la pantalla d'ajustos del mòdul ([regles generals](#regles), [valors configurables](#valors-configurables)).

<a id="ordre-del-dia-decisions"></a>
## Part A — Decisions de debò

| # | Tema | Decisió que cal prendre | Proposta de Claude | IDs |
|---|---|---|---|---|
| 0 | **Prioritari: data de naixement** | **Validar la finalitat, l'abast i l'obligatorietat per a tots els socis** ([058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) i precisió del 29/10/2026 a [M01-addenda-058](#M01-addenda-058)). Finalitat: tramitar llicències i comprovar l'edat mínima dels cursos i de les activitats. Abast: només la veuen la secretaria i l'administrador; la resta veu «major d'edat», «menor d'edat» o «edat desconeguda». Obligatorietat: a l'alta de tot soci; per als no socis, només si demanen una llicència o s'inscriuen a una activitat amb edat mínima. Socis existents: la completen ells o la secretaria, sense bloquejar res | Aprovar-ho tal com és, amb el principi de minimització; P-33 (menors) continua al punt 7 | Q-09; P-33; RN-M01-47 a 49; RN-M01-52 a 55 |
| 1 | **Preus: criteris** | Preu dels simpatitzants; no socis a les activitats; com es cobra el reforç; certificat del club; regla de l'import del canvi a ple dret; quota sencera a mig any. Els imports i el catàleg són a la part B (B1) | Simpatitzants al preu de soci; no socis només si l'activitat ho permet, al preu de no soci; reforç per proposta confirmada; certificat del club signat pel responsable; canvi a ple dret = diferència de quota; quota sencera | S-M02-04, 06, 08, 09; S-M01-01, 02 |
| 2 | **Política de cancel·lació** | Devolució quan cancel·la el participant i quan cancel·la el club (també per meteorologia). El termini per acceptar una plaça és a la part B (B2) | 100 % si cancel·la el club, també per meteorologia; si cancel·la el participant, el tresorer decideix cas per cas fins que la junta fixi una escala | S-M02-05 |
| 3 | **Centres de busseig** | Amb quins centres treballa el club; quines dades reben a la llista de lloguer. Les tarifes són a la part B (B3) | Recollir la llista de l'Excel actual; a la llista, referència i inicials, sense nom complet; si un centre demana noms, acord de tractament abans (gestoria) | S-M03-01, 04; M03-12 |
| 4 | **Material: cost d'ús i qui paga el lloguer** | Si el material del club té un cost d'ús al marge; si el lloguer es cobra en un càrrec a part o dins la inscripció; qui paga una peça perduda; bibotelles; qui assigna el material. L'import del cost d'ús, els codis, els dies dels avisos i l'inventari són a la part B (B4) | Sense cost d'ús d'inici; lloguer en un càrrec a part en confirmar-lo; la peça perduda l'anota el responsable i la junta decideix cas per cas; bibotella com una peça; assigna el responsable de material | S-M03-02, 03, 08, 09, 10 |
| 5 | **Quotes: venciment** | Quan es cobren les quotes i quan és la propera remesa; quotes pendents en una baixa; validesa del carnet dels socis que han pagat a Cluber (proposa el tresorer, ratifica la junta). Els dies dels recordatoris són a la part B (B5) | Any natural; s'anul·len les quotes posteriors a la baixa; carnet vàlid fins a final del període pagat a Cluber | P-29; S-M01-03, 05, 24 |
| 6 | **Carnet, verificació i socis** | Què mostra la verificació pública; si hi ha insígnia de soci clàssic; antiguitat en una readmissió; compte personal després de la baixa. El text del darrere i el llindar de soci clàssic són a la part B (B6) | Dos últims dígits i cap nom; sense insígnia d'inici; antiguitat des de la primera alta; el compte es manté per consultar rebuts | S-M01-06, 07, 09, 10, 12 |
| 7 | **Menors** | Si hi ha o hi haurà socis o participants menors; edat mínima a les activitats; si cal guardar la data de naixement (vegeu el punt prioritari 0) | Només majors d'edat a la plataforma fins que hi hagi un protocol (persona de referència i mandat signat pel titular del compte); cap data de naixement fins llavors | P-33; Q-09; S-M01-13; S-M02-19; dubte 2 de [M06-13](#M06-13-riscos) |
| 8 | **Matriu de rols** | **Resolt el 30/10/2026** per la [059](decisions/059-rols-i-permisos-editables.md): el responsable del projecte dona la matriu per validada, l'administrador assigna rols i edita els permisos des de l'app, i la configuració inicial és a l'[apèndix de rols i permisos](#rols-i-permisos-059-matriu). Qui canvia els preus del catàleg del 02 i les tarifes del 03 també hi és (VC-20 i VC-27). **Continua obert:** si qui puja una factura des del mòbil la pot tornar a obrir (RN-M09-23) | Per a RN-M09-23: no; només el tresorer i la junta (051) | P-04; Q-01; S-M01-14, 22, 23; S-M02-16, 17, 18; S-M03-10; S-M04-09; S-M05a-13; S-M05b-13; S-M06-05; S-M09-01; VC-20; VC-27 (resolts); RN-M09-23 (obert) |
| 9 | **Comissió de retorn** | Qui paga la comissió del banc quan es retorna un rebut domiciliat | La paga el club d'inici; es revisa si els retornats augmenten. L'import és [A verificar: banc] | S-M05b-08 |
| 10 | **Carnet amb una quota retornada** | Si el carnet continua vàlid mentre la quota retornada no es paga | No és vàlid fins que es pagui (el soci rep l'alternativa de pagament) | S-M05b-09 |
| 11 | **Ajuts: responsable i convocatòries** | Qui és el responsable dels ajuts i de cada sol·licitud; quines convocatòries s'han de vigilar; qui rep els avisos; si hi ha avisos abans de justificar; format de justificació de cada organisme. Els dies dels avisos són a la part B (B7) | Responsable per defecte: el tresorer, amb una persona de la junta per a medi ambient; començar per les convocatòries que el club ja ha demanat; avisos al responsable i al tresorer; sí, avisos també abans de justificar; paquet genèric fins que un organisme en demani un altre | S-M09A-01 a 05 |
| 12 | **Llicències** | Quan s'activa l'opció de no socis; persona de fora que es fa sòcia; comissió del cobrament de la llicència d'un soci; **condicional**: llicència d'un dia sense inscripció, només si el responsable de cursos i sortides confirma que existeix; categories (aficionat i tècnic) i si cal la tècnica per als instructors. El recàrrec, el departament i la data d'obertura de l'any següent són a la part B (B8) | Activar l'opció de no socis quan la junta ho decideixi; cap retorn; el club assumeix la comissió d'inici; llicència d'un dia desactivada fins que es confirmi i, si s'activa, sense inscripció; tècnica per als instructors segons digui el responsable de cursos i sortides | S-M06-07 (condicional), 08, 12; RP-M02-02; dubte 4 de [M06-13](#M06-13-riscos) |
| 13 | **Departaments, marge i informes** | Ingrés de les quotes a «General / Quotes de socis»; si el marge per departament inclou els costos generals; informes de l'assemblea; hores de voluntariat; pressupostos; qui reobre un període tancat i si el tresorer ho ha de poder demanar; fotos de factures i comprovants que queden a la galeria del telèfon. La llista de departaments i el llindar de marge baix són a la part B (B9) | Quotes a «General / Quotes de socis»; mostrar marges i costos generals per separat; informes en CSV; hores sense valorar en euros; pressupostos més endavant; només l'administrador reobre, amb motiu i avís per correu al tresorer i a la junta, i el tresorer no ho demana a la plataforma; text d'ajuda a la pujada que demana esborrar la foto, i una norma per als responsables si informàtica confirma que la foto es copia al núvol | S-M04-06; S-M09-06, 10, 11, 12, 13; RN-M09-25 |
| 14 | **Activitats: altres** | Avís o bloqueig si no es compleixen els requisits; dades ambientals; protocol d'accidents i contacte d'emergència; drets del simpatitzant. Els tipus de sortida propis són a la part B (B10) | Avís, no bloqueig; residus en kg, espècies, observacions i fotos; protocol fora de la plataforma; els simpatitzants tenen els mateixos drets al 01 | S-M02-01, 14, 20; S-M01-11 |
| 15 | **Pagaments i producció** | Autoritzacions dels nivells 1 i 2 de producció; qui guarda la còpia de la clau; textos del mandat, de la invitació i del correu G3; titular del compte diferent del soci; registre manual de cobraments en efectiu; doble aprovació | Autoritzar cada nivell quan es passin les portes de la checklist; dues persones de la junta per a la clau; Claude prepara els esborranys dels textos; titular diferent admès amb declaració; registre manual només pel tresorer, amb justificant; sense doble aprovació | 025; S-M05a-05, 09; M05a-14 punt 2; P-12; P-48 |
| 16 | **Canvis d'imports** | Si algun import (quota, preu, tarifa, recàrrec, comissió) només es pot canviar amb ratificació de la junta; qui rep l'avís de cada canvi com a «junta» ([055](decisions/055-ajustos-configurables-i-addendes.md)) | Cap ratificació: el canvi s'aplica, el tresorer i la junta reben un correu amb el valor anterior i el nou, i la junta pot demanar desfer-lo; destinataris: una llista d'adreces de la junta que manté l'administrador | S-AJ-01, 02 |

<a id="ordre-del-dia-valors"></a>
## Part B — Valors inicials que es poden canviar quan calgui

No bloqueja res. Són els valors amb què arrenca el codi; la junta els pot confirmar quan li vagi bé, i es canvien després des de la pantalla d'ajustos del mòdul, amb registre ([valors configurables](#valors-configurables)).

| # | Valors | Valor inicial proposat | Abans al punt | IDs |
|---|---|---|---|---|
| B1 | Catàleg de cursos i d'especialitats amb preus de soci i de no soci | Passar el catàleg actual tal com és | 1 | S-M02-07 |
| B2 | Termini per acceptar una plaça oferta | 48 hores | 2 | S-M02-03 |
| B3 | Tarifes dels centres de busseig (cost, soci i, si n'hi ha, no soci) | Les de l'Excel actual | 3 | S-M03-01 |
| B4 | Material: import del cost d'ús; format dels codis; dies dels avisos; inventari inicial | 0; `MAT-NNNN` (o les etiquetes que ja tinguin); 30 i 7 dies; càrrega en CSV | 4 | S-M03-02, 05, 06, 11 |
| B5 | Dies dels recordatoris de quota | 15 dies abans i 15 i 30 després | 5 | S-M01-04 |
| B6 | Text del darrere del carnet; llindar de soci clàssic, si n'hi ha | Contacte del club i com verificar-lo; sense llindar | 6 | S-M01-08, 09 |
| B7 | Dies dels avisos d'ajuts (abans de justificar) i d'un requeriment d'esmena | 30, 14 i 7 dies; requeriment: immediat i 7 i 2 dies abans de la data límit | 11 | S-M09A-04, 09 |
| B8 | Llicències: import del recàrrec de no soci; departament; data d'obertura de l'any següent | Quan la FECDAS doni els preus; «General / Llicències»; 1/12 (o la data de la FECDAS) | 12 | S-M06-01, 10, 13; S-M04-07 |
| B9 | Llista de departaments i centres de cost; llindar de marge baix | «General» i els departaments que avui demanen ajuts; 0 € | 13 | Q-17; S-M04-01; S-M09-04, 07 |
| B10 | Tipus de sortida propis | Sèniors i jornades obertes, desactivables | 14 | S-M02-12 |

<a id="valors-configurables"></a>
# Apèndix — Valors configurables

Aplica la regla general de [valors de negoci](#regles) (28/10/2026). Per a cada valor: on viu **ara** segons la secció del mòdul, on hauria de viure (**proposta**), valor inicial, rang vàlid, qui el canvia, si queda al registre i si té data d'entrada en vigor. **«Ajustos»** vol dir base de dades, editable a la pantalla d'ajustos del mòdul, amb registre (qui, quan, valor anterior). **«Dada»** vol dir que ja és una llista o una fila editable a l'app (catàlegs, tipus, tarifes). **«Entorn»** vol dir variable d'entorn, que canvia informàtica en desplegar.

Llegenda de la columna **Canvi**: **—** ja és com ha de ser; **058** vol dir que el valor ve de la decisió [058](decisions/058-respostes-fecdas-gestoria-i-cursos.md) i és a l'addenda del mòdul (29/10/2026); **Aplicada** vol dir que el mòdul (escrit en aquell moment, aprovat el 28/10/2026) ja el té al bloc «Valors configurables» de la secció 6 (28/10/2026); **No aplicada** vol dir que contradiu una regla escrita i es manté la regla; **055** s'aplica amb una addenda al mòdul aprovat ([055](decisions/055-ajustos-configurables-i-addendes.md)); **Es queda** és regla, seguretat, format d'integritat o secret, i no s'edita des de l'app. Cap regla aprovada no s'ha editat.

| ID | Mòdul | Valor | On viu ara | Proposta | Valor inicial | Rang vàlid | Qui el canvia | Registre | En vigor | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|
| VC-01 | 01 | Quota anual per tipus de soci (`annual_fee_cents`) | Dada (tresorer o administrador, amb motiu) | Ajustos, amb data d'entrada en vigor | 3500 i 9000 cèntims | > 0 | Tresorer o administrador | Sí, amb motiu | Sí (nova) | 055 |
| VC-02 | 01 | Dies dels recordatoris de quota (RN-M01-14) | No definit (al text) | Ajustos | 15 abans; 15 i 30 després | 1 a 90 | Tresorer | Sí | — | 055 |
| VC-03 | 01 | Text del darrere del carnet (S-M01-08) | No definit | Ajustos (text) | Contacte del club i com verificar-lo | Fins a 300 caràcters | Secretaria o administrador | Sí | — | 055 |
| VC-04 | 01 | Llindar de soci clàssic (S-M01-09) | No definit | Ajustos (anys; 0 = sense insígnia) | 0 | 0 a 60 | Junta (administrador) | Sí | — | 055 |
| VC-05 | 01 | Xifres visibles a la verificació pública (S-M01-06) | Text | Codi | Dues | — | — | — | — | Es queda (privacitat) |
| VC-06 | 01 | `CLUBER_FINAL_IMPORT_ALLOWED` | Entorn | Entorn | Fals | — | Informàtica | Desplegament | — | Es queda (seguretat d'una operació única) |
| VC-07 | 01 | `ADMIN_URL_PATH`; remitent dels correus (S-M01-19) | Entorn | Entorn | — | — | Informàtica | Desplegament | — | Es queda (tècnic) |
| VC-08 | 04 | Departaments, centres de cost i comptes de tresoreria | Dada (administrador; S-M04-09) | Dada | «General» i els seus centres | Noms únics | Administrador | Sí | — | — |
| VC-09 | 04 | `CLUB_IBAN_TRANSFERENCIES` (IBAN del club per pagar per transferència) | Entorn | Entorn | [A verificar: banc] | — | Informàtica, amb ordre del tresorer | Desplegament | — | Es queda (canviar on paguen els socis és un risc de frau) |
| VC-10 | 04 | `TRANSFER_REFERENCE_PREFIX` | Entorn | Codi o entorn | — | — | Informàtica | Desplegament | — | Es queda (format d'integritat de la conciliació) |
| VC-11 | 05a | Dies dels recordatoris de la campanya de mandats (RN-M05a-14) | No definit (al text) | Ajustos | 7 i 14 dies | 1 a 60 | Tresorer | Sí | — | 055 |
| VC-12 | 05a | Minuts per tornar a demanar la contrasenya (RN-M05a-12) | Text | Codi | 15 | — | Informàtica | — | — | Es queda (seguretat) |
| VC-13 | 05a | Caducitat d'un mandat sense cobraments (RN-M05a-08) | Text | Codi | 36 mesos | — | — | — | — | Es queda (regla SEPA) [A verificar: banc] |
| VC-14 | 05a | Mètodes actius del proveïdor (`card_enabled`, `bizum_enabled`, `tokenization_enabled`) | Dada (administrador, A7) | Dada | Segons el proveïdor | — | Administrador | Sí | — | — |
| VC-15 | 05a | `PAYMENTS_LIVE_CHARGES_ALLOWED`, `SEPA_CREDITOR_ID`, `MANDATE_ENCRYPTION_KEYS`, claus del proveïdor | Entorn | Entorn | Fals; [A verificar: banc]; secret | — | Informàtica (nivells de producció, 025) | Desplegament | — | Es queda (seguretat i secrets) |
| VC-16 | 05b | `PaymentSettings`: dies del recordatori de transferència i de l'avís previ, màxim d'intents de domiciliació | Base de dades amb registre | Ajustos (pantalla) | 30; 14; 2 | 7 a 60; 14 a 30 (avís previ, segons el text del mandat [A verificar: banc]); 1 a 3 | Tresorer | Sí | — | 055 (només la pantalla) |
| VC-17 | 05b | `PaymentSettings`: minuts d'espera de Bizum i edat de la xarxa de seguretat | Base de dades amb registre | Ajustos, només administrador | 15; 60 | 5 a 30; 30 a 240 | Administrador | Sí | — | 055 (només la pantalla) |
| VC-18 | 05b | Qui paga la comissió de retorn (`payments.return_fee_payer`, RN-M05b-16) i carnet amb una quota retornada (RN-M05b-18) | Valors configurables | Ajustos (commutadors) | El club; no vàlid. La 058 decideix que, al segon intent, la pagui el soci (RN-M05b-26), però el valor continua sent «el club» fins que la junta i el banc ho validin i ho cobreixin els estatuts | Club o soci | Administrador, per decisió de la junta | Sí | Sí | 055 (només la pantalla); 058 |
| VC-19 | 05b | Format del número de rebut (`R-AAAA-NNNNNN`) | Text | Codi | — | — | — | — | — | Es queda (numeració) |
| VC-20 | 02 | Catàleg de cursos i especialitats, preus de soci i de no soci, tipus i subtipus de sortida, projectes | Dada | Dada, amb data d'entrada en vigor per als preus | Buit; «Neteja»; Sèniors i jornades obertes desactivables | Preus ≥ 0 | Responsable de cursos i sortides; preus, tresorer [A validar: junta] | Sí | Sí (preus) | Aplicada en part: la data d'entrada en vigor dels preus sí; que els preus els canviï el tresorer, no (contradiu RN-M02-01 i HU-M02-01: els canvia el responsable de cursos i sortides) |
| VC-21 | 02 | Termini de pagament d'una inscripció per defecte (RN-M02-08; cada activitat el pot canviar) | Text (valor per defecte) | Ajustos | 72 hores | 24 a 240 | Tresorer | Sí | — | Aplicada |
| VC-22 | 02 | Hores per acceptar una plaça oferta (RN-M02-09) | Text | Ajustos | 48 | 12 a 168 | Responsable de cursos i sortides | Sí | — | Aplicada |
| VC-23 | 02 | Dies del recordatori d'una activitat (RN-M02-19) | Text | Ajustos | 2 | 0 a 14 | Secretaria | Sí | — | Aplicada |
| VC-24 | 02 | Mode dels requisits per defecte (avís o bloqueig, RN-M02-10) | Camp per activitat; per defecte al text | Ajustos (per defecte) i camp per activitat | Avís | Avís o bloqueig | Responsable de cursos i sortides, per decisió de la junta | Sí | — | Aplicada |
| VC-25 | 02 | Enllaç del servei de previsió marítima (RN-M02-24) | Text | Ajustos (URL) | Meteocat | URL https | Administrador | Sí | — | Aplicada |
| VC-26 | 02 | Numeració del certificat (`C-AAAA-NNNN`) | Text | Codi | — | — | — | — | — | Es queda (numeració) |
| VC-27 | 03 | Tipus de material, centres de busseig i tarifes | Dada | Dada, amb data d'entrada en vigor per a les tarifes | Buit | ≥ 0 | Responsable de material; tarifes, tresorer | Sí | Sí (tarifes) | No aplicada: les tarifes ja tenen versions amb data d'inici (RN-M03-06); que les canviï el tresorer contradiu C3 i MT8 (les manté el responsable de material) |
| VC-28 | 03 | Cost d'ús del material del club (RN-M03-08) | Text | Ajustos per tipus | 0 | ≥ 0 | Tresorer | Sí | Sí | Aplicada |
| VC-29 | 03 | Dies dels avisos de revisió i de peces no retornades (RN-M03-14, 15) | Text | Ajustos | 30 i 7 | 1 a 90 | Responsable de material | Sí | — | Aplicada |
| VC-30 | 03 | Format dels codis de les peces (`MAT-NNNN`) | Text | Codi | — | — | — | — | — | Es queda (integritat) |
| VC-31 | 09 | Llindar de marge baix (RN-M09-14) | Text | Ajustos | 0 € | Qualsevol import (també negatiu) | Tresorer | Sí | — | Aplicada |
| VC-32 | 09 | Durada del període (RN-M09-15) | Text | Ajustos; només s'aplica als períodes nous | Mensual | Mensual, trimestral | Tresorer | Sí | Sí | Aplicada, amb RN-M09-28 i la prova de la 055 |
| VC-33 | 09 | Categories de despesa i proveïdors | Dada | Dada | Les de F §7 | — | Tresorer | Sí | — | — |
| VC-34 | 09 | Facturació activada per tipus de càrrec (RN-M09-19) | Text | Ajustos (commutadors) | Desactivada | — | Administrador, per decisió de la junta | Sí | Sí | Aplicada |
| VC-35 | 09 | Text d'ajuda de la pujada de documents (RN-M09-25) | Text | Ajustos (text) | El de RN-M09-25 | Fins a 400 caràcters | Administrador | Sí | — | No aplicada: el text és la mitigació d'un risc de dades fora de la UE (RN-M09-25, 051); es queda al codi |
| VC-36 | 09 (ajuts) | Dies dels avisos de tancament i de justificació (RN-M09A-06) | Configurable, sense lloc | Ajustos | 30, 14 i 7 | 1 a 90 | Tresorer | Sí | — | Aplicada |
| VC-37 | 09 (ajuts) | Dies dels avisos d'un requeriment (RN-M09A-19) | Text | Ajustos (el primer, immediat, és fix) | 7 i 2 | 1 a 30 | Tresorer | Sí | — | Aplicada |
| VC-38 | 06 | Tipus, categories, regles de validesa i preus (amb trams) | Dada amb versions | Dada; `valid_from` és la data d'entrada en vigor | [A verificar: FECDAS] | Preus ≥ 0 | Tresorer (S-M06-05) | Sí, amb nota | Sí | — |
| VC-39 | 06 | `licences.non_members_enabled` | Configuració (nom d'entorn) | Ajustos (commutador) | Desactivada | — | Administrador, per decisió de la junta | Sí | — | Aplicada |
| VC-40 | 06 | `licences.day_enabled` | Ajustos | Ajustos (commutador) | **Activada** (la llicència d'un dia existeix, 058) | Sí o no | Administrador | Sí | — | 058 (el número 056 no es fa servir) |
| VC-41 | 06 | `licences.reminder_days` i `licences.to_renew_days` | Configuració (nom d'entorn) | Ajustos | 60, 30 i 7; 60 | 1 a 120 | Secretaria | Sí | — | Aplicada |
| VC-42 | 06 | `licences.next_year_opens_on` | Ajustos | Ajustos (dia i mes) | 1/12, decidit pel club (058) | 1/10 a 31/12 | Secretaria | Sí | — | 058 |
| VC-43 | 06 | `LICENCE_REMINDER_BATCH_SIZE` | Configuració | Entorn | [A validar: informàtica] | — | Informàtica | Desplegament | — | Es queda (tècnic) |
| VC-44 | 06 | Preu de soci = preu de la federació (RN-M06-05) | Regla | Codi | — | — | — | — | — | Es queda (regla) |
| VC-45 | 06 | Recàrrec de no soci (`non_member_surcharge_cents` a `LicencePrice`, RN-M06-06) | Dada amb versions | Dada; `valid_from` és la data d'entrada en vigor | 2000 cèntims (058) | ≥ 0 | Tresorer (S-M06-05) | Sí, amb nota i avís (RN-AJ-04) | Sí | 058 |
| VC-46 | 02 | `activities.instructor_requirements_mode` (RN-M02-26) | Ajustos | Ajustos | `block` [A validar: junta] | `block`, `warn` | Responsable de cursos i sortides, per decisió de la junta | Sí | — | 058 |
| VC-47 | 02 | `default_requirements_mode` per tipus de sortida i per fitxa del catàleg (RN-M02-29) | Dada | Dada | Buit (val VC-24) | `warn`, `block` o buit | Responsable de cursos i sortides | Sí | — | 058 |
| VC-48 | 05a | `payments.card_expiry_notice_days` (RN-M05a-20) | Ajustos | Ajustos | 30 dies [A validar: tresorer] (060) | [A validar: tresorer] | Tresorer | Sí | — | 058; 060 |
| VC-49 | 09 | `billing.vat_rate_by_charge_kind` (RN-M09-29) | Ajustos | Ajustos, per tipus de càrrec | Inscripció (cursos, sortides i material): tipus [A verificar: gestoria]; quota i llicència: exemptes | Tipus d'IVA vigents [A verificar: gestoria] | Tresorer | Sí, amb avís (RN-AJ-04) | Sí | 058 |
| VC-50 | 09 | `billing.vat_exemption_text` (RN-M09-29) | Ajustos | Ajustos (text) | [A verificar: gestoria] | Text | Tresorer | Sí | Sí | 058 |
| VC-51 | 09 (ajuts) | `amendment_term_days` per convocatòria (RN-M09A-23) | Dada | Dada (camp opcional de la convocatòria) | Buit | Buit o ≥ 1 | Tresorer | Sí | — | 058 (sense prioritat) |

**Fora d'aquesta llista.** Els valors de la spec 00 són a la [spec 00](../specs/00-base-comuna/spec.md) fins que la 00 tingui secció. Els rols i els permisos són dades editables per l'administrador ([059](decisions/059-rols-i-permisos-editables.md)): la configuració inicial és a l'[apèndix de rols i permisos](#rols-i-permisos-059-matriu), i qui canvia cada valor d'aquesta llista és un permís `settings.edit.<clau>` (RN-RP-17). La peça comuna d'ajustos (model, pantalla base, registre i data d'entrada en vigor) és de la 00 i és a la [055](#valors-configurables-055).

<a id="valors-configurables-055"></a>
## Decisió 055: peça comuna d'ajustos (00)

Acceptada el 28/10/2026 ([055](decisions/055-ajustos-configurables-i-addendes.md)). La spec 00 no s'edita: la peça comuna és aquí fins que la 00 tingui secció. Als mòduls aprovats s'aplica amb una addenda ([01](#M01-addenda-055), [05a](#M05a-addenda-055), [05b](#M05b-addenda-055)) sense canviar-ne cap regla. El 04 no té cap valor nou (VC-08 ja són dades). Es queden com estan: VC-05, 06, 07, 09, 10, 12, 13, 15 i 19.

**Entitats**
- `Setting`: `key` (única, amb el prefix del mòdul, per exemple `members.fee_reminder_days_before`), `module`, `value_type` (enter, cèntims, sí o no, text, opció, URL, dia i mes, llista d'enters), `initial_value`, rang (`min_value` i `max_value`, `choices` o `max_length`), `editor_roles`, `affects_money` i `effective_dated`.
- `SettingVersion`: `setting`, `value`, `effective_from` (data, buida si el valor no en té), `changed_by` (compte), `changed_at`, `previous_value`, `note`. Només s'hi afegeixen files: mai s'editen ni s'esborren.

**Regles**
| ID | Regla |
|---|---|
| RN-AJ-01 | **Lectura:** `settings.get(key, at)` torna el valor de la versió amb la `effective_from` més gran que no passa de la data `at` (si n'hi ha dues amb la mateixa data, la creada més tard); sense cap versió, el valor inicial. Cap mòdul escriu un valor de negoci al codi |
| RN-AJ-02 | **Canvi:** `settings.change(key, value, user, note, effective_from)` comprova al servidor el rol (sense permís, «no trobat»), el tipus i el rang (fora de rang es rebutja i no es desa res). Crea una `SettingVersion` i escriu al registre d'activitat qui, quan, el valor anterior i el compte. Tornar al valor inicial és un canvi més |
| RN-AJ-03 | **Data d'entrada en vigor:** si el valor afecta diners, la data és obligatòria i no pot ser anterior a avui, i la nota també és obligatòria. El canvi no toca el que ja s'ha demanat, inscrit o cobrat: cada mòdul llegeix el valor a la data que fixa la seva regla. Un canvi programat es desfà amb un altre canvi amb la mateixa data |
| RN-AJ-04 | **Avís dels canvis de diners (condició a de la 055):** tot canvi d'un valor que afecta diners (quotes, preus, tarifes, recàrrecs, comissions), sigui un `Setting` o una fila d'un catàleg o d'una tarifa, envia un correu al tresorer i a la junta amb el valor, el valor anterior, el nou, qui l'ha canviat, la nota i la data d'entrada en vigor. Els catàlegs i les tarifes el criden amb `settings.notify_money_change`. El correu va per la cua i es reintenta; si falla, el canvi no es desfà. És un avís: no cal cap segona aprovació. Si algun import ha de ser «només amb ratificació»: [A validar: junta, S-AJ-01] |
| RN-AJ-05 | **Pantalla base:** per a cada mòdul, la llista dels seus valors amb el valor vigent, el programat (si n'hi ha), el valor inicial, el rang i l'historial. Només la veuen els rols amb permís sobre algun valor del mòdul |

**Supòsits**
| ID | Supòsit | Proposta | Qui ho valida |
|---|---|---|---|
| S-AJ-01 | Si algun import només es pot canviar amb ratificació de la junta | Cap: el canvi s'aplica i s'avisa (RN-AJ-04); la junta pot demanar que es desfaci amb un altre canvi | Junta |
| S-AJ-02 | Qui rep l'avís com a «junta» mentre el rol Junta no estigui validat (P-04) | Una llista d'adreces de la junta als ajustos generals, que manté l'administrador | Junta |

**Criteris d'acceptació**
- **CA-AJ-01** Donat un valor amb rang 1 a 90, quan es desa 0 o 91, llavors es rebutja amb un missatge i no es crea cap versió.
- **CA-AJ-02** Donat un rol sense permís sobre un valor, quan el vol canviar, llavors rep «no trobat» i no es crea cap versió.
- **CA-AJ-03** Donat un valor de diners canviat amb data d'entrada en vigor demà, quan es llegeix avui, llavors torna el valor anterior; quan es llegeix demà, torna el nou; una data anterior a avui o sense nota es rebutja.
- **CA-AJ-04** Donat un canvi d'un valor de diners (un `Setting` o una fila de catàleg o de tarifa), quan es desa, llavors el tresorer i la junta reben un sol correu amb el valor anterior i el nou; un canvi d'un valor que no és de diners no envia cap correu; si el correu falla, el canvi es manté i el correu es reintenta.
- **CA-AJ-05** Donat qualsevol canvi, quan es desa, llavors el registre d'activitat guarda qui, quan, el compte i el valor anterior, i l'historial de la pantalla el mostra.
- **CA-AJ-06** (condició b de la 055) Donat períodes mensuals fins al darrer, que acaba el 31/03, quan el tresorer canvia la durada del període (VC-32) a trimestral, llavors el període nou comença l'1/04 i acaba el 30/06: cap dia queda fora de cap període ni dins de dos, i els períodes existents no canvien. La prova és a la T-M09-26.

**Tasques**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-AJ-01 | Peça comuna: `Setting`, `SettingVersion`, serveis `settings.get`, `settings.change` i `settings.notify_money_change`, registre, data d'entrada en vigor i correu dels canvis de diners | M | `apps/core/business_settings.py`, migració | T-M01-06, T-M01-07, T-M01-10 | CA-AJ-01 a 05 |
| T-AJ-02 | Pantalla base d'ajustos (llista per mòdul, formulari segons el tipus, historial) | S | `apps/core/views/business_settings.py`, plantilles | T-AJ-01 | Proves de permisos, de rang i d'historial |

---

<a id="rols-i-permisos-059"></a>
# Apèndix — Rols i permisos editables (decisió 059)

Acceptada el 30/10/2026 ([059](decisions/059-rols-i-permisos-editables.md)). És una peça comuna de la 00: la spec 00 no s'edita i la peça viu aquí fins que la 00 tingui secció, com la [peça d'ajustos](#valors-configurables-055). Als mòduls aprovats s'aplica amb una addenda ([01](#M01-addenda-059), [04](#M04-addenda-059), [05a](#M05a-addenda-059), [05b](#M05b-addenda-059), [02](#M02-addenda-059), [03](#M03-addenda-059), [09](#M09-addenda-059), [06](#M06-addenda-059)) que no canvia cap regla. Substitueix la matriu provisional de la spec 00 (§2.2 a §2.4 i RN-45) i resol P-04 i Q-01.

**Què es pot fer des de l'app.** L'administrador, i només ell:
1. assigna i retira un o diversos rols als comptes d'administrador;
2. modifica els permisos de cada rol, amb efecte sobre tots els comptes que el tenen.

La matriu de sota és la **configuració inicial**. Les regles protegides no es poden canviar des de l'app.

**Entitats**
- **Catàleg de permisos (codi, no base de dades):**
  - `code` (amb el prefix del mòdul, per exemple `expenses.register`), `module`, descripció en català i `kind` (`action` o `field`);
  - `allowed_scopes`: llista tancada, per exemple `all`, `own_activities`, `own_sessions`;
  - `protected`: si és sí, l'editor el mostra però no el deixa canviar;
  - `requires`: permisos sense els quals no es pot atorgar.
- `Role`: `code`, nom en català, `is_management` (s'assigna a comptes d'administrador). Llista fixa, creada per migració: no es crea ni es reanomena des de l'app.
- `RolePermission`: `role`, `permission_code`, `scope`. Només hi ha files per als permisos no protegits.
- `AccountRole`: `admin_account`, `role`, `assigned_by`, `assigned_at`, `removed_by`, `removed_at`. Retirar un rol omple `removed_*`; la fila no s'esborra.
- `PermissionMatrixVersion`: `number`, `changed_by` (compte), `changed_at`, `note`, `diff` (abans i després de cada cel·la) i `affected_accounts`. Només s'hi afegeixen files.
- Es fan servir taules pròpies, no els grups de Django, perquè l'abast, les regles protegides i les versions no hi caben. Amplia la T-M01-06 sense canviar-ne el que ja fa.

**Regles**
| ID | Regla |
|---|---|
| RN-RP-01 | **Permís per petició.** Els permisos d'un compte d'administrador es calculen a cada petició, a partir dels seus rols actius i de la matriu vigent. No es guarden a la sessió. Primer el rol, després l'objecte i després els camps (spec 00 §2.6, punt 3) |
| RN-RP-02 | **Unió.** El permís d'un compte és la unió dels seus rols (RN-27). Si un permís té abasts diferents en dos rols, guanya el més ampli. Els camps sensibles no protegits també se sumen |
| RN-RP-03 | **Cap deducció.** Cada permís s'atorga sol. Un permís amb `requires` no es pot desar sense els que demana: l'editor ho rebutja amb un missatge i no els afegeix sol |
| RN-RP-04 | **Abast tancat.** L'abast s'escull d'`allowed_scopes`. Els abasts base no s'amplien: el soci, «propi»; el convidat, l'objecte de l'enllaç; l'instructor, les seves sessions. Avaluar pràctiques, proposar reforç i posar apte només admeten l'abast «les seves sessions»: només ho fa qui fa classe a la sessió, tingui el rol que tingui |
| RN-RP-05 | **Regles protegides.** No són files de `RolePermission` i l'editor les mostra com a només lectura, amb la decisió que les fixa: les 15 de la [059](decisions/059-rols-i-permisos-editables.md), punt 4. Entre elles, gestionar usuaris, rols i permisos és exclusiu del rol administrador i no es pot donar a cap altre rol |
| RN-RP-06 | **Editor: qui i com.** Només el rol administrador. Per desar, cal tornar a escriure el TOTP (temps màxim des de l'últim TOTP: 5 minuts, valor de seguretat al codi, com V-01) i una nota obligatòria |
| RN-RP-07 | **Resum abans de desar.** L'editor mostra cada cel·la que canvia (abans i després), la llista de comptes afectats (nom d'usuari) i un avís si el canvi toca diners, dades personals o un camp sensible. Sense confirmar el resum no es desa res |
| RN-RP-08 | **Registre i versions.** Cada canvi de la matriu o de rols d'un compte deixa una entrada al registre d'activitat (qui, quan, compte, rol, permís, abast, valor anterior, valor nou, nota) i, per a la matriu, una `PermissionMatrixVersion`. No s'editen ni s'esborren. «Tornar a la configuració inicial» és un canvi més, amb resum i nota |
| RN-RP-09 | **Avís.** Cada canvi envia un correu de notificació a tots els comptes amb el rol administrador, als comptes afectats i als comptes amb el rol President. El correu diu què ha canviat i qui ho ha fet, sense dades personals de terceres persones |
| RN-RP-10 | **Efecte a la petició següent.** Retirar un rol o modificar un permís té efecte a la petició següent de tots els comptes afectats. En desar un formulari obert, el servidor torna a comprovar el permís: si ja no hi és, es rebutja sense revelar dades i queda al registre |
| RN-RP-11 | **Sessions.** Si un compte es queda sense cap rol, se'n tanquen les sessions i el compte continua actiu sense accés (desactivar-lo és una acció a part, CA-13.2). Si un canvi amplia l'accés a dades personals o a diners, es tanquen les sessions d'administració dels comptes afectats, perquè tornin a entrar amb TOTP |
| RN-RP-12 | **Responsables orfes.** Si un compte perd el rol amb què era responsable d'un objecte (activitat, sessió, sol·licitud d'ajut), l'objecte no es reassigna sol: surt a la llista «sense responsable» de l'administrador |
| RN-RP-13 | **Administrador operatiu.** Operatiu vol dir actiu, amb TOTP donat d'alta, no bloquejat i que no és compte d'emergència. Es rebutja qualsevol canvi que en deixi menys d'un: retirar el rol, desactivar el compte, restablir-ne el TOTP o tocar els permisos del rol administrador (que, a més, són protegits). Per sota de dos, avís permanent a l'administració (R10b de l'arquitectura). Amplia RN-26 sense canviar-la |
| RN-RP-14 | **Un sol tresorer.** Assignar el rol tresorer a un segon compte actiu mostra un avís al resum (P-48), però no es bloqueja |
| RN-RP-15 | **Rols a l'acció.** Cada entrada del registre d'activitat feta amb un compte d'administrador guarda també els rols actius en aquell moment |
| RN-RP-16 | **Dashboard.** Veure el dashboard no dona accés a cap dada per si mateix. Hi surten les xifres econòmiques per a tots els rols que el poden veure, però cap dada personal que el rol no pugui veure per un altre permís. Des del dashboard no s'obre cap pantalla de detall ni cap acció sense el permís corresponent (regla per al mòdul 08) |
| RN-RP-17 | **Ajustos (055).** El camp `editor_roles` de `Setting` se substitueix per un permís del catàleg per a cada valor o grup de valors (`settings.edit.<clau>`). La configuració inicial és la columna «Qui el canvia» de l'[apèndix de valors configurables](#valors-configurables), amb els canvis de la [matriu](#rols-i-permisos-059-matriu) |

**Criteris d'acceptació**
- **CA-RP-01** Donat un compte amb els rols tresorer i responsable de material, quan se li retira el rol tresorer, llavors la petició següent ja no té cap permís de tresorer, la sessió continua oberta i el canvi queda al registre (amplia CA-13.1).
- **CA-RP-02** Donat el rol tresorer amb el permís `members.approve`, quan l'administrador el retira, llavors tots els comptes amb aquest rol perden el permís a la petició següent, i un formulari d'aprovació que ja era obert es rebutja en desar-lo.
- **CA-RP-03** Donat un compte amb el rol President, quan intenta obrir l'editor de permisos o assignar rols, llavors rep «no trobat»; quan l'administrador intenta donar el permís de gestionar usuaris i rols al rol President, llavors l'editor ho rebutja.
- **CA-RP-04** Donat l'editor, quan l'administrador desa un canvi sense tornar a escriure el TOTP o sense nota, llavors no es desa res.
- **CA-RP-05** Donat un canvi de la matriu, quan es mostra el resum, llavors hi surten totes les cel·les que canvien i tots els comptes afectats; en confirmar, hi ha una `PermissionMatrixVersion` nova, una entrada per cel·la al registre i un correu als administradors, als afectats i al President.
- **CA-RP-06** Donat un sol administrador operatiu, quan es vol retirar-li el rol, desactivar-lo o restablir-ne el TOTP, llavors es rebutja amb un missatge que ho explica; amb dos, s'accepta i surt l'avís permanent.
- **CA-RP-07** Donat el permís «aprovar una alta» sense «consultar sol·licituds» al mateix rol, quan es desa, llavors es rebutja amb un missatge i no s'afegeix cap permís sol.
- **CA-RP-08** Donat un compte amb el rol responsable de cursos i sortides i el permís d'avaluar atorgat al seu rol, quan vol avaluar un alumne d'una sessió on no fa classe, llavors rep «no trobat».
- **CA-RP-09** Donat qualsevol regla protegida (IBAN, documents de justificació, data de naixement, dades bloquejades, gestionar usuaris i rols), quan l'administrador la vol canviar des de l'editor, llavors no hi ha cap control per fer-ho i una petició directa es rebutja.
- **CA-RP-10** Donat un canvi que dona al rol secretaria un permís sobre diners, quan es desa, llavors es tanquen les sessions d'administració dels comptes amb el rol secretaria.
- **CA-RP-11** Donat un compte que perd l'únic rol que tenia, quan es desa, llavors se'n tanquen les sessions, el compte continua actiu i les activitats on era responsable surten a «sense responsable».
- **CA-RP-12** Donat el rol Departament d'Història, quan obre el dashboard, llavors veu les xifres econòmiques agregades però cap nom, document, data de naixement ni IBAN, i cap enllaç a una pantalla de gestió fora de conferències.
- **CA-RP-13** Donat la configuració inicial, quan es carrega en una base de dades buida, llavors cada cel·la de la [matriu](#rols-i-permisos-059-matriu) té una prova que en comprova el «sí» i el «no» (checklist B4).
- **CA-RP-14** Donat un segon compte al qual s'assigna el rol tresorer, quan es mostra el resum, llavors hi surt l'avís d'un sol tresorer i el canvi es pot desar.

**Tasques**
| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan |
|---|---|---|---|---|---|
| T-RP-01 | Catàleg de permisos al codi, `Role`, `RolePermission`, `AccountRole`, motor de comprovació (rol, objecte, camps; unió; abast tancat; regles protegides) i rols a cada entrada del registre | M | `apps/core/permissions.py`, `apps/core/roles.py`, migració | T-M01-06, T-M01-10 | CA-RP-01, 02, 03, 08 i 09; prova de la llista de rutes sense sessió (RN-40). **Feta** (01/11/2026); els «rols a cada entrada del registre» (RN-RP-15), amb la T-M01-07 (02/11/2026) |
| T-RP-02 | Assignar i retirar rols als comptes d'administrador: pantalla, sessions, responsables orfes, administrador operatiu i avís d'un sol tresorer | S | `apps/core/views/roles.py`, plantilles | T-RP-01 | CA-RP-06, 11 i 14. **Feta en part** (01/11/2026): serveis d'assignar i retirar rols, administrador operatiu, autodesactivació (RN-RP-20), restabliment del TOTP amb l'excepció d'emergència (RN-RP-18) i tancament de sessions, amb proves de CA-RP-06, 11, 14, 15 i 16. Les entrades al registre, fetes amb la T-M01-07 (02/11/2026). **Queda:** la pantalla, els correus (T-M01-10) i els responsables orfes (RN-RP-12, quan existeixi el 02) |
| T-RP-03 | Editor de permisos: TOTP en desar, nota, resum de canvis i d'afectats, coherència, versions, correu, tancament de sessions quan s'amplia l'accés i «tornar a la configuració inicial» | M | `apps/core/views/permission_matrix.py`, `apps/core/services/permission_matrix.py`, plantilles | T-RP-01, T-RP-02 | CA-RP-04, 05, 07 i 10 |
| T-RP-04 | Configuració inicial com a migració de dades i proves per cel·la que es generen des de la matriu | S | migració de dades, `tests/permissions/` | T-RP-01 | CA-RP-13; proves en verd. **Feta per a la 00 i el 01** (01/11/2026): `core/0003`, versió 1 de la matriu i una prova per cel·la generada des del catàleg |
| T-RP-05 | `settings.edit.<clau>` en lloc d'`editor_roles` a la peça d'ajustos (RN-RP-17) | XS | `apps/core/business_settings.py` | T-RP-01, T-AJ-01 | CA-AJ-02 continua passant amb els permisos del catàleg |

Les tasques de cada mòdul que declaren els seus permisos al catàleg són a les addendes. El dashboard (08) aplicarà RN-RP-16 quan s'escrigui.

<a id="rols-i-permisos-059-matriu"></a>
## Configuració inicial de la matriu

Font: taula «Què pot fer cada rol» del responsable del projecte (30/10/2026), separada en permisos concrets. Les **cel·les [A validar]** que la taula no cobreix prenen el supòsit per defecte del mòdul; si no n'hi ha, «—»; si amb «—» l'acció es quedaria sense ningú, la té l'administrador. Totes es poden canviar des de l'editor, excepte les que porten **Protegit**.

**Llegenda.** **Sí**; **Les seves** (instructor: sessions on fa classe; responsable de cursos i sortides: activitats de què és responsable); **Cons.** (només veure); **—** (no). **Columnes:** Instr. = Instructor; Secr. = Secretaria; RCS = Resp. cursos i sortides; RM = Resp. material; Tres. = Tresorer; DH = Dept. d'Història; Admin. = Administrador; Pres. = President. A la columna «Canvi», «+» vol dir que el rol guanya el permís respecte del pla i «−» que el perd.

**Fora de la matriu (no editables):**
- Les **accions pròpies** es fan amb el compte personal i no són permisos de rol. Per exemple: P12 a P16, A1 a A3, B1, B2, AC1 a AC4, MT1, MT2, MG10, LC1 i el «Propi» de LC3.
- Visitant i convidat són fixos (RN-40, [021](decisions/021-persones-no-socies-com-a-convidades.md)).
- El **Responsable de comunicació** i el **Responsable de botiga** comencen sense cap permís.

### 00 Base comuna
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| M2 | Crear i editar perfils d'altres persones i els seus comptes personals | — | Sí | — | — | — | — | Sí | — | — | Les [A validar] passen a — |
| M3 | Crear comptes d'administrador, assignar i retirar rols, desactivar comptes | — | — | — | — | — | — | Sí | — | — | **Protegit** |
| M3b | Modificar els permisos dels rols (editor) | — | — | — | — | — | — | Sí | — | — | Nou; **Protegit** |
| M4 | Restablir la contrasenya o el TOTP d'un altre compte d'administrador | — | — | — | — | — | — | Sí | — | — | **Protegit** |
| M5 | Generar, reenviar i revocar enllaços de convidat | — | — | — | — | — | — | Sí | — | — | Les [A validar] passen a — (B7 continua) |
| M6 | Consultar el registre d'activitat | — | — | — | — | — | — | Sí | — | — | Les [A validar] passen a — |
| M7 | Mantenir la llista de departaments | — | — | — | — | — | — | Sí | — | — | S-M04-09 |
| M8 | Importar les dades de Cluber i desfer-ho | — | — | — | — | — | — | Sí | — | — | — |
| M9 | Importar l'extracte bancari i desfer-ho | — | — | — | — | Sí | — | — | — | — | Admin. [A validar] passa a — |
| M11 | Atendre sol·licituds RGPD d'altres persones | — | — | — | — | — | — | Sí | — | — | S-M01-14 |
| M12 | Publicar versions noves dels textos legals | — | — | — | — | — | — | Sí | — | — | Únic candidat |
| M13 | Consultar dades bloquejades | — | — | — | — | Sí | — | Sí | — | — | **Protegit** (028) |
| M14 | Registrar un cobrament manual | Bloquejat fins a P-12; no surt a l'editor | | | | | | | | | — |

### 01 Socis i carnet
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P2 | Crear una alta presencial | — | Sí | — | — | — | — | Sí | — | — | — |
| P3a | Consultar sol·licituds d'alta, de canvi de tipus i de baixa | — | Sí | — | — | Sí | — | Sí | Sí | — | Nou (requisit de P3 i P7) |
| P3 | Aprovar o rebutjar altes | — | Sí | — | — | Sí | — | Sí | Sí | — | + Tres., + Pres. |
| P4 | Llistat i fitxa de socis | — | Sí | — | — | Cons. (dades mínimes) | — | Sí | — | — | Junta [A validar] passa a — |
| P5 | Editar dades d'un soci (inclòs document i número) | — | Sí | — | — | — | — | Sí | — | — | Demana P4 (RN-RP-21) |
| P6 | Corregir la data d'alta | — | Sí | — | — | — | — | Sí | — | — | Demana P4 (RN-RP-21) |
| P7 | Resoldre canvis de tipus i baixes | — | Sí | — | — | Sí | — | Sí | Sí | — | + Tres., + Pres. |
| P8 | Generar quotes anuals | — | — | — | — | Sí | — | Sí | — | — | — |
| P9 | Marcar i desmarcar impagat | — | — | — | — | Sí | — | — | — | — | Admin. [A validar] passa a — |
| P10 | Veure l'estat de quotes de tots els socis | — | Cons. | — | — | Sí | — | Sí | — | — | — |
| P11 | Exportar el llistat de socis | — | Sí | — | — | — | — | Sí | — | — | Tres. [A validar] passa a — |
| P17 | Atendre sol·licituds RGPD d'altres | — | — | — | — | — | — | Sí | — | — | S-M01-14 |
| P18 | Importació de Cluber i desfer | — | — | — | — | — | — | Sí | — | — | — |
| P19 | Registre mínim de llicència (còpia de lectura, 052) | — | Sí | Cons. | — | Cons. | — | Sí | — | — | — |
| P20 | Consultar el registre d'activitat dels socis | — | — | — | — | — | — | Sí | — | — | Secr. [A validar] passa a — |
| C1 | Camp: data de naixement | — | Sí | — | — | — | — | Sí | — | — | **Protegit** (058); la resta veu «major», «menor» o «edat desconeguda» |
| C2 | Camps: document d'identitat, adreça i consentiments d'altres | — | Sí | — | — | — | — | Sí | — | — | El tresorer aprova sense veure'ls (D-04) |

### 04 Tresoreria
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Veure comptes, saldos i moviments | — | — | — | — | Sí | — | Sí | — | — | Junta [A validar] passa a — |
| T2 | Crear i desactivar comptes | — | — | — | — | Sí | — | Sí | — | — | — |
| T3 | Mantenir departaments i centres de cost | — | — | — | — | — | — | Sí | — | — | S-M04-09 |
| T4 | Conciliar i desfer una conciliació | — | — | — | — | Sí | — | — | — | — | S-M04-09 |
| T5 | Anul·lar un moviment amb motiu | — | — | — | — | Sí | — | Sí | — | — | — |
| T6 | Registrar un traspàs | — | — | — | — | Sí | — | Sí | — | — | — |
| T7 | Registrar un arqueig | — | — | — | — | Sí | — | Sí | — | — | — |
| T8 | Excloure una línia de l'extracte | — | — | — | — | Sí | — | — | — | — | — |
| T9 | Exportar moviments en CSV | — | — | — | — | Sí | — | Sí | — | — | — |
| T10 | Veure la llista «a revisar» | — | — | — | — | Sí | — | Sí | — | — | — |
| T11 | Veure l'estat de les quotes sense imports de tresoreria | — | Cons. | — | — | Sí | — | Sí | — | — | — |

### 05a Mètode de pagament i mandats
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A4 | Veure mètodes i mandats de tots els socis (IBAN emmascarat) | — | Cons. («té mètode: sí o no») | — | — | Sí | — | Sí | — | — | S-M05a-13 |
| A5 | Enviar la campanya i els recordatoris | — | — | — | — | Sí | — | Sí | — | — | — |
| A6 | Revocar un mandat a petició escrita, amb motiu | — | — | — | — | Sí | — | Sí | — | — | — |
| A7 | Configurar el proveïdor (les claus, per variables d'entorn) | — | — | — | — | — | — | Sí | — | — | — |
| A8 | Rotar la clau de xifratge (amb informàtica) | — | — | — | — | — | — | Sí | — | — | — |
| A9 | Veure l'IBAN complet | — | — | — | — | — | — | — | — | — | **Protegit** (044): ningú |

### 05b Cobraments
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B3 | Generar remeses, descarregar el fitxer i marcar-lo enviat | — | — | — | — | Sí | — | — | — | — | **Protegit** (fitxer amb IBAN, 044) |
| B4 | Registrar retornats i decidir el reintent | — | — | — | — | Sí | — | — | — | — | — |
| B5 | Fer devolucions | — | — | — | — | Sí | — | — | — | — | Admin. [A validar] passa a — (D-10) |
| B6 | Veure tots els pagaments, en curs, fallits i «a revisar» | — | — | — | — | Sí | — | Sí | — | — | RCS [A validar] passa a — |
| B7 | Reenviar l'alternativa de pagament o l'enllaç de convidat | — | Sí (quotes) | — | — | Sí | — | Sí | — | — | S-M05b-13 |
| B8 | Passar al nivell 2 | — | — | — | — | — | — | Sí, amb l'autorització escrita de la junta | — | — | **Protegit** (025) |

### 02 Activitats (cursos i sortides)
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AC5 | Inscriure presencialment una altra persona | — | — | Sí | — | Sí | — | Sí | Sí | — | + Tres., + Pres.; Secr. — (S-M02-16) |
| AC6 | Catàleg de cursos i especialitats, tipus, subtipus, projectes i preus | — | — | Sí | — | Sí | — | Sí | Sí | — | Tres. Cons. → Sí; + Pres.; Junta [A validar] passa a — |
| AC7 | Crear, editar, publicar, cancel·lar i duplicar activitats | — | — | Sí | — | Sí | — | Sí | Sí | — | + Tres., + Pres. |
| AC8 | Llista de participants amb requisits | Les seves | — | Sí | Cons. | Sí | — | Sí | Sí | — | Tres. Cons. → Sí; + Pres.; RM la conserva per assignar (D-06) |
| AC9 | Passar llista i registrar incidències | Les seves | — | Sí | — | — | — | Sí | Sí | — | + Pres. |
| AC10a | Avaluar pràctiques | Les seves | — | — | — | — | — | — | — | — | Només «les seves sessions» (RN-RP-04) |
| AC10b | Proposar reforç | Les seves | — | — | — | — | — | — | — | — | Només «les seves sessions»; RCS [A validar] passa a — |
| AC11 | Confirmar o rebutjar (programar) reforç | — | — | Sí | — | — | — | Sí | Sí | — | + Pres. |
| AC12 | Registrar apte o no apte | Les seves | — | — | — | — | — | — | — | — | Només «les seves sessions» (RN-RP-04) |
| AC13 | Emetre el certificat | — | — | Sí | — | — | — | Sí | Sí | — | + Pres.; Instr. [A validar] passa a — |
| AC14 | Resultats ambientals i fitxa de projecte | — | — | Sí | — | — | — | Sí | Sí | Cons. | + Pres.; Resp. comunicació [A validar] passa a — |
| AC15 | Missatge als inscrits | — | — | Sí | — | Sí | — | Sí | Sí | — | + Tres., + Pres.; les [A validar] passen a — |
| AC16 | Gestionar la llista d'espera a mà | — | — | Sí | — | Sí | — | Sí | Sí | — | + Tres., + Pres. |
| AC17 | Proposar una devolució per cancel·lació | — | — | Sí | — | Sí | — | Sí | Sí | — | + Tres., + Pres. |
| AC18 | Fer la devolució (B5) | — | — | — | — | Sí | — | — | — | — | — |
| AC19 | Veure els imports cobrats d'una activitat | — | — | Cons. (totes, S-M02-18) | — | Sí | — | Sí | — | — | Junta [A validar] passa a — |
| AC20 | Informes operatius | Les seves | — | Sí | Cons. | Sí | — | Sí | Sí | Cons. | Tres. Cons. → Sí; + Pres. |
| C3 | Camps de l'alumne per a l'instructor: nom, titulació, llicència sí o no, assistència i avaluacions; sense document, adreça, correu, telèfon ni pagaments | Les seves | | | | | | | | | S-M02-17; abast base (**Protegit**) |

### 11 Conferències i contingut històric (mòdul pendent)
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CF1 | Crear, duplicar i gestionar conferències i contingut històric | — | — | Sí | — | Sí | Sí | Sí | Sí | — | + RCS, + Tres., + Pres. |
| CF2 | Passar llista i registrar resultats de conferències | — | — | Sí | — | — | Sí | Sí | Sí | — | + Pres. |

El Departament d'Història continua sense accés a la resta de la gestió (RN-44), excepte el dashboard en lectura (RN-RP-16).

### 03 Material
«Gestionar inventari i assignar material» (fila de la taula) = MT3 a MT7, MT9 a MT11 i el lloguer puntual. No inclou les tarifes (MT8, fila de preus), el marge (MT12) ni la càrrega inicial (MT13).

| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MT3 | Mantenir tipus i inventari; donar de baixa una peça | — | — | Sí | Sí | Sí | — | Sí | Sí | — | + RCS, + Tres., + Pres. |
| MT4 | Veure l'stock | Cons. | — | Sí | Sí | Sí | — | Sí | Sí | Cons. | + Instr. (cons.); RCS i Tres. Cons. → Sí; + Pres. |
| MT5 | Material típic | — | — | Sí | Sí | Sí | — | Sí | Sí | — | + Tres., + Pres. |
| MT6 | Assignar, marcar llogat, lliurar i retornar | Les seves | — | Sí | Sí | Sí | — | Sí | Sí | — | + Instr., + RCS (S-M03-10 deia no), + Tres., + Pres. |
| MT6b | **Lloguer puntual a un centre:** qui ha agafat què i **cost del centre** | Les seves | — | Sí | Sí | Sí | — | Sí | Sí | — | Nou |
| MT7 | Veure el material dels participants | Les seves | — | Sí | Sí | Sí | — | Sí | Sí | — | + Tres., + Pres. |
| MT8 | Centres de busseig i tarifes (preu per a l'alumne) | — | — | Cons. | Sí | Sí | — | Sí | Sí | — | Tres. Cons. → Sí; + Pres.; Junta [A validar] passa a — |
| MT9 | Llista de lloguer: generar, exportar i marcar enviada | Les seves | — | Sí | Sí | Sí | — | Sí | Sí | — | + Instr., + Tres., + Pres. |
| MT10 | Quantitats reals després de l'activitat | Les seves | — | Sí | Sí | Sí | — | Sí | Sí | — | + Instr., + RCS, + Tres., + Pres. |
| MT11 | Revisions | — | — | Sí | Sí | Sí | — | Sí | Sí | — | + RCS, + Tres., + Pres. |
| MT12 | Cost per participant i per activitat; **marge dels lloguers** | — | — | Les seves | Sí | Sí | — | Sí | Sí | Cons. | RCS Cons. → les seves; + Pres. |
| C4 | Camp: preu per a l'alumne del material llogat | Les seves | — | Sí | Sí | Sí | — | Sí | Sí | — | L'instructor no veu el marge (MT12) |
| MT13 | Càrrega inicial de l'inventari | — | — | — | Sí | — | — | Sí | — | — | — |

En un lloguer puntual, qui el registra escriu el **cost del centre**. El preu per a l'alumne és el de la tarifa del centre (MT8). Si el centre no té tarifa per a aquell equip, el lloguer queda «sense preu per a l'alumne» fins que el responsable de material el posa a la tarifa [A validar: responsable de material]. **Punt feble:** l'instructor no veu el marge, però el pot calcular amb el cost que escriu i el preu de l'alumne ([059](decisions/059-rols-i-permisos-editables.md)).

### 09 Marge, despeses, ajuts i facturació
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MG1 | Registrar una despesa amb factura | — | — | Les seves | — | Sí | — | Sí | Sí | — | + Pres.; RM [A validar] passa a — (taula: no) |
| MG2 | Pagar una despesa, adjuntar-ne el comprovant i anul·lar-la | — | — | — | — | Sí | — | Sí | — | — | — |
| MG3 | Repartir una despesa entre activitats | — | — | — | — | Sí | — | Sí | — | — | — |
| MG4 | Registrar ajuts, patrocinis i donatius | — | — | — | — | Sí | — | Sí | — | — | — |
| MG5 | Costos previstos d'una activitat | — | — | Les seves | — | Sí | — | Sí | — | — | — |
| MG6 | Veure el marge d'una activitat | — | — | Les seves | — | Sí | — | Sí | Sí | Cons. | RCS: les seves; + Pres. |
| MG7 | Tancar econòmicament una activitat | — | — | — | — | Sí | — | Sí | — | — | — |
| MG8 | Informes per departament, subtipus i projecte | — | — | — | — | Sí | — | Sí | — | Cons. | DH [A validar] passa a — |
| MG9 | Emetre factures i rectificatives | — | — | — | — | Sí | — | Sí | — | — | — |
| MG11 | Tancar un període | — | — | — | — | Sí | — | Sí | — | — | — |
| MG12 | Reobrir un període | — | — | — | — | — | — | Sí | — | — | **Protegit** |
| MG13 | Hores de voluntariat | — | — | — | — | Sí | — | Sí | — | — | Junta [A validar] passa a — |
| MG14 | Categories, proveïdors i llindar de marge baix | — | — | — | — | Sí | — | Sí | — | — | — |
| C5 | Obrir documents de justificació | — | — | — | — | Sí | — | — | — | Sí | **Protegit** (051) |

**Ajuts (AJ1 a AJ13):** igual que [M09-ajuts-4](#M09-ajuts-4-rols). Les cel·les «Sí, si n'és responsable» de la Junta tenen l'abast «les que en sigui responsable». AJ12 és **Protegit** (051). Cap altre rol hi té accés.

### 06 Llicències
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LC3 | «Ja en tinc una» (registrar-la per a una altra persona) | — | Sí | Sí | — | Sí | — | Sí | Sí | — | + RCS, + Tres., + Pres. |
| LC4 | Llistat, filtres i venciments | — | Sí | Sí | — | Sí | — | Sí | Sí | — | + RCS; Tres. Cons. → Sí; + Pres.; Junta [A validar] passa a — |
| LC5 | Exportar per a la federació; marcar tramitada i vigent | — | Sí | — | — | — | — | Sí | Sí | — | + Pres. |
| LC6 | Cancel·lar una llicència | — | Sí | — | — | — | — | Sí | Sí | — | + Pres. |
| LC7 | Fer la devolució d'una llicència cancel·lada | — | — | — | — | Sí | — | — | — | — | — |
| LC8 | Tipus, preus i recàrrec | — | — | — | — | Sí | — | Sí | Sí | Cons. | + Pres. |
| LC9 | Activar l'opció de llicència per a no socis | — | — | — | — | — | — | Sí | — | — | — |
| LC10 | Veure si la llicència d'un participant és vigent | Les seves (només sí o no) | Sí | Les seves | — | — | — | Sí | Sí | — | + Pres. |
| LC11 | Passar els registres del 01 al 06 | — | — | — | — | — | — | Sí | — | — | — |
| C6 | Camps: número federatiu, categoria i venciment | — | Sí | Sí | — | Sí | — | Sí | Sí | — | Els veu qui té LC4; l'instructor continua amb «sí o no» (RN-M06-22) |

### 08 Dashboard (mòdul pendent)
| # | Permís | Instr. | Secr. | RCS | RM | Tres. | DH | Admin. | Pres. | Junta | Canvi |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DB1 | Veure el dashboard sencer, amb les xifres econòmiques | — | Sí | Sí | Sí | Sí | Sí | Sí | Sí | — | Abans: parcial per a Secr., RCS, RM i DH |
| DB2 | Fer accions des del dashboard (si n'hi ha) | — | — | Sí | — | Sí | — | Sí | Sí | — | «Complet» de la taula |

Sempre amb RN-RP-16: cap dada personal que el rol no pugui veure per un altre permís.

### Ajustos (055)
La configuració inicial dels permisos `settings.edit.<clau>` és la columna «Qui el canvia» de l'[apèndix de valors configurables](#valors-configurables), amb tres canvis:
- **VC-20** (catàleg i preus de cursos i especialitats): RCS, tresorer, administrador i President.
- **VC-27** (tipus de material, centres i tarifes): responsable de material, tresorer, administrador i President.
- **VC-38 i VC-45** (tipus, preus i recàrrec de llicències): tresorer, administrador i President.

Els valors que diuen «per decisió de la junta» els continua canviant l'administrador. Tot canvi d'un import continua avisant el tresorer i la junta (RN-AJ-04).

---

<a id="ajustos-060"></a>
# Apèndix — Ajustos de l'auditoria (decisió 060)

Acceptada el 31/10/2026 ([060](decisions/060-ajustos-de-l-auditoria-del-pla.md)). Recull el que no és de cap mòdul concret: les peces de la 00 que no tenien tasca, les precisions a la peça de rols i permisos i la lectura de les tasques substituïdes. Les addendes dels mòduls són a [01](#M01-addenda-060), [04](#M04-addenda-060), [05a](#M05a-addenda-060), [05b](#M05b-addenda-060), [06](#M06-addenda-060), [02](#M02-addenda-060), [03](#M03-addenda-060) i [09](#M09-addenda-060). La spec 00 no s'edita.

<a id="ajustos-060-peces-00"></a>
## Peces de la 00 amb tasca pròpia

El pla les esmentava ([M01-2](#M01-2-dependencies)) però no tenien cap tasca, mentre que altres tasques ja en depenien. La T-M00-05 l'afegeix la [063](decisions/063-validacions-de-la-revisio-de-la-t-m01-02.md) el 03/11/2026, pel mateix motiu: RN-M05a-12 en declarava el servei com a peça de la 00 sense cap tasca. Depèn només de les parts fetes de la T-M01-05 (TOTP i bloqueig per intents de V-01) i de la T-M01-07: precisió acceptada pel responsable del projecte el 03/11/2026. La T-M00-06 l'afegeix la [066](decisions/066-revisio-de-la-t-m01-05-reenviament-limit-d-origen-i-tasques.md) el 04/11/2026: V-07 (límit diari dels correus) no tenia cap tasca.

| ID | Tasca | Mida | Fitxers | Depèn de | Fet quan | La necessiten |
|---|---|---|---|---|---|---|
| T-M00-01 | Importació de l'extracte bancari en CSV: previsualització, validació, línies ja importades, confirmació i desfer (HU-21; RN-92 a RN-101 de la spec 00) | M | `apps/core/imports/bank_statement.py`, vistes | T-M01-07, T-M01-24 (lot i línia d'importació), T-RP-01 | CA-21.1 a CA-21.5 de la spec 00 | T-M04-11 (fase 1) |
| T-M00-02 | Enllaços de convidat: generar, enviar, caducar, reenviar (l'anterior deixa de funcionar), revocar i limitar els intents (HU-02, V-02, RN-30 a RN-33) | M | `apps/core/guest_links.py`, vistes | T-M01-05, T-M01-09, T-M01-10, T-RP-01 | CA-02.1 a CA-02.7 de la spec 00 | T-M05b-08, T-M06-07, T-M02-14 |
| T-M00-03 | Comptes d'emergència (com a mínim dos, amb TOTP) i codis de recuperació fora de línia; avís quan n'hi ha menys de dos; restabliment del TOTP de l'últim administrador ([RN-RP-18](#ajustos-060-rols)) | M | `apps/accounts/emergency.py`, `apps/accounts/recovery.py` | T-M01-05, T-RP-02 | CA-09.x i CA-10.1, 10.2 de la spec 00; CA-RP-15 | Nivell 1 de producció |
| T-M00-04 | Consulta de dades bloquejades (M13, protegit; [028](decisions/028-esborrat-rgpd-i-registre-d-activitat.md)): només el tresorer i l'administrador, cada consulta amb motiu al registre, i les dades bloquejades no surten enlloc més | S | `apps/core/privacy.py`, vistes | T-M01-22, T-RP-01 | CA-19.3 de la spec 00; prova que cap llistat, cerca ni exportació mostra una dada bloquejada | Nivell 1 de producció |
| T-M00-05 | Servei de reautenticació `accounts.require_recent_auth(account, minutes)`: torna a demanar la contrasenya, i el TOTP si el compte en té. `minutes=0` vol dir sempre, a la mateixa petició ([RN-M01-57](#M01-addenda-063)); `minutes=15`, per al 05a (RN-M05a-12). Els errors compten per al bloqueig de V-01 i queden al registre d'activitat | S | `apps/accounts/reauth.py` | Només les parts fetes de la T-M01-05 (TOTP i bloqueig per intents de V-01) i la T-M01-07 | CA-M01-46; els criteris del 05a quan es construeixi | T-M01-22, T-M05a-09 |
| T-M00-06 | Reserva, prioritat i límit diari dels correus (HU-22; RN-A3, RN-A4, RN-A6 i RN-A8; V-07): comptador diari, reserva per als transaccionals, estat «ajornat» al 100 % i sortida l'endemà per l'ordre de V-07, prioritat declarada per a cada plantilla, un sol avís al 80 % i un reintent no compta dues vegades. Fora d'abast: tandes i consentiment del butlletí (RN-A5, RN-A9) i avisos de Brevo (RN-A10) | M | `apps/core/mail.py`, `models.py`, `tasks.py`, migració | T-M01-10 | CA-A2 (part transaccional), CA-A3, CA-A4, CA-A5 i CA-A9 de la spec 00; qui rep l'avís: Q-26 [A validar] | Nivell 1 de producció |

<a id="ajustos-060-rols"></a>
## Rols i permisos (precisa la 059)

**Ordre de les tasques**
- La T-RP-01 i la T-RP-04 es fan **just després de la T-M01-06 i abans de cap vista**. La T-RP-04 carrega la configuració inicial de la 00 i del 01. Cada mòdul hi afegeix la seva part quan es construeix.
- La **T-AJ-01 depèn de la T-RP-01** i fa servir directament el permís del catàleg `settings.edit.<clau>`: no hi ha camp `editor_roles`. Per això la **T-RP-05 queda retirada**, i CA-AJ-02 es comprova amb els permisos del catàleg.
- Les tasques «declarar els permisos» de cada mòdul (T-M01-37, T-M04-21, T-M05a-25, T-M05b-25, T-M06-25, T-M02-33, T-M03-23 i T-M09-30) no s'esperen al final: cada vista declara i comprova el seu permís quan es fa. Aquestes tasques queden com a revisió final de la cobertura per cel·la (CA-RP-13).
- La **T-RP-03** (editor de permisos) **surt del camí crític**. No és condició del nivell 1 ni del 2: es construeix en acabar el 05b (després de la T-M05b-19). Fins llavors, la matriu només canvia amb una migració de dades revisada, que deixa la seva entrada al registre (RN-RP-08). Els criteris CA-RP-04, 05, 07 i 10 van amb la T-RP-03. La T-RP-02 (assignar i retirar rols) continua al camí crític.

| ID | Regla |
|---|---|
| RN-RP-18 | **Restabliment del TOTP de l'últim administrador.** Un compte d'emergència pot restablir el TOTP de l'últim administrador operatiu. És l'única excepció a RN-RP-13. Cal una nota obligatòria. Queda una entrada immutable al registre d'activitat (compte d'emergència, compte afectat, nota) i s'envia un correu a la junta i a tots els comptes amb el rol administrador. El compte restablert torna a ser operatiu quan dona d'alta el TOTP nou. Mentrestant, surt l'avís permanent de RN-RP-13 |
| RN-RP-19 | **Nom del permís d'ajustos:** `settings.edit.<clau>` (RN-RP-17). On la [059](decisions/059-rols-i-permisos-editables.md) diu `settings.edit_<mòdul>`, val `settings.edit.<clau>` |
| RN-RP-20 | **Un administrador es desactiva a si mateix** (precisió aprovada el 31/10/2026). Només es permet si queda almenys un altre administrador operatiu (RN-RP-13). En confirmar-ho, **es tanquen totes les sessions actives del seu compte d'administrador**, també la de la petició en curs, que acaba amb la sortida de l'administració. El canvi queda al registre d'activitat i s'avisa per correu els altres comptes amb el rol administrador. El compte personal de la mateixa persona no es toca. La feina és a la T-RP-02 |
| RN-RP-21 | **Editar demana consultar** (precisió aprovada el 02/11/2026). P5 (editar dades d'un soci) i P6 (corregir la data d'alta) demanen P4 (llistat i fitxa de socis) amb qualsevol abast. Al catàleg és `requires` i s'aplica RN-RP-03: un rol no pot tenir P5 o P6 sense P4. La configuració inicial ja ho compleix |

**Precisions de la T-RP-01 aprovades el 02/11/2026**
- **P10:** el «Cons.» de la secretaria és «Sí», perquè P10 ja és un permís de consulta.
- **M14** (registrar un cobrament manual) no és al catàleg fins que es resolgui P-12.
- **Comptes d'emergència:** tenen el rol administrador, però no compten com a administrador operatiu (RN-RP-13). Per això poden fer servir l'excepció de RN-RP-18.
- **Bloqueig temporal** (V-01): no és un estat del compte, sinó una data de final (`locked_until`). Mentre dura, el compte no compta com a operatiu (RN-RP-13), i torna a comptar-hi sol quan s'acaba.

- **CA-RP-15** Donat un sol administrador operatiu, quan un compte d'emergència en restableix el TOTP amb una nota, llavors s'accepta, queda l'entrada al registre, la junta i els administradors reben el correu i surt l'avís permanent fins que l'administrador dona d'alta el TOTP nou. Quan ho intenta un compte que no és d'emergència, es continua rebutjant (CA-RP-06).
- **CA-RP-16** Donat dos administradors operatius, A amb sessions obertes en dos dispositius, quan A desactiva el seu propi compte d'administrador, llavors totes dues sessions queden tancades, la petició següent de qualsevol de les dues va a l'entrada, el registre guarda el canvi i B rep el correu. Amb un sol administrador operatiu, es rebutja (CA-RP-06).

<a id="ajustos-060-lectura"></a>
## Lectura de les tasques substituïdes

Una línia per cada tasca on el text aprovat ja no és el que cal construir. Les files aprovades no s'editen: val el que diu aquesta taula.

| Tasca | Què val ara | Font |
|---|---|---|
| T-M01-06 | Rols i permisos de la 059 amb la T-RP-01 just després; no «8 rols de la 00 + P-04» (P-04 està resolta) | 059, 060 |
| T-M01-13 a T-M01-22, T-M01-33 | També depenen de la T-RP-01 | 060 |
| T-M01-31 | Es fa en construir el 06 | 060 |
| T-M04-11 | També depèn de la T-M00-01 | 060 |
| T-M05b-08, T-M06-07, T-M02-14 | Depenen de la T-M00-02, no d'«enllaços de convidat de la 00» | 060 |
| T-M05b-23 | Congelada fins a la validació del punt 11 de la 058 | 060 |
| T-M06-03 | Feta quan CA-M06-28 i CA-M06-02; inclou la T-M06-22 | 058, 060 |
| T-M02-30 | La T-M06-13 ja existeix; RN-M02-26 sense el mode provisional | 060 |
| T-AJ-01 | Depèn de la T-RP-01; sense `editor_roles` | 060 |
| T-RP-03 | Després de la T-M05b-19; fora del camí crític | 060 |
| T-RP-02 | També RN-RP-20 i CA-RP-16 (autodesactivació) | 060 |
| T-RP-05 | Retirada | 060 |
| T-M01-37, T-M04-21, T-M05a-25, T-M05b-25, T-M06-25, T-M02-33, T-M03-23, T-M09-30 | Revisió final de la cobertura per cel·la | 060 |
| T-M01-09 | CA-16.1 i CA-15.8 de la spec 00: el departament inicial és «General», no «General / Quotes de socis». Els centres de cost («Quotes de socis», «Llicències», «Ajustos de caixa») els afegeix la T-M04-02 (CA-T14.1). Els camps del pagament són del proveïdor, sense el nom de Stripe (`provider_reference`, `provider_status`; 043) | Precisió aprovada el 02/11/2026 |
| T-M01-22 | També depèn de la T-M00-05 i cobreix CA-M01-46 | 063 |
| T-M05a-09 | També depèn de la T-M00-05 (la reautenticació de RN-M05a-12) | 063 |
| T-M01-22 | També anonimitza `request_reason` i `resolution_reason` de `MemberRequest` | 064 |
| T-M01-11 | També CA-M01-47: `MemberRequest` té `request_reason` i `resolution_reason` en lloc de `reason`, amb les dues restriccions | 064 |
| T-M01-05 | També RN-M01-58 a RN-M01-61 i CA-M01-48 a CA-M01-55: límits dels enllaços del correu, comptes pendents i reenviament, revalidació TOTP i motiu en els restabliments, i avís sense adreça | 065 |
| T-RP-02, T-M00-03 | La revalidació TOTP i el motiu obligatori de RN-M01-60 també valen per a l'excepció de RN-RP-18 (ja feta a la T-M01-05); els avisos a la junta i als administradors continuen en aquestes tasques | 065 |
| T-M01-05 | RN-M01-58 i RN-M01-59 amb el text de la 066: les limitades per destinatari compten per a l'origen i el reenviament no és d'un sol ús | 066 |
| T-M01-07b, T-M01-13 a T-M01-22 | També depenen de la T-M01-38 | 066 |
| T-M01-38 | També el recorregut visible després de reenviar la verificació: confirmació, manera de tornar-lo a demanar i navegació sense dependre del botó «Enrere» sobre un POST (trobat en tancar la T-M01-05; no autoritza cap canvi d'interfície fora de la T-M01-38) | Aprovació de la T-M01-05, 04/11/2026 |
| T-M01-11 | També el model `AnnualFee`, **només el model**: camps de [M01-6](#M01-6-entitats), sobre `Charge`, sense esborrar (RN-M01-51) i únic `(member, period, kind)`. La generació de quotes i el venciment (P-29) continuen a la T-M01-14 i la T-M01-18. `HistoricFee` no hi entra | Aprovació del pla de la T-M01-11, 04/11/2026 |
| T-M01-11 | `LicenceRecord.expires_on` admet buit des d'ara ([addenda de la 058](#M01-addenda-058)), amb `expires_on ≥ issued_on` només quan hi ha data. La T-M01-34 conserva `members.licence_record`, la fitxa i CA-M01-40, i no queda feta per aquest canvi de model | Aprovació del pla de la T-M01-11, 04/11/2026 |
| T-M01-11 | Interpretacions del model aprovades pel responsable del projecte (no són regles de negoci noves): a `MemberRequest`, `requested_type` obligatori per a `join` i `change_type` i buit per a `leave`, `member` obligatori per a `change_type` i `leave`, la persona de la sol·licitud és la del soci quan n'hi ha, i `created_at`; a `MemberCard`, un carnet revocat té data i motiu i un de no revocat no en té, i `token_hash` té el format d'un SHA-256 en hexadecimal; `licence_type` és text lliure de fins a 100 caràcters, sense catàleg. Els motius obligatoris rebutgen també els valors fets només d'espais | Aprovació del pla de la T-M01-11, 04/11/2026 |
| T-M01-24 | També crea `ImportBatch` (lot d'importació de la 00) i afegeix, amb la seva migració, els camps `import_batch` de `Member` i `LicenceRecord` (i el de `HistoricFee`, quan es creï), que la T-M01-11 no construeix | Aprovació del pla de la T-M01-11, 04/11/2026 |
| T-M01-22 | També anonimitza els altres textos lliures del M01 que poden contenir dades personals: `MemberStatusChange.reason`, amb una excepció acotada als disparadors que només hi deixen afegir files (com RN-89 al registre d'activitat), `MemberCard.revoked_reason` i les referències a la persona dins de `MemberRequest.duplicate_warning`. Les relacions amb el compte (`actor_account`, `resolved_by`) no es toquen: el compte es desactiva i la persona s'anonimitza | Aprovació del pla de la T-M01-11, 04/11/2026 |
| T-M01-11 | `avatar_seed` (precisió d'abast, no canvi de requisit): segueix M01-6, **llavor aleatòria** generada amb una font aleatòria segura del sistema i mai a partir de dades personals, fixada en l'alta i que no canvia mai (disparador a la base de dades). A RN-M01-30, «es genera a partir del nom» vol dir només que l'avatar futur es dibuixarà a partir d'aquesta llavor; corregir el nom no la canvia. Com que no es deriva de cap dada personal, l'anonimització de la T-M01-22 no la toca | Decisió del responsable del projecte, 04/11/2026 |
| T-M01-14, T-M01-17, T-M01-18 | Que el càrrec d'una `AnnualFee` sigui de la mateixa persona que el soci i del tipus «quota» (M01-6) ho garanteix el servei, no la base de dades: una restricció necessitaria columnes duplicades a `AnnualFee` i una restricció nova al `Charge` de la 00. La T-M01-14 crea l'única funció que crea quotes (el càrrec amb `create_charge(member.person, kind="fee", …)` i la quota dins la mateixa transacció), amb proves; la T-M01-17 (suplement) i la T-M01-18 (generació) la reutilitzen | Revisió de la T-M01-11, 04/11/2026, segons la decisió del responsable del projecte (servei si no hi ha cap restricció clara) |
| T-M01-12, T-M01-14, T-M01-17 | **Supòsits pendents** de la T-M01-11, no regles noves: la base de dades no els imposa i cada tasca els ha de confirmar o portar a decisió. (1) T-M01-12: `left_on` només té valor quan l'estat és «baixa» i no és anterior a `joined_on`; la readmissió (P-M01-C, mateix registre) passa de «baixa» a «pendent», una transició que RN-M01-07 no llista («cap altra transició») [A validar: responsable del projecte], i cal decidir si `left_on` es buida en readmetre (la data queda a l'historial). (2) T-M01-14: `member_number` s'assigna en aprovar l'alta, és ≥ 1 i després no queda mai buit; la base de dades admet buit i 0, també per als socis importats (T-M01-24). (3) T-M01-17: una baixa aprovada canvia l'estat i escriu `left_on` a la data efectiva (pas 3 de P-M01-C), no en aprovar-la. La unicitat de les quotes amb anul·lades és a [P-54](decisions/pendents.md) | Revisió de la T-M01-11, 04/11/2026: documentats per indicació del responsable del projecte, no aprovats |
| T-M01-11, T-M01-14, T-M01-24 | `avatar_seed` té el format de `token_hex(32)` (64 caràcters hexadecimals en minúscula), comprovat a la base de dades; el format no demostra que sigui aleatòria. L'únic punt autoritzat per generar-la és el servei d'alta (T-M01-14), amb `new_avatar_seed`. La importació de Cluber (T-M01-24), que segons M01-6 també la dona, ho ha de fer amb aquest mateix servei o funció [A validar: responsable del projecte] | Decisió del responsable del projecte, 04/11/2026 |
| T-M01-14, T-M01-17, T-M01-18 | Cadascuna inclou una prova que intenta crear una `AnnualFee` amb el càrrec d'una altra persona i una altra amb un càrrec que no és del tipus «quota», i comprova que es rebutgen. Fins que aquestes proves passin, la correspondència entre la quota i el càrrec **no està garantida** | Decisió del responsable del projecte, 04/11/2026 |
| T-M01-24 | La llavor dels socis importats de Cluber la genera la mateixa funció que fa servir el servei d'alta (`new_avatar_seed`). Resol el [A validar] de la fila anterior sobre `avatar_seed` | Decisió del responsable del projecte, 04/11/2026 |
| T-M01-12, T-M01-14 | Readmissió amb el text de RN-M01-07 precisat per la [P-55](decisions/pendents.md). La T-M01-12 implementa la transició baixa → pendent; la T-M01-14 l'aplica en aprovar l'alta d'una persona que ja va ser sòcia. **Prova de la T-M01-14 sobre el número:** (a) una readmissió conserva el número del mateix soci i el comptador no avança; (b) assignar a un soci el número d'un altre soci, actiu o de baixa, es rebutja. Les dues proves són separades. Si `left_on` es buida o no, continua obert a la P-55 | Decisió del responsable del projecte, 04/11/2026 |
| T-M01-12 | En readmetre, `left_on` es buida dins la mateixa transacció que l'entrada d'historial de la readmissió; la prova comprova que l'entrada d'historial de la baixa existeix abans de buidar-lo. Resol la fila anterior ([067](decisions/067-readmissio-d-un-antic-soci.md)) | [067](decisions/067-readmissio-d-un-antic-soci.md), 04/11/2026 |
| T-M01-12 | **Interfície i actor.** Serveis autoritzats del mòdul: `mark_unpaid` i `unmark_unpaid` (P9, RN-M01-09). Primitives internes del M01 (prefix `_`, fora del contracte de [M01-8](#M01-8-serveis)): `_change_status`, `_change_type` i `_readmit`. No comproven el permís del rol: les crida el servei autoritzat de cada tasca després de comprovar-lo. `_change_status` no fa actiu ↔ impagat (només amb P9, perquè no s'esquivi) ni baixa → pendent (només `_readmit`). L'actor és un compte o el sistema (`audit.system(origen)`; a l'historial, `actor_account` buit); sense actor, es rebutja (RN-M01-08). El sistema pot fer pendent → actiu (pas 7 de P-M01-A; `on_fee_paid`, que no és d'aquesta tasca), la baixa (pas 3 de P-M01-C i pas 5 de P-M01-F) i el canvi de tipus (pas 4 de P-M01-B); no pot marcar ni desmarcar l'impagat (RN-M01-09, 040) ni readmetre (pas 5a de P-M01-A: ho aprova una persona). **Conflicte d'interès** (S-M01-22, regla protegida per la [059](#M01-addenda-059), sense excepcions): si el compte és de la persona del soci, es rebutja i l'intent es registra **abans** d'obrir la transacció de l'operació. Contracte: cada punt d'entrada fa aquesta comprovació abans d'obrir la seva transacció; si es fa dins d'una transacció exterior que es desfà, el rebuig es manté però l'intent registrat es perd | Aprovació del pla de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-12 | **Dates i `left_on`.** Data efectiva obligatòria, sense valor per defecte; es rebutja si és posterior a la data local del projecte (`TIME_ZONE` = Europe/Madrid, `timezone.localdate()`). No es programen canvis. Acceptar una data passada canvia l'estat actual: no reconstrueix l'historial ni recalcula quotes ni carnets. El servei valida que `left_on` només té valor quan el soci és de baixa; en donar de baixa, la data efectiva no pot ser anterior a `joined_on` i passa a `left_on`; en readmetre, es buida (067). Sense restricció nova a la base de dades. Resol el supòsit (1) de la T-M01-12 de la fila de la revisió de la T-M01-11 | Aprovació del pla de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-12 | **Readmissió** (`_readmit`). Exigeix una sol·licitud d'alta, de la mateixa persona i pendent; el soci de baixa; i que l'últim canvi d'estat de l'historial sigui la baixa amb la data efectiva igual a l'actual `left_on` (no qualsevol baixa antiga). Bloqueja primer el soci i després la sol·licitud, i valida després d'obtenir tots dos bloquejos. Una transacció exterior que es desfà desfà també la readmissió (prova en aquesta tasca). No crea quotes ([P-54](decisions/pendents.md)) | Aprovació del pla de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-12 | **Carnet (D1).** Marcar o desmarcar l'impagat no revoca el carnet ni el modifica: estat i validesa van separats. La part de CA-M01-09 «el carnet passa a "no vàlid"» **no** es comprova a la T-M01-12; la comprova la resposta de validesa de la T-M01-19 i la T-M01-20 | Aprovació del pla de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-12, T-M01-17 | **Limitació actual del model, no regla nova.** La restricció de l'historial de la T-M01-11 (motiu obligatori quan l'estat nou és «impagat» o «baixa») també s'aplica a una entrada de canvi de tipus d'un soci impagat, on l'estat anterior i el nou són el mateix: `_change_type` hi demana motiu. Si un soci de baixa pot canviar de tipus no està decidit; `_change_type` no ho restringeix i ho ha de portar la T-M01-17 | Aprovació del pla de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-14 | Readmissió en aprovar l'alta: en aquest recorregut no bloqueja primer la sol·licitud. Crida `_readmit`, que bloqueja el soci i després la sol·licitud i torna a validar; i, dins la **mateixa transacció**, aprova la sol·licitud i fa la resta d'operacions que li pertoquen. Fa la comprovació del conflicte d'interès abans d'obrir la transacció (fila anterior) | Aprovació del pla de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-19, T-M01-20 | Comproven la part del carnet de CA-M01-09: d'un soci impagat, el carnet no revocat respon «No vàlid» (RN-M01-18, CA-M01-14) | Aprovació del pla de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-24 | Els socis importats de baixa reben una entrada d'historial que permeti comprovar la baixa a `_readmit`, sense inventar dates, actors humans ni motius, i distingible d'una baixa feta per la plataforma. **Buit per resoldre en preparar la importació** [A validar: responsable del projecte]: amb el model actual (1) l'historial no té cap camp de procedència (`actor_account` buit vol dir «sistema»); (2) la restricció de la T-M01-11 exigeix motiu quan l'estat nou és «baixa»; i (3) la data efectiva és obligatòria, i Cluber pot no donar la data de baixa | Aprovació del pla de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-12 | **Data de la readmissió** (precisió de la fila «Dates i `left_on`»). Es rebutja una readmissió amb la data efectiva anterior a la de la baixa actual (`left_on`); la mateixa data s'accepta. Continua el rebuig de les dates futures. Cap altra regla cronològica (per exemple, respecte d'altres entrades de l'historial) sense una decisió nova | Revisió de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-12 | **Compte no actiu.** Un compte que no és actiu (`Account.is_active`: desactivat o pendent, la mateixa garantia que ja fan servir les sessions i el motor de permisos) no pot fer canvis nous amb aquests serveis, tampoc amb les primitives internes. L'estat del compte es torna a llegir de la base de dades dins la transacció del canvi, perquè un objecte carregat abans pot estar desfasat. Les referències històriques al compte (historial i registre) no es toquen. L'actor sistema explícit no hi queda afectat. Cap permís nou | Revisió de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-12, T-M01-14 | **Ordre dels bloquejos amb compte** (implementació de la fila anterior, sense regla nova). Perquè una desactivació no es pugui confirmar entre la comprovació i el canvi, la transacció bloqueja primer la fila del compte que actua (`FOR NO KEY UPDATE`: una desactivació simultània espera, però no les claus foranes cap al compte), després el soci i, en la readmissió, la sol·licitud. L'ordre soci → sol·licitud no canvia. Un compte no actiu es rebutja abans de la comprovació del conflicte d'interès i del permís, sense deixar cap intent registrat (llevat que es desactivi just entre aquesta comprovació i la de dins la transacció, que en tot cas impedeix el canvi) | Revisió de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-14, T-M01-17, T-M01-18, T-M01-22 | **Conflicte d'interès als punts d'entrada.** Cada punt d'entrada que fa servir aquests serveis o primitives amb un compte (aprovar l'alta o la readmissió, resoldre el canvi de tipus o la baixa, les vistes de l'impagat, l'esborrat RGPD) inclou una prova que, quan el compte és de la persona del soci, l'operació falla, el soci i l'historial no canvien i l'intent rebutjat **queda registrat**. El contracte no canvia: la comprovació es fa abans d'obrir la transacció del punt d'entrada, sense connexions separades | Revisió de la T-M01-12 pel responsable del projecte, 04/11/2026 |
| T-M01-24, T-M01-25 | **Fases de la importació de Cluber** (precisió de RN-92, RN-98 i CA-M01-20). (1) *Lectura, validació i resum.* `preview()` llegeix el fitxer en memòria, el valida i en torna el resum; a la base de dades només fa consultes de lectura. No escriu a la base de dades, a la sessió, al disc ni a la cua, i no envia correus. El criteri d'absència d'escriptures de CA-M01-20 té abast sobre `preview()`. (2) *Registre.* El futur punt d'entrada autoritzat que cridi `preview()` deixa una entrada al registre d'activitat per execució, amb el compte, la data, l'empremta SHA-256 del fitxer i els recomptes, sense cap valor del fitxer; en el recorregut complet és l'única escriptura permesa. Si el fitxer es rebutja per una columna d'IBAN, l'entrada només guarda el compte, la data i el motiu, sense l'empremta ni res del contingut. La T-M01-24 no crea cap punt d'entrada només per fer aquest registre. (3) *Lot.* El cicle de vida d'`ImportBatch` continua sent el de la spec 00 (previsualització, confirmat, desfet i rebutjat) fins que una decisió el canviï; `preview()` no el necessita ni en crea cap. (4) *Confirmació i importació final:* T-M01-25 | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24, T-M01-25 | **Llavor i historial.** La T-M01-24 prepara el contracte del fitxer i detecta les dades pendents, sense inventar-les. L'escriptura efectiva dels socis, de la llavor amb `new_avatar_seed` (files de la llavor) i de l'entrada d'historial dels socis importats de baixa (fila de l'aprovació de la T-M01-12, que continua [A validar: responsable del projecte]) és de la T-M01-25. Cap de les dues tasques no inventa dates, actors humans, motius de baixa, estats ni períodes de quotes per complir una restricció: una dada absent surt al resum com a pendent o error, i la procedència i les dates desconegudes de l'historial es resolen amb una decisió explícita abans de la T-M01-25 | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24 | **`ImportBatch` aplaçat dins de la tasca.** La creació d'`ImportBatch` i dels camps `import_batch` (fila de l'aprovació del pla de la T-M01-11) continua dins l'abast de la T-M01-24, però espera que s'aprovi el contracte del lot (cicle de vida, camps i relacions). El lector i la validació es fan abans i no en depenen. També espera el model la comprovació de CA-20.8 a la prova (un lot de Cluber confirmat i no desfet fa rebutjar una prova nova). Mentre quedin aquestes peces, la T-M01-24 no és «Feta» | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Presentació del resum.** No canvia de tasca ni de criteri: que l'administrador «vegi» el resum (CA-M01-20, CA-20.1) queda pendent d'aclarir amb la T-M01-38 i els criteris vigents. La T-M01-24 lliura el servei | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24, T-M01-25 | **Permís.** El recorregut d'importació del M01 s'autoritza amb P18 (`members.cluber_import.run`). M8 (`core.cluber_import.run`) es manté sense canvis. Quan `preview()` o la importació final es connectin a un punt d'entrada (vista o ordre), aquest comprova P18 al servidor abans de llegir el fitxer. `preview()` no comprova permisos perquè no és cap punt d'entrada | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Columna d'IBAN** (precisió de RN-94 i CA-M01-21). Una capçalera és d'IBAN si, després de treure el BOM inicial i els espais dels extrems i passar-la a minúscules, és exactament «iban». No hi ha àlies ni cerca de la subcadena: un àlies nou s'afegeix de manera explícita i justificada. El fitxer es rebutja sencer encara que la columna sigui buida, en llegir la capçalera i abans de processar cap fila de dades. No s'escanegen els valors de les cel·les (risc conegut: un IBAN dins d'una altra columna no es detecta) | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Document sense tipus.** L'exportació no porta el tipus de document. Per detectar possibles coincidències, el número normalitzat es compara amb el de les persones de qualsevol tipus, només amb lectures: cap fusió ni assignació automàtica, i `find_duplicates` no canvia. Una coincidència dona l'advertiment «coincidència sense tipus»; més d'una és una situació ambigua i la fila no queda preparada per importar; un document i un número de soci que apunten a persones diferents són un error. Per a la T-M01-25: el model de persona exigeix el tipus quan hi ha número, de manera que sense el tipus el document no es pot desar | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Perfil CSV inicial**, no una propietat confirmada de l'exportació de Cluber (Q-23): UTF-8 amb BOM opcional; separador «;»; cometes segons el mòdul `csv` de Python; 1 MiB de fitxer; 2.000 registres de dades sense comptar la capçalera; 10.000 caràcters per camp. Cap altra codificació ni cap heurística de format. Capçaleres reconegudes: les de la mostra parcial rebuda el 04/11/2026 (que no substitueix S-M01-16). Requerides: «Nº Soci», «Nom», «Cognoms» i «Document d'Identitat» (número, nom i document de S-M01-16; interpretació de la implementació, revisable). Una capçalera repetida o una fila amb més o menys camps que la capçalera són errors | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Número de soci.** Es conserva el text original. És vàlid si és la representació decimal d'un enter positiu: només xifres del 0 al 9, sense signe, punt, coma, espais interiors ni exponent, i amb un valor entre 1 i 2.147.483.647 (rang de `PositiveIntegerField` a PostgreSQL). Els zeros inicials s'accepten amb un advertiment, i es compara el valor enter: «00067» i «67» són el mateix número. Qualsevol altra forma és un error de línia | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Resultat de la prova.** Cada fila es classifica per separat en identitat i coincidència (nova, coincident, ambigua o en conflicte), errors, advertiments i dades pendents. Una fila amb errors, amb una identitat ambigua o en conflicte, o amb dades o equivalències obligatòries pendents no es presenta com a preparada per importar. Com que encara no hi ha cap equivalència aprovada per al tipus de soci, l'estat ni la data d'alta (S-M01-16, Q-23), ara cap fila no és preparada. Els missatges d'error no contenen cap valor del fitxer, només la línia, la columna i el codi. Els valors diferents de les columnes de catàleg («Quota», «Estat», «Renovació») poden sortir al resum, que es considera informació no fiable i potencialment personal: no van als registres ni a la documentació | Aprovació del responsable del projecte, 04/11/2026 |
| T-M01-10 | **Troballa sense corregir** (04/11/2026, trobada en preparar la T-M01-24). `validate_upload` (`apps/core/files.py`) decideix si un fitxer és text descodificant els primers 64 KB com a UTF-8. Si el tall cau a mig d'un caràcter de més d'un byte (per exemple, una lletra accentuada), rebutja com a «tipus no permès» un CSV vàlid de més de 64 KB. No es corregeix dins de la T-M01-24: cal un tiquet amb la seva prova abans que cap pujada de CSV en depengui | Preparació de la T-M01-24, 04/11/2026 |
| T-M01-24 | **Interpretacions acceptades de la primera part**, com a perfil inicial revisable, que no confirma el format de l'exportació de Cluber: (1) les quatre capçaleres requerides; (2) una dada absent queda pendent i la fila no és preparada; (3) dos conflictes d'identitat més, sense correcció ni fusió automàtica: el document apunta a un soci amb un altre número, o el número apunta a un soci amb un altre document; (4) les línies buides s'ignoren; (5) el detall d'una columna de catàleg es limita a 50 valors diferents i, si en té més, el resultat diu explícitament que el detall s'ha omès i en dona només el recompte | Revisió del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Límit de camp.** El límit aprovat és de 10.000 caràcters: amb 10.000 s'accepta i amb 10.001 és un error de la fila. El mòdul `csv` té un límit intern propi (131.072 caràcters) que no substitueix el límit aprovat i que no es canvia, perquè afecta tot el procés. Un camp que supera aquest límit intern fa rebutjar el fitxer sencer, sense mostrar-ne el contingut | Revisió del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Coincidències.** Per document, «persones actives» vol dir persones no anonimitzades (`Person.status`). No hi té cap relació el compte (actiu, pendent, desactivat o inexistent) ni l'estat del soci: una antiga sòcia no anonimitzada es continua detectant. Per número, es busca entre tots els socis, de qualsevol estat | Revisió del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Dades en memòria i resum segur.** El resultat intern només conserva de cada fila el que fa servir la previsualització: el document normalitzat i el número de soci, amb el text original. No conserva cap columna exclosa ni cap altra dada. La representació de text de l'objecte (`repr`) no mostra aquestes dades, ni els valors de catàleg, ni els noms de columna que no es reconeixen. Això no impedeix que l'objecte es pugui serialitzar d'altres maneres. El que es pot mostrar o registrar és `summary()`: recomptes, codis, files, columnes reconegudes (les altres, per posició) i el nombre de valors de catàleg, sense cap valor del fitxer. Cap persistència, sessió, registre de files ni preparació de la fase final | Revisió del responsable del projecte, 04/11/2026 |
| T-M01-24 | **Registre d'un fitxer rebutjat per IBAN** (precisió de la fila de les fases). Ometre l'empremta del fitxer és una decisió concreta de minimització d'aquesta proposta, no una necessitat tècnica. El punt d'entrada i el seu registre continuen pendents. Continua sent un risc conegut que un IBAN escrit dins d'una altra columna no es detecta: no s'escanegen les cel·les | Revisió del responsable del projecte, 04/11/2026 |
