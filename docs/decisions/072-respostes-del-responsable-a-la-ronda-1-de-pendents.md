# 072 — Respostes del responsable a la ronda 1 de pendents

- **Data:** 09/11/2026
- **Estat:** Acceptada pel responsable del projecte el 09/11/2026.
- **Origen:** respostes escrites al document de consulta «C.R.I.S. — Decisions i validacions pendents per tasca» (revisió del 06 i 07/11/2026, **ronda 1**, preguntes Q-001 a Q-238; és fora del repositori) i instruccions del responsable del 09/11/2026 sobre les contradiccions que s'hi van trobar.
- **Abast:**
  - **Substitueix el punt 3 de la [070](070-quota-integra-i-renovacio-als-12-mesos-del-pagament.md) només en la separació dels terminis**: els tres pagaments ja no van «separats per dos mesos», sinó repartits equitativament dins dels 12 mesos.
  - **Tanca** la [P-54](pendents.md), la [P-57](pendents.md) i la [P-58](pendents.md).
  - **Resol en part** la P-12, la P-29, la P-33, la P-49, la P-50, la P-53 i la P-61.
  - **Precisa** regles i supòsits del 01 a l'[addenda de la 072](../planning.md#M01-addenda-072) del pla.

## Context
El document de la ronda 1 recollia 238 preguntes. El responsable va respondre la Q-001 a la Q-089 (menys la Q-036) i la Q-091; la resta són en blanc. En revisar-les el 09/11/2026 van sortir contradiccions amb la 070, posterior al document, i el responsable les va resoldre per escrit (vegeu «Contradiccions resoltes»).

**Quin registre és més recent.** El document de la ronda 1 recull l'estat del 07/11/2026 a les 00:12. La 070 és del 09/11/2026 (commit 7fa8b97, 01:11) i recull la resposta a la Q-005, la Q-006 i la Q-007 (cap prorrata i renovació als 12 mesos del pagament). Per tant, **la 070 és el registre més recent**. Les respostes de la Q-060 («any natural») i de la Q-076 («fins al final de l'any») copien supòsits anteriors a la 070, i el responsable ha confirmat que mana la 070.

**Criteri.** Les respostes a preguntes de tipus «decisió» i les de govern del club que el responsable ha decidit s'apliquen com a decisió. Les que depenen d'un fet extern o d'una interpretació legal queden com a posició del responsable, amb la marca de qui les ha de confirmar: Q-016, Q-029, Q-030, Q-034 i Q-035 (assessor de protecció de dades), Q-062 (gestoria, per a l'avís previ SEPA), Q-063 (junta), Q-089 (banc) i Q-091 (PaynoPain).

## Decisió

### 1. Quotes, exempts i terminis

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-001 | Exempts per edat (P-57) | **Opció 1.** Passen a «actiu» en aprovar l'alta, amb carnet i sense cap quota ni càrrec de 0 €. Entrada d'historial amb el motiu «sense quota exigible (RN-M01-65)» | RN-M01-07, RN-M01-18, RN-M01-67; T-M01-14, T-M01-19 |
| Q-002 | Validesa del carnet d'un exempt | **Opció 1.** Fins al 31/12 de l'últim any exempt (any de naixement + 14). Una baixa continua revocant el carnet | RN-M01-19; T-M01-19, T-M01-20 |
| Q-003 | L'1 de gener en què comença a pagar | **Opció 1.** Continua «actiu» i se li genera la quota. A partir d'aquí, la 070 (renovació als 12 mesos del pagament). Si no paga, el tresorer el marca impagat a mà ([040](040-impagat-es-marca-a-ma.md)) i el carnet no és vàlid fins que pagui | T-M01-18 |
| Q-004 | Altres exempcions | No n'hi ha cap més aprovada. Es vol poder eximir un soci de la quota d'un període, en l'alta o en qualsevol moment. **Instrucció del 09/11/2026:** es fa com una **anul·lació amb motiu i amb un permís propi**, mai com un pagament de 0 € | RN-M01-72 i T-M01-40 (sense implementar) |
| Q-005 a Q-007 | Prorrata | Cap prorrata: ja ho recull la 070 | — |
| Q-008 | Quota anul·lada i retorn dins del mateix període (P-54) | **Sortida E.** Una quota nova del mateix període; l'anul·lada es queda a l'historial i no es pot pagar (un càrrec anul·lat ja no canvia, RN-67). «Vàlid fins a» = la data de renovació de la quota pagada més recent (070). El mateix val per a un segon canvi de tipus dins del període. Cal un ordinal a la clau d'`AnnualFee`: canvi de model a la T-M01-14 o a la T-M01-18 | RN-M01-12; T-M01-14, T-M01-17, T-M01-18 |
| Q-009 | Prorrata en una readmissió | Substituïda per la 070: la readmissió paga la quota íntegra | — |
| Q-019 | 3 × 32 € | S'ofereix, per al soci de ple dret | P-61 |
| Q-020 | Calendari dels tres pagaments | El primer en l'alta o la renovació; els altres dos, **repartits equitativament dins dels 12 mesos** (és a dir, cada quatre mesos; el càlcul exacte de les dates es fixa a la T-M01-18). Substitueix «separats per dos mesos» de la 070 | P-61; T-M01-18 |
| Q-021 | Per què 96 € | Preu fixat per la junta | — |
| Q-022 | Un termini que no es paga | El soci queda en suspens per impagat i no pot fer servir cap servei, curs ni activitat del club. Continua obert si el suspens és la marca manual d'impagat (040) o un bloqueig automàtic | P-61 |
| Q-023 | Mentrestant | Només la quota anual | — |
| Q-060 | Venciment (P-29) | **Instrucció del 09/11/2026:** per als que paguen, mana la 070 (venciment als 12 mesos del pagament confirmat). L'any natural només s'aplica als exempts (Q-002 i Q-003). Continua obert a la P-29: el calendari de la remesa i de la campanya de mandats | RN-M01-17, S-M01-03 |
| Q-061 | Dies dels recordatoris | 15 dies abans, el dia abans i el mateix dia del venciment, i 15 i 30 dies després si no s'ha pagat. Configurables | RN-M01-14, S-M01-04 |
| Q-062 | Avís previ de la renovació | Una setmana abans, configurable. La data límit per demanar la baixa abans de la renovació no s'ha respost. L'avís previ d'un rebut domiciliat (S-M05b-06, 14 dies naturals com a supòsit) és un altre avís i el confirmen el banc i la gestoria | T-M01-18, 05b |
| Q-077 | Quotes cobrades per Cluber | Informatives, no són ingressos. Al començament, el tresorer quadra a mà el compte del club (saldo d'obertura) | RN-M01-33; 04 |
| Q-078 | Llicències entre Cluber i el 06 | A mà, una a una, amb la llista que ja té el club i l'aplicació de la FECDAS. L'administració amb permís hi posa la llicència i si està pagada, sense comptar-ho com a ingrés | T-M01-23, 06 |

### 2. Canvi de tipus i baixa

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-049 | Import del canvi a ple dret | La diferència entre quotes (55 €) | RN-M01-15, S-M01-01 |
| Q-050 | Quan és efectiu | Quan el suplement està pagat | P-M01-B, pas 3 |
| Q-051 | De ple dret a simpatitzant | A la renovació següent (amb la 070, la següent data de renovació) | P-M01-B |
| Q-052 | Des d'on resol el President | Resposta: «el President ha de tenir un rol, igual que els altres». No tria entre resoldre des de la vista de sol·licituds o donar-li P4. **Continua oberta** | T-M01-17 |
| Q-053 | Canviar el tipus d'un soci de baixa | Opció 1: no; si torna, tria el tipus en la readmissió | T-M01-17 |
| Q-054 | Motiu en el canvi de tipus d'un impagat | Opció 1: es manté | T-M01-17 |
| Q-055 | Qui rebutja una baixa (P-50) | Qui tingui permís d'edició de les sol·licituds; amb només lectura, no. Els motius no estan fixats | T-M01-17 |
| Q-056 | Quotes pendents en una baixa | **Instrucció del 09/11/2026:** RN-M01-20 tal com és. Les pendents posteriors a la data efectiva s'anul·len amb motiu; les anteriors se segueixen devent | RN-M01-20, S-M01-05 |
| Q-057 | Perdonar o anul·lar una quota anterior | Qui tingui permís d'edició de les quotes; amb només lectura, no. Sempre una anul·lació amb motiu, mai un esborrat. El permís concret es fixa a la T-M01-17 | T-M01-17 |
| Q-058 | Què veu el soci abans de demanar la baixa | A criteri de l'equip. Proposta per a la T-M01-17: la data efectiva, les quotes pendents i què se'n farà (RN-M01-20), que el carnet es revoca i que el compte personal es manté (Q-059) | T-M01-17 |
| Q-059 | Compte personal després de la baixa | Es manté, per tenir l'historial | S-M01-12 |

### 3. Carnet i verificació

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-063 | Número a la verificació pública | El número sencer (són números petits). **Pendent de la confirmació de la junta: no es publica fins que la junta el confirmi**; mentrestant, la verificació es queda com està | RN-M01-26, S-M01-06; T-M01-20, T-M01-26 |
| Q-064 | Nom de pila a la verificació | Sí | RN-M01-26, S-M01-07; T-M01-20 |
| Q-065 | Darrere del carnet | En el carnet digital, el contingut del wireframe | S-M01-08; T-M01-19 |
| Q-066 | Insígnia de soci clàssic | Sense llindar automàtic (no hi ha l'historial real de tothom). L'administració l'assigna a mà com a reconeixement; el carnet passa a una versió daurada que conserva el disseny, i el voltant de la foto o l'avatar del perfil també. **Sense tasca encara** | RN-M01-23, S-M01-09 |
| Q-067 | Antiguitat en una readmissió | Des de la primera alta | S-M01-10 |
| Q-075 | Data d'alta que Cluber no té | No se'n posa cap i no es mostra l'antiguitat d'aquests socis. Substitueix el supòsit «data més antiga coneguda, aproximada» | RN-M01-21, S-M01-18; T-M01-25 |
| Q-076 | Carnet dels importats amb la quota pagada a Cluber | Sí, vàlid. Amb la 070 (instrucció del 09/11/2026), vàlid fins a 12 mesos després de l'última renovació registrada a Cluber, no fins al final de l'any | RN-M01-34, S-M01-24; T-M01-25, T-M01-19 |

### 4. Menors i alta

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-010 | Document d'un menor | El del menor és opcional i el del representant és obligatori (ja és la RN-M01-70) | — |
| Q-011 | Correu i telèfon d'un menor | **Opció 3.** Els del menor, opcionals; els del representant, obligatoris. El rebut i els avisos van al representant. Canvi de model i de formulari: `MemberRequest` no té el correu ni el telèfon del representant | T-M01-13 (canvi), T-M01-14 |
| Q-012 | Compte personal d'un menor | **Opció 1.** Cap compte personal abans dels 14 anys; a partir dels 14, compte propi amb el seu correu. En aprovar l'alta d'un menor de 14 anys no s'envia cap invitació | T-M01-14, T-M01-16 |
| Q-013 | Persona de referència per a menors | El Secretari. El protocol no està fixat | Checklist H5 |
| Q-014 | Mandat SEPA d'un menor | El signa el representant que ha autoritzat l'alta | RN-M05a-13 |
| Q-015 | Menors a les activitats | L'edat mínima és un requisit configurable per activitat, com el nivell o les especialitats | 02 |
| Q-016 | Consentiments quan el menor es fa gran | Posició del responsable: als 14 anys, el menor accepta ell mateix la política de privacitat; les obligacions econòmiques continuen amb el representant fins als 18; als 18 ho accepta tot sol. **[A validar: assessor de protecció de dades]** | T-M01-16, T-M01-22 |
| Q-017 | Passaport | **Opció 3.** El passaport només s'admet a l'alta presencial | T-M01-13 (canvi) |
| Q-018 | Data de naixement (punt 0 de l'ordre del dia) | Tancat amb la 068 | Ordre del dia |
| Q-025 | Sol·licituds que no es resolen | No caduquen; la secretaria les rebutja amb motiu | T-M01-14 |
| Q-026 | Dades del representant | Es conserven mentre la persona sigui sòcia | T-M01-22 |
| Q-042 | Contacte nou d'una persona que ja existeix | **Opció 1.** Es desa a la sol·licitud, visible només per a qui revisa l'alta; en aprovar, la secretaria decideix si actualitza la persona, amb registre | T-M01-14 |
| Q-043 | Comprovació del representant | **Opció 2.** La secretaria comprova el document del representant i ho deixa registrat abans d'aprovar. Si es guarda una còpia: per decidir (proposta: no; només la marca, qui i quan) | T-M01-14 |
| Q-044 | Acceptacions en aprovar | **Opció 1.** Només les del sol·licitant passen a `core.Consent`, amb referència a la sol·licitud; les del representant es queden a la sol·licitud | T-M01-14 |

### 5. Textos legals, consentiments i idiomes

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-027 | Terminis legals de conservació (Q-14) | Esborrany preparat a [docs/esborranys/terminis-de-conservacio.md](../esborranys/terminis-de-conservacio.md). **No és vàlid fins que el confirmi la gestoria** | S-M01-15, T-M01-22 |
| Q-028 | Textos legals de l'alta (Q-16) | Esborrany preparat a [docs/esborranys/textos-legals.md](../esborranys/textos-legals.md). **No és vàlid fins que l'aprovin la junta i l'assessor de protecció de dades** | Checklist H1 |
| Q-029 | Una versió nova obliga a tornar a acceptar? | No (es manté el supòsit de la T-M01-08) [A validar: assessor de protecció de dades] | T-M01-08 |
| Q-030 | Prova del consentiment presencial | N'hi ha prou amb el registre de qui fa l'alta [A validar: assessor de protecció de dades] | T-M01-13 |
| Q-031 | Butlletí i imatges | Es demanen **a l'alta**, amb les caselles **desmarcades per defecte** (instrucció del 09/11/2026), i es poden canviar al perfil. Substitueix el supòsit de la T-M01-13 de no posar la casella del butlletí | T-M01-13 (canvi), T-M01-16 |
| Q-032 | Llengües (P-49) | Català, castellà, anglès, basc, gallec i francès, a tota la plataforma, amb una manera fàcil d'afegir-ne d'altres | P-49, T-M01-09b |
| Q-033 | Qui tradueix | Una eina de traducció automàtica, perquè no calgui fer-ho a mà (per exemple, els butlletins). Els textos legals continuen sota la Q-034 i la Q-035 | P-49 |
| Q-034 | Quina versió preval | El català [A validar: assessor de protecció de dades] | P-49 |
| Q-035 | Consentiment en una altra llengua | N'hi ha prou amb el primer consentiment [A validar: assessor de protecció de dades] | P-49 |
| Q-037 | Qui registra un cobrament manual (P-12) | Qui tingui permís de veure i editar la tresoreria | 04, 05b |
| Q-038 | Justificant del cobrament manual | Comprovant opcional. El motiu continua sent obligatori (CLAUDE.md) | 04, 05b |
| Q-039 | Qui atén les sol·licituds RGPD | L'administrador | S-M01-14 |
| Q-045 a Q-048 | Camps opcionals del perfil (P-58) | Tots els candidats menys «observacions» (Q-045, opció 2). **Instrucció del 09/11/2026 per a la Q-046:** només entren els que tenen una finalitat justificable. Entren el **telèfon fix** (canal de contacte alternatiu, voluntari) i l'**adreça desglossada** en codi postal, població i província (correspondència i tràmits; la província la demana el model 182 si el club emet certificats de donatiu [A verificar: gestoria]). Queden fora la **nacionalitat** i la **professió**, que no tenen cap finalitat justificable ara. Els veuen i editen el soci i l'administració amb permís de camp (Q-047); es conserven, s'exporten i s'anonimitzen com la resta del perfil (Q-048) | T-M01-16, T-M01-22 |

### 6. Comptes, seguretat i operació

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-040 | Límits del formulari «Fer-se soci» | Acceptats com a valors inicials configurables: 5 sol·licituds per origen cada 60 minuts i 3 rebuts per adreça al dia | T-M01-13 |
| Q-041 | Commit de la T-M01-13 | Sí (ja fet: 7fa8b97) | — |
| Q-079 | Canvis de perfil al registre per a P20 | **Opció 1.** P20 també veu els canvis de perfil de la persona d'un soci, amb els camps protegits ocults si no té el permís de camp | T-M01-07b, T-M01-15b, T-M01-16 |
| Q-080 | Credencial temporal | Per telèfon o en persona; s'ha de canviar en la primera entrada. (La resposta esmenta els socis migrats, però la Q-03 només tracta els comptes d'administrador restablerts; els comptes personals dels socis migrats són de la T-M01-25 i del 05a) | T-M01-05 |
| Q-081 | Paleta del 31/10 | Opció 1: es registra com a decisió i s'actualitza el sistema de disseny. **Acció pendent**, no feta en aquesta decisió | T-M01-38 |
| Q-082 | Eina d'accessibilitat | axe amb Playwright | T-M01-28 |
| Q-083 | Hora de la comprovació diària de la llicència | 00:00. Ha d'anar després de la tasca diària del 06, que encara no té hora. On es veu el resum: no respost | T-M01-31 |
| Q-084 | T-M01-39 (P-53) | **Aprovada**, començant per la mesura (part a) | T-M01-39 |
| Q-085 | Retard de 5 minuts i frase | Sí. Idea del responsable: un comptador visible, perquè 5 minuts poden semblar molts | T-M01-39 |
| Q-086 | La cua, condició del nivell 1? | Delegada a l'equip. Proposta: decidir-ho amb la mesura (a) feta abans i després, també darrere del proxy; si la diferència continua fora del soroll, és condició del nivell 1. **Continua oberta** | T-M01-39 |
| Q-087 | Comptes d'emergència | No els fa servir ningú i no tenen cap perfil de soci associat. El model `accounts.Account` exigeix una persona: la T-M00-03 ha de resoldre com (per exemple, una persona tècnica sense dades personals) [A validar] | T-M00-03 |
| Q-088 | Sessions obertes d'un compte bloquejat | Es tanquen totes | T-M00-05, T-M01-22 |
| Q-089 | Format de l'extracte | Supòsit: CSV amb data, concepte, import i saldo. El responsable pregunta si hi va el nom del titular. **Pendent del banc** | T-M00-01 |
| Q-091 | Targeta guardada per a les renovacions | El responsable entén que sí. **Pendent de la confirmació de PaynoPain** | T-M05a-12 |

## Contradiccions resoltes (instruccions del 09/11/2026)
1. **Q-060 i Q-076 davant de la 070:** mana la 070 per als que paguen. L'any natural només per als exempts.
2. **Q-020 davant de la 070:** terminis repartits equitativament dins dels 12 mesos; es corregeix la P-61.
3. **Q-056:** RN-M01-20 tal com és.
4. **Q-004:** anul·lació amb motiu i amb un permís propi, com a tasca nova sense implementar ([T-M01-40](../planning.md#M01-addenda-072)).
5. **Q-031:** la casella del butlletí (i la de les imatges) va desmarcada per defecte.
6. **Q-024 i Q-073:** continuen pendents; el responsable les tornarà a respondre.

## Continuen obertes
- **Pendents de nova resposta:** Q-024 (conservació de les sol·licituds rebutjades) i Q-073 (conservació de les línies de la importació). La resposta a la Q-073 copiava el supòsit.
- **Sense decidir:**
  - la Q-052 (President);
  - la Q-086 (nivell 1);
  - de la P-61, quan passa a actiu i fins quan té carnet qui paga a terminis, si el suspens és manual o automàtic, quan es poden triar els terminis i què passa amb els menors;
  - de la P-29, el calendari de la remesa i de la campanya de mandats;
  - de la Q-062, la data límit per demanar la baixa;
  - de la Q-083, on es veu el resum.
- **En blanc al document:** Q-036, Q-090, Q-092, Q-093 i de la Q-104 a la Q-238. De la Q-094 a la Q-103 eren validacions de la T-M01-13, que ja és «Feta» (09/11/2026).
- **R2-13 i R2-21:** codis d'una segona ronda (R2) que no és al repositori. Només apareixen a la fila de la T-M01-15 i a l'índex del diari, des del commit 1dafae2, sense cap definició.

## Conseqüències
- [pendents.md](pendents.md):
  - la P-54, la P-57 i la P-58 passen a «Resolts»;
  - la P-61 es corregeix (terminis) i rep les respostes de la Q-019 a la Q-023;
  - la P-12, la P-29, la P-33, la P-49, la P-50 i la P-53 reben les respostes parcials.
- [Pla](../planning.md): [addenda de la 072](../planning.md#M01-addenda-072) amb la RN-M01-72, la CA-M01-65 a la CA-M01-67 i la T-M01-40. Hi ha precisions datades a la RN-M01-14, 15, 18, 19, 20, 21, 23, 26 i 34, als supòsits S-M01-01, 03 a 10, 12, 14, 18 i 24, a la T-M01-13 (límits) i a la T-M01-39 (aprovada).
- **Canvis a la T-M01-13, que ja està «Feta»:**
  - butlletí i imatges desmarcats (Q-031);
  - contacte del representant (Q-011);
  - passaport a l'alta presencial (Q-017).

  No s'implementen sense que el responsable n'aprovi l'abast.

## Fonts
- Document de consulta de la ronda 1 (07/11/2026, fora del repositori), amb les respostes del responsable.
- Instruccions del responsable del projecte del 09/11/2026.
- Decisions [040](040-impagat-es-marca-a-ma.md), [059](059-rols-i-permisos-editables.md), [067](067-readmissio-d-un-antic-soci.md), [068](068-socis-menors-i-inici-del-pagament-de-la-quota.md), [069](069-condicio-de-soci-i-quota-d-alta-per-mesos.md) i [070](070-quota-integra-i-renovacio-als-12-mesos-del-pagament.md).
