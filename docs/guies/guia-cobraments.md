# Guia del tresorer: remeses, retornats i devolucions

**Per a qui és:** el tresorer. **Estat:** esborrany de la T-M05b-20 [A validar: tresorer]. Està escrita a partir de les pantalles que hi ha avui. Les parts que encara no estan fetes ho diuen i porten la tasca que les farà. Les regles són al [pla, secció M05b](../planning.md#M05b). Per a la conciliació del banc, vegeu la [guia de la tresoreria](guia-tresoreria.md).

**Cap cobrament real fins al nivell 2.** Mentre la plataforma és al nivell 1 (només recollir mètodes i mandats), no es pot generar cap remesa ni cobrar res de debò (decisions 025 i 042; [P-M05b-I](../planning.md#M05b-5-processos)).

## 1. Pagaments i «a revisar»
La pantalla **Pagaments i «a revisar»** (adreça `pagaments/` de l'administració; encara no és al menú) mostra:
- **A revisar:** els pagaments que necessiten una persona, amb el motiu. Per exemple, una notificació del proveïdor que no quadra amb cap pagament, o una transferència conciliada sense rebut.
- **Tots els intents de pagament**, amb filtre per estat.

**Targeta guardada.** Ara per ara, el cobrament automàtic és **apagat**: els socis poden guardar la targeta i triar-la, però no es cobra res fins que s'encengui (amb el proveïdor real). Quan s'encengui, cada dia a les 5 del matí la plataforma cobrarà amb la targeta guardada les quotes vençudes dels socis que l'han triada, una sola vegada per quota, i només les vençudes fa com a molt 7 dies (ajust; [P-302](../decisions/pendents.md)). Les més antigues no es cobren amb la targeta: el soci rep el correu per pagar-les des de la pantalla i surten a «a revisar», sense correu per a cadascuna. Sempre que una quota no es cobra amb la targeta, reps un correu amb la quota, el càrrec i el motiu, i si el motiu és del soci (el banc la denega, demana autenticació o la targeta ja no serveix), el soci rep el correu per pagar-la d'una altra manera. Si el soci espera una transferència, no es cobra la targeta. Els intents hi surten com a «Targeta guardada» i el pagament, com a «Targeta». Al nivell 1 no es cobra res. Tots els casos són a la [taula d'estats finals](../estat/M05b.md#estats-finals-targeta-guardada).

**Tancar un intent «a revisar».** Quan ja l'has revisat (i, si calia, has fet la devolució, el pagament a mà o la conciliació a la seva pantalla), prem **Tanca** a la seva fila, tria **Pagat** (el proveïdor l'ha cobrat: es registra el pagament, el rebut i l'ingrés) o **Fallit** (no s'ha cobrat: no es mou cap diner), escriu una **Nota** (què has comprovat i què se n'ha fet, sense dades personals: el número de càrrec ja identifica el cas; 500 caràcters com a molt) i prem **Sí, tanca'l**. La nota és obligatòria i queda al registre d'activitat. Si el càrrec ja estava pagat per una altra via, «Pagat» es rebutja: tria «Fallit» i fes-ne la devolució. L'intent surt de «A revisar» i passa a **Tancats**, amb la decisió, la nota i qui l'ha tancat. Una decisió no es desfà; si després arriba una confirmació del proveïdor d'un càrrec ja pagat, l'intent torna a «A revisar» i es torna a decidir. Una confirmació que arriba tard d'un pagament fallit, caducat o abandonat el dona per pagat sola si el càrrec encara és pendent ([097](../decisions/097-respostes-del-propietari-a-les-preguntes-obertes-del-18-11-2026.md)). Les notificacions del proveïdor sense intent encara no es poden tancar ([P-378](../decisions/pendents.md)). El nom de qui paga només el veu qui té el permís de dades personals ([P-247](../decisions/pendents.md)).

## 2. Fer una remesa de quotes domiciliades
Pantalla **Remeses** (adreça `pagaments/remeses/` de l'administració; encara no és al menú) ([P-M05b-E](../planning.md#M05b-5-processos)).
1. A **Nova remesa**, escriu el **Període** (una etiqueta per trobar-la, per exemple «2026-12») i la **Data de cobrament**. La data ha de deixar temps per a l'avís previ: la pantalla proposa la primera data possible i no n'accepta cap d'anterior.
2. Prem **Previsualitza**. Hi veus quants **rebuts** hi entren, l'**import total** i, a sota, les **quotes que no entren i per què**: dades personals esborrades, sense mandat actiu, no ha triat la domiciliació, o té un pagament en curs o en una altra remesa.
3. Si està bé, prem **Sí, crea la remesa**. Si canvies la data, cal tornar a previsualitzar.

Hi entren les quotes pendents dels socis que han triat la domiciliació i tenen un mandat actiu ([regles](../planning.md#M05b-7-regles)). Quines quotes i quin període exactament: [P-230](../decisions/pendents.md).

## 3. Avisos previs
En crear la remesa, cada deutor rep l'avís previ per correu, amb l'IBAN emmascarat. El termini de l'avís és un ajust (14 dies d'entrada). El text és provisional [A validar: junta]. Si hi ha una campanya de mandats oberta, els socis convidats que encara no han triat com paguen reben el darrer recordatori de la campanya ([guia de mandats](guia-mandats.md#2-la-campanya-de-mandats)).
- La remesa surt com a **Esborrany: falten avisos** fins que tots s'han enviat, i llavors com a **Avisada**.
- Al detall de la remesa, la columna **Avís previ** diu a qui falta. Prem **Torna a enviar els avisos que falten**.
- Un soci sense adreça de correu: [P-232](../decisions/pendents.md).

## 4. Descarregar el fitxer per al banc
Al detall de la remesa, prem **Descarrega el fitxer pain.008**. El fitxer es genera a cada descàrrega i no es desa a la plataforma.

**El fitxer porta els IBAN sencers.** Puja'l a la banca en línia i esborra'l del dispositiu el mateix dia, sense enviar-lo per correu ni deixar-lo en carpetes sincronitzades (decisió [044](../decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md)). Cada descàrrega queda al registre amb l'empremta del fitxer. La versió del fitxer que demana el banc s'ha de verificar [A verificar: P-233].

## 5. Marcar la remesa com a enviada i casar l'abonament del banc
Encara no es pot fer des de la plataforma [pendent: T-M05b-11]. Quan hi sigui, marcar-la com a enviada demanarà confirmar que has esborrat el fitxer, i l'abonament del banc es casarà a la conciliació com una liquidació ([P-M05b-E, passos 6 a 8](../planning.md#M05b-5-processos)).

## 6. Rebuts retornats
Pantalla **Retornats** (adreça `pagaments/retornats/` de l'administració) ([P-M05b-F](../planning.md#M05b-5-processos), [regles](../planning.md#M05b-7-regles)). Hi tens dues maneres de registrar els rebuts que el banc ha tornat:
- **D'un en un:** a **Registra un retorn**, escriu la **Referència del rebut** (l'identificador d'extrem a extrem que surt a l'extracte o al fitxer del banc), el **Codi de motiu** (per exemple AM04) i, si n'hi ha, la **Comissió de retorn**. Prem **Registra el retorn**.
- **Amb el fitxer del banc:** a **Importa el fitxer de retornats del banc**, tria el fitxer XML de retornats (pain.002) i prem **Previsualitza**. La taula diu què passarà amb cada rebut: **Es registrarà**, **Ja registrat** (no es torna a registrar), **Cap rebut amb aquesta referència** o **No quadra** (el rebut no consta com a cobrat o l'import és diferent). Prem **Confirma els retorns**: es registren tots els que estan a punt o, si mentrestant n'ha canviat algun, cap. Llavors torna a pujar el fitxer. El fitxer no es desa. El format que envia el banc de debò encara està per confirmar [A verificar: banc, P-45 punt 5].

En registrar un retorn, la quota queda retornada, la tresoreria apunta la sortida i la comissió, i el soci rep l'avís. Segons el motiu, la plataforma proposa:
- **Reintent** (fons insuficients, AM04): la quota torna a la remesa següent. Quantes vegades com a molt és un ajust (2 d'entrada).
- **Alternativa de pagament** (la resta de motius): el soci rep un enllaç per pagar d'una altra manera. Amb compte tancat o sense mandat (AC04, MD01), el mandat queda bloquejat i el soci rep també l'enllaç per signar-ne un de nou.

Els que esperen la teva decisió surten a **Per decidir**. Si no queda cap reintent possible, l'alternativa s'aplica i s'envia en registrar-lo ([P-292](../decisions/pendents.md)). Quins codis proposen un reintent i quins bloquegen el mandat ho pots canviar a **Ajustos** > **Ajustos de pagaments**: **Codis de retorn que proposen un reintent** i **Codis de retorn que bloquegen el mandat**, de quatre lletres o xifres, separats per comes, espais o punts i comes. La plataforma els desa en majúscules, ordenats i separats per comes (per exemple, «md01 ac04» queda «AC04, MD01»). Un codi no pot ser a totes dues llistes: per moure'l, primer treu-lo de la que és. Els codis que no són a cap llista proposen l'alternativa. El canvi val per als retorns que registris a partir d'aquell moment. Els valors inicials són provisionals fins que el banc confirmi quins codis arriben ([P-291](../decisions/pendents.md)).

## 7. Devolucions
Tornar diners a un soci (una devolució que inicia el club) encara no es pot fer des de la plataforma [pendent: T-M05b-13]. El procés previst és a [P-M05b-G](../planning.md#M05b-5-processos). Mentrestant, una devolució es fa fora de la plataforma i s'ha d'anotar quan la funció hi sigui.

## 8. Mandats
La pantalla **Pagaments: mètodes i mandats** (al menú) mostra els mandats dels socis, sempre amb l'IBAN emmascarat. Amb **Revoca…**, el motiu i **Sí, revoca'l** es revoca un mandat: no es cobrarà cap quota més amb aquest mandat i el soci rep un correu. El teu propi mandat no el pots revocar des de l'administració, només des del teu compte personal. La signatura dels mandats per part dels socis està apagada fins que la junta aprovi el text ([ajuda per als socis](ajuda-socis-pagaments.md#3-el-mandat-de-domiciliació)).

La campanya de mandats, qui té quin mètode i els estats d'un mandat són a la [guia de mètodes, mandats i campanya](guia-mandats.md).
