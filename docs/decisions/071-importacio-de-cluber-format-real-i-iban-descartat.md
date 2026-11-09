# 071 — Importació de Cluber: format real, IBAN descartat en llegir i taula d'equivalències

- **Data:** 09/11/2026
- **Estat:** Acceptada pel responsable del projecte el 09/11/2026 (respostes sobre l'exportació de Cluber). **Matisa la [044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md), la RN-94 de la spec 00 (que no s'edita), la RN-M01-31 i el CA-M01-21:** un fitxer de Cluber amb una columna d'IBAN ja no es rebutja; la columna es descarta en llegir. Resol la Q-23 i la S-M01-16 per al format, amb una mostra inventada. Obre la [P-62](pendents.md) i la [P-63](pendents.md) i registra la proposta [P-64](pendents.md). La [022](022-mandats-sepa-escenari-base-b.md) (escenari B, mandats nous) no canvia.

## Context
La T-M01-24 (fase de prova) es va fer amb un perfil CSV inicial i sense cap equivalència aprovada: cap fila no quedava preparada per importar i una columna d'IBAN rebutjava el fitxer sencer. L'exportació real de Cluber **sempre** porta la columna «IBAN» (just després de «Soci titular»), de manera que la regla anterior faria impossible importar-la. El responsable del projecte ha respost les preguntes sobre el format i el contingut (09/11/2026).

## Decisió
1. **Format:** només CSV, separador «;». Primer s'intenta UTF-8 (amb BOM opcional) i, si no és UTF-8 vàlid, Windows-1252. La previsualització diu quina codificació s'ha detectat. Aquesta tasca no llegeix .xlsx ni afegeix cap dependència (la lectura d'.xlsx queda a la [P-63](pendents.md)).
2. **IBAN:** la columna amb la capçalera «IBAN» (la comparació normalitzada de la T-M01-24: sense U+FEFF ni U+200B, sense espais als extrems, en minúscules, exactament «iban») **es descarta en llegir**: no se'n desa cap valor, no es registra enlloc, no es mostra a la previsualització i no surt a cap missatge. El fitxer no es rebutja. La previsualització avisa que s'ha descartat. Continua el risc conegut: un IBAN escrit dins d'una altra columna no es detecta. La plataforma continua sense rebre cap IBAN de Cluber: els IBAN es recullen amb els mandats nous del 05a (022, 044).
3. **Cap altra informació a Cluber:** ni quotes pagades ni llicències. La RN-M01-33 (quotes històriques) queda sense res a importar.
4. **Una fila per soci.**
5. **Tipus de soci:** (1) si el nom d'un sol tipus actiu surt dins el text de «Quota» (comparació sense majúscules ni accents, per paraules senceres), aquest tipus; (2) si no, pel preu que surt dins el text de «Quota» (p. ex. «Quota de soci col·laborador 35€.» → 3.500 cèntims), comparat amb el preu vigent dels tipus actius; (3) si no es pot (cap preu, més d'un preu, cap tipus amb aquell preu) o dos tipus tenen el mateix preu, la fila queda **pendent** perquè la secretaria triï el tipus.
6. **«Preu total»:** només informació. No crea cap càrrec ni cap quota. La previsualització avisa si no coincideix amb el preu del tipus deduït.
7. **Estat:** tots els socis importats entren **actius**; la revisió és manual en fer la migració (a hores d'ara tots han pagat). L'«Estat» de Cluber no es fa servir.
8. **Dates** (format dd/mm/aaaa): si falta la data d'alta, el soci s'importa igualment i la secretaria la posa a mà. Provisionalment, «Data d'inscripció» = antiguitat (data d'alta del soci) i «Data alta/renovació» = última renovació [A validar: tresorer, [P-62](pendents.md)]. La data de naixement pot ser buida (RN-M01-55). Una data amb un altre format, inexistent o, la de naixement, futura, és un error de la fila: no s'interpreta ni es corregeix.
9. **«Renovació»:** s'ignora [A validar: tresorer, si serveix per a alguna cosa; [P-62](pendents.md)].
10. **Taula d'equivalències al codi** (`apps/members/imports/cluber.py`, `EQUIVALENCES`): cada columna de Cluber que es llegeix, el camp de destinació i la finalitat escrita. Afegir-ne una és afegir-hi una fila i la seva prova. Camps de la persona i del soci: número, nom, cognoms, document, correu, telèfon, data de naixement (`Person.birth_date`), adreça i data d'alta. A més, per resoldre o informar: «Quota» (tipus), «Preu total» (informatiu), «Data alta/renovació» (última renovació), `idInterno` (referència de Cluber) i el consentiment d'imatges. **Cap mode «importa-ho tot»:** la resta de columnes s'ignoren sense conservar-ne el valor. L'adreça es compon amb «Adreça», «Codi Postal» i «Ciutat»; la província no s'hi afegeix.
11. **Titulacions i especialitats:** no s'importen ara.
12. **`idInterno`** → `Member.cluber_id` (referència externa de Cluber, única), per al seguiment del lot.
13. **«Soci titular»:** no s'importa.
14. **«Polítiques de privadesa» no acceptades:** el soci s'importa igualment i se li demana que les accepti la primera vegada que entra. La pantalla d'acceptació no és de la T-M01-24b (vegeu la [P-62](pendents.md), punt 4).
15. **Consentiment d'imatges:** s'importa si surt. La capçalera de Cluber porta el text sencer del consentiment; la importació final el registra com una versió de text (`LegalText`) amb el canal «importat de Cluber». Si el valor de la cel·la no és un «sí» clar, no es registra cap consentiment (per defecte, no atorgat).
16. **Telèfon:** tal com ve (p. ex. `34600000000`).
17. **Ciutat «-»** = buida; no s'omple amb la província.
18. **Mètode de pagament:** s'ignora (05a).
19. **Mostra:** inventada i generada dins de les proves (cap fitxer nou al repositori): 40 socis en Windows-1252 i «;», amb la capçalera real (la de la mostra parcial del 04/11/2026 amb «IBAN» just després de «Soci titular»), IBAN clarament falsos, dates buides, accents, ciutat «-» i quotes amb el mateix preu. Valida el format, no els valors reals de Cluber. Amb aquesta mostra, la Q-23 i la S-M01-16 queden resoltes per al format; les dates (punt 8) i «Renovació» (punt 9) es validen amb el tresorer.
20. **Carnet dels importats:** provisional, vàlid fins a «Data alta/renovació» + 12 mesos; sense aquesta data, cap carnet [A validar: tresorer]. Actualitza la RN-M01-34; la implementació és de la T-M01-25 i la T-M01-19.
21. **Per si de cas:** la proposta que el tresorer guardi l'exportació final xifrada fora de la plataforma, amb data d'esborrat, no està decidida ([P-64](pendents.md)) [A validar: junta i gestoria].
22. La **importació final** continua bloquejada fins al 05a (RN-M01-31, T-M05a-20).

## Conseqüències
- **T-M01-24b** (nova, continuació de la T-M01-24, que continua Feta): lector i previsualització amb la codificació alternativa, l'IBAN descartat, la taula d'equivalències, la normalització, la resolució del tipus, `idInterno`, el consentiment d'imatges, la data de naixement i «Preu total» informatiu. No escriu res, com la T-M01-24.
- **T-M01-25:** fa servir la taula d'equivalències; crea la persona i el soci actius, amb `cluber_id`, la data de naixement i el consentiment d'imatges. Ha de resoldre, abans de posar-la en servei:
  - el **tipus de document**, que Cluber no porta i que el model de persona exigeix quan hi ha número (fila «Document sense tipus» de la T-M01-24); mentre no es resolgui, cap fila no queda preparada per importar ([P-62](pendents.md), punt 5);
  - la **data d'alta absent**: `Member.joined_on` és obligatòria i no s'inventa cap data ([P-62](pendents.md), punt 6);
  - el **canal «importat de Cluber»** a `Consent` i la versió de text del consentiment de Cluber: necessiten una migració a `core`, que no fa la T-M01-24b;
  - els codis de línia nous de la previsualització (`date_invalid`, `total_price_differs`), que encara no són a la llista tancada d'`ImportLine` (`IMPORT_LINE_CODES`, amb restricció a la base de dades): s'hi afegeixen amb la mateixa migració abans de desar cap línia;
  - l'**empremta del fitxer**: la T-M01-24 no la registra quan el fitxer té una columna d'IBAN (minimització aprovada). Com que l'exportació real sempre en porta, la prova no en registrarà mai cap; si la confirmació la necessita, cal una decisió nova.
- **RN-M01-31, RN-M01-33, RN-M01-34 i CA-M01-21:** precisats al [pla](../planning.md) amb un enllaç a aquesta decisió, sense duplicar-ne el contingut.
- **Spec 00 (RN-94, L17):** no s'edita; aquesta decisió hi preval per a la importació de Cluber.

## Fonts
- Respostes del responsable del projecte, 09/11/2026 (sessió de la T-M01-24b).
- Capçaleres de la mostra parcial del 04/11/2026 (sense dades: no està anonimitzada i no s'ha copiat enlloc).
- [044](044-domiciliacio-sepa-iban-i-mandat-xifrats.md), [022](022-mandats-sepa-escenari-base-b.md), [070](070-quota-integra-i-renovacio-als-12-mesos-del-pagament.md) (renovació als 12 mesos); RN-M01-31 a RN-M01-34, RN-M01-55 i CA-M01-21 del [pla](../planning.md).
