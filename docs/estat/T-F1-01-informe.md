# T-F1-01: informe de la revisió final de la fase 1 (primer pas, 20/11/2026)

Primer pas de la [T-F1-01](../planning.md#F1-revisio-final), fet pel carril d'auditoria del pilot mentre els altres carrils acaben les darreres tasques. El propietari la defineix així: «pendents visuals de totes les tasques, `python tools/verifica.py`, e2e senceres, i cap valor de negoci ni element de llista escrit al codi». **Aquest informe no tanca la tasca:** la revisió visual del propietari (1280, 390 i 320 px, clar i fosc) i les comprovacions manuals d'accessibilitat (T-M01-28b) continuen pendents.

Base: `master` a `837971c` (19/11/2026). Entorn: portàtil (Windows, PostgreSQL 16, Chromium de Playwright), dades inventades.

## 1. `tools/verifica.py` i e2e senceres

| Pas | `master` (837971c) | Amb els arreglos (#286 i #289) |
|---|---|---|
| pytest (7.921 proves) | **1 falla**: `test_staging_never_charges_nor_sends_mail_outside` | Verd (#289) |
| ruff, ruff format, `makemigrations --check`, `check` | Verd | Verd |
| `check --deploy` | **Falla**: `Set the MANDATE_ENCRYPTION_KEYS environment variable` | Verd (#286) |
| e2e senceres | 173 passades, 4 saltades | Les mateixes |

- **`check --deploy`:** el CI exporta `MANDATE_ENCRYPTION_KEYS` al pas de desplegament, però `deploy_env()` de `tools/verifica.py` no la tenia; la verificació local sortia vermella on el CI passa. Arreglat a la [#286](https://github.com/gerardtristan/Centre-de-Recuperacio-i-d-Investigacions-Submarines-App-Web/pull/286), amb una prova que compara les variables del pas del CI amb les de `deploy_env()`.
- **Servidor de proves:** `config/settings/staging.py` llegia `EMAIL_HOST` i `EMAIL_PORT` de l'entorn, i el `.env` del portàtil en té un altre: la garantia de la [099](../decisions/099-servidor-de-proves-al-portatil.md) («cap correu surt») depenia de l'entorn. Arreglat a la [#289](https://github.com/gerardtristan/Centre-de-Recuperacio-i-d-Investigacions-Submarines-App-Web/pull/289): servidor i port fixos (`mailpit`, 1025).
- **e2e saltades:** les 4 de `test_logotip.py` amb Firefox i WebKit, perquè aquests navegadors no són instal·lats al portàtil. El CI sí que els instal·la i les executa. No és cap error.
- **Incident d'entorn:** la primera execució es va trencar a la meitat. PostgreSQL es va quedar sense memòria (`out of memory` a `AfterTriggerEvents`) mentre la prova de volum de la 04 (`apps/treasury/tests/test_balances.py`, 50.000 moviments) inseria files, i va reiniciar en mode de recuperació: 601 errors de connexió i les e2e sense base de dades. El límit de memòria virtual de Windows estava gairebé exhaurit (4,4 GB lliures de 30,6; C: al 95 %, on hi ha el fitxer de paginació) amb diversos carrils fent proves alhora. A la segona execució la mateixa prova passa. No és cap error del codi, però tres carrils en paral·lel al mateix PostgreSQL poden fer caure les proves de tots.

## 2. Pendents visuals

**Font:** la llista de la [secció de la T-F1-01](../planning.md#F1-revisio-final) (punts 1 i 2) i les notes de `docs/estat/` amb «revisió visual», «[A comprovar]» i «captura».

**Com:** les captures de les e2e senceres (1280 i 390 px; les proves amb `review` també fan 320 px en clar i en fosc), mirades en fulls de contacte. **Mirades:** fitxa i llistat de socis, data de naixement i doble factor (T-M01-33, 35 i 51), menú de l'administració i de l'àrea personal (T-M01-46), 404 (T-M01-47), índex de recorreguts (T-M01-48), edició i data d'alta (T-M01-15b), «Quotes i impagats» (T-M01-18 i 26), altes pendents i menor sense document (T-M01-14), canvi de tipus (T-M01-17 i 42), enllaços de convidat (T-M00-02), avís dels comptes d'emergència (T-M00-03), dades bloquejades (T-M00-04), eximir la quota (T-M01-40), inici i perfil del soci (T-M01-16), carnet i còpia sense connexió (T-M01-19 i 21), «Les meves dades» i esborrat (T-M01-22), acceptació de les polítiques (T-M01-25) i sessió caducada (T-M01-45). **No mirades:** la prova de Cluber (T-M01-50) i les pantalles del 04, 05a i 05b, que no són a la llista de la T-F1-01.

Cap pantalla no té errors de consola ni desplaçament de costat a 320 px (les e2e ho comproven). Incidències (cap no és funcional ni de seguretat):

| # | Pantalla | Què passa | De qui és |
|---|---|---|---|
| V1 | Dades bloquejades, a 390 px | La cel·la «Pagaments» de la taula convertida en fitxa reparteix «Targeta · 90,00 € · 20/11/2026» en tres columnes separades | Nucli (`templates/core/`) o disseny (la taula responsiva) |
| V2 | Esborrat de dades (RGPD) | Les vinyetes de la llista «Què passarà en aprovar-la» queden fora del marge (tocant la vora a 390 px) | Disseny (estil de les llistes) |
| V3 | Altes pendents, menor sense document | «Rebutja…» queda entre les dues caselles, lluny d'«Aprova l'alta» (`deposito-accions`) | Disseny |
| V4 | Acceptació de les polítiques, a 390 px | La barra inferior té dues entrades i el botó «+» a la vora dreta, no al centre; el menú mostra entrades que, fins que no s'accepten, tornen a la mateixa pàgina | Disseny i nucli (navegació, `apps/accounts`) |
| V5 | Eximir la quota i «Restableix el doble factor» | El menú de l'administració no marca cap entrada (la fitxa i «Corregeix la data d'alta» sí que marquen «Llistat de socis») | Nucli (`apps/accounts/navigation.py`) |
| V6 | Canvi de tipus (administració), després d'acceptar | El missatge verd i el requadre groc diuen el mateix | 01 |
| V7 | «Quotes i impagats» | L'avantítol diu «Socis», però al menú és a «Quotes i tresoreria»; «Tornar a l'inici de l'administració» en unes pantalles i «Tornar a l'administració» en d'altres | 01 i disseny |
| V8 | Inici del soci, a 1280 px | «La teva història» i «Llicència» no s'alineen amb «El teu carnet» (la columna de la dreta comença més endins) | Disseny |
| V9 | Fitxa del soci i eximir la quota | «Quota de soci 2026 (2026)»: el concepte ja porta el període. Per a les quotes importades de Cluber, el parèntesi sí que aporta | 01, criteri del propietari |
| V10 | «Corregeix la data d'alta» i polítiques | L'error surt sota el camp, però sense el resum amb enllaços que té el formulari d'alta (Errata) | Disseny |
| V11 | Índex de recorreguts (`design/`) | Diu que el suplement «venç una setmana després»: ara és l'ajust VC-53 | Disseny (wireframes) |

**Notes de `docs/estat/` resoltes o precisades:**
- T-M04-11 ([M04](M04.md)): la PR que hi falta és la [#53](https://github.com/gerardtristan/Centre-de-Recuperacio-i-d-Investigacions-Submarines-App-Web/pull/53) (`5e8d690`). Corregit en aquesta PR.
- T-M01-21b ([M01](M01.md)), «el QR a la còpia sense connexió [A comprovar]»: amb Chromium sense connexió, la còpia mostra el QR (`test_pwa_079.py`, captura `carnet-sense-connexio`). Continua pendent el mòbil real.
- T-M01-45c, «la vora [A comprovar si ja s'ha fet]»: no s'ha fet. `--c-linia-forta` continua a 3,7:1 i 3,6:1 sobre el contenidor (≥ 3:1, just).
- T-M00-04 ([M00](M00.md)): «si les referències dels pagaments també s'han de bloquejar continua obert, sense fila a `pendents.md`». Continua sense fila; vegeu el punt 4.
- T-M05b-22c ([M05b](M05b.md)): el títol diu «VC-18 (`transfer_reminder_days`)», però `transfer_reminder_days` és de la VC-16. La VC-18 (qui paga la comissió de retorn i el carnet amb una quota retornada) tampoc no la llegeix cap codi. No l'he tocat: ho ha d'aclarir qui va crear la fila.

## 3. Valors de negoci i llistes escrits al codi

**Abast:** els `*.py` d'`apps/` (sense proves ni migracions), `templates/` i `config/settings/`, a `837971c`, contra l'[apèndix de valors configurables](../planning.md#valors-configurables), la [peça d'ajustos](../planning.md#valors-configurables-055) i la [revisió del 13/11/2026](revisio-valors-configurables.md). Cerques: constants en majúscules, `timedelta`, xifres a les plantilles («dies», «mesos», «€»), noms de departaments.

**Del 13/11 ja resolt:** VC-01 a VC-04 i VC-53 (T-M01-32), els tipus de soci amb atributs (T-M01-52), VC-11, VC-16 (avís previ i intents), VC-17, VC-54, els codis de retorn i els interruptors del proveïdor (VC-14): tots llegeixen `business_settings`.

**Trobat ara:**

| Fitxer | Valor | Què és | Què se'n fa |
|---|---|---|---|
| `templates/emails/mandat-caducat.ca.txt` | «fa 36 mesos» | Repetia la regla `expiry.EXPIRY_MONTHS` (VC-13, es queda al codi, [A verificar: banc]) | Arreglat a la [#285](https://github.com/gerardtristan/Centre-de-Recuperacio-i-d-Investigacions-Submarines-App-Web/pull/285): el correu llegeix la regla |
| `apps/core/charges.py`, `apps/core/models.py` (`Department.GENERAL`), `apps/treasury/services.py` (`CASH_ADJUSTMENTS`) | «General», «Quotes de socis», «Ajustos de caixa» | Departaments i centres de cost (VC-08) trobats pel nom | Dubte [P-411](../decisions/pendents.md) |
| — | VC-08 sense pantalla | Els departaments, centres de cost i comptes de tresoreria són dades, però cap pantalla ni cap tasca no els edita | Dubte [P-410](../decisions/pendents.md) |
| `config/settings/base.py` (`LOCKED_DATA_RETENTION_YEARS`), `apps/core/privacy.py` | 6 anys | Termini legal (085, G-1) per variable d'entorn; el docstring diu que hauria de ser un ajust i dona una altra data d'inici | Dubte [P-412](../decisions/pendents.md); el docstring, llista (b) |
| `apps/payments/expiry.py` (`EXPIRY_MONTHS = 36`) | 36 mesos | VC-13: regla SEPA, «es queda» | Correcte |
| `apps/treasury/reconciliation.py` (`SETTLEMENT_DAYS = 5`) | 5 dies | Ja és la [P-364](../decisions/pendents.md) | Res |
| `apps/members/instalments.py` (`COUNT = 3`) | 3 terminis | Regla de la P-61 («tres terminis») | Correcte |
| `apps/payments/settlements.py` (`LOOKBACK_DAYS = 7`), `processing.py` (`NOTICE_TRIES = 3`), `members/templatetags/vigencia.py` (`WINDOW_DAYS = 60`), mides de pàgina i de nota | — | Tècnics (reintents, escala del dibuix, paginació) | Es queden |
| VC-16 `transfer_reminder_days`, VC-18, VC-48 | — | Encara sense codi que els llegeixi | Ja tenen tasca (T-M05b-22c, T-M05a-26) |

Es queden al codi, com diu la 059: les regles d'edat (14 i 18 anys), la renovació als 12 mesos, la validesa dels enllaços, els bloquejos i els límits del webhook, les llistes tancades d'estats i els límits de les importacions.

## 4. Llista (b): el que és al nucli i no s'ha tocat

1. **`apps/core/privacy.py`**, docstring de «Termini de conservació»: diu que no hi ha cap nombre d'anys i que el termini ha de ser un ajust que comença a `executed_at`; el codi ja aplica 6 anys per variable d'entorn (`locked_data.py`) i la G-1 diu el 31/12 de l'any de l'últim registre econòmic. Cal corregir-lo segons la resposta a la P-412.
2. **Departaments pel nom** (`apps/core/charges.py`, `Department.GENERAL` a `apps/core/models.py`): segons la resposta a la P-411, cap canvi (opció A: entrades del sistema que la pantalla no deixa reanomenar) o un codi fix amb migració de `core` (opció B).
3. **Pantalla de VC-08** (P-410): faria servir els serveis de departaments de `apps/core/charges.py` (falta un servei per reanomenar) i el catàleg de permisos (T3, M7).
4. **Navegació** (`apps/accounts/navigation.py`, V4 i V5): les subpàgines de la fitxa del soci («Eximeix la quota», «Restableix el doble factor») no marquen cap entrada del menú, i la pàgina d'acceptació de les polítiques mostra entrades que no s'hi poden fer servir.
5. **V1**, `templates/core/` de les dades bloquejades: la cel·la «Pagaments» a 390 px (si no és de la taula responsiva del sistema de disseny).
6. **T-M00-04**: si les referències dels pagaments també s'han de bloquejar. Ara és la [P-420](../decisions/pendents.md) (segona volta); si la resposta és B o C, el canvi és a `apps/core/locked_data.py`.

## 5. Dubtes nous

[P-410](../decisions/pendents.md) (pantalla de VC-08), [P-411](../decisions/pendents.md) (departaments pel nom) i [P-412](../decisions/pendents.md) (termini de bloqueig: ajust o codi). Tots tres al tauler, amb la recomanació.

## 6. Què queda de la T-F1-01

- La revisió visual del propietari de les llistes 1 i 2 de la secció, amb les incidències V1 a V11 com a punt de partida.
- Les comprovacions manuals d'accessibilitat (T-M01-28b) i els dispositius reals (T-F1-02), que esperen l'entorn de proves temporal.
- Fet a la segona volta: `tools/verifica.py` amb les #285, #286 i #289 a `master` (apartat 7.5).
- La sessió de disseny: la llista de l'apartat 7.3.

## 7. Segona volta (20/11/2026)

### 7.1 Pendents visuals del 04, el 05a, el 05b i la prova de Cluber

He mirat a 1280 i 390 px les captures de les e2e d'aquestes pantalles, una per pantalla diferent: comptes i saldos, moviments i exportació, extracte bancari (CSV i Norma 43), conciliació (proposada, tria de liquidació, casar a mà, casar amb moviments), «A revisar», liquidacions, traspàs, arqueig, anul·lació en un període tancat; mètode de la quota, mandat (signar, error d'IBAN, actiu, revocar), targeta guardada, «Mètodes i mandats», revocar un mandat des de l'administració, campanya, ajustos de pagaments i del proveïdor; pagament amb targeta, Bizum i transferència, rebut, «Pagaments i a revisar», remeses (previsualització, detall, abonament), retornats (a mà i fitxer), codis de retorn, candidats a impagat i terminis. La prova de Cluber no tenia captures: ara té una e2e (#293).

Les e2e ja comproven que no hi ha errors de consola ni desplaçament de costat a 320 px.

| # | Pantalla | Què passa | De qui és |
|---|---|---|---|
| V12 | Prova de Cluber (T-M01-50) | La pàgina no feia servir el sistema de disseny: el camp del fitxer i el botó eren els del navegador, les taules no tenien estil i les vinyetes quedaven fora del marge | **Arreglat a la #293** |
| V13 | Totes les taules amb una fila buida (`{% empty %}` amb `colspan`), a 390 px | El text «Cap moviment amb aquests filtres» i similars surten alineats a la dreta: la cel·la és flex i l'etiqueta buida ocupa l'esquerra | DISSENY (taula apilada, `comptes.css`) |
| V14 | Extracte bancari, columna «Desfer», a 390 px | El formulari del motiu queda espremut a la meitat dreta de la cel·la | DISSENY (formulari dins de la taula apilada) |
| V15 | Conciliació a 1280 px amb el plafó obert | La columna «Estat» queda molt estreta i el motiu «A revisar» es parteix en moltes línies; les accions s'amunteguen | DISSENY (escriptori de la conciliació) |
| V16 | Cel·les amb més d'un element a 390 px (dades bloquejades, «Amb error» de l'extracte, «Mètodes i mandats», «Quotes i impagats») | Cada element queda en una columna separada, com a la V1 | **Arreglat a la #293** (un `<span>` per cel·la) |
| V17 | Mandat, revocació i targeta guardada (àrea del soci); campanya (administració) | Les etiquetes «A validar: junta i banc (L-M05a-01)», «A verificar: P-45 punt 6» i similars es veuen a la pantalla. Un soci real les veuria | Propietari: és el patró dels textos provisionals, però s'han de treure abans del nivell 1 |
| V18 | Ajustos de pagaments, a 1280 px | La columna del nom es parteix lletra a lletra (`payments.bizum_ui_…`) perquè la llista de països ocupa l'amplada | DISSENY |
| V19 | Àrea del soci, mandat, targeta i pagament; administració, remesa, retornats | El menú no marca cap entrada (com la V5) | Nucli i DISSENY (`apps/accounts/navigation.py`) |
| V20 | Inici del soci amb una quota pendent i sense carnet | «La teva quota» mostra «—» i el botó principal és «El meu carnet», quan encara no en té; «Paga ara» té un altre color que la resta de botons principals | DISSENY i 01 |
| V21 | Terminis de la quota, a 390 px | El número del termini sortia centrat | **Arreglat a la #293** |

### 7.2 Arreglat a la #293

V1, V2, V12, V16 i V21, només amb classes que ja existeixen (`formulari`, `camp`, `ajuda`, `boto`, `avis`, `taula`, `dades-soci`, `passos`, `cel-nom`, `cos-ample`). Captures abans i després a `docs/diari-de-construccio/captures/` (`2026-11-20_0338_T-F1-01_*`).

### 7.3 Llista per a la sessió de DISSENY

Captures de la verificació completa (`.e2e-captures/`, carpeta de la prova entre claudàtors).

| # | Fitxer | Captura | Què cal |
|---|---|---|---|
| V3 | `templates/members/join_requests.html`, `deposito-accions` | `test_minor_without_document_shows_the_possible_duplicate/menor-possible-duplicat-1280.png` | «Rebutja…» al costat d'«Aprova l'alta» encara que el formulari tingui diverses caselles |
| V4 | Plantilla base de l'àrea personal i `apps/accounts/navigation.py` | `test_imported_member_accepts_the_policies_at_first_login/politiques-390.png` | La barra inferior amb dues entrades centra el «+»; a la pàgina de les polítiques, menú sense entrades que no es poden fer servir |
| V5 i V19 | `apps/accounts/navigation.py` | `test_treasurer_exempts_the_fee_of_a_pending_member/eximeix-quota-1280.png`, `test_member_revokes_the_mandate/mandat-revoca-1280.png`, `test_treasurer_registers_a_return_and_confirms_the_retry/retornats-per-decidir-1280.png` | Marcar l'entrada de la secció a les subpàgines (fitxa del soci, mandat, targeta, pagament, remesa, retornats) |
| V8 | Inici del soci (`templates/members/`) i el seu CSS | `test_member_home_has_the_wave_header_and_the_fee_block/inici-al-dia-1280.png` | Alinear «La teva història» i «Llicència» amb «El teu carnet» |
| V10 | «Corregeix la data d'alta», polítiques | `test_edit_member_data_and_correct_the_join_date/data-alta-sense-motiu-1280.png` | Resum d'errors (Errata) com al formulari d'alta |
| V13 | `static/css/comptes.css` (`.taula td`) | `test_treasurer_sees_the_movement_and_the_balance/moviments-filtrats-390.png` | Una fila buida amb `colspan` alineada a l'esquerra |
| V14 | `templates/core/bank_statement.html` i la taula apilada | `test_treasurer_imports_and_undoes_a_statement/importat-390.png` | Un formulari dins d'una cel·la a 390 px |
| V15 | `templates/treasury/reconciliation.html` i l'escriptori de la conciliació | `test_treasurer_chooses_between_two_settlements/conciliacio-liquidacio-tria-1280.png` | Amplada de les columnes amb el plafó obert |
| V18 | `templates/core/settings_section.html` | `test_administrator_changes_a_value_and_treasurer_only_sees_it/apartat-1280.png` | Columna del nom i valors llargs (llista de països) |
| V20 | Inici del soci | `test_a_pending_fee_shows_the_flat_strip_with_pay_now/portada-pendent-390.png` | L'estat de la quota pendent i quin és el botó principal sense carnet |
| V11 | `design/` (índex de recorreguts) | `test_journeys_index_opens_from_disk_and_links_the_original_wireframes/capcalera-1280.png` | «Venç una setmana després» ara és l'ajust VC-53 |
| V6, V7, V9 | `templates/members/` (canvi de tipus, «Quotes i impagats», fitxa) | vegeu l'apartat 2 | Criteri de contingut: missatge repetit, avantítol «Socis» a «Quotes i impagats», «(2026)» repetit |

### 7.4 Dubte nou

[P-420](../decisions/pendents.md): s'han de bloquejar també les referències dels pagaments d'una persona esborrada? Ve de la nota de la T-M00-04.

### 7.5 `tools/verifica.py` amb els arreglos a `master`

`master` a `db36220` (amb les #285, #286 i #289), sense cap altre carril passant proves: **VERD** (empremta `c6ad7f5e9f5d`).

| Pas | Resultat |
|---|---|
| pytest | 7.991 passades |
| ruff, ruff format, `makemigrations --check`, `check` | Verd |
| `check --deploy` | Verd |
| e2e senceres | 179 passades, cap saltada (amb els navegadors de Playwright de `D:/CRIS/pw-browsers`, que també tenen Firefox i WebKit) |

Nota per a qui faci proves al portàtil: amb `--reuse-db` en una base on abans s'han passat e2e (que buiden les taules), `test_instalments_screens_049.py::test_off_the_fee_page_shows_nothing_and_the_post_changes_nothing` falla: la pàgina mostra els terminis com si l'interruptor estigués encès. Amb `--create-db` passa. No és cap error del codi.

### 7.6 Tercera volta (20/11/2026)

- **V6, V7 i V9:** arreglats a la PR dels continguts (`templates/members/` i el missatge de `apps/members/views/admin_requests.py`), amb captures abans i després.
- **Prova inestable dels terminis amb `--reuse-db`:** arreglada a la #298. La causa era que la neteja de les e2e no tornava els ajustos de les migracions al seu valor (apartat 7.5).
- **No s'ha fet:** associar `templates/members/cluber_preview.html` a l'e2e de Cluber (`test_politiques_079.py`) a `.claude/hooks/e2e_map.py`. És configuració del hook de Claude Code: la canvia o l'autoritza el propietari.

