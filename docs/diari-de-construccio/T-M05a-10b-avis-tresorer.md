# T-M05a-10b · Avís al tresorer en revocar un mandat amb un rebut ja al banc

| Data i hora (Europa/Madrid) | Commit | Proves | CI |
|---|---|---|---|
| 18/11/2026 | cf56dba9 | 7 noves | [A comprovar] |

**En tres línies:** si un soci revoca la domiciliació quan el seu rebut ja és al banc, el banc el cobrarà igualment. Ara el tresorer rep un correu que li diu quin mandat i quina remesa, perquè miri si encara el pot retirar o, si es cobra, torni l'import. El correu no porta ni el nom ni l'IBAN del soci.

## Què s'ha fet
- `mandates.revoke_mandate` (des del compte personal o des de l'administració) mira si el mandat té un rebut inclòs en una remesa que ja pot ser al banc ([RN-M05a-09](../planning.md#M05a-7-regles); L-M05a-04 i L-M05b-03).
- Si n'hi ha, correu `avis-mandat-revocat-remesa` a qui té el permís de la tresoreria (T1), amb la referència del mandat, el període i la data de cobrament. Text provisional [A validar: tresorer].
- Una entrada al registre d'activitat (`payments.mandate.revoked_in_remittance`) amb la referència i les remeses.

## Decisions i perquè
- **Què vol dir «ja enviada»:** la remesa «enviada al banc» o la «avisada» amb el fitxer ja descarregat, perquè el tresorer el pot haver pujat al banc sense haver-la marcat encara. Una avisada sense fitxer no avisa: el fitxer ja no es pot generar amb el mandat revocat.
- **Destinataris:** els mateixos que els altres avisos al tresorer (`processing.notify_treasurers`, permís T1), mai una persona escrita al codi.
- **Una sola vegada:** un mandat només es revoca una vegada, i el canvi d'IBAN no avisa ([P-367](../decisions/pendents.md)). El correu al soci no s'ha tocat ([P-368](../decisions/pendents.md)).

## Problemes trobats
- La prova que comprovava que no sortien els quatre darrers dígits de l'IBAN de prova (`0001`) fallava perquè la referència del mandat (`CRIS000001M01`) també els conté: es comprova la cua llarga de l'IBAN i que no hi hagi cap IBAN emmascarat.

## Com se sap que funciona
`apps/payments/tests/test_mandate_revoked_after_remittance.py`: avís a qui té T1 i no a la secretaria, una sola vegada, sense IBAN ni nom; amb el fitxer descarregat sí; amb la remesa avisada sense fitxer, liquidada o anul·lada, no; sense cap remesa, no; i la revocació d'un altre soci, no.

## Termes nous
- Cap.
