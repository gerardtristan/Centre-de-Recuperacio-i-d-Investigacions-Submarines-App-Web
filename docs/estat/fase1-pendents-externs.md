# Fase 1: tasques que esperen algú de fora del projecte

Inventari del 19/11/2026, fet per instrucció del propietari. De les tasques que no són «feta» als mòduls 00, 01, 04, 05a i 05b i a les transversals de la fase 1, aquí hi ha les que no es poden acabar sense algú de fora de l'equip: el proveïdor de pagaments o el banc reals, proves en mòbils reals, textos o respostes de la junta, el tresorer o la gestoria, o un mòdul de la fase 2. **No es construeixen.** Les branques que ja tenen feina feta (`tasca/T-M05a-23-caducitat-i-invitacio`, `tasca/T-M05a-26-targeta-caducada-o-denegada` i `tasca/T-M05b-24-reintent-targeta-guardada`) es queden sense PR i no s'esborren.

Les preguntes estan agrupades per qui les ha de respondre, perquè cada bloc es pugui enviar d'una vegada. Cada bloc té el missatge llest per enviar, escrit perquè l'entengui algú de fora del projecte, i una taula que diu quina tasca desbloqueja cada pregunta i on és al tauler. «Al tauler» vol dir la fila de [`pendents.md`](../decisions/pendents.md) o de l'[apèndix de preguntes del pla](../planning.md#preguntes) (totes surten al tauler) i, si en té, la clau de [`tauler-preguntes.yml`](../decisions/tauler-preguntes.yml) amb les opcions. Aquest document no dona cap pregunta per resposta: quan arribi una resposta, es registra a `pendents.md` o en una decisió i la fila de la tasca canvia a `docs/estat/`. L'estat de cada tasca és al fitxer del seu mòdul ([README](README.md)); aquí no es repeteix.

Abans d'enviar res: cap dada personal (ni noms de socis, ni IBAN, ni exportacions reals).

## Resum

| Tasca | Què l'atura | Qui respon | Preguntes |
|---|---|---|---|
| [T-RP-02b](M00.md) | El mòdul 02 (activitats i sessions), de la fase 2 | — | [Sense pregunta](#sense-pregunta) |
| [T-RP-02c](M00.md) | Si assignar un rol tanca les sessions | Propietari | [O1](#propietari) |
| [E4b](M00.md) i [P-80](M00.md) | El servidor de producció | Propietari | [O3](#propietari) |
| [T-M01-16b](M01.md) | Revisió i aprovació dels textos legals | Gestoria o assessor; junta | [G3, G4](#gestoria), [J2](#junta) |
| [T-M01-18b](M01.md) | Textos dels recordatoris de quota | Junta, amb el tresorer | [J1](#junta) |
| [T-M01-21b](M01.md), [T-M01-28b](M01.md), [T-M05a-18b](M05a.md), [T-F1-02](F1.md) | Proves en mòbils reals (les fa el propietari, P-284 i P-301) | Propietari | [O2](#propietari) |
| [T-M01-22b](M01.md) | Confirmació professional del termini i de les respostes RGPD | Gestoria o assessor | [G1, G2, G5](#gestoria) |
| [T-M01-31](M01.md) | El mòdul 06 (llicències), de la fase 2 | — | [Sense pregunta](#sense-pregunta) |
| [T-M01-39](M01.md), part (c) | La mesura darrere del proxy, a l'entorn de proves | Propietari | [O2](#propietari) |
| [T-M01-43c](M01.md) i [T-M05a-13e](M05a.md) | Cap tasca crea els avisos dins l'app | Propietari | [O6](#propietari) |
| [T-M01-45b](M01.md) | Un iPhone real i el logotip reduït | Propietari | [O2, O5](#propietari) |
| [P-12c](M04.md) | Com es corregeix un pagament a mà equivocat | Tresorer | [T1](#tresorer) |
| [T-M05a-23](M05a.md) | El proveïdor real (targeta guardada i caducitat) | Banc; PaynoPain | [B1](#banc), [PP1 a PP3](#paynopain) |
| [T-M05a-26](M05a.md) | El proveïdor real (targeta caducada o denegada) | PaynoPain | [PP3, PP4](#paynopain) |
| [T-M05b-24](M05b.md) | El proveïdor real (reintents amb la targeta guardada) | PaynoPain | [PP4 a PP7](#paynopain) |
| [T-M05b-19b](M05b.md) | Portes del nivell 2: proveïdor i banc reals, autorització de la junta | Banc, PaynoPain, junta, tresorer i propietari | [B1 a B7](#banc), [PP1, PP2, PP8](#paynopain), [J3, J4](#junta), [T3](#tresorer), [O4](#propietari) |

A més, la [T-M01-49](M01.md) (terminis de la quota) es pot construir, però no es pot encendre sense la [J5](#junta). Recompte: banc 8, PaynoPain 8, junta 6, tresorer 3, gestoria o assessor 5, propietari 6.

<a id="banc"></a>
## Banc (a través del tresorer)

> Bon dia,
>
> Som el C.R.I.S., club de busseig de Barcelona i client de l'entitat. Estem acabant una aplicació pròpia per cobrar les quotes dels socis amb rebuts domiciliats, amb targeta i amb Bizum. Abans de fer-la servir de debò ens cal que ens confirmeu per escrit uns quants punts. Entre parèntesis, el que l'aplicació fa ara mentre no tenim la vostra resposta.
>
> 1. Podem contractar a través vostre el TPV virtual de PaynoPain (Paylands) per cobrar amb targeta i Bizum, com a associació sense ànim de lucre? Amb quines condicions i comissions?
> 2. L'identificador de creditor SEPA del club és ES + dígits de control + «000» + el NIF del club? Si no en tenim, com el demanem? (Ara el calculem així.)
> 3. De quins països admeteu IBAN per domiciliar rebuts? (Ara, tota la zona SEPA; el tresorer pot treure'n països.)
> 4. Per a les remeses de rebuts: quina versió del fitxer pain.008 voleu? Cal marcar el primer rebut de cada mandat (FRST) o sempre recurrent (RCUR)? Cal el BIC de l'entitat del deutor? Quin nom del creditor teniu exactament? Ens podeu enviar un fitxer de mostra? (Ara: pain.008.001.02, SEPA Core, sempre RCUR, sense BIC i el nom del club en majúscules sense accents.)
> 5. Quan cobreu una remesa, ens l'abonen en un sol moviment o rebut a rebut? La comissió la descompteu de l'abonament o surt en un moviment a part? (Ara: un sol abonament per remesa; admetem la comissió descomptada o a part.)
> 6. Quins codis de retorn ens poden arribar quan un rebut torna? Ens agradaria confirmar què fem amb cadascun: només tornem a passar el rebut amb el codi AM04 (fons insuficients); amb AC04 (compte tancat) i MD01 (sense mandat) deixem de fer servir el mandat; amb la resta, oferim al soci una altra manera de pagar. És correcte?
> 7. L'extracte del compte, el podem descarregar en format Norma 43 (quadern 43)? (Ara l'aplicació llegeix Norma 43 i CSV.)
> 8. Els socis tenen mandats signats amb el programa que fem servir ara (Cluber). Es poden traspassar al club, o cal que cada soci en signi un de nou? (Ara: cada soci en signa un de nou des de l'aplicació.)
>
> **Per què ens cal:** sense aquestes dades no podem cobrar cap quota per domiciliació ni amb targeta, i si el format del fitxer o els codis no coincideixen amb els vostres, els rebuts tornarien.
>
> Moltes gràcies.

| Pregunta | Tasques | Al tauler |
|---|---|---|
| 1 | T-M05a-23, T-M05a-26, T-M05b-24, T-M05b-19b | `pendents.md` P-44; apèndix, banc, P-44. Sense clau d'opcions |
| 2 | T-M05b-19b (abans del primer avís previ) | `pendents.md` P-24. Sense clau d'opcions |
| 3 | Encendre la signatura del mandat (nivell 1) | `pendents.md` P-123; clau P-123 (A qualsevol IBAN, B només ES, C llista editable; per defecte, C) |
| 4 | T-M05b-19b | `pendents.md` P-233; clau P-233 (A com s'ha fet, B esperar la mostra; recomanada A) |
| 5 | T-M05b-19b | `pendents.md` P-237; clau P-237 (A una per remesa, B per rebut, C brut i comissió a part; recomanada A) |
| 6 | T-M05b-19b | `pendents.md` P-291; clau P-291 (A com s'ha fet, B reintentar els desconeguts, C que triï el tresorer; recomanada A) |
| 7 | T-M05b-19b (conciliació real) | `pendents.md` P-45, punt 10. Sense clau d'opcions |
| 8 | Abast de la campanya de mandats (no atura cap tasca) | `pendents.md` P-21; apèndix, banc, «S-M01-25; S-M05a-14». Sense clau d'opcions |

<a id="paynopain"></a>
## PaynoPain

Completa els missatges de [`preguntes-externes.md`](../preguntes-externes.md) (seccions 4 i 8); si aquells no s'han enviat, aquest es pot enviar sol.

> Bon dia,
>
> Des del C.R.I.S., club de busseig de Barcelona, volem cobrar les quotes dels socis, les inscripcions i les llicències amb el vostre TPV virtual des d'una aplicació pròpia. La part de la targeta guardada per a les renovacions ja la tenim feta amb un simulador, i abans de connectar-la amb vosaltres ens cal saber:
>
> 1. On es tracten i es guarden les dades (servidors i còpies), quines empreses hi intervenen i si signeu un contracte d'encarregat del tractament. Hi ha cap transferència de dades fora de la Unió Europea? (Per a nosaltres és un requisit: les dades només poden ser a la UE.)
> 2. Teniu entorn de proves? Com s'hi accedeix?
> 3. Es pot guardar la targeta d'un soci per cobrar-li la renovació anual sense que ell hi sigui (cobrament iniciat pel club)? En guardar-la, ens doneu la data de caducitat i els quatre últims dígits? Si el banc del soci li envia una targeta nova, ens n'avisa el sistema o l'actualitza sol?
> 4. Quan un cobrament es denega, quins motius o codis ens arriben? Es pot distingir una denegació definitiva (targeta perduda, robada o cancel·lada) d'una de temporal (sense saldo, límit superat)?
> 5. Després d'una denegació, podem tornar a intentar el cobrament amb la mateixa targeta? Quantes vegades i cada quant ho recomaneu? Té cost un intent denegat? (Ara l'aplicació no reintenta: avisa el soci perquè pagui d'una altra manera.)
> 6. Si el banc del soci demana que s'autentiqui per a un cobrament amb la targeta guardada, què rebem? L'ordre queda oberta o es tanca sola? Podem enviar una clau perquè una mateixa ordre no es cobri dues vegades si la repetim per un error de xarxa?
> 7. Podem saber l'identificador de l'ordre abans de cobrar, i consultar després l'estat d'una ordre si no ens arriba l'avís?
> 8. Qui contracta el servei (nosaltres o el banc) i quines comissions hi ha per targeta, Bizum, devolucions, contracàrrecs i intents denegats?
>
> **Per què ens cal:** l'aplicació ha de saber què fer quan una targeta caduca o es denega, sense cobrar dues vegades ni deixar cap quota sense avisar; i les dades del club només es poden tractar dins la UE.
>
> Moltes gràcies.

| Pregunta | Tasques | Al tauler |
|---|---|---|
| 1 | T-M05b-19b (eliminatòria) | `pendents.md` P-45, punt 3; apèndix, PaynoPain. Sense clau d'opcions |
| 2 | T-M05a-23, T-M05a-26, T-M05b-24, T-M05b-19b | `pendents.md` P-45, punt 8; apèndix, PaynoPain, «S-M05a-03; P-45 punt 8». Sense clau d'opcions |
| 3 | T-M05a-23, T-M05a-26 | `pendents.md` P-45, punt 6; apèndix, PaynoPain, «S-M05a-02; P-45 punt 6». Sense clau d'opcions |
| 4 | T-M05a-26, T-M05b-24 | No és al tauler (és a les [limitacions de la targeta guardada](M05b.md#limitacions-targeta-guardada)) |
| 5 | T-M05b-24 | No és al tauler |
| 6 | T-M05b-24 | No és al tauler com a pregunta al proveïdor; el cas de l'autenticació és la P-303 (clau P-303, que respon el propietari) |
| 7 | T-M05b-24 | Apèndix, PaynoPain, S-M05b-03 (consulta d'ordres). L'identificador per endavant no és al tauler |
| 8 | T-M05b-19b | `pendents.md` P-45, punts 1 i 2; apèndix, PaynoPain. Sense clau d'opcions |

<a id="junta"></a>
## Junta

> Hola,
>
> L'aplicació del club està gairebé llesta per a la primera fase (socis, quotes, carnet i cobraments). Abans de fer-la servir amb socis reals ens calen unes decisions de la junta:
>
> 1. **Textos dels recordatoris de quota.** Els correus que avisen un soci que té la quota pendent tenen un text provisional. Els podeu llegir i corregir vosaltres mateixos des de l'aplicació («Ajustos», textos editables), amb el tresorer. Ens dieu quan els doneu per bons?
> 2. **Textos legals i consentiments.** La política de privacitat, el text de l'alta i els consentiments del butlletí i de les imatges els ha redactat l'equip i ja són a l'aplicació, però no són vigents fins que la junta els aprovi, després de la revisió de la gestoria o de l'assessor de protecció de dades. Qui els ha de revisar i quan els podeu aprovar?
> 3. **Protocol de protecció de menors.** Hi ha un esborrany del protocol (persona de referència, comunicacions amb el representant). Ara no hi ha socis menors, però és condició per obrir l'aplicació a tothom. El podeu aprovar o dir què hi canviaríeu?
> 4. **Autorització per fer-la servir de debò.** L'aplicació s'encén en dos passos, i cadascun necessita l'autorització expressa de la junta: primer, recollir les dades bancàries i les signatures dels mandats dels socis, sense cobrar res; després, cobrar de debò les quotes i deixar Cluber. Quan estigui tot provat us demanarem cada autorització per escrit: ens podeu dir qui la signa i com la voleu rebre?
> 5. **Pagament de la quota en tres terminis.** L'estem preparant per als socis de ple dret amb aquests valors: 96 € en total i sense recàrrec. Els confirmeu per escrit? (Es poden canviar des de l'aplicació; mentre no ho confirmeu, l'opció queda apagada.)
> 6. **Domini cris.es.** Els correus de l'aplicació sortiran de cris@cris.es, i per això cal afegir dos registres al domini (SPF i DKIM) perquè no arribin com a correu brossa. Sabem que l'accés al domini el teniu a través d'una empresa: qui ho pot fer?
>
> Moltes gràcies.

| Pregunta | Tasques | Al tauler |
|---|---|---|
| 1 | T-M01-18b | No és al tauler com a pregunta pròpia (RN-M01-14, [A validar: junta i tresorer]) |
| 2 | T-M01-16b | No és al tauler (Q-028 i Q-16, a la [072](../decisions/072-respostes-del-responsable-a-la-ronda-1-de-pendents.md) i la [085](../decisions/085-respostes-del-responsable-a-les-preguntes-pendents-de-t-m00-i-t-m01.md), G-4; checklist H1) |
| 3 | T-M05b-19b (porta H5) | `pendents.md` P-33; apèndix, junta, «S-M01-12, 13». Sense clau d'opcions |
| 4 | T-M05b-19b, i encendre el nivell 1 | Apèndix, junta, fila «025». Sense clau d'opcions |
| 5 | Encendre la T-M01-49 (no n'atura la construcció) | `pendents.md` P-61. Sense clau d'opcions |
| 6 | Desplegament a producció (no és cap fila d'estat) | `pendents.md` P-25. Sense clau d'opcions |

<a id="tresorer"></a>
## Tresorer

> Hola,
>
> Tres preguntes de la part de tresoreria de l'aplicació. Entre parèntesis, el que fa ara.
>
> 1. **Un pagament apuntat a mà per error** (per exemple, una quota marcada com a pagada en efectiu que no s'havia pagat): com s'ha de poder corregir? Opcions: (a) es desfà com una transferència apuntada per error: la quota torna a pendent, el pagament queda anul·lat i el rebut també, tot amb un motiu; (b) es tracta com una devolució del club: la quota queda anul·lada i surt una sortida del compte, i el soci ja no deu res; (c) no es corregeix a l'aplicació: ho resols amb un altre moviment i una nota. Recomanem la (a). (Ara no hi ha cap correcció: ho anotes fora de l'aplicació.)
> 2. **Importació de Cluber.** La columna «Data alta/renovació» de l'exportació de Cluber és la data de l'últim pagament de la quota? L'aplicació compta els 12 mesos de la quota d'un soci importat des d'aquesta data. (Ara: sí, i una fila sense data queda pendent fins que la secretaria la posa.)
> 3. **Calendari.** Quan vols fer la primera remesa de rebuts amb l'aplicació, i quan vols obrir la campanya perquè els socis triïn com paguen i signin el mandat? (Ara no hi ha cap data fixada.)
>
> I, amb la junta, els textos dels recordatoris de quota (pregunta 1 de la junta).
>
> Gràcies.

| Pregunta | Tasques | Al tauler |
|---|---|---|
| 1 | P-12c | `pendents.md` P-333; clau P-333 (A com la 045, B com una devolució, C fora de l'aplicació; recomanada A) |
| 2 | T-M01-18c, T-M01-19b, T-M01-25b (no les atura) | No és al tauler: la P-62 és a «Resolts» (097, punt 1) amb aquesta confirmació pendent |
| 3 | T-M05b-19b (primera remesa real) | `pendents.md` P-29; apèndix, tresorer, «P-29; S-M01-03». Sense clau d'opcions |

<a id="gestoria"></a>
## Gestoria o assessor de protecció de dades

Qui és l'assessor de protecció de dades del club [A validar: junta]. Les preguntes 1 i 2 són de la gestoria; la 3, la 4 i la 5, de l'assessor (o de la gestoria, si també en fa).

> Bon dia,
>
> Des del C.R.I.S. estem acabant una aplicació per gestionar els socis i les quotes del club, i abans de fer-la servir amb dades reals volem confirmar que complim la protecció de dades i les obligacions de conservació. Entre parèntesis, el que fa ara l'aplicació.
>
> 1. Quan una persona demana que esborrem les seves dades, les quotes, els rebuts i els pagaments no s'eliminen: el nom, els cognoms i el document queden xifrats i bloquejats. Durant quant de temps els hem de conservar? Els ajuts públics demanen un termini més llarg? (Ara: 6 anys des del 31 de desembre de l'any de l'últim moviment econòmic de la persona, i després es destrueixen.)
> 2. Si qui demana l'esborrat encara deu alguna quota, és correcte no esborrar-lo fins que el deute es pagui o s'anul·li amb un motiu? (Ara: és així.)
> 3. Ens podeu revisar la política de privacitat, el text de l'alta i els consentiments del butlletí i de les imatges? Us enviem l'esborrany.
> 4. Amb un soci de 14 a 17 anys: és correcte que accepti ell mateix la política de privacitat i doni ell mateix els consentiments opcionals (butlletí, imatges), mentre el representant continua responent de les quotes fins als 18? (Ara: és així.)
> 5. Quan una persona demana una còpia de les seves dades, hi incloem les notes de l'administració després que les revisi qui atén la petició. I quan esborrem les dades d'algú, conservem el registre dels consentiments que va donar lligat a una referència anònima. És correcte totes dues coses?
>
> **Per què ens cal:** l'aplicació aplica aquestes regles automàticament; si no són les correctes, hauríem de corregir dades reals.
>
> Moltes gràcies.

| Pregunta | Tasques | Al tauler |
|---|---|---|
| 1 | T-M01-22b (i el termini de la T-M00-04) | Apèndix, gestoria, «S-M01-15 (Q-14); S-M09A-06». Sense clau d'opcions |
| 2 | T-M01-22b | No és al tauler com a oberta: la 085 (G-2) la va respondre sense validació professional |
| 3 | T-M01-16b | No és al tauler (Q-028; esborrany a [`esborranys/textos-legals.md`](../esborranys/textos-legals.md)) |
| 4 | T-M01-16b | No és al tauler (Q-016, a la 072 i la 085, A-5) |
| 5 | T-M01-22b | No és al tauler com a oberta: la 085 (A-1 i A-4) la va respondre sense validació professional |

<a id="propietari"></a>
## Propietari

> 1. **Assignar un rol tanca les sessions del compte?** (a) No: el rol nou val a la petició següent; (b) sí, quan el rol dona accés a dades personals o a diners; (c) sí, sempre. Es recomana la (c); ara es fa la (a).
> 2. **Entorn de proves temporal.** Les proves en mòbils reals (Android i iOS, TalkBack i VoiceOver), les captures de l'ajuda per instal·lar la web a l'iPhone i la mesura de «He oblidat la contrasenya» darrere del proxy necessiten l'entorn de proves temporal. Aproves la PR #251 (servidor de proves al portàtil amb Docker i Cloudflare Tunnel, decisió 099) com a entorn de proves, i quan pots fer les proves de la llista?
> 3. **Servidor de producció.** Quan es contracta el servidor de producció? Encendre el seguiment d'errors i crear els dos usuaris de la base de dades es fan en desplegar-hi.
> 4. **Punts del nivell 2 que són de mòduls de la fase 2** (sitemap, dades estructurades, preguntes freqüents, imatges OG, analítica i llista d'assistència): (a) al nivell 2 s'apliquen a les pàgines públiques que hi hagi llavors i al carnet, i la resta amb la web pública i el 02; (b) el nivell 2 espera la web pública i el 02 sencers; (c) surten del nivell 2 i passen a ser condició de publicar la web pública. Es recomana la (a).
> 5. **Logotip reduït.** Per a la icona de la web instal·lable cal una versió reduïda del logotip (amb el logotip sencer, el marge és massa just). La pot aportar el club?
> 6. **Avisos dins l'app.** Cap tasca de la fase 1 no crea una safata d'avisos dins l'aplicació, i dues tasques l'esperen (l'avís de renovació i el darrer recordatori de la campanya de mandats; tots dos ja surten per correu). Es crea a la fase 1 o s'espera?

| Pregunta | Tasques | Al tauler |
|---|---|---|
| 1 | T-RP-02c | `pendents.md` P-330; clau P-330 (A, B, C; recomanada C) |
| 2 | T-F1-02, T-M01-21b, T-M01-28b, T-M05a-18b, T-M01-45b, T-M01-39 (c) | No és al tauler: P-284 i P-301 ja són resoltes (097); l'entorn és la D5 de la 089 i la PR #251. La Q-086 (072) la decideix l'equip amb la mesura |
| 3 | E4b, P-80 | No és al tauler (P-294 és resolta: no s'encén fins que el servidor existeixi) |
| 4 | T-M05b-19b | `pendents.md` P-300; clau P-300 (A, B, C; recomanada A) |
| 5 | T-M01-45b | `pendents.md`, tanda del 10/11/2026, fila «Ajuda per instal·lar la web a l'iPhone». Sense clau d'opcions |
| 6 | T-M01-43c, T-M05a-13e | No és al tauler |

<a id="sense-pregunta"></a>
## Sense pregunta: esperen un mòdul de la fase 2

- [T-RP-02b](M00.md) (responsables orfes d'una sessió): espera el mòdul 02 (activitats), aparcat per la D6 de la 089.
- [T-M01-31](M01.md) (còpia de lectura de la llicència): espera el mòdul 06 (llicències).
