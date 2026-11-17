# Guia del tresorer: remeses, retornats i devolucions

**Per a qui és:** el tresorer. **Estat:** esborrany de la T-M05b-20 [A validar: tresorer]. Està escrita a partir de les pantalles que hi ha avui. Les parts que encara no estan fetes ho diuen i porten la tasca que les farà. Les regles són al [pla, secció M05b](../planning.md#M05b). Per a la conciliació del banc, vegeu la [guia de la tresoreria](guia-tresoreria.md).

**Cap cobrament real fins al nivell 2.** Mentre la plataforma és al nivell 1 (només recollir mètodes i mandats), no es pot generar cap remesa ni cobrar res de debò (decisions 025 i 042; [P-M05b-I](../planning.md#M05b-5-processos)).

## 1. Pagaments i «a revisar»
La pantalla **Pagaments i «a revisar»** (adreça `pagaments/` de l'administració; encara no és al menú) mostra:
- **A revisar:** els pagaments que necessiten una persona, amb el motiu. Per exemple, una notificació del proveïdor que no quadra amb cap pagament, o una transferència conciliada sense rebut.
- **Tots els intents de pagament**, amb filtre per estat.

Només és de consulta: un «a revisar» encara no es pot tancar des de la pantalla ([P-82](../decisions/pendents.md)). El nom de qui paga només el veu qui té el permís de dades personals ([P-247](../decisions/pendents.md)).

## 2. Fer una remesa de quotes domiciliades
Pantalla **Remeses** (adreça `pagaments/remeses/` de l'administració; encara no és al menú) ([P-M05b-E](../planning.md#M05b-5-processos)).
1. A **Nova remesa**, escriu el **Període** (una etiqueta per trobar-la, per exemple «2026-12») i la **Data de cobrament**. La data ha de deixar temps per a l'avís previ: la pantalla proposa la primera data possible i no n'accepta cap d'anterior.
2. Prem **Previsualitza**. Hi veus quants **rebuts** hi entren, l'**import total** i, a sota, les **quotes que no entren i per què**: dades personals esborrades, sense mandat actiu, no ha triat la domiciliació, o té un pagament en curs o en una altra remesa.
3. Si està bé, prem **Sí, crea la remesa**. Si canvies la data, cal tornar a previsualitzar.

Hi entren les quotes pendents dels socis que han triat la domiciliació i tenen un mandat actiu ([regles](../planning.md#M05b-7-regles)). Quines quotes i quin període exactament: [P-230](../decisions/pendents.md).

## 3. Avisos previs
En crear la remesa, cada deutor rep l'avís previ per correu, amb l'IBAN emmascarat. El termini de l'avís és un ajust (14 dies d'entrada). El text és provisional [A validar: junta].
- La remesa surt com a **Esborrany: falten avisos** fins que tots s'han enviat, i llavors com a **Avisada**.
- Al detall de la remesa, la columna **Avís previ** diu a qui falta. Prem **Torna a enviar els avisos que falten**.
- Un soci sense adreça de correu: [P-232](../decisions/pendents.md).

## 4. Descarregar el fitxer per al banc
Al detall de la remesa, prem **Descarrega el fitxer pain.008**. El fitxer es genera a cada descàrrega i no es desa a la plataforma.

**El fitxer porta els IBAN sencers.** Puja'l a la banca en línia i esborra'l del dispositiu el mateix dia, sense enviar-lo per correu ni deixar-lo en carpetes sincronitzades (decisió [044](../decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)). Cada descàrrega queda al registre amb l'empremta del fitxer. La versió del fitxer que demana el banc s'ha de verificar [A verificar: P-233].

## 5. Marcar la remesa com a enviada i casar l'abonament del banc
Encara no es pot fer des de la plataforma [pendent: T-M05b-11]. Quan hi sigui, marcar-la com a enviada demanarà confirmar que has esborrat el fitxer, i l'abonament del banc es casarà a la conciliació com una liquidació ([P-M05b-E, passos 6 a 8](../planning.md#M05b-5-processos)).

## 6. Rebuts retornats
Encara no hi ha pantalla de retornats [pendent: T-M05b-12]. La plataforma ja sap passar un càrrec de «pagat» a «retornat» i reobrir-lo, però ningú no ho fa encara des d'una pantalla. Quan hi sigui, el reintent o l'alternativa de pagament dependran del motiu del banc ([P-M05b-F](../planning.md#M05b-5-processos), [regles](../planning.md#M05b-7-regles)). Dubte obert: què passa amb el pagament retornat ([P-240](../decisions/pendents.md)).

## 7. Devolucions
Tornar diners a un soci (una devolució que inicia el club) encara no es pot fer des de la plataforma [pendent: T-M05b-13]. El procés previst és a [P-M05b-G](../planning.md#M05b-5-processos). Mentrestant, una devolució es fa fora de la plataforma i s'ha d'anotar quan la funció hi sigui.

## 8. Mandats
La pantalla **Pagaments: mètodes i mandats** (al menú) mostra els mandats dels socis, sempre amb l'IBAN emmascarat. Amb **Revoca…**, el motiu i **Sí, revoca'l** es revoca un mandat: no es cobrarà cap quota més amb aquest mandat i el soci rep un correu. El teu propi mandat no el pots revocar des de l'administració, només des del teu compte personal. La signatura dels mandats per part dels socis està apagada fins que la junta aprovi el text ([ajuda per als socis](ajuda-socis-pagaments.md#3-el-mandat-de-domiciliació)).
