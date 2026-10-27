# Mapa de mòduls

- **Data:** 27/10/2026
- **Ordre:** el de la [decisió 024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), sense dates ([038](decisions/038-planificar-sense-dates.md)): per dependències i per valor.
- **Numeració:** la d'aquest repositori (0-8, CLAUDE.md). La taula del final la relaciona amb la del mapa de la plataforma v8.
- **Origen:** mapa de mòduls del repositori anterior (històric), adaptat.

## 1. Resum
| Fase | Mòdul | Valor | Depèn de | Bloquejat per | Spec |
|---|---|---|---|---|---|
| **1 · Deixar Cluber** | 00 Base comuna | Imprescindible | — | P-04 (matriu de rols) | [spec 00](../specs/00-base-comuna/spec.md) (v2) |
| | 01 Socis i carnet (amb registre mínim de llicència) | Molt alt | 00 | Regles de soci de F §3; P-28; [039](decisions/039-numeros-de-soci-no-es-reutilitzen.md) i [040](decisions/040-impagat-es-marca-a-ma.md) provisionals | [planning.md, M01](planning.md#M01) (aprovat) |
| | 04 Tresoreria, part mínima | Molt alt | 00, 01 | Q-17 (departaments); format de l'extracte (P-45) | [planning.md, M04](planning.md#M04) (escrit; integra la [spec 04](../specs/04-tresoreria/spec.md) v2) |
| | 05a Alta del mètode de pagament i mandats | Molt alt | 01, 04 | Proveïdor ([043](decisions/043-proveidor-de-pagaments-dins-la-ue.md)) i preguntes al banc (P-45); [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md); P-21 | [planning.md, M05a](planning.md#M05a) (escrit) |
| | 05b Cobraments: **pagament dins l'app amb targeta i Bizum**, domiciliació, transferència, remeses, retornats, devolucions | Molt alt: és el criteri per deixar Cluber | 05a | Proveïdor (043); P-12, P-24, P-29; experiència de pagament (spec 04, annex D) | [planning.md, M05b](planning.md#M05b) (escrit) |
| **2 · La resta** | 02 Activitats (cursos i sortides) | Alt | 01, 04 | Catàleg i preus; centres de busseig; subtipus de medi ambient | Pendent |
| | 03 Material | Alt | 02 | Qui paga el material llogat; cost d'ús | Pendent |
| | Resta de la 04 (marge, despeses amb factura, ajuts, facturació) | Molt alt | 02, 03, 05b | P-02 (gestoria: IVA, Verifactu i què s'ha de facturar, P-47) | Pendent |
| | 06 Llicències | Alt | 01, 05b | Preus i procés de la FECDAS ([036](decisions/036-fecdas-alia.md)) | Pendent |
| | 07 Web pública | Mitjà | 01, 02 | P-40 a P-43 | Pendent |
| | 08 Dashboard | Alt per a la junta | 02, 04 | Preguntes de la junta | Pendent |

**Pagar dins l'app no queda per a més endavant:** targeta i Bizum són al 05b, dins la fase 1, just després de la 04 i del 05a ([024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), [043](decisions/043-proveidor-de-pagaments-dins-la-ue.md)).

## 2. Peces que el mapa v8 té i aquest repositori encara no numera
| Peça | Proposta | Depèn de |
|---|---|---|
| Web instal·lable (PWA): manifest, carnet i pantalla sense connexió, safata d'avisos, ajuda per instal·lar-la | Va amb el frontend des del 01 ([041](decisions/041-web-installable-i-avisos-sense-push.md)). Sense botigues ni push | 01 |
| Missatges i xat per activitat | Mòdul propi a la fase 2 [A validar número] | 01, 02 |
| Departament d'Història i conferències | Dins el 02 (activitats) o propi [A validar] | 01, 07 |
| Ajuda: preguntes freqüents, contacte, tutorials | Dins el 07 | 07 |
| Idees noves (avatars de fauna marina, bitàcola…) | Després de la fase 2 | 01, 03 |
| Botiga en línia | Fora d'abast ara (CLAUDE.md) | — |

## 3. Requisits no funcionals (tots els mòduls)
- **Dades personals només dins la UE** ([035](decisions/035-dades-nomes-dins-ue.md)); tot proveïdor passa pel [registre](proveidors-i-dades-ue.md).
- Cap dada de targeta ni credencials del banc a l'app. IBAN: només xifrat al mandat si s'aplica la [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md).
- La resta, a CLAUDE.md («Regles que sempre s'han de complir») i a la [checklist](checklist-produccio.md).

## 4. Correspondència amb el mapa v8
| Mapa v8 | Aquest repositori |
|---|---|
| M00 Base | 00 Base comuna |
| M01 Socis i carnet | 01 Socis i carnet |
| M05a Tresoreria: nucli | 04 Tresoreria, part mínima |
| M05b Pagaments | 05a i 05b |
| M05c Marge, factures i ajuts | Resta de la 04 |
| M02 Cursos i M03 Sortides | 02 Activitats |
| M04 Material | 03 Material |
| M06 Llicències | 06 Llicències |
| M07a Web, M07b Ajuda | 07 Web pública |
| M09 Dashboard | 08 Dashboard |
| M07c Missatges, M08 Història, M11 Idees, M12 PWA | §2 |
| M10 Botiga | Fora d'abast |
