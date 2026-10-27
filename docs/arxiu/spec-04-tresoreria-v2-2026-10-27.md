# Especificació 04 — Tresoreria, part mínima

- **Arxivada el 27/10/2026** (decisió 047): la font vigent és [`docs/planning.md`, M04](../planning.md#M04).
- **Versió:** 2 · 27/10/2026
- **Estat:** la versió 1 es va aprovar amb canvis el 27/10/2026; aquesta versió els incorpora. L'annex C és l'esborrany de `tasks.md`; `plan.md` i `data-model.md` són el pas següent.
- **Formalitat:** completa, perquè són finances (metodologia §7).
- **Revisió:** el tresorer i l'equip (metodologia §6).
- **Ordre:** tercer mòdul de la fase 1 segons la [decisió 024](../decisions/024-abast-minim-i-ordre-per-deixar-cluber.md): 00 → 01 → **04 mínim** → 05a → 05b. Al pla del repositori anterior es deia «M05a, tresoreria: nucli».
- **Abast:** el de l'arquitectura §9.1 per a la 04: comptes (banc, caixa, trànsit del proveïdor), moviments immutables, ingressos automàtics, comissions, devolucions i retorns com a moviments nous, departaments i centres de cost, i conciliació amb l'extracte en CSV.

> **Proveïdor de cobrament.** Totes les dades es tracten només dins la UE ([035](../decisions/035-dades-nomes-dins-ue.md)) i Stripe queda descartat ([042](../decisions/042-proveidors-substituits-pel-requisit-ue.md)). El proveïdor es tria segons la [043](../decisions/043-proveidor-de-pagaments-dins-la-ue.md): primer el TPV virtual del banc del club (CaixaGuissona via PaynoPain [A verificar]); si no, la millor alternativa verificada. Aquesta spec parla de «proveïdor de cobrament» i d'un «compte de trànsit» per proveïdor, i no en depèn. Els llocs on el proveïdor canvia alguna cosa porten la marca **[Proveïdor]**.

**Canvis respecte a la versió 1**
1. Revisor: el tresorer. Hi ha un sol rol de tresorer i es tracta com una sola persona; no hi ha doble aprovació de pagaments (queda com a pregunta opcional futura, P-48).
2. QT-02 (proveïdor) se substitueix per la decisió 043. La tasca T13 (liquidacions) és obligatòria.
3. QT-04 resolta: transició «pagat → pendent» només per a transferències conciliades amb el càrrec equivocat ([045](../decisions/045-correccio-transferencia-conciliada-per-error.md)).
4. QT-05 resolta: l'excés d'una transferència es retorna pel banc; no hi ha saldo a favor ni pagaments parcials.
5. La matriu de rols inclou els rols del mapa v8 que no són a la spec 00 (§2.1).
6. Annex D nou: requisits d'experiència de pagament per a la spec 05b.
7. Domiciliació SEPA pròpia: si s'aplica la [044](../decisions/044-domiciliacio-sepa-iban-i-mandat-xifrats.md), la plataforma guarda l'IBAN xifrat al mandat (mòdul 05a), mai a la 04.

## Com llegir aquesta spec

Es fan servir les mateixes abreviatures que a la [spec 00](../../specs/00-base-comuna/spec.md) (CLAUDE, CTX, F, ARQ, CK, V-nn, Q-nn). Els identificadors d'aquesta spec porten una **T** (tresoreria) per no confondre'ls amb els de la 00: HU-T01, CA-T01.1, RN-T01, LT1, VT-01 i QT-01.

Regles de la 00 que aquesta spec **no canvia** ([decisió 027](../decisions/027-estructura-basica-de-carrec-i-pagament.md), RN-76): imports en cèntims i positius (RN-60), res s'esborra (RN-61), departament obligatori (RN-62 a RN-65), tipus i estats del càrrec (RN-66, RN-67), mètodes (RN-68, RN-69), cap IBAN ni targeta (RN-70), un càrrec no passa a pagat pel navegador (RN-71), registre manual bloquejat per P-12 (RN-72), devolucions com a moviment nou (RN-73).

---

## 1. Context i objectiu

### 1.1 Context
- Avui els diners del club es porten en diverses eines que es creuen a mà, sense visió de la tresoreria (CTX §2).
- Cluber cobra les quotes pel seu compte i ingressa al club l'import menys un percentatge (CTX §3). Quan es deixi Cluber, el club cobrarà directament i haurà de quadrar què ha cobrat, què ha pagat de comissions i què ha arribat al banc.
- La 00 ja té el **càrrec** i el **pagament** (estructura bàsica, RN-60 a RN-76) i la **importació de l'extracte bancari** (HU-21). La casació de les línies amb els pagaments és d'aquesta spec.

### 1.2 Objectiu
Que el tresorer sàpiga, en tot moment i sense creuar fulls de càlcul:
1. quant hi ha a cada compte (banc, caixa i trànsit del proveïdor);
2. de quin departament és cada euro que entra o surt;
3. quins cobraments ja han arribat al banc i quins no;
4. que cap moviment s'ha modificat ni esborrat.

### 1.3 Què ofereix la 04 a la resta de mòduls
Serveis, no accés directe als models (CLAUDE, «una app no escriu als models d'una altra»):

| Servei | Qui el crida | Què fa |
|---|---|---|
| `registrar_cobrament(pagament)` | 05b (confirmació verificada del proveïdor) i la mateixa 04 (conciliació d'una transferència) | Crea l'ingrés del pagament. Idempotent |
| `registrar_comissio(pagament o liquidació, import)` | 05b i la 04 (en conciliar una liquidació) | Crea la despesa de comissió al departament de la [decisió 013](../decisions/013-imputacio-comissions.md) |
| `registrar_devolucio(pagament, import, motiu)` i `registrar_retorn(pagament)` | 05b | Crea el moviment de signe contrari i, si n'hi ha, la comissió |
| `referencia_transferencia(càrrec)` | 05b (pantalla de pagament per transferència) | Retorna la referència única del càrrec (RN-T20) |
| `registrar_liquidacio(proveïdor, dades)` | 05b (notificació o fitxer de liquidació del proveïdor) | Crea la liquidació i la llista dels cobraments que conté (RN-T21) |
| `saldo(compte, data)` i `moviments(filtres)` | 08 Dashboard i 01 (rebuts) | Consultes només de lectura |

---

## 2. Rols i permisos

Matriu provisional, igual que la de la 00 (P-04, Q-01). **Sí** = pot fer-ho; **Consulta** = només veure; **—** = no.

| # | Acció | Soci | Instructor | Secretaria | Resp. cursos i sortides | Resp. material | Tresorer | Dept. Història | Administrador | Font |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Veure comptes, saldos i moviments | — | — | — | — | — | Sí | — | Sí | F §2 («Registrar ingressos, despeses i factures») |
| T2 | Crear i desactivar comptes de tresoreria | — | — | — | — | — | Sí | — | Sí | Proposta |
| T3 | Mantenir departaments i centres de cost | — | — | — | — | — | [A validar] | — | Sí | 00, M7 |
| T4 | Conciliar línies de l'extracte i desfer una conciliació | — | — | — | — | — | Sí | — | [A validar] | 00, M9; ARQ §4.6 |
| T5 | Anul·lar un moviment amb motiu (contramoviment) | — | — | — | — | — | Sí | — | Sí | RN-61 |
| T6 | Registrar un traspàs entre comptes propis (per exemple, ingressar l'efectiu al banc) | — | — | — | — | — | Sí | — | Sí | ARQ §4.7 |
| T7 | Registrar un arqueig de caixa | — | — | — | — | — | Sí | — | Sí | ARQ §4.7 |
| T8 | Excloure una línia de l'extracte de la conciliació, amb motiu | — | — | — | — | — | Sí | — | — | Proposta |
| T9 | Exportar moviments en CSV (per a la gestoria) | — | — | — | — | — | Sí | — | Sí | Proposta |
| T10 | Veure la llista «a revisar» | — | — | — | — | — | Sí | — | Sí | ARQ §4.2, punt 4 |
| T11 | Veure l'estat de les quotes (pagada o no) sense imports de tresoreria | — | — | Consulta | — | — | Sí | — | Sí | F §2 (secretaria: altes i baixes) |
| T12 | Veure els seus càrrecs, pagaments i rebuts | Propi | Propi | Propi | Propi | Propi | Propi | Propi | Propi | 00, §2.5 (compte personal) |

### 2.1 Rols del mapa v8 que no són a la spec 00
La spec 00 té 8 rols (P-04). El mapa de la plataforma v8 en té més. Per a aquesta spec no tenen cap permís:

| Rol del mapa v8 | T1-T11 | T12 | Nota |
|---|---|---|---|
| Visitant (sense sessió) | — | — | Cap endpoint de tresoreria és públic |
| Participant no soci (convidat, decisió 021) | — | Propi, només amb l'enllaç de convidat | 00, §2.5 |
| Junta | — | — | Si ha de veure saldos o el dashboard: P-04 [A validar] |
| Resp. comunicació | — | — | — |
| Resp. botiga | — | — | Botiga fora d'abast ara |

Hi ha **un sol rol de tresorer** i es tracta com una sola persona. Cap acció d'aquesta spec no necessita una segona aprovació; si la junta la volgués més endavant (per exemple, per a devolucions a partir d'un import), és la pregunta opcional P-48.

**Per objecte:** el tresorer veu les dades de les persones que calen per cobrar i conciliar (nom, número de soci, concepte i import), no el perfil sencer (00, §2.5; Q-01). L'extracte bancari pot portar noms de persones que no són del club (per exemple, qui fa una transferència en nom d'un altre): aquestes dades només es veuen a la pantalla de conciliació.

---

## 3. Històries d'usuari

**Comptes i saldos**
- **HU-T01.** Com a tresorer, vull tenir els comptes del club a la plataforma (cada compte bancari, la caixa i un compte de trànsit per a cada proveïdor de cobrament), per veure el saldo de cadascun.
- **HU-T02.** Com a tresorer, vull que el saldo de cada compte el calculi la plataforma a partir dels moviments, per no haver-lo de quadrar a mà.

**Moviments automàtics**
- **HU-T03.** Com a tresorer, vull que cada cobrament confirmat generi sol el seu ingrés al compte i al departament correctes, per no apuntar res dues vegades.
- **HU-T04.** Com a tresorer, vull que cada comissió del proveïdor es registri com a despesa del departament que toca (decisió 013), per saber quant costa cobrar.
- **HU-T05.** Com a tresorer, vull que una devolució o un rebut retornat generi un moviment nou de signe contrari, sense tocar l'original, per poder justificar-ho tot.

**Correccions**
- **HU-T06.** Com a tresorer, vull anul·lar un moviment erroni amb un motiu, de manera que en quedi rastre, per corregir sense esborrar.
- **HU-T07.** Com a tresorer, vull registrar un traspàs entre comptes propis (per exemple, l'efectiu que ingresso al banc), per tenir la caixa i el banc quadrats.
- **HU-T08.** Com a tresorer, vull registrar l'arqueig de la caixa i veure la diferència amb el saldo calculat, per detectar errors.

**Conciliació**
- **HU-T09.** Com a tresorer, vull que la plataforma em proposi a quin pagament o liquidació correspon cada línia de l'extracte importat, per només haver de confirmar.
- **HU-T10.** Com a tresorer, vull que en confirmar una transferència amb la referència i l'import correctes el càrrec passi a pagat i es creï l'ingrés, per no haver de marcar-ho a part.
- **HU-T11.** Com a tresorer, vull casar l'abonament agrupat del proveïdor amb els cobraments que conté, per saber que el que s'ha cobrat ha arribat al banc.
- **HU-T12.** Com a tresorer, vull excloure amb un motiu les línies de l'extracte que no són de l'abast mínim (per exemple, una despesa amb factura), per tenir la conciliació neta.
- **HU-T13.** Com a tresorer, vull una llista dels pagaments i les línies «a revisar», per resoldre les diferències.

**Departaments i consultes**
- **HU-T14.** Com a tresorer, vull que els departaments puguin tenir centres de cost (per exemple, «General / Quotes de socis»), per justificar-ho per departament.
- **HU-T15.** Com a tresorer, vull filtrar els moviments per compte, departament, centre de cost i període, i exportar-los en CSV, per passar-los a la gestoria.

---

## 4. Criteris d'acceptació

### HU-T01 i HU-T02 Comptes i saldos
- **CA-T01.1** Donat una instal·lació nova, quan s'executen les migracions, llavors existeixen el compte «Caixa» i un compte bancari «Banc principal» (VT-01).
- **CA-T01.2** Donat un compte de tresoreria, quan es desa, llavors no hi ha cap camp que guardi un IBAN complet; només un nom i, si es vol, els quatre darrers dígits (RN-70; CA-15.6).
- **CA-T01.3** Donat un compte amb moviments, quan es vol esborrar, llavors es rebutja; es pot desactivar i un compte desactivat no admet moviments nous.
- **CA-T02.1** Donat un compte, quan es consulta el saldo a una data, llavors és la suma de les entrades menys les sortides amb data de valor fins a aquella data; cap pantalla permet escriure el saldo.
- **CA-T02.2** Donat un compte de trànsit d'un proveïdor, quan totes les liquidacions estan conciliades, llavors el seu saldo és la suma dels cobraments encara no liquidats.

### HU-T03 Ingrés automàtic
- **CA-T03.1** Donat un càrrec que passa a «pagat», quan la 05b o la conciliació criden `registrar_cobrament`, llavors es crea un sol ingrés amb l'import del pagament, el departament i el centre de cost del càrrec i el compte de RN-T08.
- **CA-T03.2** Donat un pagament que ja té ingrés, quan es torna a cridar `registrar_cobrament` (per exemple, per una confirmació repetida), llavors no es crea cap moviment nou i queda al registre com a repetició.
- **CA-T03.3** Donat un càrrec que no és «pagat», quan es crida `registrar_cobrament`, llavors es rebutja.
- **CA-T03.4** Donat una petició del navegador, quan intenta crear un ingrés, llavors es rebutja (RN-71).

### HU-T04 Comissions
- **CA-T04.1** Donat un cobrament d'una quota amb comissió del proveïdor, quan es registra la comissió, llavors és una sortida del compte de trànsit del proveïdor al departament «General / Quotes de socis» (013; RN-63).
- **CA-T04.2** Donat un cobrament d'una inscripció amb comissió, quan es registra, llavors la despesa va al departament i a l'activitat del càrrec (RN-64).
- **CA-T04.3** Donat un cobrament d'una llicència amb comissió, quan es registra, llavors va al departament que fixi la junta (RN-65; Q-19). Mentre no es fixi, va a «General / Llicències» marcat com a provisional (VT-04).
- **CA-T04.4** Donat una liquidació en què el proveïdor no detalla la comissió de cada cobrament **[Proveïdor]**, quan el tresorer la concilia, llavors la diferència entre el brut i el net es reparteix entre els cobraments de la liquidació en proporció a l'import (VT-05) i cada part va al departament del seu càrrec; el repartiment es mostra abans de confirmar.

### HU-T05 Devolucions i retorns
- **CA-T05.1** Donat un pagament amb ingrés, quan es registra una devolució total o parcial, llavors es crea una sortida nova pel mateix compte, departament i centre de cost; l'ingrés original no canvia (RN-73).
- **CA-T05.2** Donat una devolució, quan es registra, llavors la comissió original no es retorna: la despesa de comissió continua (013).
- **CA-T05.3** Donat un rebut domiciliat retornat, quan la 05b crida `registrar_retorn`, llavors es crea la sortida de l'import i, si n'hi ha, la comissió de retorn com a despesa del mateix departament.
- **CA-T05.4** Donat un pagament, quan la suma de les devolucions superaria l'import cobrat, llavors es rebutja.

### HU-T06 Anul·lació
- **CA-T06.1** Donat un moviment, quan el tresorer l'anul·la, llavors cal un motiu i es crea un contramoviment de sentit contrari amb el mateix import, compte, departament i centre de cost, lligat a l'original. L'original queda marcat com a anul·lat i no desapareix de cap llistat.
- **CA-T06.2** Donat un moviment generat per un cobrament (ingrés automàtic), quan es vol anul·lar des de la tresoreria, llavors es rebutja: s'ha de fer amb una devolució (05b) o desfent la conciliació (CA-T10.4).
- **CA-T06.3** Donat qualsevol moviment, quan algú intenta modificar-ne o esborrar-ne un camp (a l'aplicació o amb una consulta directa a la base de dades), llavors es rebutja (RNF-T2).

### HU-T07 i HU-T08 Traspassos i arqueig
- **CA-T07.1** Donat un traspàs de Caixa a Banc, quan es registra, llavors es creen dos moviments enllaçats (sortida de la caixa i entrada al banc) amb el mateix import i sense departament (RN-T05).
- **CA-T07.2** Donat un traspàs, quan la línia de l'extracte de l'ingrés en efectiu es concilia, llavors es casa amb l'entrada al banc del traspàs.
- **CA-T08.1** Donat un arqueig amb un import comptat diferent del saldo calculat, quan es desa, llavors es mostra la diferència i no es crea cap moviment sol; el tresorer pot crear un ajust amb motiu, que va al departament «General» (VT-06).

### HU-T09 a HU-T13 Conciliació
- **CA-T09.1** Donat un extracte confirmat (HU-21 de la 00), quan s'obre la conciliació, llavors cada línia té un estat: pendent, proposada, conciliada o exclosa.
- **CA-T09.2** Donat una línia d'abonament que conté una referència de transferència vàlida (RN-T20) i el mateix import que el càrrec, quan es processa, llavors queda «proposada» amb aquell càrrec.
- **CA-T09.3** Donat una línia amb referència vàlida però un import diferent, o sense referència però amb un import que coincideix amb un sol càrrec pendent per transferència, quan es processa, llavors queda «a revisar» i no es proposa res automàticament.
- **CA-T10.1** Donat una línia proposada amb una transferència, quan el tresorer la confirma, llavors el càrrec passa a «pagat», es crea el pagament amb el mètode transferència i l'ingrés al compte bancari, i queda al registre d'activitat qui ho ha confirmat.
- **CA-T10.2** Donat una línia que paga diversos càrrecs (per exemple, dues quotes d'una família amb una sola transferència), quan el tresorer la casa amb aquests càrrecs i la suma coincideix exactament, llavors es pot confirmar; si no coincideix, no.
- **CA-T10.3** Donat una línia ja conciliada, quan es vol fer servir per a un altre càrrec, llavors es rebutja.
- **CA-T10.4** Donat una conciliació confirmada que no ha canviat l'estat de cap càrrec (per exemple, una liquidació), quan el tresorer la desfà amb motiu, llavors la línia torna a «pendent» i queda al registre.
- **CA-T10.5** Donat una transferència conciliada amb el càrrec equivocat, quan el tresorer ho corregeix amb motiu, llavors el càrrec passa de «pagat» a «pendent», el pagament queda anul·lat amb el mateix motiu, l'ingrés es compensa amb un contramoviment i la línia torna a «pendent»; tot queda al registre i res s'esborra ([045](../decisions/045-correccio-transferencia-conciliada-per-error.md)).
- **CA-T10.6** Donat un càrrec pagat amb targeta, Bizum o domiciliació, quan es demana «pagat → pendent», llavors es rebutja: es corregeix amb una devolució.
- **CA-T11.1** Donat una liquidació del proveïdor (abonament agrupat), quan la línia del banc té l'import net de la liquidació, llavors es proposa casar-la i, en confirmar-ho, es crea el traspàs del compte de trànsit al banc i, si cal, la comissió (CA-T04.4).
- **CA-T11.2** Donat una liquidació amb cobraments que no són a la plataforma, quan es concilia, llavors es marca «a revisar» i no es confirma fins que el tresorer ho resol.
- **CA-T12.1** Donat una línia de l'extracte que no és de l'abast mínim, quan el tresorer l'exclou, llavors cal un motiu, la línia passa a «exclosa» i no crea cap moviment.
- **CA-T13.1** Donat pagaments «a revisar» (ARQ §4.2, punt 4) o línies «a revisar», quan el tresorer obre la llista, llavors els veu tots amb el motiu; la llista buida diu «No hi ha res a revisar».

### HU-T14 i HU-T15 Departaments i consultes
- **CA-T14.1** Donat una instal·lació nova, quan s'executen les migracions, llavors existeixen el departament «General» i els seus centres de cost «Quotes de socis», «Llicències» (provisional, VT-04) i «Ajustos de caixa» (VT-06). El nom complet es mostra com «General / Quotes de socis» (RN-74; Q-17).
- **CA-T14.2** Donat un centre de cost desactivat, quan es crea un càrrec o un moviment nou, llavors no es pot triar (RN-75).
- **CA-T15.1** Donat un filtre per període, compte, departament o centre de cost, quan s'exporta en CSV, llavors el fitxer té data, compte, concepte, departament, centre de cost, entrada, sortida i referència, en cèntims convertits a euros amb dos decimals, i cap dada personal més enllà del concepte (RNF-T4).

---

## 5. Regles de negoci

### 5.1 Comptes
| ID | Regla | Font |
|---|---|---|
| RN-T01 | Hi ha tres tipus de compte: **bancari**, **caixa** i **trànsit** (un per proveïdor de cobrament) | ARQ §4.1; 027 |
| RN-T02 | El saldo es calcula sempre a partir dels moviments; no es desa com a camp editable | RN-61; proposta |
| RN-T03 | Cap compte guarda l'IBAN complet. L'IBAN que es mostra per pagar per transferència és configuració (`CLUB_IBAN_TRANSFERENCIES`) | RN-70; ARQ §5 |
| RN-T04 | Un compte amb moviments no s'esborra: es desactiva | RN-61 |

### 5.2 Moviments
| ID | Regla | Font |
|---|---|---|
| RN-T05 | Un **moviment** té compte, sentit (entrada o sortida), import enter positiu en cèntims, data de valor, data de registre, tipus, concepte, departament i centre de cost (excepte els traspassos), i l'origen (pagament, liquidació, línia d'extracte, arqueig o moviment anul·lat) | RN-60; RN-62; ARQ §4.1 |
| RN-T06 | Tipus de moviment: **ingrés de cobrament**, **comissió**, **devolució**, **retorn**, **traspàs** (dues potes enllaçades), **ajust d'arqueig** i **contramoviment** (anul·lació) | ARQ §4.1, §4.3-4.7 |
| RN-T07 | Els moviments **no es modifiquen ni s'esborren** mai. Una correcció és un contramoviment amb motiu (CA-T06.1) | CLAUDE; RN-61 |
| RN-T08 | Compte de l'ingrés segons el mètode del pagament: domiciliació, targeta i Bizum → compte de **trànsit** del proveïdor; transferència → compte **bancari**; manual → **caixa** o compte bancari, segons indiqui qui el registra (quan P-12 es resolgui) | ARQ §4.1, §4.6 i §4.7 |
| RN-T09 | Cada pagament genera com a màxim **un** ingrés de cobrament. La base de dades ho garanteix (unicitat per pagament) | ARQ §4.2, punt 5 |
| RN-T10 | L'ingrés porta el departament i el centre de cost del càrrec. La comissió va on diu la 013: quotes → «General / Quotes de socis»; inscripcions → activitat i departament de l'activitat; llicències → Q-19 | 013; RN-63 a RN-65 |
| RN-T11 | Les devolucions i els retorns són moviments nous de sortida; la comissió no es recupera. La suma de devolucions no pot superar l'import cobrat | RN-73; 013 |
| RN-T12 | Els traspassos entre comptes propis no són ni ingrés ni despesa i no porten departament | Proposta (RN-62 parla d'ingressos i despeses) |
| RN-T13 | Cada moviment, anul·lació, conciliació, exclusió i arqueig queda al registre d'activitat de la 00 (qui, quan, què, valor anterior) | RN-50; CK C8 |

### 5.3 Conciliació
| ID | Regla | Font |
|---|---|---|
| RN-T14 | Les línies de l'extracte les importa la 00 (HU-21). La 04 les casa i no n'altera les dades | 00, HU-21 i RN-92 |
| RN-T15 | Estats d'una línia: **pendent** → **proposada** → **conciliada**; **pendent** → **exclosa** (amb motiu). Tots els estats poden passar a «a revisar», que és una marca, no un estat | Proposta |
| RN-T16 | Només el tresorer confirma una conciliació. La plataforma només proposa; mai concilia sola | ARQ §4.6; RN-71 |
| RN-T17 | Una línia es concilia una sola vegada. Pot casar amb un o més càrrecs, un o més moviments o una liquidació, sempre que la suma coincideixi exactament | Proposta |
| RN-T17b | **Pagaments de més o de menys per transferència:** no hi ha saldo a favor ni pagaments parcials. L'excés es retorna pel banc (transferència sortint registrada com a devolució amb motiu); un pagament de menys queda «a revisar» i el tresorer demana la diferència o retorna l'import | Aprovació de la v1 (QT-05) |
| RN-T18 | Una transferència només posa un càrrec en «pagat» si coincideixen la referència i l'import. Qualsevol altra coincidència és «a revisar» | ARQ §4.6 |
| RN-T19 | Una conciliació que ha passat un càrrec a «pagat» només es desfà amb la transició «pagat → pendent» de la 045: només per a transferències, amb motiu i registre | 045; RN-67 |
| RN-T20 | **Referència de transferència:** una per càrrec, única, amb el prefix `TRANSFER_REFERENCE_PREFIX` i un dígit de control, per exemple `CRIS-7K3Q9-4` (VT-03). Es genera la primera vegada que es demana i no canvia | ARQ §4.6 i §5 |
| RN-T21 | **[Proveïdor]** Una liquidació és l'abonament agrupat que el proveïdor fa al banc. Té import brut, comissions, import net, data i la llista de cobraments. Com arriba (notificació, fitxer o només l'extracte) no consta a la documentació pública de Paylands [A verificar: P-45]. Si el proveïdor no en dona el detall, el tresorer casa la línia del banc amb els cobraments del període | 043; `docs/integracio-paylands.md` §7 |

### 5.4 Departaments i centres de cost
| ID | Regla | Font |
|---|---|---|
| RN-T22 | Dos nivells: **departament** i **centre de cost**. Un càrrec o un moviment té sempre departament i, si el departament en té, centre de cost (VT-02) | 013 (el nom «General / Quotes de socis»); Q-17 |
| RN-T23 | La llista de departaments i centres de cost la fixa la junta; les úniques que existeixen des de l'inici són les de CA-T14.1 | RN-74 |

---

## 6. Entitats

Nivell de domini. Tipus, índexs i noms de codi: `data-model.md`, quan s'aprovi la spec.

| Entitat | Camps principals | Restriccions |
|---|---|---|
| **Compte de tresoreria** | nom; tipus (bancari, caixa, trànsit); proveïdor (només trànsit); quatre darrers dígits (opcional, només bancari); actiu | Cap IBAN complet. No s'esborra si té moviments |
| **Moviment** | compte; sentit (entrada, sortida); import en cèntims; data de valor; data de registre; tipus (RN-T06); concepte; departament; centre de cost; pagament (si escau); liquidació (si escau); moviment enllaçat (traspàs o anul·lació); anul·lat (sí o no); motiu; registrat per (compte o «sistema») | Import enter positiu. Departament obligatori excepte traspàs. Només s'hi afegeix: ni UPDATE ni DELETE (RNF-T2). Un sol ingrés de cobrament per pagament |
| **Liquidació del proveïdor** | proveïdor; identificador extern; data; import brut; comissions; import net; estat (rebuda, conciliada, a revisar) | Identificador extern únic per proveïdor |
| **Cobrament de la liquidació** | liquidació; pagament; import; comissió (si el proveïdor la detalla) | Un pagament només pot ser en una liquidació |
| **Conciliació** | línia d'importació (de la 00); objectes casats (càrrecs, moviments o liquidació); confirmada per; data; desfeta per; motiu de desfer | Una conciliació activa per línia. La suma dels objectes = import de la línia |
| **Estat de conciliació de la línia** | línia d'importació; estat (RN-T15); a revisar (sí o no) i motiu; motiu d'exclusió | La línia d'importació és de la 00 i no es modifica; l'estat viu a la 04 |
| **Arqueig** | compte (caixa); data; import comptat; saldo calculat; diferència; registrat per; ajust creat (si n'hi ha) | — |
| **Centre de cost** | departament; nom; actiu | Nom únic dins del departament |
| **Referència de transferència** | càrrec; referència; data de creació | Una per càrrec; referència única |

La 04 hi afegeix, sense canviar les regles de la 00 (027): al **càrrec**, el centre de cost; al **pagament**, el moviment d'ingrés que ha generat.

---

## 7. Casos límit, estats buits i errors

| # | Cas | Comportament esperat | Font |
|---|---|---|---|
| LT1 | La confirmació del proveïdor arriba dues vegades | Un sol ingrés (CA-T03.2) | RN-T09 |
| LT2 | Un soci fa una transferència sense referència | La línia queda «a revisar»; el tresorer la casa a mà amb el càrrec | CA-T09.3 |
| LT3 | Un soci paga per transferència més del que deu | «A revisar». El tresorer concilia el càrrec i retorna l'excés pel banc; la devolució es registra amb motiu | RN-T17b |
| LT4 | Un soci paga per transferència menys del que deu | «A revisar». No es concilia: el tresorer demana la diferència (una segona transferència que sumi l'import exacte es casa amb les dues línies) o retorna l'import | RN-T17b; RN-67 |
| LT5 | Una família paga dues quotes amb una transferència | Una línia, dos càrrecs (CA-T10.2) | RN-T17 |
| LT6 | Un soci paga per transferència un càrrec que ja s'ha pagat amb targeta | «A revisar». El tresorer fa una devolució de la transferència des del banc i la registra (ARQ §4.6) | RN-T18 |
| LT7 | El tresorer s'equivoca i concilia una transferència amb el càrrec d'una altra persona | Es corregeix amb la transició de la 045 (CA-T10.5) | 045 |
| LT8 | El proveïdor envia una liquidació amb un cobrament que no es troba | Liquidació «a revisar» (CA-T11.2) | ARQ §4.2, punt 4 |
| LT9 | Una comissió de liquidació no es pot repartir en cèntims exactes | El cèntim que sobra va al cobrament més gran (VT-05) | Proposta |
| LT10 | Es desactiva un departament amb càrrecs pendents | Els càrrecs existents el conserven; no es pot triar per a càrrecs nous | RN-75 |
| LT11 | L'extracte porta línies de despeses amb factura (fora de l'abast mínim) | El tresorer les exclou amb motiu; es tractaran a la resta de la 04 | CA-T12.1 |
| LT12 | Ningú no ha importat cap extracte | La conciliació mostra «Encara no hi ha cap extracte. Importa'n un des de Tresoreria → Extractes» | CK B9 |
| LT13 | Cap compte té moviments | Els saldos mostren 0,00 € i un text que explica d'on sortiran els moviments | Proposta |
| LT14 | Una persona demana l'esborrat RGPD i té moviments | Els moviments es conserven i la persona es bloqueja o s'anonimitza segons la 028; el concepte no ha de portar el nom (RNF-T4) | 028; RN-88 |

---

## 8. Requisits no funcionals

- **RNF-T1 Exactitud.** Tots els càlculs es fan amb enters (cèntims). Cap número de coma flotant en cap import ni en cap repartiment. Proves automàtiques de cada regla de càlcul (CK B1).
- **RNF-T2 Immutabilitat.** Els moviments, les conciliacions i els arqueigs només s'afegeixen. A més de la regla a l'aplicació, la base de dades rebutja UPDATE i DELETE a la taula de moviments (activador o permisos de l'usuari de l'aplicació). Prova que una consulta directa falla (CK C8).
- **RNF-T3 Traçabilitat.** Des de qualsevol moviment s'arriba al seu origen (pagament, càrrec, liquidació, línia de l'extracte o moviment anul·lat), i a l'inrevés.
- **RNF-T4 Mínim de dades.** El concepte d'un moviment no porta el nom de la persona, només el número de soci o la referència. L'exportació CSV no porta cap altra dada personal.
- **RNF-T5 Dades dins la UE.** La base de dades, les còpies i els fitxers de l'extracte es tracten només a la UE ([035](../decisions/035-dades-nomes-dins-ue.md)). Cap dada de tresoreria s'envia a serveis de fora de la UE (seguiment d'errors inclòs, decisió 011).
- **RNF-T6 Seguretat.** Permís per rol i per objecte a cada endpoint (CK C1). Tresorer i administrador entren amb TOTP (015). Cap acció de diners pel navegador sense sessió d'administració, excepte les consultes del compte personal (T12).
- **RNF-T7 Rendiment.** Volum esperat: uns quants milers de moviments a l'any. El saldo d'un compte es calcula en menys d'un segon amb 50.000 moviments (prova amb dades inventades).
- **RNF-T8 Accessibilitat i ús.** Pantalles d'administració segons el sistema de disseny (030): imports amb tipografia monoespaiada, alineats a la dreta i amb signe i color; els estats sempre amb símbol, text i color.
- **RNF-T9 Dades de prova.** Només dades inventades fora de producció (010), inclosos extractes inventats.

---

## 9. Fora d'abast

- **Resta de la 04** (fase 2): marge per activitat, despeses amb factura obligatòria, ajuts i justificació per departament, facturació i Verifactu (P-02), tancament de període, pressupostos.
- **05a i 05b:** integració amb el proveïdor de cobrament, webhooks, mandats, remeses, avís previ, reintents, pantalles de pagament. La 04 només ofereix els serveis de §1.3.
- **Registre manual de cobraments:** bloquejat per P-12 (RN-72). La 04 ja admet el compte de destinació (RN-T08).
- **Connexió directa amb el banc** (API de PSD2 o agregadors): l'extracte entra en CSV.
- **Imputació de despeses que no són comissions:** les línies de l'extracte que no siguin cobraments, liquidacions o traspassos s'exclouen amb motiu fins a la resta de la 04.
- **Monedes que no siguin l'euro.**

---

## 10. Valors proposats i preguntes obertes

### 10.1 Valors proposats
| ID | Tema | Proposta |
|---|---|---|
| VT-01 | Comptes inicials | «Caixa» i «Banc principal». El compte de trànsit es crea quan es configuri el proveïdor de cobrament |
| VT-02 | Departaments | Dos nivells: departament i centre de cost (resol Q-17 si la junta ho accepta) |
| VT-03 | Referència de transferència | Prefix, guió, cinc caràcters sense ambigüitats (sense 0, O, 1, I), guió i dígit de control (Luhn mod N). Exemple `CRIS-7K3Q9-4` |
| VT-04 | Comissions de llicències | Centre de cost «General / Llicències», provisional fins que la junta respongui Q-19 |
| VT-05 | Repartiment de comissions sense detall | Proporcional a l'import de cada cobrament; el cèntim que sobra, al cobrament més gran |
| VT-06 | Ajust d'arqueig | Departament «General», centre de cost «Ajustos de caixa», amb motiu obligatori |

### 10.2 Preguntes obertes
**Resoltes a la revisió de la v1**
| ID | Pregunta | Resolució |
|---|---|---|
| QT-01 | Qui revisa la spec | El tresorer |
| QT-02 | Proveïdor de cobrament | Substituïda per la [043](../decisions/043-proveidor-de-pagaments-dins-la-ue.md) |
| QT-04 | Corregir una transferència conciliada amb el càrrec equivocat | [045](../decisions/045-correccio-transferencia-conciliada-per-error.md) |
| QT-05 | Pagaments de més o de menys per transferència | RN-T17b |

**Junta**
| ID | Pregunta | Abans de |
|---|---|---|
| QT-03 | Llista de departaments i centres de cost (Q-17) | Dades reals |

**Tresoreria**
| ID | Pregunta | Abans de |
|---|---|---|
| QT-06 | Quants comptes bancaris té el club i a quin banc | Dades reals |
| QT-07 | Format de l'extracte (CSV o Norma 43, Q-24 de la 00) i fitxer de liquidacions del TPV: vegeu les preguntes al banc, P-45 | Pla |
| QT-08 | Si hi ha caixa en efectiu i cada quant es fa l'arqueig | Implementar HU-T08 |

---

## 11. Proves derivades

| Prova | Criteris | Requisit de la checklist |
|---|---|---|
| Ingrés automàtic: un sol ingrés per pagament, confirmacions repetides, càrrec no pagat, intent des del navegador | CA-T03.x | B1 (càlculs econòmics), C9 (pagaments) |
| Comissions per tipus de càrrec i repartiment proporcional amb cèntims que sobren | CA-T04.x; LT9 | B1 |
| Devolucions totals, parcials i de més; retorns amb comissió | CA-T05.x | B1 |
| Immutabilitat a l'aplicació i a la base de dades | CA-T06.3; RNF-T2 | C8 (registre d'activitat) |
| Saldos amb dades inventades grans (50.000 moviments) | CA-T02.x; RNF-T7 | B1 |
| Conciliació: referència i import exactes, sense referència, import diferent, una línia per a diversos càrrecs, línia ja usada, desfer | CA-T09.x a CA-T12.x; LT2 a LT8 | B9 (importacions) |
| Revisió automàtica del model: cap camp d'IBAN complet ni de targeta | CA-T01.2 | C9 |
| Matriu de rols de §2 convertida en proves | §2 | B4 (permisos) |
| Exportació CSV sense dades personals | CA-T15.1; RNF-T4 | H3 (RGPD) |

---

## Annex A — Dubtes i supòsits (per comprovar abans d'implementar)

| Dubte | Supòsit mentre no es decideix | Com es comprova | Risc si és erroni |
|---|---|---|---|
| Proveïdor de cobrament (043) | La 04 es fa sense dependre'n: trànsit genèric | Respostes del banc i de PaynoPain (P-45) | Baix per a la 04; alt per a la 05a i la 05b |
| El proveïdor detalla la comissió de cada cobrament? | Si no, repartiment proporcional (VT-05) | Documentació del proveïdor o del banc | Mitjà: imputació aproximada per departament |
| Format del CSV del banc | Columnes data, concepte, import i saldo (V-06 de la 00) | Mostra anonimitzada de l'extracte | Alt per a la conciliació |
| L'ingrés de la quota va a «General / Quotes de socis» (Q-18) | Sí | Junta | Baix |
| Hi ha transferències que paguen diversos càrrecs | Sí (famílies) | Tresoreria | Baix |

## Annex B — Seguretat (resum)

- Endpoints de tresoreria només per a comptes d'administrador amb rol tresorer o administrador, amb TOTP (015, 018).
- Cap camp d'IBAN complet ni de targeta; l'IBAN del club és configuració (RN-T03).
- Immutabilitat a la base de dades, no només a l'aplicació (RNF-T2).
- Els fitxers d'extracte no es desen (RN-101 de la 00); les línies normalitzades no es mostren fora de la conciliació.
- Cap dada de tresoreria als registres d'errors (011).
- Proves de permisos per rol i per objecte abans de fusionar (CK B4).

## Annex C — Esborrany de pla i tasques (per dependències, sense dates)

Esborrany perquè es vegi l'ordre. Es farà `plan.md` i `tasks.md` definitius quan s'aprovi la spec.

| # | Tasca | Depèn de | Feta quan |
|---|---|---|---|
| T01 | Model de compte de tresoreria i comptes inicials | 00 (departaments, càrrec, pagament) | CA-T01.x en verd |
| T02 | Centres de cost i dades inicials «General / …» | 00 | CA-T14.x |
| T03 | Model de moviment immutable (aplicació i base de dades) | T01, T02 | CA-T06.3; RNF-T2 |
| T04 | Càlcul de saldos i prova de volum | T03 | CA-T02.x; RNF-T7 |
| T05 | Servei `registrar_cobrament` idempotent | T03 | CA-T03.x |
| T06 | Servei de comissions per tipus de càrrec | T05 | CA-T04.1 a CA-T04.3 |
| T07 | Serveis de devolució i retorn | T05, T06 | CA-T05.x |
| T08 | Anul·lació amb contramoviment | T03 | CA-T06.1, CA-T06.2 |
| T09 | Traspassos i arqueig | T03 | CA-T07.x, CA-T08.1 |
| T10 | Referència de transferència amb dígit de control | 00 (càrrec) | RN-T20; VT-03 |
| T11 | Estats de conciliació de les línies i propostes per referència i import | T05, T10; HU-21 de la 00 | CA-T09.x |
| T12 | Confirmar i desfer conciliacions de transferències (una i diverses) i correcció de la 045 | T11 | CA-T10.x |
| T13 | Liquidacions del proveïdor i repartiment de comissions (**obligatòria**) | T06, T11; format de la liquidació (P-45) | CA-T04.4; CA-T11.x |
| T14 | Exclusions i llista «a revisar» | T11 | CA-T12.1; CA-T13.1 |
| T15 | Pantalles de tresoreria (comptes, moviments, conciliació, a revisar) segons el sistema de disseny | T04, T12, T14 | Proves de permisos (§2) i revisió d'accessibilitat |
| T16 | Exportació CSV | T04 | CA-T15.1 |
| T17 | Dades de prova inventades (moviments, extractes, liquidacions) | T13 | Es carreguen amb una ordre |
| T18 | Guia curta per al tresorer | T15 | Document al repositori |

T13 és obligatòria: la liquidació agrupada del proveïdor és la que permet quadrar el compte de trànsit amb el banc. És l'única tasca que depèn del proveïdor (043); la resta es pot fer abans.

## Annex D — Experiència de pagament (requisits per a la spec 05b)

Requisits aprovats el 27/10/2026. La 04 no fa les pantalles de pagament, però n'ha de poder donar les dades.

**Pagar sense sortir de l'app**
- El soci paga la quota i les inscripcions **dins l'app**, amb targeta o Bizum, al camp o la pàgina segura del proveïdor (per exemple, un `iframe`). L'app no veu ni guarda mai el número de la targeta (043).
- Sempre hi ha el camí de reserva: transferència amb la referència única del càrrec (RN-T20), l'IBAN del club i l'import, amb un botó per copiar-los.

**Estats visibles**
| Estat que veu el soci | Què vol dir | Estat a la 00 |
|---|---|---|
| **Pendent** | Encara no s'ha intentat pagar | Càrrec «pendent», sense pagament en curs |
| **En curs** | S'ha començat a pagar i s'espera la confirmació del proveïdor. Amb Bizum: «Esperant confirmació a l'app del teu banc» | Càrrec «pendent», pagament amb estat al proveïdor «en curs» |
| **Pagat** | El proveïdor ho ha confirmat al servidor | Càrrec «pagat» |
| **Fallit** | L'últim intent no s'ha pogut completar. Es pot tornar a provar o pagar d'una altra manera | Càrrec «pendent», pagament amb estat «fallit» |

Cada estat es mostra amb símbol, text i color (030) i un missatge que diu què ha de fer el soci.

**Bizum**
- Estat «Esperant confirmació» mentre el soci no ha confirmat al seu banc.
- **Caducitat:** si no es confirma dins el temps que fixi el proveïdor [A verificar: P-45], l'intent passa a «fallit» amb el missatge «No s'ha confirmat a temps» i es pot tornar a provar. El càrrec continua pendent.
- **Abandonament:** si el soci tanca la pantalla, el càrrec continua pendent i l'intent caduca sol; en tornar, veu l'estat real.

**Confirmació**
- El càrrec només passa a «pagat» quan el proveïdor ho confirma **al servidor** (notificació verificada), **mai** des del navegador (RN-71). La tornada del navegador només diu «Estem confirmant el pagament».
- **Idempotència:** una confirmació repetida no crea cap segon pagament ni cap segon ingrés (CA-T03.2).

**Rebut**
- En confirmar-se el pagament, el soci veu i pot descarregar **de seguida** un **rebut** amb: referència, concepte, import, departament, data i mètode.
- De moment el justificant és un **rebut**, no una factura. Si cada tipus d'ingrés s'ha de facturar, ho ha de dir la gestoria (P-47; P-02, Verifactu).
