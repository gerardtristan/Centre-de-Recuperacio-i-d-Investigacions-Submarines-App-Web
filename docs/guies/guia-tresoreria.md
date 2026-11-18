# Guia curta de la tresoreria

**Per a qui és:** el tresorer. **Estat:** esborrany de la T-M04-19 [A validar: tresorer]. Està escrita a partir de les pantalles que hi ha avui. Les regles no es copien aquí: cada apartat enllaça la secció del [pla](../planning.md#M04) on són. Per entrar a l'administració, vegeu la [guia del tresorer](guia-tresorer.md#1-entrar-a-ladministració).

Al menú de l'administració, la tresoreria té quatre entrades: **Tresoreria: comptes i saldos**, **Tresoreria: moviments**, **Tresoreria: conciliació** i **Tresoreria: extracte bancari**. Només surten si tens el permís.

## 1. Importar l'extracte del banc
**Tresoreria: extracte bancari** ([P-M04-E](../planning.md#M04-5-processos)).
1. A **Importar un extracte**, tria el fitxer del banc (CSV o Norma 43) i prem **Previsualitza**. El fitxer no es desa.
2. La previsualització compta les **línies noves**, les **duplicades (ja importades)** i les que tenen **error**. Els números de compte i de targeta del concepte surten tapats.
3. Si hi ha línies amb error, marca **Exclou les línies amb error** i prem **Confirma la importació**. Si no, **Cancel·la**.

Les duplicades no es tornen a importar mai. Un cop importat, les línies noves ja surten a la conciliació.

**Desfer una importació:** a la taula d'extractes importats, escriu el **motiu per desfer-lo** i prem **Desfés**. No es pot desfer si alguna línia de l'extracte ja està conciliada: primer desfés aquella conciliació (apartat 3).

## 2. Conciliar
**Tresoreria: conciliació** ([P-M04-E](../planning.md#M04-5-processos), [regles](../planning.md#M04-7-regles)). La plataforma proposa i només el tresorer confirma.
- **Proposada:** la línia porta la referència d'un càrrec (o de diversos) i l'import quadra. Revisa els càrrecs de la columna **Càrrecs** i prem **Confirma**. Els càrrecs passen a «pagat», l'ingrés s'apunta al banc i el soci rep el rebut.
- **A revisar:** la plataforma no ha pogut proposar res. El motiu surt al costat: l'import no coincideix, el càrrec ja no està pendent, la referència no és de cap càrrec, el càrrec ja és en una altra proposta, o la línia no té referència i hi ha un sol càrrec pendent amb aquest import.
- **Proposada amb una liquidació:** la línia és l'abonament agrupat del proveïdor de pagaments (targetes i Bizum): l'import és el net d'una liquidació rebuda i la data, dels 5 dies següents ([P-M04-F](../planning.md#M04-5-processos), [P-364](../decisions/pendents.md)). La columna **Càrrecs** en diu el proveïdor i l'identificador. Prem **Revisa i confirma…**: hi veus el brut, la comissió de cada cobrament i el net; prem **Sí, confirma-la**. Les comissions s'apunten al departament de cada cobrament i el net passa del compte de trànsit al banc. Si dues liquidacions (o dues línies) tenen el mateix import, la línia queda «a revisar»: prem **Revisa i tria…**, marca la liquidació, prem **Revisa aquesta liquidació** i confirma-la igual. Desfer-la (apartat 3) torna la liquidació a «rebuda» i compensa el traspàs; les comissions es queden i aquella línia no es torna a proposar amb la mateixa liquidació ([P-365](../decisions/pendents.md)). Una liquidació proposada a una línia no es confirma des de **Liquidacions**: es fa des de la conciliació. Una remesa conciliada no es desfà (es corregeix amb un retorn o una devolució).
- **Conciliada** i **Exclosa:** ja estan resoltes.

**Casar a mà** una línia pendent (també «a revisar»): prem **Casa a mà…** (a la conciliació o a «A revisar»), escriu les referències de transferència o els números de soci (diversos, separats per espais) i prem **Cerca**. Un càrrec amb un cobrament en curs (una targeta o un Bizum en curs o «a revisar», o una remesa enviada al banc) o que ja és a la proposta d'una altra línia surt sense casella. Marca els càrrecs i prem **Revisa el casament**: han de sumar exactament l'import de la línia. Si quadra, prem **Sí, casa-la**: passa el mateix que en confirmar una proposta, i es desfà igual (apartat 3). Casar una línia amb un moviment (per exemple, l'efectiu ingressat al banc) encara no es pot fer [pendent: T-M04-12f].

## 3. Desfer una conciliació
A la línia conciliada, obre **Desfés…**, escriu el **motiu per desfer-la** i prem **Desfés la conciliació**. Els càrrecs tornen a «pendent», el pagament queda anul·lat i l'ingrés es compensa amb un contramoviment. No s'esborra res, i el rebut d'una transferència queda anul·lat amb una nota (decisió [045](../decisions/045-correccio-transferencia-conciliada-per-error.md)).

## 4. Excloure una línia
Per a una línia que no és de cap càrrec (per exemple, un moviment del banc que no té res a veure amb els socis): obre **Exclou…**, escriu el **motiu de l'exclusió** i prem **Exclou la línia**. No es crea cap moviment ni es paga cap càrrec. La línia queda «exclosa», amb el motiu, a la línia i al registre d'activitat ([regles](../planning.md#M04-7-regles)).

La llista **A revisar** (enllaç **Mira les línies a revisar** de la conciliació) recull les línies pendents de decidir, amb el motiu i el mateix botó **Exclou…**, i les liquidacions del proveïdor «a revisar» (un cobrament que la plataforma no reconeix), amb la referència i el problema; **Revisa-les a «Liquidacions»** porta a la seva pantalla. Des d'aquesta llista no es mou cap diner. Els pagaments «a revisar» del proveïdor es tanquen a la llista de pagaments (enllaç **Pagaments «a revisar»**) ([P-191](../decisions/pendents.md), [P-390](../decisions/pendents.md)).

## 5. Comptes, saldos i moviments
- **Tresoreria: comptes i saldos:** el saldo de cada compte el calcula la plataforma, mai s'escriu a mà. Tria una **Data del saldo** i prem **Mostra** per veure el saldo d'un altre dia.
- **Tresoreria: moviments:** filtra per compte, departament, centre de cost i dates. Un moviment no es modifica ni s'esborra: una correcció és un contramoviment, i el moviment anul·lat continua a la llista marcat «Anul·lat» ([regles](../planning.md#M04-7-regles)).

## 6. Exportar per a la gestoria
A **Tresoreria: moviments**, posa els filtres que vulguis (per exemple, les dates del trimestre) i prem **Descarrega el CSV per a la gestoria**. El fitxer porta els mateixos filtres que la pantalla, sense IBAN ni noms. Cada descàrrega queda al registre d'activitat. El format dels imports és provisional ([P-242](../decisions/pendents.md)).

## 7. Encara sense pantalla
- **Traspassos entre comptes** (per exemple, de la caixa al banc) i **arqueig de caixa**: la plataforma ja els sap registrar, però encara no hi ha pantalla [pendent: T-M04-15]. Regles: [M04-7](../planning.md#M04-7-regles); dubtes oberts: [P-222 a P-225](../decisions/pendents.md).

## 8. Si alguna cosa no quadra
- Una pàgina que diu **«No s'ha trobat la pàgina»** pot voler dir que no tens el permís: les dues coses es veuen igual, a propòsit.
- Tot el que confirmes, desfàs o exclous queda al registre d'activitat amb el teu compte i el motiu.
