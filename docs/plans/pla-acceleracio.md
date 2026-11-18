# Pla d'acceleració del desenvolupament

- **Què és:** una proposta per anar més de pressa sense perdre qualitat ni control. No és una especificació: no canvia cap regla de negoci de [`docs/planning.md`](../planning.md).
- **Estat:** proposta, pendent de l'aprovació del propietari (el responsable del projecte). Fins que l'aprovi no s'escriu codi de producció ni es canvia cap regla de treball.
- **Sobre què s'ha mesurat:** `origin/master` al commit `c8d7f66` (la data només identifica la versió; aquest pla no té calendari, [038](../decisions/038-planificar-sense-dates.md)).
- **Què es demana al propietari:** les sis decisions de l'[apartat 9](#aprovar).

## Resum

1. **El problema no és que falti codi.** Hi ha 19.900 línies de codi, 31.900 de proves (2.093 proves), integració contínua amb proves al navegador i el model d'usuari propi fet des de la T-M01-04. El que falla és que tot aquest codi és d'un sol mòdul, no corre enlloc fora d'un portàtil i una part no es pot donar per tancada.
2. **El que frena de veritat** són cinc coses: s'ha aprofundit en el 01 abans de fer passar un sol euro pel sistema; una decisió pendent bloqueja el tancament d'una tasca en lloc de bloquejar només l'entrada en producció; totes les decisions passen per una sola persona en tandes molt grans; la feina de registrar pesa més que la de construir; i les PR són tan grans que ningú no les pot revisar.
3. **La proposta:** congelar l'especificació de la fase 1, construir per llesques que travessen 04, 05a i 05b començant pel primer cobrament amb un proveïdor fals, desplegar cada fusió en un entorn de proves, posar el control on hi ha el risc (diners, permisos, dades personals i les portes de producció) i automatitzar la resta.
4. **El camí crític no és de codi.** Les respostes del banc i del proveïdor de pagaments ([P-44 i P-45](../decisions/pendents.md)) decideixen quan es pot cobrar de veritat. Cap millora d'aquest pla ho escurça: s'han de demanar ara.

---

## 1. Diagnosi

### 1.1 Què hi ha avui

| Què | Mesura |
|---|---|
| Codi d'aplicació (`apps/` i `config/`, sense proves ni migracions) | 19.909 línies, en 3 apps: `core`, `accounts` i `members` |
| Proves | 31.911 línies, 2.093 proves, 21 fitxers de proves al navegador |
| Integració contínua | Lint, migracions al dia, proves, `check --deploy`, proves al navegador, escaneig de secrets. Uns 5 minuts |
| Documentació (`docs/` i `specs/`, només Markdown) | 18.567 línies; `planning.md` sol fa 6.871 línies i 1,09 MB |
| Decisions | 85 de numerades; unes 26 files obertes o obertes en part a `pendents.md`; 330 marques «[A validar]» i 171 «[A verificar]» dins del pla |
| Tasques del 01 (55) | 39 fetes; 6 «feta en part»; 5 «pendent de validació»; 5 sense començar (recompte aproximat, vegeu 1.2 c) |
| Tasques del 04, el 05a i el 05b (74) | Cap de començada |
| Desplegament | Cap. No hi ha `Dockerfile` ni cap entorn de proves; l'aplicació només corre en local |
| Commits | 426: 203 de pla, diari i decisions; 146 de tasques |

**Tres de les causes que es donaven per fetes no ho són.** Hi ha proves i n'hi ha moltes. Hi ha integració contínua. El model d'usuari propi existeix (`accounts.Account`). Afegir-ne més no acceleraria res.

### 1.2 Què frena de veritat

**a) Profunditat abans que amplada.** El 01 té importació de Cluber en dues fases, web instal·lable, auditoria d'accessibilitat, preparació per traduir i fins una mesura de la diferència de temps de «He oblidat la contrasenya». Mentrestant, la tresoreria i els pagaments, que són el motiu per deixar Cluber i on hi ha el risc del projecte, tenen zero línies. Cada millora del 01 és correcta per separat; juntes han endarrerit la primera prova de si el recorregut sencer funciona.

**b) Una decisió pendent bloqueja la tasca, no la producció.** La regla actual diu que una part amb una pregunta oberta no s'implementa. El resultat és que una tasca es queda «feta en part» mentre espera la junta, el tresorer, la secretaria, l'assessor o una tasca del 05b. Dels motius que surten a les files de les tasques no tancades del 01, els més repetits són la revisió visual (ja resolta per la [080](../decisions/080-revisio-visual-al-final-de-la-fase-1.md)), una fila de `pendents.md`, i respostes de la secretaria, la junta i el tresorer. Com que encara no hi ha cap dada real ni cap soci fent servir la plataforma, cap d'aquestes preguntes necessitava aturar el codi: n'hi havia prou que aturessin l'activació a producció.

**c) L'estat no es pot llegir.** L'estat de cada tasca viu dins de la seva fila del pla, barrejat amb l'historial. El pla té 41 línies de més de 2.000 caràcters i la fila de tasca més llarga en fa 11.043. Segons com es llegeixi, surten entre 6 i 21 tasques «fetes en part». Ni una persona ni una eina poden respondre de pressa «què falta per acabar el 01?».

**d) Tota decisió passa per una sola persona, en tandes molt grans.** Una decisió recull 31 respostes del propietari, una altra 25. El propietari fa alhora de qui decideix, de qui revisa pantalles, de qui fusiona i de qui porta les preguntes a la junta. Quan ell no respon, tot s'atura; quan respon, ho ha de fer sobre desenes de punts de cop.

**e) El registre pesa més que la construcció.** Per cada commit de tasca n'hi ha 1,4 de pla, diari o decisions. Cada tasca demana actualitzar la seva fila del pla, escriure el diari en un commit a part i tornar a anotar al pla que el CI ha sortit verd, cosa que genera un altre commit i un altre CI. A més, com que totes les tasques editen `planning.md`, dues branques que avancen alhora xoquen sempre al mateix fitxer.

**f) Les PR no es poden revisar.** La PR 7 té 77.747 línies afegides, 589 fitxers i 100 commits. La PR 4, 53.714 línies. Amb aquesta mida, «revisar» vol dir respondre un inventari de preguntes, no mirar el canvi. `master` no està protegida: s'hi pot pujar directament.

**g) No hi ha res desplegat.** El propietari valida amb captures i llistes de preguntes perquè no pot obrir l'aplicació i fer-la servir. La junta, la secretaria i el tresorer tampoc. Moltes de les preguntes obertes es respondrien soles en veure la pantalla funcionant.

**h) Feina fora d'ordre i feina a mig fusionar.** La branca `feature/t-m02-activitats` té 14.700 línies del mòdul 02 (22 commits sense fusionar) i ja ha generat decisions pròpies, quan el 02 depèn del 04, el 05b i el 06, que no existeixen. Cinc branques de nit més conserven entre 1 i 11 commits que no consten a `master`; cal comprovar si el seu contingut ja hi va entrar per una altra via [A verificar]. La feina començada que no es fusiona no compta com a acabada i consumeix revisions del propietari.

**i) Els bloquejos externs no han començat a córrer.** El banc i el proveïdor de pagaments ([P-44, P-45](../decisions/pendents.md)) han de respondre 14 preguntes (qui contracta el TPV, comissions, on són les dades, format de la remesa, identificador de creditor, entorn de proves). El README encara diu que els comptes de proveïdors no estan creats. D'això depenen els dos nivells de producció, i és l'única part del projecte que té un temps d'espera que no depèn de l'equip.

### 1.3 Què funciona i no s'ha de tocar

- Les proves i el pipeline. No es rebaixa cap control existent.
- La font única (`planning.md`, [047](../decisions/047-planning-font-unica-de-l-especificacio.md)) i el registre de decisions.
- L'adaptador del proveïdor de pagaments ([043](../decisions/043-proveidor-de-pagaments-dins-la-ue.md)): és el que permet construir tot el 05 amb un proveïdor fals.
- Els dos nivells de producció amb autorització expressa de la junta ([025](../decisions/025-dos-nivells-de-produccio.md)).
- Les regles fixes: dades personals només dins la UE, cap dada real fora de producció, plans sense dates, tot en català.

---

## 2. Congelació de l'especificació

### 2.1 Què es congela

Les seccions 1 a 9 dels mòduls de la fase 1 (01, 04, 05a i 05b) i les seves addendes, tal com són al commit que aprovi aquest pla. Es marca amb una etiqueta de Git (`spec-fase1-v1`). A partir d'aquí:

- **No s'hi afegeixen més addendes** mentre duri la fase 1, llevat d'un canvi de regla aprovat pel propietari (2.4).
- **Els mòduls de la fase 2 (06, 02, 03 i 09) no es toquen** fins que la llesca 2 de la fase 1 funcioni. Les seves preguntes noves s'apunten i prou.
- **Les files de tasques deixen de portar historial.** L'estat passa a un fitxer petit per mòdul (4.4). El pla torna a ser un document que es llegeix, no un registre.

### 2.2 Què es pot construir ja

| Mòdul | Es pot construir ara | Espera una resposta externa |
|---|---|---|
| 01 | Tot el que queda, tret del que depèn del 05b (rebut, terminis) i del 06 (còpia de lectura de la llicència) | Textos legals definitius (gestoria i assessor); condicions de posada en servei de la importació de Cluber ([P-62, P-65](../decisions/pendents.md)) |
| 04 | T-M04-01 a T-M04-12 i T-M04-14 a T-M04-21: comptes, centres de cost, moviment immutable, ingressos, comissions, devolucions, anul·lacions, traspassos, referències, conciliació, pantalles i exportació | T-M04-13: format de la liquidació (P-45, punt 9). Es construeix amb el format del proveïdor fals i s'ajusta després |
| 05a | Adaptador i proveïdor fals, notificacions amb signatura, xifratge de camp, mandat, IBAN xifrat, signatura, preferència, campanya, llistat emmascarat i caducitat | T-M05a-05 (proveïdor real), T-M05a-12 (targeta guardada, P-45 punt 6) i l'identificador de creditor al text del mandat (P-45 punt 5; el text porta un marcador fins llavors) |
| 05b | Intent de pagament, targeta i Bizum sobre l'adaptador, notificacions, transferència, rebut, remesa, retornats, devolucions i proves de principi a fi amb el proveïdor fals | T-M05b-10: versió del fitxer de remesa i mostra del banc (P-45 punt 5); T-M05b-14: format de la liquidació; T-M05b-15 i les que en depenen (targeta guardada) |

Tot el que espera una resposta externa queda **darrere de l'adaptador o darrere d'un interruptor**, de manera que no atura cap altra tasca.

### 2.3 Com entra un dubte nou sense aturar la feina

Qui troba un dubte **no edita el pla**. Afegeix una fila a `pendents.md` amb aquests camps i continua treballant:

| Camp | Contingut |
|---|---|
| Pregunta | En el llenguatge del club, amb un exemple si cal |
| Opcions | Dues o tres, amb la conseqüència de cadascuna |
| **Tipus** | **R**, **C** o **I** (vegeu sota) |
| **Per defecte** | L'opció amb què es construeix mentrestant |
| **Què bloqueja** | Res, el nivell 1, el nivell 2 o l'activació d'una funció concreta |
| Qui respon | Propietari, junta, tresorer, secretaria, gestoria, assessor, banc o proveïdor |
| Tasca | La tasca que l'ha trobat |

Els tres tipus:

| Tipus | Quan | Què fa l'equip | Qui decideix |
|---|---|---|---|
| **R — reversible** | Un text, l'ordre d'una pantalla, un detall de comportament que es canvia sense tocar dades | Tria l'opció per defecte, construeix i tanca la tasca. Ho llista a la revisió setmanal | L'equip. El propietari ho pot canviar a la revisió |
| **C — configurable** | Un valor: un import, uns dies, un llindar | El posa a «Ajustos» amb un valor inicial ([055](../decisions/055-ajustos-configurables-i-addendes.md)) i tanca la tasca | Qui tingui el permís d'editar-lo, quan vulgui |
| **I — irreversible o cara** | Regles de diners, model de dades que afecta la migració de dades reals, RGPD i conservació, seguretat, permisos, el que veurà un soci real | Construeix l'opció més conservadora **darrere d'un interruptor apagat** i tanca la tasca. La pregunta passa a la llista de la porta de producció que bloqueja | El propietari o qui correspongui. **Sense resposta, no s'activa mai** |

L'interruptor és una variable de configuració per entorn, com la que ja bloqueja la importació final de Cluber (T-M01-25). No és un ajust editable des de l'aplicació: activar-lo a producció és una decisió.

**Això canvia una regla de CLAUDE.md** («si una spec té una pregunta oberta que afecta una regla de negoci, no implementis aquesta part: pregunta»). La regla nova seria: *una pregunta oberta de tipus I no s'activa a producció; una de tipus R o C es construeix amb l'opció per defecte i es revisa després.* El risc és refer feina quan la resposta no sigui l'opció per defecte. Queda limitat perquè només es tanquen sols els dubtes barats de desfer, i s'accepta perquè avui el cost d'esperar és més alt que el de refer.

### 2.4 Com es canvia una regla congelada

Només per tres motius: un error que impedeix construir, una resposta externa que contradiu el pla, o una decisió de la junta. Es fa amb una decisió numerada curta i **una sola edició al lloc de la regla**, sense addenda. És sempre una PR vermella (5.2).

### 2.5 S'acaba el «feta en part»

Una tasca que té una part feta i una part bloquejada **es parteix en dues**: la part feta passa a «Feta» i el que queda es converteix en una tasca nova i petita, amb el seu bloqueig escrit (una fila de `pendents.md` o una altra tasca). Estats possibles: *per fer*, *en curs*, *feta*, *bloquejada*. Cap més.

---

## 3. Ordre de construcció per llesques verticals

Una **llesca** és el mínim que una persona pot fer de punta a punta: té model, vistes, proves i queda desplegada a l'entorn de proves. Cada llesca acaba amb una demostració que el propietari pot fer ell mateix des del navegador.

L'ordre dels mòduls de la [024](../decisions/024-abast-minim-i-ordre-per-deixar-cluber.md) i la [060](../decisions/060-ajustos-de-l-auditoria-del-pla.md) es respecta com a **ordre de dependències**. El que canvia és que el 04, el 05a i el 05b no es construeixen sencers un darrere l'altre (74 tasques abans de veure un cobrament), sinó a talls que els travessen tots tres.

### Llesca 0 — Entorn de proves

No és de cap mòdul, però tota la resta s'hi recolza.

- **Què:** l'aplicació desplegada amb Coolify en un servidor de proves temporal a la UE ([010](../decisions/010-entorns.md)), amb HTTPS, les dades inventades de `seed_demo_data` i un compte de prova per rol.
- **Desplegament:** cada fusió a `master` es desplega sola.
- **Privacitat:** només dades inventades; accés amb contrasenya al davant; sense indexació; els correus no s'envien, es capturen.
- **Prova:** una comprovació automàtica després de cada desplegament (la pàgina de salut respon i s'hi pot entrar).

### Llesca 1 — Mòdul 01: fer-se soci, de punta a punta

El 01 ja té gairebé totes les peces. La llesca no afegeix funcions: demostra que el flux principal funciona sencer i tanca el que és obert.

- **Què pot fer una persona:** omplir «Fer-se soci» a la web → la secretaria aprova i s'assigna el número → es genera la quota → el tresorer registra el pagament a mà amb motiu → el soci passa a actiu → té carnet → la verificació pública respon.
- **Model:** el que hi ha (`Person`, `Account`, `Member`, `MemberRequest`, `AnnualFee`, `Charge`, `MemberCard`). Cap entitat nova.
- **Vistes:** les que hi ha. Si falta la pantalla de registre manual del pagament ([P-12](../decisions/pendents.md); 072, Q-037), és l'única peça nova.
- **Proves:** **una sola prova al navegador que fa el flux sencer**, de la sol·licitud al carnet verificat. Avui hi ha proves de cada tram, però cap que els encadeni.
- **Desplegament:** el mateix flux fet a mà pel propietari a l'entorn de proves.
- **Tancament:** les tasques no tancades del 01 es parteixen segons 2.5. El que depèn del 05b (rebut de la T-M01-16, terminis de la T-M01-49) i del 06 (T-M01-31) queda com a tasca bloquejada, amb nom.

### Llesca 2 — El primer euro (04, 05a i 05b, amb proveïdor fals)

És la llesca més important del pla: fa passar un cobrament per tots els mòduls de la fase 1 i demostra l'arquitectura abans d'omplir-la.

- **Què pot fer una persona:** un soci amb la quota pendent paga amb targeta → arriba la notificació signada del proveïdor (fals) → el càrrec passa a pagat → es crea l'ingrés a tresoreria amb el seu departament → el soci passa a actiu i el carnet és vàlid → el tresorer veu el moviment i el saldo.
- **Model:** comptes de tresoreria i centres de cost (T-M04-01, T-M04-02), moviment immutable (T-M04-03), notificació rebuda (T-M05a-04), intent de pagament (T-M05b-03).
- **Serveis:** `record_income` idempotent (T-M04-05), interfície de l'adaptador i `FakeProvider` (T-M05a-03), `start_payment` amb targeta (el tall de targeta de la T-M05b-04), processament de notificacions (T-M05b-05).
- **Vistes:** pantalla de pagament amb els seus estats; llista de moviments i saldos per al tresorer (el primer tall de la T-M04-15).
- **Proves:** signatura vàlida i invàlida, la mateixa notificació rebuda dues vegades, notificació que arriba abans que el navegador torni, i el pagament mai donat per fet només pel navegador. Cobertura completa dels càlculs.
- **Abans de començar-la:** revisar la dependència T-M05b-03 → T-M05a-08 (models de mandat). Per pagar amb targeta només cal l'adaptador; la relació amb el mandat pot arribar amb la llesca 4 [A verificar al pla abans de la primera tasca].

### Llesques 3 a 7 — Completar la fase 1

| Llesca | Què pot fer una persona en acabar | Tasques principals | Depèn de fora? |
|---|---|---|---|
| **3. Transferència i conciliació** | El soci veu la referència única, el tresorer importa l'extracte i el sistema proposa i confirma el cobrament | T-M04-10, T-M00-01, T-M04-11, T-M04-12, T-M04-14, T-M05b-06 No: banc fictici amb extracte Norma 43 ([092](../decisions/092-carril-extern-amb-proveidor-i-banc-ficticis.md)); format real [A verificar: P-45 punt 10] |
| **4. Mandat SEPA signat** | El soci tria la domiciliació, escriu l'IBAN i signa el mandat; el tresorer en veu la llista emmascarada | T-M05a-02, T-M05a-07 a T-M05a-11, T-M05a-14, T-M05a-17 | Identificador de creditor (marcador al text) |
| **Porta del nivell 1** | La campanya de mandats es pot fer amb dades reals i sense cap cobrament | T-M05a-06, T-M05a-13, T-M05a-16, T-M05a-18, T-M05a-19 i la llista de preguntes de tipus I del nivell 1 | **Sí:** proveïdor contractat i autorització de la junta |
| **5. Remesa i retornats** | El tresorer prepara la remesa, genera el fitxer, registra un retornat i el sistema reintenta o proposa una alternativa | T-M05b-01, T-M05b-09 a T-M05b-12, T-M05b-27, T-M04-13 No: banc fictici amb pain.008 i pain.002 (092); es valida contra l'esquema estàndard i s'ajusta quan respongui el banc |
| **6. Devolucions, rebut i liquidacions** | Es torna un cobrament, el soci rep el rebut i la liquidació del proveïdor quadra amb tresoreria | T-M04-06 a T-M04-08, T-M05b-07, T-M05b-13, T-M05b-14, T-M05b-16, T-M05b-21 No: liquidació del proveïdor fictici (092); format real [A verificar: P-45 punt 9] |
| **7. Tancament de la fase 1** | Arqueig, traspassos, exportació, pagaments de convidats, ajustos, guies i la revisió visual conjunta | T-M04-04, T-M04-09, T-M04-16, T-M04-18 a T-M04-20, T-M05b-08, T-M05b-17 a T-M05b-20, T-AJ-02, T-M05a-20, T-F1-01 | — |
| **Porta del nivell 2** | Cobraments reals i migració única de Cluber | T-M05b-19 i la llista de preguntes de tipus I del nivell 2 | **Sí:** proveïdor en mode real i autorització de la junta |

El **carril extern** (T-M05a-12, T-M05a-23, T-M05a-26, T-M05b-15, T-M05b-24 i T-M05b-26) ja no espera P-44 i P-45: es fa contra un proveïdor fictici «tipus PaynoPain» i un banc fictici, darrere del mateix adaptador, apagats a producció i sense xarxa ([092](../decisions/092-carril-extern-amb-proveidor-i-banc-ficticis.md)). Continuen bloquejats fins que hi hagi proveïdor real: la implementació del proveïdor real en mode de proves (T-M05a-05), activar el mode real, la certificació i les portes del nivell 1 i 2.

### Fase 2 — una llesca mínima per mòdul

| Mòdul | Llesca mínima | Necessita |
|---|---|---|
| **06 Llicències** | Un soci demana i paga una llicència; la secretaria la veu al llistat i l'exporta per a la federació | Llesca 2 i l'esdeveniment `charge.paid` (llesca 6) |
| **02 Activitats** | Es crea i es publica una sortida; un soci s'hi inscriu i paga; l'instructor té la llista del dia | Llesca 2; el catàleg i la creació d'activitats no depenen dels pagaments |
| **03 Material** | Es dona d'alta una peça, s'assigna a un inscrit i es retorna | Llesca mínima del 02 |
| **09 Marge i despeses** | Es registra una despesa amb departament i es veu el marge d'una activitat | Llesques mínimes del 02 i el 03. El nucli de despeses (T-M09-02 a T-M09-05) va abans que el 06 entri en producció (060) |
| **07 Web pública** i **08 Dashboard** | Especificació d'una pàgina i una primera pantalla amb dades reals dels mòduls anteriors | Sense secció aprovada: primer cal escriure-la |

**La branca del 02 que ja existeix.** Recomanació: aparcar-la. No s'esborra i no es fusiona sencera (té 14.700 línies, molt per sobre del límit de 4.2). Quan hi hagi un carril lliure, la part que no depèn dels pagaments (catàleg i creació d'activitats, T-M02-02 a T-M02-09) pot entrar en PR petites. La decisió és del propietari.

---

## 4. Paral·lelització

### 4.1 Què pot avançar alhora

El límit real no és quant de codi es pot escriure alhora, sinó **quant en pot absorbir una sola persona que revisa**. Per això hi ha un màxim de tres carrils oberts.

| Carril | App | Pot anar en paral·lel amb | No pot avançar sense |
|---|---|---|---|
| **A. Tresoreria** | `apps/treasury` (nova) | B i C | Els contractes de la llesca 2 |
| **B. Pagaments** | `apps/payments` (nova) | A i C | Els contractes de la llesca 2 |
| **C. Tancament del 01** | `apps/members` | A i B | — |
| **N. Nucli** | `apps/core`, `apps/accounts` | **Amb un altre canvi al nucli només si no comparteixen cap fitxer** (propietari, 16/11/2026); les migracions del nucli compten com a fitxer compartit (dues alhora deixarien dues fulles). Qui fusiona segon fa el rebase | — |
| **D. Disseny** (16/11/2026) | `static/css`, `static/js`, plantilles comunes ([recursos externs](recursos-disseny-extern.md), [`estat/DX.md`](../estat/DX.md)) | A, B i C, dins el màxim de tres carrils oberts; **una sola tasca alhora**; si xoca amb A o B, cedeix | Res; el que toqui `apps/core` o `apps/accounts` passa pel nucli |

- **A i B es troben en un contracte.** Abans de separar-se, s'escriuen i es proven les signatures on es toquen: `treasury.record_income`, l'adaptador del proveïdor i l'esdeveniment `charge.paid`. Cada carril treballa contra el contracte i contra un doble de prova de l'altre.
- **Qui fusiona i com es comença** (16/11/2026, [094](../decisions/094-fusio-de-les-risc-alt-i-tres-carrils.md)): fins a tres carrils oberts per ordre del camí crític, sense compartir fitxers de codi ni migracions; la tasca següent es comença sense demanar confirmació. Des del 18/11/2026, una `risc:alt` només es fusiona amb un sí escrit del propietari que n'esmenti el número ([098](../decisions/098-risc-alt-nomes-amb-el-si-escrit-del-propietari.md)); Claude pregunta abans al propietari només per tocar diners reals o producció, esborrar dades o canviar una norma del pla.
- **El nucli és el punt de xoc.** `apps/core/models.py` fa 1.290 línies i hi escriu tothom (el càrrec, els permisos, els ajustos). Un canvi al nucli va en una PR pròpia, petita, que es fusiona abans que les que la necessiten. Abans d'obrir-ne un mentre n'hi ha un altre d'obert, es comparen els fitxers de totes dues PR (també de l'altra sessió) i s'avisa l'altra sessió.
- **No poden anar en paral·lel:** la remesa (llesca 5) amb el mandat (llesca 4) ni amb les liquidacions del 04; el 06 i la inscripció del 02 amb res fins que existeixi la llesca 2.
- **A la fase 2**, un cop existeixi la llesca 2: el 06, el catàleg del 02 i el nucli de despeses del 09 poden anar alhora. El 03 espera la llesca mínima del 02.

### 4.2 Mida màxima d'una PR

| Límit | Valor |
|---|---|
| Codi d'aplicació canviat (sense proves, migracions ni plantilles) | 400 línies |
| Si és una PR vermella (5.2) | 200 línies |
| Abast | Una tasca del pla o un tall d'una tasca; una sola app, més les seves plantilles |
| Migracions | Una per app i per PR |
| Proves | Sense límit |

Si una tasca no hi cap, es talla. Un pas del CI compta les línies i falla si es passa del límit, tret que la PR porti l'etiqueta `gran-justificada` amb el motiu a la descripció (per exemple, una migració de dades inicials generada).

### 4.3 Estratègia de branques

- **Una sola branca llarga: `master`**, protegida i sempre desplegable a l'entorn de proves.
- **Branques curtes, una per PR**, que surten de `master`: `tasca/T-M04-03-moviment-immutable`. S'esborren en fusionar.
- **Fusió per aixafament** (un commit per PR), amb l'identificador de la tasca al títol.
- **Cap branca d'integració ni de tanda** (`night/…`, `integracio/…`). Una tanda de nit pot fer diverses tasques, però cada tasca és la seva branca i la seva PR. Com a molt, una PR apilada sobre una altra.
- **El que no està acabat entra apagat**, darrere d'un interruptor, en lloc de viure en una branca llarga.
- **Abans de fusionar, la branca es posa al dia amb `master`.** Si dues PR creen migracions de la mateixa app, la segona regenera la seva.
- Els arbres de treball continuen fora del disc C, com fins ara.

### 4.4 L'estat surt del pla

Un fitxer per mòdul a `docs/estat/` (per exemple, `docs/estat/M04.md`) amb una línia per tasca: identificador, estat, PR i bloqueig si en té. El pla hi enllaça. Així:

- dues branques ja no xoquen a `planning.md`;
- no cal cap commit per anotar que el CI és verd, perquè amb `master` protegida una PR fusionada sempre l'ha passat;
- la skill `propera-tasca` llegeix un fitxer de trenta línies en lloc d'un d'1 MB.

El diari de construcció es manté, en un commit propi **dins la mateixa PR** de la tasca.

---

## 5. Control de qualitat automàtic

### 5.1 Què ja hi ha i què s'hi afegeix

| Control | Avui | Proposta |
|---|---|---|
| Proves (`pytest-django`) | 2.093, a cada push i PR | Es mantenen. Cada criteri d'acceptació continua tenint la seva prova |
| Proves al navegador | Sí, amb captures si fallen | S'hi afegeix una prova de flux sencer per llesca |
| Lint i format (`ruff`) | Sí, amb regles de seguretat i de traducció | Es manté |
| Migracions al dia | Sí | S'hi afegeix un avís quan una migració esborra o estreny una columna (obliga a PR vermella) |
| Escaneig de secrets | Sí, sobre tota la PR ([078](../decisions/078-escaneig-de-secrets-de-tota-la-pr-limit-de-30-commits.md)) | Es manté |
| Rutes públiques declarades | Sí (`test_access.py`) | S'estén a les apps noves |
| **Cobertura** | **No es mesura** | Mesurar-la al CI. Mínim global: el valor del primer dia, que no pot baixar, amb l'objectiu del 90 % de línies i branques. **100 % als mòduls de càlcul econòmic** (càrrecs, quotes, tresoreria i transicions de pagament), tal com ja exigeix CLAUDE.md. Cal aprovar la dependència `pytest-cov` |
| **Fronteres entre apps** | Regla escrita, sense prova | Una prova que falla si una app importa els models d'una altra en lloc dels seus serveis. Sense cap dependència nova |
| **Interfície només amb tokens** | Regla escrita; només es comprova als recorreguts dels wireframes | Una prova que falla si una plantilla porta `style=` o un color fora de `tokens.css` |
| **Protecció de `master`** | No | Només per PR, amb tots els controls en verd i la branca al dia. Sense pujades directes ni forçades [A verificar: el repositori és privat i la protecció de branques depèn del pla de GitHub] |
| **Mida de la PR** | No | El pas de 4.2 |
| **Revisió de codi abans de la persona** | A mà | Cada PR groga o vermella passa per una revisió automàtica de codi i, si toca seguretat, per una de seguretat. El resultat es resumeix a la PR |
| **Desplegament** | No | Cada fusió es desplega a l'entorn de proves i s'hi comprova que respon |

### 5.2 Tres classes de PR

El control es posa on hi ha el risc. La classe la declara qui obre la PR i la comprova un fitxer de propietaris per camí (`CODEOWNERS`): si la PR toca un camí vermell, és vermella encara que digui una altra cosa.

| Classe | Què hi entra | Com es fusiona |
|---|---|---|
| **Verda** | Proves, refactors sense canvi de comportament, textos de la interfície, plantilles fetes amb components existents, documentació que no és norma | Sola, amb el CI verd |
| **Groga** | Funcions dins l'especificació congelada que no toquen diners, permisos ni el model de dades personals | Amb el CI verd i la revisió automàtica sense objeccions. El propietari la veu a la revisió setmanal i es pot revertir |
| **Vermella** | Càlculs i moviments de diners, pagaments i notificacions, autenticació i sessions, permisos, RGPD i anonimització, xifratge, importacions, migracions que modifiquen o esborren dades, dependències noves, el CI, `CLAUDE.md` i les regles del pla | **El propietari l'aprova abans de fusionar** |

Això canvia la regla de la metodologia («es fusiona només si ho validen la IA i una persona») per a les classes verda i groga. Es pot fer perquè `master` només es desplega a un entorn de proves amb dades inventades; l'entrada en producció continua tenint les seves portes amb revisió completa. Si el propietari no ho vol, l'alternativa conservadora és que també aprovi les grogues, a canvi d'anar més a poc a poc.

### 5.3 Plantilla de PR

```markdown
## Què fa
<!-- Dues frases. Què pot fer ara una persona que abans no podia. -->

- Tasca: T-…        Llesca: …
- Especificació: docs/planning.md#…
- Classe: verda | groga | vermella (per què)

## Criteris i proves
| Criteri | Prova |
|---|---|
| CA-… | fitxer::prova |

## Com es comprova a l'entorn de proves
1. Entra com a … 2. Ves a … 3. Hauries de veure …

## Seguretat i privacitat
- Permís que s'exigeix al servidor:
- Dades personals que es mostren o es desen:
- Què queda al registre d'activitat:

## Decisions
- Preses per l'equip (tipus R o C), amb l'opció triada:
- Noves a pendents.md (tipus I), amb l'interruptor que queda apagat:

## Comprovacions
- [ ] Proves i lint en verd
- [ ] Captures a 1280 i 390 px mirades (si toca pantalles)
- [ ] Migració reversible, o explicat per què no
- [ ] Estat de la tasca i diari actualitzats
```

### 5.4 Què mira el propietari en una PR vermella

El propietari revisa **comportament i decisions**, no codi línia per línia. La seguretat a nivell de codi la donen les proves, la revisió automàtica i la mida petita.

1. Entenc què fa amb les dues frases del principi?
2. Fa només el que diu la tasca, sense res de més?
3. Cada criteri de la taula té una prova?
4. Ho he provat jo a l'entorn de proves seguint els tres passos?
5. He provat d'entrar-hi amb un rol que no hi hauria de poder entrar?
6. Si hi ha diners: els imports són els que esperava i hi ha un exemple amb números?
7. Estic d'acord amb les decisions que l'equip ha pres sol?
8. Hi ha alguna pregunta de tipus I que hagi de portar a la junta?

---

## 6. Rol del propietari

### 6.1 Qui decideix què

| Ho decideix l'equip sol | Ho decideix el propietari | El propietari ho porta a un altre |
|---|---|---|
| Dubtes de tipus R i valors inicials de tipus C | Dubtes de tipus I | Regles del club: junta |
| Noms, estructura interna i disseny de proves | Canvis a l'especificació congelada | Imports, terminis i conciliació: tresorer |
| Textos provisionals de pantalla i de correu | PR vermelles | Procediments d'altes i baixes: secretaria |
| Ordre de les tasques dins d'una llesca | Dependències noves i qualsevol cost | Textos legals i conservació: gestoria i assessor |
| Refactors sense canvi de comportament | Ordre de les llesques i què s'aparca | Banc i proveïdor de pagaments |
| Fusió de PR verdes i grogues | Pas als nivells 1 i 2 (amb la junta) | |

### 6.2 Revisió setmanal

Un sol document per revisió (`docs/revisions/revisio-NN.md`), preparat per l'equip, pensat perquè el propietari el resolgui en una sola sessió. Les preguntes es responen amb una lletra, com ja es fa a les decisions 079 i 085.

```markdown
# Revisió NN

## 1. Prova-ho tu
Adreça de l'entorn de proves i tres recorreguts per fer (un per llesca tocada).

## 2. Què s'ha fusionat
| Llesca | Tasques tancades | PR verdes | PR grogues | PR vermelles |

## 3. Decisions
### A. Et necessitem (tipus I) — com a màxim 10
| Codi | Pregunta | Opcions | Recomanació | Què bloqueja | Resposta |

### B. Ho hem decidit nosaltres (tipus R i C)
| Codi | Què hem triat | Per què | Com es desfà |
Si no hi dius res, queda així.

### C. Per portar a algú altre
| A qui | Pregunta, en el llenguatge del club | Què bloqueja |

## 4. PR vermelles que esperen la teva aprovació
| PR | Què fa | Com provar-la |

## 5. Indicadors
Llesques demostrables · tasques en curs · preguntes de tipus I per porta · mida mitjana de les PR

## 6. Què ve ara
La llesca següent i què necessitem de tu per començar-la.
```

Regles del format:

- **Silenci a la part B: s'accepta.** Les decisions de tipus R i C queden fermes si el propietari no hi diu res.
- **Silenci a la part A: continua apagat.** Una pregunta de tipus I no s'activa mai sola.
- **Màxim 10 preguntes a la part A.** Si n'hi ha més, les altres esperen la revisió següent. Això obliga a triar les que bloquegen una porta.
- **Les respostes es registren en una sola decisió numerada per revisió.**
- **La part C és una llista per endur-se**, ordenada per destinatari, perquè el propietari la pugui portar a la junta, al tresorer o a la secretaria sense reescriure-la.

### 6.3 Indicadors

Quatre, sense cap data:

1. **Llesques demostrables** a l'entorn de proves (acumulat). És l'indicador principal.
2. **Tasques en curs alhora.** Límit: tres carrils i tres PR vermelles esperant.
3. **Preguntes de tipus I obertes per porta** (nivell 1 i nivell 2). Han de baixar a zero abans de cada porta.
4. **Mida mitjana de les PR** i quantes han necessitat l'etiqueta `gran-justificada`.

---

## 7. Primers passos concrets

Cinc tasques, en aquest ordre. Les dues primeres no toquen codi de producció.

### Tasca 1 — Registrar les regles noves

Decisió numerada amb el que s'aprovi de l'apartat 9; actualització de `CLAUDE.md` i de la metodologia; etiqueta `spec-fase1-v1`.

**Criteri d'acceptació:** la decisió existeix i diu, per a cada punt de l'apartat 9, què s'ha aprovat. `CLAUDE.md` descriu els tres tipus de dubte, les tres classes de PR i el límit de mida. L'etiqueta apunta al commit de l'especificació congelada. Cap regla de negoci del pla ha canviat.

### Tasca 2 — Baranes automàtiques

Protecció de `master`, plantilla de PR, `CODEOWNERS` amb els camins vermells, pas de mida de la PR, cobertura al CI i proves de fronteres entre apps i de tokens.

**Criteri d'acceptació:** una pujada directa a `master` es rebutja. Una PR de prova amb 401 línies de codi d'aplicació falla, i passa amb l'etiqueta. Una PR de prova que toca `apps/core/charges.py` demana l'aprovació del propietari. El CI publica la cobertura i falla si baixa del valor inicial o si un mòdul de càlcul econòmic no arriba al 100 %. Una plantilla de prova amb `style=` fa fallar el CI.

### Tasca 3 — Entorn de proves (llesca 0)

**Criteri d'acceptació:** el propietari obre una adreça amb HTTPS, hi entra amb un compte de prova de cada rol i veu socis inventats. Una fusió a `master` hi arriba sense cap pas manual. No hi ha cap dada real, cap correu surt cap a fora i el servidor és a la UE. El desplegament es pot desfer tornant a la versió anterior. La manera d'entrar-hi i de refer-lo és escrita en una pàgina.

### Tasca 4 — Sanejar l'estat i tancar la llesca 1

Partir les tasques no tancades del 01, moure l'estat a `docs/estat/`, afegir tipus, opció per defecte i porta a les files obertes de `pendents.md`, resoldre les branques a mig fusionar i afegir la prova de flux sencer.

**Criteri d'acceptació:** cap tasca del 00 ni del 01 és «feta en part» ni «pendent de validació»: totes són per fer, en curs, fetes o bloquejades, i cada bloquejada diu per què. Cada fila oberta de `pendents.md` té tipus, opció per defecte, què bloqueja i qui respon. Cada branca antiga s'ha comprovat i s'ha fusionat o esborrat, tret de la del 02 si s'aparca. Una prova al navegador fa el flux de la sol·licitud al carnet verificat, i el propietari l'ha repetit a mà a l'entorn de proves.

### Tasca 5 — Contractes de la llesca 2

Interfície de l'adaptador i `FakeProvider` (T-M05a-03), signatura de `treasury.record_income` i de `members.on_fee_paid` amb les seves proves de contracte, i l'esquelet buit de les apps `treasury` i `payments`. PR vermella.

**Criteri d'acceptació:** les proves de contracte passen contra dobles de prova. El proveïdor fals reprodueix un pagament correcte, un de denegat, una notificació repetida i una amb la signatura incorrecta. La dependència T-M05b-03 → T-M05a-08 està resolta per escrit. A partir d'aquesta PR, el carril A i el carril B poden obrir cadascun la seva sense tocar cap fitxer de l'altre.

**En paral·lel a tot això, i sense esperar res:** enviar al banc i al proveïdor de pagaments les preguntes de [P-45](../decisions/pendents.md) i demanar l'entorn de proves. És una gestió del propietari, no una tasca de codi, i és el que més condiciona quan es podrà cobrar.

---

## 8. Riscos d'aquest pla

| Risc | Com es limita |
|---|---|
| Refer feina quan una resposta no sigui l'opció per defecte | Només es tanquen sols els dubtes barats de desfer (R i C). Els cars queden apagats |
| Una PR groga introdueix un error sense que cap persona l'hagi mirat | Només arriba a l'entorn de proves, amb dades inventades. Les portes de producció mantenen la revisió completa. Tot es pot revertir |
| Els interruptors s'acumulen i ningú no sap què és apagat | Cada interruptor té una fila a `pendents.md` i surt a la llista de la seva porta. A cada porta, o s'activa o s'esborra |
| El proveïdor real es comporta diferent del fals | El carril extern es fa contra un proveïdor i un banc ficticis amb els formats desconeguts marcats [A verificar] (092). Quan hi hagi entorn de proves del proveïdor, només canvia l'adaptador concret i les proves de contracte es tornen a passar contra el real |
| L'entorn de proves té un cost | És temporal i es pot crear i destruir ([010](../decisions/010-entorns.md)). El cost s'ha de confirmar abans d'aprovar la tasca 3 [A verificar: preu vigent] |
| El propietari continua sent el coll d'ampolla | El límit de 10 preguntes i de 3 PR vermelles fa visible la cua. Si s'omple, s'atura un carril en lloc d'acumular feina |

---

<a id="aprovar"></a>
## 9. Què ha d'aprovar el propietari

| # | Decisió | Recomanació | Alternativa |
|---|---|---|---|
| 1 | Congelar l'especificació de la fase 1 i treure l'estat de les files del pla (2.1, 4.4) | Sí | Continuar amb addendes |
| 2 | Regla dels tres tipus de dubte: R i C es construeixen amb l'opció per defecte; I queda apagat fins a la resposta (2.3). **Canvia CLAUDE.md** | Sí | Mantenir la regla actual: un dubte atura la tasca |
| 3 | Construir per llesques que travessen 04, 05a i 05b, començant pel primer euro (apartat 3). Precisa la 024 i la 060 sense canviar-ne les dependències | Sí | Mòdul sencer darrere mòdul sencer |
| 4 | Tres classes de PR, amb fusió sense aprovació humana per a les verdes i les grogues (5.2). **Canvia la metodologia** | Sí | El propietari aprova també les grogues |
| 5 | Entorn de proves temporal, amb el seu cost, i dependència `pytest-cov` (tasques 2 i 3) | Sí | Seguir només en local |
| 6 | Què es fa amb la branca del 02 (apartat 3) | Aparcar-la | Fusionar-ne ara la part que no depèn de pagaments, en PR petites |
