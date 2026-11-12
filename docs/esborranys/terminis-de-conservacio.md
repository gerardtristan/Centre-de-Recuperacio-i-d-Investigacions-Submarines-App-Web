# Terminis de conservació: esborrany

> **Decisió [085](../decisions/085-respostes-del-responsable-a-les-preguntes-pendents-de-t-m00-i-t-m01.md) (12/11/2026, G-1):** queda fixat i implementat el termini de les **dades bloquejades** d'una persona esborrada: 6 anys des del 31/12 de l'any de l'últim registre econòmic, i després es destrueixen (fila 3). Triat per l'equip per delegació del responsable, sense validació d'una gestoria. La resta de files continua sent una proposta.

> **ESBORRANY. NO VIGENT. A VALIDAR: gestoria i assessor de protecció de dades.** No es pot aplicar. Respon a la Q-027 (Q-14 de la spec 00), segons la [decisió 072](../decisions/072-respostes-del-responsable-a-la-ronda-1-de-pendents.md). Les bases legals les ha consultat l'equip en fonts secundàries el 09/11/2026: cada una porta **[A verificar]** fins que la gestoria la confirmi amb el text oficial.

## Principis que ja són decisió
- **Limitació del termini (RGPD, art. 5.1.e):** les dades personals es conserven només el temps necessari per a la finalitat.
- **Bloqueig (LOPDGDD, art. 32):** quan acaba la finalitat però encara hi ha una obligació legal o una possible reclamació, les dades es bloquegen. Només les pot veure qui les necessiti per a aquesta obligació.
- **Registres econòmics** ([058](../decisions/058-respostes-fecdas-gestoria-i-cursos.md), punt 7): les factures, els cobraments, les despeses i els moviments no s'eliminen mai. Les dades personals que hi surten es bloquegen i, passat el termini legal, s'anonimitzen.
- **Registre d'activitat** ([028](../decisions/028-esborrat-rgpd-i-registre-d-activitat.md)): en esborrar una persona, el que la identifica se substitueix per una referència anònima.
- **IBAN** ([044](../decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)): només xifrat al mandat.

## Proposta de terminis

| # | Què | Termini proposat | Des de quan | Base legal | Després del termini |
|---|---|---|---|---|---|
| 1 | Comptabilitat: moviments, comptes, llibres i comptes anuals | 6 anys | Tancament de l'exercici (o últim assentament) | Codi de comerç, art. 30, aplicat per analogia. El Codi civil de Catalunya (llibre tercer, art. 313-1 i 313-2) obliga les associacions a portar comptabilitat; no s'ha trobat que hi fixi un termini **[A verificar]** | El moviment es conserva; les dades personals s'anonimitzen |
| 2 | Factures emeses i rebudes, i rebuts | 6 anys (mínim fiscal, 4) | Final del termini de declaració de l'exercici | Llei 58/2003 General Tributària, art. 66 (prescripció de 4 anys) i art. 70 (conservació mentre no prescriu); RD 1619/2012, art. 19; si formen part de la comptabilitat, 6 anys (fila 1) **[A verificar]**. En alguns casos, la comprovació pot arribar a 10 anys (LGT, art. 66 bis) **[A verificar]** | Com la fila 1 |
| 3 | Quotes, càrrecs i pagaments dels socis | 6 anys | Tancament de l'exercici del pagament | Fila 1 (formen part de la comptabilitat) | Com la fila 1 |
| 4 | Deutes de quotes impagades | Mentre es puguin reclamar: 3 anys | Venciment de cada quota | Codi civil de Catalunya, art. 121-21 (3 anys per a prestacions periòdiques). Cal confirmar si s'aplica a les quotes associatives **[A verificar]** | Es tanca el deute amb motiu; es manté la fila 3 |
| 5 | Mandats SEPA (05a) | Mentre és vigent i com a mínim 14 mesos després de l'últim cobrament | Últim cobrament o cancel·lació | Rulebook SDD Core de l'EPC (versió vigent: 2025 v1.2). Un mandat caduca als 36 mesos sense cap cobrament **[A verificar amb el banc]** | S'esborra el mandat amb l'IBAN xifrat; se'n conserva una referència sense IBAN |
| 6 | Documents de justificació d'ajuts ([051](../decisions/051-abast-de-la-044-i-documents-de-justificacio.md)) | El que digui cada convocatòria; com a mínim 4 anys | Data de justificació | Llei 38/2003 General de Subvencions, art. 39 (prescripció del reintegrament, 4 anys); els fons europeus poden demanar més temps **[A verificar]** | Es conserva la còpia amb l'IBAN emmascarat fins a la fila 1 |
| 7 | Certificats de donatius (model 182) | 4 anys | Any de la declaració | LGT, art. 66 **[A verificar]** | Com la fila 1 |
| 8 | Dades del perfil d'una persona sòcia | Mentre és sòcia | — | RGPD, art. 6.1.b (relació associativa) | Vegeu la fila 9 |
| 9 | Dades del perfil després de la baixa | 3 anys, bloquejades | Data efectiva de la baixa | Termini de les reclamacions de la fila 4 **[A validar]** | S'anonimitza el perfil; el que surt als registres econòmics segueix les files 1 a 3 |
| 10 | Dades del representant d'un menor | Com les del soci (resposta Q-026: mentre sigui soci) | — | RGPD, art. 6.1.b i 6.1.c | Com les files 8 i 9 |
| 11 | Sol·licituds d'alta rebutjades o no aprovades | **Pendent de nova resposta del responsable (Q-024)** | Data del rebuig | Proposta de l'equip: 1 any, bloquejades, per si hi ha una reclamació; després s'anonimitzen i les acceptacions queden sense identificar ningú **[A validar]** | — |
| 12 | Consentiments i textos acceptats | Mentre dura el tractament, i 3 anys després de la retirada o de la fi | Retirada o fi del tractament | Per poder demostrar el consentiment (RGPD, art. 7.1) durant el termini de prescripció de les infraccions de la LOPDGDD (art. 72 a 74: 3, 2 i 1 anys) **[A verificar]** | S'anonimitza la persona; la versió del text es conserva |
| 13 | Registre d'activitat (dades de socis i diners) | Com els registres que descriu: 6 anys per als econòmics | Data de l'acció | Files 1 a 3 | Referència anònima (028) |
| 14 | Línies de la importació de Cluber | **Pendent de nova resposta del responsable (Q-073)** | — | — | — |
| 15 | Registres tècnics de límits (IP, empremtes) | Els que ja fixa el pla (minuts o 24 hores) | — | RGPD, art. 6.1.f | S'esborren |
| 16 | Còpies de seguretat | Rotació de la [006](../decisions/006-copies-de-seguretat.md) | — | — | Una dada esborrada pot sobreviure a una còpia fins que caduca; cal dir-ho a la política de privacitat |

## Esborrat amb càrrecs pendents (segona part de la Q-027)
Proposta de l'equip **[A validar: gestoria]**:
- Es desactiven els comptes i s'anonimitzen les dades que no calen per al deute.
- Les que calen per reclamar-lo (nom, document i quotes pendents) es bloquegen fins que es cobra el deute o prescriu (fila 4).
- Després s'anonimitzen.
- Mai no s'esborra cap registre econòmic.

## Preguntes per a la gestoria
1. Quin termini de conservació s'aplica a la comptabilitat d'una associació catalana: el del Codi de comerç (6 anys) o un altre?
2. Les factures i els rebuts: 4 o 6 anys?
3. Les quotes impagades prescriuen als 3 anys (art. 121-21 CCCat)?
4. Els ajuts que rep el club tenen terminis propis a les bases de les convocatòries?
5. Hi ha cap altra obligació (per exemple, la Llei 10/2010 de prevenció del blanqueig de capitals) que s'apliqui al club? Si no s'hi aplica, no cal cap termini de 10 anys.
6. Els terminis de les files 9, 11 i 12 són raonables?

## Fonts consultades (secundàries, 09/11/2026)
- Codi de comerç, art. 30, i guies per a entitats: [Ajuntament del Prat, sessió 2](https://www.elprat.cat/sites/default/files/sessio_02_-_normativa_i_pgc_1.pdf) i [ENS, «Conservar la documentació associativa»](https://www.ens.cat/assets/files/recursos/31/Conservar%20la%20documentaci%C3%B3%20associativa.pdf).
- Codi civil de Catalunya, llibre tercer (Llei 4/2008): [text consolidat al BOE](https://www.boe.es/buscar/pdf/2008/BOE-A-2008-9293-consolidado.pdf).
- LGT, prescripció: [Papelea, articles 66 a 70](https://papelea.com/es/leyes/ley-general-tributaria/titulo-ii_capitulo-iv_seccion-3-la-prescripcion); conservació de factures: [TeamSystem](https://teamsystem.es/magazine/cuanto-hay-que-conservar-originales-facturas/).
- Prescripció de deutes periòdics a Catalunya: [Diputació de Barcelona, consum](https://consum.diba.cat/printpdf/news/2024/05/31/prescripcio-del-dret-reclamar-deutes-les-persones-consumidores).
- Mandats SEPA: [EPC, rulebook SDD Core](https://www.europeanpaymentscouncil.eu/what-we-do/sepa-direct-debit/sepa-direct-debit-core-rulebook) i [Microsoft, resum per a creditors](https://learn.microsoft.com/dynamics365/finance/accounts-receivable/sepa-direct-debit-overview).
