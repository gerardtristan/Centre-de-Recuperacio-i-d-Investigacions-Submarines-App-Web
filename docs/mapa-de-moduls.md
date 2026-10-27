# Mapa de mòduls

- **Data:** 27/10/2026
- **Ordre:** el de la [decisió 024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), sense dates ([038](decisions/038-planificar-sense-dates.md)): per dependències i per valor.
- **Numeració:** fixa, de 00 a 13 ([planning.md, estat i numeració](planning.md#estat)). Cap mòdul no canvia de número; un mòdul nou s'afegeix al final. **El número no és l'ordre de construcció.** La correspondència amb el mapa de la plataforma v8 (M00–M12), amb el document de funcionalitats i amb els textos antics («resta de la 04» = 09) és a [planning.md#numeracio](planning.md#numeracio).
- **Origen:** mapa de mòduls del repositori anterior (històric), adaptat.

## 1. Resum
| Fase | Mòdul | Valor | Depèn de | Bloquejat per | Spec |
|---|---|---|---|---|---|
| **1 · Deixar Cluber** | 00 Base comuna | Imprescindible | — | P-04 (matriu de rols) | [spec 00](../specs/00-base-comuna/spec.md) (v2) |
| | 01 Socis i carnet digital (amb registre mínim de llicència) | Molt alt | 00 | Regles de soci de F §3; P-28; [039](decisions/039-numeros-de-soci-no-es-reutilitzen.md) i [040](decisions/040-impagat-es-marca-a-ma.md) provisionals | [planning.md, M01](planning.md#M01) (aprovat) |
| | 04 Tresoreria, part mínima | Molt alt | 00, 01 | Q-17 (departaments); format de l'extracte i de les liquidacions (P-45) | [planning.md, M04](planning.md#M04) (aprovat; la spec 04 v2 és a l'[arxiu](arxiu/spec-04-tresoreria-v2-2026-10-27.md)) |
| | 05a Alta del mètode de pagament i mandats | Molt alt | 01, 04 | Proveïdor ([043](decisions/043-proveidor-de-pagaments-dins-la-ue.md)) i preguntes al banc (P-45); P-21. La [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md) és acceptada | [planning.md, M05a](planning.md#M05a) (aprovat) |
| | 05b Cobraments: **pagament dins l'app amb targeta i Bizum**, domiciliació, transferència, remeses, retornats, devolucions | Molt alt: és el criteri per deixar Cluber | 05a | Proveïdor (043); remeses del banc (P-45 punt 5); P-12, P-29 | [planning.md, M05b](planning.md#M05b) (aprovat) |
| **2 · La resta** (ordre: 02 → 03 → 09 → 06 → 07 → 08) | 02 Activitats (cursos i sortides) | Alt | 00, 01, 04, 05b | Catàleg i preus; política de cancel·lació; requisits; subtipus de medi ambient | [planning.md, M02](planning.md#M02) (escrit) |
| | 03 Material | Alt | 00, 02 | Centres de busseig i tarifes; cost d'ús; qui paga el material llogat | [planning.md, M03](planning.md#M03) (escrit) |
| | 09 Marge, despeses, ajuts i facturació | Molt alt | 02, 03, 04, 05b | P-02 i P-47 (gestoria: IVA, Verifactu i què s'ha de facturar) | Pendent |
| | 06 Llicències | Alt | 01, 05b | Preus i procés de la FECDAS ([036](decisions/036-fecdas-alia.md)) | Pendent |
| | 07 Web pública (amb l'ajuda: preguntes freqüents, contacte i tutorials) | Mitjà | 01, 02 | P-40 a P-43 | Pendent |
| | 08 Dashboard | Alt per a la junta | 01, 02, 04, 09 | Preguntes de la junta | Pendent |
| **Després de la fase 2** | 10 Missatges i xat per activitat | Mitjà | 01, 02 | Abast del xat | Pendent |
| | 11 Departament d'Història i conferències | Mitjà | 01, 02, 07 | P-43 | Pendent |
| | 12 Idees noves (avatars de fauna marina i bitàcola) | Baix (Could) | 01, 02, 03 | P-38 | Pendent |
| **Fora d'abast ara** | 13 Botiga en línia | — | — | — | — |

**Pagar dins l'app no queda per a més endavant:** targeta i Bizum són al 05b, dins la fase 1, just després de la 04 i del 05a ([024](decisions/024-abast-minim-i-ordre-per-deixar-cluber.md), [043](decisions/043-proveidor-de-pagaments-dins-la-ue.md)).

## 2. Peces del mapa v8 que no són mòduls
| Peça | On va | Depèn de |
|---|---|---|
| Web instal·lable (PWA, M12 del mapa v8): manifest, carnet i pantalla sense connexió, safata d'avisos, ajuda per instal·lar-la | Amb la interfície des del 01 ([041](decisions/041-web-installable-i-avisos-sense-push.md)). Sense botigues ni push | 01 |
| Ajuda: preguntes freqüents, contacte, tutorials (M07b) | Dins el 07 | 07 |

## 3. Requisits no funcionals (tots els mòduls)
- **Dades personals només dins la UE** ([035](decisions/035-dades-nomes-dins-ue.md)); tot proveïdor passa pel [registre](proveidors-i-dades-ue.md).
- Cap dada de targeta ni credencials del banc a l'app. IBAN: només xifrat al mandat segons la [044](decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md).
- La resta, a CLAUDE.md («Regles que sempre s'han de complir»), a [planning.md, regles generals](planning.md#regles) i a la [checklist](checklist-produccio.md).

## 4. Correspondència amb el mapa v8
A [planning.md#numeracio](planning.md#numeracio) (una sola taula, per no duplicar-la).
