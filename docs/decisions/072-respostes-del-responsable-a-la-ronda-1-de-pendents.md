# 072 — Respostes del responsable a la ronda 1 de pendents

- **Data:** 09/11/2026
- **Estat:** Acceptada pel responsable del projecte el 09/11/2026, amb correccions del mateix dia (segona, tercera i quarta instruccions escrites).
- **Origen:** respostes escrites al document de consulta «C.R.I.S. — Decisions i validacions pendents per tasca» (revisió del 06 i 07/11/2026, **ronda 1**, preguntes Q-001 a Q-238; és fora del repositori) i dues instruccions escrites del responsable del 09/11/2026: la primera sobre les contradiccions i la segona amb les correccions.
- **Abast:**
  - **Substitueix el punt 3 de la [070](070-quota-integra-i-renovacio-als-12-mesos-del-pagament.md)** en la separació dels terminis (repartits equitativament dins dels 12 mesos i editables). Precisa el punt 2 en el càlcul del «vàlid fins a»: el mateix dia de l'any següent.
  - **Tanca** la [P-54](pendents.md), la [P-57](pendents.md) i la [P-58](pendents.md).
  - **Resol en part** la P-12, la P-29, la P-33, la P-49, la P-50, la P-53 i la P-61.
  - **Precisa** regles i supòsits del 01 a l'[addenda de la 072](../planning.md#M01-addenda-072) del pla.

## Prioritat dels registres
Si dos registres es contradiuen, l'ordre és aquest:
1. les decisions de la tercera instrucció del 09/11/2026 i, després, les correccions de la segona;
2. la decisió més recent (per exemple, la 070);
3. el document de la ronda 1, del 07/11/2026.

Qualsevol altre conflicte que es trobi es comunica al responsable i no el resol l'equip.

## Context
El document de la ronda 1 recollia 238 preguntes. El responsable va respondre la Q-001 a la Q-089 (menys la Q-036) i la Q-091; la resta són en blanc. La 070 (09/11/2026, commit 7fa8b97, a la 01:11) és posterior al document (estat del 07/11/2026 a les 00:12) i recull la resposta a la Q-005, la Q-006 i la Q-007. Les respostes de la Q-060 («any natural») i de la Q-076 («fins al final de l'any») copiaven supòsits anteriors; les ha corregit el responsable (vegeu «Correccions del 09/11/2026»).

**Criteri.** Les respostes a preguntes de tipus «decisió» i les de govern del club que el responsable ha decidit s'apliquen com a decisió. Les que depenen d'un fet extern o d'una interpretació legal queden com a posició del responsable, amb la marca de qui les ha de confirmar: Q-016, Q-029, Q-030, Q-034 i Q-035 (assessor de protecció de dades), Q-062 (gestoria, per a l'avís previ SEPA), Q-089 (banc) i Q-091 (PaynoPain).

## Correccions del 09/11/2026 (segona instrucció; prevalen)
1. **Validesa del carnet (Q-060 i Q-076).** El carnet dura **un any des del dia del pagament**, calculat com el **mateix dia de l'any següent**, no com a «+365 dies». Un pagament del 29 de febrer caduca el 28 de febrer de l'any següent. Substitueix qualsevol supòsit d'any natural.
   - Els exempts continuen amb la Q-002 i la Q-003.
   - Per als importats de Cluber, la data des de la qual compta és **[A validar: tresorer]**, perquè depèn de la P-62.1. Proposta de l'equip: la columna «Data alta/renovació» de Cluber, si el tresorer confirma que és la data de l'última renovació pagada.
2. **Terminis (Q-020).** Repartits equitativament dins dels 12 mesos i **editables per la secretaria** (l'import i la data de cada termini), amb un **permís propi** i un **motiu obligatori a l'historial**. El càlcul exacte de les dates es fixa a la T-M01-18.
3. **Camps del perfil (Q-046).** Entren **tots**: telèfon fix, adreça desglossada (codi postal, població i província), nacionalitat i professió.
   - Tots són **opcionals** i mai obligatoris per ser soci.
   - Cada camp té la seva finalitat escrita a la política de privacitat (vegeu l'esborrany [textos-legals.md](../esborranys/textos-legals.md)).
   - Substitueix la tria anterior de l'equip. «Observacions» continua descartada (Q-045).
   - La província per al model 182 continua **[A verificar: gestoria]**.
4. **Verificació pública (Q-063 i Q-064).** **Confirmat i validat per la junta** (comunicat pel responsable del projecte el 09/11/2026; [referència de l'acta: a completar]). La verificació pública mostra el **número de soci sencer i el nom de pila**.
5. **Es mantenen:** la Q-056 (RN-M01-20 tal com és), la Q-004 (RN-M01-72 i T-M01-40, sense implementar), la Q-040 (acceptat) i la Q-079 (opció 1). La Q-024 i la Q-073 continuen pendents de nova resposta.
6. **Formulari d'alta.** Els canvis de la Q-031, la Q-011 i la Q-017 van en una **tasca nova (T-M01-41)**, no a la T-M01-13, que està tancada. Les caselles del butlletí i de les imatges van desmarcades per defecte i separades de les obligatòries. On es desa el consentiment d'imatges d'un menor de 14 anys està pendent de la tria del responsable entre dues opcions.

## Decisions de la tercera instrucció (09/11/2026; prevalen)
1. **Exempts (Q-002 i Q-003).** Es manté la Q-002: el carnet d'un exempt per edat val fins al 31/12 de l'últim any exempt. Els exempts no paguen: per a ells manen la Q-002 i la Q-003. La correcció 1 (un any des del pagament, fins al mateix dia de l'any següent) **només afecta els que paguen**.
2. **Edició dels terminis (Q-020).**
   - Mentre un termini no té cap pagament associat, la secretaria en pot editar l'import i la data, amb motiu obligatori; l'historial guarda el valor anterior.
   - Quan ja té un pagament, només es pot anul·lar i crear-ne un de nou.
   - Els terminis sempre sumen el preu a terminis (96 €; vegeu la quarta instrucció, punt 2). Moure imports i dates entre terminis és editar; canviar el total és anul·lar i tornar a generar.
   - Es fa a la T-M01-18.
3. **Consentiment d'imatges d'un menor de 14 anys (Q-031 i Q-044): opció A.**
   - Es desa a la persona del menor (`core.Consent`), amb el representant com a «qui el dona».
   - És l'**única excepció a la Q-044** (les altres acceptacions del representant es queden a la sol·licitud).
   - Va a la T-M01-41: un camp «qui el dona» a `core.Consent`, amb una migració posterior a la `core/0013`.
   - No s'implementa ara.
4. **Carnet dels importats (Q-076).** S'accepta la proposta: compta des de la columna «Data alta/renovació» de Cluber (un any, fins al mateix dia de l'any següent), **[A validar: tresorer]**.
5. **T-M01-25:** passa a «feta en part».
6. **Nacionalitat i professió: decisió del responsable del projecte (09/11/2026, opció 1).** Es queden fora del perfil fins que hi hagi un procés que en justifiqui la finalitat. Entren el telèfon fix i l'adreça desglossada.

## Decisions de la quarta instrucció (09/11/2026; decisions del responsable del projecte; prevalen)
1. **Socis de baixa a Cluber (Q-071).** La importació llegeix l'«Estat» de Cluber i **exclou les files de baixa**, amb el motiu explícit «baixa a Cluber», i en dona una llista a la secretaria. **Modifica el punt 7 de la [071](071-importacio-de-cluber-format-real-i-iban-descartat.md)**: la resta de socis continuen entrant actius. El valor exacte que fa servir Cluber per a la baixa es comprova amb l'exportació real **[A validar: secretaria o tresorer]**. Es fa a la T-M01-24b i a la T-M01-25.
2. **Terminis (P-61, Q-019 i Q-021): opció (a).** 3 × 32 € = 96 € és un **preu propi del pagament a terminis**, no la quota anual repartida: la diferència amb la quota anual és un **recàrrec que decideix la junta** (és una dada, no una regla del codi). Els terminis sumen el preu a terminis. Corregeix el punt 2 de la tercera instrucció («sumen la quota anual»). La resta de la P-61 continua oberta.
3. **Recordatoris de quota d'un menor que paga.** Fins als 14 anys, al correu del representant; a partir dels 14, al contacte del soci. **Es resol a la T-M01-41** (on es desa el representant); mentrestant, els recordatoris van al contacte de la persona.
4. **Pantalla per anul·lar una quota.** Va a la **T-M01-40**, amb el mateix permís i el mateix motiu obligatori que l'exempció. No es fa ara; el servei `fees.cancel_fee` ja existeix.
5. **Importat sense data d'alta (Q-075).** S'accepta que l'entrada inicial de l'historial porti la data de la importació, amb la procedència «importat de Cluber», **amb la condició que no es mostri mai com a antiguitat ni com a data d'alta**.

## Decisió

### 1. Quotes, exempts i terminis

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-001 | Exempts per edat (P-57) | **Opció 1.** Passen a «actiu» en aprovar l'alta, amb carnet i sense cap quota ni càrrec de 0 €. Entrada d'historial amb el motiu «sense quota exigible (RN-M01-65)» | RN-M01-07, RN-M01-18, RN-M01-67; T-M01-14, T-M01-19 |
| Q-002 | Validesa del carnet d'un exempt | **Opció 1.** Fins al 31/12 de l'últim any exempt (any de naixement + 14). Una baixa continua revocant el carnet. **Es manté (tercera instrucció):** la correcció 1 només afecta els que paguen | RN-M01-19; T-M01-19, T-M01-20 |
| Q-003 | L'1 de gener en què comença a pagar | **Opció 1.** Continua «actiu» i se li genera la quota. Quan la paga, el carnet li val un any des del pagament (correcció 1). Si no paga, el tresorer el marca impagat a mà ([040](040-impagat-es-marca-a-ma.md)) i el carnet no és vàlid fins que pagui | T-M01-18 |
| Q-004 | Altres exempcions | No n'hi ha cap més aprovada. Es vol poder eximir un soci de la quota d'un període, en l'alta o en qualsevol moment. Es fa com una **anul·lació amb motiu i amb un permís propi**, mai com un pagament de 0 € | RN-M01-72 i T-M01-40 (sense implementar) |
| Q-005 a Q-007 | Prorrata | Cap prorrata: ja ho recull la 070 | — |
| Q-008 | Quota anul·lada i retorn dins del mateix període (P-54) | **Sortida E.** Una quota nova del mateix període; l'anul·lada es queda a l'historial i no es pot pagar (un càrrec anul·lat ja no canvia, RN-67). «Vàlid fins a»: el que doni la quota pagada més recent (correcció 1). El mateix val per a un segon canvi de tipus dins del període. Cal un número d'ordre a la clau d'`AnnualFee` | RN-M01-12; T-M01-14, T-M01-17, T-M01-18 |
| Q-009 | Prorrata en una readmissió | Substituïda per la 070: la readmissió paga la quota íntegra | — |
| Q-019 | 3 × 32 € | S'ofereix, per al soci de ple dret | P-61 |
| Q-020 | Calendari dels tres pagaments | El primer en l'alta o la renovació; els altres dos, **repartits equitativament dins dels 12 mesos**. **Correcció 2:** l'import i la data de cada termini els pot editar la secretaria, amb permís propi i motiu obligatori a l'historial. **Tercera instrucció:** només mentre el termini no té cap pagament (l'historial guarda el valor anterior); amb un pagament, només anul·lar i crear-ne un de nou; els terminis sempre sumen la quota anual (canviar el total és anul·lar i tornar a generar). El càlcul de les dates es fixa a la T-M01-18 | P-61; T-M01-18 |
| Q-021 | Per què 96 € | Preu fixat per la junta | — |
| Q-022 | Un termini que no es paga | El soci queda en suspens per impagat i no pot fer servir cap servei, curs ni activitat del club. Continua obert si el suspens és la marca manual d'impagat (040) o un bloqueig automàtic | P-61 |
| Q-023 | Mentrestant | Només la quota anual | — |
| Q-060 | Venciment (P-29) | **Correcció 1:** un any des del dia del pagament, fins al mateix dia de l'any següent (29/02 → 28/02). Cap any natural, excepte per als exempts (Q-002 i Q-003). Continua obert a la P-29: el calendari de la remesa i de la campanya de mandats | RN-M01-17, RN-M01-19, S-M01-03 |
| Q-061 | Dies dels recordatoris | 15 dies abans, el dia abans i el mateix dia del venciment, i 15 i 30 dies després si no s'ha pagat. Configurables | RN-M01-14, S-M01-04 |
| Q-062 | Avís previ de la renovació | Una setmana abans, configurable. La data límit per demanar la baixa abans de la renovació no s'ha respost. L'avís previ d'un rebut domiciliat (S-M05b-06, 14 dies naturals com a supòsit) és un altre avís i el confirmen el banc i la gestoria | T-M01-18, 05b |
| Q-077 | Quotes cobrades per Cluber | Informatives, no són ingressos. Al començament, el tresorer quadra a mà el compte del club (saldo d'obertura) | RN-M01-33; 04 |
| Q-078 | Llicències entre Cluber i el 06 | A mà, una a una, amb la llista que ja té el club i l'aplicació de la FECDAS. L'administració amb permís hi posa la llicència i si està pagada, sense comptar-ho com a ingrés | T-M01-23, 06 |

### 2. Canvi de tipus i baixa

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-049 | Import del canvi a ple dret | La diferència entre quotes (55 €) | RN-M01-15, S-M01-01 |
| Q-050 | Quan és efectiu | Quan el suplement està pagat | P-M01-B, pas 3 |
| Q-051 | De ple dret a simpatitzant | A la renovació següent | P-M01-B |
| Q-052 | Des d'on resol el President | Resposta: «el President ha de tenir un rol, igual que els altres». No tria entre resoldre des de la vista de sol·licituds o donar-li P4. **Continua oberta** | T-M01-17 |
| Q-053 | Canviar el tipus d'un soci de baixa | Opció 1: no; si torna, tria el tipus en la readmissió | T-M01-17 |
| Q-054 | Motiu en el canvi de tipus d'un impagat | Opció 1: es manté | T-M01-17 |
| Q-055 | Qui rebutja una baixa (P-50) | Qui tingui permís d'edició de les sol·licituds; amb només lectura, no. Els motius no estan fixats | T-M01-17 |
| Q-056 | Quotes pendents en una baixa | RN-M01-20 tal com és. Les pendents posteriors a la data efectiva s'anul·len amb motiu; les anteriors se segueixen devent | RN-M01-20, S-M01-05 |
| Q-057 | Perdonar o anul·lar una quota anterior | Qui tingui permís d'edició de les quotes; amb només lectura, no. Sempre una anul·lació amb motiu, mai un esborrat. El permís concret es fixa a la T-M01-17 | T-M01-17 |
| Q-058 | Què veu el soci abans de demanar la baixa | A criteri de l'equip. Proposta per a la T-M01-17: la data efectiva, les quotes pendents i què se'n farà (RN-M01-20), que el carnet es revoca i que el compte personal es manté (Q-059) | T-M01-17 |
| Q-059 | Compte personal després de la baixa | Es manté, per tenir l'historial | S-M01-12 |

### 3. Carnet i verificació

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-063 | Número a la verificació pública | El número sencer. **Confirmat per la junta** (correcció 4; [referència de l'acta: a completar]) | RN-M01-26, S-M01-06; T-M01-20, T-M01-26 |
| Q-064 | Nom de pila a la verificació | Sí. **Confirmat per la junta** (correcció 4; [referència de l'acta: a completar]) | RN-M01-26, S-M01-07; T-M01-20, T-M01-26 |
| Q-065 | Darrere del carnet | En el carnet digital, el contingut del wireframe | S-M01-08; T-M01-19 |
| Q-066 | Insígnia de soci clàssic | Sense llindar automàtic (no hi ha l'historial real de tothom). L'administració l'assigna a mà com a reconeixement; el carnet passa a una versió daurada que conserva el disseny, i el voltant de la foto o l'avatar del perfil també. **Sense tasca encara** | RN-M01-23, S-M01-09 |
| Q-067 | Antiguitat en una readmissió | Des de la primera alta | S-M01-10 |
| Q-075 | Data d'alta que Cluber no té | No se'n posa cap i no es mostra l'antiguitat d'aquests socis. Substitueix el supòsit «data més antiga coneguda, aproximada» | RN-M01-21, S-M01-18; T-M01-25 |
| Q-076 | Carnet dels importats amb la quota pagada a Cluber | Sí, vàlid. **Correcció 1:** un any des del pagament, fins al mateix dia de l'any següent. **Tercera instrucció:** compta des de la columna «Data alta/renovació» de Cluber [A validar: tresorer] | RN-M01-34, S-M01-24; T-M01-25, T-M01-19 |

### 4. Menors i alta

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-010 | Document d'un menor | El del menor és opcional i el del representant és obligatori (ja és la RN-M01-70) | — |
| Q-011 | Correu i telèfon d'un menor | **Opció 3.** Els del menor, opcionals; els del representant, obligatoris. El rebut i els avisos van al representant. `MemberRequest` no té el correu ni el telèfon del representant: cal un canvi de model | T-M01-41, T-M01-14 |
| Q-012 | Compte personal d'un menor | **Opció 1.** Cap compte personal abans dels 14 anys; a partir dels 14, compte propi amb el seu correu. En aprovar l'alta d'un menor de 14 anys no s'envia cap invitació | T-M01-14, T-M01-16 |
| Q-013 | Persona de referència per a menors | El Secretari. El protocol no està fixat | Checklist H5 |
| Q-014 | Mandat SEPA d'un menor | El signa el representant que ha autoritzat l'alta | RN-M05a-13 |
| Q-015 | Menors a les activitats | L'edat mínima és un requisit configurable per activitat, com el nivell o les especialitats | 02 |
| Q-016 | Consentiments quan el menor es fa gran | Posició del responsable: als 14 anys, el menor accepta ell mateix la política de privacitat; les obligacions econòmiques continuen amb el representant fins als 18; als 18 ho accepta tot sol. **[A validar: assessor de protecció de dades]** | T-M01-16, T-M01-22 |
| Q-017 | Passaport | **Opció 3.** El passaport només s'admet a l'alta presencial | T-M01-41 |
| Q-018 | Data de naixement (punt 0 de l'ordre del dia) | Tancat amb la 068 | Ordre del dia |
| Q-025 | Sol·licituds que no es resolen | No caduquen; la secretaria les rebutja amb motiu | T-M01-14 |
| Q-026 | Dades del representant | Es conserven mentre la persona sigui sòcia | T-M01-22 |
| Q-042 | Contacte nou d'una persona que ja existeix | **Opció 1.** Es desa a la sol·licitud, visible només per a qui revisa l'alta; en aprovar, la secretaria decideix si actualitza la persona, amb registre | T-M01-14 |
| Q-043 | Comprovació del representant | **Opció 2.** La secretaria comprova el document del representant i ho deixa registrat abans d'aprovar. Si es guarda una còpia: per decidir (proposta: no; només la marca, qui i quan) | T-M01-14 |
| Q-044 | Acceptacions en aprovar | **Opció 1.** Només les del sol·licitant passen a `core.Consent`, amb referència a la sol·licitud; les del representant es queden a la sol·licitud. **Excepció (tercera instrucció, opció A):** el consentiment d'imatges d'un menor de 14 anys es desa a la persona del menor, amb el representant com a qui el dona (T-M01-41) | T-M01-14, T-M01-41 |

### 5. Textos legals, consentiments i idiomes

| Q | Tema | Resposta | On s'aplica |
|---|---|---|---|
| Q-027 | Terminis legals de conservació (Q-14) | Esborrany a [docs/esborranys/terminis-de-conservacio.md](../esborranys/terminis-de-conservacio.md). **No vigent; a validar: gestoria i assessor de protecció de dades** | S-M01-15, T-M01-22 |
| Q-028 | Textos legals de l'alta (Q-16) | Esborrany a [docs/esborranys/textos-legals.md](../esborranys/textos-legals.md). **No vigent; a validar: gestoria i assessor de protecció de dades** (i la junta) | Checklist H1 |
| Q-029 | Una versió nova obliga a tornar a acceptar? | No (es manté el supòsit de la T-M01-08) [A validar: assessor de protecció de dades] | T-M01-08 |
| Q-030 | Prova del consentiment presencial | N'hi ha prou amb el registre de qui fa l'alta [A validar: assessor de protecció de dades] | T-M01-13 |
| Q-031 | Butlletí i imatges | Es demanen **a l'alta**, amb les caselles **desmarcades per defecte** i separades de les obligatòries, i es poden canviar al perfil. Substitueix el supòsit de la T-M01-13 de no posar la casella del butlletí | T-M01-41, T-M01-16 |
| Q-032 | Llengües (P-49) | Català, castellà, anglès, basc, gallec i francès, a tota la plataforma, amb una manera fàcil d'afegir-ne d'altres | P-49, T-M01-09b |
| Q-033 | Qui tradueix | Una eina de traducció automàtica, perquè no calgui fer-ho a mà (per exemple, els butlletins). Els textos legals continuen sota la Q-034 i la Q-035 | P-49 |
| Q-034 | Quina versió preval | El català [A validar: assessor de protecció de dades] | P-49 |
| Q-035 | Consentiment en una altra llengua | N'hi ha prou amb el primer consentiment [A validar: assessor de protecció de dades] | P-49 |
| Q-037 | Qui registra un cobrament manual (P-12) | Qui tingui permís de veure i editar la tresoreria | 04, 05b |
| Q-038 | Justificant del cobrament manual | Comprovant opcional. El motiu continua sent obligatori (CLAUDE.md) | 04, 05b |
| Q-039 | Qui atén les sol·licituds RGPD | L'administrador | S-M01-14 |
| Q-045 a Q-048 | Camps opcionals del perfil (P-58) | **Tercera instrucció:** entren el telèfon fix i l'adreça desglossada (codi postal, població i província); la nacionalitat i la professió es queden fora fins que hi hagi un procés que en justifiqui la finalitat (decisió del responsable). Text de la correcció 3, ara substituït: entren el telèfon fix, l'adreça desglossada, la nacionalitat i la professió, tots opcionals i mai obligatoris per ser soci, cadascun amb la finalitat escrita a la política de privacitat. «Observacions» queda fora (Q-045). Els veuen i editen el soci i l'administració amb permís de camp (Q-047); es conserven, s'exporten i s'anonimitzen com la resta del perfil (Q-048). La província per al model 182 continua [A verificar: gestoria] | T-M01-16, T-M01-22 |

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

## Continuen obertes
- **Pendents de nova resposta:** Q-024 (conservació de les sol·licituds rebutjades) i Q-073 (conservació de les línies de la importació).
- **Sense decidir:**
  - la Q-052 (President);
  - la Q-086 (nivell 1);
  - de la P-61 (el preu a terminis ja és decidit, quarta instrucció), quan passa a actiu i fins quan té carnet qui paga a terminis, si el suspens és manual o automàtic, quan es poden triar els terminis i què passa amb els menors;
  - de la P-29, el calendari de la remesa i de la campanya de mandats;
  - de la Q-062, la data límit per demanar la baixa;
  - de la Q-083, on es veu el resum;
  - la confirmació del tresorer de la data d'inici del carnet dels importats («Data alta/renovació», [A validar: tresorer]);
  - el valor exacte de l'«Estat» de baixa a l'exportació real de Cluber ([A validar: secretaria o tresorer]);
  - l'import del recàrrec del pagament a terminis (la junta).
- **En blanc al document:** Q-036, Q-090, Q-092, Q-093 i de la Q-104 a la Q-238. De la Q-094 a la Q-103 eren validacions de la T-M01-13, que ja és «Feta» (09/11/2026).
- **R2-13 i R2-21:** són del document de la ronda 2, que ha d'aportar el responsable. No són al repositori: només apareixen a la fila de la T-M01-15 i a l'índex del diari, des del commit 1dafae2, sense cap definició.

## Conseqüències
- [pendents.md](pendents.md):
  - la P-54, la P-57 i la P-58 passen a «Resolts»;
  - la P-61 es corregeix (terminis repartits i editables) i rep les respostes de la Q-019 a la Q-023;
  - la P-12, la P-29, la P-33, la P-49, la P-50 i la P-53 reben les respostes parcials.
- [Pla](../planning.md): [addenda de la 072](../planning.md#M01-addenda-072) amb la RN-M01-72, la CA-M01-65 a la CA-M01-67, la T-M01-40 i la T-M01-41. Hi ha precisions datades a la RN-M01-07, 14, 15, 17, 18, 19, 20, 21, 23, 26, 34 i 67, als supòsits de M01-13, a la T-M01-13 (límits), a la T-M01-18 (terminis editables) i a la T-M01-39 (aprovada).

## Fonts
- Document de consulta de la ronda 1 (07/11/2026, fora del repositori), amb les respostes del responsable.
- Instruccions escrites del responsable del projecte del 09/11/2026 (dues).
- Decisions [040](040-impagat-es-marca-a-ma.md), [059](059-rols-i-permisos-editables.md), [067](067-readmissio-d-un-antic-soci.md), [068](068-socis-menors-i-inici-del-pagament-de-la-quota.md), [069](069-condicio-de-soci-i-quota-d-alta-per-mesos.md) i [070](070-quota-integra-i-renovacio-als-12-mesos-del-pagament.md).
