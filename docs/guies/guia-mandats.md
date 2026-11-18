# Guia del tresorer: mètodes de pagament, mandats i campanya

**Per a qui és:** el tresorer. **Estat:** esborrany de la T-M05a-21 [A validar: tresorer]. Està escrita a partir de les pantalles que hi ha avui. Les parts que encara no estan fetes ho diuen i porten la tasca que les farà. Les regles són al [pla, secció M05a](../planning.md#M05a-5-processos) i les [regles de negoci](../planning.md#M05a-7-regles). Per a remeses, retornats i devolucions, vegeu la [guia de cobraments](guia-cobraments.md); per al que veu el soci, l'[ajuda per als socis](ajuda-socis-pagaments.md).

## 1. Abans de començar: el nivell 1
En el nivell 1 la plataforma **només recull com pagarà cada soci i els seus mandats**. No es cobra res de debò ni es pot fer cap remesa (decisions 025 i 042; [P-M05a-F](../planning.md#M05a-5-processos)). Passar al nivell 1 demana l'autorització escrita de la junta.

Avui **la signatura del mandat està apagada**: els socis no poden signar cap mandat ni es pot obrir cap campanya. S'encendrà quan la junta aprovi el text del mandat i el de la invitació (T-M05a-01) i el banc confirmi l'identificador de creditor del club. Encendre-la és configuració del servidor, no una opció de la pantalla.

## 2. La campanya de mandats
Al menú, **Pagaments: campanya de mandats**. Serveix perquè cada soci actiu triï com pagarà la quota abans de la primera remesa ([P-M05a-E](../planning.md#M05a-5-processos)). Per veure-la cal el permís de veure mètodes i mandats; per obrir, enviar i tancar, el d'enviar la campanya. Tots dos els tenen el Tresorer i l'Administrador.

**El recompte.** A dalt hi ha quants socis actius han triat **Domiciliació**, **Targeta guardada** o **Pagar cada vegada**, i quants són **Sense resposta**. Només són xifres: cap nom ni cap dada bancària.

**Si no es pot enviar.** La pantalla diu **No es pot enviar cap campanya** i el motiu: la signatura del mandat no està activada, falta l'identificador de creditor o falta publicar el text de la invitació. Mentre surti, no hi ha cap botó per obrir ni enviar.

**Pas a pas**
1. **Obrir.** Escriu el **Nom de la campanya** (per exemple «Mandats 2027») i prem **Obre la campanya**. Només hi pot haver una campanya oberta alhora.
2. **Revisar.** La pantalla mostra quants socis **Per convidar** hi ha (socis actius que encara no han triat cap mètode), quants són **Sense correu** i quina versió del text s'enviarà. El text sencer no surt a la pantalla ([P-306](../decisions/pendents.md)).
3. **Enviar.** Prem **Envia N invitacions…** i després **Sí, envia-les**. Les invitacions surten per la cua de correu, amb l'assumpte «Com vols pagar la quota del C.R.I.S.?» i l'enllaç a **Com pago la quota**. Cada soci la rep una sola vegada: si tornes a prémer el botó més endavant, només es convida qui ha entrat després (per exemple, un soci nou) i encara no ha triat.
4. **Recordatoris.** Surten sols, cada dia, a qui encara no ha triat. Els dies des de la invitació **són un ajust**: d'entrada, 7 i 14 dies. El canvies a **Ajustos**, apartat de pagaments ([RN-M05a-14](../planning.md#M05a-7-regles)). Qui ja ha triat no en rep cap. Quan confirmes una remesa (vegeu la [guia de cobraments](guia-cobraments.md)), qui encara no ha triat rep **el darrer recordatori**, amb la data de cobrament, i després ja no en rep cap més. Surt un sol cop per campanya, encara que facis més remeses.
5. **Seguir el recompte** fins a la data de la primera remesa. Qui no triï res pagarà la quota amb targeta, Bizum o transferència quan es generi ([RN-M05a-15](../planning.md#M05a-7-regles)).
6. **Tancar.** Prem **Tanca la campanya…** i després **Sí, tanca-la**. Un cop tancada no surt cap invitació ni cap recordatori més. Després en pots obrir una altra, que tornarà a convidar qui encara no hagi triat.

**Socis que la invitació no arriba**
- **Sense correu:** la plataforma no els pot convidar. La pantalla diu que els atén la secretaria ([P-199](../decisions/pendents.md)).
- **Sense compte personal activat:** reben la invitació, però per triar han d'entrar al seu compte. Què es fa amb ells és la [P-198](../decisions/pendents.md).

**Encara no està fet:** l'avís dins l'app (només surt el correu; encara no hi ha servei d'avisos).

## 3. Qui té quin mètode
Al menú, **Pagaments: mètodes i mandats**. Hi surten tots els socis actius amb el **Mètode** triat, el **Mandat o targeta** i l'**IBAN** emmascarat. Amb el filtre **Mètode** (Tots, domiciliació, targeta guardada, pagar cada vegada o Sense resposta) i **Filtra** veus només un grup; **Treu els filtres** els torna a mostrar tots. Si el teu permís és només de consulta, només veus si cada soci **Té mètode** (sí o no).

**Atenció:** la columna **Mandat o targeta** només mostra el mandat **actiu**. Un soci amb «domiciliació» i un guió (—) vol dir que el seu mandat ja no és actiu (caducat o bloquejat, vegeu el punt 4): no entrarà a la remesa fins que en signi un de nou. El recompte de la campanya també el compta a «Domiciliació» ([P-305](../decisions/pendents.md)).

**Targeta guardada:** feta contra el proveïdor de proves; amb el real, depèn que permeti guardar targetes ([P-45](../decisions/pendents.md), punt 6), i si no ho permet els socis no la veuen com a opció. La columna **Mandat o targeta** mostra els quatre darrers dígits i la caducitat; ni tu ni el soci no veieu mai el número. Cada soci té com a molt una targeta activa: si en guarda una de nova, l'anterior queda esborrada ([P-297](../decisions/pendents.md)).

## 4. Els estats d'un mandat
- **Actiu:** el soci l'ha signat i es pot fer servir a les remeses. Cada soci en té com a molt un ([RN-M05a-02](../planning.md#M05a-7-regles)).
- **Revocat:** l'ha revocat el soci des del seu compte o tu a petició escrita. Quan el soci canvia d'IBAN, l'anterior queda revocat amb el motiu «substituït». El soci passa a «pagar cada vegada».
- **Caducat:** han passat 36 mesos sense cap cobrament. Ho fa una tasca diària i el soci rep un correu per signar-ne un de nou ([RN-M05a-08](../planning.md#M05a-7-regles)).
- **Bloquejat:** el banc ha retornat un rebut perquè el compte és tancat o no hi ha mandat (vegeu [Rebuts retornats](guia-cobraments.md#6-rebuts-retornats)), o s'han esborrat les dades de la persona (RGPD). Un mandat bloquejat no es revoca, no caduca ni es torna a activar: el soci n'ha de signar un de nou.

**Revocar a petició escrita del soci:** des de **Pagaments: mètodes i mandats**, amb **Revoca…**. Els passos són a la [guia de cobraments](guia-cobraments.md#8-mandats).

**Si el mandat revocat ja tenia un rebut al banc** (en una remesa enviada, o avisada amb el fitxer ja descarregat), et ve un correu amb la referència del mandat i la remesa ([RN-M05a-09](../planning.md#M05a-7-regles)). El banc presentarà el rebut igualment: mira si encara el pots retirar o, si es cobra, torna l'import al soci. Si el banc ho permet és [A verificar: banc].

## 5. L'IBAN: què no veuràs mai
- A totes les pantalles l'IBAN surt **emmascarat**: el país i els quatre últims caràcters, per exemple «ES … 1234» ([P-121](../decisions/pendents.md)). Ningú no el veu sencer, tampoc l'administrador.
- No surt mai sencer als correus, al registre d'activitat, a les exportacions ni als informes d'error (decisió [044](../decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md); [RN-M05a-06](../planning.md#M05a-7-regles)). L'única excepció és el fitxer de la remesa per al banc ([guia de cobraments](guia-cobraments.md#4-descarregar-el-fitxer-per-al-banc)).
- Si un soci t'envia l'IBAN per correu o en paper, no l'apuntis enlloc: demana-li que signi el mandat ell mateix des del seu compte.

## 6. Què encara no es pot fer
- Signar mandats i obrir la campanya: apagat fins que la junta aprovi els textos [pendent: T-M05a-01].
- Esborrar la targeta guardada [pendent: P-132] i cobrar-hi la quota [pendent: T-M05b-15].
- Connectar el proveïdor de pagaments real en mode de proves [pendent: T-M05a-05].
- Monitoratge, alertes i marxa enrere del flux de mandats, necessaris per al nivell 1 [pendent: T-M05a-19].
- La importació final de Cluber [pendent: T-M05a-20]. Els mandats de Cluber no s'importen ([RN-M05a-16](../planning.md#M05a-7-regles)).
